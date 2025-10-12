"""Tests for authentication settings configuration.

Tests the AuthSettings class for managing time-based authentication
configuration from environment variables.
"""

import pytest
import os
from unittest.mock import patch

from faciliter_lib.api_utils.auth_settings import AuthSettings
from faciliter_lib.config.base_settings import SettingsError


class TestAuthSettings:
    """Test authentication settings configuration."""
    
    def test_auth_settings_defaults(self):
        """Test default values when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = AuthSettings.from_env(load_dotenv=False)
            
            assert settings.auth_enabled is False
            assert settings.auth_private_key is None
            assert settings.auth_key_header_name == "x-auth-key"
    
    def test_auth_settings_from_env_enabled(self):
        """Test loading settings from environment variables."""
        env = {
            "AUTH_ENABLED": "true",
            "AUTH_PRIVATE_KEY": "my-super-secret-key-12345",
            "AUTH_KEY_HEADER_NAME": "x-custom-auth",
        }
        
        with patch.dict(os.environ, env, clear=True):
            settings = AuthSettings.from_env(load_dotenv=False)
            
            assert settings.auth_enabled is True
            assert settings.auth_private_key == "my-super-secret-key-12345"
            assert settings.auth_key_header_name == "x-custom-auth"
    
    def test_auth_settings_with_overrides(self):
        """Test that overrides take precedence over env vars."""
        env = {
            "AUTH_ENABLED": "false",
            "AUTH_PRIVATE_KEY": "env-key",
        }
        
        with patch.dict(os.environ, env, clear=True):
            settings = AuthSettings.from_env(
                load_dotenv=False,
                auth_enabled=True,
                auth_private_key="override-key"
            )
            
            assert settings.auth_enabled is True
            assert settings.auth_private_key == "override-key"
    
    def test_validation_fails_when_enabled_without_key(self):
        """Test validation error when auth is enabled but no key provided."""
        with pytest.raises(SettingsError, match="AUTH_PRIVATE_KEY must be set"):
            AuthSettings(
                auth_enabled=True,
                auth_private_key=None
            )
    
    def test_validation_fails_when_enabled_with_empty_key(self):
        """Test validation error when auth is enabled with empty key."""
        with pytest.raises(SettingsError, match="AUTH_PRIVATE_KEY must be set"):
            AuthSettings(
                auth_enabled=True,
                auth_private_key=""
            )
    
    def test_validation_fails_when_enabled_with_whitespace_key(self):
        """Test validation error when auth is enabled with whitespace key."""
        with pytest.raises(SettingsError, match="AUTH_PRIVATE_KEY must be set"):
            AuthSettings(
                auth_enabled=True,
                auth_private_key="   "
            )
    
    def test_validation_fails_when_key_too_short(self):
        """Test validation error when private key is too short."""
        with pytest.raises(SettingsError, match="at least 16 characters"):
            AuthSettings(
                auth_enabled=True,
                auth_private_key="short"
            )
    
    def test_validation_passes_when_disabled_without_key(self):
        """Test validation passes when auth is disabled even without key."""
        settings = AuthSettings(
            auth_enabled=False,
            auth_private_key=None
        )
        
        assert settings.is_valid
    
    def test_validation_passes_with_valid_key(self):
        """Test validation passes with valid key."""
        settings = AuthSettings(
            auth_enabled=True,
            auth_private_key="my-super-secret-key-12345"
        )
        
        assert settings.is_valid
    
    def test_validation_fails_with_empty_header_name(self):
        """Test validation error when header name is empty."""
        with pytest.raises(SettingsError, match="auth_key_header_name cannot be empty"):
            AuthSettings(
                auth_enabled=False,
                auth_key_header_name=""
            )
    
    def test_as_dict_masks_private_key(self):
        """Test that as_dict masks the private key for security."""
        settings = AuthSettings(
            auth_enabled=True,
            auth_private_key="my-super-secret-key-12345",
            auth_key_header_name="x-auth"
        )
        
        settings_dict = settings.as_dict()
        
        assert settings_dict["auth_enabled"] is True
        assert settings_dict["auth_private_key"] == "***"  # Masked
        assert settings_dict["auth_key_header_name"] == "x-auth"
    
    def test_as_dict_with_no_key(self):
        """Test as_dict when no private key is set."""
        settings = AuthSettings(
            auth_enabled=False,
            auth_private_key=None
        )
        
        settings_dict = settings.as_dict()
        
        assert settings_dict["auth_enabled"] is False
        assert settings_dict["auth_private_key"] is None
    
    def test_auth_enabled_boolean_parsing(self):
        """Test that AUTH_ENABLED correctly parses boolean values."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"AUTH_ENABLED": env_value}, clear=True):
                settings = AuthSettings.from_env(load_dotenv=False)
                assert settings.auth_enabled == expected, f"Failed for {env_value}"
    
    def test_minimum_key_length_boundary(self):
        """Test key length validation at boundary (15 vs 16 chars)."""
        # 15 characters - should fail
        with pytest.raises(SettingsError, match="at least 16 characters"):
            AuthSettings(
                auth_enabled=True,
                auth_private_key="a" * 15
            )
        
        # 16 characters - should pass
        settings = AuthSettings(
            auth_enabled=True,
            auth_private_key="a" * 16
        )
        assert settings.is_valid
    
    def test_settings_immutable(self):
        """Test that settings are immutable (frozen dataclass)."""
        settings = AuthSettings(
            auth_enabled=True,
            auth_private_key="my-super-secret-key-12345"
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            settings.auth_enabled = False  # type: ignore
