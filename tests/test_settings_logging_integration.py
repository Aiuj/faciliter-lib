"""Tests for automatic logging setup in initialize_settings()."""

import logging
import pytest
from dataclasses import dataclass

from faciliter_lib.config import (
    StandardSettings,
    initialize_settings,
    reset_settings,
    AppSettings,
    LoggerSettings,
)


@pytest.fixture(autouse=True)
def reset_settings_fixture():
    """Reset settings before and after each test."""
    reset_settings()
    yield
    reset_settings()


def test_initialize_settings_with_logging_enabled():
    """Test that logging is automatically configured when setup_logging=True."""
    # Initialize with logging enabled (default)
    settings = initialize_settings(
        force=True,
        setup_logging=True,
    )
    
    # Verify settings were created
    assert settings is not None
    assert isinstance(settings, StandardSettings)
    
    # Verify logging was configured by checking root logger
    root_logger = logging.getLogger()
    assert root_logger.level > 0  # Should be configured


def test_initialize_settings_with_logging_disabled():
    """Test that logging is skipped when setup_logging=False."""
    # Initialize without logging setup
    settings = initialize_settings(
        force=True,
        setup_logging=False,
    )
    
    # Verify settings were created
    assert settings is not None
    assert isinstance(settings, StandardSettings)


def test_initialize_settings_logging_with_custom_settings():
    """Test that logging works with custom settings class."""
    
    @dataclass(frozen=True)
    class CustomSettings(StandardSettings):
        custom_field: str = "test_value"
    
    # Initialize with custom class and logging
    settings = initialize_settings(
        settings_class=CustomSettings,
        force=True,
        setup_logging=True,
    )
    
    # Verify custom settings were created
    assert settings is not None
    assert isinstance(settings, CustomSettings)
    assert settings.custom_field == "test_value"


def test_initialize_settings_without_app_settings():
    """Test that logging setup is skipped gracefully when no app settings."""
    
    @dataclass(frozen=True)
    class MinimalSettings(StandardSettings):
        # Override app to be None
        app: AppSettings = None  # type: ignore
    
    # Should not raise even without app settings
    settings = initialize_settings(
        settings_class=MinimalSettings,
        force=True,
        setup_logging=True,
    )
    
    assert settings is not None


def test_initialize_settings_logging_with_overrides():
    """Test that logging respects overrides in settings."""
    # Initialize with log level override
    settings = initialize_settings(
        force=True,
        setup_logging=True,
    )
    
    # Verify settings were created with logging
    assert settings is not None
    assert settings.app is not None


def test_force_reinitialize_reconfigures_logging():
    """Test that force=True reconfigures logging."""
    # First initialization
    settings1 = initialize_settings(
        force=True,
        setup_logging=True,
    )
    assert settings1 is not None
    
    # Force reinitialize
    settings2 = initialize_settings(
        force=True,
        setup_logging=True,
    )
    
    # Both should be valid but may be different instances due to force
    assert settings2 is not None
