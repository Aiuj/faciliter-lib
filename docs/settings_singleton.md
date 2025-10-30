# Settings Singleton Manager

The Settings Singleton Manager provides a thread-safe singleton pattern for managing a single `StandardSettings` instance throughout your application's lifecycle. This is particularly useful for applications that extend `StandardSettings` with custom fields and need a centralized configuration management approach.

## Features

- **Thread-safe singleton implementation** with double-checked locking
- **Easy initialization** from environment variables
- **Flexible reset/reconfiguration** capabilities
- **Type-safe** with full type hints support
- **Factory functions** for convenient access
- **Custom settings class support** - works with any class extending `StandardSettings`

## Quick Start

### Basic Usage

```python
from faciliter_lib.config import initialize_settings, get_settings

# Initialize settings (typically done at application startup)
settings = initialize_settings()

# Access settings anywhere in your application
def some_function():
    config = get_settings()
    print(config.app_name)
```

### With Custom Settings Class

```python
from dataclasses import dataclass
from faciliter_lib.config import StandardSettings, initialize_settings, get_settings

@dataclass(frozen=True)
class MyAppSettings(StandardSettings):
    """Custom settings for my application."""
    api_key: str = ""
    max_retries: int = 3
    timeout_seconds: float = 30.0

# Initialize with your custom class
settings = initialize_settings(
    settings_class=MyAppSettings,
    api_key="your-api-key",
    max_retries=5
)

# Access anywhere
config = get_settings()
assert isinstance(config, MyAppSettings)
print(config.api_key)
```

## API Reference

### Factory Functions

#### `initialize_settings()`

Initialize the global settings singleton from environment variables and optionally configure logging.

**Parameters:**
- `settings_class: Type[T] = StandardSettings` - The Settings class to instantiate (must extend StandardSettings)
- `force: bool = False` - If True, reinitialize even if already initialized
- `load_dotenv: bool = True` - Whether to load .env files
- `dotenv_paths: Optional[List[Union[str, Path]]] = None` - Custom paths to search for .env files
- `setup_logging: bool = True` - Whether to automatically configure logging based on settings (default: True)
- `**overrides` - Direct value overrides passed to `from_env()`

**Returns:** The initialized settings instance

**Raises:**
- `SettingsError` - If initialization fails or attempting to change settings class without `force=True`

**Features:**
- **Automatic Logging Setup**: When `setup_logging=True` (default), logging is automatically configured based on the settings' `app` and `logger` configurations. This eliminates the need to call `setup_logging()` separately.
- **Skip Logging**: Set `setup_logging=False` to skip automatic logging setup (useful for tests or when you need custom logging configuration).

**Example:**
```python
from faciliter_lib.config import initialize_settings

# Simple initialization with automatic logging setup
settings = initialize_settings()

# With overrides
settings = initialize_settings(
    app_name="my-app",
    log_level="DEBUG",
    enable_cache=True
)

# Force reinitialization
settings = initialize_settings(
    log_level="INFO",
    force=True
)

# Skip logging setup (useful for tests)
settings = initialize_settings(
    setup_logging=False
)
```

#### `get_settings()`

Get the current settings instance.

**Returns:** The current settings instance

**Raises:**
- `SettingsError` - If settings have not been initialized

**Example:**
```python
from faciliter_lib.config import get_settings

def my_function():
    config = get_settings()
    print(config.app_name)
```

#### `set_settings()`

Set the settings instance directly.

**Parameters:**
- `settings: StandardSettings` - The settings instance to use

**Raises:**
- `TypeError` - If settings is not a StandardSettings instance

**Example:**
```python
from faciliter_lib.config import set_settings, StandardSettings

# Create a settings instance manually
custom_settings = StandardSettings.from_env(app_name="manual-app")

# Set it as the global singleton
set_settings(custom_settings)
```

#### `reset_settings()`

Reset the settings singleton, removing the current instance.

**Example:**
```python
from faciliter_lib.config import reset_settings, initialize_settings

# Reset and reconfigure
reset_settings()
settings = initialize_settings(log_level="DEBUG")
```

#### `has_settings()`

Check if settings have been initialized.

**Returns:** `True` if settings are initialized, `False` otherwise

**Example:**
```python
from faciliter_lib.config import has_settings, initialize_settings

if not has_settings():
    initialize_settings()
```

#### `get_settings_safe()`

Get settings without raising an error if not initialized.

**Returns:** The settings instance if initialized, `None` otherwise

**Example:**
```python
from faciliter_lib.config import get_settings_safe

settings = get_settings_safe()
if settings:
    print(settings.app_name)
else:
    print("Settings not initialized")
```

### SettingsSingletonManager Class

The `SettingsSingletonManager` class provides the underlying singleton implementation. The factory functions are the recommended interface, but you can use the class directly if needed.

**Methods:**
- `initialize_settings(...)` - Initialize the singleton
- `get_settings()` - Get the current instance
- `set_settings(settings)` - Set the instance directly
- `reset_settings()` - Reset the singleton
- `has_settings()` - Check if initialized
- `get_settings_safe()` - Get instance without raising errors

## Usage Patterns

### Application Startup Pattern

Initialize settings once at application startup, then access throughout your codebase:

```python
# main.py
from faciliter_lib.config import initialize_settings

def main():
    # Initialize at startup
    settings = initialize_settings(
        app_name="my-application",
        log_level="INFO",
        enable_cache=True,
        enable_tracing=True
    )
    
    # Start your application
    run_app()

# module_a.py
from faciliter_lib.config import get_settings

def process_data():
    config = get_settings()
    # Use config.llm, config.cache, etc.
    pass

# module_b.py
from faciliter_lib.config import get_settings

def api_handler():
    config = get_settings()
    logger.setLevel(config.log_level)
    # ...
```

### Lazy Initialization Pattern

Initialize settings only when first needed:

```python
from faciliter_lib.config import has_settings, initialize_settings, get_settings

def get_config():
    """Get application config, initializing if needed."""
    if not has_settings():
        initialize_settings(app_name="lazy-app")
    return get_settings()

# Usage
def some_function():
    config = get_config()
    print(config.app_name)
```

### Testing Pattern

Reset settings between tests for isolation:

```python
import pytest
from faciliter_lib.config import reset_settings, initialize_settings, get_settings

class TestMyFeature:
    def setup_method(self):
        """Reset before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_with_debug_logging(self):
        """Test with debug configuration."""
        initialize_settings(log_level="DEBUG")
        assert get_settings().log_level == "DEBUG"
    
    def test_with_info_logging(self):
        """Test with info configuration."""
        initialize_settings(log_level="INFO")
        assert get_settings().log_level == "INFO"
```

### Environment-Specific Initialization

Configure based on environment:

```python
import os
from faciliter_lib.config import initialize_settings

def init_for_environment():
    env = os.getenv("ENVIRONMENT", "dev")
    
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

# Call at startup
init_for_environment()
```

### Custom Settings with Extended Fields

Define and use custom settings throughout your application:

```python
from dataclasses import dataclass
from typing import Optional
from faciliter_lib.config import StandardSettings, initialize_settings, get_settings

@dataclass(frozen=True)
class APIServerSettings(StandardSettings):
    """Settings for API server application."""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_key: Optional[str] = None
    cors_origins: str = "*"
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

# Initialize at startup
initialize_settings(
    settings_class=APIServerSettings,
    api_port=9000,
    api_workers=8,
    enable_cache=True,
    enable_tracing=True
)

# Use in different modules
def start_server():
    config = get_settings()
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        workers=config.api_workers
    )

def setup_cors():
    config = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins.split(",")
    )
```

## Thread Safety

The singleton manager uses double-checked locking to ensure thread-safe initialization:

```python
from faciliter_lib.config import initialize_settings
import threading

def init_in_thread(thread_id):
    settings = initialize_settings(app_name=f"thread-{thread_id}")
    return settings

# Multiple threads trying to initialize simultaneously
threads = [
    threading.Thread(target=init_in_thread, args=(i,))
    for i in range(10)
]

for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

# All threads will get the same singleton instance
# Only one initialization actually occurs
```

## Best Practices

1. **Initialize Early**: Call `initialize_settings()` once at application startup
2. **Use Factory Functions**: Prefer `get_settings()` over direct class access
3. **Custom Classes**: Extend `StandardSettings` for application-specific configuration
4. **Environment Variables**: Use `.env` files for configuration management
5. **Testing**: Always reset settings between test cases for isolation
6. **Type Safety**: Use type hints when working with custom settings classes
7. **Force Sparingly**: Only use `force=True` when you really need to reinitialize

## Comparison with SettingsManager

The `SettingsManager` (from `base_settings.py`) is different from the singleton pattern:

| Feature | SettingsSingletonManager | SettingsManager |
|---------|-------------------------|-----------------|
| Purpose | Single global settings instance | Multiple named settings instances |
| Pattern | Singleton | Registry |
| Access | `get_settings()` | `settings_manager.get("name")` |
| Use Case | Application-wide configuration | Multi-tenant or modular configs |
| Thread Safety | Built-in | User's responsibility |

**Use SettingsSingletonManager when:**
- You have one primary application configuration
- You want simple, application-wide access
- You're extending StandardSettings with custom fields

**Use SettingsManager when:**
- You need multiple independent configurations
- You're managing multi-tenant settings
- You need to register/unregister configs dynamically

## Error Handling

```python
from faciliter_lib.config import (
    get_settings,
    initialize_settings,
    SettingsError
)

try:
    # This will raise SettingsError if not initialized
    settings = get_settings()
except SettingsError as e:
    print(f"Settings not initialized: {e}")
    # Initialize with defaults
    settings = initialize_settings()

# Or use safe access
settings = get_settings_safe()
if settings is None:
    settings = initialize_settings()
```

## Integration Examples

### With Agent-RFx

```python
# In agent-rfx/src/settings.py
from dataclasses import dataclass
from faciliter_lib.config import StandardSettings, initialize_settings

@dataclass(frozen=True)
class Settings(StandardSettings):
    """Agent-RFx specific settings."""
    rfx_data_path: str = "data"
    rules_path: str = "rules"
    knowledge_base_path: str = "kb"

# In agent-rfx/src/main.py
from .settings import Settings

def main():
    # Initialize at startup
    settings = initialize_settings(
        settings_class=Settings,
        enable_llm=True,
        enable_embeddings=True,
        enable_mcp_server=True
    )
    
    # Now accessible everywhere via get_settings()
    run_mcp_server()
```

### With FastAPI

```python
from fastapi import FastAPI, Depends
from faciliter_lib.config import initialize_settings, get_settings

app = FastAPI()

# Initialize at startup
@app.on_event("startup")
async def startup():
    initialize_settings(
        app_name="fastapi-app",
        enable_cache=True,
        enable_tracing=True
    )

# Dependency for routes
def get_config():
    return get_settings()

@app.get("/")
async def root(config=Depends(get_config)):
    return {"app": config.app_name, "version": config.version}
```

## See Also

- [StandardSettings Documentation](settings.md)
- [Base Settings Guide](base_settings.md)
- [Configuration Best Practices](configuration_best_practices.md)
