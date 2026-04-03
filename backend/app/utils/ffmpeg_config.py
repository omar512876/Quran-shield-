"""FFmpeg configuration and path detection"""
import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Optional
from .ffmpeg_manager import ensure_ffmpeg

logger = logging.getLogger(__name__)


class FFmpegConfig:
    """
    Manages ffmpeg binary paths for the application.
    
    This class handles:
    1. Automatic FFmpeg download to backend/bin/ffmpeg/ if not present
    2. Fallback to imageio-ffmpeg bundled binaries
    3. Fallback to system FFmpeg if installed
    4. Configuring pydub and yt-dlp to use the correct ffmpeg
    """
    
    def __init__(self):
        """Initialize FFmpeg configuration"""
        self.ffmpeg_path: Optional[str] = None
        self.ffprobe_path: Optional[str] = None
        self._detect_ffmpeg()
    
    def _detect_ffmpeg(self):
        """
        Detect or download FFmpeg binaries.
        
        Uses the FFmpegManager to automatically:
        1. Check backend/bin/ffmpeg/ directory
        2. Try imageio-ffmpeg if installed
        3. Check system PATH
        4. Download binaries if none found
        """
        logger.info("Detecting FFmpeg binaries...")
        
        # Use the FFmpeg manager to ensure binaries are available
        ffmpeg_path, ffprobe_path = ensure_ffmpeg()
        
        if ffmpeg_path and ffprobe_path:
            self.ffmpeg_path = ffmpeg_path
            self.ffprobe_path = ffprobe_path
            logger.info(f"✅ FFmpeg: {self.ffmpeg_path}")
            logger.info(f"✅ FFprobe: {self.ffprobe_path}")
        else:
            logger.error("❌ FFmpeg not found and auto-download failed!")
            logger.error("   The application may not work correctly.")
            logger.error("   Please check your internet connection and try again,")
            logger.error("   or install FFmpeg manually: https://ffmpeg.org/download.html")
    
    def is_available(self) -> bool:
        """Check if ffmpeg is available"""
        return self.ffmpeg_path is not None and self.ffprobe_path is not None
    
    def configure_pydub(self):
        """Configure pydub to use detected ffmpeg"""
        if not self.is_available():
            logger.warning("⚠️ Cannot configure pydub: ffmpeg not available")
            return
        
        from pydub import AudioSegment
        AudioSegment.converter = self.ffmpeg_path
        AudioSegment.ffmpeg = self.ffmpeg_path
        
        if self.ffprobe_path:
            AudioSegment.ffprobe = self.ffprobe_path
        
        logger.info("✅ pydub configured to use detected ffmpeg")
    
    def get_yt_dlp_postprocessor_args(self) -> dict:
        """
        Get yt-dlp postprocessor arguments for ffmpeg.
        
        Returns:
            Dictionary with ffmpeg location for yt-dlp
        """
        if not self.is_available():
            return {}
        
        return {
            "ffmpeg_location": str(Path(self.ffmpeg_path).parent)
        }


# Global instance
_ffmpeg_config: Optional[FFmpegConfig] = None


def get_ffmpeg_config() -> FFmpegConfig:
    """
    Get the global FFmpeg configuration instance.
    
    Returns:
        FFmpegConfig instance
    """
    global _ffmpeg_config
    if _ffmpeg_config is None:
        _ffmpeg_config = FFmpegConfig()
    return _ffmpeg_config


def ensure_ffmpeg_available():
    """
    Ensure ffmpeg is available and raise error if not.
    
    Raises:
        RuntimeError: If ffmpeg is not available
    """
    config = get_ffmpeg_config()
    if not config.is_available():
        raise RuntimeError(
            "FFmpeg is not available and could not be downloaded automatically.\n"
            "Please check your internet connection and restart the application,\n"
            "or install FFmpeg manually from https://ffmpeg.org/download.html"
        )
