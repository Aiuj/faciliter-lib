# cache_manager.py
# Cache manager with support for Redis and Valkey providers
import os
from typing import Any, Optional, Literal, Union
import logging
from .base_cache import BaseCache
from .redis_cache import RedisCache
from .valkey_cache import ValkeyCache
from .redis_config import RedisConfig
from .valkey_config import ValkeyConfig

CacheProvider = Literal["redis", "valkey", "auto"]


def create_cache(
    provider: CacheProvider = "auto",
    name: str = '',
    config: Optional[Union[RedisConfig, ValkeyConfig]] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None
) -> BaseCache:
    """
    Create a cache instance based on the specified provider.
    
    Args:
        provider: Cache provider to use ("redis", "valkey", or "auto")
        name: Cache name/prefix
        config: Provider-specific configuration
        ttl: Time to live for cache entries
        time_out: Connection timeout
        
    Returns:
        BaseCache instance (RedisCache or ValkeyCache)
        
    Raises:
        ValueError: If provider is invalid or no suitable provider is found
    """
    if provider == "auto":
        provider = _auto_detect_provider()
    
    if provider == "redis":
        redis_config = config if isinstance(config, RedisConfig) else None
        return RedisCache(name=name, config=redis_config, ttl=ttl, time_out=time_out)
    elif provider == "valkey":
        valkey_config = config if isinstance(config, ValkeyConfig) else None
        return ValkeyCache(name=name, config=valkey_config, ttl=ttl, time_out=time_out)
    else:
        raise ValueError(f"Unsupported cache provider: {provider}")


def _auto_detect_provider() -> CacheProvider:
    """
    Automatically detect which cache provider to use based on environment variables.
    Priority: VALKEY_HOST > REDIS_HOST
    """
    if os.getenv("VALKEY_HOST"):
        return "valkey"
    elif os.getenv("REDIS_HOST"):
        return "redis"
    else:
        # Default to Redis if no specific config is found
        return "redis"

_cache_instance = None

def set_cache(
    provider: CacheProvider = "auto",
    config: Optional[Union[RedisConfig, ValkeyConfig]] = None,
    ttl: Optional[int] = None,
    time_out: Optional[int] = None
):
    """
    Explicitly initialize the global cache instance with custom parameters.
    Only creates a new instance if one does not already exist.
    
    Args:
        provider: Cache provider to use ("redis", "valkey", or "auto")
        config: Provider-specific configuration
        ttl: Time to live for cache entries
        time_out: Connection timeout
        
    Returns:
        bool: True if cache was successfully initialized, False otherwise
    """
    global _cache_instance
    if _cache_instance is not None and _cache_instance is not False:
        return True
    try:
        instance = create_cache(provider=provider, config=config, ttl=ttl, time_out=time_out)
        instance.connect()
        if instance.client is False:
            _cache_instance = False
            return False
        _cache_instance = instance
        return True
    except Exception as e:
        logging.error(f"[set_cache] Could not instantiate cache: {e}")
        _cache_instance = False
        return False

def get_cache() -> Optional[BaseCache]:
    """
    Return the global cache instance if initialized.
    """
    global _cache_instance
    if _cache_instance is None:
        set_cache()
    if _cache_instance is False or _cache_instance is None:
        return False
    return _cache_instance

def cache_get(input_data: Any) -> Optional[Any]:
    """
    Get cached output for the given input data.
    """
    cache = get_cache()
    if cache is False:
        return None
    return cache.get(input_data)

def cache_set(input_data: Any, output_data: Any, ttl: Optional[int] = None):
    """
    Set cached output for the given input data.
    """
    cache = get_cache()
    if cache is False:
        return
    cache.set(input_data, output_data, ttl)
