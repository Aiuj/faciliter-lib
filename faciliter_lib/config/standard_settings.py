"""
Standard Settings Implementation - Modular Version

Standard settings implementation that combines core application settings
with provider-specific configurations for LLM, embeddings, cache, tracing, 
database, and MCP server.

This module provides a unified settings interface that can be easily configured
for any Faciliter application, with automatic detection and configuration of
the services needed by the application. It also provides an easy extension
mechanism for adding custom settings.

Features:
- Inherits from AppSettings for core app configuration
- Optional LLM, embeddings, cache, tracing, database, and MCP server configuration
- Auto-detection of required services
- Easy extension for custom settings via extend_from_env
- Comprehensive validation
- Modular structure with separate files for each service type
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .base_settings import BaseSettings, SettingsError, EnvParser, NullConfig
from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embeddings_settings import EmbeddingsSettings
from .cache_settings import CacheSettings
from .tracing_settings import TracingSettings
from .database_settings import DatabaseSettings
from .mcp_settings import MCPServerSettings
from .fastapi_settings import FastAPIServerSettings


@dataclass(frozen=True)
class StandardSettings(BaseSettings):
    """Standard settings that combines app settings with optional provider configurations.
    
    This class provides a unified interface for configuring Faciliter applications
    with support for LLM, embeddings, cache, tracing, database, and MCP server services. 
    Services are automatically configured based on environment variables or can be 
    explicitly enabled/disabled.
    
    For easy customization, subclass this class and use the extend_from_env() method
    to add your own configuration fields.
    """
    
    # Core app settings (based on AppSettings)
    app_name: str = "faciliter-app"
    version: str = "0.2.8"
    environment: str = "dev"
    log_level: str = "INFO"
    project_root: Optional[Path] = None
    
    # Optional service configurations
    llm: Optional[LLMSettings] = None
    embeddings: Optional[EmbeddingsSettings] = None
    cache: Optional[CacheSettings] = None
    tracing: Optional[TracingSettings] = None
    database: Optional[DatabaseSettings] = None
    mcp_server: Optional[MCPServerSettings] = None
    fastapi_server: Optional[FastAPIServerSettings] = None
    
    # Service enablement flags
    enable_llm: bool = field(default=True)
    enable_embeddings: bool = field(default=False)
    enable_cache: bool = field(default=False)
    enable_tracing: bool = field(default=False)
    enable_database: bool = field(default=False)
    enable_mcp_server: bool = field(default=False)
    enable_fastapi_server: bool = field(default=False)
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "StandardSettings":
        """Create standard settings from environment variables and auto-detect services."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        # Get core app settings from the dedicated module
        app_settings = AppSettings.from_env(load_dotenv=False, **{
            k: v for k, v in overrides.items() 
            if k in ["app_name", "version", "environment", "log_level", "project_root"]
        })
        
        # Auto-detect services from environment
        enable_llm = cls._should_enable_llm(overrides)
        enable_embeddings = cls._should_enable_embeddings(overrides)
        enable_cache = cls._should_enable_cache(overrides)
        enable_tracing = cls._should_enable_tracing(overrides)
        enable_database = cls._should_enable_database(overrides)
        enable_mcp_server = cls._should_enable_mcp_server(overrides)
        enable_fastapi_server = cls._should_enable_fastapi_server(overrides)
        
        # Create service configurations if enabled
        llm_config = None
        if enable_llm:
            try:
                llm_config = LLMSettings.from_env(load_dotenv=False)
            except Exception:
                enable_llm = False
        
        embeddings_config = None
        if enable_embeddings:
            try:
                embeddings_config = EmbeddingsSettings.from_env(load_dotenv=False)
            except Exception:
                enable_embeddings = False
        
        cache_config = None
        if enable_cache:
            try:
                cache_config = CacheSettings.from_env(load_dotenv=False)
            except Exception:
                enable_cache = False
        
        tracing_config = None
        if enable_tracing:
            try:
                tracing_config = TracingSettings.from_env(load_dotenv=False)
            except Exception:
                enable_tracing = False
        
        database_config = None
        if enable_database:
            try:
                database_config = DatabaseSettings.from_env(load_dotenv=False)
            except Exception:
                enable_database = False
        
        mcp_server_config = None
        if enable_mcp_server:
            try:
                mcp_server_config = MCPServerSettings.from_env(load_dotenv=False)
            except Exception:
                enable_mcp_server = False
        
        fastapi_server_config = None
        if enable_fastapi_server:
            try:
                fastapi_server_config = FastAPIServerSettings.from_env(load_dotenv=False)
            except Exception:
                enable_fastapi_server = False
        
        # Build the settings dict
        settings_dict = {
            "app_name": app_settings.app_name,
            "version": app_settings.version,
            "environment": app_settings.environment,
            "log_level": app_settings.log_level,
            "project_root": app_settings.project_root,
            "llm": llm_config,
            "embeddings": embeddings_config,
            "cache": cache_config,
            "tracing": tracing_config,
            "database": database_config,
            "mcp_server": mcp_server_config,
            "fastapi_server": fastapi_server_config,
            "enable_llm": enable_llm,
            "enable_embeddings": enable_embeddings,
            "enable_cache": enable_cache,
            "enable_tracing": enable_tracing,
            "enable_database": enable_database,
            "enable_mcp_server": enable_mcp_server,
            "enable_fastapi_server": enable_fastapi_server,
        }
        
        # Apply overrides
        settings_dict.update(overrides)
        
        return cls(**settings_dict)
    
    @staticmethod
    def _should_enable_llm(overrides: dict) -> bool:
        """Check if LLM should be enabled based on environment variables."""
        if "enable_llm" in overrides:
            return overrides["enable_llm"]
        
        if EnvParser.get_env("ENABLE_LLM", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_LLM", env_type=bool)
        
        # Auto-detect based on API keys
        return (
            EnvParser.get_env("OPENAI_API_KEY") or
            EnvParser.get_env("AZURE_OPENAI_API_KEY") or
            EnvParser.get_env("GEMINI_API_KEY") or
            EnvParser.get_env("GOOGLE_GENAI_API_KEY") or
            EnvParser.get_env("OLLAMA_HOST") or
            EnvParser.get_env("LLM_PROVIDER")
        ) is not None
    
    @staticmethod
    def _should_enable_embeddings(overrides: dict) -> bool:
        """Check if embeddings should be enabled based on environment variables."""
        if "enable_embeddings" in overrides:
            return overrides["enable_embeddings"]
        
        if EnvParser.get_env("ENABLE_EMBEDDINGS", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_EMBEDDINGS", env_type=bool)
        
        # Auto-detect based on provider or model settings
        return (
            EnvParser.get_env("EMBEDDING_PROVIDER") or
            EnvParser.get_env("EMBEDDING_MODEL")
        ) is not None
    
    @staticmethod
    def _should_enable_cache(overrides: dict) -> bool:
        """Check if cache should be enabled based on environment variables."""
        if "enable_cache" in overrides:
            return overrides["enable_cache"]
        
        if EnvParser.get_env("ENABLE_CACHE", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_CACHE", env_type=bool)
        
        # Auto-detect based on Redis/Valkey settings
        return (
            EnvParser.get_env("REDIS_HOST") or
            EnvParser.get_env("VALKEY_HOST") or
            EnvParser.get_env("CACHE_PROVIDER")
        ) is not None
    
    @staticmethod
    def _should_enable_tracing(overrides: dict) -> bool:
        """Check if tracing should be enabled based on environment variables."""
        if "enable_tracing" in overrides:
            return overrides["enable_tracing"]
        
        if EnvParser.get_env("ENABLE_TRACING", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_TRACING", env_type=bool)
        
        # Auto-detect based on Langfuse settings
        return (
            EnvParser.get_env("LANGFUSE_PUBLIC_KEY") and
            EnvParser.get_env("LANGFUSE_SECRET_KEY")
        ) is not None
    
    @staticmethod
    def _should_enable_database(overrides: dict) -> bool:
        """Check if database should be enabled based on environment variables."""
        if "enable_database" in overrides:
            return overrides["enable_database"]
        
        if EnvParser.get_env("ENABLE_DATABASE", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_DATABASE", env_type=bool)
        
        # Auto-detect based on database settings
        return (
            EnvParser.get_env("POSTGRES_HOST") or
            EnvParser.get_env("DATABASE_HOST") or
            EnvParser.get_env("POSTGRES_USER") or
            EnvParser.get_env("DATABASE_USER")
        ) is not None
    
    @staticmethod
    def _should_enable_mcp_server(overrides: dict) -> bool:
        """Check if MCP server should be enabled based on environment variables."""
        if "enable_mcp_server" in overrides:
            return overrides["enable_mcp_server"]
        
        if EnvParser.get_env("ENABLE_MCP_SERVER", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_MCP_SERVER", env_type=bool)
        
        # Auto-detect based on MCP server settings
        return (
            EnvParser.get_env("MCP_SERVER_HOST") or
            EnvParser.get_env("MCP_SERVER_PORT") or
            EnvParser.get_env("MCP_SERVER_NAME") or
            EnvParser.get_env("MCP_TRANSPORT")
        ) is not None

    @staticmethod
    def _should_enable_fastapi_server(overrides: dict) -> bool:
        """Check if FastAPI server should be enabled based on environment variables."""
        if "enable_fastapi_server" in overrides:
            return overrides["enable_fastapi_server"]
        
        if EnvParser.get_env("ENABLE_FASTAPI_SERVER", env_type=bool) is not None:
            return EnvParser.get_env("ENABLE_FASTAPI_SERVER", env_type=bool)
        
        return (
            EnvParser.get_env("FASTAPI_HOST") or
            EnvParser.get_env("FASTAPI_PORT") or
            EnvParser.get_env("FASTAPI_RELOAD") or
            EnvParser.get_env("API_AUTH_ENABLED") or
            EnvParser.get_env("API_KEYS")
        ) is not None
    
    def validate(self) -> None:
        """Validate the complete settings configuration."""
        # Validate individual service configurations
        if self.llm:
            self.llm.validate()
        if self.embeddings:
            self.embeddings.validate()
        if self.cache:
            self.cache.validate()
        if self.tracing:
            self.tracing.validate()
        if self.database:
            self.database.validate()
        if self.mcp_server:
            if not self.mcp_server.is_valid:
                raise SettingsError(f"MCP server configuration invalid: {', '.join(self.mcp_server.validate())}")
        if self.fastapi_server:
            self.fastapi_server.validate()
    
    @classmethod
    def extend_from_env(
        cls, 
        custom_config: Dict[str, Dict[str, Any]],
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **kwargs
    ) -> "StandardSettings":
        """Create a custom settings class that extends StandardSettings.
        
        Args:
            custom_config: Dictionary of custom field configurations
            load_dotenv: Whether to load .env files
            dotenv_paths: Paths to .env files
            **kwargs: Additional overrides
            
        Returns:
            StandardSettings instance with custom fields added as a dict
        """
        # First get standard settings using StandardSettings.from_env (not super())
        standard_settings = StandardSettings.from_env(load_dotenv=load_dotenv, dotenv_paths=dotenv_paths, **{
            k: v for k, v in kwargs.items() 
            if k in cls.__dataclass_fields__
        })
        
        # Parse custom fields from environment
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        custom_fields = {}
        
        for field_name, config in custom_config.items():
            env_vars = config.get("env_vars", [])
            default = config.get("default")
            env_type = config.get("env_type", str)
            required = config.get("required", False)
            
            value = None
            for env_var in env_vars:
                value = EnvParser.get_env(env_var, env_type=env_type)
                if value is not None:
                    break
            
            if value is None:
                if required:
                    raise SettingsError(f"Required custom field '{field_name}' not found in environment variables: {env_vars}")
                value = default
            
            custom_fields[field_name] = value
        
        # Convert standard settings to dict and add custom fields
        # Keep nested settings as objects, not dicts, so properties can be accessed
        settings_dict = {
            "app_name": standard_settings.app_name,
            "version": standard_settings.version,
            "environment": standard_settings.environment,
            "log_level": standard_settings.log_level,
            "project_root": standard_settings.project_root,
            "llm": standard_settings.llm,
            "embeddings": standard_settings.embeddings,
            "cache": standard_settings.cache,
            "tracing": standard_settings.tracing,
            "database": standard_settings.database,
            "mcp_server": standard_settings.mcp_server,
            "fastapi_server": getattr(standard_settings, 'fastapi_server', None),
            "enable_llm": standard_settings.enable_llm,
            "enable_embeddings": standard_settings.enable_embeddings,
            "enable_cache": standard_settings.enable_cache,
            "enable_tracing": standard_settings.enable_tracing,
            "enable_database": standard_settings.enable_database,
            "enable_mcp_server": standard_settings.enable_mcp_server,
            "enable_fastapi_server": getattr(standard_settings, 'enable_fastapi_server', False),
        }
        
        # Add custom fields
        settings_dict.update(custom_fields)
        
        # Override with any additional kwargs
        settings_dict.update({k: v for k, v in kwargs.items() if k not in cls.__dataclass_fields__})
        
        # Create a dynamic class that combines StandardSettings with custom fields
        from types import SimpleNamespace
        extended = SimpleNamespace(**settings_dict)
        
        # Add methods from StandardSettings
        extended.validate = lambda: None  # Simple validation
        extended.is_valid = True
        extended.get_llm_config = lambda: standard_settings.get_llm_config() if standard_settings.llm else None
        extended.get_embeddings_config = lambda: standard_settings.get_embeddings_config() if standard_settings.embeddings else None
        extended.get_redis_config = lambda: standard_settings.get_redis_config() if standard_settings.cache else None
        extended.get_database_config = lambda: standard_settings.get_database_config() if standard_settings.database else None
        extended.get_mcp_server_config = lambda: standard_settings.get_mcp_server_config() if standard_settings.mcp_server else None
        extended.get_fastapi_server_config = lambda: standard_settings.get_fastapi_server_config() if getattr(standard_settings, 'fastapi_server', None) else None
        
        # Create a dict serializer that converts nested objects to dicts
        def _as_dict():
            result = {}
            for key, value in settings_dict.items():
                if hasattr(value, 'as_dict'):
                    result[key] = value.as_dict()
                else:
                    result[key] = value
            result.update(custom_fields)
            return result
        
        extended.as_dict = _as_dict
        
        return extended
    
    def _get_attr(self, obj, attr, default=None):
        """Get attribute from object or dictionary."""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def get_llm_config(self):
        """Get LLM configuration in the format expected by existing LLM clients."""
        if not self.llm:
            raise SettingsError("LLM not configured")
        
        # Import here to avoid circular imports
        provider = self._get_attr(self.llm, "provider", "").lower()
        if provider in ("gemini", "google"):
            from ..llm.providers.google_genai_provider import GeminiConfig
            return GeminiConfig(
                api_key=self._get_attr(self.llm, "google_api_key") or "",
                model=self._get_attr(self.llm, "model"),
                temperature=self._get_attr(self.llm, "temperature"),
                max_tokens=self._get_attr(self.llm, "max_tokens"),
                thinking_enabled=self._get_attr(self.llm, "thinking_enabled"),
            )
        elif provider == "ollama":
            from ..llm.providers.ollama_provider import OllamaConfig
            return OllamaConfig(
                model=self._get_attr(self.llm, "model"),
                temperature=self._get_attr(self.llm, "temperature"),
                max_tokens=self._get_attr(self.llm, "max_tokens"),
                thinking_enabled=self._get_attr(self.llm, "thinking_enabled"),
                host=self._get_attr(self.llm, "ollama_host"),
                timeout=self._get_attr(self.llm, "ollama_timeout"),
            )
        else:  # OpenAI/Azure
            from ..llm.providers.openai_provider import OpenAIConfig
            return OpenAIConfig(
                api_key=self._get_attr(self.llm, "api_key") or "",
                model=self._get_attr(self.llm, "model"),
                temperature=self._get_attr(self.llm, "temperature"),
                max_tokens=self._get_attr(self.llm, "max_tokens"),
                base_url=self._get_attr(self.llm, "base_url"),
                organization=self._get_attr(self.llm, "organization"),
                project=self._get_attr(self.llm, "project"),
                azure_endpoint=self._get_attr(self.llm, "azure_endpoint"),
                azure_api_version=self._get_attr(self.llm, "azure_api_version"),
            )
    
    def get_embeddings_config(self):
        """Get embeddings configuration compatible with existing EmbeddingsConfig."""
        if not self.embeddings:
            raise SettingsError("Embeddings not configured")
        
        from ..embeddings.embeddings_config import EmbeddingsConfig
        return EmbeddingsConfig(
            provider=self._get_attr(self.embeddings, "provider"),
            model=self._get_attr(self.embeddings, "model"),
            embedding_dimension=self._get_attr(self.embeddings, "embedding_dimension"),
            task_type=self._get_attr(self.embeddings, "task_type"),
            title=self._get_attr(self.embeddings, "title"),
            api_key=self._get_attr(self.embeddings, "api_key"),
            base_url=self._get_attr(self.embeddings, "base_url"),
            organization=self._get_attr(self.embeddings, "organization"),
            project=self._get_attr(self.embeddings, "project"),
            google_api_key=self._get_attr(self.embeddings, "google_api_key"),
            huggingface_api_key=self._get_attr(self.embeddings, "huggingface_api_key"),
            ollama_host=self._get_attr(self.embeddings, "ollama_host"),
            ollama_url=self._get_attr(self.embeddings, "ollama_url"),
            ollama_timeout=self._get_attr(self.embeddings, "ollama_timeout"),
            device=self._get_attr(self.embeddings, "device"),
            cache_dir=self._get_attr(self.embeddings, "cache_dir"),
            trust_remote_code=self._get_attr(self.embeddings, "trust_remote_code"),
            use_sentence_transformers=self._get_attr(self.embeddings, "use_sentence_transformers"),
            cache_duration_seconds=self._get_attr(self.embeddings, "cache_duration_seconds"),
        )
    
    def get_redis_config(self):
        """Get Redis configuration compatible with existing RedisConfig."""
        if not self.cache:
            raise SettingsError("Cache not configured")
        
        from ..cache.redis_config import RedisConfig
        return RedisConfig(
            host=self._get_attr(self.cache, "host"),
            port=self._get_attr(self.cache, "port"),
            db=self._get_attr(self.cache, "db"),
            prefix=self._get_attr(self.cache, "prefix"),
            ttl=self._get_attr(self.cache, "ttl"),
            password=self._get_attr(self.cache, "password"),
            time_out=self._get_attr(self.cache, "timeout"),
        )
    
    def get_database_config(self) -> DatabaseSettings:
        """Get database configuration."""
        if not self.database:
            raise SettingsError("Database not configured")
        return self.database
    
    def get_mcp_server_config(self) -> MCPServerSettings:
        """Get MCP server configuration.""" 
        if not self.mcp_server:
            raise SettingsError("MCP server not configured")
        return self.mcp_server

    def get_fastapi_server_config(self) -> FastAPIServerSettings:
        """Get FastAPI server configuration."""
        if not self.fastapi_server:
            raise SettingsError("FastAPI server not configured")
        return self.fastapi_server
    
    def as_app_settings(self) -> AppSettings:
        """Convert to AppSettings for backward compatibility."""
        return AppSettings(
            app_name=self.app_name,
            version=self.version,
            environment=self.environment,
            log_level=self.log_level,
            project_root=self.project_root
        )

    # Null-safe convenience properties for sub-configs
    @property
    def mcp_server_safe(self) -> MCPServerSettings | NullConfig:
        return self.mcp_server if self.mcp_server is not None else NullConfig()

    @property
    def fastapi_server_safe(self) -> FastAPIServerSettings | NullConfig:
        return self.fastapi_server if self.fastapi_server is not None else NullConfig()

    @property
    def llm_safe(self) -> LLMSettings | NullConfig:
        return self.llm if self.llm is not None else NullConfig()

    @property
    def embeddings_safe(self) -> EmbeddingsSettings | NullConfig:
        return self.embeddings if self.embeddings is not None else NullConfig()

    @property
    def cache_safe(self) -> CacheSettings | NullConfig:
        return self.cache if self.cache is not None else NullConfig()

    @property
    def tracing_safe(self) -> TracingSettings | NullConfig:
        return self.tracing if self.tracing is not None else NullConfig()

    @property
    def database_safe(self) -> DatabaseSettings | NullConfig:
        return self.database if self.database is not None else NullConfig()
    
    def as_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "environment": self.environment,
            "log_level": self.log_level,
            "project_root": str(self.project_root) if self.project_root else None,
            "llm": self.llm.as_dict() if self.llm else None,
            "embeddings": self.embeddings.as_dict() if self.embeddings else None,
            "cache": self.cache.as_dict() if self.cache else None,
            "tracing": self.tracing.as_dict() if self.tracing else None,
            "database": self.database.as_dict() if self.database else None,
            "mcp_server": self.mcp_server.as_dict() if self.mcp_server else None,
            "fastapi_server": self.fastapi_server.as_dict() if self.fastapi_server else None,
            "enable_llm": self.enable_llm,
            "enable_embeddings": self.enable_embeddings,
            "enable_cache": self.enable_cache,
            "enable_tracing": self.enable_tracing,
            "enable_database": self.enable_database,
            "enable_mcp_server": self.enable_mcp_server,
            "enable_fastapi_server": self.enable_fastapi_server,
        }