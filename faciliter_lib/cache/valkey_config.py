import os
from dataclasses import dataclass
from typing import Optional

from .redis_config import RedisConfig


@dataclass
class ValkeyConfig(RedisConfig):
    """Valkey config re-uses RedisConfig fields for compatibility.

    Valkey is a drop-in replacement so it shares host/port/db/prefix/ttl fields.
    We inherit from `RedisConfig` and provide an env-based constructor that
    reads VALKEY-specific environment variables but populates the same fields.
    """

    @classmethod
    def from_env(cls) -> "ValkeyConfig":
        return cls(
            host=os.getenv("VALKEY_HOST", os.getenv("REDIS_HOST", "localhost")),
            port=int(os.getenv("VALKEY_PORT", os.getenv("REDIS_PORT", "6379"))),
            db=int(os.getenv("VALKEY_DB", os.getenv("REDIS_DB", "0"))),
            prefix=os.getenv("VALKEY_PREFIX", os.getenv("REDIS_PREFIX", "cache:")),
            ttl=int(os.getenv("VALKEY_CACHE_TTL", os.getenv("REDIS_CACHE_TTL", "3600"))),
            password=os.getenv("VALKEY_PASSWORD", os.getenv("REDIS_PASSWORD", None)),
            time_out=int(os.getenv("VALKEY_TIMEOUT", os.getenv("REDIS_TIMEOUT", "4"))),
            max_connections=int(os.getenv("VALKEY_MAX_CONNECTIONS", os.getenv("REDIS_MAX_CONNECTIONS", "50"))),
            retry_on_timeout=os.getenv("VALKEY_RETRY_ON_TIMEOUT", os.getenv("REDIS_RETRY_ON_TIMEOUT", "true")).lower() == "true"
        )
