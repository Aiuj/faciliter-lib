"""
Example: Using Settings Singleton Manager

Demonstrates how to use the Settings Singleton Manager pattern in faciliter-lib
for managing application-wide configuration with custom settings.
"""

from dataclasses import dataclass
from faciliter_lib.config import (
    StandardSettings,
    initialize_settings,
    get_settings,
    reset_settings,
    has_settings,
)


# Example 1: Basic usage with StandardSettings
def example_basic_usage():
    """Basic singleton pattern usage."""
    print("\n=== Example 1: Basic Usage ===")
    
    # Initialize settings at application startup
    settings = initialize_settings(
        app_name="example-app",
        log_level="DEBUG",
        enable_cache=True,
        enable_llm=True
    )
    
    print(f"Initialized: {settings.app_name}")
    print(f"Log Level: {settings.log_level}")
    print(f"Cache Enabled: {settings.enable_cache}")
    
    # Access settings from anywhere in the application
    config = get_settings()
    print(f"Retrieved: {config.app_name}")
    
    # Verify it's the same instance
    print(f"Same instance: {settings is config}")
    
    # Clean up
    reset_settings()


# Example 2: Custom Settings Class
@dataclass(frozen=True)
class MyAppSettings(StandardSettings):
    """Custom settings for my application."""
    api_key: str = "default-key"
    max_retries: int = 3
    timeout_seconds: float = 30.0
    feature_flag_x: bool = False


def example_custom_settings():
    """Using a custom settings class."""
    print("\n=== Example 2: Custom Settings Class ===")
    
    # Initialize with custom class
    settings = initialize_settings(
        settings_class=MyAppSettings,
        app_name="custom-app",
        api_key="my-secret-key",
        max_retries=5,
        feature_flag_x=True
    )
    
    print(f"App Name: {settings.app_name}")
    print(f"API Key: {settings.api_key}")
    print(f"Max Retries: {settings.max_retries}")
    print(f"Feature Flag X: {settings.feature_flag_x}")
    
    # Access from another function
    def process_data():
        config = get_settings()
        print(f"Processing with {config.max_retries} retries")
        return config
    
    retrieved = process_data()
    print(f"Same instance: {settings is retrieved}")
    
    # Clean up
    reset_settings()


# Example 3: Lazy Initialization
def get_config():
    """Get config with lazy initialization."""
    if not has_settings():
        print("Settings not initialized, initializing now...")
        initialize_settings(app_name="lazy-app")
    return get_settings()


def example_lazy_initialization():
    """Lazy initialization pattern."""
    print("\n=== Example 3: Lazy Initialization ===")
    
    # First access initializes
    config1 = get_config()
    print(f"First access: {config1.app_name}")
    
    # Second access uses existing
    config2 = get_config()
    print(f"Second access: {config2.app_name}")
    print(f"Same instance: {config1 is config2}")
    
    # Clean up
    reset_settings()


# Example 4: Environment-Specific Configuration
def init_for_environment(env: str):
    """Initialize settings based on environment."""
    print(f"\nInitializing for {env} environment...")
    
    if env == "production":
        initialize_settings(
            app_name="prod-app",
            log_level="INFO",
            enable_cache=True,
            enable_tracing=True
        )
    elif env == "staging":
        initialize_settings(
            app_name="staging-app",
            log_level="DEBUG",
            enable_cache=True,
            enable_tracing=True
        )
    else:  # development
        initialize_settings(
            app_name="dev-app",
            log_level="DEBUG",
            enable_cache=False,
            enable_tracing=False
        )


def example_environment_specific():
    """Environment-specific configuration."""
    print("\n=== Example 4: Environment-Specific Configuration ===")
    
    # Development environment
    init_for_environment("development")
    dev_config = get_settings()
    print(f"Dev - App: {dev_config.app_name}, Log: {dev_config.log_level}, Cache: {dev_config.enable_cache}")
    
    # Switch to production
    reset_settings()
    init_for_environment("production")
    prod_config = get_settings()
    print(f"Prod - App: {prod_config.app_name}, Log: {prod_config.log_level}, Cache: {prod_config.enable_cache}")
    
    # Clean up
    reset_settings()


# Example 5: Application Modules Pattern
class DatabaseModule:
    """Example module that uses settings."""
    
    def connect(self):
        config = get_settings()
        print(f"[DB] Connecting with app: {config.app_name}")
        print(f"[DB] Log level: {config.log_level}")


class CacheModule:
    """Another example module."""
    
    def initialize(self):
        config = get_settings()
        print(f"[Cache] Initializing for app: {config.app_name}")
        print(f"[Cache] Enabled: {config.enable_cache}")


def example_multi_module_access():
    """Multiple modules accessing the same settings."""
    print("\n=== Example 5: Multi-Module Access ===")
    
    # Initialize once at startup
    initialize_settings(
        app_name="multi-module-app",
        log_level="INFO",
        enable_cache=True
    )
    
    # Different modules access the same config
    db = DatabaseModule()
    db.connect()
    
    cache = CacheModule()
    cache.initialize()
    
    # Clean up
    reset_settings()


# Example 6: Testing Pattern
def example_testing_pattern():
    """Pattern for testing with different configurations."""
    print("\n=== Example 6: Testing Pattern ===")
    
    # Test case 1: Debug configuration
    print("\nTest Case 1:")
    initialize_settings(log_level="DEBUG", enable_cache=False)
    assert get_settings().log_level == "DEBUG"
    assert not get_settings().enable_cache
    print("Test 1 passed with DEBUG logging")
    
    # Reset for test case 2
    reset_settings()
    
    # Test case 2: Info configuration
    print("\nTest Case 2:")
    initialize_settings(log_level="INFO", enable_cache=True)
    assert get_settings().log_level == "INFO"
    assert get_settings().enable_cache
    print("Test 2 passed with INFO logging")
    
    # Clean up
    reset_settings()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Settings Singleton Manager Examples")
    print("=" * 60)
    
    example_basic_usage()
    example_custom_settings()
    example_lazy_initialization()
    example_environment_specific()
    example_multi_module_access()
    example_testing_pattern()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
