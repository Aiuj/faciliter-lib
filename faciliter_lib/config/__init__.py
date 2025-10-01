"""Configuration helpers for faciliter_lib.

Expose configuration classes and category constants for easy import.
"""
from .doc_categories import DOC_CATEGORIES, DOC_CATEGORIES_BY_KEY, DOC_CATEGORY_CHOICES
from .base_settings import (
    BaseSettings, 
    SettingsError, 
    EnvironmentVariableError, 
    SettingsManager, 
    settings_manager,
    EnvParser,
    DotEnvLoader
)
from .app_settings import AppSettings
from .llm_settings import LLMSettings
from .embeddings_settings import EmbeddingsSettings
from .cache_settings import CacheSettings
from .tracing_settings import TracingSettings
from .database_settings import DatabaseSettings
from .mcp_settings import MCPServerSettings
from .fastapi_settings import FastAPIServerSettings
from .standard_settings import StandardSettings
from .settings_singleton import (
    SettingsSingletonManager,
    initialize_settings,
    get_settings,
    set_settings,
    reset_settings,
    has_settings,
    get_settings_safe,
)

__all__ = [
    # Legacy doc categories
    "DOC_CATEGORIES", 
    "DOC_CATEGORIES_BY_KEY", 
    "DOC_CATEGORY_CHOICES",
    
    # New settings system
    "BaseSettings",
    "SettingsError",
    "EnvironmentVariableError", 
    "SettingsManager",
    "settings_manager",
    "EnvParser",
    "DotEnvLoader",
    "AppSettings",
    "LLMSettings",
    "EmbeddingsSettings", 
    "CacheSettings",
    "TracingSettings",
    "DatabaseSettings",
    "MCPServerSettings",
    "FastAPIServerSettings",
    "StandardSettings",
    
    # Settings singleton
    "SettingsSingletonManager",
    "initialize_settings",
    "get_settings",
    "set_settings",
    "reset_settings",
    "has_settings",
    "get_settings_safe",
]
