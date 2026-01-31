"""
FastAPI routes for the Carousel Optimizer API.
"""

import asyncio
import time
from typing import List
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import FileResponse

from app.api.schemas import (
    UploadResponse, UploadedFileInfo, AnalysisRequest, AnalysisResponse,
    HealthResponse, SessionInfoResponse, ImageAnalysisResult, QualityMetricsResponse,
    RecommendationItem, DuplicatePair
)
from app.api.dependencies import (
    SessionManagerDep, ClientIPDep, validate_session_exists,
    upload_rate_limit, analyze_rate_limit, limiter
)
from core.security import validate_upload_file, get_safe_filename
from core.logger import get_api_logger, log_request, log_response, log_error
from core.storage import storage_service
from core.session_manager import session_manager
from app.config import settings, UPLOAD_PATH
from modules.embeddings import embedding_generator
from modules.quality_metrics import QualityAnalyzer
from modules.similarity import SimilarityAnalyzer
from modules.recommendation_engine import recommendation_engine, ImageData


logger = get_api_logger()
router = APIRouter()

# Global state for uptime tracking
_start_time = time.time()


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service status.
    
    Returns service status, model availability, and performance metrics.
    """
    uptime = time.time() - _start_time
    memory_usage = get_memory_usage()
    
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        model_loaded=embedding_generator.model is not None,
        active_sessions=len(session_manager.sessions),
        uptime_seconds=uptime,
        memory_usage_mb=memory_usage if memory_usage > 0 else None
    )


@router.post("/api/upload", response_model=UploadResponse)
@limiter.limit(settings.rate_limit_uploads)
async def upload_images(
    request: Request,
    session_mgr: SessionManagerDep,
    client_ip: ClientIPDep,
    files: List[UploadFile] = File(...)
) -> UploadResponse:
    """
    Upload multiple images for carousel analysis.
    
    Args:
        files: List of image files (max 12, 8MB each)
        
    Returns:
        Upload response with session ID and file information
    """
    start_time = time.time()
    log_request(logger, "POST", "/api/upload", 
               file_count=len(files), client_ip=client_ip)
    
    try:
        # Validate file count
        if len(files) > settings.max_files:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {settings.max_files} files allowed, got {len(files)}"
            )
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Create new session
        session_id = await session_mgr.create_session()
        
        # Process files
        successful_uploads = []
        errors = []
        
        for file in files:
            try:
                # Validate file
                await validate_upload_file(file)
                
                # Generate unique filename
                file_id = str(uuid4())
                safe_filename = get_safe_filename(file.filename)
                file_extension = Path(safe_filename).suffix
                unique_filename = f"{file_id}{file_extension}"
                
                # Read file content
                content = await file.read()
                
                # Save file using storage service
                await storage_service.save_file(session_id, unique_filename, content)
                
                # Add to session with original filename mapping
                await session_mgr.add_file_to_session(session_id, unique_filename, safe_filename)
                
                successful_uploads.append(UploadedFileInfo(
                    id=file_id,
                    filename=safe_filename,
                    size=len(content),
                    content_type=file.content_type
                ))
                
                logger.debug("File uploaded successfully", 
                           session_id=session_id,
                           file_id=file_id,
                           filename=safe_filename)
                
            except HTTPException as e:
                error_msg = f"{file.filename}: {e.detail}"
                errors.append(error_msg)
                logger.warning("File upload failed", 
                             filename=file.filename, 
                             error=e.detail)
            except Exception as e:
                error_msg = f"{file.filename}: {str(e)}"
                errors.append(error_msg)
                logger.error("File upload error", 
                           filename=file.filename, 
                           error=str(e))
        
        response = UploadResponse(
            session_id=session_id,
            images=successful_uploads,
            errors=errors,
            total_count=len(files),
            success_count=len(successful_uploads)
        )
        
        duration = time.time() - start_time
        log_response(logger, "POST", "/api/upload", 200, duration,
                    session_id=session_id, 
                    success_count=len(successful_uploads),
                    error_count=len(errors))
        
        return response
        
    except HTTPException:
        duration = time.time() - start_time
        log_response(logger, "POST", "/api/upload", 400, duration)
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_error(logger, e, {"endpoint": "/api/upload", "client_ip": client_ip})
        log_response(logger, "POST", "/api/upload", 500, duration)
        raise HTTPException(status_code=500, detail="Upload processing failed")


@router.post("/api/analyze", response_model=AnalysisResponse)
@limiter.limit(settings.rate_limit_analyze)
async def analyze_images(
    request: Request,
    analysis_request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    session_mgr: SessionManagerDep,
    client_ip: ClientIPDep
) -> AnalysisResponse:
    """
    Analyze uploaded images and generate carousel recommendations.
    
    Args:
        analysis_request: Analysis configuration including session ID
        
    Returns:
        Complete analysis with quality metrics and recommendations
    """
    start_time = time.time()
    session_id = analysis_request.session_id
    
    log_request(logger, "POST", "/api/analyze", 
               session_id=session_id, client_ip=client_ip)
    
    try:
        # Validate session exists
        await validate_session_exists(session_id, session_mgr)
        
        # Get session files
        image_paths = await session_mgr.get_session_files(session_id)
        
        if not image_paths:
            raise HTTPException(
                status_code=400,
                detail=f"No images found in session {session_id}"
            )
        
        logger.info("Starting image analysis", 
                   session_id=session_id,
                   image_count=len(image_paths))
        
        # Step 1: Parallel quality analysis and embedding generation
        quality_task = asyncio.create_task(
            QualityAnalyzer.analyze_images_parallel(image_paths)
        )
        embedding_task = asyncio.create_task(
            embedding_generator.generate_embeddings_batch(image_paths)
        )
        
        quality_results = await quality_task
        embeddings = await embedding_task
        
        # Step 2: Create ImageData objects
        images = []
        for i, path in enumerate(image_paths):
            file_id = path.stem  # Use filename without extension as ID
            # Get original filename from session metadata
            original_filename = await session_mgr.get_original_filename(session_id, path.name)
            logger.debug(f"Image {i}: {path.name} -> {original_filename}")
            images.append(ImageData(
                id=file_id,
                filename=original_filename,
                path=path,
                quality_metrics=quality_results[i],
                embedding=embeddings[i]
            ))
        
        # Step 3: Generate recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            images, embeddings, analysis_request.duplicate_threshold
        )
        
        # Step 4: Format response with enhanced metrics
        image_results = []
        for img in images:
            metrics_dict = img.quality_metrics.to_dict()
            
            # Add file-specific information
            if img.path.exists():
                metrics_dict["file_size"] = img.path.stat().st_size
                metrics_dict["format"] = img.path.suffix.upper().replace(".", "")
            
            image_results.append(ImageAnalysisResult(
                id=img.id,
                filename=img.filename,
                image_url=f"/api/image/{session_id}/{img.id}",
                quality_metrics=QualityMetricsResponse(**metrics_dict)
            ))
        
        duplicate_pairs = [
            DuplicatePair(
                image_a=dup["image_a"],
                image_b=dup["image_b"], 
                similarity=dup["similarity"]
            )
            for dup in recommendations.similarity_result.duplicates
        ]
        
        recommendation_items = [
            RecommendationItem(
                position=rec.position,
                image_id=rec.image_id,
                score=rec.score,
                reason=rec.reason,
                is_hero=rec.is_hero
            )
            for rec in recommendations.recommendations
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        # Note: Session will be cleaned up automatically after TTL expires
        # (not immediately, so frontend can access images)
        
        response = AnalysisResponse(
            session_id=session_id,
            images=image_results,
            duplicates=duplicate_pairs,
            recommended_order=recommendation_items,
            processing_time_ms=processing_time,
            hero_image=recommendations.hero_image.image_id if recommendations.hero_image else None
        )
        
        log_response(logger, "POST", "/api/analyze", 200, time.time() - start_time,
                    session_id=session_id,
                    processing_time_ms=processing_time,
                    image_count=len(images),
                    duplicate_count=len(duplicate_pairs))
        
        return response
        
    except HTTPException:
        log_response(logger, "POST", "/api/analyze", 400, time.time() - start_time)
        raise
    except Exception as e:
        log_error(logger, e, {
            "endpoint": "/api/analyze", 
            "session_id": session_id,
            "client_ip": client_ip
        })
        log_response(logger, "POST", "/api/analyze", 500, time.time() - start_time)
        raise HTTPException(status_code=500, detail="Analysis processing failed")


@router.get("/api/session/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    session_mgr: SessionManagerDep
) -> SessionInfoResponse:
    """
    Get information about a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information including file count and expiration
    """
    session = await session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from datetime import timedelta
    expires_at = session.created_at + timedelta(hours=settings.session_ttl_hours)
    
    return SessionInfoResponse(
        session_id=session_id,
        created_at=session.created_at,
        file_count=len(session.files),
        expires_at=expires_at
    )


@router.get("/api/image/{session_id}/{image_id}")
async def get_image(
    session_id: str,
    image_id: str,
    session_mgr: SessionManagerDep
) -> FileResponse:
    """
    Serve an uploaded image for preview.
    
    Args:
        session_id: Session identifier
        image_id: Image identifier
        
    Returns:
        Image file response
    """
    # Validate session
    await validate_session_exists(session_id, session_mgr)
    
    # Get session data to find filename
    session = await session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Find file with matching ID
    matching_file = None
    for filename in session.files:
        if filename.startswith(image_id):
            matching_file = filename
            break
    
    if not matching_file:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Get file path
    file_path = await storage_service.get_file_path(session_id, matching_file)
    
    # For S3, we need to return the content directly
    if storage_service.use_s3:
        content = await storage_service.read_file(session_id, matching_file)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=storage_service._get_content_type(matching_file),
            headers={"Content-Disposition": f"inline; filename={matching_file}"}
        )
    else:
        # For local files, use FileResponse
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Image file not found")
        
        return FileResponse(
            path=file_path,
            media_type="image/jpeg",
            filename=matching_file
        )