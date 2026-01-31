"""
Pydantic schemas for API request/response validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class UploadedFileInfo(BaseModel):
    """Information about an uploaded file."""
    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME content type")


class UploadResponse(BaseModel):
    """Response for file upload endpoint."""
    session_id: str = Field(..., description="Session identifier")
    images: List[UploadedFileInfo] = Field(..., description="Successfully uploaded images")
    errors: List[str] = Field(default_factory=list, description="Upload errors")
    total_count: int = Field(..., description="Total number of files processed")
    success_count: int = Field(..., description="Number of successful uploads")


class AnalysisRequest(BaseModel):
    """Request for image analysis."""
    session_id: str = Field(..., description="Session identifier for uploaded images")
    duplicate_threshold: Optional[float] = Field(
        default=0.92, 
        ge=0.5, 
        le=1.0,
        description="Similarity threshold for duplicate detection (0.5-1.0)"
    )


class QualityMetricsResponse(BaseModel):
    """Quality metrics for an image."""
    blur_score: float = Field(..., description="Blur detection score (higher is better)")
    brightness: float = Field(..., description="Average brightness (0-255)")
    contrast: float = Field(..., description="Contrast score (higher is better)")
    resolution: tuple[int, int] = Field(..., description="Image dimensions (width, height)")
    composite_score: float = Field(..., description="Overall quality score (0-100)")
    flags: List[str] = Field(..., description="Quality warning flags")
    suggestions: List[str] = Field(..., description="Improvement suggestions")
    
    # Additional detailed metrics
    megapixels: float = Field(..., description="Image size in megapixels")
    aspect_ratio: float = Field(..., description="Width to height ratio")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Image format (JPEG, PNG, etc)")
    quality_grade: str = Field(..., description="Quality grade: EXCEPTIONAL, PROFESSIONAL, GOOD, ACCEPTABLE, or POOR")


class ImageAnalysisResult(BaseModel):
    """Analysis result for a single image."""
    id: str = Field(..., description="Image identifier")
    filename: str = Field(..., description="Original filename")
    image_url: str = Field(..., description="URL to access the image")
    quality_metrics: QualityMetricsResponse = Field(..., description="Quality analysis results")


class DuplicatePair(BaseModel):
    """Information about duplicate image pair."""
    image_a: str = Field(..., description="First image ID")
    image_b: str = Field(..., description="Second image ID")
    similarity: float = Field(..., description="Similarity score (0-1)")


class RecommendationItem(BaseModel):
    """Single carousel recommendation item."""
    position: int = Field(..., description="Recommended position in carousel (1-based)")
    image_id: str = Field(..., description="Image identifier")
    score: float = Field(..., description="Recommendation score")
    reason: str = Field(..., description="Explanation for recommendation")
    is_hero: bool = Field(default=False, description="Whether this is the hero image")


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    session_id: str = Field(..., description="Session identifier")
    images: List[ImageAnalysisResult] = Field(..., description="Per-image analysis results")
    duplicates: List[DuplicatePair] = Field(..., description="Detected duplicate pairs")
    recommended_order: List[RecommendationItem] = Field(..., description="Recommended carousel order")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    hero_image: Optional[str] = Field(None, description="ID of the hero image")
    
    @validator('processing_time_ms')
    def validate_processing_time(cls, v):
        if v < 0:
            raise ValueError('Processing time cannot be negative')
        return v


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    model_loaded: bool = Field(..., description="Whether CLIP model is loaded")
    active_sessions: int = Field(..., description="Number of active sessions")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    memory_usage_mb: Optional[float] = Field(None, description="Current memory usage in MB")


class ErrorResponse(BaseModel):
    """Error response format."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    error_code: Optional[str] = Field(None, description="Error code for client handling")


class SessionInfoResponse(BaseModel):
    """Session information response."""
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation time")
    file_count: int = Field(..., description="Number of files in session")
    expires_at: datetime = Field(..., description="Session expiration time")