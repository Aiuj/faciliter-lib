import redis
from typing import Any, Optional
import logging
from .base_cache import BaseCache
from .redis_config import RedisConfig


class RedisCache(BaseCache):
    """Redis-specific cache implementation"""
    
    def __init__(self, name: str = '', config: RedisConfig = None, ttl: Optional[int] = None, time_out: Optional[int] = None):
        config = config or RedisConfig.from_env()
        super().__init__(name, config, ttl, time_out)
        self.config: RedisConfig = config
        self._redis_kwargs = {
            'host': self.config.host,
            'port': self.config.port,
            'db': self.config.db,
            'decode_responses': True,
            'socket_connect_timeout': self.time_out,
            'socket_timeout': self.time_out
        }
        if self.config.password:
            self._redis_kwargs['password'] = self.config.password

    def _create_client(self) -> redis.Redis:
        """Create Redis client"""
        return redis.Redis(**self._redis_kwargs)

    def connect(self):
        """Establish connection to Redis server"""
        try:
            self.client = self._create_client()
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

    def get(self, input_data: Any) -> Optional[Any]:
        """Retrieve cached data for the given input"""
        if self.client is False:
            return None
        key = self._make_key(input_data)
        value = self.client.get(key)
        if value is not None:
            return self._deserialize_data(value)
        return None

    def set(self, input_data: Any, output_data: Any, ttl: Optional[int] = None):
        """Store data in cache with optional TTL"""
        if self.client is False:
            return
        key = self._make_key(input_data)
        value = self._serialize_data(output_data)
        ttl_to_use = ttl if ttl is not None else self.ttl
        self.client.setex(key, ttl_to_use, value)
        # Debug: log TTL set
        logging.debug(f"[RedisCache] Set key {key} with TTL {ttl_to_use}")
        # For some Redis test/mocks, force expire as fallback
        try:
            self.client.expire(key, ttl_to_use)
        except Exception:
            pass