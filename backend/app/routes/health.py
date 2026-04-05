"""Health check endpoints"""
import logging
from fastapi import APIRouter, Request
from ..config import settings

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint.
    
    Returns basic service status, version information, and FFmpeg availability.
    Useful for monitoring and load balancer health checks.
    """
    # Check FFmpeg availability from app state
    ffmpeg_available = False
    ffmpeg_path = None
    
    try:
        ffmpeg_config = getattr(request.app.state, 'ffmpeg_config', None)
        if ffmpeg_config and ffmpeg_config.is_available():
            ffmpeg_available = True
            ffmpeg_path = ffmpeg_config.ffmpeg_path
    except Exception as e:
        logger.warning(f"Could not check FFmpeg status: {e}")
    
    # Check AudioAnalyzer availability
    analyzer_available = getattr(request.app.state, 'analyzer', None) is not None
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "ffmpeg_available": ffmpeg_available,
        "ffmpeg_path": ffmpeg_path,
        "analyzer_ready": analyzer_available,
        "features": {
            "file_upload": True,
            "youtube_download": ffmpeg_available,
        }
    }
