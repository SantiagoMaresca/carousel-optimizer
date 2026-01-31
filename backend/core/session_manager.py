"""
Session management for handling user sessions and file uploads.
"""

import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4, UUID
import json

from core.logger import get_session_logger
from app.config import settings, UPLOAD_PATH
from core.storage import storage_service


logger = get_session_logger()


class SessionData:
    """Data structure for session information."""
    
    def __init__(self, session_id: str, created_at: datetime):
        self.session_id = session_id
        self.created_at = created_at
        self.files: List[str] = []
        self.metadata: Dict = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "files": self.files,
            "metadata": self.metadata
        }


class SessionManager:
    """Manages user sessions and file uploads with automatic cleanup."""
    
    def __init__(self, upload_dir: Path = UPLOAD_PATH, ttl_hours: int = None):
        self.upload_dir = upload_dir
        self.ttl_hours = ttl_hours or settings.session_ttl_hours
        self.sessions: Dict[str, SessionData] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("SessionManager initialized", 
                   upload_dir=str(upload_dir), 
                   ttl_hours=self.ttl_hours)
    
    async def create_session(self) -> str:
        """Create a new session with unique directory."""
        session_id = str(uuid4())
        session_path = self.upload_dir / session_id
        
        try:
            session_path.mkdir(parents=True, exist_ok=True)
            
            session_data = SessionData(session_id, datetime.utcnow())
            self.sessions[session_id] = session_data
            
            # Save session metadata
            metadata_file = session_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(session_data.to_dict(), f)
            
            logger.info("Session created", session_id=session_id)
            return session_id
            
        except Exception as e:
            logger.error("Failed to create session", session_id=session_id, error=str(e))
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID."""
        if session_id not in self.sessions:
            # Try to load from disk
            await self._load_session_from_disk(session_id)
        
        return self.sessions.get(session_id)
    
    async def add_file_to_session(self, session_id: str, filename: str, original_filename: str = None) -> None:
        """Add a file to session tracking with original filename mapping."""
        session = await self.get_session(session_id)
        if session:
            session.files.append(filename)
            # Store original filename mapping
            if original_filename:
                if 'filename_map' not in session.metadata:
                    session.metadata['filename_map'] = {}
                session.metadata['filename_map'][filename] = original_filename
                
                # Save updated metadata
                session_dir = self.upload_dir / session_id
                metadata_file = session_dir / "metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(session.to_dict(), f)
                    
            logger.debug("File added to session", session_id=session_id, filename=filename, original=original_filename)
    
    async def get_session_files(self, session_id: str) -> List[Path]:
        """
        Get all files for a session.
        
        For S3: Downloads files to temporary local directory for processing
        For local: Returns paths directly
        """
        session = await self.get_session(session_id)
        if not session:
            return []
        
        if storage_service.use_s3:
            # Download S3 files to temp directory for processing
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "carousel_temp" / session_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            file_paths = []
            for filename in session.files:
                temp_file = temp_dir / filename
                # Only download if not already exists
                if not temp_file.exists():
                    content = await storage_service.read_file(session_id, filename)
                    with open(temp_file, 'wb') as f:
                        f.write(content)
                file_paths.append(temp_file)
            
            return file_paths
        else:
            # Local filesystem - return paths directly
            session_dir = self.upload_dir / session_id
            return [session_dir / filename for filename in session.files if (session_dir / filename).exists()]
    
    async def get_original_filename(self, session_id: str, filename: str) -> str:
        """Get original filename from session metadata."""
        session = await self.get_session(session_id)
        if session and 'filename_map' in session.metadata:
            original = session.metadata['filename_map'].get(filename, filename)
            logger.debug(f"Filename mapping: {filename} -> {original}")
            return original
        logger.warning(f"No filename mapping found for {filename} in session {session_id}")
        return filename
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Clean up a specific session."""
        try:
            # Delete from storage service (handles both S3 and local)
            await storage_service.delete_session(session_id)
            
            # Clean up temp files if using S3
            if storage_service.use_s3:
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "carousel_temp" / session_id
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            logger.info("Session cleaned up", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("Failed to cleanup session", session_id=session_id, error=str(e))
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.ttl_hours)
        expired_sessions = []
        
        # Find expired sessions in memory
        for session_id, session_data in self.sessions.items():
            if session_data.created_at < cutoff_time:
                expired_sessions.append(session_id)
        
        # Find expired sessions on disk
        if self.upload_dir.exists():
            for session_dir in self.upload_dir.iterdir():
                if session_dir.is_dir():
                    metadata_file = session_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            created_at = datetime.fromisoformat(metadata['created_at'])
                            if created_at < cutoff_time:
                                expired_sessions.append(session_dir.name)
                        except Exception:
                            # If we can't read metadata, consider it expired
                            expired_sessions.append(session_dir.name)
        
        # Clean up expired sessions
        cleanup_count = 0
        for session_id in set(expired_sessions):  # Remove duplicates
            if await self.cleanup_session(session_id):
                cleanup_count += 1
        
        if cleanup_count > 0:
            logger.info("Cleaned up expired sessions", count=cleanup_count)
        
        return cleanup_count
    
    async def _load_session_from_disk(self, session_id: str) -> bool:
        """Load session data from disk."""
        try:
            session_dir = self.upload_dir / session_id
            metadata_file = session_dir / "metadata.json"
            
            if not metadata_file.exists():
                return False
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            session_data = SessionData(session_id, datetime.fromisoformat(metadata['created_at']))
            session_data.files = metadata.get('files', [])
            session_data.metadata = metadata.get('metadata', {})
            
            self.sessions[session_id] = session_data
            return True
            
        except Exception as e:
            logger.error("Failed to load session from disk", session_id=session_id, error=str(e))
            return False
    
    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                await self.cleanup_expired_sessions()
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
            raise


# Global session manager instance
session_manager = SessionManager()