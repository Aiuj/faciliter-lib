"""Tracing module for OpenTelemetry and Langfuse configuration."""

from .tracing import TracingManager, TracingProvider, setup_tracing
from .logger import setup_logging, get_logger, get_module_logger, get_last_logging_config
from .logging_context import (
    LoggingContext,
    LoggingContextFilter,
    get_current_logging_context,
    set_logging_context,
    clear_logging_context,
    install_logging_context_filter,
)
from .observability_models import FromMetadata, FromMetadataSchema, FROM_FIELD_DESCRIPTION, INTELLIGENCE_LEVEL_DESCRIPTION
from .service_usage import (
    ServiceType,
    log_llm_usage,
    log_embedding_usage,
    log_ocr_usage,
    calculate_llm_cost,
    calculate_embedding_cost,
)
from .service_pricing import (
    LLM_PRICING,
    EMBEDDING_PRICING,
    OCR_PRICING,
    get_llm_pricing,
    get_embedding_pricing,
    get_ocr_pricing,
)

__all__ = [
    "TracingManager",
    "TracingProvider",
    "setup_tracing",
    "setup_logging",
    "get_logger",
    "get_module_logger",
    "get_last_logging_config",
    "LoggingContext",
    "LoggingContextFilter",
    "get_current_logging_context",
    "set_logging_context",
    "clear_logging_context",
    "install_logging_context_filter",
    "FROM_FIELD_DESCRIPTION",
    "INTELLIGENCE_LEVEL_DESCRIPTION",
    "FromMetadata",
    "FromMetadataSchema",
    "ServiceType",
    "log_llm_usage",
    "log_embedding_usage",
    "log_ocr_usage",
    "calculate_llm_cost",
    "calculate_embedding_cost",
    "LLM_PRICING",
    "EMBEDDING_PRICING",
    "OCR_PRICING",
    "get_llm_pricing",
    "get_embedding_pricing",
    "get_ocr_pricing",
]
