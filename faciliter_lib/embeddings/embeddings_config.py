"""
Embeddings configuration module.

Modeled after the project's LLM config style. Provides a Pydantic-based
`EmbeddingsConfig` and a singleton `embeddings_settings` loaded from
environment variables.
"""

from __future__ import annotations

import os
from typing import Optional
from enum import Enum

from pydantic import BaseModel


class TaskType(str, Enum):
    """Supported embedding task types based on Google GenAI documentation."""
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    CLASSIFICATION = "CLASSIFICATION"
    CLUSTERING = "CLUSTERING"
    RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
    RETRIEVAL_QUERY = "RETRIEVAL_QUERY"
    CODE_RETRIEVAL_QUERY = "CODE_RETRIEVAL_QUERY"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    FACT_VERIFICATION = "FACT_VERIFICATION"
    # Legacy alias for backward compatibility
    DOCUMENT_RETRIEVAL = "RETRIEVAL_DOCUMENT"


class EmbeddingsConfig(BaseModel):
    """Configuration for embeddings providers.

    Fields are intentionally permissive to support OpenAI, Ollama, HuggingFace,
    Google GenAI, and other embedding providers. Use `from_env()` to populate from
    environment variables.
    """

    provider: str = "openai"
    model: str = "text-embedding-3-small"
    embedding_dimension: Optional[int] = None  # Optional dimension, can be set from env
    
    # Task configuration
    task_type: Optional[str] = None
    title: Optional[str] = None  # For Google GenAI

    # Ollama-specific
    ollama_host: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_timeout: Optional[int] = None

    # Infinity-specific (reuses base_url and ollama_timeout)
    # Infinity runs on http://localhost:7997 by default
    infinity_url: Optional[str] = None  # Alias for base_url
    infinity_timeout: Optional[int] = None  # Alias for ollama_timeout

    # OpenAI / compatible
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None

    # Google GenAI specific
    google_api_key: Optional[str] = None

    # Local model specific
    device: Optional[str] = None
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False
    use_sentence_transformers: bool = True

    # HuggingFace or other providers
    huggingface_api_key: Optional[str] = None
    
    # Cache configuration
    cache_duration_seconds: int = 7200  # 2 hours default

    @classmethod
    def from_env(cls) -> "EmbeddingsConfig":
        def getenv(name: str, default: Optional[str] = None) -> Optional[str]:
            v = os.getenv(name)
            return v if v is not None else default

        provider = (getenv("EMBEDDING_PROVIDER", "openai") or "openai").lower()
        model = getenv("EMBEDDING_MODEL", "text-embedding-3-small") or "text-embedding-3-small"

        emb_dim = getenv("EMBEDDING_DIMENSION")
        # Handle both string and int types from environment
        if isinstance(emb_dim, int):
            embedding_dimension = emb_dim
        elif emb_dim and str(emb_dim).isdigit():
            embedding_dimension = int(emb_dim)
        else:
            embedding_dimension = None

        ollama_timeout = None
        ot = getenv("OLLAMA_TIMEOUT")
        if ot and ot.isdigit():
            ollama_timeout = int(ot)

        # Task configuration
        task_type = getenv("EMBEDDING_TASK_TYPE")
        title = getenv("EMBEDDING_TITLE")

        # Device configuration for local models
        device = getenv("EMBEDDING_DEVICE", "auto")
        cache_dir = getenv("EMBEDDING_CACHE_DIR")
        trust_remote_code = getenv("EMBEDDING_TRUST_REMOTE_CODE", "false").lower() == "true"
        use_sentence_transformers = getenv("EMBEDDING_USE_SENTENCE_TRANSFORMERS", "true").lower() == "true"
        
        # Cache configuration
        cache_duration = getenv("EMBEDDING_CACHE_DURATION_SECONDS", "86400")
        cache_duration_seconds = int(cache_duration) if cache_duration.isdigit() else 86400
        
        # Unified timeout configuration (shared across providers)
        embedding_timeout = None
        et = getenv("EMBEDDING_TIMEOUT")
        if et and et.isdigit():
            embedding_timeout = int(et)
        
        infinity_timeout = None
        it = getenv("INFINITY_TIMEOUT")
        if it and it.isdigit():
            infinity_timeout = int(it)

        # Unified base URL configuration
        # EMBEDDING_BASE_URL serves as common default for all providers
        # Provider-specific URLs (OLLAMA_URL, INFINITY_URL, OPENAI_BASE_URL) override for multi-provider setups
        embedding_base_url = getenv("EMBEDDING_BASE_URL")
        infinity_url = getenv("INFINITY_URL") or getenv("INFINITY_BASE_URL") or embedding_base_url
        ollama_url = getenv("OLLAMA_URL") or embedding_base_url
        openai_base_url = getenv("OPENAI_BASE_URL") or getenv("BASE_URL") or embedding_base_url

        return cls(
            provider=provider,
            model=model,
            embedding_dimension=embedding_dimension,
            task_type=task_type,
            title=title,
            ollama_host=getenv("OLLAMA_HOST"),
            ollama_url=ollama_url,
            ollama_timeout=embedding_timeout or ollama_timeout,
            api_key=getenv("OPENAI_API_KEY") or getenv("API_KEY"),
            base_url=openai_base_url,
            organization=getenv("OPENAI_ORGANIZATION"),
            project=getenv("OPENAI_PROJECT"),
            google_api_key=getenv("GOOGLE_GENAI_API_KEY") or getenv("GEMINI_API_KEY"),
            device=device,
            cache_dir=cache_dir,
            trust_remote_code=trust_remote_code,
            use_sentence_transformers=use_sentence_transformers,
            huggingface_api_key=getenv("HUGGINGFACE_API_KEY"),
            cache_duration_seconds=cache_duration_seconds,
            infinity_url=infinity_url,
            infinity_timeout=embedding_timeout or infinity_timeout,
        )


# Singleton used by embeddings modules
embeddings_settings: EmbeddingsConfig = EmbeddingsConfig.from_env()
