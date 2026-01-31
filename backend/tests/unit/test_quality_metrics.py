"""
Unit tests for quality metrics module.
"""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import tempfile

from modules.quality_metrics import QualityAnalyzer, QualityMetrics


class TestQualityMetrics:
    """Test QualityMetrics class."""
    
    def test_quality_metrics_creation(self):
        """Test QualityMetrics object creation and score calculation."""
        metrics = QualityMetrics(
            blur_score=500.0,
            brightness=128.0,
            contrast=45.0,
            resolution=(1920, 1080)
        )
        
        assert metrics.blur_score == 500.0
        assert metrics.brightness == 128.0
        assert metrics.contrast == 45.0
        assert metrics.resolution == (1920, 1080)
        assert 0 <= metrics.composite_score <= 100
    
    def test_quality_flags_generation(self):
        """Test quality flag generation based on metrics."""
        # Good quality image
        good_metrics = QualityMetrics(1000.0, 128.0, 50.0, (1920, 1080))
        assert len(good_metrics.flags) == 0
        
        # Poor quality image
        poor_metrics = QualityMetrics(50.0, 30.0, 10.0, (400, 300))
        expected_flags = {"blurry", "too_dark", "low_contrast", "low_resolution"}
        assert set(poor_metrics.flags) == expected_flags
    
    def test_suggestions_generation(self):
        """Test improvement suggestions generation."""
        poor_metrics = QualityMetrics(50.0, 30.0, 10.0, (400, 300))
        
        assert "Improve image sharpness and focus" in poor_metrics.suggestions
        assert "Increase lighting or exposure" in poor_metrics.suggestions
        assert "Enhance contrast for better clarity" in poor_metrics.suggestions
        assert "Upload higher resolution image" in poor_metrics.suggestions
    
    def test_to_dict_serialization(self):
        """Test dictionary serialization."""
        metrics = QualityMetrics(500.0, 128.0, 45.0, (1920, 1080))
        result = metrics.to_dict()
        
        required_keys = {
            "blur_score", "brightness", "contrast", "resolution",
            "composite_score", "flags", "suggestions"
        }
        assert set(result.keys()) == required_keys
        assert isinstance(result["resolution"], tuple)
        assert isinstance(result["flags"], list)
        assert isinstance(result["suggestions"], list)


class TestQualityAnalyzer:
    """Test QualityAnalyzer functionality."""
    
    @pytest.fixture
    def test_image(self):
        """Create a test image for analysis."""
        # Create a test image with some patterns
        image = Image.new('RGB', (400, 300), color='white')
        # Add some patterns to make it more realistic
        pixels = image.load()
        for i in range(100, 300):
            for j in range(100, 200):
                pixels[i, j] = (i % 255, j % 255, (i + j) % 255)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG', quality=85)
        yield Path(temp_file.name)
        Path(temp_file.name).unlink(missing_ok=True)
    
    def test_blur_detection(self, test_image):
        """Test blur detection functionality."""
        import cv2
        image_array = cv2.imread(str(test_image))
        blur_score = QualityAnalyzer.detect_blur(image_array)
        
        assert isinstance(blur_score, float)
        assert blur_score >= 0
    
    def test_brightness_calculation(self, test_image):
        """Test brightness calculation."""
        import cv2
        image_array = cv2.imread(str(test_image))
        brightness = QualityAnalyzer.calculate_brightness(image_array)
        
        assert isinstance(brightness, float)
        assert 0 <= brightness <= 255
    
    def test_contrast_calculation(self, test_image):
        """Test contrast calculation."""
        import cv2
        image_array = cv2.imread(str(test_image))
        contrast = QualityAnalyzer.calculate_contrast(image_array)
        
        assert isinstance(contrast, float)
        assert contrast >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_image_quality(self, test_image):
        """Test complete image quality analysis."""
        metrics = await QualityAnalyzer.analyze_image_quality(test_image)
        
        assert isinstance(metrics, QualityMetrics)
        assert metrics.blur_score >= 0
        assert 0 <= metrics.brightness <= 255
        assert metrics.contrast >= 0
        assert metrics.resolution == (400, 300)
        assert 0 <= metrics.composite_score <= 100
    
    @pytest.mark.asyncio
    async def test_analyze_images_parallel(self, sample_images):
        """Test parallel analysis of multiple images."""
        results = await QualityAnalyzer.analyze_images_parallel(sample_images[:3])
        
        assert len(results) == 3
        assert all(isinstance(r, QualityMetrics) for r in results)
        assert all(0 <= r.composite_score <= 100 for r in results)
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_image(self):
        """Test handling of nonexistent image file."""
        fake_path = Path("nonexistent_image.jpg")
        metrics = await QualityAnalyzer.analyze_image_quality(fake_path)
        
        # Should return default metrics without crashing
        assert isinstance(metrics, QualityMetrics)
        assert metrics.composite_score == 0
        assert metrics.resolution == (0, 0)