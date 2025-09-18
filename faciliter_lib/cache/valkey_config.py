import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValkeyConfig:
    host: str
    port: int
    db: int
    prefix: str
    ttl: int = 3600
    password: Optional[str] = None
    time_out: int = 4

    @classmethod
    def from_env(cls) -> "ValkeyConfig":
        return cls(
            host=os.getenv("VALKEY_HOST", "localhost"),
            port=int(os.getenv("VALKEY_PORT", 6379)),
            db=int(os.getenv("VALKEY_DB", 0)),
            prefix=os.getenv("VALKEY_PREFIX", "cache:"),
            ttl=int(os.getenv("VALKEY_CACHE_TTL", 3600)),  # Default TTL of 1 hour
            password=os.getenv("VALKEY_PASSWORD", None),
            time_out=int(os.getenv("VALKEY_TIMEOUT", 4))  # Default timeout of 4 seconds
        )
