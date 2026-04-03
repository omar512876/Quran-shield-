"""
FFmpeg Auto-Download Manager

This module automatically downloads and manages FFmpeg binaries for the application.
It ensures FFmpeg is available without requiring manual installation by the user.

Features:
- Automatic download of FFmpeg binaries for Windows, Linux, and macOS
- Platform detection and correct binary selection
- Binary verification and permission management
- Fallback to system FFmpeg if preferred
- Offline-capable after first download
"""

import os
import sys
import platform
import logging
import shutil
import zipfile
import tarfile
import stat
import urllib.request
import hashlib
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# FFmpeg download URLs for different platforms
# Using static builds from official sources
FFMPEG_URLS = {
    "Windows": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "archive_type": "zip",
        "binary_path": "bin/ffmpeg.exe",
        "probe_path": "bin/ffprobe.exe",
    },
    "Linux": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
        "archive_type": "tar.xz",
        "binary_path": "bin/ffmpeg",
        "probe_path": "bin/ffprobe",
    },
    "Darwin": {  # macOS
        "url": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        "url_probe": "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        "archive_type": "zip",
        "binary_path": "ffmpeg",
        "probe_path": "ffprobe",
    },
}


class FFmpegManager:
    """
    Manages FFmpeg binaries for the application.
    
    Automatically downloads and installs FFmpeg if not present in the project directory.
    Handles platform-specific differences and ensures binaries are executable.
    """
    
    def __init__(self, install_dir: Optional[Path] = None):
        """
        Initialize FFmpeg Manager.
        
        Args:
            install_dir: Directory to install FFmpeg. Defaults to backend/bin/ffmpeg/
        """
        if install_dir is None:
            # Default to backend/bin/ffmpeg relative to this file
            # This file is in backend/app/utils/, so go up 2 levels, then to bin/ffmpeg
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent.parent
            install_dir = backend_dir / "bin" / "ffmpeg"
        
        self.install_dir = Path(install_dir)
        self.platform = platform.system()
        self.ffmpeg_path: Optional[Path] = None
        self.ffprobe_path: Optional[Path] = None
        
        logger.info(f"FFmpegManager initialized for {self.platform}")
        logger.info(f"Install directory: {self.install_dir}")
    
    def ensure_ffmpeg(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Ensure FFmpeg is available. Download if necessary.
        
        Returns:
            Tuple of (ffmpeg_path, ffprobe_path) as strings, or (None, None) if failed
        """
        # First, check if already installed in project directory
        if self._check_local_ffmpeg():
            logger.info("✅ FFmpeg found in project directory")
            return str(self.ffmpeg_path), str(self.ffprobe_path)
        
        # Try to use imageio-ffmpeg if available (from previous setup)
        imageio_paths = self._try_imageio_ffmpeg()
        if imageio_paths[0]:
            logger.info("✅ Using imageio-ffmpeg bundled binaries")
            return imageio_paths
        
        # Check system PATH
        system_paths = self._check_system_ffmpeg()
        if system_paths[0]:
            logger.info("✅ Using system FFmpeg from PATH")
            return system_paths
        
        # Download FFmpeg
        logger.info("FFmpeg not found. Downloading...")
        if self._download_ffmpeg():
            logger.info("✅ FFmpeg downloaded successfully")
            return str(self.ffmpeg_path), str(self.ffprobe_path)
        
        # All methods failed
        logger.error("❌ Failed to obtain FFmpeg binaries")
        return None, None
    
    def _check_local_ffmpeg(self) -> bool:
        """
        Check if FFmpeg exists in the project directory.
        
        Returns:
            True if found and valid, False otherwise
        """
        if not self.install_dir.exists():
            return False
        
        # Determine binary names based on platform
        if self.platform == "Windows":
            ffmpeg_name = "ffmpeg.exe"
            ffprobe_name = "ffprobe.exe"
        else:
            ffmpeg_name = "ffmpeg"
            ffprobe_name = "ffprobe"
        
        ffmpeg_path = self.install_dir / ffmpeg_name
        ffprobe_path = self.install_dir / ffprobe_name
        
        if ffmpeg_path.exists() and ffprobe_path.exists():
            # Verify they're executable
            if self._verify_executable(ffmpeg_path) and self._verify_executable(ffprobe_path):
                self.ffmpeg_path = ffmpeg_path
                self.ffprobe_path = ffprobe_path
                return True
        
        return False
    
    def _try_imageio_ffmpeg(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to use imageio-ffmpeg if installed.
        
        Returns:
            Tuple of (ffmpeg_path, ffprobe_path) or (None, None)
        """
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            if ffmpeg_exe and os.path.exists(ffmpeg_exe):
                # Try to find ffprobe in same directory
                ffmpeg_dir = Path(ffmpeg_exe).parent
                ffprobe_name = "ffprobe.exe" if self.platform == "Windows" else "ffprobe"
                ffprobe_path = ffmpeg_dir / ffprobe_name
                
                if ffprobe_path.exists():
                    return str(ffmpeg_exe), str(ffprobe_path)
                else:
                    # Fallback to system ffprobe
                    system_ffprobe = shutil.which(ffprobe_name)
                    return str(ffmpeg_exe), system_ffprobe
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"imageio-ffmpeg check failed: {e}")
        
        return None, None
    
    def _check_system_ffmpeg(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Check if FFmpeg is available in system PATH.
        
        Returns:
            Tuple of (ffmpeg_path, ffprobe_path) or (None, None)
        """
        ffmpeg_name = "ffmpeg.exe" if self.platform == "Windows" else "ffmpeg"
        ffprobe_name = "ffprobe.exe" if self.platform == "Windows" else "ffprobe"
        
        ffmpeg_path = shutil.which(ffmpeg_name)
        ffprobe_path = shutil.which(ffprobe_name)
        
        if ffmpeg_path and ffprobe_path:
            return ffmpeg_path, ffprobe_path
        
        return None, None
    
    def _download_ffmpeg(self) -> bool:
        """
        Download FFmpeg binaries for the current platform.
        
        Returns:
            True if successful, False otherwise
        """
        if self.platform not in FFMPEG_URLS:
            logger.error(f"Unsupported platform: {self.platform}")
            return False
        
        config = FFMPEG_URLS[self.platform]
        
        try:
            # Create install directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # Download based on platform
            if self.platform == "Darwin":
                # macOS requires separate downloads for ffmpeg and ffprobe
                return self._download_macos(config)
            else:
                # Windows and Linux have combined archives
                return self._download_archive(config)
            
        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            return False
    
    def _download_archive(self, config: dict) -> bool:
        """
        Download and extract FFmpeg from archive (Windows/Linux).
        
        Args:
            config: Platform configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        url = config["url"]
        archive_type = config["archive_type"]
        
        # Determine archive filename
        if archive_type == "zip":
            archive_name = "ffmpeg.zip"
        elif archive_type == "tar.xz":
            archive_name = "ffmpeg.tar.xz"
        else:
            logger.error(f"Unknown archive type: {archive_type}")
            return False
        
        archive_path = self.install_dir / archive_name
        
        # Download archive
        logger.info(f"Downloading FFmpeg from {url}")
        try:
            urllib.request.urlretrieve(url, archive_path)
            logger.info(f"Downloaded to {archive_path}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
        
        # Extract archive
        logger.info("Extracting archive...")
        try:
            if archive_type == "zip":
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Extract to temporary directory first
                    temp_dir = self.install_dir / "temp"
                    temp_dir.mkdir(exist_ok=True)
                    zip_ref.extractall(temp_dir)
                    
                    # Find the binaries in extracted content
                    self._find_and_move_binaries(temp_dir, config)
                    
                    # Cleanup
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            elif archive_type == "tar.xz":
                with tarfile.open(archive_path, 'r:xz') as tar_ref:
                    # Extract to temporary directory
                    temp_dir = self.install_dir / "temp"
                    temp_dir.mkdir(exist_ok=True)
                    tar_ref.extractall(temp_dir)
                    
                    # Find and move binaries
                    self._find_and_move_binaries(temp_dir, config)
                    
                    # Cleanup
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Remove archive
            archive_path.unlink()
            
            # Make binaries executable
            self._make_executable()
            
            # Verify
            return self._check_local_ffmpeg()
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return False
    
    def _download_macos(self, config: dict) -> bool:
        """
        Download FFmpeg binaries for macOS (separate files).
        
        Args:
            config: Platform configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Download ffmpeg
            ffmpeg_zip = self.install_dir / "ffmpeg.zip"
            urllib.request.urlretrieve(config["url"], ffmpeg_zip)
            
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
            ffmpeg_zip.unlink()
            
            # Download ffprobe
            ffprobe_zip = self.install_dir / "ffprobe.zip"
            urllib.request.urlretrieve(config["url_probe"], ffprobe_zip)
            
            with zipfile.ZipFile(ffprobe_zip, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
            ffprobe_zip.unlink()
            
            # Make executable
            self._make_executable()
            
            # Verify
            return self._check_local_ffmpeg()
            
        except Exception as e:
            logger.error(f"macOS download failed: {e}", exc_info=True)
            return False
    
    def _find_and_move_binaries(self, temp_dir: Path, config: dict):
        """
        Find binaries in extracted archive and move to install directory.
        
        Args:
            temp_dir: Temporary extraction directory
            config: Platform configuration
        """
        # Look for binaries in the extraction
        binary_path = config["binary_path"]
        probe_path = config["probe_path"]
        
        # Search for the binaries
        for root, dirs, files in os.walk(temp_dir):
            root_path = Path(root)
            
            # Check if this directory contains the binaries
            if binary_path.endswith("ffmpeg.exe") or binary_path.endswith("ffmpeg"):
                binary_name = os.path.basename(binary_path)
                if binary_name in files:
                    src = root_path / binary_name
                    dst = self.install_dir / binary_name
                    shutil.copy2(src, dst)
                    logger.info(f"Copied {binary_name} to {dst}")
            
            if probe_path.endswith("ffprobe.exe") or probe_path.endswith("ffprobe"):
                probe_name = os.path.basename(probe_path)
                if probe_name in files:
                    src = root_path / probe_name
                    dst = self.install_dir / probe_name
                    shutil.copy2(src, dst)
                    logger.info(f"Copied {probe_name} to {dst}")
    
    def _make_executable(self):
        """Make binaries executable on Unix-like systems."""
        if self.platform in ["Linux", "Darwin"]:
            for binary_name in ["ffmpeg", "ffprobe"]:
                binary_path = self.install_dir / binary_name
                if binary_path.exists():
                    # Add executable permission
                    st = os.stat(binary_path)
                    os.chmod(binary_path, st.st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    logger.info(f"Made {binary_name} executable")
    
    def _verify_executable(self, binary_path: Path) -> bool:
        """
        Verify that a binary is executable.
        
        Args:
            binary_path: Path to binary
            
        Returns:
            True if executable, False otherwise
        """
        if not binary_path.exists():
            return False
        
        # On Unix, check if executable bit is set
        if self.platform in ["Linux", "Darwin"]:
            return os.access(binary_path, os.X_OK)
        
        # On Windows, just check if file exists
        return True
    
    def get_version(self) -> Optional[str]:
        """
        Get FFmpeg version.
        
        Returns:
            Version string or None if failed
        """
        if not self.ffmpeg_path:
            return None
        
        try:
            import subprocess
            result = subprocess.run(
                [str(self.ffmpeg_path), "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse version from output
                first_line = result.stdout.split('\n')[0]
                return first_line
            
        except Exception as e:
            logger.error(f"Failed to get FFmpeg version: {e}")
        
        return None


# Global instance
_manager: Optional[FFmpegManager] = None


def get_ffmpeg_manager() -> FFmpegManager:
    """
    Get the global FFmpeg manager instance.
    
    Returns:
        FFmpegManager instance
    """
    global _manager
    if _manager is None:
        _manager = FFmpegManager()
    return _manager


def ensure_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    """
    Ensure FFmpeg is available. Download if necessary.
    
    This is the main function to call from other modules.
    
    Returns:
        Tuple of (ffmpeg_path, ffprobe_path) or (None, None) if failed
    """
    manager = get_ffmpeg_manager()
    return manager.ensure_ffmpeg()
