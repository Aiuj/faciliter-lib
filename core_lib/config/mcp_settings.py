"""MCP Server Configuration Settings.

This module contains configuration classes for Model Context Protocol (MCP) servers.
"""

from typing import Optional, List, Union
from pathlib import Path
from .base_settings import BaseSettings, EnvParser


class MCPServerSettings(BaseSettings):
    """MCP Server configuration settings.
    
    Manages configuration for Model Context Protocol servers including
    server metadata, network settings, and transport configuration.
    """

    def __init__(
        self,
        server_name: str = "app-server",
        version: str = "0.1.0", 
        host: str = "0.0.0.0",
        port: int = 8204,
        url: Optional[str] = None,
        timeout: int = 30,
        transport: str = "streamable-http",
        **kwargs
    ):
        """Initialize MCP server settings.
        
        Args:
            server_name: Name of the MCP server
            version: Version of the MCP server
            host: Host address to bind the server to
            port: Port number for the server
            url: Full URL for the server (auto-generated if not provided)
            timeout: Request timeout in seconds
            transport: MCP transport type (streamable-http, stdio, websocket)
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.server_name = server_name
        self.version = version
        self.host = host
        self.port = port
        self.url = url or f"http://{host}:{port}"
        self.timeout = timeout
        self.transport = transport

    @classmethod
    def get_config_spec(cls) -> dict:
        """Get configuration specification for environment variable parsing."""
        return {
            "server_name": {
                "env_vars": ["MCP_SERVER_NAME", "APP_NAME"],
                "default": "app-server",
                "env_type": str,
                "description": "Name of the MCP server"
            },
            "version": {
                "env_vars": ["MCP_SERVER_VERSION", "APP_VERSION"],
                "default": "0.1.0",
                "env_type": str,
                "description": "Version of the MCP server"
            },
            "host": {
                "env_vars": ["MCP_SERVER_HOST", "SERVER_HOST"],
                "default": "0.0.0.0",
                "env_type": str,
                "description": "Host address to bind the server to"
            },
            "port": {
                "env_vars": ["MCP_SERVER_PORT", "MCP_PORT", "SERVER_PORT"],
                "default": 8204,
                "env_type": int,
                "description": "Port number for the server"
            },
            "url": {
                "env_vars": ["MCP_SERVER_URL"],
                "default": None,
                "env_type": str,
                "description": "Full URL for the server (auto-generated if not provided)"
            },
            "timeout": {
                "env_vars": ["MCP_SERVER_TIMEOUT"],
                "default": 30,
                "env_type": int,
                "description": "Request timeout in seconds"
            },
            "transport": {
                "env_vars": ["MCP_TRANSPORT"],
                "default": "streamable-http",
                "env_type": str,
                "description": "MCP transport type (streamable-http, stdio, websocket)"
            }
        }
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "MCPServerSettings":
        """Create MCP server settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        config_spec = cls.get_config_spec()
        settings_dict = {}
        
        for field_name, config in config_spec.items():
            env_vars = config["env_vars"]
            default = config["default"]
            env_type = config["env_type"]
            
            value = None
            for env_var in env_vars:
                value = EnvParser.get_env(env_var, env_type=env_type)
                if value is not None:
                    break
            
            if value is None:
                value = default
            
            settings_dict[field_name] = value
        
        # Auto-generate URL if not provided
        if not settings_dict.get("url"):
            host = settings_dict["host"]
            port = settings_dict["port"]
            settings_dict["url"] = f"http://{host}:{port}"
        
        settings_dict.update(overrides)
        return cls(**settings_dict)

    def validate(self) -> List[str]:
        """Validate MCP server configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append("Port must be between 1 and 65535")
        
        # Validate timeout
        if self.timeout <= 0:
            errors.append("Timeout must be positive")
        
        # Validate transport type
        valid_transports = ["streamable-http", "stdio", "websocket"]
        if self.transport not in valid_transports:
            errors.append(f"Transport must be one of: {', '.join(valid_transports)}")
        
        # Validate server name
        if not self.server_name or not self.server_name.strip():
            errors.append("Server name cannot be empty")
        
        # Validate version format (basic semver check)
        if not self.version or not self.version.strip():
            errors.append("Version cannot be empty")
        
        return errors

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "server_name": self.server_name,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "url": self.url,
            "timeout": self.timeout,
            "transport": self.transport
        }

    def get_server_info(self) -> dict:
        """Get server information for MCP protocol responses."""
        return {
            "name": self.server_name,
            "version": self.version
        }

    def get_connection_config(self) -> dict:
        """Get connection configuration for MCP clients."""
        config = {
            "url": self.url,
            "timeout": self.timeout,
            "transport": self.transport
        }
        
        if self.transport == "streamable-http":
            config.update({
                "host": self.host,
                "port": self.port
            })
        
        return config

    def __repr__(self) -> str:
        return (
            f"MCPServerSettings("
            f"server_name='{self.server_name}', "
            f"version='{self.version}', "
            f"host='{self.host}', "
            f"port={self.port}, "
            f"transport='{self.transport}'"
            f")"
        )