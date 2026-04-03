"""Health check endpoints"""
from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service status and version information.
    Useful for monitoring and load balancer health checks.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
    }


@router.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "frontend": "/app",
    }
