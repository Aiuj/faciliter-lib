try:
    import valkey
except ImportError:
    valkey = None
from typing import Any, Optional
import logging
from .base_cache import BaseCache
from .valkey_config import ValkeyConfig


class ValkeyCache(BaseCache):
    """Valkey-specific cache implementation"""
    
    def __init__(self, name: str = '', config: ValkeyConfig = None, ttl: Optional[int] = None, time_out: Optional[int] = None):
        config = config or ValkeyConfig.from_env()
        super().__init__(name, config, ttl, time_out)
        self.config: ValkeyConfig = config
        self._valkey_kwargs = {
            'host': self.config.host,
            'port': self.config.port,
            'db': self.config.db,
            'decode_responses': True,
            'socket_connect_timeout': self.time_out,
            'socket_timeout': self.time_out
        }
        if self.config.password:
            self._valkey_kwargs['password'] = self.config.password

    def _create_client(self) -> Any:
        """Create Valkey client"""
        if valkey is None:
            raise ImportError("valkey package is not installed")
        return valkey.Valkey(**self._valkey_kwargs)

    def connect(self):
        """Establish connection to Valkey server"""
        try:
            self.client = self._create_client()
            try:
                result = self.client.ping()
                if result:
                    self.connected = True
                else:
                    self.connected = False
                    self.client = False
                    logging.error("[ValkeyCache] Valkey ping failed.")
            except Exception as e:
                logging.error(f"[ValkeyCache] Could not connect to Valkey server: {e}")
                self.client = False
                self.connected = False
        except Exception as e:
            logging.error(f"[ValkeyCache] Could not connect to Valkey server: {e}")
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
        logging.debug(f"[ValkeyCache] Set key {key} with TTL {ttl_to_use}")
        # For some Valkey test/mocks, force expire as fallback
        try:
            self.client.expire(key, ttl_to_use)
        except Exception:
            pass