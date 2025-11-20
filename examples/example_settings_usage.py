"""
Settings Management Examples

This module demonstrates practical usage of the Core settings management system
with real-world scenarios and patterns.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

# Example 1: Basic Usage
def example_basic_usage():
    """Demonstrate basic settings usage."""
    print("=== Example 1: Basic Settings Usage ===")
    
    from core_lib.config import StandardSettings
    
    # Load settings from environment (will look for .env files automatically)
    settings = StandardSettings.from_env()
    
    print(f"App Name: {settings.app_name}")
    print(f"Version: {settings.version}")
    print(f"Environment: {settings.environment}")
    print(f"Log Level: {settings.log_level}")
    
    # Check which services are enabled
    if settings.llm:
        print(f"LLM: {settings.llm.provider} - {settings.llm.model}")
    else:
        print("LLM: Not configured")
    
    if settings.cache:
        print(f"Cache: {settings.cache.provider}://{settings.cache.host}:{settings.cache.port}")
    else:
        print("Cache: Not configured")
    
    if settings.tracing:
        print(f"Tracing: Enabled for service '{settings.tracing.service_name}'")
    else:
        print("Tracing: Not configured")
    
    print()


# Example 2: Custom Settings Extension
@dataclass(frozen=True)
class DatabaseSettings:
    """Custom database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = 10
    ssl_mode: str = "prefer"


@dataclass(frozen=True)
class MyAppSettings:
    """Extended application settings."""
    # Core settings
    app_name: str
    version: str
    environment: str
    debug_mode: bool = False
    
    # Service configurations  
    llm_enabled: bool = False
    cache_enabled: bool = False
    
    # Custom configuration
    database: Optional[DatabaseSettings] = None
    max_workers: int = 4
    api_timeout: int = 30


def example_custom_settings():
    """Demonstrate custom settings creation."""
    print("=== Example 2: Custom Settings ===")
    
    # Simulate environment variables
    os.environ.update({
        "APP_NAME": "my-custom-app",
        "ENVIRONMENT": "development",
        "DEBUG_MODE": "true",
        "MAX_WORKERS": "8",
        "API_TIMEOUT": "60",
        "DB_HOST": "postgres.example.com",
        "DB_USER": "myapp_user",
        "DB_PASSWORD": "secret123"
    })
    
    from core_lib.config import EnvParser
    
    # Build custom settings from environment
    database_config = None
    if EnvParser.get_env("DB_HOST"):
        database_config = DatabaseSettings(
            host=EnvParser.get_env("DB_HOST", default="localhost"),
            port=EnvParser.get_env("DB_PORT", default=5432, env_type=int),
            database=EnvParser.get_env("DB_NAME", default="myapp"),
            username=EnvParser.get_env("DB_USER"),
            password=EnvParser.get_env("DB_PASSWORD"),
            pool_size=EnvParser.get_env("DB_POOL_SIZE", default=10, env_type=int),
            ssl_mode=EnvParser.get_env("DB_SSL_MODE", default="prefer")
        )
    
    app_settings = MyAppSettings(
        app_name=EnvParser.get_env("APP_NAME", default="my-app"),
        version=EnvParser.get_env("APP_VERSION", default="1.0.0"),
        environment=EnvParser.get_env("ENVIRONMENT", default="dev"),
        debug_mode=EnvParser.get_env("DEBUG_MODE", default=False, env_type=bool),
        llm_enabled=bool(EnvParser.get_env("OPENAI_API_KEY", "GEMINI_API_KEY")),
        cache_enabled=bool(EnvParser.get_env("REDIS_HOST")),
        database=database_config,
        max_workers=EnvParser.get_env("MAX_WORKERS", default=4, env_type=int),
        api_timeout=EnvParser.get_env("API_TIMEOUT", default=30, env_type=int)
    )
    
    print(f"App: {app_settings.app_name} v{app_settings.version}")
    print(f"Environment: {app_settings.environment}")
    print(f"Debug Mode: {app_settings.debug_mode}")
    print(f"Max Workers: {app_settings.max_workers}")
    print(f"API Timeout: {app_settings.api_timeout}")
    
    if app_settings.database:
        print(f"Database: {app_settings.database.username}@{app_settings.database.host}:{app_settings.database.port}/{app_settings.database.database}")
    else:
        print("Database: Not configured")
    
    print()


# Example 3: Integration with Existing LLM Clients
def example_llm_integration():
    """Demonstrate integration with existing LLM clients."""
    print("=== Example 3: LLM Integration ===")
    
    # Set up environment for OpenAI
    os.environ.update({
        "OPENAI_API_KEY": "sk-example-key-not-real",
        "OPENAI_MODEL": "gpt-4o-mini",
        "OPENAI_TEMPERATURE": "0.3"
    })
    
    from core_lib.config import StandardSettings
    
    try:
        settings = StandardSettings.from_env(load_dotenv=False)
        
        if settings.llm:
            print(f"LLM Provider: {settings.llm.provider}")
            print(f"LLM Model: {settings.llm.model}")
            print(f"Temperature: {settings.llm.temperature}")
            
            # Get configuration compatible with existing LLM clients
            llm_config = settings.get_llm_config()
            print(f"Config type: {type(llm_config).__name__}")
            
            # This would work with existing LLM client code:
            # from core_lib.llm import LLMClient
            # client = LLMClient(llm_config)
            # response = client.chat("Hello!")
            
            print("✓ LLM configuration ready for existing clients")
        else:
            print("❌ LLM not configured")
    
    except Exception as e:
        print(f"❌ LLM configuration error: {e}")
    
    print()


# Example 4: Settings Manager Usage
def example_settings_manager():
    """Demonstrate settings manager for complex applications."""
    print("=== Example 4: Settings Manager ===")
    
    from core_lib.config import settings_manager, StandardSettings, LLMSettings
    
    # Set up environment
    os.environ.update({
        "APP_NAME": "complex-app",
        "ENVIRONMENT": "production",
        "OPENAI_API_KEY": "sk-test",
        "REDIS_HOST": "cache.example.com"
    })
    
    try:
        # Register multiple settings configurations
        app_settings = StandardSettings.from_env(load_dotenv=False)
        settings_manager.register("app", app_settings)
        
        # Register a separate LLM configuration for a specific use case
        llm_settings = LLMSettings.from_env(
            load_dotenv=False,
            model="gpt-4",  # Override model for this specific use case
            temperature=0.1
        )
        settings_manager.register("analysis_llm", llm_settings)
        
        # List all registered settings
        print("Registered settings:")
        for name in settings_manager.list_names():
            print(f"  - {name}")
        
        # Access specific settings
        app_config = settings_manager.get_required("app")
        analysis_config = settings_manager.get("analysis_llm")
        
        print(f"\nApp Environment: {app_config.environment}")
        print(f"Analysis LLM Model: {analysis_config.model}")
        
        # Validate all settings
        errors = settings_manager.validate_all()
        if errors:
            print("\n❌ Validation errors found:")
            for name, error_list in errors.items():
                print(f"  {name}: {error_list}")
        else:
            print("\n✓ All settings are valid")
        
        # Export all settings for debugging
        all_settings = settings_manager.as_dict()
        print(f"\nTotal settings configurations: {len(all_settings)}")
    
    except Exception as e:
        print(f"❌ Settings manager error: {e}")
    
    print()


# Example 5: .env File Usage
def example_dotenv_usage():
    """Demonstrate .env file loading."""
    print("=== Example 5: .env File Usage ===")
    
    # Create a temporary .env file
    env_content = """
# Core application settings
APP_NAME=dotenv-example-app
ENVIRONMENT=staging
LOG_LEVEL=INFO

# LLM configuration
OPENAI_API_KEY=sk-example-from-env-file
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.5

# Cache configuration
REDIS_HOST=redis.staging.example.com
REDIS_PORT=6379
REDIS_PASSWORD=staging-secret
REDIS_PREFIX=staging:

# Tracing configuration
ENABLE_TRACING=true
LANGFUSE_PUBLIC_KEY=pk_staging_key
LANGFUSE_SECRET_KEY=sk_staging_secret
LANGFUSE_HOST=https://staging.langfuse.com
"""
    
    # Write .env file to current directory
    env_file = Path(".env.example")
    env_file.write_text(env_content.strip())
    
    try:
        from core_lib.config import StandardSettings, DotEnvLoader
        
        # Load .env file manually with custom name
        DotEnvLoader.load_dotenv_files([Path.cwd()], filename=".env.example")
        
        # Load settings (dotenv already loaded)
        settings = StandardSettings.from_env(load_dotenv=False)
        
        print(f"App: {settings.app_name}")
        print(f"Environment: {settings.environment}")
        print(f"Log Level: {settings.log_level}")
        
        if settings.llm:
            print(f"LLM: {settings.llm.provider} - {settings.llm.model} (temp: {settings.llm.temperature})")
        
        if settings.cache:
            print(f"Cache: {settings.cache.host}:{settings.cache.port} (prefix: {settings.cache.prefix})")
        
        if settings.tracing:
            print(f"Tracing: {settings.tracing.langfuse_host}")
        
        print("✓ Successfully loaded from .env file")
    
    except Exception as e:
        print(f"❌ .env loading error: {e}")
    
    finally:
        # Clean up
        if env_file.exists():
            env_file.unlink()
    
    print()


# Example 6: Environment-Specific Configuration
def example_environment_specific():
    """Demonstrate environment-specific configuration patterns."""
    print("=== Example 6: Environment-Specific Configuration ===")
    
    from core_lib.config import StandardSettings
    
    environments = ["development", "staging", "production"]
    
    for env in environments:
        print(f"\n--- {env.upper()} ---")
        
        # Simulate environment-specific variables
        env_vars = {
            "ENVIRONMENT": env,
            "APP_NAME": f"myapp-{env}",
        }
        
        if env == "development":
            env_vars.update({
                "LOG_LEVEL": "DEBUG",
                "OPENAI_API_KEY": "sk-dev-key",
                "REDIS_HOST": "localhost",
                "ENABLE_TRACING": "false"
            })
        elif env == "staging":
            env_vars.update({
                "LOG_LEVEL": "INFO", 
                "OPENAI_API_KEY": "sk-staging-key",
                "REDIS_HOST": "redis.staging.example.com",
                "ENABLE_TRACING": "true",
                "LANGFUSE_PUBLIC_KEY": "pk_staging",
                "LANGFUSE_SECRET_KEY": "sk_staging"
            })
        elif env == "production":
            env_vars.update({
                "LOG_LEVEL": "WARNING",
                "OPENAI_API_KEY": "sk-prod-key",
                "REDIS_HOST": "redis.prod.example.com",
                "REDIS_PASSWORD": "super-secret",
                "ENABLE_TRACING": "true",
                "LANGFUSE_PUBLIC_KEY": "pk_prod",
                "LANGFUSE_SECRET_KEY": "sk_prod",
                "LANGFUSE_HOST": "https://cloud.langfuse.com"
            })
        
        # Update environment
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            settings = StandardSettings.from_env(load_dotenv=False)
            
            print(f"App: {settings.app_name}")
            print(f"Log Level: {settings.log_level}")
            print(f"LLM Enabled: {settings.enable_llm}")
            print(f"Cache Enabled: {settings.enable_cache}")
            print(f"Tracing Enabled: {settings.enable_tracing}")
            
            if settings.cache:
                cache_info = f"{settings.cache.host}"
                if settings.cache.password:
                    cache_info += " (password protected)"
                print(f"Cache: {cache_info}")
        
        except Exception as e:
            print(f"❌ Configuration error: {e}")
        
        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
    
    print()


# Example 7: Validation and Error Handling
def example_validation_and_errors():
    """Demonstrate validation and error handling."""
    print("=== Example 7: Validation and Error Handling ===")
    
    from core_lib.config import StandardSettings, SettingsError, EnvironmentVariableError
    
    # Test 1: Invalid temperature
    print("Test 1: Invalid temperature")
    os.environ.update({
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_TEMPERATURE": "5.0"  # Invalid (> 2.0)
    })
    
    try:
        settings = StandardSettings.from_env(load_dotenv=False)
        if not settings.is_valid:
            print("❌ Settings validation failed:")
            for error in settings.validation_errors:
                print(f"  - {error}")
        else:
            print("✓ Settings are valid")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Test 2: Missing required environment variable
    print("\nTest 2: Missing required API key")
    for key in ["OPENAI_API_KEY", "OPENAI_TEMPERATURE"]:
        if key in os.environ:
            del os.environ[key]
    
    os.environ["LLM_PROVIDER"] = "openai"  # Force OpenAI provider
    
    try:
        settings = StandardSettings.from_env(load_dotenv=False)
        if settings.llm and not settings.llm.is_valid:
            print("❌ LLM settings validation failed:")
            for error in settings.llm.validation_errors:
                print(f"  - {error}")
        else:
            print("✓ LLM settings are valid or not configured")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Test 3: Invalid cache configuration
    print("\nTest 3: Invalid cache configuration")
    os.environ.update({
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "99999",  # Invalid port
        "REDIS_CACHE_TTL": "-1"  # Invalid TTL
    })
    
    try:
        settings = StandardSettings.from_env(load_dotenv=False)
        if settings.cache and not settings.cache.is_valid:
            print("❌ Cache settings validation failed:")
            for error in settings.cache.validation_errors:
                print(f"  - {error}")
        else:
            print("✓ Cache settings are valid or not configured")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()


def main():
    """Run all examples."""
    print("Core Settings Management Examples")
    print("=" * 50)
    
    # Clear environment to start fresh
    env_keys_to_clear = [
        "APP_NAME", "ENVIRONMENT", "LOG_LEVEL", "DEBUG_MODE", "MAX_WORKERS",
        "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_TEMPERATURE", "LLM_PROVIDER",
        "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_PREFIX", "REDIS_CACHE_TTL",
        "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "ENABLE_TRACING",
        "DB_HOST", "DB_USER", "DB_PASSWORD", "API_TIMEOUT"
    ]
    
    original_env = {}
    for key in env_keys_to_clear:
        original_env[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]
    
    try:
        example_basic_usage()
        example_custom_settings()
        example_llm_integration()
        example_settings_manager()
        example_dotenv_usage()
        example_environment_specific()
        example_validation_and_errors()
        
        print("✅ All examples completed successfully!")
    
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


if __name__ == "__main__":
    main()