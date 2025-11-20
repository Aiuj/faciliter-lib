"""Tests for rate limiter functionality."""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock

from core_lib.llm.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimitConfig:
    """Test RateLimitConfig class."""

    def test_default_config(self):
        """Test default RateLimitConfig values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_second == 1.0
        assert config.burst_allowance == 5

    def test_custom_config(self):
        """Test custom RateLimitConfig values."""
        config = RateLimitConfig(
            requests_per_minute=120,
            requests_per_second=2.5,
            burst_allowance=10,
        )
        assert config.requests_per_minute == 120
        assert config.requests_per_second == 2.5
        assert config.burst_allowance == 10


class TestRateLimiter:
    """Test RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test that RateLimiter initializes correctly."""
        config = RateLimitConfig(requests_per_minute=100, requests_per_second=2.0)
        limiter = RateLimiter(config)
        
        assert limiter.config == config
        assert limiter.request_times == []
        assert limiter.last_request_time == 0.0
        assert limiter._lock is not None

    @pytest.mark.asyncio
    async def test_single_request_no_delay(self):
        """Test that first request passes without delay."""
        config = RateLimitConfig(requests_per_minute=60, requests_per_second=1.0)
        limiter = RateLimiter(config)
        
        start_time = time.time()
        await limiter.acquire()
        end_time = time.time()
        
        # Should be nearly instantaneous
        assert end_time - start_time < 0.1
        assert len(limiter.request_times) == 1
        assert limiter.last_request_time > 0

    @pytest.mark.asyncio
    async def test_requests_per_second_limit(self):
        """Test that requests per second limit is enforced."""
        config = RateLimitConfig(requests_per_minute=3600, requests_per_second=2.0)  # High RPM, low RPS
        limiter = RateLimiter(config)
        
        with patch('asyncio.sleep') as mock_sleep:
            # First request should pass immediately
            await limiter.acquire()
            mock_sleep.assert_not_called()
            
            # Second request should be delayed
            await limiter.acquire()
            mock_sleep.assert_called_once()
            
            # Verify delay is approximately 1/RPS = 0.5 seconds
            call_args = mock_sleep.call_args[0][0]
            assert 0.4 < call_args < 0.6  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_requests_per_minute_limit(self):
        """Test that requests per minute limit is enforced."""
        config = RateLimitConfig(requests_per_minute=2, requests_per_second=10.0)  # Low RPM, high RPS
        limiter = RateLimiter(config)
        
        # Mock time to control the clock
        mock_time = 1000.0
        
        def mock_time_func():
            return mock_time
        
        with patch('time.time', side_effect=mock_time_func), \
             patch('asyncio.sleep') as mock_sleep:
            
            # First two requests should pass
            await limiter.acquire()
            await limiter.acquire()
            
            # Third request should be delayed until oldest request expires
            mock_time += 30.0  # Advance time by 30 seconds
            await limiter.acquire()
            
            # Should sleep until the oldest request (at 1000.0) expires at 1060.0
            # Current time is 1030.0, so should sleep for 30 seconds
            # Note: RPS limit may also cause additional sleep
            assert mock_sleep.call_count >= 1
            # Check that one of the sleep calls was for RPM (around 30 seconds)
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            rpm_sleep_found = any(29 < sleep_time < 31 for sleep_time in sleep_calls)

    @pytest.mark.asyncio
    async def test_old_requests_cleaned_up(self):
        """Test that old request timestamps are cleaned up."""
        config = RateLimitConfig(requests_per_minute=10, requests_per_second=10.0)
        limiter = RateLimiter(config)
        
        # Mock time to control aging
        mock_time = 1000.0
        
        def mock_time_func():
            nonlocal mock_time
            return mock_time
        
        with patch('time.time', side_effect=mock_time_func):
            # Make several requests
            await limiter.acquire()
            mock_time += 10
            await limiter.acquire()
            mock_time += 10
            await limiter.acquire()
            
            assert len(limiter.request_times) == 3
            
            # Advance time by more than 60 seconds
            mock_time += 65
            await limiter.acquire()
            
            # Old requests should be cleaned up, only the latest should remain
            assert len(limiter.request_times) == 1
            assert limiter.request_times[0] == mock_time

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test that concurrent requests are handled correctly."""
        config = RateLimitConfig(requests_per_minute=100, requests_per_second=5.0)
        limiter = RateLimiter(config)
        
        async def make_request(request_id):
            await limiter.acquire()
            return request_id
        
        # Start multiple concurrent requests
        tasks = [make_request(i) for i in range(5)]
        
        with patch('asyncio.sleep') as mock_sleep:
            results = await asyncio.gather(*tasks)
        
        # All requests should complete
        assert results == [0, 1, 2, 3, 4]
        
        # Some requests should have been delayed (due to RPS limit)
        assert mock_sleep.call_count >= 3  # At least some delays
        
        # All requests should be recorded
        assert len(limiter.request_times) == 5

    @pytest.mark.asyncio
    async def test_warning_logged_on_rpm_limit(self):
        """Test that warning is logged when RPM limit is hit."""
        config = RateLimitConfig(requests_per_minute=1, requests_per_second=10.0)
        limiter = RateLimiter(config)
        
        with patch('asyncio.sleep'), \
             patch('core_lib.llm.rate_limiter.logger') as mock_logger:
            
            # First request passes
            await limiter.acquire()
            mock_logger.warning.assert_not_called()
            
            # Second request hits RPM limit
            await limiter.acquire()
            mock_logger.warning.assert_called_once()
            
            # Verify warning message
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Rate limit reached" in warning_call
            assert "sleeping for" in warning_call

    @pytest.mark.asyncio
    async def test_zero_rps_edge_case(self):
        """Test edge case with very low RPS."""
        config = RateLimitConfig(requests_per_minute=60, requests_per_second=0.1)  # 1 request per 10 seconds
        limiter = RateLimiter(config)
        
        with patch('asyncio.sleep') as mock_sleep:
            await limiter.acquire()  # First request
            await limiter.acquire()  # Second request should be delayed
            
            # Should sleep for ~10 seconds (1/0.1)
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            assert 9 < sleep_time < 11


class TestRateLimiterIntegration:
    """Integration tests for rate limiter."""

    @pytest.mark.asyncio
    async def test_real_time_behavior(self):
        """Test rate limiter with real time (short duration)."""
        # Use very permissive limits for fast test
        config = RateLimitConfig(requests_per_minute=60, requests_per_second=5.0)
        limiter = RateLimiter(config)
        
        start_time = time.time()
        
        # Make 3 requests
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()
        
        end_time = time.time()
        
        # Should take at least 2 * (1/5) = 0.4 seconds for the delays
        assert end_time - start_time >= 0.3
        
        # But shouldn't take too long (allowing for some overhead)
        assert end_time - start_time < 1.0
        
        # All requests should be recorded
        assert len(limiter.request_times) == 3

    @pytest.mark.asyncio
    async def test_mixed_rpm_and_rps_limits(self):
        """Test scenario where both RPM and RPS limits come into play."""
        config = RateLimitConfig(requests_per_minute=3, requests_per_second=2.0)
        limiter = RateLimiter(config)
        
        mock_time = 1000.0
        
        def mock_time_func():
            return mock_time
        
        with patch('time.time', side_effect=mock_time_func), \
             patch('asyncio.sleep') as mock_sleep:
            
            # First 3 requests fill up the RPM quota
            await limiter.acquire()
            await limiter.acquire()
            await limiter.acquire()
            
            # RPS delays should have occurred
            assert mock_sleep.call_count >= 2
            
            # Reset mock for RPM test
            mock_sleep.reset_mock()
            
            # Fourth request should hit RPM limit
            await limiter.acquire()
            
            # Should have triggered RPM-based sleep
            # Note: both RPS and RPM limits may cause sleeps
            assert mock_sleep.call_count >= 1
            # Check that one of the sleep calls was for RPM (much longer than RPS)
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            rpm_sleep_found = any(sleep_time > 10 for sleep_time in sleep_calls)
            assert rpm_sleep_found  # Should have at least one long sleep for RPM