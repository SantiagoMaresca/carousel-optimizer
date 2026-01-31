"""
Simple unit tests that work without heavy dependencies.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from PIL import Image
import numpy as np
import shutil

from core.session_manager import SessionManager


class TestSessionManager:
    """Tests for SessionManager without external dependencies."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a test session manager."""
        temp_dir = Path(tempfile.mkdtemp())
        manager = SessionManager(upload_dir=temp_dir)
        yield manager
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager):
        """Test session creation."""
        session_id = await session_manager.create_session()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID length
        assert session_id.count('-') == 4  # UUID format
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_manager):
        """Test getting session data."""
        # Create session
        session_id = await session_manager.create_session()
        
        # Get session
        session_data = await session_manager.get_session(session_id)
        
        assert session_data is not None
        assert session_data.session_id == session_id
        assert session_data.files == []
        assert session_data.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager):
        """Test getting nonexistent session returns None."""
        session_data = await session_manager.get_session("nonexistent")
        assert session_data is None
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, session_manager):
        """Test session cleanup."""
        # Create session
        session_id = await session_manager.create_session()
        
        # Verify it exists
        session_data = await session_manager.get_session(session_id)
        assert session_data is not None
        
        # Clean up session
        result = await session_manager.cleanup_session(session_id)
        assert result is True
        
        # Verify it's gone
        session_data = await session_manager.get_session(session_id)
        assert session_data is None


class TestImageHandling:
    """Basic image handling tests."""
    
    @pytest.fixture
    def test_image_path(self):
        """Create a test image file."""
        # Create a simple test image
        image = Image.new('RGB', (200, 150), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_file.close()  # Close file handle to avoid Windows lock
        image.save(temp_file.name, 'JPEG')
        
        yield Path(temp_file.name)
        
        # Cleanup with retry for Windows
        try:
            Path(temp_file.name).unlink()
        except PermissionError:
            import time
            time.sleep(0.1)
            try:
                Path(temp_file.name).unlink()
            except PermissionError:
                pass  # Skip if still locked
    
    def test_image_creation(self, test_image_path):
        """Test that we can create and read test images."""
        assert test_image_path.exists()
        assert test_image_path.suffix == '.jpg'
        
        # Verify we can load it
        with Image.open(test_image_path) as img:
            assert img.size == (200, 150)
            assert img.mode == 'RGB'
    
    def test_image_file_size(self, test_image_path):
        """Test image file properties."""
        stat = test_image_path.stat()
        assert stat.st_size > 0
        assert stat.st_size < 100000  # Should be reasonable size


class TestBasicConfiguration:
    """Test basic configuration and setup."""
    
    def test_config_import(self):
        """Test that we can import configuration."""
        from app.config import settings
        
        assert settings is not None
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'upload_directory')  # Correct attribute name
    
    def test_logger_import(self):
        """Test that we can import and use logger."""
        from core.logger import get_ai_logger
        
        logger = get_ai_logger()
        assert logger is not None
        
        # Test logging (should not raise exception)
        logger.info("Test log message", test_data="test_value")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])