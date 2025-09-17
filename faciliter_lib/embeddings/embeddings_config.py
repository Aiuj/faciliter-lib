"""
Embeddings configuration module.

Modeled after the project's LLM config style. Provides a Pydantic-based
`EmbeddingsConfig` and a singleton `embeddings_settings` loaded from
environment variables.
"""

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel


class EmbeddingsConfig(BaseModel):
    """Configuration for embeddings providers.

    Fields are intentionally permissive to support OpenAI, Ollama, HuggingFace,
    and other embedding providers. Use `from_env()` to populate from
    environment variables.
    """

    provider: str = "openai"
    model: str = "text-embedding-3-small"
    embedding_dimension: Optional[int] = None

    # Ollama-specific
    ollama_host: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_timeout: Optional[int] = None

    # OpenAI / compatible
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    # HuggingFace or other providers
    huggingface_api_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "EmbeddingsConfig":
        def getenv(name: str, default: Optional[str] = None) -> Optional[str]:
            v = os.getenv(name)
            return v if v is not None else default

        provider = (getenv("EMBEDDING_PROVIDER", "openai") or "openai").lower()
        model = getenv("EMBEDDING_MODEL", "text-embedding-3-small") or "text-embedding-3-small"

        emb_dim = getenv("EMBEDDING_DIMENSION")
        embedding_dimension = int(emb_dim) if emb_dim and emb_dim.isdigit() else None

        ollama_timeout = None
        ot = getenv("OLLAMA_TIMEOUT")
        if ot and ot.isdigit():
            ollama_timeout = int(ot)

        return cls(
            provider=provider,
            model=model,
            embedding_dimension=embedding_dimension,
            ollama_host=getenv("OLLAMA_HOST"),
            ollama_url=getenv("OLLAMA_URL"),
            ollama_timeout=ollama_timeout,
            api_key=getenv("OPENAI_API_KEY") or getenv("API_KEY"),
            base_url=getenv("OPENAI_BASE_URL") or getenv("BASE_URL"),
            huggingface_api_key=getenv("HUGGINGFACE_API_KEY"),
        )


# Singleton used by embeddings modules
embeddings_settings: EmbeddingsConfig = EmbeddingsConfig.from_env()
