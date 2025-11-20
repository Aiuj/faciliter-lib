# Cache Provider and Client Usage Guide

The library provides a unified cache manager supporting both **Redis** and **Valkey** as backing stores. Both implementations include connection pooling and health check capabilities for production-grade performance and reliability.

## Quick Start (Recommended)

The recommended pattern is environment-driven initialization using `set_cache()` with no arguments:

**Key Benefits:**

- **Auto-detection**: Automatically selects the best provider based on `CACHE_BACKEND` env var and installed libraries
- **Zero configuration**: Works out of the box with sensible defaults
- **Backend-agnostic**: Application code doesn't need to know which cache provider is in use
- **Connection pooling**: Built-in connection reuse for better performance
- **Health monitoring**: Integrated health checks for reliability

**Essential Guidelines:**

- Call `set_cache()` once during application startup (reads environment variables)
- Use facade helpers (`cache_get`, `cache_set`, `cache_delete`, `cache_exists`) throughout your code
- Two built-in implementations: `RedisCache` and `ValkeyCache` (both Redis-compatible)
- Avoid direct provider instantiation unless you need provider-specific features

### Quick Startup Example (Recommended)

```python
# Application startup
from core_lib.cache import set_cache

# Environment-driven initialization - reads CACHE_BACKEND and provider env vars
set_cache()

# Use cache anywhere in your application
from core_lib.cache import cache_get, cache_set

result = cache_get({"query": "expensive operation"})
if result is None:
    result = expensive_computation()
    cache_set({"query": "expensive operation"}, result, ttl=3600)
```

## When to Use Programmatic Configuration

- Use programmatic initialization only when you must construct provider configs in code (for tests, local scripts, or when envs are not available)
- If you do initialize programmatically, call `set_cache(provider=..., config=..., ttl=...)` so the cache manager still performs selection and connection logic

## Programmatic Examples (Optional)

### Example: Explicit Redis Cache Instance

```python
from core_lib.cache import RedisCache, RedisConfig, set_cache, cache_get, cache_set

cfg = RedisConfig(host="localhost", port=6379, db=0, ttl=3600)
set_cache(provider="redis", config=cfg)

# Use facade helpers
cache_set({"user_id": 123}, {"name": "Alice"}, ttl=300)
user = cache_get({"user_id": 123})
```

### Example: Using Valkey as the Backend

```python
from core_lib.cache import ValkeyCache, ValkeyConfig, set_cache, cache_get, cache_set

cfg = ValkeyConfig(host="localhost", port=6379, db=0, ttl=3600)
set_cache(provider="valkey", config=cfg)

# Use facade helpers (same API as Redis)
cache_set({"session_id": "abc"}, {"user": "data"}, ttl=600)
value = cache_get({"session_id": "abc"})
```

## Facade Helper API (Client-Facing)

**Initialization:**

- `set_cache(provider="auto", config=None, ttl=None, time_out=None)`: Initialize the global cache instance
  - `provider`: "redis", "valkey", or "auto" (default)
  - `config`: Optional provider-specific config (RedisConfig or ValkeyConfig)
  - `ttl`: Default time-to-live in seconds
  - `time_out`: Connection timeout in seconds
  - Calling with no arguments uses environment variables and auto-detection (recommended)
  - Returns `True` if cache is usable, `False` if disabled/failed

**Basic Operations:**

- `cache_get(input_data, company_id=None)`: Retrieve cached value
  - `input_data`: Any hashable type (dict, string, tuple, etc.)
  - `company_id`: Optional tenant identifier for isolation
  - Returns cached value or `None` if not found

- `cache_set(input_data, output_data, ttl=None, company_id=None)`: Store value in cache
  - `input_data`: Cache key (any hashable type)
  - `output_data`: Value to cache
  - `ttl`: Optional time-to-live in seconds (overrides default)
  - `company_id`: Optional tenant identifier for isolation

- `cache_delete(input_data, company_id=None)`: Delete cached entry
  - Returns `True` if key was deleted, `False` if key didn't exist

- `cache_exists(input_data, company_id=None)`: Check if cached entry exists
  - Returns `True` if key exists, `False` otherwise
  - More efficient than `cache_get` when you only need existence check

**Bulk Clearing Operations:**

- `cache_clear_company(company_id)`: Remove all cached entries for a specific tenant
- `cache_clear_global()`: Remove all cached entries not associated with any tenant
- `cache_clear_all()`: Remove all cached entries across all tenants and global

**Advanced:**

- `get_cache()`: Get the global cache instance (for direct access)
- `get_cache_client()`: Get the underlying client (Redis/Valkey) for direct operations

## Tenant-Aware Caching (Multi-Tenant / Company Isolation)

Many applications require strict separation of cached data across tenants (companies). The cache system supports an optional `company_id` parameter on all cache operations that creates a hard namespace wall between tenants.

**Key Design:**

- Global (no tenant): `<prefix><name>:<hash>`
- Tenant scoped: `<prefix>tenant:<company_id>:<name>:<hash>`

 This ensures no accidental key collisions across tenants and makes it feasible to selectively purge cache for one tenant without affecting others.

**Clearing Strategies:**

- Per-tenant purge: `cache_clear_company("acme")`
- Global-only purge: `cache_clear_global()` (entries cached without a `company_id`)
- Complete purge: `cache_clear_all()` (all tenants and global)

**Implementation Overview:**

- Each stored key is added to a Redis/Valkey Set registry per tenant (`<prefix>registry:tenant:<company_id>`) or to a global registry (`<prefix>registry:global`)
- Clear operations read the registry, delete member keys, then remove the registry set itself
- Failures in registry bookkeeping never prevent core cache operations (best-effort tracking)

**Example:**

```python
from core_lib.cache import set_cache, cache_set, cache_get, cache_clear_company

set_cache()  # environment driven
cache_set({'user_id': 10}, {'name': 'Alice'}, company_id='acme')
cache_set({'user_id': 11}, {'name': 'Bob'}, company_id='globex')

# Retrieve within tenant scopes
alice = cache_get({'user_id': 10}, company_id='acme')
bob = cache_get({'user_id': 11}, company_id='globex')

# Purge only Acme's cached entries
cache_clear_company('acme')
assert cache_get({'user_id': 10}, company_id='acme') is None
assert cache_get({'user_id': 11}, company_id='globex') is not None
```

## Notes and Best Practices

- **Use facade helpers**: Prefer `cache_get`, `cache_set`, `cache_delete`, `cache_exists` so switching providers requires only initialization changes
- **TTL in seconds**: Providers respect the `ttl` argument; `None` means persist until evicted
- **Hashable keys**: Input data can be any hashable type (dict, string, tuple, etc.) - the cache automatically generates consistent hash keys
- **Error handling**: `set_cache()` returns `True` when cache is usable, `False` when disabled/failed. Check return value to decide if your app should degrade gracefully
- **Provider-specific features**: You can import and use concrete cache classes directly (`RedisCache`, `ValkeyCache`), but that couples your code to the vendor implementation
- **Connection pooling**: Both Redis and Valkey implementations use connection pooling by default for better performance

## Environment Variables

The library uses environment variables for configuration. The following is the recommended convention for deployments. Calling `set_cache()` with no args will read these vars and configure the appropriate backend.

**General:**

- `CACHE_BACKEND`: Which backend to use. Allowed values: `redis`, `valkey`, `auto`. Default: `auto` (auto-detect based on installed clients and envs)

**Redis-related variables** (used when `CACHE_BACKEND=redis` or when Redis is selected):

- `REDIS_HOST`: Redis server host (default: `localhost`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis DB/index (default: `0`)
- `REDIS_PASSWORD`: Optional Redis password
- `REDIS_MAX_CONNECTIONS`: Maximum connections in pool (default: `50`)
- `REDIS_RETRY_ON_TIMEOUT`: Retry on connection timeout (default: `true`)
- `REDIS_TIMEOUT`: Connection timeout in seconds (default: `4`)
- `REDIS_CACHE_TTL`: Default TTL in seconds (default: `3600`)
- `REDIS_PREFIX`: Key prefix (default: `cache:`)

**Valkey-related variables** (used when `CACHE_BACKEND=valkey`):

- `VALKEY_HOST`: Valkey server host (default: `localhost`, falls back to `REDIS_HOST`)
- `VALKEY_PORT`: Valkey server port (default: `6379`, falls back to `REDIS_PORT`)
- `VALKEY_DB`: Valkey DB/index (default: `0`, falls back to `REDIS_DB`)
- `VALKEY_PASSWORD`: Optional Valkey password (falls back to `REDIS_PASSWORD`)
- `VALKEY_MAX_CONNECTIONS`: Maximum connections in pool (default: `50`, falls back to `REDIS_MAX_CONNECTIONS`)
- `VALKEY_RETRY_ON_TIMEOUT`: Retry on connection timeout (default: `true`, falls back to `REDIS_RETRY_ON_TIMEOUT`)
- `VALKEY_TIMEOUT`: Connection timeout in seconds (default: `4`, falls back to `REDIS_TIMEOUT`)
- `VALKEY_CACHE_TTL`: Default TTL in seconds (default: `3600`, falls back to `REDIS_CACHE_TTL`)
- `VALKEY_PREFIX`: Key prefix (default: `cache:`, falls back to `REDIS_PREFIX`)

## When to Explicitly Specify Redis or Valkey

- In most cases prefer `set_cache()` with environment-driven configuration so the library picks the appropriate backend
- If you must force a specific backend (for example, during tests or in environments where `valkey` is installed but you still want Redis), call `set_cache(provider="redis", config=...)` or `set_cache(provider="valkey", config=...)`

This approach keeps application code simple and ensures the cache manager performs consistent initialization, connection checks, and fallbacks.

## Connection Pooling and Health Checks

Both Redis and Valkey cache implementations include connection pooling for improved performance and resource management:

### Connection Pooling Benefits

- **Reduced overhead**: Reuse existing connections instead of creating new ones for each operation
- **Better performance**: Eliminate connection setup/teardown costs
- **Resource management**: Control maximum concurrent connections
- **Fault tolerance**: Automatic retry on timeout if configured

### Configuration

Connection pool settings can be configured via environment variables or programmatically:

```python
from core_lib.cache import RedisConfig, RedisCache

# Programmatic configuration
config = RedisConfig(
    host="localhost",
    port=6379,
    max_connections=100,        # Pool size
    retry_on_timeout=True       # Retry failed connections
)
cache = RedisCache(config=config)
cache.connect()
```

### Health Checks

Both cache implementations provide health check functionality to monitor server availability:

```python
from core_lib.cache import get_cache

cache = get_cache()
if cache and cache.health_check():
    print("Cache server is healthy")
else:
    print("Cache server is unavailable")
```

### Resource Cleanup

Always call `close()` to properly cleanup connection pools:

```python
from core_lib.cache import RedisCache

cache = RedisCache()
try:
    cache.connect()
    # ... use cache
finally:
    cache.close()  # Cleanup connection pool
```

### Example Usage

See `examples/example_cache_pooling_health_check.py` for a complete demonstration of connection pooling and health check features.
