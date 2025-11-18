"""
Embeddings configuration module.

This module provides embeddings configuration re-exported from the centralized
config module. Use `EmbeddingsSettings` (the canonical class) or the singleton
`embeddings_settings` loaded from environment variables.

For backward compatibility, EmbeddingsConfig is an alias to EmbeddingsSettings.
"""

from __future__ import annotations

from enum import Enum

from ..config.embeddings_settings import EmbeddingsSettings


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


# Backward compatibility alias - EmbeddingsConfig is now EmbeddingsSettings
EmbeddingsConfig = EmbeddingsSettings

# Singleton used by embeddings modules
embeddings_settings: EmbeddingsSettings = EmbeddingsSettings.from_env(load_dotenv=False)
