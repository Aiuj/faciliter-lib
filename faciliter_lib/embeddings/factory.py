"""Factory helpers to create singleton embedding client instances based on configuration."""
import logging
from typing import Optional
from threading import Lock

from .embeddings_config import embeddings_settings
from .base import BaseEmbeddingClient
from .ollama import OllamaEmbeddingClient

logger = logging.getLogger(__name__)

# Module-level cache for singleton instance and a lock for thread-safety
_singleton_lock = Lock()
_singleton_client: Optional[BaseEmbeddingClient] = None


def create_embedding_client(preferred: Optional[str] = None, force_recreate: bool = False,
                            model: Optional[str] = None, embedding_dim: Optional[int] = None, use_l2_norm: bool = True) -> BaseEmbeddingClient:
    """Return a singleton embedding client instance.

    Args:
        preferred: optional provider name (e.g., "ollama")
        force_recreate: if True, re-create the client even if one exists

    Returns:
        A single shared instance of `BaseEmbeddingClient`.
    """
    global _singleton_client

    with _singleton_lock:
        if _singleton_client is not None and not force_recreate:
            if model is not None or embedding_dim is not None:
                logger.debug("create_embedding_client called with model/embedding_dim but returning existing singleton (ignoring new params)")
            return _singleton_client

        # Normalize preferred provider name
        if preferred:
            preferred = preferred.strip().lower()

        # Preferred explicit selection
        if preferred == "ollama":
            logger.debug("Creating OllamaEmbeddingClient (preferred)")
            _singleton_client = OllamaEmbeddingClient(model=model, embedding_dim=embedding_dim, use_l2_norm=use_l2_norm)
            return _singleton_client

        # Auto-detect based on settings
        try:
            ollama_host = getattr(embeddings_settings, "ollama_host", None)
        except Exception:
            ollama_host = None

        if ollama_host:
            logger.debug("Creating OllamaEmbeddingClient (detected via settings.ollama_host)")
            _singleton_client = OllamaEmbeddingClient(model=model, embedding_dim=embedding_dim, use_l2_norm=use_l2_norm)
            return _singleton_client

        raise RuntimeError("No embedding provider is configured. Set OLLAMA_HOST or provide a preferred provider.")


def get_embedding_client() -> BaseEmbeddingClient:
    """Convenience wrapper to get the singleton client (create if absent).

    This will attempt to create a client automatically based on configuration.
    """
    return create_embedding_client()
