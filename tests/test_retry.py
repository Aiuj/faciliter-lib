"""Tests for retry functionality."""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, call
from typing import Any

from faciliter_lib.llm.retry import (
    RetryConfig,
    RetryStrategy,
    retry_handler,
    _calculate_delay,
)


class CustomRetryableError(Exception):
    """Custom exception for testing retry logic."""
    pass


class NonRetryableError(Exception):
    """Custom exception that should not be retried."""
    pass


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_config(self):
        """Test default RetryConfig values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.retry_on_exceptions == (Exception,)
        assert config.jitter_factor == 0.5

    def test_custom_config(self):
        """Test custom RetryConfig values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            retry_on_exceptions=(ValueError, TypeError),
            jitter_factor=0.2,
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config.retry_on_exceptions == (ValueError, TypeError)
        assert config.jitter_factor == 0.2


class TestCalculateDelay:
    """Test delay calculation functions."""

    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(
            base_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter_factor=0.0,  # No jitter for predictable testing
        )
        
        # Test first few attempts
        assert _calculate_delay(0, config) == 1.0  # 1.0 * 2^0
        assert _calculate_delay(1, config) == 2.0  # 1.0 * 2^1
        assert _calculate_delay(2, config) == 4.0  # 1.0 * 2^2
        assert _calculate_delay(3, config) == 8.0  # 1.0 * 2^3

    def test_linear_backoff(self):
        """Test linear backoff calculation."""
        config = RetryConfig(
            base_delay=2.0,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            jitter_factor=0.0,  # No jitter for predictable testing
        )
        
        assert _calculate_delay(0, config) == 2.0  # 2.0 * (0 + 1)
        assert _calculate_delay(1, config) == 4.0  # 2.0 * (1 + 1)
        assert _calculate_delay(2, config) == 6.0  # 2.0 * (2 + 1)
        assert _calculate_delay(3, config) == 8.0  # 2.0 * (3 + 1)

    def test_fixed_delay(self):
        """Test fixed delay calculation."""
        config = RetryConfig(
            base_delay=3.0,
            strategy=RetryStrategy.FIXED_DELAY,
            jitter_factor=0.0,  # No jitter for predictable testing
        )
        
        assert _calculate_delay(0, config) == 3.0
        assert _calculate_delay(1, config) == 3.0
        assert _calculate_delay(2, config) == 3.0
        assert _calculate_delay(10, config) == 3.0

    def test_max_delay_capping(self):
        """Test that delays are capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            jitter_factor=0.0,  # No jitter for predictable testing
        )
        
        # Large attempt should be capped at max_delay
        delay = _calculate_delay(10, config)  # Would be 1024 without capping
        assert delay == 5.0

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        config = RetryConfig(
            base_delay=1.0,
            strategy=RetryStrategy.FIXED_DELAY,
            jitter_factor=0.5,
        )
        
        # Generate multiple delays and verify they're different (due to jitter)
        delays = [_calculate_delay(0, config) for _ in range(10)]
        
        # All delays should be >= base_delay (1.0)
        assert all(d >= 1.0 for d in delays)
        
        # At least some delays should be different (jitter effect)
        # This test might occasionally fail due to randomness, but very unlikely
        assert len(set(delays)) > 1


class TestRetryHandlerSync:
    """Test retry_handler decorator with synchronous functions."""

    def test_successful_function_no_retry(self):
        """Test that successful functions are not retried."""
        config = RetryConfig(max_retries=3)
        call_count = 0
        
        @retry_handler(config)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_configured_exception(self):
        """Test retry behavior on configured exceptions."""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,  # Very small delay for fast tests
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_count = 0
        
        @retry_handler(config)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CustomRetryableError(f"Attempt {call_count}")
            return "success"
        
        with patch('time.sleep') as mock_sleep:
            result = flaky_func()
            
        assert result == "success"
        assert call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2  # Sleep called for each retry

    def test_exhaust_retries_and_fail(self):
        """Test behavior when all retries are exhausted."""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_count = 0
        
        @retry_handler(config)
        def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise CustomRetryableError(f"Attempt {call_count}")
        
        with patch('time.sleep'):
            with pytest.raises(CustomRetryableError) as exc_info:
                always_fail_func()
            
        assert "Attempt 3" in str(exc_info.value)  # Final attempt
        assert call_count == 3  # Initial + 2 retries

    def test_non_retryable_exception_not_retried(self):
        """Test that non-configured exceptions are not retried."""
        config = RetryConfig(
            max_retries=3,
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_count = 0
        
        @retry_handler(config)
        def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("Should not retry")
        
        with pytest.raises(NonRetryableError):
            non_retryable_func()
            
        assert call_count == 1  # No retries

    def test_logging_during_retries(self):
        """Test that retry attempts are logged properly."""
        config = RetryConfig(
            max_retries=1,
            base_delay=0.01,
            retry_on_exceptions=(CustomRetryableError,),
        )
        
        @retry_handler(config)
        def logged_func():
            raise CustomRetryableError("Test error")
        
        with patch('time.sleep'), \
             patch('faciliter_lib.llm.retry.logger') as mock_logger:
            
            with pytest.raises(CustomRetryableError):
                logged_func()
            
            # Verify warning log for retry attempt
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Attempt 1 failed" in warning_call
            assert "Retrying in" in warning_call
            
            # Verify error log for final failure
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "Final attempt failed" in error_call


class TestRetryHandlerAsync:
    """Test retry_handler decorator with asynchronous functions."""

    @pytest.mark.asyncio
    async def test_async_successful_function_no_retry(self):
        """Test that successful async functions are not retried."""
        config = RetryConfig(max_retries=3)
        call_count = 0
        
        @retry_handler(config)
        async def async_success_func():
            nonlocal call_count
            call_count += 1
            return "async success"
        
        result = await async_success_func()
        assert result == "async success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_on_exception(self):
        """Test async retry behavior on configured exceptions."""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_count = 0
        
        @retry_handler(config)
        async def async_flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise CustomRetryableError(f"Async attempt {call_count}")
            return "async success"
        
        with patch('asyncio.sleep') as mock_sleep:
            result = await async_flaky_func()
            
        assert result == "async success"
        assert call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2  # Sleep called for each retry

    @pytest.mark.asyncio
    async def test_async_exhaust_retries_and_fail(self):
        """Test async behavior when all retries are exhausted."""
        config = RetryConfig(
            max_retries=1,
            base_delay=0.01,
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_count = 0
        
        @retry_handler(config)
        async def async_always_fail_func():
            nonlocal call_count
            call_count += 1
            raise CustomRetryableError(f"Async attempt {call_count}")
        
        with patch('asyncio.sleep'):
            with pytest.raises(CustomRetryableError) as exc_info:
                await async_always_fail_func()
            
        assert "Async attempt 2" in str(exc_info.value)  # Final attempt
        assert call_count == 2  # Initial + 1 retry


class TestRetryIntegration:
    """Integration tests for retry functionality."""

    def test_retry_with_different_strategies(self):
        """Test that different retry strategies work correctly."""
        strategies_and_expected_delays = [
            (RetryStrategy.EXPONENTIAL_BACKOFF, [1.0, 2.0, 4.0]),
            (RetryStrategy.LINEAR_BACKOFF, [1.0, 2.0, 3.0]),
            (RetryStrategy.FIXED_DELAY, [1.0, 1.0, 1.0]),
        ]
        
        for strategy, expected_delays in strategies_and_expected_delays:
            config = RetryConfig(
                max_retries=2,
                base_delay=1.0,
                strategy=strategy,
                jitter_factor=0.0,  # No jitter for predictable testing
                retry_on_exceptions=(CustomRetryableError,),
            )
            
            @retry_handler(config)
            def failing_func():
                raise CustomRetryableError("Always fails")
            
            with patch('time.sleep') as mock_sleep:
                with pytest.raises(CustomRetryableError):
                    failing_func()
                
                # Verify sleep was called with expected delays
                expected_calls = [call(delay) for delay in expected_delays[:2]]  # Only first 2 retries
                mock_sleep.assert_has_calls(expected_calls)

    def test_function_arguments_passed_through(self):
        """Test that function arguments are passed through correctly during retries."""
        config = RetryConfig(
            max_retries=1,
            base_delay=0.01,
            retry_on_exceptions=(CustomRetryableError,),
        )
        call_args = []
        
        @retry_handler(config)
        def func_with_args(arg1, arg2, kwarg1=None):
            call_args.append((arg1, arg2, kwarg1))
            if len(call_args) < 2:
                raise CustomRetryableError("First call fails")
            return f"result: {arg1}, {arg2}, {kwarg1}"
        
        with patch('time.sleep'):
            result = func_with_args("test1", "test2", kwarg1="test3")
        
        assert result == "result: test1, test2, test3"
        assert len(call_args) == 2
        # Verify arguments were passed correctly to both calls
        assert call_args[0] == ("test1", "test2", "test3")
        assert call_args[1] == ("test1", "test2", "test3")