"""
Tests for embedding dimension normalization utilities.
"""

import pytest
import numpy as np

from faciliter_lib.embeddings.embedding_utils import (
    normalize_embedding_dimension,
    normalize_embeddings_batch,
    _truncate_or_pad,
    _interpolate,
    _pca_approximate,
    is_matryoshka_model,
    get_best_normalization_method,
)

class TestNormalizeEmbeddingDimension:
    """Tests for normalize_embedding_dimension function."""
    
    def test_same_dimension_no_change(self):
        """Test that embeddings with correct dimension are unchanged."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = normalize_embedding_dimension(embedding, target_dimension=5)
        assert result == embedding
    
    def test_truncate_longer_embedding(self):
        """Test truncation of longer embeddings."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
        result = normalize_embedding_dimension(embedding, target_dimension=5, method="truncate_or_pad")
        assert len(result) == 5
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    def test_pad_shorter_embedding(self):
        """Test padding of shorter embeddings."""
        embedding = [0.1, 0.2, 0.3]
        result = normalize_embedding_dimension(embedding, target_dimension=5, method="truncate_or_pad")
        assert len(result) == 5
        assert result == [0.1, 0.2, 0.3, 0.0, 0.0]
    
    def test_interpolate_expansion(self):
        """Test interpolation for expanding dimensions."""
        embedding = [0.0, 1.0]
        result = normalize_embedding_dimension(embedding, target_dimension=5, method="interpolate")
        assert len(result) == 5
        # Result should be interpolated and normalized
        assert all(isinstance(x, float) for x in result)
    
    def test_interpolate_reduction(self):
        """Test interpolation for reducing dimensions."""
        embedding = [0.1] * 100
        result = normalize_embedding_dimension(embedding, target_dimension=50, method="interpolate")
        assert len(result) == 50
        assert all(isinstance(x, float) for x in result)
    
    def test_pca_approximate_reduction(self):
        """Test PCA-approximate method for dimension reduction."""
        embedding = [0.1] * 100
        result = normalize_embedding_dimension(embedding, target_dimension=50, method="pca_approximate")
        assert len(result) == 50
        assert all(isinstance(x, float) for x in result)
    
    def test_empty_embedding_returns_zero_vector(self):
        """Test that empty embeddings return zero vectors."""
        result = normalize_embedding_dimension([], target_dimension=10)
        assert result == [0.0] * 10
    
    def test_invalid_method_raises_error(self):
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported normalization method"):
            normalize_embedding_dimension([0.1, 0.2], target_dimension=5, method="invalid")


class TestNormalizeEmbeddingsBatch:
    """Tests for batch normalization."""
    
    def test_batch_normalization(self):
        """Test normalizing multiple embeddings at once."""
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]
        result = normalize_embeddings_batch(embeddings, target_dimension=5)
        assert len(result) == 3
        assert all(len(emb) == 5 for emb in result)
    
    def test_batch_with_error_fallback(self):
        """Test that batch normalization handles individual errors."""
        embeddings = [
            [0.1, 0.2, 0.3],
            None,  # Invalid embedding
            [0.7, 0.8, 0.9]
        ]
        # Should not raise, but return zero vector for invalid embedding
        result = normalize_embeddings_batch(embeddings, target_dimension=5)
        assert len(result) == 3
        assert result[1] == [0.0] * 5  # Fallback zero vector

class TestInterpolationQuality:
    """Tests to verify interpolation preserves embedding quality."""
    
    def test_interpolation_preserves_relative_magnitudes(self):
        """Test that interpolation preserves relative value relationships."""
        # Create embedding with clear pattern
        embedding = [0.0, 0.5, 1.0]
        result = normalize_embedding_dimension(embedding, target_dimension=6, method="interpolate")
        
        # Should maintain general pattern (increasing values)
        assert result[0] <= result[len(result)//2] <= result[-1]
    
    def test_interpolation_maintains_unit_norm(self):
        """Test that interpolation maintains unit norm (L2 normalized)."""
        embedding = [0.6, 0.8]  # Unit vector (0.6^2 + 0.8^2 = 1)
        result = normalize_embedding_dimension(embedding, target_dimension=5, method="interpolate")
        
        # Result should be approximately unit length
        norm = np.linalg.norm(result)
        assert 0.99 <= norm <= 1.01
    
    def test_dimension_reduction_768_to_512(self):
        """Test realistic scenario: reducing 768 to 512 dimensions."""
        # Simulate a 768-dimensional embedding (e.g., from BERT)
        embedding = [np.sin(i * 0.1) for i in range(768)]
        result = normalize_embedding_dimension(embedding, target_dimension=512, method="interpolate")
        
        assert len(result) == 512
        # Should maintain some similarity to original
        # Check that not all values are identical (i.e., information preserved)
        assert len(set(result)) > 100
    
    def test_dimension_expansion_512_to_1024(self):
        """Test realistic scenario: expanding 512 to 1024 dimensions."""
        # Simulate a 512-dimensional embedding
        embedding = [np.cos(i * 0.05) for i in range(512)]
        result = normalize_embedding_dimension(embedding, target_dimension=1024, method="interpolate")
        
        assert len(result) == 1024
        # Should maintain pattern
        assert len(set(result)) > 200


class TestTruncateOrPad:
    """Tests for the truncate_or_pad method."""
    
    def test_truncate(self):
        """Test truncation."""
        embedding = list(range(10))
        result = _truncate_or_pad(embedding, 5)
        assert result == [0, 1, 2, 3, 4]
    
    def test_pad(self):
        """Test padding."""
        embedding = [1, 2, 3]
        result = _truncate_or_pad(embedding, 5)
        assert result == [1, 2, 3, 0.0, 0.0]


class TestPCAApproximate:
    """Tests for the PCA-approximate method."""
    
    def test_reduction_with_averaging(self):
        """Test that PCA-approximate reduces dimensions by averaging."""
        # Create embedding where we can verify averaging
        embedding = [1.0] * 100
        result = _pca_approximate(embedding, 50)
        assert len(result) == 50
        # After L2 normalization, values should be approximately equal
        # and the norm should be close to 1
        norm = np.linalg.norm(result)
        assert 0.99 <= norm <= 1.01
        # All values should have similar magnitude after normalization
        mean_val = np.mean(result)
        assert all(abs(x - mean_val) < 0.1 for x in result)
    
    def test_expansion_falls_back_to_interpolate(self):
        """Test that expansion uses interpolation."""
        embedding = [0.0, 1.0]
        result = _pca_approximate(embedding, 10)
        assert len(result) == 10


class TestIsMatryoshkaModel:
    """Tests for Matryoshka model detection."""
    
    def test_nomic_models(self):
        """Test detection of Nomic models."""
        assert is_matryoshka_model("nomic-embed-text")
        assert is_matryoshka_model("nomic-embed-text-v1")
        assert is_matryoshka_model("nomic-embed-text-v1.5")
        assert is_matryoshka_model("nomic-ai/nomic-embed-text")
    
    def test_openai_models(self):
        """Test detection of OpenAI models with MRL."""
        assert is_matryoshka_model("text-embedding-3-small")
        assert is_matryoshka_model("text-embedding-3-large")
        assert is_matryoshka_model("text-embedding-3")
        # Old models should not be detected
        assert not is_matryoshka_model("text-embedding-ada-002")
    
    def test_jina_models(self):
        """Test detection of Jina models."""
        assert is_matryoshka_model("jinaai/jina-embeddings-v2-base-en")
        assert is_matryoshka_model("jina-embeddings-v2-base-en")
        assert is_matryoshka_model("jina-embeddings-v2")
        assert is_matryoshka_model("jina-embeddings-v3")
    
    def test_cohere_models(self):
        """Test detection of Cohere models."""
        assert is_matryoshka_model("embed-english-v3.0")
        assert is_matryoshka_model("embed-multilingual-v3.0")
    
    def test_fuzzy_matching(self):
        """Test fuzzy matching for model names with variations."""
        # Should match even with different casing
        assert is_matryoshka_model("NOMIC-EMBED-TEXT")
        assert is_matryoshka_model("Text-Embedding-3-Large")
        
        # Should match with extra characters
        assert is_matryoshka_model("snowflake/arctic-embed-large")
        assert is_matryoshka_model("mixedbread-ai/mxbai-embed-large-v1.5")
    
    def test_pattern_matching(self):
        """Test pattern-based detection."""
        assert is_matryoshka_model("custom-model-with-matryoshka")
        assert is_matryoshka_model("my-mrl-embeddings")
        assert is_matryoshka_model("adaptive-embeddings-v2")
    
    def test_non_matryoshka_models(self):
        """Test that non-MRL models are not detected."""
        assert not is_matryoshka_model("text-embedding-ada-002")
        assert not is_matryoshka_model("sentence-transformers/all-MiniLM-L6-v2")
        assert not is_matryoshka_model("bert-base-uncased")
        assert not is_matryoshka_model("custom-regular-model")
    
    def test_empty_or_none(self):
        """Test handling of empty or None model names."""
        assert not is_matryoshka_model("")
        assert not is_matryoshka_model(None)


class TestGetBestNormalizationMethod:
    """Tests for automatic normalization method selection."""
    
    def test_matryoshka_model_prefers_truncate_or_pad(self):
        """Test that Matryoshka models use truncate_or_pad."""
        method = get_best_normalization_method(
            model_name="nomic-embed-text-v1.5",
            current_dimension=768,
            target_dimension=512
        )
        assert method == "truncate_or_pad"
    
    def test_non_matryoshka_model_prefers_interpolate(self):
        """Test that non-MRL models use interpolate."""
        method = get_best_normalization_method(
            model_name="text-embedding-ada-002",
            current_dimension=1536,
            target_dimension=512
        )
        assert method == "interpolate"
    
    def test_large_dimension_increase_uses_interpolate(self):
        """Test that large dimension increases use interpolate."""
        method = get_best_normalization_method(
            current_dimension=512,
            target_dimension=1024
        )
        assert method == "interpolate"
    
    def test_large_reduction_non_matryoshka_uses_pca(self):
        """Test that large reductions for non-MRL models use PCA-approximate."""
        method = get_best_normalization_method(
            model_name="bert-base-uncased",
            current_dimension=1536,
            target_dimension=512
        )
        assert method == "pca_approximate"
    
    def test_same_dimension_uses_truncate_or_pad(self):
        """Test that same dimensions use truncate_or_pad (fastest)."""
        method = get_best_normalization_method(
            current_dimension=768,
            target_dimension=768
        )
        assert method == "truncate_or_pad"
    
    def test_default_without_parameters(self):
        """Test default recommendation without any parameters."""
        method = get_best_normalization_method()
        assert method == "interpolate"
    
    def test_matryoshka_overrides_dimension_logic(self):
        """Test that Matryoshka models override dimension-based logic."""
        # Even with large reduction, Matryoshka should use truncate_or_pad
        method = get_best_normalization_method(
            model_name="text-embedding-3-large",
            current_dimension=3072,
            target_dimension=512
        )
        assert method == "truncate_or_pad"
    
    def test_moderate_reduction_uses_interpolate(self):
        """Test that moderate reductions use interpolate."""
        method = get_best_normalization_method(
            current_dimension=768,
            target_dimension=600
        )
        assert method == "interpolate"
    
    def test_only_model_name_provided(self):
        """Test recommendation based only on model name."""
        # Matryoshka model
        method = get_best_normalization_method(model_name="nomic-embed-text")
        assert method == "truncate_or_pad"
        
        # Non-Matryoshka model - should use default
        method = get_best_normalization_method(model_name="bert-base")
        assert method == "interpolate"
    
    def test_only_dimensions_provided(self):
        """Test recommendation based only on dimensions."""
        # Small reduction
        method = get_best_normalization_method(current_dimension=768, target_dimension=700)
        assert method == "interpolate"
        
        # Large reduction
        method = get_best_normalization_method(current_dimension=1536, target_dimension=512)
        assert method == "pca_approximate"


class TestNormalizationWorkflow:
    """Integration tests for the complete normalization workflow."""
    
    def test_matryoshka_model_workflow(self):
        """Test complete workflow with Matryoshka model."""
        model_name = "nomic-embed-text-v1.5"
        embedding = [0.1 * i for i in range(768)]
        
        # Get recommended method
        method = get_best_normalization_method(
            model_name=model_name,
            current_dimension=len(embedding),
            target_dimension=512
        )
        
        # Apply normalization
        result = normalize_embedding_dimension(embedding, 512, method=method)
        
        assert len(result) == 512
        assert method == "truncate_or_pad"
        # First 512 values should match exactly
        assert result[:100] == embedding[:100]
    
    def test_non_matryoshka_workflow(self):
        """Test complete workflow with non-MRL model."""
        model_name = "bert-base-uncased"
        embedding = [0.1 * i for i in range(768)]
        
        # Get recommended method
        method = get_best_normalization_method(
            model_name=model_name,
            current_dimension=len(embedding),
            target_dimension=512
        )
        
        # Apply normalization
        result = normalize_embedding_dimension(embedding, 512, method=method)
        
        assert len(result) == 512
        assert method == "pca_approximate"
        # Values should be different due to PCA averaging
        assert result[:100] != embedding[:100]

