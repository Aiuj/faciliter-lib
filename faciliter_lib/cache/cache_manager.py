# cache.py
# Generic Redis-based cache for input/output pairs
import redis
import json
import hashlib
from typing import Any, Optional
import logging
from .redis_config import RedisConfig

class RedisCache:
    def __init__(self, name: str = '', config: RedisConfig = None, ttl: Optional[int] = None, time_out: Optional[int] = None):
        # Allow first argument to be a name (prefix), for compatibility with test usage
        self.name = name or ''
        self.config = config or RedisConfig.from_env()
        self.ttl = ttl or self.config.ttl
        self.client = None
        self.connected = False
        self._redis_kwargs = {
            'host': self.config.host,
            'port': self.config.port,
            'db': self.config.db,
            'decode_responses': True,
            'socket_connect_timeout': time_out or self.config.time_out,
            'socket_timeout': time_out or self.config.time_out
        }
        if self.config.password:
            self._redis_kwargs['password'] = self.config.password

    def connect(self):
        try:
            self.client = redis.Redis(**self._redis_kwargs)
            try:
                result = self.client.ping()
                if result:
                    self.connected = True
                else:
                    self.connected = False
                    self.client = False
                    logging.error("[RedisCache] Redis ping failed.")
            except Exception as e:
                logging.error(f"[RedisCache] Could not connect to Redis server: {e}")
                self.client = False
                self.connected = False
        except Exception as e:
            logging.error(f"[RedisCache] Could not connect to Redis server: {e}")
            self.client = False
            self.connected = False

    def _make_key(self, input_data: Any) -> str:
        # Use a hash of the input as the key with configured prefix
        input_str = json.dumps(input_data, sort_keys=True, default=str)
        hash_key = hashlib.sha256(input_str.encode('utf-8')).hexdigest()
        return f"{self.config.prefix}{self.name}:{hash_key}"

    def get(self, input_data: Any) -> Optional[Any]:
        if self.client is False:
            return None
        key = self._make_key(input_data)
        value = self.client.get(key)
        if value is not None:
            return json.loads(value)
        return None

    def set(self, input_data: Any, output_data: Any, ttl: Optional[int] = None):
        if self.client is False:
            return
        key = self._make_key(input_data)
        value = json.dumps(output_data, default=str)
        ttl_to_use = ttl if ttl is not None else self.ttl
        self.client.setex(key, ttl_to_use, value)
        # Debug: log TTL set
        logging.debug(f"[RedisCache] Set key {key} with TTL {ttl_to_use}")
        # For some Redis test/mocks, force expire as fallback
        try:
            self.client.expire(key, ttl_to_use)
        except Exception:
            pass

_cache_instance = None

def set_cache(config: Optional[RedisConfig] = None, ttl: Optional[int] = None, time_out: Optional[int] = None):
    """
    Explicitly initialize the global cache instance with custom parameters.
    Only creates a new instance if one does not already exist.
    """
    global _cache_instance
    if _cache_instance is not None and _cache_instance is not False:
        return True
    try:
        instance = RedisCache(config=config, ttl=ttl, time_out=time_out)
        instance.connect()
        if instance.client is False:
            _cache_instance = False
            return False
        _cache_instance = instance
        return True
    except Exception as e:
        logging.error(f"[set_cache] Could not instantiate RedisCache: {e}")
        _cache_instance = False
        return False

def get_cache() -> Optional[RedisCache]:
    """
    Return the global RedisCache instance if initialized.
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
