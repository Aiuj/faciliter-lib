"""
standard_settings.py

Standard settings implementation that combines core application settings
with provider-specific configurations for LLM, embeddings, cache, tracing, and database.

This module provides a unified settings interface that can be easily configured
for any Faciliter application, with automatic detection and configuration of
the services needed by the application. It also provides an easy extension
mechanism for adding custom settings.

Features:
- Inherits from AppSettings for core app configuration
- Optional LLM, embeddings, cache, tracing, and database configuration
- Auto-detection of required services
- Easy extension for custom settings via extend_from_env
- Comprehensive validation
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..config.base_settings import BaseSettings, SettingsError, EnvParser
from ..utils.app_settings import AppSettings


@dataclass(frozen=True)
class LLMSettings(BaseSettings):
    """LLM provider configuration settings."""
    
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    thinking_enabled: bool = False
    
    # OpenAI/Azure specific
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = "2024-08-01-preview"
    
    # Ollama specific
    ollama_host: Optional[str] = None
    ollama_timeout: Optional[int] = None
    
    # Gemini specific
    google_api_key: Optional[str] = None
    safety_settings: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_env(
        cls, 
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "LLMSettings":
        """Create LLM settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        # Auto-detect provider if not specified
        provider = overrides.get("provider") or cls._detect_provider()
        
        # Parse common settings
        model = EnvParser.get_env(
            "LLM_MODEL", f"{provider.upper()}_MODEL", 
            default="gpt-4o-mini"
        )
        temperature = EnvParser.get_env(
            "LLM_TEMPERATURE", f"{provider.upper()}_TEMPERATURE",
            default=0.7, env_type=float
        )
        max_tokens = EnvParser.get_env(
            "LLM_MAX_TOKENS", f"{provider.upper()}_MAX_TOKENS",
            env_type=int
        )
        thinking_enabled = EnvParser.get_env(
            "LLM_THINKING_ENABLED", f"{provider.upper()}_THINKING_ENABLED",
            default=False, env_type=bool
        )
        
        # Provider-specific settings
        settings_dict = {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking_enabled": thinking_enabled,
        }
        
        if provider.lower() in ("openai", "azure"):
            settings_dict.update({
                "api_key": EnvParser.get_env("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY"),
                "base_url": EnvParser.get_env("OPENAI_BASE_URL"),
                "organization": EnvParser.get_env("OPENAI_ORG", "OPENAI_ORGANIZATION"),
                "project": EnvParser.get_env("OPENAI_PROJECT"),
                "azure_endpoint": EnvParser.get_env("AZURE_OPENAI_ENDPOINT"),
                "azure_api_version": EnvParser.get_env("AZURE_OPENAI_API_VERSION", default="2024-08-01-preview"),
            })
        elif provider.lower() == "ollama":
            settings_dict.update({
                "ollama_host": EnvParser.get_env("OLLAMA_HOST", "OLLAMA_BASE_URL"),
                "ollama_timeout": EnvParser.get_env("OLLAMA_TIMEOUT", env_type=int),
            })
        elif provider.lower() in ("gemini", "google"):
            settings_dict.update({
                "google_api_key": EnvParser.get_env("GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY"),
            })
        
        # Apply overrides
        settings_dict.update(overrides)
        
        return cls(**settings_dict)
    
    @staticmethod
    def _detect_provider() -> str:
        """Auto-detect LLM provider from environment variables."""
        if EnvParser.get_env("LLM_PROVIDER"):
            return EnvParser.get_env("LLM_PROVIDER")
        
        # Check for provider-specific API keys in order of preference
        # Azure first since it's more specific than generic OpenAI
        if EnvParser.get_env("AZURE_OPENAI_API_KEY") or EnvParser.get_env("AZURE_OPENAI_ENDPOINT"):
            return "azure"
        elif EnvParser.get_env("GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY"):
            return "gemini"
        elif EnvParser.get_env("OLLAMA_HOST", "OLLAMA_BASE_URL"):
            return "ollama"
        elif EnvParser.get_env("OPENAI_API_KEY"):
            return "openai"
        
        return "openai"  # Default
    
    def validate(self) -> None:
        """Validate LLM configuration."""
        if self.provider.lower() in ("openai", "azure") and not self.api_key:
            raise SettingsError("OpenAI/Azure provider requires api_key")
        elif self.provider.lower() in ("gemini", "google") and not self.google_api_key:
            raise SettingsError("Gemini provider requires google_api_key")
        
        if self.temperature < 0 or self.temperature > 2:
            raise SettingsError("Temperature must be between 0 and 2")
        
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise SettingsError("max_tokens must be positive")


@dataclass(frozen=True) 
class EmbeddingsSettings(BaseSettings):
    """Embeddings provider configuration settings."""
    
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    embedding_dimension: Optional[int] = None
    task_type: Optional[str] = None
    title: Optional[str] = None
    
    # Provider-specific settings
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None
    google_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    
    # Ollama settings
    ollama_host: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_timeout: Optional[int] = None
    
    # Local model settings
    device: str = "auto"
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False
    use_sentence_transformers: bool = True
    
    # Cache settings
    cache_duration_seconds: int = 7200
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "EmbeddingsSettings":
        """Create embeddings settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        provider = EnvParser.get_env("EMBEDDING_PROVIDER", default="openai")
        model = EnvParser.get_env("EMBEDDING_MODEL", default="text-embedding-3-small")
        
        settings_dict = {
            "provider": provider,
            "model": model,
            "embedding_dimension": EnvParser.get_env("EMBEDDING_DIMENSION", env_type=int),
            "task_type": EnvParser.get_env("EMBEDDING_TASK_TYPE"),
            "title": EnvParser.get_env("EMBEDDING_TITLE"),
            "api_key": EnvParser.get_env("OPENAI_API_KEY", "API_KEY"),
            "base_url": EnvParser.get_env("OPENAI_BASE_URL", "BASE_URL"),
            "organization": EnvParser.get_env("OPENAI_ORGANIZATION"),
            "project": EnvParser.get_env("OPENAI_PROJECT"),
            "google_api_key": EnvParser.get_env("GOOGLE_GENAI_API_KEY", "GEMINI_API_KEY"),
            "huggingface_api_key": EnvParser.get_env("HUGGINGFACE_API_KEY"),
            "ollama_host": EnvParser.get_env("OLLAMA_HOST"),
            "ollama_url": EnvParser.get_env("OLLAMA_URL"),
            "ollama_timeout": EnvParser.get_env("OLLAMA_TIMEOUT", env_type=int),
            "device": EnvParser.get_env("EMBEDDING_DEVICE", default="auto"),
            "cache_dir": EnvParser.get_env("EMBEDDING_CACHE_DIR"),
            "trust_remote_code": EnvParser.get_env("EMBEDDING_TRUST_REMOTE_CODE", default=False, env_type=bool),
            "use_sentence_transformers": EnvParser.get_env("EMBEDDING_USE_SENTENCE_TRANSFORMERS", default=True, env_type=bool),
            "cache_duration_seconds": EnvParser.get_env("EMBEDDING_CACHE_DURATION_SECONDS", default=7200, env_type=int),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)


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


@dataclass(frozen=True)
class TracingSettings(BaseSettings):
    """Tracing configuration settings."""
    
    enabled: bool = True
    service_name: Optional[str] = None
    service_version: str = "0.1.0"
    
    # Langfuse settings
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3000"
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "TracingSettings":
        """Create tracing settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        settings_dict = {
            "enabled": EnvParser.get_env("TRACING_ENABLED", default=True, env_type=bool),
            "service_name": EnvParser.get_env("APP_NAME", "SERVICE_NAME"),
            "service_version": EnvParser.get_env("APP_VERSION", "SERVICE_VERSION", default="0.1.0"),
            "langfuse_public_key": EnvParser.get_env("LANGFUSE_PUBLIC_KEY"),
            "langfuse_secret_key": EnvParser.get_env("LANGFUSE_SECRET_KEY"),
            "langfuse_host": EnvParser.get_env("LANGFUSE_HOST", default="http://localhost:3000"),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate tracing configuration."""
        if self.enabled and not self.langfuse_public_key:
            raise SettingsError("Tracing enabled but langfuse_public_key not provided")
        if self.enabled and not self.langfuse_secret_key:
            raise SettingsError("Tracing enabled but langfuse_secret_key not provided")


@dataclass(frozen=True)
class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration settings."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "faciliter-qa-rag"
    username: str = "rfp_user"
    password: str = "rfp_password"
    sslmode: str = "disable"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "DatabaseSettings":
        """Create database settings from environment variables."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        settings_dict = {
            "host": EnvParser.get_env("POSTGRES_HOST", "DATABASE_HOST", default="localhost"),
            "port": EnvParser.get_env("POSTGRES_PORT", "DATABASE_PORT", default=5432, env_type=int),
            "database": EnvParser.get_env("POSTGRES_DB", "DATABASE_NAME", default="faciliter-qa-rag"),
            "username": EnvParser.get_env("POSTGRES_USER", "DATABASE_USER", default="rfp_user"),
            "password": EnvParser.get_env("POSTGRES_PASSWORD", "DATABASE_PASSWORD", default="rfp_password"),
            "sslmode": EnvParser.get_env("POSTGRES_SSLMODE", "DATABASE_SSLMODE", default="disable"),
            "pool_size": EnvParser.get_env("POSTGRES_POOL_SIZE", "DATABASE_POOL_SIZE", default=10, env_type=int),
            "max_overflow": EnvParser.get_env("POSTGRES_MAX_OVERFLOW", "DATABASE_MAX_OVERFLOW", default=20, env_type=int),
            "pool_timeout": EnvParser.get_env("POSTGRES_POOL_TIMEOUT", "DATABASE_POOL_TIMEOUT", default=30, env_type=int),
        }
        
        settings_dict.update(overrides)
        return cls(**settings_dict)
    
    def validate(self) -> None:
        """Validate database configuration."""
        if self.port <= 0 or self.port > 65535:
            raise SettingsError("Database port must be between 1 and 65535")
        if not self.database:
            raise SettingsError("Database name is required")
        if not self.username:
            raise SettingsError("Database username is required")
        if self.pool_size <= 0:
            raise SettingsError("Pool size must be positive")
        if self.max_overflow < 0:
            raise SettingsError("Max overflow must be non-negative")
        if self.pool_timeout <= 0:
            raise SettingsError("Pool timeout must be positive")
        if self.sslmode not in ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]:
            raise SettingsError("Invalid SSL mode. Must be one of: disable, allow, prefer, require, verify-ca, verify-full")
    
    def get_connection_string(self, driver: str = "postgresql") -> str:
        """Generate database connection string.
        
        Args:
            driver: Database driver (postgresql, postgresql+psycopg2, postgresql+asyncpg, etc.)
            
        Returns:
            Database connection string
        """
        return f"{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.sslmode}"
    
    def get_async_connection_string(self) -> str:
        """Generate async database connection string for asyncpg."""
        return self.get_connection_string("postgresql+asyncpg")
    
    def get_sync_connection_string(self) -> str:
        """Generate sync database connection string for psycopg2."""
        return self.get_connection_string("postgresql+psycopg2")


@dataclass(frozen=True)
class StandardSettings(BaseSettings):
    """Standard settings that combines app settings with optional provider configurations.
    
    This class provides a unified interface for configuring Faciliter applications
    with support for LLM, embeddings, cache, tracing, and database services. Services are
    automatically configured based on environment variables or can be explicitly
    enabled/disabled.
    
    For easy customization, subclass this class and use the extend_from_env() method
    to add your own configuration fields.
    """
    
    # Core app settings (based on AppSettings)
    app_name: str = "faciliter-app"
    version: str = "0.1.0"
    environment: str = "dev"
    log_level: str = "INFO"
    project_root: Optional[Path] = None
    
    # Optional service configurations
    llm: Optional[LLMSettings] = None
    embeddings: Optional[EmbeddingsSettings] = None
    cache: Optional[CacheSettings] = None
    tracing: Optional[TracingSettings] = None
    database: Optional[DatabaseSettings] = None
    
    # Service enablement flags
    enable_llm: bool = field(default=True)
    enable_embeddings: bool = field(default=False)
    enable_cache: bool = field(default=False)
    enable_tracing: bool = field(default=False)
    enable_database: bool = field(default=False)
    
    @classmethod
    def from_env(
        cls,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "StandardSettings":
        """Create standard settings from environment variables and auto-detect services."""
        cls._load_dotenv_if_requested(load_dotenv, dotenv_paths)
        
        # Get core app settings
        app_name = EnvParser.get_env("APP_NAME", default="faciliter-app")
        environment = EnvParser.get_env("ENVIRONMENT", default="dev")
        log_level = EnvParser.get_env("LOG_LEVEL", default="DEBUG" if environment == "dev" else "INFO")
        
        # Determine project root
        project_root = cls._resolve_project_root(overrides.get("project_root"))
        
        # Get version from pyproject.toml or env
        version = cls._resolve_version(project_root)
        
        # Auto-detect service enablement
        enable_llm = overrides.get("enable_llm", cls._should_enable_llm())
        enable_embeddings = overrides.get("enable_embeddings", cls._should_enable_embeddings())
        enable_cache = overrides.get("enable_cache", cls._should_enable_cache())
        enable_tracing = overrides.get("enable_tracing", cls._should_enable_tracing())
        enable_database = overrides.get("enable_database", cls._should_enable_database())
        
        # Create service configurations if enabled
        llm_settings = None
        if enable_llm:
            try:
                llm_settings = LLMSettings.from_env(load_dotenv=False)  # Already loaded
            except Exception:
                llm_settings = None
                enable_llm = False
        
        embeddings_settings = None
        if enable_embeddings:
            try:
                embeddings_settings = EmbeddingsSettings.from_env(load_dotenv=False)
            except Exception:
                embeddings_settings = None
                enable_embeddings = False
        
        cache_settings = None
        if enable_cache:
            try:
                cache_settings = CacheSettings.from_env(load_dotenv=False)
            except Exception:
                cache_settings = None
                enable_cache = False
        
        tracing_settings = None
        if enable_tracing:
            try:
                tracing_settings = TracingSettings.from_env(load_dotenv=False)
            except Exception:
                tracing_settings = None
                enable_tracing = False
        
        database_settings = None
        if enable_database:
            try:
                database_settings = DatabaseSettings.from_env(load_dotenv=False)
            except Exception:
                database_settings = None
                enable_database = False
        
        # Build final settings
        settings_dict = {
            "app_name": app_name,
            "version": version,
            "environment": environment,
            "log_level": log_level,
            "project_root": project_root,
            "llm": llm_settings,
            "embeddings": embeddings_settings,
            "cache": cache_settings,
            "tracing": tracing_settings,
            "database": database_settings,
            "enable_llm": enable_llm,
            "enable_embeddings": enable_embeddings,
            "enable_cache": enable_cache,
            "enable_tracing": enable_tracing,
            "enable_database": enable_database,
        }
        
        # Apply overrides (except for service objects)
        for key, value in overrides.items():
            if key not in ("llm", "embeddings", "cache", "tracing", "database"):
                settings_dict[key] = value
        
        return cls(**settings_dict)
    
    @classmethod
    def extend_from_env(
        cls,
        custom_env_mappings: Optional[Dict[str, Dict[str, Any]]] = None,
        load_dotenv: bool = True,
        dotenv_paths: Optional[List[Union[str, Path]]] = None,
        **overrides
    ) -> "StandardSettings":
        """Extended factory method for subclasses to add custom settings easily.
        
        This method allows subclasses to define custom environment variable mappings
        without having to reimplement the entire from_env logic.
        
        Args:
            custom_env_mappings: Dict mapping field names to environment variable parsing config.
                Format: {"field_name": {"env_vars": ["VAR1", "VAR2"], "default": value, "env_type": type}}
            load_dotenv: Whether to load .env files
            dotenv_paths: Custom paths for .env files
            **overrides: Direct field overrides
            
        Returns:
            Configured settings instance
            
        Example:
            ```python
            @dataclass(frozen=True)
            class MyAppSettings(StandardSettings):
                api_timeout: int = 30
                debug_mode: bool = False
                api_key: Optional[str] = None
                
                @classmethod
                def from_env(cls, **kwargs):
                    return cls.extend_from_env(
                        custom_env_mappings={
                            "api_timeout": {"env_vars": ["API_TIMEOUT"], "default": 30, "env_type": int},
                            "debug_mode": {"env_vars": ["DEBUG_MODE", "DEBUG"], "default": False, "env_type": bool},
                            "api_key": {"env_vars": ["API_KEY", "MY_API_KEY"], "required": True},
                        },
                        **kwargs
                    )
            ```
        """
        # First get standard settings using StandardSettings.from_env (not super())
        standard_settings = StandardSettings.from_env(load_dotenv=load_dotenv, dotenv_paths=dotenv_paths, **overrides)
        
        # Parse custom environment variables if provided
        custom_fields = {}
        if custom_env_mappings:
            for field_name, config in custom_env_mappings.items():
                env_vars = config.get("env_vars", [])
                default = config.get("default")
                env_type = config.get("env_type", str)
                required = config.get("required", False)
                
                # Parse the environment variable
                value = EnvParser.get_env(
                    *env_vars,
                    default=default,
                    required=required,
                    env_type=env_type
                )
                custom_fields[field_name] = value
        
        # Apply any direct overrides for custom fields
        for key, value in overrides.items():
            if key not in standard_settings.as_dict():
                custom_fields[key] = value
        
        # Create the new instance with both standard and custom fields
        all_fields = {**standard_settings.as_dict(), **custom_fields}
        return cls(**all_fields)
    
    @staticmethod
    def _should_enable_llm() -> bool:
        """Check if LLM should be enabled based on environment."""
        return bool(EnvParser.get_env(
            "ENABLE_LLM", "LLM_PROVIDER", "OPENAI_API_KEY", "GEMINI_API_KEY", 
            "GOOGLE_GENAI_API_KEY", "OLLAMA_HOST", "AZURE_OPENAI_API_KEY"
        ))
    
    @staticmethod 
    def _should_enable_embeddings() -> bool:
        """Check if embeddings should be enabled based on environment."""
        return bool(EnvParser.get_env(
            "ENABLE_EMBEDDINGS", "EMBEDDING_PROVIDER", "EMBEDDING_MODEL"
        ))
    
    @staticmethod
    def _should_enable_cache() -> bool:
        """Check if cache should be enabled based on environment."""
        return bool(EnvParser.get_env(
            "ENABLE_CACHE", "REDIS_HOST", "VALKEY_HOST", "CACHE_PROVIDER"
        ))
    
    @staticmethod
    def _should_enable_tracing() -> bool:
        """Check if tracing should be enabled based on environment."""
        return bool(EnvParser.get_env(
            "ENABLE_TRACING", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"
        ))
    
    @staticmethod
    def _should_enable_database() -> bool:
        """Check if database should be enabled based on environment."""
        return bool(EnvParser.get_env(
            "ENABLE_DATABASE", "POSTGRES_HOST", "POSTGRES_DB", "DATABASE_HOST", "DATABASE_NAME"
        ))
    
    @staticmethod
    def _resolve_project_root(project_root: Optional[Union[str, Path]]) -> Optional[Path]:
        """Resolve project root path."""
        if project_root is not None:
            root = Path(project_root).resolve()
            return root if root.exists() else None

        # Walk upwards from CWD looking for pyproject.toml
        cwd = Path(os.getcwd()).resolve()
        for parent in [cwd, *cwd.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        return None
    
    @staticmethod
    def _resolve_version(project_root: Optional[Path]) -> str:
        """Resolve application version from pyproject.toml or environment."""
        if project_root is not None:
            pyproject = project_root / "pyproject.toml"
            if pyproject.exists():
                version = StandardSettings._read_pyproject_version(pyproject)
                if version:
                    return version
        
        return EnvParser.get_env("APP_VERSION", default="0.1.0")
    
    @staticmethod
    def _read_pyproject_version(pyproject_path: Path) -> Optional[str]:
        """Read version from pyproject.toml file."""
        try:
            import tomllib
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            project = data.get("project", {})
            version = project.get("version")
            if isinstance(version, str) and version.strip():
                return version.strip()
        except Exception:
            pass
        return None
    
    def validate(self) -> None:
        """Validate all settings."""
        # Validate service configurations
        if self.llm and not self.llm.is_valid:
            raise SettingsError(f"LLM settings invalid: {self.llm.validation_errors}")
        if self.embeddings and not self.embeddings.is_valid:
            raise SettingsError(f"Embeddings settings invalid: {self.embeddings.validation_errors}")
        if self.cache and not self.cache.is_valid:
            raise SettingsError(f"Cache settings invalid: {self.cache.validation_errors}")
        if self.tracing and not self.tracing.is_valid:
            raise SettingsError(f"Tracing settings invalid: {self.tracing.validation_errors}")
        if self.database and not self.database.is_valid:
            raise SettingsError(f"Database settings invalid: {self.database.validation_errors}")
    
    def as_app_settings(self) -> AppSettings:
        """Convert to AppSettings instance for backward compatibility."""
        return AppSettings(
            app_name=self.app_name,
            project_root=self.project_root
        )
    
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