"""
Security utilities for file validation and sanitization.
"""

# import magic  # Temporarily disabled due to libmagic dependency issue
from pathlib import Path
from typing import Set, Tuple, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

from core.logger import get_security_logger
from app.config import settings


logger = get_security_logger()


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class SecureFileValidator:
    """Comprehensive file validation for security."""
    
    ALLOWED_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_MIMETYPES: Set[str] = {'image/jpeg', 'image/png', 'image/webp'}
    MAX_DIMENSIONS: Tuple[int, int] = (4096, 4096)
    
    # Magic bytes for image formats
    MAGIC_BYTES = {
        b'\xFF\xD8\xFF': 'jpeg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'RIFF': 'webp'  # WebP files start with RIFF
    }
    
    @classmethod
    async def validate_file(cls, file: UploadFile) -> bool:
        """
        Comprehensive file validation.
        
        Args:
            file: The uploaded file to validate
            
        Returns:
            True if file is valid
            
        Raises:
            SecurityError: If file fails validation
        """
        logger.info("Validating file", filename=file.filename, content_type=file.content_type)
        
        try:
            # 1. Check filename and extension
            if not file.filename:
                raise SecurityError("Filename is required")
            
            file_path = Path(file.filename)
            extension = file_path.suffix.lower()
            
            if extension not in cls.ALLOWED_EXTENSIONS:
                raise SecurityError(f"Invalid file extension: {extension}")
            
            # 2. Check content type
            if file.content_type not in cls.ALLOWED_MIMETYPES:
                raise SecurityError(f"Invalid content type: {file.content_type}")
            
            # 3. Read file content for validation
            content = await file.read()
            file_size = len(content)
            
            # Reset file pointer
            await file.seek(0)
            
            # 4. Check file size
            if file_size > settings.max_file_size:
                raise SecurityError(f"File too large: {file_size} bytes (max: {settings.max_file_size})")
            
            if file_size < 100:  # Minimum reasonable image size
                raise SecurityError("File too small to be a valid image")
            
            # 5. Validate magic bytes
            if not cls._validate_magic_bytes(content):
                raise SecurityError("Invalid file format (magic bytes check failed)")
            
            # 6. Validate image can be opened and check dimensions
            try:
                image = Image.open(io.BytesIO(content))
                
                # Check image dimensions
                width, height = image.size
                if width > cls.MAX_DIMENSIONS[0] or height > cls.MAX_DIMENSIONS[1]:
                    raise SecurityError(f"Image dimensions too large: {width}x{height}")
                
                if width < 100 or height < 100:  # Minimum reasonable dimensions
                    raise SecurityError(f"Image dimensions too small: {width}x{height}")
                
                # Verify image format matches extension
                image_format = image.format.lower() if image.format else None
                expected_formats = {
                    '.jpg': 'jpeg', '.jpeg': 'jpeg',
                    '.png': 'png',
                    '.webp': 'webp'
                }
                
                if image_format != expected_formats.get(extension):
                    raise SecurityError(f"Image format mismatch: expected {expected_formats.get(extension)}, got {image_format}")
                
                logger.info("File validation passed", 
                           filename=file.filename,
                           size=file_size,
                           dimensions=f"{width}x{height}",
                           format=image_format)
                
                return True
                
            except Exception as e:
                if isinstance(e, SecurityError):
                    raise
                raise SecurityError(f"Invalid image file: {str(e)}")
            
        except SecurityError:
            logger.warning("File validation failed", filename=file.filename, error=str(e))
            raise
        except Exception as e:
            logger.error("File validation error", filename=file.filename, error=str(e))
            raise SecurityError(f"Validation failed: {str(e)}")
    
    @classmethod
    def _validate_magic_bytes(cls, content: bytes) -> bool:
        """Validate file format using magic bytes."""
        if not content:
            return False
        
        # Check for JPEG
        if content.startswith(b'\xFF\xD8\xFF'):
            return True
        
        # Check for PNG
        if content.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
            return True
        
        # Check for WebP
        if content.startswith(b'RIFF') and b'WEBP' in content[:12]:
            return True
        
        return False
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage."""
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = Path(filename).name
        
        # Remove dangerous characters
        dangerous_chars = '<>:"/\\|?*\x00'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250 - len(ext)] + ('.' + ext if ext else '')
        
        return filename


async def validate_upload_file(file: UploadFile) -> UploadFile:
    """
    Validate an uploaded file and return it if valid.
    
    Args:
        file: The uploaded file to validate
        
    Returns:
        The validated file
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        await SecureFileValidator.validate_file(file)
        return file
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_safe_filename(filename: str) -> str:
    """Get a sanitized filename for safe storage."""
    return SecureFileValidator.sanitize_filename(filename)