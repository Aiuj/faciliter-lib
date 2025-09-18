# Cache provider and how clients should use it

The library exposes a unified cache manager that can use either Redis or Valkey as the backing store. Clients should prefer the facade helpers and the cache manager rather than instantiating provider classes directly. This keeps calling code agnostic to which cache backend is used and makes it easier to switch providers via configuration.
Key high-level points for client usage:
- Use `faciliter_lib.cache.cache_manager.set_cache` to install a global cache instance for the process. The rest of the helper APIs (`cache_get`, `cache_set`, `cache_delete`) operate against that global cache.
- Two built-in implementations exist: `RedisCache` (backed by Redis) and `ValkeyCache` (backed by Valkey). Both implement the same minimal interface: `get(key)`, `set(key, value, ttl=None)`, and `delete(key)`.
- You can configure the cache either in code or via environment variables (see the config notes below).
Example: basic usage with explicit Redis cache instance

```python
from faciliter_lib.cache.redis_cache import RedisCache
from faciliter_lib.cache.redis_config import RedisConfig
from faciliter_lib.cache.cache_manager import set_cache, cache_get, cache_set, cache_delete

# Build a RedisConfig (or use your own config loader)
cfg = RedisConfig(host="localhost", port=6379, db=0)

# Create and install the global cache instance
cache = RedisCache.from_config(cfg)
set_cache(cache)

# Use facade helpers anywhere in your app
cache_set("user:123", {"name": "Alice"}, ttl=300)
user = cache_get("user:123")
cache_delete("user:123")
```

Example: using Valkey as the backend (same facade)

```python
from faciliter_lib.cache.valkey_cache import ValkeyCache
from faciliter_lib.cache.valkey_config import ValkeyConfig
from faciliter_lib.cache.cache_manager import set_cache, cache_get, cache_set

cfg = ValkeyConfig(url="https://valkey.example.com", api_key="YOUR_KEY")
cache = ValkeyCache.from_config(cfg)
set_cache(cache)

cache_set("session:abc", "some-value", ttl=600)
value = cache_get("session:abc")
```

Programmatic vs environment configuration

- Programmatic: construct a `RedisConfig` or `ValkeyConfig` and call the provider's `from_config(...)` factory, then `set_cache(...)`.
- Environment-driven (recommended for deployed apps): you can read configuration from environment variables in your app and construct the appropriate config object. Typical env vars might include `CACHE_BACKEND=redis|valkey`, `REDIS_HOST`, `REDIS_PORT`, `VALKEY_URL`, `VALKEY_API_KEY`, etc. This repo's concrete config loader utilities may provide helpers to read from env; otherwise, read env vars and pass them to the config constructors.

Facade helper API (client-facing)

- `set_cache(cache_instance)` — Install a global cache instance used by helpers.
- `cache_get(key, default=None)` — Retrieve a value by key (returns `default` if missing).
- `cache_set(key, value, ttl=None)` — Store a value with optional TTL in seconds.
- `cache_delete(key)` — Remove a key from the cache.

Notes and best practices

- Prefer using the facade helpers (`cache_get`, `cache_set`) in application code so switching providers requires only a single initialization change.
- Encode TTLs in seconds. Providers should respect the `ttl` argument; `None` means persist until evicted by the provider.
- Keys are plain strings; use a consistent prefixing strategy (for example, `myapp:users:{id}`) to avoid collisions when sharing a Redis instance.
- Error handling: when initializing the global cache (e.g., network failures connecting to Redis), handle exceptions and decide whether your app should degrade gracefully (skip caching) or fail fast.

If you need to access provider-specific functionality, you can still import and use the concrete cache class directly, but that couples your code to the vendor implementation.

## Environment variables

The library does not force a specific set of environment variable names, but the following is a recommended convention for simple deployments. Use these env vars to drive which backend to initialize and the provider connection details.

- `CACHE_BACKEND` — Which backend to use. Allowed values: `redis`, `valkey`. Default: `redis`.

Redis-related variables (used when `CACHE_BACKEND=redis`):

- `REDIS_HOST`: Redis server host (default: `localhost`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis DB/index (default: `0`)
- `REDIS_PASSWORD`: Optional Redis password

Valkey-related variables (used when `CACHE_BACKEND=valkey`):

- `VALKEY_URL`: Valkey service URL (e.g., `https://valkey.example.com`)
- `VALKEY_API_KEY`: API key or token for Valkey

Small bootstrap example (env-driven)

```python
import os
from faciliter_lib.cache.cache_manager import set_cache

backend = os.getenv("CACHE_BACKEND", "redis").lower()


if backend == "valkey":
    from faciliter_lib.cache.valkey_config import ValkeyConfig
    from faciliter_lib.cache.valkey_cache import ValkeyCache

    cfg = ValkeyConfig(url=os.getenv("VALKEY_URL"), api_key=os.getenv("VALKEY_API_KEY"))
    cache = ValkeyCache.from_config(cfg)
    set_cache(cache)
else:
    from faciliter_lib.cache.redis_config import RedisConfig
    from faciliter_lib.cache.redis_cache import RedisCache

    cfg = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD", None),
    )
    cache = RedisCache.from_config(cfg)
    set_cache(cache)

# After this bootstrap, application code can safely call cache_get/cache_set helpers
```

This section should give you a straightforward way to wire the cache via environment variables in most deployment environments (containers, serverless functions, or traditional VMs).
