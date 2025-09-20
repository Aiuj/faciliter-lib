"""Base embedding client interface and helpers."""
from typing import List, Union, cast
import logging
import numpy as np
import hashlib
import json

from .embeddings_config import embeddings_settings
from ..cache.cache_manager import cache_get, cache_set

logger = logging.getLogger(__name__)


class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails."""
    pass


class BaseEmbeddingClient:
    """Abstract base client for embedding providers.

    Concrete implementations should implement `_generate_embedding_raw` (which takes List[str] and returns List[List[float]]) and may
    override `normalize`, `_l2_normalize`, and `health_check` as needed.
    """

    def __init__(self, model: str | None = None, embedding_dim: int | None = None, use_l2_norm: bool = True, cache_duration_seconds: int | None = None):
        # Use provided values, otherwise fall back to settings defaults
        self.model = model if model is not None else embeddings_settings.model
        self.embedding_dim = embedding_dim if embedding_dim is not None else embeddings_settings.embedding_dimension
        self.cache_duration_seconds = cache_duration_seconds if cache_duration_seconds is not None else embeddings_settings.cache_duration_seconds
        self.embedding_time_ms = 0
        self.use_l2_norm = use_l2_norm

    def _generate_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text and model configuration."""
        cache_data = {
            "text": text,
            "model": self.model,
            "embedding_dim": self.embedding_dim,
            "use_l2_norm": self.use_l2_norm,
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"embedding:{hashlib.sha256(cache_string.encode()).hexdigest()}"

    def generate_embedding(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for the given text(s), applying L2 normalization if enabled."""
        if isinstance(text, str):
            return self.generate_embedding_single(text)
        elif isinstance(text, list):
            return self.generate_embedding_batch(text)
        else:
            raise ValueError("Input must be a string or list of strings")

    def generate_embedding_single(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        # Check cache first
        cache_key = self._generate_cache_key(text)
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for embedding: {cache_key}")
            return cached_result
        
        # Generate new embedding
        embeddings = self._generate_embedding_raw([text])
        if self.use_l2_norm:
            # _l2_normalize now expects a list of vectors; wrap and unwrap
            embeddings = self._l2_normalize(embeddings)
        
        result = embeddings[0] if embeddings else []
        
        # Cache the result
        cache_set(cache_key, result, ttl=self.cache_duration_seconds)
        logger.debug(f"Cached embedding result: {cache_key}")
        
        return result

    def generate_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text strings."""
        results = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._generate_cache_key(text)
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for embedding: {cache_key}")
                results.append((i, cached_result))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            embeddings = self._generate_embedding_raw(uncached_texts)
            if self.use_l2_norm:
                embeddings = self._l2_normalize(embeddings)
            
            # Cache and collect the new embeddings
            for j, (text, embedding) in enumerate(zip(uncached_texts, embeddings)):
                cache_key = self._generate_cache_key(text)
                cache_set(cache_key, embedding, ttl=self.cache_duration_seconds)
                logger.debug(f"Cached embedding result: {cache_key}")
                results.append((uncached_indices[j], embedding))
        
        # Sort results by original index and return embeddings in order
        results.sort(key=lambda x: x[0])
        return [embedding for _, embedding in results]

    def _generate_embedding_raw(self, texts: List[str]) -> List[List[float]]:
        """Abstract method for generating raw embeddings without normalization.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors, one for each input text.
        """
        raise NotImplementedError()

    def normalize(self, vec: list) -> list:
        """Normalize the embedding vector to the expected dimension.

        Args:
            vec: The embedding vector to normalize.

        Returns:
            The normalized vector (padded, truncated, or as-is).
        """
        dim = self.embedding_dim
        if not isinstance(vec, list):
            return [0.0] * dim
        if len(vec) == dim:
            return vec
        if len(vec) > dim:
            return vec[:dim]
        # pad
        return vec + [0.0] * (dim - len(vec))

    def _l2_normalize(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Apply L2 normalization to a list of embedding vectors using numpy.

        Args:
            embeddings: List of embedding vectors.

        Returns:
            List of L2 normalized embedding vectors.
        """
        normalized = []
        for vec in embeddings:
            vec_np = np.array(vec, dtype=np.float32)
            norm = np.linalg.norm(vec_np)
            if norm > 0:
                normalized_vec = (vec_np / norm).tolist()
            else:
                normalized_vec = vec_np.tolist()  # Avoid division by zero
            normalized.append(normalized_vec)
        return normalized

    def health_check(self) -> bool:
        """Optional health check. Return True if service reachable."""
        return True

    def get_embedding_time_ms(self) -> float:
        return self.embedding_time_ms
