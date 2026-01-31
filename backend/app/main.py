"""
Main FastAPI application for the Carousel Optimizer.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.routes import router
from app.api.dependencies import limiter
from core.logger import Logger, get_api_logger, log_request, log_response, log_error
from core.session_manager import session_manager
from modules.embeddings import embedding_generator


# Configure logging
Logger.configure()
logger = get_api_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events for startup and shutdown.
    """
    # Startup
    logger.info("Starting Carousel Optimizer application...")
    
    try:
        # CLIP model will be lazy-loaded on first use
        logger.info("CLIP model will be loaded on first request")
        
        # Start session cleanup task
        await session_manager.start_cleanup_task()
        logger.info("Session cleanup task started")
        
        logger.info("Application startup completed")
        
        yield
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        
        # Stop cleanup task
        await session_manager.stop_cleanup_task()
        
        # Clear embedding cache
        embedding_generator.clear_cache()
        
        logger.info("Application shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="PDP Carousel Optimizer",
    description="AI-powered product image carousel optimization service",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Middleware for request/response logging and timing.
    """
    start_time = time.time()
    
    # Log request start
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    log_request(logger, request.method, str(request.url.path), client_ip=client_ip)
    
    try:
        response = await call_next(request)
        
        # Log successful response
        duration = time.time() - start_time
        log_response(logger, request.method, str(request.url.path), 
                    response.status_code, duration, client_ip=client_ip)
        
        return response
        
    except Exception as e:
        # Log error response
        duration = time.time() - start_time
        log_error(logger, e, {
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": client_ip,
            "duration": duration
        })
        
        # Return generic error response
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to all responses.
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler with structured error responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    log_error(logger, exc, {
        "method": request.method,
        "path": str(request.url.path),
        "client_ip": request.client.host if request.client else "unknown"
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "PDP Carousel Optimizer",
        "version": "0.3.0",
        "status": "running",
        "docs": "/docs" if settings.debug else None
    }