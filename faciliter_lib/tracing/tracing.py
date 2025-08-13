"""Configure OpenTelemetry and Langfuse for the application.

This module centralizes all tracing concerns so callers don't import or depend
on Langfuse directly. It also exposes small helpers to integrate model
providers (e.g., Google Gemini) with Langfuse's standard provider tracing when
available, while remaining a no-op fallback if the integration isn't present.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langfuse import Langfuse, get_client
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


class TracingProvider(ABC):
    """Abstract base class for tracing providers."""
    
    @abstractmethod
    def add_metadata(self, metadata: Any) -> None:
        """Add metadata to the current trace. Accepts dict or JSON string."""
        pass


class LangfuseTracingProvider(TracingProvider):
    """Langfuse implementation of the tracing provider."""
    
    def __init__(self, langfuse_client: Langfuse):
        self._client = langfuse_client
    
    def add_metadata(self, metadata: Any) -> None:
        """Add metadata to the current trace. Accepts dict or JSON string."""
        from faciliter_lib.mcp_utils import parse_from
        if isinstance(metadata, str):
            metadata = parse_from(metadata)
        self._client.update_current_span(metadata=metadata)


class TracingManager:
    """Manages tracing configuration and provides a unified interface."""
    
    def __init__(self, service_name: Optional[str] = None):
        self.service_name = service_name or os.getenv("APP_NAME", "unknown")
        self.service_version = os.getenv("APP_VERSION", "0.1.0")
        self._provider: Optional[TracingProvider] = None
        self._initialized = False
    
    def setup(self) -> TracingProvider:
        """Setup tracing and return the tracing provider."""
        if self._initialized and self._provider is not None:
            return self._provider
        
        # Check if TracerProvider is already set
        if trace.get_tracer_provider() is not trace.ProxyTracerProvider():
            # Tracing already initialized, just return Langfuse client
            langfuse_client = get_client()
            self._provider = LangfuseTracingProvider(langfuse_client)
            self._initialized = True
            return self._provider
        
        # Configure OpenTelemetry
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "service.version": self.service_version,
            }
        )
        
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # Configure Langfuse
        langfuse_client = Langfuse(
            x_langfuse_sdk_name="Langfuse Python SDK",
            x_langfuse_sdk_version="1.0.0",
            x_langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            username=os.getenv("LANGFUSE_SECRET_KEY"),
            password="",
            base_url=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
        )
        
        self._provider = LangfuseTracingProvider(langfuse_client)
        self._initialized = True
        return self._provider
    
    def get_provider(self) -> Optional[TracingProvider]:
        """Get the current tracing provider."""
        return self._provider
    
    def add_metadata(self, metadata: Any) -> None:
        """Add metadata to the current trace. Accepts dict or JSON string."""
        if self._provider:
            self._provider.add_metadata(metadata)


# ------------------------- Convenience helpers -------------------------
def add_trace_metadata(metadata: Any) -> None:
    """Add metadata to the current trace in a provider-agnostic way.

    Args:
        metadata: Additional info to attach to the active span/trace.
            Can be a dict or a JSON string; implementation will parse strings.
    """
    try:
        manager = TracingManager()
        provider = manager.get_provider() or manager.setup()
        provider.add_metadata(metadata)  # type: ignore[union-attr]
    except Exception:
        # Never fail application flow due to tracing
        pass

def setup_tracing(name: Optional[str] = None) -> TracingProvider:
    """Configure tracing and return the tracing provider.
    
    This function maintains backward compatibility with the original API.
    """
    manager = TracingManager(name)
    return manager.setup()