"""
Integration tests for the recommendation engine.
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
import numpy as np

from modules.recommendation_engine import CarouselRecommendationEngine, ImageData
from modules.embeddings import EmbeddingGenerator
from modules.quality_metrics import QualityAnalyzer
from core.session_manager import session_manager


class TestRecommendationEngineIntegration:
    """Integration tests for recommendation engine with real components."""
    
    @pytest.fixture
    async def recommendation_engine(self):
        """Create recommendation engine with real components."""
        engine = RecommendationEngine()
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_images(self):
        """Create sample images with different characteristics."""
        temp_dir = Path(tempfile.mkdtemp())
        image_paths = []
        
        # High quality image
        high_quality = Image.new('RGB', (800, 600), color='white')
        high_quality_path = temp_dir / 'high_quality.jpg'
        high_quality.save(high_quality_path, 'JPEG', quality=95)
        image_paths.append(high_quality_path)
        
        # Medium quality image
        medium_quality = Image.new('RGB', (400, 300), color='gray')
        medium_quality_path = temp_dir / 'medium_quality.jpg'
        medium_quality.save(medium_quality_path, 'JPEG', quality=80)
        image_paths.append(medium_quality_path)
        
        # Low quality image
        low_quality = Image.new('RGB', (200, 150), color='black')
        low_quality_path = temp_dir / 'low_quality.jpg'
        low_quality.save(low_quality_path, 'JPEG', quality=60)
        image_paths.append(low_quality_path)
        
        # Similar image (duplicate candidate)
        similar_image = Image.new('RGB', (800, 600), color='lightgray')
        similar_path = temp_dir / 'similar.jpg'
        similar_image.save(similar_path, 'JPEG', quality=95)
        image_paths.append(similar_path)
        
        yield image_paths
        
        # Cleanup
        for path in image_paths:
            path.unlink(missing_ok=True)
        temp_dir.rmdir()
    
    @pytest.fixture
    async def sample_image_data(self, sample_images):
        """Create ImageData objects from sample images."""
        image_data_list = []
        
        for i, image_path in enumerate(sample_images):
            with open(image_path, 'rb') as f:
                content = f.read()
            
            image_data = ImageData(
                id=f"img_{i}",
                filename=image_path.name,
                content_type="image/jpeg",
                content=content,
                size=len(content),
                width=800 if 'high_quality' in image_path.name or 'similar' in image_path.name else 400 if 'medium' in image_path.name else 200,
                height=600 if 'high_quality' in image_path.name or 'similar' in image_path.name else 300 if 'medium' in image_path.name else 150
            )
            image_data_list.append(image_data)
        
        return image_data_list
    
    @pytest.mark.asyncio
    async def test_end_to_end_recommendation(self, recommendation_engine, sample_image_data):
        """Test complete recommendation pipeline."""
        # Run recommendation
        results = await recommendation_engine.recommend_order(sample_image_data)
        
        # Verify results structure
        assert isinstance(results, dict)
        required_keys = {"recommendations", "duplicates", "hero_image", "processing_stats"}
        assert set(results.keys()) == required_keys
        
        # Check recommendations
        recommendations = results["recommendations"]
        assert len(recommendations) == len(sample_image_data)
        
        for i, rec in enumerate(recommendations):
            assert rec["position"] == i + 1
            assert "image_id" in rec
            assert "score" in rec
            assert "reason" in rec
            assert isinstance(rec["is_hero"], bool)
            assert 0 <= rec["score"] <= 100
        
        # First recommendation should be hero
        assert recommendations[0]["is_hero"] is True
        assert results["hero_image"] == recommendations[0]["image_id"]
        
        # Check processing stats
        stats = results["processing_stats"]
        required_stat_keys = {
            "total_images", "embedding_time_ms", "quality_time_ms", 
            "similarity_time_ms", "ranking_time_ms", "total_time_ms"
        }
        assert set(stats.keys()) == required_stat_keys
        assert stats["total_images"] == len(sample_image_data)
        assert all(isinstance(v, (int, float)) for v in stats.values())
        assert all(v >= 0 for v in stats.values())
    
    @pytest.mark.asyncio
    async def test_duplicate_detection_integration(self, recommendation_engine):
        """Test duplicate detection with similar images."""
        # Create very similar images
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Original image
            original = Image.new('RGB', (400, 300), color='red')
            original_path = temp_dir / 'original.jpg'
            original.save(original_path, 'JPEG', quality=90)
            
            # Very similar image (slight color variation)
            similar = Image.new('RGB', (400, 300), color=(255, 10, 10))
            similar_path = temp_dir / 'similar.jpg'
            similar.save(similar_path, 'JPEG', quality=90)
            
            # Different image
            different = Image.new('RGB', (400, 300), color='blue')
            different_path = temp_dir / 'different.jpg'
            different.save(different_path, 'JPEG', quality=90)
            
            # Create ImageData objects
            image_data_list = []
            for i, path in enumerate([original_path, similar_path, different_path]):
                with open(path, 'rb') as f:
                    content = f.read()
                
                image_data = ImageData(
                    id=f"img_{i}",
                    filename=path.name,
                    content_type="image/jpeg",
                    content=content,
                    size=len(content),
                    width=400,
                    height=300
                )
                image_data_list.append(image_data)
            
            # Run recommendation with high duplicate sensitivity
            results = await recommendation_engine.recommend_order(
                image_data_list, 
                duplicate_threshold=0.8
            )
            
            # Should detect duplicates between original and similar images
            duplicates = results["duplicates"]
            assert len(duplicates) > 0
            
            # Verify duplicate structure
            for duplicate_pair in duplicates:
                assert "image1_id" in duplicate_pair
                assert "image2_id" in duplicate_pair
                assert "similarity_score" in duplicate_pair
                assert duplicate_pair["similarity_score"] >= 0.8
                
        finally:
            # Cleanup
            for path in [original_path, similar_path, different_path]:
                path.unlink(missing_ok=True)
            temp_dir.rmdir()
    
    @pytest.mark.asyncio
    async def test_quality_based_ranking(self, recommendation_engine):
        """Test that recommendations prioritize high-quality images."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create images with clear quality differences
            images_info = [
                {'name': 'low_quality.jpg', 'size': (200, 150), 'quality': 30, 'color': 'black'},
                {'name': 'high_quality.jpg', 'size': (1200, 800), 'quality': 95, 'color': 'white'},
                {'name': 'medium_quality.jpg', 'size': (600, 400), 'quality': 75, 'color': 'gray'},
            ]
            
            image_data_list = []
            for i, info in enumerate(images_info):
                image = Image.new('RGB', info['size'], color=info['color'])
                path = temp_dir / info['name']
                image.save(path, 'JPEG', quality=info['quality'])
                
                with open(path, 'rb') as f:
                    content = f.read()
                
                image_data = ImageData(
                    id=f"img_{i}",
                    filename=info['name'],
                    content_type="image/jpeg",
                    content=content,
                    size=len(content),
                    width=info['size'][0],
                    height=info['size'][1]
                )
                image_data_list.append(image_data)
            
            # Run recommendation
            results = await recommendation_engine.recommend_order(image_data_list)
            recommendations = results["recommendations"]
            
            # High quality image should be ranked first (hero)
            hero_recommendation = recommendations[0]
            assert hero_recommendation["is_hero"] is True
            
            # Find which image is the hero
            hero_image = next(img for img in image_data_list 
                            if img.id == hero_recommendation["image_id"])
            
            # Should be the high quality image (largest size, best quality)
            assert hero_image.filename == 'high_quality.jpg'
            
            # Scores should be in descending order
            scores = [rec["score"] for rec in recommendations]
            assert scores == sorted(scores, reverse=True)
            
        finally:
            # Cleanup
            for info in images_info:
                path = temp_dir / info['name']
                path.unlink(missing_ok=True)
            temp_dir.rmdir()
    
    @pytest.mark.asyncio
    async def test_single_image_recommendation(self, recommendation_engine):
        """Test recommendation with single image."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create single image
            image = Image.new('RGB', (400, 300), color='red')
            image_path = temp_dir / 'single.jpg'
            image.save(image_path, 'JPEG', quality=85)
            
            with open(image_path, 'rb') as f:
                content = f.read()
            
            image_data = ImageData(
                id="single_img",
                filename="single.jpg",
                content_type="image/jpeg",
                content=content,
                size=len(content),
                width=400,
                height=300
            )
            
            # Run recommendation
            results = await recommendation_engine.recommend_order([image_data])
            
            # Should handle single image correctly
            assert len(results["recommendations"]) == 1
            assert len(results["duplicates"]) == 0
            
            recommendation = results["recommendations"][0]
            assert recommendation["position"] == 1
            assert recommendation["is_hero"] is True
            assert recommendation["image_id"] == "single_img"
            assert results["hero_image"] == "single_img"
            
        finally:
            # Cleanup
            image_path.unlink(missing_ok=True)
            temp_dir.rmdir()
    
    @pytest.mark.asyncio
    async def test_performance_with_multiple_images(self, recommendation_engine):
        """Test performance with larger image set."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create 8 images with varied characteristics
            image_data_list = []
            colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'cyan']
            sizes = [(200, 150), (400, 300), (600, 450), (800, 600)] * 2
            
            for i in range(8):
                image = Image.new('RGB', sizes[i], color=colors[i])
                path = temp_dir / f'image_{i}.jpg'
                image.save(path, 'JPEG', quality=85)
                
                with open(path, 'rb') as f:
                    content = f.read()
                
                image_data = ImageData(
                    id=f"img_{i}",
                    filename=f"image_{i}.jpg",
                    content_type="image/jpeg",
                    content=content,
                    size=len(content),
                    width=sizes[i][0],
                    height=sizes[i][1]
                )
                image_data_list.append(image_data)
            
            # Run recommendation and check performance
            results = await recommendation_engine.recommend_order(image_data_list)
            
            # Should complete in reasonable time (< 10 seconds)
            total_time = results["processing_stats"]["total_time_ms"]
            assert total_time < 10000, f"Processing took too long: {total_time}ms"
            
            # Should have all recommendations
            assert len(results["recommendations"]) == 8
            
            # Should have proper ordering
            recommendations = results["recommendations"]
            positions = [rec["position"] for rec in recommendations]
            assert positions == list(range(1, 9))
            
        finally:
            # Cleanup
            for i in range(8):
                path = temp_dir / f'image_{i}.jpg'
                path.unlink(missing_ok=True)
            temp_dir.rmdir()