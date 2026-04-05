"""Main FastAPI application"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .config import settings
from .routes import audio_router, health_router
from .services.audio_analyzer import AudioAnalyzer
from .utils.ffmpeg_config import get_ffmpeg_config, FFmpegConfig

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Global FFmpeg config for health checks
_ffmpeg_config: FFmpegConfig = None


def get_app_ffmpeg_config() -> FFmpegConfig:
    """Get the global FFmpeg config instance."""
    global _ffmpeg_config
    return _ffmpeg_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    global _ffmpeg_config
    
    # Startup
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} v{settings.VERSION} starting...")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    
    # Warn if CORS is wide open
    if "*" in settings.CORS_ORIGINS:
        logger.warning("⚠️ WARNING: CORS is open to all origins. Set CORS_ORIGINS in .env for production.")
    
    # CRITICAL: Initialize FFmpeg FIRST before anything else
    logger.info("=" * 60)
    logger.info("INITIALIZING FFMPEG...")
    logger.info("=" * 60)
    
    try:
        _ffmpeg_config = get_ffmpeg_config()
        if _ffmpeg_config.is_available():
            logger.info(f"✅ FFmpeg available at: {_ffmpeg_config.ffmpeg_path}")
            logger.info(f"✅ FFprobe available at: {_ffmpeg_config.ffprobe_path}")
            _ffmpeg_config.configure_pydub()
            logger.info("✅ pydub configured with FFmpeg")
        else:
            logger.error("❌ FFmpeg NOT AVAILABLE!")
            logger.error("   YouTube processing and some audio formats will NOT work.")
            logger.error("   The application will start but with limited functionality.")
    except Exception as e:
        logger.error(f"❌ FFmpeg initialization failed: {e}")
        logger.error("   YouTube processing and some audio formats will NOT work.")
        _ffmpeg_config = None
    
    # Store FFmpeg config in app state for health checks
    app.state.ffmpeg_config = _ffmpeg_config
    
    # Initialize AudioAnalyzer singleton
    logger.info("=" * 60)
    logger.info("INITIALIZING AUDIO ANALYZER...")
    logger.info("=" * 60)
    
    try:
        app.state.analyzer = AudioAnalyzer()
        logger.info("✅ AudioAnalyzer initialized and cached")
    except Exception as e:
        logger.error(f"❌ AudioAnalyzer initialization failed: {e}")
        # Create a minimal analyzer anyway - it will fail gracefully on use
        app.state.analyzer = None
    
    logger.info("=" * 60)
    logger.info(f"✅ {settings.APP_NAME} READY")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully...")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Audio analysis API to detect music vs. Quran/speech in audio files and YouTube URLs",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    root_path=""
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routes FIRST (so they take precedence over static files)
app.include_router(health_router)
app.include_router(audio_router)

# Add root endpoint to serve frontend
@app.get("/", response_class=None)
async def root():
    """Serve the frontend application."""
    from fastapi.responses import FileResponse
    frontend_file = project_root / "frontend" / "index.html"
    if frontend_file.exists():
        return FileResponse(path=frontend_file, media_type="text/html")
    # Fallback to app mount
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app/index.html")

# ============================================================================
# FRONTEND STATIC FILES MOUNTING
# ============================================================================
# The frontend folder is in the project root, not in the backend folder.
# We need to calculate the correct path relative to this file's location.
#
# Directory structure:
#   Quran-shield-/
#   ├── backend/
#   │   └── app/
#   │       └── main.py  <-- we are here
#   └── frontend/
#       └── index.html
#
# So frontend is at: ../../frontend (relative to this file)
# ============================================================================

# Get the directory where this main.py file is located
current_file_dir = Path(__file__).resolve().parent

# Navigate up to the project root: backend/app -> backend -> project_root
project_root = current_file_dir.parent.parent

# Frontend directory is at project_root/frontend
frontend_dir = project_root / "frontend"

# Mount frontend static files at /app
try:
    if frontend_dir.exists() and frontend_dir.is_dir():
        # StaticFiles with html=True serves index.html for directory requests
        app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
        logger.info(f"✅ Frontend mounted at /app from {frontend_dir}")
    else:
        logger.warning(f"⚠️ Frontend directory not found at {frontend_dir}")
except Exception as e:
    logger.error(f"❌ Could not mount frontend: {e}")
