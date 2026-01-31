"""
FastAPI dependency providers for rate limiting and session management.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.session_manager import session_manager, SessionManager
from core.logger import get_api_logger
from app.config import settings


logger = get_api_logger()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance."""
    return session_manager


async def get_client_ip(request: Request) -> str:
    """Get client IP address for logging and rate limiting."""
    # Check for forwarded headers first (for proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


async def validate_session_exists(
    session_id: str,
    session_mgr: Annotated[SessionManager, Depends(get_session_manager)]
) -> str:
    """
    Validate that a session exists and return the session ID.
    
    Args:
        session_id: Session ID to validate
        session_mgr: Session manager instance
        
    Returns:
        Validated session ID
        
    Raises:
        HTTPException: If session doesn't exist
    """
    session = await session_mgr.get_session(session_id)
    if not session:
        logger.warning("Session not found", session_id=session_id)
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or expired"
        )
    
    return session_id


# Rate limiting decorators
def upload_rate_limit(request: Request):
    """Rate limit for upload endpoints."""
    return limiter.limit(settings.rate_limit_uploads)(request)


def analyze_rate_limit(request: Request):
    """Rate limit for analysis endpoints."""
    return limiter.limit(settings.rate_limit_analyze)(request)


# Type aliases for dependency injection
SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]
ClientIPDep = Annotated[str, Depends(get_client_ip)]