"""OpenSearch Configuration Settings.

This module contains configuration classes for OpenSearch providers
including connection settings, authentication, and index management.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .base_settings import BaseSettings, EnvParser, SettingsError


@dataclass(frozen=True)
class OpenSearchSettings(BaseSettings):
    """OpenSearch configuration settings."""
    
    host: str = "localhost"
    port: int = 9200
    use_ssl: bool = False
    verify_certs: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_on_timeout: bool = True
    connections_per_node: int = 5
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "OpenSearchSettings":
        """Create OpenSearch settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        settings_dict = {
            "host": EnvParser.get_env("OPENSEARCH_HOST", default="localhost"),
            "port": EnvParser.get_env("OPENSEARCH_PORT", default=9200, env_type=int),
            "use_ssl": EnvParser.get_env("OPENSEARCH_USE_SSL", default=False, env_type=bool),
            "verify_certs": EnvParser.get_env("OPENSEARCH_VERIFY_CERTS", default=False, env_type=bool),
            "username": EnvParser.get_env("OPENSEARCH_USERNAME"),
            "password": EnvParser.get_env("OPENSEARCH_PASSWORD"),
            "timeout": EnvParser.get_env("OPENSEARCH_TIMEOUT", default=30, env_type=int),
            "max_retries": EnvParser.get_env("OPENSEARCH_MAX_RETRIES", default=3, env_type=int),
            "retry_on_timeout": EnvParser.get_env("OPENSEARCH_RETRY_ON_TIMEOUT", default=True, env_type=bool),
            "connections_per_node": EnvParser.get_env("OPENSEARCH_CONNECTIONS_PER_NODE", default=5, env_type=int),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate OpenSearch configuration."""
        if self.port <= 0 or self.port > 65535:
            raise SettingsError("OpenSearch port must be between 1 and 65535")
        if self.timeout <= 0:
            raise SettingsError("Timeout must be positive")
        if self.max_retries < 0:
            raise SettingsError("Max retries must be non-negative")
        if self.connections_per_node <= 0:
            raise SettingsError("Connections per node must be positive")
        if (self.username is None) != (self.password is None):
            raise SettingsError("Both username and password must be provided together, or neither")
    
    @property
    def url(self) -> str:
        """Get OpenSearch URL."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    @property
    def auth(self) -> Optional[Tuple[str, str]]:
        """Get authentication tuple for OpenSearch client."""
        if self.username and self.password:
            return (self.username, self.password)
        return None
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get OpenSearch client configuration dictionary.
        
        Returns:
            Dictionary with OpenSearch client configuration suitable for opensearchpy.OpenSearch()
        """
        config = {
            "hosts": [{"host": self.host, "port": self.port}],
            "use_ssl": self.use_ssl,
            "verify_certs": self.verify_certs,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_on_timeout": self.retry_on_timeout,
            "connections_per_node": self.connections_per_node,
        }
        if self.auth:
            config["http_auth"] = self.auth
        return config
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "host": self.host,
            "port": self.port,
            "use_ssl": self.use_ssl,
            "verify_certs": self.verify_certs,
            "username": self.username,
            "password": "***" if self.password else None,  # Mask password
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_on_timeout": self.retry_on_timeout,
            "connections_per_node": self.connections_per_node,
        }
