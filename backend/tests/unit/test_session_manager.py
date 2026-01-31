"""
Unit tests for session management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from core.session_manager import SessionManager, SessionData


class TestSessionData:
    """Test SessionData functionality."""
    
    def test_session_data_creation(self):
        """Test SessionData object creation."""
        session_id = "test-session-123"
        created_at = datetime.utcnow()
        
        data = SessionData(session_id, created_at)
        
        assert data.session_id == session_id
        assert data.created_at == created_at
        assert data.files == []
        assert data.metadata == {}
    
    def test_session_data_serialization(self):
        """Test SessionData dictionary serialization."""
        session_id = "test-session-123"
        created_at = datetime.utcnow()
        
        data = SessionData(session_id, created_at)
        data.files = ["file1.jpg", "file2.png"]
        data.metadata = {"key": "value"}
        
        serialized = data.to_dict()
        
        assert serialized["session_id"] == session_id
        assert serialized["created_at"] == created_at.isoformat()
        assert serialized["files"] == ["file1.jpg", "file2.png"]
        assert serialized["metadata"] == {"key": "value"}


class TestSessionManager:
    """Test SessionManager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager_fixture):
        """Test session creation."""
        session_id = await session_manager_fixture.create_session()
        
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format
        assert session_id in session_manager_fixture.sessions
        
        # Check directory creation
        session_dir = session_manager_fixture.upload_dir / session_id
        assert session_dir.exists()
        assert session_dir.is_dir()
        
        # Check metadata file
        metadata_file = session_dir / "metadata.json"
        assert metadata_file.exists()
    
    @pytest.mark.asyncio
    async def test_get_session(self, session_manager_fixture):
        """Test session retrieval."""
        # Create session
        session_id = await session_manager_fixture.create_session()
        
        # Retrieve session
        session = await session_manager_fixture.get_session(session_id)
        
        assert session is not None
        assert session.session_id == session_id
        assert isinstance(session.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager_fixture):
        """Test retrieval of nonexistent session."""
        session = await session_manager_fixture.get_session("nonexistent")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_add_file_to_session(self, session_manager_fixture):
        """Test adding files to session."""
        session_id = await session_manager_fixture.create_session()
        
        await session_manager_fixture.add_file_to_session(session_id, "test.jpg")
        await session_manager_fixture.add_file_to_session(session_id, "test2.png")
        
        session = await session_manager_fixture.get_session(session_id)
        assert len(session.files) == 2
        assert "test.jpg" in session.files
        assert "test2.png" in session.files
    
    @pytest.mark.asyncio
    async def test_get_session_files(self, session_manager_fixture):
        """Test getting session files."""
        session_id = await session_manager_fixture.create_session()
        session_dir = session_manager_fixture.upload_dir / session_id
        
        # Create test files
        test_file1 = session_dir / "test1.jpg"
        test_file2 = session_dir / "test2.png"
        test_file1.write_text("test content 1")
        test_file2.write_text("test content 2")
        
        await session_manager_fixture.add_file_to_session(session_id, "test1.jpg")
        await session_manager_fixture.add_file_to_session(session_id, "test2.png")
        
        files = await session_manager_fixture.get_session_files(session_id)
        
        assert len(files) == 2
        assert all(isinstance(f, Path) for f in files)
        assert all(f.exists() for f in files)
    
    @pytest.mark.asyncio
    async def test_cleanup_session(self, session_manager_fixture):
        """Test session cleanup."""
        session_id = await session_manager_fixture.create_session()
        session_dir = session_manager_fixture.upload_dir / session_id
        
        # Create test file
        test_file = session_dir / "test.jpg"
        test_file.write_text("test content")
        
        # Cleanup session
        result = await session_manager_fixture.cleanup_session(session_id)
        
        assert result is True
        assert not session_dir.exists()
        assert session_id not in session_manager_fixture.sessions
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, temp_upload_dir):
        """Test cleanup of expired sessions."""
        # Create session manager with very short TTL
        sm = SessionManager(temp_upload_dir, ttl_hours=0.001)  # ~3.6 seconds
        
        # Create session
        session_id = await sm.create_session()
        
        # Wait for expiration
        await asyncio.sleep(0.1)  # Wait longer than TTL
        
        # Run cleanup
        cleaned_count = await sm.cleanup_expired_sessions()
        
        assert cleaned_count == 1
        assert session_id not in sm.sessions
        
        await sm.stop_cleanup_task()
    
    @pytest.mark.asyncio
    async def test_load_session_from_disk(self, session_manager_fixture):
        """Test loading session from disk metadata."""
        # Create session directory manually
        session_id = "manual-session-123"
        session_dir = session_manager_fixture.upload_dir / session_id
        session_dir.mkdir()
        
        # Create metadata file
        metadata = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "files": ["test.jpg"],
            "metadata": {"key": "value"}
        }
        
        metadata_file = session_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Try to get session (should load from disk)
        session = await session_manager_fixture.get_session(session_id)
        
        assert session is not None
        assert session.session_id == session_id
        assert session.files == ["test.jpg"]
        assert session.metadata == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_session_manager_startup_cleanup(self, temp_upload_dir):
        """Test that cleanup task can be started and stopped."""
        sm = SessionManager(temp_upload_dir)
        
        # Start cleanup task
        await sm.start_cleanup_task()
        assert sm._cleanup_task is not None
        assert not sm._cleanup_task.done()
        
        # Stop cleanup task
        await sm.stop_cleanup_task()
        assert sm._cleanup_task.done()