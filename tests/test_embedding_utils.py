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
    _pca_approximate
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
