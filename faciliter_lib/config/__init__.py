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
from .standard_settings import StandardSettings

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
    "StandardSettings",
]
