"""Cache Provider Configuration Settings.

This module contains configuration classes for cache providers
including Redis and Valkey.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from .base_settings import BaseSettings, SettingsError, EnvParser


@dataclass(frozen=True)
class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    provider: str = "redis"
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    prefix: str = "cache:"
    ttl: int = 3600
    password: Optional[str] = None
    timeout: int = 4
    max_connections: int = 50
    retry_on_timeout: bool = True
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "CacheSettings":
        """Create cache settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        # Support both Redis and Valkey
        provider = EnvParser.get_env("CACHE_PROVIDER", default="redis")
        
        if provider.lower() == "valkey":
            # Valkey-specific env vars with Redis fallbacks
            settings_dict = {
                "provider": "valkey",
                "host": EnvParser.get_env("VALKEY_HOST", "REDIS_HOST", default="localhost"),
                "port": EnvParser.get_env("VALKEY_PORT", "REDIS_PORT", default=6379, env_type=int),
                "db": EnvParser.get_env("VALKEY_DB", "REDIS_DB", default=0, env_type=int),
                "prefix": EnvParser.get_env("VALKEY_PREFIX", "REDIS_PREFIX", default="cache:"),
                "ttl": EnvParser.get_env("VALKEY_CACHE_TTL", "REDIS_CACHE_TTL", default=3600, env_type=int),
                "password": EnvParser.get_env("VALKEY_PASSWORD", "REDIS_PASSWORD"),
                "timeout": EnvParser.get_env("VALKEY_TIMEOUT", "REDIS_TIMEOUT", default=4, env_type=int),
            }
        else:
            # Redis settings
            settings_dict = {
                "provider": "redis",
                "host": EnvParser.get_env("REDIS_HOST", default="localhost"),
                "port": EnvParser.get_env("REDIS_PORT", default=6379, env_type=int),
                "db": EnvParser.get_env("REDIS_DB", default=0, env_type=int),
                "prefix": EnvParser.get_env("REDIS_PREFIX", default="cache:"),
                "ttl": EnvParser.get_env("REDIS_CACHE_TTL", default=3600, env_type=int),
                "password": EnvParser.get_env("REDIS_PASSWORD"),
                "timeout": EnvParser.get_env("REDIS_TIMEOUT", default=4, env_type=int),
            }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate cache configuration."""
        if self.port <= 0 or self.port > 65535:
            raise SettingsError("Port must be between 1 and 65535")
        if self.db < 0:
            raise SettingsError("Database number must be non-negative")
        if self.ttl <= 0:
            raise SettingsError("TTL must be positive")
        if self.timeout <= 0:
            raise SettingsError("Timeout must be positive")
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "provider": self.provider,
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "prefix": self.prefix,
            "ttl": self.ttl,
            "password": self.password,
            "timeout": self.timeout,
            "max_connections": self.max_connections,
            "retry_on_timeout": self.retry_on_timeout,
        }