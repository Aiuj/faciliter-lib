"""FastAPI HTTP Server Configuration Settings.

Configuration class for an optional FastAPI HTTP server that can be used by
downstream apps. Mirrors the style and API of MCPServerSettings to keep
consistency across server configs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union
from pathlib import Path

from .base_settings import BaseSettings, EnvParser, SettingsError


@dataclass(frozen=True)
class FastAPIServerSettings(BaseSettings):
    """FastAPI HTTP server configuration settings.

    Fields mirror the MCP server style for a consistent developer experience.
    """

    host: str = "0.0.0.0"
    port: int = 8096
    reload: bool = False
    url: Optional[str] = None

    api_auth_enabled: bool = False
    api_key_header_name: str = "x-api-key"
    api_keys: List[str] = None  # parsed from comma-separated env var

    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides,
    ) -> "FastAPIServerSettings":
        """Create FastAPI server settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)

        host = EnvParser.get_env("FASTAPI_HOST", default="0.0.0.0")
        port = EnvParser.get_env("FASTAPI_PORT", default=8096, env_type=int)
        reload = EnvParser.get_env("FASTAPI_RELOAD", default=False, env_type=bool)
        url = EnvParser.get_env("FASTAPI_URL", default=None)

        api_auth_enabled = EnvParser.get_env("API_AUTH_ENABLED", default=False, env_type=bool)
        api_key_header_name = EnvParser.get_env("API_KEY_HEADER_NAME", default="x-api-key")
        api_keys = EnvParser.get_env("API_KEYS", default=[], env_type=list)

        if url is None:
            url = f"http://{host}:{port}"

        settings = {
            "host": host,
            "port": port,
            "reload": reload,
            "url": url,
            "api_auth_enabled": api_auth_enabled,
            "api_key_header_name": api_key_header_name,
            "api_keys": api_keys,
        }

        settings.update(overrides)
        return cls(**settings)

    def validate(self) -> None:
        """Validate FastAPI server configuration."""
        if not (1 <= int(self.port) <= 65535):
            raise SettingsError("Port must be between 1 and 65535")

        if self.api_auth_enabled:
            if not self.api_key_header_name or not self.api_key_header_name.strip():
                raise SettingsError("API key header name cannot be empty when API auth is enabled")
            if not self.api_keys or len(self.api_keys) == 0:
                raise SettingsError("API_KEYS must contain at least one key when API auth is enabled")

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "url": self.url or f"http://{self.host}:{self.port}",
            "api_auth_enabled": self.api_auth_enabled,
            "api_key_header_name": self.api_key_header_name,
            "api_keys": list(self.api_keys or []),
        }

    def get_connection_config(self) -> dict:
        """Return minimal connection info for server startup/clients."""
        return {"url": self.as_dict()["url"], "host": self.host, "port": self.port}
