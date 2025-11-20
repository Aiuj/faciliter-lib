#!/usr/bin/env python3
"""
Example usage of core-lib cache functionality.
This script demonstrates how to use the Redis cache.
"""

from core_lib import RedisCache, cache_get, cache_set, set_cache, parse_from

def main():
    print("🧰 core-lib Cache Example")
    print("-" * 40)
    
    # Test MCP utils
    print("\n📋 Testing MCP Utils:")
    test_data = '{"message": "hello", "value": 42}'
    parsed = parse_from(test_data)
    print(f"Parsed JSON: {parsed}")
    
    # Test cache functionality (works even without Redis)
    print("\n💾 Testing Cache Functions:")

    # Initialize the cache singleton before using cache_get/cache_set
    set_cache(name="example_app")

    # This will work even if Redis is not available
    test_input = {"query": "test data", "params": [1, 2, 3]}
    
    # Try to get from cache
    result = cache_get(test_input)
    if result is None:
        print("Cache miss - computing result...")
        result = {"computed": True, "data": [x*2 for x in test_input["params"]]}
        cache_set(test_input, result, ttl=60)
        print(f"Computed and cached: {result}")
    else:
        print(f"Cache hit: {result}")
    
    # Test direct cache instance
    print("\n🔧 Testing Direct Cache Instance:")
    cache = RedisCache("direct_example")
    cache.connect()
    
    if cache.connected:
        print("✅ Connected to Redis successfully")
        
        # Test cache operations
        test_key = {"test": "direct_access"}
        cached_value = cache.get(test_key)
        
        if cached_value is None:
            new_value = {"timestamp": "2025-01-27", "source": "direct_cache"}
            cache.set(test_key, new_value, ttl=120)
            print(f"Stored in cache: {new_value}")
        else:
            print(f"Retrieved from cache: {cached_value}")
    else:
        print("⚠️  Redis not available - cache operations will be no-ops")
    
    print("\n✨ Example completed successfully!")

if __name__ == "__main__":
    main()
