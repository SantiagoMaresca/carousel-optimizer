"""
Storage service abstraction supporting local filesystem and S3-compatible storage.

Supports both local development (filesystem) and production (S3/R2) seamlessly.
"""

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError

from core.logger import get_api_logger

logger = get_api_logger()


class StorageService:
    """
    File storage abstraction that supports both local filesystem and S3-compatible storage.
    
    Configured via environment variables:
    - USE_S3: Set to 'true' to use S3/R2, 'false' for local filesystem
    - S3_ENDPOINT_URL: S3-compatible endpoint (e.g., Cloudflare R2)
    - S3_ACCESS_KEY: Access key ID
    - S3_SECRET_KEY: Secret access key
    - S3_BUCKET_NAME: Bucket name
    - S3_REGION: Region (default: 'auto' for R2)
    - UPLOAD_DIRECTORY: Local path when not using S3
    """
    
    def __init__(self):
        self.use_s3 = os.getenv('USE_S3', 'false').lower() == 'true'
        
        if self.use_s3:
            self._init_s3_client()
            logger.info("Storage initialized with S3/R2", 
                       bucket=self.bucket,
                       endpoint=os.getenv('S3_ENDPOINT_URL', 'N/A'))
        else:
            self.upload_dir = Path(os.getenv('UPLOAD_DIRECTORY', 'uploads'))
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Storage initialized with local filesystem", 
                       path=str(self.upload_dir))
    
    def _init_s3_client(self):
        """Initialize S3/R2 client."""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv('S3_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
                region_name=os.getenv('S3_REGION', 'auto')
            )
            self.bucket = os.getenv('S3_BUCKET_NAME', 'uploads')
            
            # Verify bucket exists (optional - will fail if bucket doesn't exist)
            try:
                self.s3_client.head_bucket(Bucket=self.bucket)
                logger.info("S3 bucket verified", bucket=self.bucket)
            except ClientError as e:
                logger.warning("Could not verify S3 bucket", 
                             bucket=self.bucket, 
                             error=str(e))
                
        except Exception as e:
            logger.error("Failed to initialize S3 client", error=str(e))
            raise
    
    async def save_file(self, session_id: str, filename: str, content: bytes) -> str:
        """
        Save file to storage.
        
        Args:
            session_id: Session identifier
            filename: Name of the file
            content: File content as bytes
            
        Returns:
            Full path or S3 key of saved file
        """
        if self.use_s3:
            return await self._save_to_s3(session_id, filename, content)
        else:
            return await self._save_to_local(session_id, filename, content)
    
    async def _save_to_s3(self, session_id: str, filename: str, content: bytes) -> str:
        """Save file to S3/R2."""
        key = f"{session_id}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=self._get_content_type(filename)
            )
            logger.debug("File saved to S3", key=key, size=len(content))
            return key
            
        except ClientError as e:
            logger.error("Failed to save file to S3", 
                        key=key, 
                        error=str(e))
            raise
    
    async def _save_to_local(self, session_id: str, filename: str, content: bytes) -> str:
        """Save file to local filesystem."""
        session_dir = self.upload_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = session_dir / filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.debug("File saved locally", path=str(file_path), size=len(content))
            return str(file_path)
            
        except Exception as e:
            logger.error("Failed to save file locally", 
                        path=str(file_path), 
                        error=str(e))
            raise
    
    async def read_file(self, session_id: str, filename: str) -> bytes:
        """
        Read file from storage.
        
        Args:
            session_id: Session identifier
            filename: Name of the file
            
        Returns:
            File content as bytes
        """
        if self.use_s3:
            return await self._read_from_s3(session_id, filename)
        else:
            return await self._read_from_local(session_id, filename)
    
    async def _read_from_s3(self, session_id: str, filename: str) -> bytes:
        """Read file from S3/R2."""
        key = f"{session_id}/{filename}"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read()
            logger.debug("File read from S3", key=key, size=len(content))
            return content
            
        except ClientError as e:
            logger.error("Failed to read file from S3", 
                        key=key, 
                        error=str(e))
            raise
    
    async def _read_from_local(self, session_id: str, filename: str) -> bytes:
        """Read file from local filesystem."""
        file_path = self.upload_dir / session_id / filename
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            logger.debug("File read locally", path=str(file_path), size=len(content))
            return content
            
        except Exception as e:
            logger.error("Failed to read file locally", 
                        path=str(file_path), 
                        error=str(e))
            raise
    
    async def get_file_path(self, session_id: str, filename: str) -> str:
        """
        Get file path/key.
        
        For local storage: returns absolute path
        For S3: returns S3 key
        
        Args:
            session_id: Session identifier
            filename: Name of the file
            
        Returns:
            File path or S3 key
        """
        if self.use_s3:
            return f"{session_id}/{filename}"
        else:
            return str(self.upload_dir / session_id / filename)
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete all files for a session.
        
        Args:
            session_id: Session identifier
        """
        if self.use_s3:
            await self._delete_session_from_s3(session_id)
        else:
            await self._delete_session_from_local(session_id)
    
    async def _delete_session_from_s3(self, session_id: str) -> None:
        """Delete all files for a session from S3/R2."""
        try:
            # List all objects with session prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{session_id}/"
            )
            
            if 'Contents' not in response:
                logger.debug("No files to delete in S3", session_id=session_id)
                return
            
            # Delete all objects
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            
            if objects:
                self.s3_client.delete_objects(
                    Bucket=self.bucket,
                    Delete={'Objects': objects}
                )
                logger.info("Session files deleted from S3", 
                           session_id=session_id, 
                           count=len(objects))
                
        except ClientError as e:
            logger.error("Failed to delete session from S3", 
                        session_id=session_id, 
                        error=str(e))
            raise
    
    async def _delete_session_from_local(self, session_id: str) -> None:
        """Delete all files for a session from local filesystem."""
        session_dir = self.upload_dir / session_id
        
        try:
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info("Session directory deleted", 
                           session_id=session_id,
                           path=str(session_dir))
            else:
                logger.debug("Session directory does not exist", 
                            session_id=session_id)
                
        except Exception as e:
            logger.error("Failed to delete session directory", 
                        session_id=session_id, 
                        error=str(e))
            raise
    
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session has any files.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session has files, False otherwise
        """
        if self.use_s3:
            return await self._session_exists_in_s3(session_id)
        else:
            return await self._session_exists_locally(session_id)
    
    async def _session_exists_in_s3(self, session_id: str) -> bool:
        """Check if session exists in S3/R2."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{session_id}/",
                MaxKeys=1
            )
            return 'Contents' in response and len(response['Contents']) > 0
            
        except ClientError as e:
            logger.error("Failed to check session in S3", 
                        session_id=session_id, 
                        error=str(e))
            return False
    
    async def _session_exists_locally(self, session_id: str) -> bool:
        """Check if session exists locally."""
        session_dir = self.upload_dir / session_id
        return session_dir.exists() and any(session_dir.iterdir())
    
    async def list_sessions(self) -> list[str]:
        """
        List all session IDs in storage.
        
        Returns:
            List of session IDs
        """
        if self.use_s3:
            return await self._list_sessions_from_s3()
        else:
            return await self._list_sessions_from_local()
    
    async def _list_sessions_from_s3(self) -> list[str]:
        """List all sessions from S3/R2."""
        try:
            sessions = set()
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            # List all objects and extract unique session IDs (prefixes)
            for page in paginator.paginate(Bucket=self.bucket, Delimiter='/'):
                if 'CommonPrefixes' in page:
                    for prefix in page['CommonPrefixes']:
                        # Remove trailing slash to get session ID
                        session_id = prefix['Prefix'].rstrip('/')
                        sessions.add(session_id)
            
            return list(sessions)
            
        except ClientError as e:
            logger.error("Failed to list sessions from S3", error=str(e))
            return []
    
    async def _list_sessions_from_local(self) -> list[str]:
        """List all sessions from local filesystem."""
        try:
            if not self.upload_dir.exists():
                return []
            
            sessions = []
            for session_dir in self.upload_dir.iterdir():
                if session_dir.is_dir():
                    sessions.append(session_dir.name)
            
            return sessions
            
        except Exception as e:
            logger.error("Failed to list sessions from local", error=str(e))
            return []
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension."""
        extension = Path(filename).suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.json': 'application/json',
        }
        return content_types.get(extension, 'application/octet-stream')


# Global storage service instance
storage_service = StorageService()
