"""faciliter-lib: Shared library for MCP agent tools."""

__version__ = "0.2.9"

from .cache import (
    create_cache, 
    set_cache, get_cache, cache_get, cache_set
)
from .jobs import (
    create_job_queue, set_job_queue, get_job_queue,
    submit_job, get_job_status, get_job_result,
    update_job_status, update_job_progress,
    complete_job, fail_job, cancel_job,
    list_jobs, cleanup_old_jobs,
    BaseJobQueue, JobConfig, JobStatus, Job,
    JobWorker, JobHandler
)
from .mcp_utils import parse_from, get_transport_from_args
from .tracing import setup_tracing, setup_logging, get_logger, get_module_logger, get_last_logging_config
from .llm import (
    LLMClient, LLMConfig, GeminiConfig, OllamaConfig, OpenAIConfig,
    create_llm_client, create_gemini_client, create_ollama_client, 
    create_openai_client, create_client_from_env, clean_and_parse_json_response
)
from .utils import LanguageUtils, AppSettings
from .tools import ExcelManager

# New settings management system
from .config import (
    StandardSettings, BaseSettings, LLMSettings, EmbeddingsSettings,
    CacheSettings, TracingSettings, DatabaseSettings, SettingsManager, settings_manager,
    SettingsError, EnvironmentVariableError,
    DOC_CATEGORIES, DOC_CATEGORIES_BY_KEY, DOC_CATEGORY_CHOICES
)

__all__ = [
    # Cache
    "create_cache",
    "set_cache", 
    "get_cache", 
    "cache_get",
    "cache_set",
    
    # Jobs
    "create_job_queue",
    "set_job_queue",
    "get_job_queue",
    "submit_job",
    "get_job_status",
    "get_job_result",
    "update_job_status",
    "update_job_progress",
    "complete_job",
    "fail_job",
    "cancel_job",
    "list_jobs",
    "cleanup_old_jobs",
    "BaseJobQueue",
    "JobConfig",
    "JobStatus",
    "Job",
    "JobWorker",
    "JobHandler",
    
    # MCP Utils
    "parse_from",
    "get_transport_from_args",
    
    # Tracing & Logging
    "setup_tracing",
    "setup_logging",
    "get_logger",
    "get_module_logger",
    "get_last_logging_config",
    
    # LLM
    "LLMClient",
    "LLMConfig",
    "GeminiConfig",
    "OllamaConfig",
    "OpenAIConfig",
    "create_llm_client",
    "create_gemini_client",
    "create_ollama_client",
    "create_openai_client",
    "create_client_from_env",
    "clean_and_parse_json_response",
    
    # Utils
    "LanguageUtils",
    "AppSettings",
    
    # Tools
    "ExcelManager",
    
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
    "DOC_CATEGORIES",
    "DOC_CATEGORIES_BY_KEY",
    "DOC_CATEGORY_CHOICES",
    
    "__version__",
]
