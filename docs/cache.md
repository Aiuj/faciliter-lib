 # Cache provider and how clients should use it

 The library exposes a unified cache manager that can use either Redis or Valkey as the backing store. The recommended pattern is to initialize the global cache via `faciliter_lib.cache.cache_manager.set_cache()` using environment variables (recommended for deployments). This ensures the library selects the proper backend automatically and keeps application code backend-agnostic.

 Key high-level points for client usage:
 - Use `faciliter_lib.cache.cache_manager.set_cache` (no-args) during app startup so the module can select the best provider based on `CACHE_BACKEND`, installed libraries, and environment settings.
 - Use the facade helpers (`cache_get`, `cache_set`, `cache_delete`) throughout your code; they operate against the global cache installed by `set_cache()`.
 - Two built-in implementations exist: `RedisCache` and `ValkeyCache`. Prefer not to instantiate provider classes directly unless you need provider-specific features.

 Quick startup example (recommended - env-driven)

 ```python
 # app startup
 from faciliter_lib.cache.cache_manager import set_cache

 # Prefer environment-driven initialization; set_cache() will read
 # `CACHE_BACKEND` and provider-specific env vars and auto-detect clients.
 set_cache()

 # Later in app code
 from faciliter_lib.cache.cache_manager import cache_get, cache_set
 cache_set("user:123", {"name": "Alice"}, ttl=300)
 user = cache_get("user:123")
 ```

 When to use programmatic configuration

 - Use programmatic initialization only when you must construct provider configs in code (for tests, local scripts, or when envs are not available).
 - If you do initialize programmatically, call `set_cache(provider=..., config=..., ttl=...)` so the cache manager still performs selection and connection logic.

 Programmatic examples (optional)

 Example: explicit Redis cache instance

 ```python
 from faciliter_lib.cache.redis_cache import RedisCache
 from faciliter_lib.cache.redis_config import RedisConfig
 from faciliter_lib.cache.cache_manager import set_cache, cache_get, cache_set

 cfg = RedisConfig(host="localhost", port=6379, db=0)
 cache = RedisCache.from_config(cfg)
 set_cache(provider="redis", config=cfg)

 cache_set("user:123", {"name": "Alice"}, ttl=300)
 user = cache_get("user:123")
 ```

 Example: using Valkey as the backend (same facade)

 ```python
 from faciliter_lib.cache.valkey_cache import ValkeyCache
 from faciliter_lib.cache.valkey_config import ValkeyConfig
 from faciliter_lib.cache.cache_manager import set_cache, cache_get, cache_set

 cfg = ValkeyConfig(url="https://valkey.example.com", api_key="YOUR_KEY")
 cache = ValkeyCache.from_config(cfg)
 set_cache(provider="valkey", config=cfg)

 cache_set("session:abc", "some-value", ttl=600)
 value = cache_get("session:abc")
 ```

 Facade helper API (client-facing)

 - `set_cache(cache_instance)` or `set_cache(provider=..., config=...)`: Install the global cache instance used by helpers. Calling `set_cache()` with no arguments uses environment variables and auto-detection (recommended).
 - `cache_get(key, default=None)`: Retrieve a value by key (returns `default` if missing).
 - `cache_set(key, value, ttl=None)`: Store a value with optional TTL in seconds.
 - `cache_delete(key)`: Remove a key from the cache.

 Notes and best practices

 - Prefer using the facade helpers (`cache_get`, `cache_set`) in application code so switching providers requires only a single initialization change.
 - Encode TTLs in seconds. Providers should respect the `ttl` argument; `None` means persist until evicted by the provider.
 - Keys are plain strings; use a consistent prefixing strategy (for example, `myapp:users:{id}`) to avoid collisions when sharing a Redis instance.
 - Error handling: when initializing the global cache (e.g., network failures connecting to Redis), handle exceptions and decide whether your app should degrade gracefully (skip caching) or fail fast. `set_cache()` returns `True` when a usable cache was created, and `False` when caching is disabled.

 If you need to access provider-specific functionality, you can still import and use the concrete cache class directly, but that couples your code to the vendor implementation.

 ## Environment variables

 The library does not force a specific set of environment variable names, but the following is a recommended convention for simple deployments. Use these env vars to drive which backend to initialize and the provider connection details. Calling `set_cache()` with no args will read these vars and prefer the configured backend.

 - `CACHE_BACKEND`: Which backend to use. Allowed values: `redis`, `valkey`, `auto`. Default: `auto` (auto-detect based on installed clients and envs).

 Redis-related variables (used when `CACHE_BACKEND=redis` or when Redis is selected):

 - `REDIS_HOST`: Redis server host (default: `localhost`)
 - `REDIS_PORT`: Redis server port (default: `6379`)
 - `REDIS_DB`: Redis DB/index (default: `0`)
 - `REDIS_PASSWORD`: Optional Redis password

 Valkey-related variables (used when `CACHE_BACKEND=valkey`):

 - `VALKEY_URL`: Valkey service URL (e.g., `https://valkey.example.com`)
 - `VALKEY_API_KEY`: API key or token for Valkey

 ## When to explicitly specify Redis or Valkey

 - In most cases prefer `set_cache()` with environment-driven configuration so the library picks the appropriate backend.
 - If you must force a specific backend (for example, during tests or in environments where `valkey` is installed but you still want Redis), call `set_cache(provider="redis", config=...)` or `set_cache(provider="valkey", config=...)`.

 This approach keeps application code simple and ensures the cache manager performs consistent initialization, connection checks, and fallbacks.

