"""Embeddings package public exports."""
from .base import BaseEmbeddingClient, EmbeddingGenerationError
from .ollama import OllamaEmbeddingClient
from .factory import create_embedding_client
from .embeddings_config import EmbeddingsConfig, embeddings_settings

__all__ = [
	"BaseEmbeddingClient",
	"EmbeddingGenerationError",
	"OllamaEmbeddingClient",
	"create_embedding_client",
	"EmbeddingsConfig",
	"embeddings_settings",
]
"""Embeddings package: generic base and provider-specific implementations.

This package provides a stable public API for generating embeddings. It
includes a provider-agnostic `BaseEmbeddingClient` and an `OllamaEmbeddingClient`
implementation. The legacy module `rfp_rag.retrieval.embeddings` re-exports
these classes for backward compatibility.
"""
from .base import BaseEmbeddingClient, EmbeddingGenerationError
from .ollama import OllamaEmbeddingClient
from .factory import create_embedding_client
from .embeddings_config import EmbeddingsConfig, embeddings_settings

__all__ = [
	"BaseEmbeddingClient",
	"EmbeddingGenerationError",
	"OllamaEmbeddingClient",
	"create_embedding_client",
	"EmbeddingsConfig",
	"embeddings_settings",
]
