"""
Image similarity detection using cosine similarity of CLIP embeddings.
"""

import asyncio
from typing import List, Tuple, Dict, Set
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from core.logger import get_ai_logger


logger = get_ai_logger()


class SimilarityResult:
    """Container for similarity analysis results."""
    
    def __init__(self, similarity_matrix: np.ndarray, image_ids: List[str]):
        self.similarity_matrix = similarity_matrix
        self.image_ids = image_ids
        self.duplicates = self._find_duplicates()
    
    def _find_duplicates(self, threshold: float = 0.92) -> List[Dict[str, any]]:
        """Find duplicate image pairs based on similarity threshold."""
        duplicates = []
        n_images = len(self.image_ids)
        
        for i in range(n_images):
            for j in range(i + 1, n_images):
                similarity = self.similarity_matrix[i, j]
                if similarity > threshold:
                    duplicates.append({
                        "image_a": self.image_ids[i],
                        "image_b": self.image_ids[j],
                        "similarity": float(similarity)
                    })
        
        return duplicates
    
    def get_similarity(self, image_a_id: str, image_b_id: str) -> float:
        """Get similarity between two specific images."""
        try:
            idx_a = self.image_ids.index(image_a_id)
            idx_b = self.image_ids.index(image_b_id)
            return float(self.similarity_matrix[idx_a, idx_b])
        except ValueError:
            return 0.0
    
    def get_duplicate_ids(self) -> Set[str]:
        """Get set of all image IDs that are duplicates."""
        duplicate_ids = set()
        for dup in self.duplicates:
            duplicate_ids.add(dup["image_a"])
            duplicate_ids.add(dup["image_b"])
        return duplicate_ids
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "duplicates": self.duplicates,
            "duplicate_count": len(self.duplicates),
            "similarity_stats": {
                "mean": float(np.mean(self.similarity_matrix)),
                "std": float(np.std(self.similarity_matrix)),
                "max": float(np.max(self.similarity_matrix)),
                "min": float(np.min(self.similarity_matrix))
            }
        }


class SimilarityAnalyzer:
    """Analyzes image similarity using CLIP embeddings."""
    
    @staticmethod
    async def compute_similarity_matrix(embeddings: List[np.ndarray]) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix for embeddings.
        
        Args:
            embeddings: List of normalized embedding vectors
            
        Returns:
            Similarity matrix (n x n)
        """
        logger.info("Computing similarity matrix", embedding_count=len(embeddings))
        
        if not embeddings:
            return np.array([])
        
        try:
            # Stack embeddings into matrix
            embedding_matrix = np.stack(embeddings)
            
            # Compute cosine similarity in thread pool to avoid blocking
            similarity_matrix = await asyncio.to_thread(
                cosine_similarity, 
                embedding_matrix
            )
            
            logger.info("Similarity matrix computed", 
                       shape=similarity_matrix.shape,
                       mean_similarity=float(np.mean(similarity_matrix)),
                       max_similarity=float(np.max(similarity_matrix[similarity_matrix < 1.0])))
            
            return similarity_matrix
            
        except Exception as e:
            logger.error("Failed to compute similarity matrix", error=str(e))
            # Return identity matrix on failure
            n = len(embeddings)
            return np.eye(n)
    
    @classmethod
    async def analyze_similarity(
        self, 
        embeddings: List[np.ndarray], 
        image_ids: List[str],
        duplicate_threshold: float = 0.92
    ) -> SimilarityResult:
        """
        Analyze similarity between images and detect duplicates.
        
        Args:
            embeddings: List of image embeddings
            image_ids: Corresponding image identifiers
            duplicate_threshold: Similarity threshold for duplicate detection
            
        Returns:
            SimilarityResult with analysis results
        """
        logger.info("Starting similarity analysis", 
                   image_count=len(embeddings),
                   duplicate_threshold=duplicate_threshold)
        
        if len(embeddings) != len(image_ids):
            raise ValueError("Number of embeddings must match number of image IDs")
        
        if not embeddings:
            logger.warning("No embeddings provided for similarity analysis")
            return SimilarityResult(np.array([]), [])
        
        # Compute similarity matrix
        similarity_matrix = await self.compute_similarity_matrix(embeddings)
        
        # Create result object
        result = SimilarityResult(similarity_matrix, image_ids)
        
        # Override default threshold if specified
        if duplicate_threshold != 0.92:
            result.duplicates = result._find_duplicates(duplicate_threshold)
        
        logger.info("Similarity analysis completed", 
                   duplicate_pairs=len(result.duplicates),
                   duplicate_images=len(result.get_duplicate_ids()))
        
        return result
    
    @staticmethod
    def get_redundancy_score(image_id: str, result: SimilarityResult) -> float:
        """
        Calculate redundancy score for an image.
        Higher score means more similar to other images.
        
        Args:
            image_id: ID of the image to score
            result: Similarity analysis result
            
        Returns:
            Redundancy score (0-1, where 1 is most redundant)
        """
        try:
            idx = result.image_ids.index(image_id)
            similarities = result.similarity_matrix[idx]
            
            # Remove self-similarity
            other_similarities = np.concatenate([
                similarities[:idx], 
                similarities[idx+1:]
            ])
            
            if len(other_similarities) == 0:
                return 0.0
            
            # Use max similarity as redundancy score
            redundancy = float(np.max(other_similarities))
            
            logger.debug("Calculated redundancy score", 
                        image_id=image_id, 
                        redundancy=redundancy)
            
            return redundancy
            
        except (ValueError, IndexError) as e:
            logger.error("Failed to calculate redundancy score", 
                        image_id=image_id, 
                        error=str(e))
            return 0.0
    
    @staticmethod
    def get_diversity_score(
        image_id: str, 
        selected_ids: List[str], 
        result: SimilarityResult
    ) -> float:
        """
        Calculate diversity score for an image relative to already selected images.
        Higher score means more diverse from selected images.
        
        Args:
            image_id: ID of the image to score
            selected_ids: IDs of already selected images
            result: Similarity analysis result
            
        Returns:
            Diversity score (0-1, where 1 is most diverse)
        """
        if not selected_ids:
            return 1.0
        
        try:
            max_similarity = 0.0
            
            for selected_id in selected_ids:
                similarity = result.get_similarity(image_id, selected_id)
                max_similarity = max(max_similarity, similarity)
            
            diversity = 1.0 - max_similarity
            
            logger.debug("Calculated diversity score", 
                        image_id=image_id, 
                        selected_count=len(selected_ids),
                        diversity=diversity)
            
            return diversity
            
        except Exception as e:
            logger.error("Failed to calculate diversity score", 
                        image_id=image_id, 
                        error=str(e))
            return 0.0