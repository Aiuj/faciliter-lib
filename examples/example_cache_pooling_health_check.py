#!/usr/bin/env python3
"""
Example demonstrating Redis and Valkey cache with connection pooling and health checks.

This example shows:
1. Connection pooling configuration
2. Health check functionality
3. Resource cleanup with close() method
4. Connection pool settings via environment variables

Environment variables for connection pooling:
- REDIS_MAX_CONNECTIONS: Maximum connections in pool (default: 50)
- REDIS_RETRY_ON_TIMEOUT: Retry on connection timeout (default: true)
- VALKEY_MAX_CONNECTIONS: Maximum connections for Valkey pool (default: 50)  
- VALKEY_RETRY_ON_TIMEOUT: Retry on timeout for Valkey (default: true)
"""

import time
import logging
from faciliter_lib.cache import RedisCache, ValkeyCache
from faciliter_lib.cache.redis_config import RedisConfig
from faciliter_lib.cache.valkey_config import ValkeyConfig

# Setup logging to see pool management messages
logging.basicConfig(level=logging.INFO)

def demo_redis_pooling():
    """Demonstrate Redis cache with connection pooling and health check"""
    print("=== Redis Cache with Connection Pooling Demo ===")
    
    # Create config with custom pool settings
    config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
        prefix="demo:",
        ttl=300,
        max_connections=10,  # Smaller pool for demo
        retry_on_timeout=True
    )
    
    # Create cache instance
    cache = RedisCache(name="demo", config=config)
    
    try:
        # Connect to Redis
        cache.connect()
        
        if cache.connected:
            print("✅ Connected to Redis successfully")
            
            # Perform health check
            health_status = cache.health_check()
            print(f"Health check result: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
            
            # Test cache operations
            test_data = {"message": "Hello from Redis with pooling!", "timestamp": time.time()}
            cache.set("test_key", test_data)
            
            retrieved = cache.get("test_key")
            if retrieved:
                print(f"✅ Cache operation successful: {retrieved['message']}")
            else:
                print("❌ Cache operation failed")
        else:
            print("❌ Failed to connect to Redis")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always cleanup connection pool
        cache.close()
        print("🧹 Connection pool closed")


def demo_valkey_pooling():
    """Demonstrate Valkey cache with connection pooling and health check"""
    print("\n=== Valkey Cache with Connection Pooling Demo ===")
    
    try:
        # Create config with custom pool settings
        config = ValkeyConfig(
            host="localhost", 
            port=6380,  # Typical Valkey port
            db=0,
            prefix="valkey_demo:",
            ttl=300,
            max_connections=10,
            retry_on_timeout=True
        )
        
        # Create cache instance
        cache = ValkeyCache(name="demo", config=config)
        
        # Connect to Valkey
        cache.connect()
        
        if cache.connected:
            print("✅ Connected to Valkey successfully")
            
            # Perform health check
            health_status = cache.health_check()
            print(f"Health check result: {'✅ Healthy' if health_status else '❌ Unhealthy'}")
            
            # Test cache operations
            test_data = {"message": "Hello from Valkey with pooling!", "timestamp": time.time()}
            cache.set("test_key", test_data)
            
            retrieved = cache.get("test_key")
            if retrieved:
                print(f"✅ Cache operation successful: {retrieved['message']}")
            else:
                print("❌ Cache operation failed")
        else:
            print("❌ Failed to connect to Valkey")
            
    except ImportError:
        print("⚠️ Valkey package not installed - skipping Valkey demo")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always cleanup connection pool
        try:
            cache.close()
            print("🧹 Connection pool closed")
        except:
            pass


def demo_environment_config():
    """Demonstrate loading pool config from environment variables"""
    print("\n=== Environment Configuration Demo ===")
    
    print("To use custom pool settings, set these environment variables:")
    print("export REDIS_MAX_CONNECTIONS=100")
    print("export REDIS_RETRY_ON_TIMEOUT=true")
    print("export VALKEY_MAX_CONNECTIONS=75")
    print("export VALKEY_RETRY_ON_TIMEOUT=false")
    
    # Load config from environment
    redis_config = RedisConfig.from_env()
    valkey_config = ValkeyConfig.from_env()
    
    print(f"\nCurrent Redis pool config:")
    print(f"  Max connections: {redis_config.max_connections}")
    print(f"  Retry on timeout: {redis_config.retry_on_timeout}")
    
    print(f"\nCurrent Valkey pool config:")
    print(f"  Max connections: {valkey_config.max_connections}")
    print(f"  Retry on timeout: {valkey_config.retry_on_timeout}")


if __name__ == "__main__":
    print("Connection Pooling and Health Check Demo")
    print("========================================")
    
    # Note: These demos will only work if Redis/Valkey servers are running
    demo_redis_pooling()
    demo_valkey_pooling()
    demo_environment_config()
    
    print("\n🎉 Demo completed!")
    print("\nKey benefits of connection pooling:")
    print("• Reduced connection overhead")
    print("• Better resource management")
    print("• Improved performance under load")
    print("• Automatic connection reuse")
    print("• Configurable pool size and behavior")