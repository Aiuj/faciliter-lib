"""
cache.py - Redis-based cache utility for Faciliter stack

This module provides a generic Redis-based cache for input/output pairs, useful for caching results of expensive operations in applications using the Faciliter stack.

Classes:
    RedisCache: Handles connection and operations with Redis.

Functions:
    set_cache: Initializes the global singleton cache instance with custom parameters.
    get_cache: Returns the singleton RedisCache instance if initialized.
    cache_get: Gets a cached value for a given input.
    cache_set: Sets a cached value for a given input.

Configuration:
    The cache can be configured via environment variables:

    REDIS_HOST: Redis server host (default: localhost)
    REDIS_PORT: Redis server port (default: 6379)
    REDIS_DB: Redis database number (default: 0)
    REDIS_PASSWORD: (Optional) Redis password
    REDIS_PREFIX: Prefix for all cache keys (e.g., myapp:).  
      This allows you to namespace cache entries for different applications.
    REDIS_CACHE_TTL: Default time-to-live for cache entries in seconds (e.g., 3600).  
      This controls how long cached values persist.
    REDIS_TIMEOUT: Redis connection timeout in seconds (default: 4)

    You can override these parameters programmatically when calling set_cache() if you need a specific configuration for your app or use case.

Example usage:
    from faciliter_lib import set_cache, cache_get, cache_set

    # Initialize the cache singleton (should be done once at startup)
    set_cache(name="my_app", ttl=1800)  # name and ttl are optional

    input_data = {"query": "expensive operation"}
    result = cache_get(input_data)
    if result is None:
        # Compute result
        result = compute_expensive_result(input_data)
        cache_set(input_data, result, ttl=600)  # Optionally override TTL for this entry
"""

<!-- filepath: c:\Dev\github\faciliter-lib\docs\cache.md -->
# Redis-based Cache Utility for Faciliter Stack

This module provides a generic Redis-based cache for input/output pairs, useful for caching results of expensive operations in applications using the Faciliter stack.

## Classes

- `RedisCache`: Handles connection and operations with Redis.

## Functions

- `set_cache`: Initializes the global singleton cache instance with custom parameters.
- `get_cache`: Returns the singleton RedisCache instance if initialized.
- `cache_get`: Gets a cached value for a given input.
- `cache_set`: Sets a cached value for a given input.

## Configuration

The cache can be configured via environment variables:

- `REDIS_HOST`: Redis server host (default: `localhost`)
- `REDIS_PORT`: Redis server port (default: `6379`)
- `REDIS_DB`: Redis database number (default: `0`)
- `REDIS_PASSWORD`: (Optional) Redis password
- `REDIS_PREFIX`: Prefix for all cache keys (e.g., `myapp:`).  
  This allows you to namespace cache entries for different applications.
- `REDIS_CACHE_TTL`: Default time-to-live for cache entries in seconds (e.g., `3600`).  
  This controls how long cached values persist.
- `REDIS_TIMEOUT`: Redis connection timeout in seconds (default: `4`)

You can override these parameters programmatically when calling `set_cache()` if you need a specific configuration for your app or use case.

## Example Usage

```python
from faciliter_lib import cache_get, cache_set

input_data = {"query": "expensive operation"}
result = cache_get(input_data)
if result is None:
    # Compute result
    result = compute_expensive_result(input_data)
    cache_set(input_data, result, ttl=600)  # Optionally override TTL for this entry
```

For advanced use cases, you can explicitly initialize the cache singleton with custom parameters (e.g., to override the name or TTL):

```python
from faciliter_lib import set_cache, cache_get, cache_set

# Advanced: initialize the cache singleton with a specific name or TTL
set_cache(name="my_app", ttl=1800)

input_data = {"query": "expensive operation"}
result = cache_get(input_data)
if result is None:
    result = compute_expensive_result(input_data)
    cache_set(input_data, result, ttl=600)
```

Or using a direct cache instance:

```python
from faciliter_lib import RedisCache

cache = RedisCache("my_app")
cache.connect()
if cache.connected:
    value = cache.get(input_data)
    if value is None:
        result = compute_expensive_result(input_data)
        cache.set(input_data, result, ttl=600)
```

## Notes

- Using `REDIS_PREFIX` and `REDIS_CACHE_TTL` in your environment allows you to define cache namespaces and lifetimes per application.
- You can also specify these parameters directly in `set_cache()` or when creating a `RedisCache` instance for more granular control.
- If Redis is unavailable, cache operations will be no-ops and your application will continue to function.
