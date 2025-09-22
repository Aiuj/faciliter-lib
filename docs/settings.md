# Settings Management System

The Faciliter library provides a comprehensive, extensible settings management system that handles configuration for any application. The system supports environment variables, .env files, type conversion, validation, and easy extension for custom settings.

## Overview

The settings system is built around several key components:

- **`StandardSettings`**: Main settings class with all standard services (LLM, cache, database, etc.) and easy extension via `extend_from_env()`
- **Service-specific modules**: Dedicated classes for each service type (LLM, embeddings, cache, tracing, database, MCP server)
- **`BaseSettings`**: Abstract base class for advanced custom settings (when you need full control)
- **`SettingsManager`**: Manages multiple settings instances with validation
- **Utilities**: Helper classes for .env loading and environment variable parsing

> **💡 Quick Start**: For most applications, use `StandardSettings.extend_from_env()` to add custom configuration. This gives you all standard services plus your custom fields with minimal code.

### Modular Architecture

The settings system uses a modular architecture with dedicated files for each service type:

```
faciliter_lib/config/
├── base_settings.py       # Core framework and utilities
├── app_settings.py        # Core application settings  
├── llm_settings.py        # LLM provider configuration
├── embeddings_settings.py # Embeddings provider configuration
├── cache_settings.py      # Cache provider configuration
├── tracing_settings.py    # Tracing provider configuration
├── database_settings.py   # Database configuration
├── mcp_settings.py        # MCP server configuration
└── standard_settings.py   # Main unified settings class
```

This modular design provides:
- **Clear separation of concerns** - each service has its own module
- **Easy maintenance** - changes to one service don't affect others
- **Extensibility** - new services can be added as separate modules
- **Testability** - each module can be tested independently

## Quick Start

### Basic Usage

```python
from faciliter_lib.config import StandardSettings

# Load all settings from environment variables and .env files
settings = StandardSettings.from_env()

print(f"App: {settings.app_name} v{settings.version}")
print(f"Environment: {settings.environment}")

# Access service configurations if enabled
if settings.llm:
    print(f"LLM Provider: {settings.llm.provider}")
    print(f"LLM Model: {settings.llm.model}")

if settings.cache:
    print(f"Cache: {settings.cache.provider}://{settings.cache.host}:{settings.cache.port}")

if settings.database:
    print(f"Database: {settings.database.username}@{settings.database.host}:{settings.database.port}/{settings.database.database}")
```

### Using .env Files

Create a `.env` file in your project root:

```bash
# Core app settings
APP_NAME=my-awesome-app
ENVIRONMENT=production
LOG_LEVEL=INFO

# LLM configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# Cache configuration
ENABLE_CACHE=true
REDIS_HOST=redis.example.com
REDIS_PASSWORD=secret123
REDIS_PREFIX=myapp:

# Tracing configuration
ENABLE_TRACING=true
LANGFUSE_PUBLIC_KEY=pk_your_public_key
LANGFUSE_SECRET_KEY=sk_your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# MCP server configuration
MCP_SERVER_NAME=my-mcp-server
MCP_SERVER_PORT=8204
MCP_SERVER_HOST=0.0.0.0
MCP_TRANSPORT=streamable-http
```

The settings system will automatically discover and load `.env` files from:
1. Current working directory
2. Project root (directory containing `pyproject.toml`)
3. User home directory

### Service Auto-Detection

The system automatically detects which services to enable based on environment variables:

```python
# Will automatically enable LLM if any LLM-related env vars are present
# Will automatically enable cache if Redis/Valkey env vars are present
# Will automatically enable tracing if Langfuse env vars are present
settings = StandardSettings.from_env()

# Or explicitly control which services to enable
settings = StandardSettings.from_env(
    enable_llm=True,
    enable_embeddings=False,
    enable_cache=True,
    enable_tracing=False
)
```

### Adding Custom Configuration

For application-specific settings, extend StandardSettings using the simplified `extend_from_env()` pattern:

```python
class MyAppSettings:
    @classmethod
    def from_env(cls, **kwargs):
        return StandardSettings.extend_from_env(
            custom_config={
                "api_key": {"env_vars": ["API_KEY"], "required": True},
                "debug_mode": {"env_vars": ["DEBUG"], "default": False, "env_type": bool},
                "max_workers": {"env_vars": ["MAX_WORKERS"], "default": 4, "env_type": int},
            },
            **kwargs
        )

# Get all standard services + custom configuration
settings = MyAppSettings.from_env()
print(f"API Key: {settings.api_key}")
print(f"LLM enabled: {settings.enable_llm}")
```

## Individual Settings Classes

### LLM Settings

```python
from faciliter_lib.config import LLMSettings

# Auto-detect provider from environment
llm_settings = LLMSettings.from_env()

# Or specify explicitly
llm_settings = LLMSettings.from_env(
    provider="openai",
    model="gpt-4",
    temperature=0.3
)

# Get configuration for existing LLM clients
llm_config = settings.get_llm_config()  # Returns OpenAIConfig/GeminiConfig/OllamaConfig
```

### Embeddings Settings

```python
from faciliter_lib.config import EmbeddingsSettings

embeddings_settings = EmbeddingsSettings.from_env(
    provider="openai",
    model="text-embedding-3-large",
    embedding_dimension=1536
)

# Get configuration for existing embeddings client
embeddings_config = settings.get_embeddings_config()  # Returns EmbeddingsConfig
```

### Cache Settings  

```python
from faciliter_lib.config import CacheSettings

cache_settings = CacheSettings.from_env(
    provider="redis",  # or "valkey"
    host="localhost",
    port=6379,
    password="secret"
)

# Get configuration for existing cache client
redis_config = settings.get_redis_config()  # Returns RedisConfig
```

### Database Settings

```python
from faciliter_lib.config import DatabaseSettings

database_settings = DatabaseSettings.from_env(
    host="localhost",
    port=5432,
    database="myapp",
    username="user",
    password="password",
    sslmode="require"
)

# Generate connection strings for different drivers
sync_conn = database_settings.get_sync_connection_string()      # postgresql+psycopg2://
async_conn = database_settings.get_async_connection_string()    # postgresql+asyncpg://
basic_conn = database_settings.get_connection_string()          # postgresql://

# Use with StandardSettings
settings = StandardSettings.from_env()
if settings.database:
    db_config = settings.get_database_config()  # Returns DatabaseSettings
```

### MCP Server Settings

```python
from faciliter_lib.config import MCPServerSettings

# Configure MCP (Model Context Protocol) server
mcp_settings = MCPServerSettings.from_env(
    server_name="my-mcp-server",
    version="1.0.0",
    host="0.0.0.0",
    port=8204,
    transport="streamable-http",
    timeout=30
)

# Get server information for MCP protocol
server_info = mcp_settings.get_server_info()  # {"name": "...", "version": "..."}

# Get connection configuration for MCP clients
connection_config = mcp_settings.get_connection_config()

# Use with StandardSettings
settings = StandardSettings.from_env()
if settings.mcp_server:
    mcp_config = settings.get_mcp_server_config()  # Returns MCPServerSettings
```

### Tracing Settings

```python
from faciliter_lib.config import TracingSettings

tracing_settings = TracingSettings.from_env(
    service_name="my-service",
    langfuse_public_key="pk_...",
    langfuse_secret_key="sk_..."
)
```

## Creating Custom Settings

The easiest way to add custom configuration to your application is to extend `StandardSettings` using the `extend_from_env()` method. This approach gives you all the standard services (LLM, cache, database, etc.) plus your custom fields with minimal code.

### Recommended Approach: Extending StandardSettings

```python
from faciliter_lib.config import StandardSettings
from typing import Optional

class MyAppSettings:
    """Custom settings that extend StandardSettings with app-specific configuration."""
    
    @classmethod
    def from_env(cls, **kwargs):
        """Load settings from environment with custom field mappings."""
        return StandardSettings.extend_from_env(
            custom_config={
                "api_key": {
                    "env_vars": ["API_KEY", "MY_API_KEY"], 
                    "required": True
                },
                "api_timeout": {
                    "env_vars": ["API_TIMEOUT", "TIMEOUT"], 
                    "default": 30, 
                    "env_type": int
                },
                "debug_mode": {
                    "env_vars": ["DEBUG_MODE", "DEBUG"], 
                    "default": False, 
                    "env_type": bool
                },
                "max_workers": {
                    "env_vars": ["MAX_WORKERS", "WORKERS"], 
                    "default": 4, 
                    "env_type": int
                },
                "feature_flags": {
                    "env_vars": ["FEATURE_FLAGS"], 
                    "default": [], 
                    "env_type": list
                },
                "allowed_hosts": {
                    "env_vars": ["ALLOWED_HOSTS"], 
                    "default": ["localhost"], 
                    "env_type": list
                },
            },
            **kwargs
        )

# Usage
settings = MyAppSettings.from_env()

# Access standard services
if settings.enable_llm:
    llm_config = settings.get_llm_config()
    print(f"LLM Provider: {llm_config.provider}")

if settings.enable_cache:
    redis_config = settings.get_redis_config()
    print(f"Cache Host: {redis_config.host}")

# Access custom fields
print(f"API Key: {settings.api_key[:8]}...")
print(f"Debug Mode: {settings.debug_mode}")
print(f"Max Workers: {settings.max_workers}")
print(f"Feature Flags: {settings.feature_flags}")
```

### Custom Configuration Options

Each custom field supports these configuration options:

- **`env_vars`**: List of environment variable names to check (in order of preference)
- **`default`**: Default value if no environment variable is found
- **`env_type`**: Type conversion (str, int, float, bool, list)
- **`required`**: Whether the field is required (raises error if missing)

### Environment Variables for Custom Settings

```bash
# Required API key
API_KEY=your-secret-key

# Optional configuration with defaults
API_TIMEOUT=60
DEBUG_MODE=true
MAX_WORKERS=8
FEATURE_FLAGS=feature_a,feature_b,feature_c
ALLOWED_HOSTS=localhost,127.0.0.1,example.com

# Standard services still work
OPENAI_API_KEY=sk-your-key
REDIS_HOST=localhost
```

### Benefits of This Approach

✅ **Get all standard services automatically** (LLM, cache, database, tracing, MCP server)  
✅ **Minimal boilerplate code** - just define your custom fields  
✅ **Full type safety and validation**  
✅ **Environment variable parsing with fallbacks**  
✅ **Compatible with existing StandardSettings APIs**  
✅ **Easy to test and maintain**

### Alternative: Advanced Custom Settings (BaseSettings)

For more complex scenarios where you need full control over validation logic or want completely custom settings classes, you can still inherit from `BaseSettings`:

```python
from dataclasses import dataclass
from typing import Optional
from faciliter_lib.config import BaseSettings, SettingsError

@dataclass(frozen=True)
class CustomAPISettings(BaseSettings):
    """Advanced custom settings with complex validation."""
    
    base_url: str = "https://api.example.com"
    timeout: int = 30
    max_retries: int = 3
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 1000
    
    @classmethod
    def from_env(cls, load_dotenv=True, dotenv_paths=None, **overrides):
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        settings_dict = {
            "base_url": cls.get_env("API_BASE_URL", default="https://api.example.com"),
            "timeout": cls.get_env("API_TIMEOUT", default=30, env_type=int),
            "max_retries": cls.get_env("API_MAX_RETRIES", default=3, env_type=int),
            "api_key": cls.get_env("API_KEY", required=True),
            "rate_limit_per_minute": cls.get_env("API_RATE_LIMIT", default=1000, env_type=int),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self):
        """Custom validation logic."""
        if self.timeout <= 0:
            raise SettingsError("Timeout must be positive")
        if self.max_retries < 0:
            raise SettingsError("Max retries cannot be negative")
        if not self.base_url.startswith(('http://', 'https://')):
            raise SettingsError("Base URL must be a valid HTTP/HTTPS URL")
```

> **💡 Recommendation**: Use `StandardSettings.extend_from_env()` for most use cases. Only use `BaseSettings` directly when you need complex custom validation or completely separate settings classes.

## Environment Variable Parsing

The system provides powerful environment variable parsing with type conversion:

```python
from faciliter_lib.config import EnvParser

# Basic parsing with defaults
api_key = EnvParser.get_env("API_KEY", "OPENAI_API_KEY", default="")
timeout = EnvParser.get_env("TIMEOUT", default=30, env_type=int)
enabled = EnvParser.get_env("FEATURE_ENABLED", default=False, env_type=bool)

# Required variables (raises EnvironmentVariableError if missing)
db_password = EnvParser.get_env("DB_PASSWORD", required=True)

# List parsing (comma-separated values)
allowed_hosts = EnvParser.get_env("ALLOWED_HOSTS", default=[], env_type=list)
# ALLOWED_HOSTS=localhost,127.0.0.1,example.com -> ["localhost", "127.0.0.1", "example.com"]

# Multiple fallback names
redis_host = EnvParser.get_env("REDIS_HOST", "CACHE_HOST", "DB_HOST", default="localhost")
```

## Settings Manager

Use the settings manager to register and manage multiple configuration instances:

```python
from faciliter_lib.config import settings_manager, StandardSettings

# Register settings
app_settings = StandardSettings.from_env()
settings_manager.register("app", app_settings)

# Add custom settings
db_settings = DatabaseSettings.from_env()
settings_manager.register("database", db_settings)

# Access settings
app_config = settings_manager.get_required("app")
db_config = settings_manager.get("database")

# Validate all settings
errors = settings_manager.validate_all()
if errors:
    print("Configuration errors found:")
    for name, error_list in errors.items():
        print(f"  {name}: {error_list}")

# Export all settings
all_settings = settings_manager.as_dict()
```

## Integration with Existing Libraries

### Using with LLM Clients

```python
from faciliter_lib.config import StandardSettings
from faciliter_lib.llm import LLMClient

# Load settings and create LLM client
settings = StandardSettings.from_env()
if settings.llm:
    llm_config = settings.get_llm_config()
    llm_client = LLMClient(llm_config)
    
    response = llm_client.chat("Hello, world!")
    print(response["content"])
```

### Using with Cache

```python
from faciliter_lib.config import StandardSettings
from faciliter_lib.cache import RedisCache

settings = StandardSettings.from_env()
if settings.cache:
    redis_config = settings.get_redis_config()
    cache = RedisCache(redis_config)
    
    cache.set("key", "value")
    value = cache.get("key")
```

### Using with Embeddings

```python
from faciliter_lib.config import StandardSettings
from faciliter_lib.embeddings import create_embeddings_provider

settings = StandardSettings.from_env()
if settings.embeddings:
    embeddings_config = settings.get_embeddings_config()
    embeddings_provider = create_embeddings_provider(embeddings_config)
    
    vectors = embeddings_provider.embed_texts(["Hello world"])
```

## Advanced Features

### Custom .env File Paths

```python
from pathlib import Path

# Load from specific paths
settings = StandardSettings.from_env(
    load_dotenv=True,
    dotenv_paths=[
        Path("/etc/myapp/.env"),      # System config
        Path.home() / ".myapp.env",    # User config  
        Path.cwd() / ".env.local"      # Local overrides
    ]
)
```

### Settings Merging and Overrides

```python
# Base settings from environment
base_settings = StandardSettings.from_env()

# Create variant with overrides
test_settings = base_settings.merge(
    environment="test",
    log_level="DEBUG",
    enable_cache=False
)

# Direct overrides during creation
settings = StandardSettings.from_env(
    app_name="custom-app",
    enable_tracing=False,
    # Override LLM model specifically
    llm=LLMSettings.from_env(model="gpt-3.5-turbo")
)
```

### Validation and Error Handling

```python
try:
    settings = StandardSettings.from_env()
    if not settings.is_valid:
        print("Settings validation failed:")
        for error in settings.validation_errors:
            print(f"  - {error}")
except EnvironmentVariableError as e:
    print(f"Missing required environment variable: {e}")
except SettingsError as e:
    print(f"Settings configuration error: {e}")
```

## Best Practices

1. **Use .env files for development**, environment variables for production
2. **Validate settings early** in your application startup
3. **Use the settings manager** for complex applications with multiple configuration sources
4. **Create custom settings classes** for domain-specific configuration
5. **Leverage auto-detection** to simplify configuration management
6. **Use type hints** and validation to catch configuration errors early
7. **Document your environment variables** for your team and deployment processes

## Environment Variables Reference

### Core Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `"faciliter-app"` | Application name |
| `APP_VERSION` | `"0.1.0"` | Application version (fallback if not in pyproject.toml) |
| `ENVIRONMENT` | `"dev"` | Environment name (dev/prod/staging/etc.) |
| `LOG_LEVEL` | `"DEBUG"` (dev) / `"INFO"` (prod) | Logging level |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | Auto-detected | LLM provider (openai/azure/gemini/ollama) |
| `LLM_MODEL` | Provider-specific | Model name |
| `LLM_TEMPERATURE` | `0.7` | Sampling temperature |
| `LLM_MAX_TOKENS` | `None` | Maximum tokens to generate |
| `LLM_THINKING_ENABLED` | `false` | Enable thinking mode |

**OpenAI/Azure:**
- `OPENAI_API_KEY` - API key
- `OPENAI_BASE_URL` - Custom base URL
- `OPENAI_ORGANIZATION` - Organization ID  
- `OPENAI_PROJECT` - Project ID
- `AZURE_OPENAI_ENDPOINT` - Azure endpoint
- `AZURE_OPENAI_API_VERSION` - API version

**Gemini:**
- `GEMINI_API_KEY` / `GOOGLE_GENAI_API_KEY` - API key

**Ollama:**
- `OLLAMA_HOST` / `OLLAMA_BASE_URL` - Ollama server URL
- `OLLAMA_TIMEOUT` - Request timeout

### Embeddings Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_PROVIDER` | `"openai"` | Embeddings provider |
| `EMBEDDING_MODEL` | `"text-embedding-3-small"` | Model name |
| `EMBEDDING_DIMENSION` | Model default | Embedding dimension |
| `EMBEDDING_TASK_TYPE` | `None` | Task type for Google GenAI |

### Cache Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_PROVIDER` | `"redis"` | Cache provider (redis/valkey) |
| `REDIS_HOST` / `VALKEY_HOST` | `"localhost"` | Cache server host |
| `REDIS_PORT` / `VALKEY_PORT` | `6379` | Cache server port |
| `REDIS_DB` / `VALKEY_DB` | `0` | Database number |
| `REDIS_PREFIX` / `VALKEY_PREFIX` | `"cache:"` | Key prefix |
| `REDIS_CACHE_TTL` / `VALKEY_CACHE_TTL` | `3600` | Default TTL in seconds |
| `REDIS_PASSWORD` / `VALKEY_PASSWORD` | `None` | Password |
| `REDIS_TIMEOUT` / `VALKEY_TIMEOUT` | `4` | Connection timeout |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` / `DATABASE_HOST` | `"localhost"` | PostgreSQL server host |
| `POSTGRES_PORT` / `DATABASE_PORT` | `5432` | PostgreSQL server port |
| `POSTGRES_DB` / `DATABASE_NAME` | `"faciliter-qa-rag"` | Database name |
| `POSTGRES_USER` / `DATABASE_USER` | `"rfp_user"` | Database username |
| `POSTGRES_PASSWORD` / `DATABASE_PASSWORD` | `"rfp_password"` | Database password |
| `POSTGRES_SSLMODE` / `DATABASE_SSLMODE` | `"disable"` | SSL mode (disable/allow/prefer/require/verify-ca/verify-full) |
| `POSTGRES_POOL_SIZE` / `DATABASE_POOL_SIZE` | `10` | Connection pool size |
| `POSTGRES_MAX_OVERFLOW` / `DATABASE_MAX_OVERFLOW` | `20` | Max pool overflow |
| `POSTGRES_POOL_TIMEOUT` / `DATABASE_POOL_TIMEOUT` | `30` | Pool timeout in seconds |

### Tracing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACING_ENABLED` | `true` | Enable tracing |
| `LANGFUSE_PUBLIC_KEY` | Required | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Required | Langfuse secret key |
| `LANGFUSE_HOST` | `"http://localhost:3000"` | Langfuse host URL |

### MCP Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_NAME` / `APP_NAME` | `"faciliter-mcp-server"` | MCP server name |
| `MCP_SERVER_VERSION` / `APP_VERSION` | `"0.1.0"` | MCP server version |
| `MCP_SERVER_HOST` | `"0.0.0.0"` | Host address to bind server |
| `MCP_SERVER_PORT` | `8204` | Port number for server |
| `MCP_SERVER_URL` | Auto-generated | Full URL for server |
| `MCP_SERVER_TIMEOUT` | `30` | Request timeout in seconds |
| `MCP_TRANSPORT` | `"streamable-http"` | Transport type (streamable-http/stdio/websocket) |

### Service Enablement

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_LLM` | Auto-detected | Force enable/disable LLM |
| `ENABLE_EMBEDDINGS` | Auto-detected | Force enable/disable embeddings |
| `ENABLE_CACHE` | Auto-detected | Force enable/disable cache |
| `ENABLE_TRACING` | Auto-detected | Force enable/disable tracing |
| `ENABLE_DATABASE` | Auto-detected | Force enable/disable database |
| `ENABLE_MCP_SERVER` | Auto-detected | Force enable/disable MCP server |