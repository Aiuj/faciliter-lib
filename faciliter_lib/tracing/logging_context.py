"""Logging context manager for adding request metadata to log records.

This module provides a context manager and filter mechanism to inject
contextual information (user_id, session_id, company_id, etc.) from the
`from` parameter into all log records within a request scope.

This enables:
- Correlating logs across distributed systems using session_id
- Filtering logs by user, company, or session in observability dashboards
- Reconstructing complete request flows across multiple services
- Debugging user-specific or company-specific issues

Usage:
    ```python
    from faciliter_lib.tracing import LoggingContext
    
    # In a FastAPI endpoint:
    @app.post("/api/endpoint")
    async def endpoint(from_: Optional[str] = Query(None, alias="from")):
        from_dict = parse_from(from_)
        
        with LoggingContext(from_dict):
            logger.info("Processing request")  # Automatically includes context
            # ... rest of endpoint logic
    ```

The context is stored in thread-local storage and automatically added
to all log records emitted within the context block.
"""

import logging
import threading
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Thread-safe context storage using contextvars (works with asyncio)
_logging_context: ContextVar[Dict[str, Any]] = ContextVar('logging_context', default={})


class LoggingContextFilter(logging.Filter):
    """Logging filter that adds contextual metadata to log records.
    
    This filter reads from the current logging context and adds fields
    like user_id, session_id, company_id to the log record's extra_attrs,
    which are then sent to observability systems (OTLP, OVH LDP, etc.).
    
    The filter should be added to the root logger during setup_logging().
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context metadata to the log record.
        
        Args:
            record: The log record to enhance
            
        Returns:
            True (always pass the record through)
        """
        # Get current context
        context = _logging_context.get()
        
        if context:
            # Add context to extra_attrs for OTLP handler
            if not hasattr(record, 'extra_attrs'):
                record.extra_attrs = {}
            
            # Map from_ fields to OpenTelemetry semantic conventions
            # See: https://opentelemetry.io/docs/specs/semconv/
            
            if 'session_id' in context and context['session_id']:
                record.extra_attrs['session.id'] = context['session_id']
            
            if 'user_id' in context and context['user_id']:
                record.extra_attrs['user.id'] = context['user_id']
            
            if 'user_name' in context and context['user_name']:
                record.extra_attrs['user.name'] = context['user_name']
            
            if 'company_id' in context and context['company_id']:
                record.extra_attrs['organization.id'] = context['company_id']
            
            if 'company_name' in context and context['company_name']:
                record.extra_attrs['organization.name'] = context['company_name']
            
            if 'app_name' in context and context['app_name']:
                record.extra_attrs['client.app.name'] = context['app_name']
            
            if 'app_version' in context and context['app_version']:
                record.extra_attrs['client.app.version'] = context['app_version']
            
            if 'model_name' in context and context['model_name']:
                record.extra_attrs['gen_ai.request.model'] = context['model_name']
        
        return True


class LoggingContext:
    """Context manager for setting logging context metadata.
    
    Use this to wrap request handlers and automatically inject
    user_id, session_id, company_id, etc. into all log records.
    
    Example:
        ```python
        from_dict = {"session_id": "123", "user_id": "user-456", "company_id": "comp-789"}
        
        with LoggingContext(from_dict):
            logger.info("Processing request")
            # Log will include session.id=123, user.id=user-456, organization.id=comp-789
        ```
    
    Supports nesting - inner contexts extend outer contexts.
    Thread-safe and async-safe (uses contextvars).
    """
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """Initialize the logging context.
        
        Args:
            context: Dictionary of metadata to add to logs.
                    Typically parsed from the `from` parameter.
                    Common keys: session_id, user_id, company_id, user_name,
                               company_name, app_name, app_version, model_name
        """
        self.context = context or {}
        self.token = None
        self.previous_context = None
    
    def __enter__(self):
        """Enter the context and set logging metadata."""
        # Get current context (may be empty or from outer context)
        self.previous_context = _logging_context.get().copy()
        
        # Merge new context with previous (new context takes precedence)
        merged_context = {**self.previous_context, **self.context}
        
        # Set the new context
        self.token = _logging_context.set(merged_context)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore previous logging metadata."""
        if self.token is not None:
            _logging_context.reset(self.token)
        return False  # Don't suppress exceptions


def get_current_logging_context() -> Dict[str, Any]:
    """Get the current logging context metadata.
    
    Returns:
        Dictionary of current context metadata
    """
    return _logging_context.get().copy()


def set_logging_context(**kwargs):
    """Update the current logging context with additional metadata.
    
    This adds to or updates the current context without replacing it entirely.
    Useful for adding metadata at different points in request processing.
    
    Args:
        **kwargs: Key-value pairs to add to context
        
    Example:
        ```python
        set_logging_context(user_id="user-123", session_id="session-456")
        logger.info("User logged in")  # Includes user.id and session.id
        ```
    """
    current = _logging_context.get().copy()
    current.update(kwargs)
    _logging_context.set(current)


def clear_logging_context():
    """Clear all logging context metadata.
    
    Useful for cleanup or testing.
    """
    _logging_context.set({})


# Convenience function to install the filter
def install_logging_context_filter(logger: Optional[logging.Logger] = None):
    """Install the logging context filter on all handlers.
    
    This is automatically called by setup_logging() if context filtering is enabled.
    
    IMPORTANT: Filters must be added to HANDLERS, not loggers, to ensure they
    are applied to all log records from child loggers. Filters on loggers only
    apply to records from that specific logger, not child loggers.
    
    Args:
        logger: Logger whose handlers will get the filter. If None, uses root logger.
    """
    if logger is None:
        logger = logging.getLogger()
    
    # Add filter to all handlers
    context_filter = LoggingContextFilter()
    
    for handler in logger.handlers:
        # Check if filter already installed on this handler
        if any(isinstance(f, LoggingContextFilter) for f in handler.filters):
            continue  # Already installed on this handler
        
        handler.addFilter(context_filter)


__all__ = [
    'LoggingContext',
    'LoggingContextFilter',
    'get_current_logging_context',
    'set_logging_context',
    'clear_logging_context',
    'install_logging_context_filter',
]
