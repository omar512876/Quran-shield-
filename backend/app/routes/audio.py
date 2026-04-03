"""Audio analysis route handlers"""
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
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
    analyzer = getattr(request.app.state, 'analyzer', None)
    if analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Audio analyzer is not available. The service may be starting up. Please try again in a moment."
        )
    return analyzer


def create_error_response(status_code: int, message: str, error_type: str = "error") -> JSONResponse:
    """
    Create a standardized JSON error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Type of error (error, validation_error, server_error)
        
    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": message,
            "error_type": error_type,
            "detail": message  # For backwards compatibility
        }
    )


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
    - `success`: Boolean indicating success
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
    - 503: Service not ready
    """
    # Validate: at least one input required
    if file is None and url is None:
        return create_error_response(
            400,
            "Please provide either an audio file or a YouTube URL.",
            "validation_error"
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
                    return create_error_response(
                        413,
                        f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
                        "validation_error"
                    )
            
            # Read file contents
            audio_bytes = await file.read()
            
            # Second check: validate actual file size (for chunked uploads without Content-Length)
            if len(audio_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                return create_error_response(
                    413,
                    f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB.",
                    "validation_error"
                )
            
            if not audio_bytes:
                return create_error_response(
                    400,
                    "Uploaded file is empty.",
                    "validation_error"
                )
            
            logger.info(f"Analyzing uploaded file: {file.filename} ({len(audio_bytes)} bytes)")
            
            # Analyze
            result = analyzer.analyze_file(audio_bytes, file.filename)
            result["success"] = True
            return result
            
        except ValueError as e:
            # Audio decoding error
            logger.warning(f"Audio decode failed: {e}")
            return create_error_response(
                422,
                f"Could not decode audio file: {str(e)}",
                "validation_error"
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"File analysis failed: {e}", exc_info=True)
            return create_error_response(
                500,
                "Audio analysis failed. Please try again.",
                "server_error"
            )
    
    # === Process YouTube URL ===
    if url is not None:
        # Validate URL format
        if not is_valid_url(url):
            return create_error_response(
                422,
                "Invalid URL. Please provide a valid HTTP/HTTPS URL.",
                "validation_error"
            )
        
        # Check if FFmpeg is available (required for YouTube)
        ffmpeg_config = getattr(request.app.state, 'ffmpeg_config', None)
        if not ffmpeg_config or not ffmpeg_config.is_available():
            return create_error_response(
                503,
                "YouTube processing is not available. FFmpeg is not configured on this server. Please upload an audio file instead.",
                "server_error"
            )
        
        try:
            # Analyze
            logger.info(f"Processing YouTube URL: {url}")
            result = analyzer.analyze_youtube_url(url)
            result["success"] = True
            logger.info(f"YouTube analysis successful: {result.get('prediction')}")
            return result
        
        except RuntimeError as e:
            # ffmpeg not available
            logger.error(f"ffmpeg configuration error: {e}")
            return create_error_response(
                503,
                "YouTube processing failed: FFmpeg is not properly configured. Please try uploading an audio file instead.",
                "server_error"
            )
            
        except ValueError as e:
            # Video too long, private, or other validation error
            logger.warning(f"YouTube validation error: {e}")
            return create_error_response(
                422,
                str(e),
                "validation_error"
            )
        except FileNotFoundError as e:
            # Download or conversion failed
            logger.error(f"YouTube download/conversion failed: {e}")
            return create_error_response(
                500,
                str(e),
                "server_error"
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"YouTube analysis failed for {url}: {e}", exc_info=True)
            
            # Provide helpful error message based on error type
            error_str = str(e).lower()
            if "network" in error_str or "connection" in error_str:
                detail = "Network error. Please check your internet connection and try again."
            elif "timeout" in error_str:
                detail = "Request timed out. The video may be too large or the connection is slow."
            elif "403" in error_str or "forbidden" in error_str:
                detail = "Access denied by YouTube. The video may be region-locked or age-restricted."
            elif "404" in error_str or "not found" in error_str:
                detail = "Video not found. Please check the URL and try again."
            elif "private" in error_str or "unavailable" in error_str:
                detail = "This video is private or unavailable."
            else:
                detail = f"Failed to download or analyze the YouTube URL. Error: {str(e)}"
            
            return create_error_response(
                500,
                detail,
                "server_error"
            )
