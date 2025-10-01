# Settings Singleton Quick Reference

## Installation
```bash
# faciliter-lib already installed
from faciliter_lib.config import initialize_settings, get_settings
```

## Basic Usage (3 Lines)
```python
from faciliter_lib.config import initialize_settings, get_settings

# 1. Initialize once at startup
settings = initialize_settings(app_name="my-app")

# 2. Access anywhere in your code
config = get_settings()
```

## Custom Settings Class
```python
from dataclasses import dataclass
from faciliter_lib.config import StandardSettings, initialize_settings

@dataclass(frozen=True)
class MySettings(StandardSettings):
    api_key: str = ""
    max_retries: int = 3

# Initialize with your class
settings = initialize_settings(
    settings_class=MySettings,
    api_key="secret-key"
)
```

## Common Patterns

### Application Startup
```python
def main():
    initialize_settings(
        app_name="my-app",
        enable_cache=True,
        enable_llm=True
    )
    run_app()
```

### Access in Functions
```python
def my_function():
    config = get_settings()
    print(config.app_name)
```

### Lazy Initialization
```python
def get_config():
    if not has_settings():
        initialize_settings()
    return get_settings()
```

### Testing
```python
def setup_method():
    reset_settings()

def test_feature():
    initialize_settings(log_level="DEBUG")
    assert get_settings().log_level == "DEBUG"
```

## All Functions

| Function | Purpose |
|----------|---------|
| `initialize_settings()` | Create singleton from env |
| `get_settings()` | Get current instance |
| `set_settings(s)` | Set instance directly |
| `reset_settings()` | Clear singleton |
| `has_settings()` | Check if initialized |
| `get_settings_safe()` | Get without error |

## Common Parameters

```python
initialize_settings(
    settings_class=MySettings,     # Your custom class
    force=True,                    # Force reinit
    load_dotenv=True,              # Load .env files
    app_name="my-app",             # Override values
    log_level="DEBUG",
    enable_cache=True,
    enable_llm=True,
    # ... any StandardSettings field
)
```

## Error Handling

```python
from faciliter_lib.config import get_settings, SettingsError

try:
    settings = get_settings()
except SettingsError:
    initialize_settings()  # Initialize if needed
    settings = get_settings()

# OR use safe version
settings = get_settings_safe()
if settings is None:
    initialize_settings()
```

## Thread Safety
✓ Fully thread-safe
✓ Uses double-checked locking
✓ Safe concurrent initialization

## Environment Variables
All StandardSettings env vars work:
- `APP_NAME`, `LOG_LEVEL`, `ENVIRONMENT`
- `OPENAI_API_KEY`, `GEMINI_API_KEY`
- `REDIS_HOST`, `REDIS_PORT`
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- ... and more (see StandardSettings docs)

## Best Practices
1. ✓ Initialize once at app startup
2. ✓ Use `get_settings()` everywhere else
3. ✓ Reset in test fixtures
4. ✓ Extend StandardSettings for custom fields
5. ✗ Don't call `initialize_settings()` repeatedly
6. ✗ Don't create Settings.from_env() instances

## Complete Example

```python
# app.py
from dataclasses import dataclass
from faciliter_lib.config import (
    StandardSettings,
    initialize_settings,
    get_settings
)

@dataclass(frozen=True)
class AppSettings(StandardSettings):
    api_key: str = ""

def main():
    # Startup
    initialize_settings(
        settings_class=AppSettings,
        app_name="my-app"
    )
    
    # Use
    process_data()

def process_data():
    config = get_settings()
    print(f"Processing with {config.app_name}")

if __name__ == "__main__":
    main()
```

## See Also
- Full docs: `docs/settings_singleton.md`
- Examples: `examples/example_settings_singleton.py`
- StandardSettings: `docs/settings.md`
