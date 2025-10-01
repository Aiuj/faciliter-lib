"""
Tests for settings singleton manager.

Tests the thread-safe singleton pattern implementation for managing
StandardSettings instances across an application lifecycle.
"""

import pytest
import threading
from dataclasses import dataclass
from typing import Optional

from faciliter_lib.config import (
    StandardSettings,
    SettingsSingletonManager,
    initialize_settings,
    get_settings,
    set_settings,
    reset_settings,
    has_settings,
    get_settings_safe,
    SettingsError,
)


@dataclass(frozen=True)
class CustomSettings(StandardSettings):
    """Custom settings for testing."""
    custom_field: str = "custom_value"
    another_field: int = 42


class TestSettingsSingletonManager:
    """Test the SettingsSingletonManager class."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_initialize_settings_default(self):
        """Test initializing with default StandardSettings."""
        settings = SettingsSingletonManager.initialize_settings()
        
        assert settings is not None
        assert isinstance(settings, StandardSettings)
        assert SettingsSingletonManager.has_settings()
    
    def test_initialize_settings_custom_class(self):
        """Test initializing with custom Settings class."""
        settings = SettingsSingletonManager.initialize_settings(
            settings_class=CustomSettings
        )
        
        assert settings is not None
        assert isinstance(settings, CustomSettings)
        assert settings.custom_field == "custom_value"
        assert settings.another_field == 42
    
    def test_initialize_settings_with_overrides(self):
        """Test initializing with override values."""
        settings = SettingsSingletonManager.initialize_settings(
            app_name="test-app",
            log_level="DEBUG"
        )
        
        assert settings.app_name == "test-app"
        assert settings.log_level == "DEBUG"
    
    def test_get_settings_before_initialization(self):
        """Test getting settings before initialization raises error."""
        with pytest.raises(SettingsError, match="not initialized"):
            SettingsSingletonManager.get_settings()
    
    def test_get_settings_after_initialization(self):
        """Test getting settings after initialization."""
        initialized = SettingsSingletonManager.initialize_settings(
            app_name="test-app"
        )
        retrieved = SettingsSingletonManager.get_settings()
        
        assert retrieved is initialized
        assert retrieved.app_name == "test-app"
    
    def test_initialize_twice_returns_same_instance(self):
        """Test that initializing twice returns the same instance."""
        first = SettingsSingletonManager.initialize_settings(app_name="first")
        second = SettingsSingletonManager.initialize_settings(app_name="second")
        
        assert first is second
        assert first.app_name == "first"  # Original values preserved
    
    def test_initialize_twice_different_class_raises_error(self):
        """Test that initializing with different class raises error."""
        SettingsSingletonManager.initialize_settings(
            settings_class=StandardSettings
        )
        
        with pytest.raises(SettingsError, match="already initialized with different class"):
            SettingsSingletonManager.initialize_settings(
                settings_class=CustomSettings
            )
    
    def test_initialize_with_force_reinitializes(self):
        """Test that force=True allows reinitialization."""
        first = SettingsSingletonManager.initialize_settings(app_name="first")
        second = SettingsSingletonManager.initialize_settings(
            app_name="second",
            force=True
        )
        
        assert first is not second
        assert second.app_name == "second"
    
    def test_set_settings(self):
        """Test directly setting a settings instance."""
        custom = CustomSettings.from_env(app_name="custom-app")
        SettingsSingletonManager.set_settings(custom)
        
        retrieved = SettingsSingletonManager.get_settings()
        assert retrieved is custom
        assert retrieved.app_name == "custom-app"
    
    def test_set_settings_invalid_type(self):
        """Test that setting invalid type raises error."""
        with pytest.raises(TypeError, match="must be a StandardSettings instance"):
            SettingsSingletonManager.set_settings("not a settings object")  # type: ignore
    
    def test_reset_settings(self):
        """Test resetting settings."""
        SettingsSingletonManager.initialize_settings(app_name="test")
        assert SettingsSingletonManager.has_settings()
        
        SettingsSingletonManager.reset_settings()
        
        assert not SettingsSingletonManager.has_settings()
        with pytest.raises(SettingsError):
            SettingsSingletonManager.get_settings()
    
    def test_has_settings(self):
        """Test has_settings check."""
        assert not SettingsSingletonManager.has_settings()
        
        SettingsSingletonManager.initialize_settings()
        assert SettingsSingletonManager.has_settings()
        
        SettingsSingletonManager.reset_settings()
        assert not SettingsSingletonManager.has_settings()
    
    def test_get_settings_safe(self):
        """Test safe settings retrieval."""
        # Before initialization
        settings = SettingsSingletonManager.get_settings_safe()
        assert settings is None
        
        # After initialization
        SettingsSingletonManager.initialize_settings(app_name="test")
        settings = SettingsSingletonManager.get_settings_safe()
        assert settings is not None
        assert settings.app_name == "test"
        
        # After reset
        SettingsSingletonManager.reset_settings()
        settings = SettingsSingletonManager.get_settings_safe()
        assert settings is None
    
    def test_thread_safety(self):
        """Test that singleton is thread-safe."""
        results = []
        errors = []
        
        def init_settings(thread_id: int):
            try:
                settings = SettingsSingletonManager.initialize_settings(
                    app_name=f"thread-{thread_id}"
                )
                results.append((thread_id, settings))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create multiple threads that try to initialize simultaneously
        threads = [
            threading.Thread(target=init_settings, args=(i,))
            for i in range(10)
        ]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All threads should get the same instance
        assert len(results) == 10
        first_settings = results[0][1]
        for thread_id, settings in results:
            assert settings is first_settings
        
        # No errors should occur
        assert len(errors) == 0


class TestFactoryFunctions:
    """Test the factory functions for convenience."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_initialize_settings_function(self):
        """Test initialize_settings factory function."""
        settings = initialize_settings(app_name="factory-test")
        
        assert settings.app_name == "factory-test"
        assert has_settings()
    
    def test_get_settings_function(self):
        """Test get_settings factory function."""
        initialize_settings(app_name="get-test")
        settings = get_settings()
        
        assert settings.app_name == "get-test"
    
    def test_set_settings_function(self):
        """Test set_settings factory function."""
        custom = CustomSettings.from_env(app_name="set-test")
        set_settings(custom)
        
        settings = get_settings()
        assert settings is custom
    
    def test_reset_settings_function(self):
        """Test reset_settings factory function."""
        initialize_settings()
        assert has_settings()
        
        reset_settings()
        assert not has_settings()
    
    def test_has_settings_function(self):
        """Test has_settings factory function."""
        assert not has_settings()
        initialize_settings()
        assert has_settings()
    
    def test_get_settings_safe_function(self):
        """Test get_settings_safe factory function."""
        assert get_settings_safe() is None
        
        initialize_settings(app_name="safe-test")
        settings = get_settings_safe()
        assert settings is not None
        assert settings.app_name == "safe-test"


class TestRealWorldUsage:
    """Test real-world usage patterns."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_lazy_initialization_pattern(self):
        """Test lazy initialization pattern."""
        def get_app_config():
            if not has_settings():
                initialize_settings(app_name="lazy-app")
            return get_settings()
        
        # First call initializes
        config1 = get_app_config()
        assert config1.app_name == "lazy-app"
        
        # Second call returns existing
        config2 = get_app_config()
        assert config1 is config2
    
    def test_application_startup_pattern(self):
        """Test typical application startup pattern."""
        # Application startup
        settings = initialize_settings(
            app_name="my-app",
            log_level="INFO",
            enable_cache=True
        )
        
        # Different parts of the app can access settings
        def module_a():
            config = get_settings()
            return config.app_name
        
        def module_b():
            config = get_settings()
            return config.log_level
        
        assert module_a() == "my-app"
        assert module_b() == "INFO"
    
    def test_testing_pattern_with_reset(self):
        """Test pattern for testing with different configurations."""
        # Test with config A
        initialize_settings(app_name="config-a", log_level="DEBUG")
        assert get_settings().log_level == "DEBUG"
        
        # Reset for test with config B
        reset_settings()
        initialize_settings(app_name="config-b", log_level="INFO")
        assert get_settings().log_level == "INFO"
    
    def test_custom_settings_class_pattern(self):
        """Test using custom settings class."""
        @dataclass(frozen=True)
        class AppSettings(StandardSettings):
            api_key: str = "default-key"
            max_retries: int = 3
        
        # Initialize with custom class
        settings = initialize_settings(
            settings_class=AppSettings,
            api_key="real-key",
            max_retries=5
        )
        
        # Access throughout the app
        config = get_settings()
        assert isinstance(config, AppSettings)
        assert config.api_key == "real-key"
        assert config.max_retries == 5
    
    def test_conditional_initialization_pattern(self):
        """Test conditional initialization based on environment."""
        # Simulate different environments
        def init_for_environment(env: str):
            if env == "test":
                initialize_settings(
                    app_name="test-app",
                    log_level="DEBUG",
                    enable_cache=False
                )
            elif env == "prod":
                initialize_settings(
                    app_name="prod-app",
                    log_level="INFO",
                    enable_cache=True
                )
        
        # Test environment
        init_for_environment("test")
        assert get_settings().log_level == "DEBUG"
        assert not get_settings().enable_cache
        
        # Switch to prod
        reset_settings()
        init_for_environment("prod")
        assert get_settings().log_level == "INFO"
        assert get_settings().enable_cache
