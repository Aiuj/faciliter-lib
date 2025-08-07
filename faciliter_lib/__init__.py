"""faciliter-lib: Shared library for MCP agent tools."""

__version__ = "0.2.0"

from .cache.cache_manager import RedisCache, set_cache, get_cache, cache_get, cache_set
from .mcp_utils import parse_from, get_transport_from_args
from .tracing import setup_tracing, setup_logging, get_logger, get_module_logger

from .llm import LLMClient, GeminiConfig, OllamaConfig, create_gemini_client, create_ollama_client, create_client_from_env, clean_and_parse_json_response
from .utils.language_utils import LanguageUtils

__all__ = [
    "RedisCache",
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
    "LLMClient",
    "GeminiConfig", 
    "OllamaConfig",
    "create_gemini_client",
    "create_ollama_client",
    "create_client_from_env",
    "clean_and_parse_json_response",
    "LanguageUtils",
    "__version__",
]
