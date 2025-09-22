"""faciliter-lib: Shared library for MCP agent tools."""

__version__ = "0.2.0"

from .cache import (
    create_cache, 
    set_cache, get_cache, cache_get, cache_set
)
from .mcp_utils import parse_from, get_transport_from_args
from .tracing import setup_tracing, setup_logging, get_logger, get_module_logger

#from .llm import LLMClient, GeminiConfig, OllamaConfig, create_gemini_client, create_ollama_client, create_client_from_env, clean_and_parse_json_response
from .utils.language_utils import LanguageUtils
from .utils.app_settings import AppSettings

# New settings management system
from .config import (
    StandardSettings, BaseSettings, LLMSettings, EmbeddingsSettings,
    CacheSettings, TracingSettings, DatabaseSettings, SettingsManager, settings_manager,
    SettingsError, EnvironmentVariableError
)

# from .config import DOC_CATEGORIES, DOC_CATEGORIES_BY_KEY, DOC_CATEGORY_CHOICES
# from .tools import ExcelManager

__all__ = [
    "create_cache",
    "set_cache", 
    "get_cache", 
    "cache_get",
    "cache_set",
    "parse_from",
    "get_transport_from_args",
    "setup_tracing",
    "setup_logging",
    "get_logger",
    "get_module_logger",
    "clean_and_parse_json_response",
    "LanguageUtils",
    "AppSettings",
    
    # Settings management system
    "StandardSettings",
    "BaseSettings", 
    "LLMSettings",
    "EmbeddingsSettings",
    "CacheSettings",
    "TracingSettings",
    "DatabaseSettings",
    "SettingsManager",
    "settings_manager",
    "SettingsError",
    "EnvironmentVariableError",
    
    "__version__",
]
