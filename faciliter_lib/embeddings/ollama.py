"""Ollama embedding client implementation."""
import time
import logging
import ollama
from typing import List, Union, cast

from .embeddings_config import embeddings_settings
from .base import BaseEmbeddingClient, EmbeddingGenerationError
from .models import EmbeddingResponse

logger = logging.getLogger(__name__)


class OllamaEmbeddingClient(BaseEmbeddingClient):
    """Client for generating embeddings using a local Ollama HTTP API."""

    def __init__(self, model: str | None = None, embedding_dim: int | None = None, use_l2_norm: bool = False, base_url: str | None = None, timeout: int | None = None):
        # If model/embedding_dim are not provided, BaseEmbeddingClient will
        # fall back to values from `settings`.
        super().__init__(model=model, embedding_dim=embedding_dim, use_l2_norm=use_l2_norm)
        # Priority: explicit param > OLLAMA_URL > EMBEDDING_BASE_URL > default
        self.base_url = base_url or embeddings_settings.ollama_url or "http://localhost:11434"
        # Priority: explicit param > OLLAMA_TIMEOUT > EMBEDDING_TIMEOUT > None
        self.timeout = timeout or embeddings_settings.ollama_timeout
        """Initialize Ollama client with configuration from settings."""
        self.client = ollama.Client(host=self.base_url)  # Use Ollama library client

    def _generate_embedding_raw(self, texts: List[str]) -> List[List[float]]:
        """Generate raw embeddings for a list of texts without L2 normalization.

        Args:
            texts: List of text strings to generate embeddings for.

        Returns:
            A list of embedding vectors (List[List[float]]), one per input text.

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not isinstance(texts, list) or not texts:
            raise EmbeddingGenerationError("Input must be a non-empty list of strings")

        # Validate and strip inputs
        if any(not t or not isinstance(t, str) or not t.strip() for t in texts):
            raise EmbeddingGenerationError("All texts must be non-empty strings")

        input_data = [t.strip() for t in texts]

        try:
            # Use Ollama library's embed function
            start_time = time.perf_counter()
            response = self.client.embed(model=self.model, input=input_data)
            end_time = time.perf_counter()
            self.embedding_time_ms = (end_time - start_time) * 1000

            # Parse response using EmbeddingResponse. The ollama client may return
            # a library response object rather than a plain dict, so coerce to dict
            # Coerce the library response to a plain dict with expected keys.
            response_data: dict
            if isinstance(response, dict):
                response_data = response
            else:
                # Try common conversion paths
                if hasattr(response, "dict") and callable(getattr(response, "dict")):
                    try:
                        response_data = response.dict()
                    except Exception:
                        response_data = {}
                elif hasattr(response, "__dict__"):
                    response_data = dict(getattr(response, "__dict__", {}))
                else:
                    # Last resort: try to convert to dict
                    try:
                        response_data = dict(response)
                    except Exception:
                        response_data = {}

            # Ensure keys are in the shape EmbeddingResponse expects
            if 'embeddings' not in response_data and 'embedding' not in response_data:
                # Try to extract plausible attributes
                possible_embedding = getattr(response, 'embedding', None) or getattr(response, 'embeddings', None)
                if possible_embedding is not None:
                    response_data = {'embedding': possible_embedding, 'model': getattr(response, 'model', self.model)}

            embedding_response = EmbeddingResponse.from_dict(response_data)

            # Normalize each returned embedding using BaseEmbeddingClient.normalize
            embeddings_raw = embedding_response.embedding

            # If the API returned a single vector for the batch, wrap it into a list
            if isinstance(embeddings_raw, list) and embeddings_raw and not isinstance(embeddings_raw[0], list):
                embeddings_raw = [embeddings_raw]

            if not isinstance(embeddings_raw, list):
                raise EmbeddingGenerationError("Unexpected embedding format from Ollama")

            embeddings_list = cast(List[List[float]], embeddings_raw)

            normalized: List[List[float]] = []
            for emb in embeddings_list:
                if not isinstance(emb, list) or len(emb) != self.embedding_dim:
                    logger.debug(
                        f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(emb) if hasattr(emb, '__len__') else 'unknown'}"
                    )
                normalized.append(self.normalize(emb))

            logger.debug(f"Generated {len(normalized)} embedding(s) using model {embedding_response.model}")
            return normalized

        except ollama.ResponseError as e:  # Use library's exception
            error_msg = f"Ollama API error: {e}"
            logger.error(error_msg)
            raise EmbeddingGenerationError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during embedding generation: {e}"
            logger.error(error_msg)
            raise EmbeddingGenerationError(error_msg)

    def health_check(self) -> bool:
        """Verify Ollama server is reachable and responsive.

        Attempts a lightweight call to the client. Returns True when the server
        responds without raising an exception, otherwise False.
        """
        try:
            # Prefer a non-destructive models() call if available
            if hasattr(self.client, "show"):
                show = self.client.show(model=self.model)
            else:
                # Fallback: tiny embed call (should be safe) to detect reachability
                _ = self.client.embed(model=self.model, input="healthcheck")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
