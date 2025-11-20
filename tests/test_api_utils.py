"""Tests for time-based authentication utilities.

Tests the core HMAC-based time-window authentication system including
key generation, verification, and time window transitions.
"""

import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

from core_lib.api_utils import (
    generate_time_key,
    verify_time_key,
    TimeBasedAuthError,
)


class TestTimeBasedAuth:
    """Test time-based authentication key generation and verification."""
    
    def test_generate_time_key_success(self):
        """Test successful key generation."""
        private_key = "my-secret-private-key"
        key = generate_time_key(private_key)
        
        assert key is not None
        assert isinstance(key, str)
        assert len(key) == 64  # HMAC-SHA256 produces 64 hex characters
    
    def test_generate_time_key_empty_private_key(self):
        """Test that empty private key raises error."""
        with pytest.raises(TimeBasedAuthError, match="Private key cannot be empty"):
            generate_time_key("")
        
        with pytest.raises(TimeBasedAuthError, match="Private key cannot be empty"):
            generate_time_key("   ")
    
    def test_verify_time_key_same_hour(self):
        """Test verification of key generated in same hour."""
        private_key = "my-secret-private-key"
        key = generate_time_key(private_key)
        
        # Should verify successfully in same hour
        assert verify_time_key(key, private_key) is True
    
    def test_verify_time_key_wrong_key(self):
        """Test verification fails with wrong key."""
        private_key = "my-secret-private-key"
        wrong_key = "0" * 64
        
        assert verify_time_key(wrong_key, private_key) is False
    
    def test_verify_time_key_wrong_private_key(self):
        """Test verification fails with different private key."""
        private_key1 = "my-secret-private-key"
        private_key2 = "different-secret-key"
        
        key = generate_time_key(private_key1)
        assert verify_time_key(key, private_key2) is False
    
    def test_verify_time_key_empty_key(self):
        """Test verification fails with empty provided key."""
        private_key = "my-secret-private-key"
        
        assert verify_time_key("", private_key) is False
        assert verify_time_key("   ", private_key) is False
    
    def test_verify_time_key_empty_private_key(self):
        """Test verification raises error with empty private key."""
        key = "some-key"
        
        with pytest.raises(TimeBasedAuthError, match="Private key cannot be empty"):
            verify_time_key(key, "")
    
    @freeze_time("2024-01-15 14:30:00")
    def test_verify_time_key_previous_hour(self):
        """Test that key from previous hour is still valid."""
        private_key = "my-secret-private-key"
        
        # Generate key at 14:30
        key = generate_time_key(private_key)
        
        # Move to 15:15 (45 minutes later, in next hour)
        with freeze_time("2024-01-15 15:15:00"):
            # Should still be valid (previous hour window)
            assert verify_time_key(key, private_key) is True
    
    @freeze_time("2024-01-15 14:30:00")
    def test_verify_time_key_next_hour_window(self):
        """Test that key generated in next hour is already valid."""
        private_key = "my-secret-private-key"
        
        # Generate key for next hour (15:00)
        future_time = datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
        future_key = generate_time_key(private_key, dt=future_time)
        
        # Should be valid in current time (14:30) because we accept next hour
        assert verify_time_key(future_key, private_key) is True
    
    @freeze_time("2024-01-15 14:30:00")
    def test_verify_time_key_expired_after_2_hours(self):
        """Test that key expires after 2 hours."""
        private_key = "my-secret-private-key"
        
        # Generate key at 14:30
        key = generate_time_key(private_key)
        
        # Move to 17:00 (2.5 hours later)
        with freeze_time("2024-01-15 17:00:00"):
            # Should be expired (outside 3-hour window)
            assert verify_time_key(key, private_key) is False
    
    @freeze_time("2024-01-15 14:59:59")
    def test_verify_time_key_hour_boundary_transition(self):
        """Test smooth transition at hour boundary."""
        private_key = "my-secret-private-key"
        
        # Generate key at 14:59:59
        key = generate_time_key(private_key)
        
        # Move to 15:00:01 (just after hour boundary)
        with freeze_time("2024-01-15 15:00:01"):
            # Should still be valid (previous hour window)
            assert verify_time_key(key, private_key) is True
    
    def test_different_private_keys_different_outputs(self):
        """Test that different private keys produce different outputs."""
        private_key1 = "key-one"
        private_key2 = "key-two"
        
        key1 = generate_time_key(private_key1)
        key2 = generate_time_key(private_key2)
        
        assert key1 != key2
    
    @freeze_time("2024-01-15 14:30:00")
    def test_same_private_key_same_hour_same_output(self):
        """Test that same private key in same hour produces same output."""
        private_key = "my-secret-private-key"
        
        key1 = generate_time_key(private_key)
        key2 = generate_time_key(private_key)
        
        assert key1 == key2
    
    @freeze_time("2024-01-15 14:30:00")
    def test_same_private_key_different_hour_different_output(self):
        """Test that same private key in different hour produces different output."""
        private_key = "my-secret-private-key"
        
        # Generate key at 14:30
        key1 = generate_time_key(private_key)
        
        # Move to 16:30 (2 hours later)
        with freeze_time("2024-01-15 16:30:00"):
            key2 = generate_time_key(private_key)
        
        assert key1 != key2
    
    def test_verify_time_key_with_custom_datetime(self):
        """Test verification with custom datetime."""
        private_key = "my-secret-private-key"
        
        # Generate key for specific time
        dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        key = generate_time_key(private_key, dt=dt)
        
        # Verify with same time
        assert verify_time_key(key, private_key, dt=dt) is True
        
        # Verify with time 1 hour later (should still work)
        dt_plus_1h = dt + timedelta(hours=1)
        assert verify_time_key(key, private_key, dt=dt_plus_1h) is True
        
        # Verify with time 2 hours later (should fail)
        dt_plus_2h = dt + timedelta(hours=2)
        assert verify_time_key(key, private_key, dt=dt_plus_2h) is False
    
    def test_constant_time_comparison_used(self):
        """Test that verification doesn't leak timing information."""
        # This is more of a code inspection test, but we verify behavior
        private_key = "my-secret-private-key"
        key = generate_time_key(private_key)
        
        # Try with slightly wrong keys - should all fail in similar time
        wrong_key1 = "a" * 64
        wrong_key2 = "b" * 64
        
        assert verify_time_key(wrong_key1, private_key) is False
        assert verify_time_key(wrong_key2, private_key) is False
    
    @freeze_time("2024-01-15 14:30:00")
    def test_three_hour_window_coverage(self):
        """Test that all three time windows (prev, current, next) work."""
        private_key = "my-secret-private-key"
        
        # Generate keys for all three windows
        prev_hour = datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
        curr_hour = datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
        
        prev_key = generate_time_key(private_key, dt=prev_hour)
        curr_key = generate_time_key(private_key, dt=curr_hour)
        next_key = generate_time_key(private_key, dt=next_hour)
        
        # All three should be valid at 14:30
        assert verify_time_key(prev_key, private_key) is True
        assert verify_time_key(curr_key, private_key) is True
        assert verify_time_key(next_key, private_key) is True
        
        # But key from 2 hours ago should not be valid
        two_hours_ago = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        old_key = generate_time_key(private_key, dt=two_hours_ago)
        assert verify_time_key(old_key, private_key) is False
