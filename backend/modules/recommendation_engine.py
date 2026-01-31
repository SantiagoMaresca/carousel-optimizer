"""
AI-powered carousel recommendation engine with diversity-aware ranking.
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from modules.quality_metrics import QualityMetrics
from modules.similarity import SimilarityResult, SimilarityAnalyzer
from core.logger import get_ai_logger


logger = get_ai_logger()


@dataclass
class ImageData:
    """Container for image data and metadata."""
    id: str
    filename: str
    path: Path
    quality_metrics: QualityMetrics
    embedding: Optional[Any] = None


@dataclass
class RecommendationItem:
    """Container for a single recommendation item."""
    position: int
    image_id: str
    score: float
    reason: str
    is_hero: bool = False


class RecommendationResult:
    """Container for carousel recommendation results."""
    
    def __init__(self, recommendations: List[RecommendationItem], similarity_result: SimilarityResult):
        self.recommendations = recommendations
        self.similarity_result = similarity_result
        self.hero_image = next((r for r in recommendations if r.is_hero), None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "recommended_order": [
                {
                    "position": r.position,
                    "image_id": r.image_id,
                    "score": round(r.score, 2),
                    "reason": r.reason,
                    "is_hero": r.is_hero
                }
                for r in self.recommendations
            ],
            "hero_image": {
                "image_id": self.hero_image.image_id,
                "score": round(self.hero_image.score, 2),
                "reason": self.hero_image.reason
            } if self.hero_image else None,
            "similarity_analysis": self.similarity_result.to_dict()
        }


class CarouselRecommendationEngine:
    """
    AI-powered recommendation engine for optimal carousel ordering.
    
    Uses a combination of quality metrics, diversity scoring, and duplicate detection
    to recommend the best order for product images in a carousel.
    """
    
    def __init__(self):
        self.quality_weight = 0.6
        self.diversity_weight = 0.4
        self.duplicate_penalty = 0.3
        logger.info("CarouselRecommendationEngine initialized", 
                   quality_weight=self.quality_weight,
                   diversity_weight=self.diversity_weight,
                   duplicate_penalty=self.duplicate_penalty)
    
    async def generate_recommendations(
        self,
        images: List[ImageData],
        embeddings: List[Any],
        duplicate_threshold: float = 0.92
    ) -> RecommendationResult:
        """
        Generate carousel recommendations for a set of images.
        
        Args:
            images: List of ImageData objects
            embeddings: List of CLIP embeddings for each image
            duplicate_threshold: Similarity threshold for duplicate detection
            
        Returns:
            RecommendationResult with ordered recommendations
        """
        logger.info("Generating carousel recommendations", 
                   image_count=len(images),
                   duplicate_threshold=duplicate_threshold)
        
        if not images:
            logger.warning("No images provided for recommendations")
            return RecommendationResult([], SimilarityResult([], []))
        
        # Analyze similarity between images
        image_ids = [img.id for img in images]
        similarity_result = await SimilarityAnalyzer.analyze_similarity(
            embeddings, image_ids, duplicate_threshold
        )
        
        # Get duplicate image IDs
        duplicate_ids = similarity_result.get_duplicate_ids()
        
        # Select hero image
        hero_image = await self._select_hero_image(images, duplicate_ids)
        
        # Rank remaining images
        remaining_images = [img for img in images if img.id != hero_image.id]
        ranked_images = await self._rank_remaining_images(
            remaining_images, 
            [hero_image],
            similarity_result,
            duplicate_ids
        )
        
        # Create recommendation items
        recommendations = [
            RecommendationItem(
                position=1,
                image_id=hero_image.id,
                score=hero_image.quality_metrics.composite_score,
                reason=f"Hero: {self._get_hero_reason(hero_image, duplicate_ids)}",
                is_hero=True
            )
        ]
        
        for i, (image, score, reason) in enumerate(ranked_images, start=2):
            recommendations.append(RecommendationItem(
                position=i,
                image_id=image.id,
                score=score,
                reason=reason
            ))
        
        result = RecommendationResult(recommendations, similarity_result)
        
        logger.info("Carousel recommendations generated", 
                   total_items=len(recommendations),
                   hero_id=hero_image.id,
                   duplicate_count=len(duplicate_ids))
        
        return result
    
    async def _select_hero_image(self, images: List[ImageData], duplicate_ids: set) -> ImageData:
        """
        Select the best hero image based on quality and duplicate status.
        
        Args:
            images: List of available images
            duplicate_ids: Set of image IDs that are duplicates
            
        Returns:
            Selected hero image
        """
        logger.debug("Selecting hero image", 
                    image_count=len(images),
                    duplicate_count=len(duplicate_ids))
        
        # Score images for hero selection
        scored_images = []
        
        for image in images:
            quality_score = image.quality_metrics.composite_score
            
            # Penalize duplicates heavily for hero selection
            if image.id in duplicate_ids:
                quality_score *= 0.2  # Strong penalty
            
            # Bonus for good resolution
            width, height = image.quality_metrics.resolution
            if width >= 1200 and height >= 800:
                quality_score *= 1.1
            
            scored_images.append((image, quality_score))
        
        # Select highest scoring image
        hero_image, hero_score = max(scored_images, key=lambda x: x[1])
        
        logger.info("Hero image selected", 
                   hero_id=hero_image.id,
                   hero_score=hero_score,
                   is_duplicate=hero_image.id in duplicate_ids)
        
        return hero_image
    
    async def _rank_remaining_images(
        self,
        images: List[ImageData],
        selected_images: List[ImageData],
        similarity_result: SimilarityResult,
        duplicate_ids: set
    ) -> List[Tuple[ImageData, float, str]]:
        """
        Rank remaining images using quality and diversity scoring.
        
        Args:
            images: Images to rank
            selected_images: Already selected images (hero)
            similarity_result: Similarity analysis result
            duplicate_ids: Set of duplicate image IDs
            
        Returns:
            List of (image, score, reason) tuples sorted by score
        """
        logger.debug("Ranking remaining images", 
                    remaining_count=len(images),
                    selected_count=len(selected_images))
        
        scored_images = []
        selected_ids = [img.id for img in selected_images]
        
        for image in images:
            # Base quality score
            quality_score = image.quality_metrics.composite_score / 100.0
            
            # Diversity score (how different from already selected)
            diversity_score = SimilarityAnalyzer.get_diversity_score(
                image.id, selected_ids, similarity_result
            )
            
            # Combined score
            combined_score = (
                self.quality_weight * quality_score +
                self.diversity_weight * diversity_score
            )
            
            # Apply duplicate penalty
            is_duplicate = image.id in duplicate_ids
            if is_duplicate:
                combined_score *= self.duplicate_penalty
            
            # Generate professional reason
            reason_parts = []
            
            # Quality assessment
            if quality_score >= 0.85:
                reason_parts.append("✅ Premium quality")
            elif quality_score >= 0.70:
                reason_parts.append("✓ Strong quality")
            elif quality_score >= 0.60:
                reason_parts.append("Good quality")
            else:
                reason_parts.append("Acceptable quality")
            
            # Diversity value
            if diversity_score > 0.75:
                reason_parts.append("🎯 Unique angle - Adds product depth")
            elif diversity_score > 0.5:
                reason_parts.append("📸 Good variety - Enhances carousel flow")
            elif diversity_score > 0.3:
                reason_parts.append("Similar perspective - Use strategically")
            else:
                reason_parts.append("⚠️ Very similar - Consider replacing")
            
            # Specific strengths
            if image.quality_metrics.blur_score > 500:
                reason_parts.append("Sharp details")
            if image.quality_metrics.resolution[0] >= 1920:
                reason_parts.append("High-res")
            
            # Duplicate warning
            if is_duplicate:
                reason_parts.append("⚠️ Duplicate detected - Remove or replace")
            
            reason = " • ".join(reason_parts)
            
            scored_images.append((image, combined_score * 100, reason))
        
        # Sort by score (descending)
        ranked_images = sorted(scored_images, key=lambda x: x[1], reverse=True)
        
        logger.debug("Image ranking completed", 
                    ranked_count=len(ranked_images),
                    top_score=ranked_images[0][1] if ranked_images else 0)
        
        return ranked_images
    
    def _get_hero_reason(self, hero_image: ImageData, duplicate_ids: set) -> str:
        """Generate reason string for hero image selection."""
        reasons = []
        
        quality = hero_image.quality_metrics.composite_score
        if quality >= 90:
            reasons.append("🏆 Premium quality (top 10%)")
        elif quality >= 80:
            reasons.append("⭐ Excellent quality")
        elif quality >= 70:
            reasons.append("✓ Strong quality")
        elif quality >= 60:
            reasons.append("Good quality")
        else:
            reasons.append("Acceptable quality")
        
        # Add specific strengths
        if hero_image.quality_metrics.blur_score > 500:
            reasons.append("crystal clear focus")
        
        if 110 <= hero_image.quality_metrics.brightness <= 145:
            reasons.append("optimal lighting")
        
        if hero_image.quality_metrics.contrast > 50:
            reasons.append("vibrant contrast")
        
        width, height = hero_image.quality_metrics.resolution
        if width >= 1920 and height >= 1080:
            reasons.append("premium resolution")
        elif width >= 1200 and height >= 800:
            reasons.append("high resolution")
        
        if hero_image.id not in duplicate_ids:
            reasons.append("unique perspective")
        
        # E-commerce value proposition
        if quality >= 85 and hero_image.quality_metrics.blur_score > 500:
            reasons.append("💰 Maximizes conversion potential")
        
        return " • ".join(reasons) if reasons else "Best available - consider retaking for optimal results"
    
    def update_weights(self, quality_weight: float, diversity_weight: float) -> None:
        """Update scoring weights for recommendation algorithm."""
        if abs(quality_weight + diversity_weight - 1.0) > 0.01:
            raise ValueError("Quality and diversity weights must sum to 1.0")
        
        self.quality_weight = quality_weight
        self.diversity_weight = diversity_weight
        
        logger.info("Recommendation weights updated", 
                   quality_weight=quality_weight,
                   diversity_weight=diversity_weight)
    
    def set_duplicate_penalty(self, penalty: float) -> None:
        """Set penalty factor for duplicate images (0-1)."""
        if not 0 <= penalty <= 1:
            raise ValueError("Duplicate penalty must be between 0 and 1")
        
        self.duplicate_penalty = penalty
        logger.info("Duplicate penalty updated", penalty=penalty)


# Global recommendation engine instance
recommendation_engine = CarouselRecommendationEngine()