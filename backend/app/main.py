"""Main FastAPI application"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routes import audio_router, health_router
from .services.audio_analyzer import AudioAnalyzer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    logger.info(f"{settings.APP_NAME} v{settings.VERSION} starting...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    
    # Warn if CORS is wide open
    if "*" in settings.CORS_ORIGINS:
        logger.warning("⚠️ WARNING: CORS is open to all origins. Set CORS_ORIGINS in .env for production.")
    
    # Initialize AudioAnalyzer singleton
    logger.info("Initializing AudioAnalyzer...")
    app.state.analyzer = AudioAnalyzer()
    logger.info("✅ AudioAnalyzer initialized and cached")
    
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
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register routes FIRST (so they take precedence over static files)
app.include_router(health_router)
app.include_router(audio_router)

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
