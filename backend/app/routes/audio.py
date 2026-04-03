"""Audio analysis route handlers"""
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, Depends
from ..services.audio_analyzer import AudioAnalyzer
from ..utils.validators import is_valid_url
from ..config import settings

router = APIRouter(prefix="/api", tags=["Audio Analysis"])
logger = logging.getLogger(__name__)


def get_analyzer(request: Request) -> AudioAnalyzer:
    """
    Dependency to get the cached AudioAnalyzer instance.
    
    This avoids re-instantiating AudioAnalyzer on every request.
    """
    return request.app.state.analyzer


@router.post("/analyze")
async def analyze_audio(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    analyzer: AudioAnalyzer = Depends(get_analyzer),
):
    """
    Analyze audio and classify it as 'music' or 'quran/speech'.
    
    **Accepts either:**
    - `file`: An uploaded audio file (any format ffmpeg supports)
    - `url`: A YouTube URL
    
    **Returns:**
    - `source`: "file" or "youtube"
    - `prediction`: "music" or "quran/speech"
    - `confidence`: Confidence score (0.0 to 1.0)
    - `features`: Extracted acoustic features
    - `reasoning`: Per-feature classification breakdown
    - `filename` or `url`: Original source identifier
    
    **Error Responses:**
    - 400: Neither file nor URL provided, or file is empty
    - 413: File too large
    - 422: Invalid audio format or invalid URL
    - 500: Analysis failed due to internal error
    """
    # Validate: at least one input required
    if file is None and url is None:
        raise HTTPException(
            status_code=400,
            detail="Please provide either an audio file or a YouTube URL."
        )
    
    # === Process File Upload ===
    if file is not None:
        try:
            # Check Content-Length header BEFORE reading file
            content_length = request.headers.get("content-length")
            if content_length:
                content_length_bytes = int(content_length)
                max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
                
                if content_length_bytes > max_size_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB."
                    )
            
            # Read file contents
            audio_bytes = await file.read()
            
            # Second check: validate actual file size (for chunked uploads without Content-Length)
            if len(audio_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB."
                )
            
            if not audio_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty."
                )
            
            # Analyze
            result = analyzer.analyze_file(audio_bytes, file.filename)
            return result
            
        except ValueError as e:
            # Audio decoding error
            logger.warning(f"Audio decode failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Could not decode audio file: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            # Unexpected error
            logger.error(f"File analysis failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Audio analysis failed. Please try again."
            )
    
    # === Process YouTube URL ===
    if url is not None:
        # Validate URL format
        if not is_valid_url(url):
            raise HTTPException(
                status_code=422,
                detail="Invalid URL. Must be a valid HTTP/HTTPS URL."
            )
        
        try:
            # Analyze
            logger.info(f"Processing YouTube URL: {url}")
            result = analyzer.analyze_youtube_url(url)
            logger.info(f"YouTube analysis successful: {result.get('prediction')}")
            return result
        
        except RuntimeError as e:
            # ffmpeg not available
            logger.error(f"ffmpeg configuration error: {e}")
            raise HTTPException(
                status_code=500,
                detail=str(e) + "\nPlease download ffmpeg and place in bin/ffmpeg/ folder. See FFMPEG_SETUP.md for instructions."
            )
            
        except ValueError as e:
            # Video too long, private, or other validation error
            logger.warning(f"YouTube validation error: {e}")
            raise HTTPException(
                status_code=422,
                detail=str(e)
            )
        except FileNotFoundError as e:
            # Download or conversion failed
            logger.error(f"YouTube download/conversion failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"YouTube analysis failed for {url}: {e}", exc_info=True)
            
            # Provide helpful error message based on error type
            error_str = str(e).lower()
            if "network" in error_str or "connection" in error_str:
                detail = "Network error. Please check your internet connection and try again."
            elif "timeout" in error_str:
                detail = "Request timed out. The video may be too large or your connection is slow."
            elif "403" in error_str or "forbidden" in error_str:
                detail = "Access denied by YouTube. The video may be region-locked or age-restricted."
            elif "404" in error_str or "not found" in error_str:
                detail = "Video not found. Please check the URL and try again."
            else:
                detail = f"Failed to download or analyze the YouTube URL: {str(e)}"
            
            raise HTTPException(
                status_code=500,
                detail=detail
            )
