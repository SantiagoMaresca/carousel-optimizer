"""
Configuration management for the Carousel Optimizer application.
"""

import os
import json
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Upload Configuration
    max_file_size: int = 8 * 1024 * 1024  # 8MB
    max_files: int = 12
    upload_directory: str = "uploads"
    session_ttl_hours: int = 2
    
    # Redis (optional)
    redis_url: str = "redis://localhost:6379"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    cors_origins: Union[List[str], str] = ["http://localhost:3000", "http://localhost:3002", "http://localhost:5173"]
    
    # Rate Limiting
    rate_limit_uploads: str = "10/minute"
    rate_limit_analyze: str = "5/minute"
    
    # Additional settings
    node_env: str = "development"
    session_timeout_minutes: int = 30
    max_file_size_mb: int = 10
    max_files_per_session: int = 20
    mock_ai_data: bool = False
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                return json.loads(v)
            except json.JSONDecodeError:
                # If not JSON, split by comma
                return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields


# Global settings instance
settings = Settings()

# Derived paths
BASE_DIR = Path(__file__).parent.parent

# Handle upload directory - support both relative and absolute paths
if os.path.isabs(settings.upload_directory):
    UPLOAD_PATH = Path(settings.upload_directory)
else:
    UPLOAD_PATH = BASE_DIR / settings.upload_directory

# Ensure upload directory exists
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)