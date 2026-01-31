"""
Test configuration and fixtures.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
import numpy as np
from PIL import Image
import tempfile
import shutil

from core.session_manager import SessionManager

# Try to import modules that might have dependency issues
try:
    from modules.embeddings import EmbeddingGenerator
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    # Mock EmbeddingGenerator for tests
    class EmbeddingGenerator:
        def __init__(self, *args, **kwargs):
            pass
        async def initialize(self):
            pass
        async def generate_embedding(self, image_path):
            return np.random.normal(0, 1, 512).astype(np.float32)

try:
    from modules.quality_metrics import QualityMetrics
    HAS_QUALITY_METRICS = True
except ImportError:
    HAS_QUALITY_METRICS = False
    # Mock QualityMetrics for tests
    class QualityMetrics:
        def __init__(self, blur_score=150.0, brightness=128.0, contrast=45.0, resolution=(800, 600)):
            self.blur_score = blur_score
            self.brightness = brightness
            self.contrast = contrast
            self.resolution = resolution
            self.composite_score = 80.0
            self.flags = []
            self.suggestions = []
        
        def to_dict(self):
            return {
                "blur_score": self.blur_score,
                "brightness": self.brightness,
                "contrast": self.contrast,
                "resolution": self.resolution,
                "composite_score": self.composite_score,
                "flags": self.flags,
                "suggestions": self.suggestions
            }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def session_manager_fixture(temp_upload_dir):
    """Create session manager with temporary directory."""
    sm = SessionManager(temp_upload_dir, ttl_hours=1)
    yield sm
    # Cleanup is handled by temp_upload_dir fixture
    # Note: Async cleanup would require different fixture handling


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple 200x200 RGB image
    image = Image.new('RGB', (200, 200), color='red')
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    image.save(temp_file.name, 'JPEG')
    yield Path(temp_file.name)
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def sample_images():
    """Create multiple sample test images."""
    images = []
    colors = ['red', 'green', 'blue', 'yellow', 'purple']
    
    for i, color in enumerate(colors):
        image = Image.new('RGB', (200, 200), color=color)
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG')
        images.append(Path(temp_file.name))
    
    yield images
    
    # Cleanup
    for image_path in images:
        image_path.unlink(missing_ok=True)


@pytest.fixture
def mock_quality_metrics():
    """Create mock quality metrics."""
    return QualityMetrics(
        blur_score=500.0,
        brightness=128.0,
        contrast=45.0,
        resolution=(200, 200)
    )


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing."""
    return [
        np.random.rand(512).astype(np.float32),
        np.random.rand(512).astype(np.float32),
        np.random.rand(512).astype(np.float32)
    ]


@pytest.fixture
async def mock_embedding_generator():
    """Create mock embedding generator."""
    generator = AsyncMock(spec=EmbeddingGenerator)
    generator.initialize = AsyncMock()
    generator.generate_embedding = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
    generator.generate_embeddings_batch = AsyncMock(return_value=[
        np.random.rand(512).astype(np.float32) for _ in range(3)
    ])
    return generator