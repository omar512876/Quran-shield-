"""Audio analysis route handlers"""
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from ..services import AudioAnalyzer
from ..utils import is_valid_url

router = APIRouter(prefix="/api", tags=["Audio Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_audio(
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
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
    - 422: Invalid audio format or invalid URL
    - 500: Analysis failed due to internal error
    """
    # Validate: at least one input required
    if file is None and url is None:
        raise HTTPException(
            status_code=400,
            detail="Please provide either an audio file or a YouTube URL."
        )
    
    analyzer = AudioAnalyzer()
    
    # === Process File Upload ===
    if file is not None:
        try:
            # Read file contents
            audio_bytes = await file.read()
            
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
