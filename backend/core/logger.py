"""
Structured logging wrapper for the Carousel Optimizer application.
"""

import sys
import logging
import structlog
from typing import Any, Dict, Optional
from pathlib import Path

from app.config import settings


class Logger:
    """Centralized logging wrapper with structured logging support."""
    
    _configured = False
    
    @classmethod
    def configure(cls) -> None:
        """Configure structured logging for the application."""
        if cls._configured:
            return
            
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.JSONRenderer() if settings.log_format == "json" 
                else structlog.dev.ConsoleRenderer(colors=True)
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.log_level.upper(), logging.INFO)
            ),
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> structlog.BoundLogger:
        """Get a configured logger instance."""
        cls.configure()
        return structlog.get_logger(name)


def get_logger(name: str) -> structlog.BoundLogger:
    """Convenience function to get a logger."""
    return Logger.get_logger(name)


# Application loggers
def get_api_logger() -> structlog.BoundLogger:
    """Get logger for API operations."""
    return get_logger("api")


def get_ai_logger() -> structlog.BoundLogger:
    """Get logger for AI/ML operations.""" 
    return get_logger("ai")


def get_session_logger() -> structlog.BoundLogger:
    """Get logger for session management."""
    return get_logger("session")


def get_security_logger() -> structlog.BoundLogger:
    """Get logger for security operations."""
    return get_logger("security")


# Log helper functions
def log_request(logger: structlog.BoundLogger, method: str, path: str, **kwargs):
    """Log HTTP request with context."""
    logger.info("Request started", method=method, path=path, **kwargs)


def log_response(logger: structlog.BoundLogger, method: str, path: str, status: int, duration: float, **kwargs):
    """Log HTTP response with context."""
    logger.info("Request completed", method=method, path=path, status=status, duration_ms=duration * 1000, **kwargs)


def log_error(logger: structlog.BoundLogger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error with context."""
    logger.error("Error occurred", error=str(error), error_type=type(error).__name__, **(context or {}))