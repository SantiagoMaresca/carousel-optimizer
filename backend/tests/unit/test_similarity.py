"""
Unit tests for similarity analysis.
"""

import pytest
import numpy as np
from modules.similarity import SimilarityAnalyzer, SimilarityResult


class TestSimilarityResult:
    """Test SimilarityResult functionality."""
    
    @pytest.fixture
    def sample_similarity_matrix(self):
        """Create sample similarity matrix."""
        # 3x3 similarity matrix with known values
        return np.array([
            [1.0, 0.8, 0.2],
            [0.8, 1.0, 0.3],
            [0.2, 0.3, 1.0]
        ])
    
    @pytest.fixture
    def sample_image_ids(self):
        """Sample image IDs."""
        return ["img1", "img2", "img3"]
    
    def test_similarity_result_creation(self, sample_similarity_matrix, sample_image_ids):
        """Test SimilarityResult object creation."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        
        assert np.array_equal(result.similarity_matrix, sample_similarity_matrix)
        assert result.image_ids == sample_image_ids
        assert isinstance(result.duplicates, list)
    
    def test_duplicate_detection_default_threshold(self, sample_similarity_matrix, sample_image_ids):
        """Test duplicate detection with default threshold."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        
        # No pairs above 0.92 threshold in our sample matrix
        assert len(result.duplicates) == 0
    
    def test_duplicate_detection_custom_threshold(self, sample_similarity_matrix, sample_image_ids):
        """Test duplicate detection with custom threshold."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        # Override with lower threshold
        result.duplicates = result._find_duplicates(threshold=0.7)
        
        # Should find img1-img2 pair (similarity 0.8)
        assert len(result.duplicates) == 1
        assert result.duplicates[0]["image_a"] == "img1"
        assert result.duplicates[0]["image_b"] == "img2"
        assert result.duplicates[0]["similarity"] == 0.8
    
    def test_get_similarity(self, sample_similarity_matrix, sample_image_ids):
        """Test getting similarity between specific images."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        
        assert result.get_similarity("img1", "img2") == 0.8
        assert result.get_similarity("img2", "img1") == 0.8  # Symmetric
        assert result.get_similarity("img1", "img3") == 0.2
        assert result.get_similarity("nonexistent", "img1") == 0.0
    
    def test_get_duplicate_ids(self, sample_similarity_matrix, sample_image_ids):
        """Test getting all duplicate image IDs."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        result.duplicates = result._find_duplicates(threshold=0.7)
        
        duplicate_ids = result.get_duplicate_ids()
        assert duplicate_ids == {"img1", "img2"}
    
    def test_to_dict_serialization(self, sample_similarity_matrix, sample_image_ids):
        """Test dictionary serialization."""
        result = SimilarityResult(sample_similarity_matrix, sample_image_ids)
        serialized = result.to_dict()
        
        required_keys = {"duplicates", "duplicate_count", "similarity_stats"}
        assert set(serialized.keys()) == required_keys
        
        # Check similarity stats
        stats = serialized["similarity_stats"]
        assert "mean" in stats
        assert "std" in stats
        assert "max" in stats
        assert "min" in stats


class TestSimilarityAnalyzer:
    """Test SimilarityAnalyzer functionality."""
    
    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings."""
        # Create embeddings that will have known similarities
        emb1 = np.array([1.0, 0.0, 0.0])  # Orthogonal vectors
        emb2 = np.array([0.0, 1.0, 0.0])
        emb3 = np.array([0.707, 0.707, 0.0])  # 45 degree angle with emb1 and emb2
        
        # Normalize to unit length
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        emb3 = emb3 / np.linalg.norm(emb3)
        
        return [emb1, emb2, emb3]
    
    @pytest.mark.asyncio
    async def test_compute_similarity_matrix(self, sample_embeddings):
        """Test similarity matrix computation."""
        matrix = await SimilarityAnalyzer.compute_similarity_matrix(sample_embeddings)
        
        assert matrix.shape == (3, 3)
        
        # Check diagonal elements (self-similarity should be 1.0)
        assert np.allclose(np.diag(matrix), 1.0)
        
        # Check symmetry
        assert np.allclose(matrix, matrix.T)
        
        # Check orthogonal vectors have 0 similarity
        assert np.isclose(matrix[0, 1], 0.0, atol=1e-6)
    
    @pytest.mark.asyncio
    async def test_compute_similarity_matrix_empty(self):
        """Test similarity matrix computation with empty input."""
        matrix = await SimilarityAnalyzer.compute_similarity_matrix([])
        assert matrix.size == 0
    
    @pytest.mark.asyncio
    async def test_analyze_similarity(self, sample_embeddings):
        """Test complete similarity analysis."""
        image_ids = ["img1", "img2", "img3"]
        
        result = await SimilarityAnalyzer.analyze_similarity(
            sample_embeddings, 
            image_ids,
            duplicate_threshold=0.5
        )
        
        assert isinstance(result, SimilarityResult)
        assert result.image_ids == image_ids
        assert result.similarity_matrix.shape == (3, 3)
        
        # With threshold 0.5, should detect img1-img3 and img2-img3 as similar
        # (45 degree angle gives ~0.707 similarity)
        assert len(result.duplicates) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_similarity_mismatched_inputs(self):
        """Test error handling for mismatched inputs."""
        embeddings = [np.array([1.0, 0.0]), np.array([0.0, 1.0])]
        image_ids = ["img1"]  # Mismatch: 2 embeddings, 1 ID
        
        with pytest.raises(ValueError, match="Number of embeddings must match"):
            await SimilarityAnalyzer.analyze_similarity(embeddings, image_ids)
    
    def test_get_redundancy_score(self, sample_embeddings):
        """Test redundancy score calculation."""
        image_ids = ["img1", "img2", "img3"]
        similarity_matrix = np.array([
            [1.0, 0.0, 0.707],
            [0.0, 1.0, 0.707],
            [0.707, 0.707, 1.0]
        ])
        
        result = SimilarityResult(similarity_matrix, image_ids)
        
        # img3 should have highest redundancy (similar to both img1 and img2)
        redundancy_img3 = SimilarityAnalyzer.get_redundancy_score("img3", result)
        redundancy_img1 = SimilarityAnalyzer.get_redundancy_score("img1", result)
        
        assert redundancy_img3 > redundancy_img1
        assert 0 <= redundancy_img3 <= 1
        assert 0 <= redundancy_img1 <= 1
    
    def test_get_redundancy_score_nonexistent(self, sample_embeddings):
        """Test redundancy score for nonexistent image."""
        image_ids = ["img1", "img2"]
        similarity_matrix = np.eye(2)
        result = SimilarityResult(similarity_matrix, image_ids)
        
        redundancy = SimilarityAnalyzer.get_redundancy_score("nonexistent", result)
        assert redundancy == 0.0
    
    def test_get_diversity_score(self):
        """Test diversity score calculation."""
        image_ids = ["img1", "img2", "img3"]
        similarity_matrix = np.array([
            [1.0, 0.8, 0.2],
            [0.8, 1.0, 0.3],
            [0.2, 0.3, 1.0]
        ])
        
        result = SimilarityResult(similarity_matrix, image_ids)
        
        # Test diversity relative to img1
        diversity = SimilarityAnalyzer.get_diversity_score("img3", ["img1"], result)
        expected_diversity = 1.0 - 0.2  # 1 - similarity(img3, img1)
        assert np.isclose(diversity, expected_diversity)
        
        # Test diversity relative to multiple images
        diversity_multi = SimilarityAnalyzer.get_diversity_score("img3", ["img1", "img2"], result)
        expected_diversity_multi = 1.0 - max(0.2, 0.3)  # 1 - max_similarity
        assert np.isclose(diversity_multi, expected_diversity_multi)
    
    def test_get_diversity_score_no_selected(self):
        """Test diversity score with no selected images."""
        image_ids = ["img1", "img2"]
        similarity_matrix = np.eye(2)
        result = SimilarityResult(similarity_matrix, image_ids)
        
        diversity = SimilarityAnalyzer.get_diversity_score("img1", [], result)
        assert diversity == 1.0