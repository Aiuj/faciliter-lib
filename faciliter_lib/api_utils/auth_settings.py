"""Authentication settings configuration.

Configuration for time-based authentication using private keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from ..config.base_settings import BaseSettings, EnvParser, SettingsError


@dataclass(frozen=True)
class AuthSettings(BaseSettings):
    """Authentication settings for time-based HMAC authentication.
    
    This configuration manages the private key used for generating and
    verifying time-based authentication keys between applications.
    
    Environment Variables:
        AUTH_PRIVATE_KEY: The secret private key for authentication
        AUTH_ENABLED: Whether authentication is enabled (default: False)
        AUTH_KEY_HEADER_NAME: HTTP header name for auth key (default: x-auth-key)
    
    Example:
        ```python
        # From environment
        settings = AuthSettings.from_env()
        
        # With overrides
        settings = AuthSettings.from_env(
            auth_enabled=True,
            auth_private_key="my-secret-key"
        )
        ```
    """
    
    auth_enabled: bool = False
    auth_private_key: Optional[str] = None
    auth_key_header_name: str = "x-auth-key"
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "AuthSettings":
        """Create authentication settings from environment variables.
        
        Args:
            load_dotenv: Whether to load .env files
            dotenv_paths: Custom paths to search for .env files
            **overrides: Direct value overrides
            
        Returns:
            AuthSettings instance
        """
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        settings_dict = {
            "auth_enabled": EnvParser.get_env(
                "AUTH_ENABLED",
                default=False,
                env_type=bool
            ),
            "auth_private_key": EnvParser.get_env(
                "AUTH_PRIVATE_KEY",
                default=None
            ),
            "auth_key_header_name": EnvParser.get_env(
                "AUTH_KEY_HEADER_NAME",
                default="x-auth-key"
            ),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate authentication settings.
        
        Raises:
            SettingsError: If auth is enabled but private key is not set
        """
        if self.auth_enabled:
            if not self.auth_private_key or not self.auth_private_key.strip():
                raise SettingsError(
                    "AUTH_PRIVATE_KEY must be set when AUTH_ENABLED is True"
                )
            if len(self.auth_private_key) < 16:
                raise SettingsError(
                    "AUTH_PRIVATE_KEY should be at least 16 characters for security"
                )
        
        if not self.auth_key_header_name or not self.auth_key_header_name.strip():
            raise SettingsError("auth_key_header_name cannot be empty")
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation.
        
        Note: Excludes the private key for security when serializing.
        """
        return {
            "auth_enabled": self.auth_enabled,
            "auth_private_key": "***" if self.auth_private_key else None,
            "auth_key_header_name": self.auth_key_header_name,
        }
