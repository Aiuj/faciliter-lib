"""Tests for LoggerSettings and OVH LDP integration."""

import os
import pytest
from unittest.mock import MagicMock, patch

from faciliter_lib.config import LoggerSettings
from faciliter_lib.config.base_settings import SettingsError


class TestLoggerSettings:
    """Tests for LoggerSettings configuration."""
    
    def test_logger_settings_defaults(self):
        """Test default LoggerSettings values."""
        settings = LoggerSettings()
        
        assert settings.log_level == "INFO"
        assert settings.file_logging is False
        assert settings.ovh_ldp_enabled is False
        assert settings.ovh_ldp_port == 12202
        assert settings.ovh_ldp_protocol == "gelf_tcp"
        assert settings.ovh_ldp_use_tls is True
        assert settings.ovh_ldp_compress is True
    
    def test_logger_settings_from_env(self, monkeypatch):
        """Test loading LoggerSettings from environment variables."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOG_FILE_ENABLED", "true")
        monkeypatch.setenv("LOG_FILE_PATH", "logs/test.log")
        monkeypatch.setenv("OVH_LDP_ENABLED", "true")
        monkeypatch.setenv("OVH_LDP_TOKEN", "test-token")
        monkeypatch.setenv("OVH_LDP_ENDPOINT", "gra1.logs.ovh.com")
        monkeypatch.setenv("OVH_LDP_PORT", "12345")
        monkeypatch.setenv("OVH_LDP_PROTOCOL", "gelf_udp")
        
        settings = LoggerSettings.from_env(load_dotenv=False)
        
        assert settings.log_level == "DEBUG"
        assert settings.file_logging is True
        assert settings.file_path == "logs/test.log"
        assert settings.ovh_ldp_enabled is True
        assert settings.ovh_ldp_token == "test-token"
        assert settings.ovh_ldp_endpoint == "gra1.logs.ovh.com"
        assert settings.ovh_ldp_port == 12345
        assert settings.ovh_ldp_protocol == "gelf_udp"
    
    def test_logger_settings_additional_fields_parsing(self, monkeypatch):
        """Test parsing of additional fields from JSON."""
        monkeypatch.setenv("OVH_LDP_ADDITIONAL_FIELDS", '{"env": "prod", "version": "1.0"}')
        
        settings = LoggerSettings.from_env(load_dotenv=False)
        
        assert settings.ovh_ldp_additional_fields == {"env": "prod", "version": "1.0"}
    
    def test_logger_settings_invalid_json_additional_fields(self, monkeypatch):
        """Test handling of invalid JSON in additional fields."""
        monkeypatch.setenv("OVH_LDP_ADDITIONAL_FIELDS", "invalid-json")
        
        settings = LoggerSettings.from_env(load_dotenv=False)
        
        # Should default to empty dict on invalid JSON
        assert settings.ovh_ldp_additional_fields == {}
    
    def test_logger_settings_validation_invalid_log_level(self):
        """Test validation rejects invalid log level."""
        with pytest.raises(SettingsError, match="Invalid log level"):
            settings = LoggerSettings(log_level="INVALID")
    
    def test_logger_settings_validation_missing_token(self):
        """Test validation requires token when OVH LDP is enabled."""
        with pytest.raises(SettingsError, match="ovh_ldp_token not provided"):
            settings = LoggerSettings(
                ovh_ldp_enabled=True,
                ovh_ldp_endpoint="gra1.logs.ovh.com"
            )
    
    def test_logger_settings_validation_missing_endpoint(self):
        """Test validation requires endpoint when OVH LDP is enabled."""
        with pytest.raises(SettingsError, match="ovh_ldp_endpoint not provided"):
            settings = LoggerSettings(
                ovh_ldp_enabled=True,
                ovh_ldp_token="token"
            )
    
    def test_logger_settings_validation_invalid_protocol(self):
        """Test validation rejects invalid protocol."""
        with pytest.raises(SettingsError, match="Invalid OVH LDP protocol"):
            settings = LoggerSettings(
                ovh_ldp_enabled=True,
                ovh_ldp_token="token",
                ovh_ldp_endpoint="gra1.logs.ovh.com",
                ovh_ldp_protocol="invalid"
            )
    
    def test_logger_settings_validation_invalid_port(self):
        """Test validation rejects invalid port."""
        with pytest.raises(SettingsError, match="Invalid port"):
            settings = LoggerSettings(
                ovh_ldp_enabled=True,
                ovh_ldp_token="token",
                ovh_ldp_endpoint="gra1.logs.ovh.com",
                ovh_ldp_port=99999
            )
    
    def test_logger_settings_validation_invalid_timeout(self):
        """Test validation rejects invalid timeout."""
        with pytest.raises(SettingsError, match="timeout must be at least 1"):
            settings = LoggerSettings(
                ovh_ldp_enabled=True,
                ovh_ldp_token="token",
                ovh_ldp_endpoint="gra1.logs.ovh.com",
                ovh_ldp_timeout=0
            )
    
    def test_logger_settings_as_dict_masks_token(self):
        """Test that as_dict masks the token."""
        settings = LoggerSettings(
            ovh_ldp_enabled=True,
            ovh_ldp_token="secret-token",
            ovh_ldp_endpoint="gra1.logs.ovh.com"
        )
        
        settings_dict = settings.as_dict()
        
        assert settings_dict["ovh_ldp_token"] == "***"
        assert settings_dict["ovh_ldp_endpoint"] == "gra1.logs.ovh.com"


class TestLoggerIntegration:
    """Tests for logger integration with OVH LDP."""
    
    @patch('faciliter_lib.tracing.handlers.gelf_handler.GELFTCPHandler')
    def test_setup_logging_with_ovh_ldp(self, mock_gelf_handler):
        """Test setup_logging with OVH LDP enabled."""
        from faciliter_lib.tracing.logger import setup_logging
        
        logger_settings = LoggerSettings(
            log_level="INFO",
            ovh_ldp_enabled=True,
            ovh_ldp_token="test-token",
            ovh_ldp_endpoint="gra1.logs.ovh.com",
            ovh_ldp_port=12202,
            ovh_ldp_protocol="gelf_tcp",
            ovh_ldp_use_tls=True,
            ovh_ldp_compress=True,
            ovh_ldp_additional_fields={"env": "test"},
            ovh_ldp_timeout=10,
        )
        
        logger = setup_logging(
            app_name="test_app",
            logger_settings=logger_settings,
            force=True
        )
        
        # Verify GELF handler was created with correct params
        mock_gelf_handler.assert_called_once_with(
            host="gra1.logs.ovh.com",
            port=12202,
            token="test-token",
            use_tls=True,
            compress=True,
            additional_fields={"env": "test"},
            timeout=10,
        )
        
        assert logger is not None
    
    def test_setup_logging_without_ovh_ldp(self):
        """Test setup_logging works without OVH LDP."""
        from faciliter_lib.tracing.logger import setup_logging
        
        logger_settings = LoggerSettings(
            log_level="INFO",
            ovh_ldp_enabled=False
        )
        
        logger = setup_logging(
            app_name="test_app",
            logger_settings=logger_settings,
            force=True
        )
        
        assert logger is not None
    
    def test_setup_logging_uses_logger_settings_level(self):
        """Test that logger settings level takes precedence."""
        from faciliter_lib.tracing.logger import setup_logging
        
        logger_settings = LoggerSettings(log_level="DEBUG")
        
        logger = setup_logging(
            app_name="test_app",
            logger_settings=logger_settings,
            force=True
        )
        
        # Logger should be at DEBUG level
        assert logger.level == 10  # DEBUG = 10


class TestStandardSettingsWithLogger:
    """Tests for StandardSettings integration with LoggerSettings."""
    
    def test_standard_settings_auto_detects_logger(self, monkeypatch):
        """Test that StandardSettings auto-detects logger config."""
        monkeypatch.setenv("OVH_LDP_ENABLED", "true")
        monkeypatch.setenv("OVH_LDP_TOKEN", "token")
        monkeypatch.setenv("OVH_LDP_ENDPOINT", "gra1.logs.ovh.com")
        
        from faciliter_lib.config import StandardSettings
        
        settings = StandardSettings.from_env(load_dotenv=False)
        
        assert settings.enable_logger is True
        assert settings.logger is not None
        assert settings.logger.ovh_ldp_enabled is True
        assert settings.logger.ovh_ldp_token == "token"
    
    def test_standard_settings_logger_disabled_by_default(self):
        """Test that logger is not enabled by default."""
        from faciliter_lib.config import StandardSettings
        
        settings = StandardSettings.from_env(load_dotenv=False)
        
        # Should be disabled if no OVH LDP vars set
        assert settings.enable_logger is False or settings.logger is None
    
    def test_standard_settings_logger_safe_property(self, monkeypatch):
        """Test logger_safe property returns NullConfig when logger is None."""
        from faciliter_lib.config import StandardSettings
        
        settings = StandardSettings.from_env(load_dotenv=False)
        
        # Should not raise even if logger is None
        logger_safe = settings.logger_safe
        assert logger_safe is not None
        
        # NullConfig returns None for any attribute
        assert logger_safe.ovh_ldp_enabled is None
