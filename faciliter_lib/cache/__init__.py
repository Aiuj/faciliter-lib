"""Cache module for faciliter-lib."""

from .cache_manager import create_cache, set_cache, get_cache, cache_get, cache_set
from .base_cache import BaseCache, CacheConfig
from .redis_cache import RedisCache
from .valkey_cache import ValkeyCache
from .redis_config import RedisConfig
from .valkey_config import ValkeyConfig

__all__ = [
    'BaseCache', 'CacheConfig',
    'RedisCache', 'ValkeyCache',
    'RedisConfig', 'ValkeyConfig',
    'create_cache', 'set_cache', 'get_cache', 'cache_get', 'cache_set'
]
