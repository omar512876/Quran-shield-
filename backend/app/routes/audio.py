"""Audio analysis route handlers"""
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from ..services.audio_analyzer import AudioAnalyzer
from ..services.task_store import get_task, set_task, delete_task
from ..utils.validators import is_valid_url, validate_audio_mime, validate_youtube_url
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


def _run_analysis_task(task_id: str, callable, *args):
    """
    Run analysis in background and store result in task store.
    
    Args:
        task_id: Unique task identifier
        callable: The analysis function to call
        *args: Arguments to pass to the callable
    """
    set_task(task_id, {"status": "processing"})
    try:
        result = callable(*args)
        result["success"] = True
        set_task(task_id, {"status": "done", "result": result})
    except Exception as e:
        set_task(task_id, {"status": "error", "error": str(e)})


@router.post("/analyze")
async def analyze_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    analyzer: AudioAnalyzer = Depends(get_analyzer),
):
    """
    Analyze audio for suspicious background sounds.
    
    **Accepts either:**
    - `file`: An uploaded audio file (any format ffmpeg supports)
    - `url`: A YouTube URL
    
    **Returns:**
    - `success`: Boolean indicating success
    - `task_id`: Unique task identifier for polling results
    - `status`: "processing"
    
    **Poll /api/result/{task_id} to get the final result.**
    
    **Error Responses:**
    - 400: Neither file nor URL provided, or file is empty
    - 413: File too large
    - 415: Unsupported file type
    - 422: Invalid audio format or invalid URL
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
        
        # Check file size limit (50 MB)
        if len(audio_bytes) > 52_428_800:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": "File too large. Maximum is 50 MB."}
            )
        
        # Check MIME type
        if not validate_audio_mime(file.content_type):
            return JSONResponse(
                status_code=415,
                content={"success": False, "error": "Unsupported file type. Please upload an audio file."}
            )
        
        logger.info(f"Queuing analysis for uploaded file: {file.filename} ({len(audio_bytes)} bytes)")
        
        # Generate task ID and queue background task
        task_id = str(uuid.uuid4())
        background_tasks.add_task(_run_analysis_task, task_id, analyzer.analyze_file, audio_bytes, file.filename)
        
        return JSONResponse(
            status_code=202,
            content={"success": True, "task_id": task_id, "status": "processing"}
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
        
        # Validate YouTube domain
        if not validate_youtube_url(url):
            return JSONResponse(
                status_code=422,
                content={"success": False, "error": "Only YouTube URLs are supported."}
            )
        
        # Check if FFmpeg is available (required for YouTube)
        ffmpeg_config = getattr(request.app.state, 'ffmpeg_config', None)
        if not ffmpeg_config or not ffmpeg_config.is_available():
            return create_error_response(
                503,
                "YouTube processing is not available. FFmpeg is not configured on this server. Please upload an audio file instead.",
                "server_error"
            )
        
        logger.info(f"Queuing analysis for YouTube URL: {url}")
        
        # Generate task ID and queue background task
        task_id = str(uuid.uuid4())
        background_tasks.add_task(_run_analysis_task, task_id, analyzer.analyze_youtube_url, url)
        
        return JSONResponse(
            status_code=202,
            content={"success": True, "task_id": task_id, "status": "processing"}
        )


@router.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    Get the result of a background analysis task.
    
    **Returns:**
    - 404 if task not found
    - 202 if still processing
    - 200 if done (includes full result)
    - 500 if error occurred during processing
    """
    task = get_task(task_id)
    
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Task not found"}
        )
    
    status = task.get("status")
    
    if status == "processing":
        return JSONResponse(
            status_code=202,
            content={"success": True, "status": "processing"}
        )
    
    if status == "done":
        result = task.get("result", {})
        result["status"] = "done"
        delete_task(task_id)
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    if status == "error":
        error_msg = task.get("error", "Unknown error")
        delete_task(task_id)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": error_msg}
        )
    
    # Fallback for unexpected status
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Unknown task status"}
    )
