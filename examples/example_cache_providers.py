"""
Example demonstrating the new cache system with Redis and Valkey support.

This example shows how to:
1. Use auto-detection to choose between Redis and Valkey
2. Explicitly specify a cache provider
3. Use the existing cache helper functions
"""

import os
from core_lib.cache import (
    create_cache, set_cache, get_cache, cache_get, cache_set,
    RedisCache, ValkeyCache, RedisConfig, ValkeyConfig
)

def example_auto_detection():
    """Demonstrate automatic provider detection based on environment variables."""
    print("=== Auto-detection Example ===")
    
    # By default, this will use Redis if no VALKEY_HOST is set
    # If VALKEY_HOST is set, it will use Valkey
    # If both are set, it prefers Valkey
    cache = create_cache(provider="auto")
    print(f"Created cache of type: {type(cache).__name__}")
    
    # You can also set the global cache with auto-detection
    success = set_cache(provider="auto")
    print(f"Global cache set successfully: {success}")
    
    # Use the helper functions
    cache_set({"user_id": 123}, {"name": "John", "email": "john@example.com"})
    cached_user = cache_get({"user_id": 123})
    print(f"Cached user: {cached_user}")

def example_explicit_redis():
    """Demonstrate explicit Redis usage."""
    print("\n=== Explicit Redis Example ===")
    
    # Create explicit Redis cache with custom config
    config = RedisConfig(
        host="localhost",
        port=6379,
        db=1,
        prefix="myapp:",
        ttl=7200  # 2 hours
    )
    
    redis_cache = create_cache(provider="redis", config=config)
    print(f"Created Redis cache: {type(redis_cache).__name__}")
    
    # Or use directly
    redis_cache = RedisCache(name="users", config=config)
    redis_cache.connect()
    
    if redis_cache.connected:
        redis_cache.set({"query": "top_products"}, ["product1", "product2", "product3"])
        result = redis_cache.get({"query": "top_products"})
        print(f"Retrieved from Redis: {result}")
    else:
        print("Could not connect to Redis")

def example_explicit_valkey():
    """Demonstrate explicit Valkey usage."""
    print("\n=== Explicit Valkey Example ===")
    
    # Create explicit Valkey cache with custom config
    config = ValkeyConfig(
        host="localhost",
        port=6379,
        db=2,
        prefix="valkey:",
        ttl=3600  # 1 hour
    )
    
    try:
        valkey_cache = create_cache(provider="valkey", config=config)
        print(f"Created Valkey cache: {type(valkey_cache).__name__}")
        
        # Or use directly
        valkey_cache = ValkeyCache(name="analytics", config=config)
        valkey_cache.connect()
        
        if valkey_cache.connected:
            valkey_cache.set({"report": "monthly"}, {"revenue": 10000, "users": 250})
            result = valkey_cache.get({"report": "monthly"})
            print(f"Retrieved from Valkey: {result}")
        else:
            print("Could not connect to Valkey")
    except ImportError:
        print("Valkey package not available (this is expected if not installed)")

def example_environment_based():
    """Demonstrate environment-based configuration."""
    print("\n=== Environment-based Configuration ===")
    
    # Example environment variables you might set:
    print("Environment variables for Redis:")
    print("  REDIS_HOST=localhost")
    print("  REDIS_PORT=6379")
    print("  REDIS_DB=0")
    print("  REDIS_PREFIX=cache:")
    print("  REDIS_CACHE_TTL=3600")
    
    print("\nEnvironment variables for Valkey:")
    print("  VALKEY_HOST=localhost")
    print("  VALKEY_PORT=6379")
    print("  VALKEY_DB=0")
    print("  VALKEY_PREFIX=cache:")
    print("  VALKEY_CACHE_TTL=3600")
    
    # If VALKEY_HOST is set, auto-detection will prefer Valkey
    # Otherwise, it will use Redis
    
    # You can also force a specific provider:
    print("\nForcing Redis even if VALKEY_HOST is set:")
    cache = create_cache(provider="redis")
    print(f"Forced cache type: {type(cache).__name__}")

if __name__ == "__main__":
    # Note: These examples assume you have Redis running locally
    # Some may fail if the servers are not available, which is expected
    
    try:
        example_auto_detection()
        example_explicit_redis()
        example_explicit_valkey()
        example_environment_based()
    except Exception as e:
        print(f"Example failed (expected if cache servers not running): {e}")