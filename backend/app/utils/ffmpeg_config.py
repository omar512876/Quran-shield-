"""FFmpeg configuration and path detection"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FFmpegConfig:
    """
    Manages ffmpeg binary paths for the application.
    
    This class handles:
    1. Detecting bundled ffmpeg in bin/ffmpeg/
    2. Falling back to system ffmpeg if bundled not found
    3. Configuring pydub and yt-dlp to use the correct ffmpeg
    """
    
    def __init__(self):
        """Initialize FFmpeg configuration"""
        self.ffmpeg_path: Optional[str] = None
        self.ffprobe_path: Optional[str] = None
        self._detect_ffmpeg()
    
    def _detect_ffmpeg(self):
        """
        Detect ffmpeg binaries in the following order:
        1. Bundled in bin/ffmpeg/ (for out-of-the-box Windows support)
        2. System PATH (if user has ffmpeg installed)
        """
        # Get project root directory
        # This file is in backend/app/utils/, so go up 3 levels
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # Path to bundled ffmpeg
        bundled_ffmpeg_dir = project_root / "bin" / "ffmpeg"
        
        # Determine binary names based on OS
        if sys.platform == "win32":
            ffmpeg_name = "ffmpeg.exe"
            ffprobe_name = "ffprobe.exe"
        else:
            ffmpeg_name = "ffmpeg"
            ffprobe_name = "ffprobe"
        
        # Check for bundled ffmpeg
        bundled_ffmpeg = bundled_ffmpeg_dir / ffmpeg_name
        bundled_ffprobe = bundled_ffmpeg_dir / ffprobe_name
        
        if bundled_ffmpeg.exists() and bundled_ffprobe.exists():
            self.ffmpeg_path = str(bundled_ffmpeg)
            self.ffprobe_path = str(bundled_ffprobe)
            logger.info(f"✅ Using bundled ffmpeg: {self.ffmpeg_path}")
            logger.info(f"✅ Using bundled ffprobe: {self.ffprobe_path}")
            return
        else:
            logger.warning(f"⚠️ Bundled ffmpeg not found at {bundled_ffmpeg_dir}")
        
        # Fall back to system PATH
        ffmpeg_in_path = self._find_in_path(ffmpeg_name)
        ffprobe_in_path = self._find_in_path(ffprobe_name)
        
        if ffmpeg_in_path and ffprobe_in_path:
            self.ffmpeg_path = ffmpeg_in_path
            self.ffprobe_path = ffprobe_in_path
            logger.info(f"✅ Using system ffmpeg: {self.ffmpeg_path}")
            logger.info(f"✅ Using system ffprobe: {self.ffprobe_path}")
            return
        
        # No ffmpeg found
        logger.error("❌ ffmpeg not found! The application will not work correctly.")
        logger.error("   Please either:")
        logger.error("   1. Place ffmpeg binaries in bin/ffmpeg/ folder, OR")
        logger.error("   2. Install ffmpeg system-wide and add to PATH")
    
    def _find_in_path(self, binary_name: str) -> Optional[str]:
        """
        Search for a binary in system PATH.
        
        Args:
            binary_name: Name of the binary (e.g., 'ffmpeg.exe' or 'ffmpeg')
            
        Returns:
            Full path to binary if found, None otherwise
        """
        # Use 'where' on Windows, 'which' on Unix
        if sys.platform == "win32":
            import subprocess
            try:
                result = subprocess.run(
                    ["where", binary_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Return first match
                    return result.stdout.strip().split('\n')[0]
            except Exception:
                pass
        else:
            import shutil
            return shutil.which(binary_name)
        
        return None
    
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
            "ffmpeg is not available. Please either:\n"
            "1. Download ffmpeg binaries and place in bin/ffmpeg/ folder, OR\n"
            "2. Install ffmpeg system-wide (https://ffmpeg.org/download.html)"
        )
