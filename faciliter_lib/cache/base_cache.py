from abc import ABC, abstractmethod
import json
import hashlib
from typing import Any, Optional
import logging
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Base configuration class for cache providers"""
    host: str
    port: int
    db: int
    prefix: str
    ttl: int = 3600
    password: Optional[str] = None
    time_out: int = 4
    # Connection pool settings
    max_connections: int = 50
    retry_on_timeout: bool = True


class BaseCache(ABC):
    """Abstract base class for cache providers"""
    
    def __init__(self, name: str = '', config: CacheConfig = None, ttl: Optional[int] = None, time_out: Optional[int] = None):
        self.name = name or ''
        self.config = config
        self.ttl = ttl or (config.ttl if config else 3600)
        self.client = None
        self.connected = False
        self.time_out = time_out or (config.time_out if config else 4)

    @abstractmethod
    def connect(self):
        """Establish connection to the cache server"""
        pass

    @abstractmethod
    def _create_client(self) -> Any:
        """Create and return the client instance for the specific provider"""
        pass

    def _make_key(self, input_data: Any) -> str:
        """Generate a cache key from input data"""
        input_str = json.dumps(input_data, sort_keys=True, default=str)
        hash_key = hashlib.sha256(input_str.encode('utf-8')).hexdigest()
        prefix = self.config.prefix if self.config else "cache:"
        return f"{prefix}{self.name}:{hash_key}"

    @abstractmethod
    def get(self, input_data: Any) -> Optional[Any]:
        """Retrieve cached data for the given input"""
        pass

    @abstractmethod
    def set(self, input_data: Any, output_data: Any, ttl: Optional[int] = None):
        """Store data in cache with optional TTL"""
        pass

    def _serialize_data(self, data: Any) -> str:
        """Serialize data for storage"""
        return json.dumps(data, default=str)

    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from storage"""
        return json.loads(data)
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the cache server is healthy and responding"""
        pass

    def close(self):
        """Close connections and cleanup resources - override in subclasses if needed"""
        self.connected = False
        self.client = None