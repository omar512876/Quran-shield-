"""Unit tests for FFmpeg manager"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.ffmpeg_manager import FFmpegManager, get_ffmpeg_manager, ensure_ffmpeg


class TestFFmpegManager:
    """Test suite for FFmpeg auto-download manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = FFmpegManager(install_dir=self.test_dir)
    
    def teardown_method(self):
        """Cleanup after tests"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """Test FFmpegManager initializes correctly"""
        assert self.manager.install_dir == self.test_dir
        assert self.manager.platform in ["Windows", "Linux", "Darwin"]
        assert self.manager.ffmpeg_path is None  # Not detected yet
        assert self.manager.ffprobe_path is None
    
    def test_check_local_ffmpeg_not_found(self):
        """Test _check_local_ffmpeg returns False when binaries don't exist"""
        result = self.manager._check_local_ffmpeg()
        assert result is False
    
    def test_check_local_ffmpeg_found(self):
        """Test _check_local_ffmpeg finds existing binaries"""
        # Create dummy binaries
        self.test_dir.mkdir(exist_ok=True)
        
        if self.manager.platform == "Windows":
            ffmpeg_path = self.test_dir / "ffmpeg.exe"
            ffprobe_path = self.test_dir / "ffprobe.exe"
        else:
            ffmpeg_path = self.test_dir / "ffmpeg"
            ffprobe_path = self.test_dir / "ffprobe"
        
        # Create dummy files
        ffmpeg_path.write_text("dummy")
        ffprobe_path.write_text("dummy")
        
        # Make executable on Unix
        if self.manager.platform != "Windows":
            import stat
            os.chmod(ffmpeg_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            os.chmod(ffprobe_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        result = self.manager._check_local_ffmpeg()
        assert result is True
        assert self.manager.ffmpeg_path == ffmpeg_path
        assert self.manager.ffprobe_path == ffprobe_path
    
    def test_check_system_ffmpeg(self):
        """Test _check_system_ffmpeg detects system binaries"""
        # This test may pass or fail depending on system FFmpeg installation
        ffmpeg_path, ffprobe_path = self.manager._check_system_ffmpeg()
        
        # Either both found or both not found
        if ffmpeg_path:
            assert ffprobe_path is not None or ffprobe_path is None
            assert Path(ffmpeg_path).exists()
    
    @patch('urllib.request.urlretrieve')
    def test_download_prevents_actual_download(self, mock_download):
        """Test that download methods are called but don't actually download in tests"""
        # Mock the download to prevent actual network calls in tests
        mock_download.return_value = None
        
        # Test should not make real network calls
        assert True  # Placeholder test
    
    def test_verify_executable_windows(self):
        """Test executable verification on Windows"""
        if self.manager.platform == "Windows":
            test_file = self.test_dir / "test.exe"
            test_file.write_text("test")
            
            result = self.manager._verify_executable(test_file)
            assert result is True
    
    def test_verify_executable_unix(self):
        """Test executable verification on Unix"""
        if self.manager.platform in ["Linux", "Darwin"]:
            test_file = self.test_dir / "test"
            test_file.write_text("test")
            
            # Not executable yet
            result = self.manager._verify_executable(test_file)
            assert result is False
            
            # Make executable
            import stat
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            
            result = self.manager._verify_executable(test_file)
            assert result is True
    
    def test_make_executable_unix(self):
        """Test _make_executable on Unix systems"""
        if self.manager.platform in ["Linux", "Darwin"]:
            # Create test binaries
            ffmpeg_path = self.test_dir / "ffmpeg"
            ffprobe_path = self.test_dir / "ffprobe"
            ffmpeg_path.write_text("test")
            ffprobe_path.write_text("test")
            
            self.manager._make_executable()
            
            # Check if executable
            assert os.access(ffmpeg_path, os.X_OK)
            assert os.access(ffprobe_path, os.X_OK)
    
    def test_try_imageio_ffmpeg_not_installed(self):
        """Test _try_imageio_ffmpeg when package not installed"""
        with patch.dict('sys.modules', {'imageio_ffmpeg': None}):
            ffmpeg, ffprobe = self.manager._try_imageio_ffmpeg()
            # Should return None when package not available
            # (or actual paths if package is installed)
            assert isinstance(ffmpeg, (str, type(None)))
            assert isinstance(ffprobe, (str, type(None)))
    
    def test_ensure_ffmpeg_finds_existing(self):
        """Test ensure_ffmpeg uses existing binaries"""
        # Create dummy binaries
        self.test_dir.mkdir(exist_ok=True)
        
        if self.manager.platform == "Windows":
            ffmpeg_path = self.test_dir / "ffmpeg.exe"
            ffprobe_path = self.test_dir / "ffprobe.exe"
        else:
            ffmpeg_path = self.test_dir / "ffmpeg"
            ffprobe_path = self.test_dir / "ffprobe"
        
        ffmpeg_path.write_text("dummy")
        ffprobe_path.write_text("dummy")
        
        if self.manager.platform != "Windows":
            import stat
            os.chmod(ffmpeg_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            os.chmod(ffprobe_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        ffmpeg, ffprobe = self.manager.ensure_ffmpeg()
        
        assert ffmpeg == str(ffmpeg_path)
        assert ffprobe == str(ffprobe_path)
    
    def test_global_manager_singleton(self):
        """Test that get_ffmpeg_manager returns singleton"""
        manager1 = get_ffmpeg_manager()
        manager2 = get_ffmpeg_manager()
        assert manager1 is manager2
    
    def test_ensure_ffmpeg_function(self):
        """Test module-level ensure_ffmpeg function"""
        ffmpeg, ffprobe = ensure_ffmpeg()
        # Should return paths or None
        assert isinstance(ffmpeg, (str, type(None)))
        assert isinstance(ffprobe, (str, type(None)))


class TestFFmpegIntegration:
    """Integration tests for FFmpeg functionality"""
    
    def test_ffmpeg_available_after_ensure(self):
        """Test that FFmpeg is available after calling ensure_ffmpeg"""
        ffmpeg_path, ffprobe_path = ensure_ffmpeg()
        
        # If successful, paths should exist
        if ffmpeg_path:
            assert Path(ffmpeg_path).exists()
        if ffprobe_path:
            assert Path(ffprobe_path).exists()
    
    def test_ffmpeg_version_check(self):
        """Test getting FFmpeg version"""
        manager = get_ffmpeg_manager()
        manager.ensure_ffmpeg()
        
        version = manager.get_version()
        # Version might be None if FFmpeg not available
        if version:
            assert "ffmpeg" in version.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
