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

    @classmethod
    def from_env(cls) -> "RedisConfig":
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            prefix=os.getenv("REDIS_PREFIX", "cache:"),
            ttl=int(os.getenv("REDIS_CACHE_TTL", 3600)),  # Default TTL of 1 hour
            password=os.getenv("REDIS_PASSWORD", None),
            time_out=int(os.getenv("REDIS_TIMEOUT", 4))  # Default timeout of 4 seconds
        )
