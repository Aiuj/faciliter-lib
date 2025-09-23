import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class RedisConfig:
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

    @classmethod
    def from_env(cls) -> "RedisConfig":
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            prefix=os.getenv("REDIS_PREFIX", "cache:"),
            ttl=int(os.getenv("REDIS_CACHE_TTL", 3600)),  # Default TTL of 1 hour
            password=os.getenv("REDIS_PASSWORD", None),
            time_out=int(os.getenv("REDIS_TIMEOUT", 4)),  # Default timeout of 4 seconds
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
        )
