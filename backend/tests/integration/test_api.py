"""
Integration tests for the FastAPI application.
"""

import pytest
import asyncio
from httpx import AsyncClient
from pathlib import Path
import tempfile
from PIL import Image
import json

from app.main import app
from core.session_manager import session_manager


class TestUploadEndpoint:
    """Integration tests for upload endpoint."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def test_image_file(self):
        """Create test image file."""
        image = Image.new('RGB', (200, 200), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG')
        yield temp_file.name
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = {"status", "version", "model_loaded", "active_sessions", "uptime_seconds"}
        assert set(data.keys()).issuperset(required_fields)
        assert data["status"] == "healthy"
        assert data["version"] == "0.3.0"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "PDP Carousel Optimizer"
        assert data["version"] == "0.3.0"
        assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_upload_single_image(self, client, test_image_file):
        """Test uploading a single image."""
        with open(test_image_file, 'rb') as f:
            files = {"files": ("test.jpg", f, "image/jpeg")}
            response = await client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert len(data["images"]) == 1
        assert data["total_count"] == 1
        assert data["success_count"] == 1
        assert len(data["errors"]) == 0
        
        # Check image info
        image_info = data["images"][0]
        assert "id" in image_info
        assert image_info["filename"] == "test.jpg"
        assert image_info["content_type"] == "image/jpeg"
        assert image_info["size"] > 0
    
    @pytest.mark.asyncio
    async def test_upload_multiple_images(self, client):
        """Test uploading multiple images."""
        # Create multiple test images
        test_files = []
        for i in range(3):
            image = Image.new('RGB', (200, 200), color=['red', 'green', 'blue'][i])
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            image.save(temp_file.name, 'JPEG')
            test_files.append(temp_file.name)
        
        try:
            files = []
            for i, file_path in enumerate(test_files):
                with open(file_path, 'rb') as f:
                    files.append(("files", (f"test{i}.jpg", f.read(), "image/jpeg")))
            
            response = await client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["images"]) == 3
            assert data["total_count"] == 3
            assert data["success_count"] == 3
            assert len(data["errors"]) == 0
            
        finally:
            # Cleanup
            for file_path in test_files:
                Path(file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_upload_no_files(self, client):
        """Test upload with no files."""
        response = await client.post("/api/upload", files={})
        
        assert response.status_code == 400
        assert "No files provided" in response.json()["error"]
    
    @pytest.mark.asyncio
    async def test_upload_too_many_files(self, client):
        """Test upload with too many files."""
        # Create 13 files (exceeding limit of 12)
        files = []
        for i in range(13):
            files.append(("files", (f"test{i}.jpg", b"fake_image_content", "image/jpeg")))
        
        response = await client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "Maximum 12 files allowed" in response.json()["error"]
    
    @pytest.mark.asyncio 
    async def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        files = {"files": ("test.txt", "not an image", "text/plain")}
        response = await client.post("/api/upload", files=files)
        
        assert response.status_code == 200  # Upload endpoint doesn't fail completely
        data = response.json()
        
        # Should have errors for invalid file
        assert data["success_count"] == 0
        assert len(data["errors"]) > 0
        assert "test.txt" in str(data["errors"])


class TestAnalysisEndpoint:
    """Integration tests for analysis endpoint."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    async def uploaded_session(self, client):
        """Create session with uploaded images."""
        # Create test images
        test_files = []
        for i in range(3):
            image = Image.new('RGB', (300, 200), color=['red', 'green', 'blue'][i])
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            image.save(temp_file.name, 'JPEG')
            test_files.append(temp_file.name)
        
        try:
            # Upload images
            files = []
            for i, file_path in enumerate(test_files):
                with open(file_path, 'rb') as f:
                    files.append(("files", (f"test{i}.jpg", f.read(), "image/jpeg")))
            
            response = await client.post("/api/upload", files=files)
            assert response.status_code == 200
            
            session_id = response.json()["session_id"]
            yield session_id
            
        finally:
            # Cleanup files
            for file_path in test_files:
                Path(file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_analyze_images(self, client, uploaded_session):
        """Test image analysis endpoint."""
        request_data = {"session_id": uploaded_session}
        response = await client.post("/api/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        required_fields = {
            "session_id", "images", "duplicates", "recommended_order", 
            "processing_time_ms", "hero_image"
        }
        assert set(data.keys()) == required_fields
        
        assert data["session_id"] == uploaded_session
        assert len(data["images"]) == 3
        assert isinstance(data["duplicates"], list)
        assert len(data["recommended_order"]) == 3
        assert data["processing_time_ms"] > 0
        
        # Check image analysis structure
        for image_result in data["images"]:
            required_image_fields = {"id", "filename", "quality_metrics"}
            assert set(image_result.keys()) == required_image_fields
            
            metrics = image_result["quality_metrics"]
            required_metrics_fields = {
                "blur_score", "brightness", "contrast", "resolution",
                "composite_score", "flags", "suggestions"
            }
            assert set(metrics.keys()) == required_metrics_fields
            assert 0 <= metrics["composite_score"] <= 100
        
        # Check recommendation structure
        for i, rec in enumerate(data["recommended_order"]):
            required_rec_fields = {"position", "image_id", "score", "reason", "is_hero"}
            assert set(rec.keys()) == required_rec_fields
            assert rec["position"] == i + 1
            assert isinstance(rec["reason"], str)
            assert len(rec["reason"]) > 0
        
        # First recommendation should be hero
        assert data["recommended_order"][0]["is_hero"] is True
        assert data["hero_image"] == data["recommended_order"][0]["image_id"]
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_session(self, client):
        """Test analysis with nonexistent session."""
        request_data = {"session_id": "nonexistent-session"}
        response = await client.post("/api/analyze", json=request_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()
    
    @pytest.mark.asyncio
    async def test_analyze_custom_threshold(self, client, uploaded_session):
        """Test analysis with custom duplicate threshold."""
        request_data = {
            "session_id": uploaded_session,
            "duplicate_threshold": 0.8
        }
        response = await client.post("/api/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should complete successfully with custom threshold
        assert data["session_id"] == uploaded_session
        assert len(data["recommended_order"]) == 3
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_threshold(self, client, uploaded_session):
        """Test analysis with invalid threshold values."""
        # Test threshold too low
        request_data = {
            "session_id": uploaded_session,
            "duplicate_threshold": 0.3
        }
        response = await client.post("/api/analyze", json=request_data)
        assert response.status_code == 422  # Validation error
        
        # Test threshold too high
        request_data = {
            "session_id": uploaded_session,
            "duplicate_threshold": 1.5
        }
        response = await client.post("/api/analyze", json=request_data)
        assert response.status_code == 422  # Validation error


class TestSessionEndpoints:
    """Integration tests for session-related endpoints."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_get_session_info(self, client):
        """Test getting session information."""
        # First create a session
        image = Image.new('RGB', (200, 200), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG')
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {"files": ("test.jpg", f, "image/jpeg")}
                upload_response = await client.post("/api/upload", files=files)
            
            session_id = upload_response.json()["session_id"]
            
            # Get session info
            response = await client.get(f"/api/session/{session_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            required_fields = {"session_id", "created_at", "file_count", "expires_at"}
            assert set(data.keys()) == required_fields
            assert data["session_id"] == session_id
            assert data["file_count"] == 1
            
        finally:
            Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session_info(self, client):
        """Test getting info for nonexistent session."""
        response = await client.get("/api/session/nonexistent-session")
        
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()