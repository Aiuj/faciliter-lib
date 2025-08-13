"""Configure OpenTelemetry and Langfuse for the application.

Defaults to a no-op provider unless explicitly enabled via environment
variables. This avoids any external service dependency during tests.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

try:  # Optional dependency
    from langfuse import Langfuse, get_client  # type: ignore
except Exception:  # pragma: no cover - not installed in minimal/test envs
    Langfuse = None  # type: ignore
    def get_client():  # type: ignore
        raise RuntimeError("Langfuse not available")


class TracingProvider(ABC):
    """Abstract base class for tracing providers."""
    
    @abstractmethod
    def add_metadata(self, metadata: Any) -> None:
        """Add metadata to the current trace. Accepts dict or JSON string."""
        pass


class LangfuseTracingProvider(TracingProvider):
    """Langfuse implementation of the tracing provider."""
    
    def __init__(self, langfuse_client: Any):
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
            # Tracing already initialized, wrap existing Langfuse client if available
            if Langfuse is not None:
                try:
                    langfuse_client = get_client()  # may raise if not configured
                    self._provider = LangfuseTracingProvider(langfuse_client)
                except Exception:
                    self._provider = _NoopTracingProvider()
            else:
                self._provider = _NoopTracingProvider()
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

        # Configure provider: use Langfuse if available, otherwise no-op
        if Langfuse is not None:
            try:
                langfuse_client = Langfuse(
                    x_langfuse_sdk_name="Langfuse Python SDK",
                    x_langfuse_sdk_version="1.0.0",
                    x_langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    username=os.getenv("LANGFUSE_SECRET_KEY"),
                    password="",
                    base_url=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
                )
                self._provider = LangfuseTracingProvider(langfuse_client)
            except Exception:
                self._provider = _NoopTracingProvider()
        else:
            self._provider = _NoopTracingProvider()
        self._initialized = True
        return self._provider
    
    def get_provider(self) -> Optional[TracingProvider]:
        """Get the current tracing provider."""
        return self._provider
    
    def add_metadata(self, metadata: Any) -> None:
        """Add metadata to the current trace. Accepts dict or JSON string."""
        if self._provider:
            self._provider.add_metadata(metadata)


def setup_tracing(name: Optional[str] = None) -> TracingProvider:
    """Configure tracing and return the tracing provider.

    If `name` is not provided, the service name will be taken from the APP_NAME
    environment variable (or 'unknown' if not set).
    """
    manager = TracingManager(name)
    return manager.setup()


class _NoopTracingProvider(TracingProvider):
    def add_metadata(self, metadata: Any) -> None:  # pragma: no cover - trivial
        return