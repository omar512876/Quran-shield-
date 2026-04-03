"""YouTube audio download service"""
import os
import glob
import tempfile
import shutil
import logging
import yt_dlp
from typing import Tuple
from pydub import AudioSegment
from ..utils.ffmpeg_config import get_ffmpeg_config

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """
    Downloads audio from YouTube URLs using yt-dlp.
    
    This service handles the downloading and conversion of YouTube videos
    to WAV format for audio analysis. It uses bundled ffmpeg for out-of-the-box
    Windows support.
    
    Process:
    1. Download best audio with yt-dlp (gets webm, m4a, etc.)
    2. Convert to WAV using pydub with bundled ffmpeg
    """
    
    def __init__(self):
        """Initialize the YouTube downloader with ffmpeg configuration"""
        self.max_duration = 600  # 10 minutes max to avoid huge files
        
        # Get and configure ffmpeg
        self.ffmpeg_config = get_ffmpeg_config()
        if self.ffmpeg_config.is_available():
            self.ffmpeg_config.configure_pydub()
            logger.info("✅ YouTubeDownloader initialized with ffmpeg support")
        else:
            logger.warning("⚠️ YouTubeDownloader initialized WITHOUT ffmpeg - downloads may fail!")
    
    def download_to_wav(self, url: str) -> Tuple[str, str]:
        """
        Download audio from a YouTube URL and convert to WAV.
        
        This method uses a robust two-stage process:
        1. Download best audio format using yt-dlp (webm, m4a, etc.)
        2. Convert to WAV using pydub with bundled/system ffmpeg
        
        Args:
            url: YouTube video URL
            
        Returns:
            Tuple of (wav_file_path, temp_directory_path)
            The caller is responsible for cleaning up the temp directory.
            
        Raises:
            ValueError: If URL is invalid or video too long
            RuntimeError: If ffmpeg is not available
            FileNotFoundError: If download or conversion fails
            Exception: If download fails for other reasons
        """
        # Verify ffmpeg is available before attempting download
        if not self.ffmpeg_config.is_available():
            raise RuntimeError(
                "ffmpeg is not available. Please download ffmpeg binaries and place them in bin/ffmpeg/ folder.\n"
                "See FFMPEG_SETUP.md for instructions."
            )
        
        tmp_dir = None
        try:
            # Create temporary directory for download
            tmp_dir = tempfile.mkdtemp(prefix="quran_shield_yt_")
            logger.info(f"Created temp directory: {tmp_dir}")
            
            # Output template for downloaded file
            output_template = os.path.join(tmp_dir, "audio.%(ext)s")
            
            # Configure yt-dlp options for downloading best audio
            ydl_opts = {
                "format": "bestaudio/best",  # Get best audio quality
                "outtmpl": output_template,
                "quiet": False,  # Show output for debugging
                "no_warnings": False,
                "extract_flat": False,
                # Don't use ffmpeg postprocessor - we'll convert manually with pydub
                # This is more reliable and allows us to use bundled ffmpeg
                "postprocessors": [],
                # Limit file size to avoid huge downloads
                "max_filesize": 100 * 1024 * 1024,  # 100MB max
            }
            
            # Add ffmpeg location if using bundled version
            ffmpeg_args = self.ffmpeg_config.get_yt_dlp_postprocessor_args()
            if ffmpeg_args:
                ydl_opts.update(ffmpeg_args)
            
            logger.info(f"Starting YouTube download for: {url}")
            
            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, extract info to check duration
                try:
                    info = ydl.extract_info(url, download=False)
                    duration = info.get('duration', 0)
                    
                    if duration > self.max_duration:
                        raise ValueError(
                            f"Video is too long ({duration}s). "
                            f"Maximum allowed is {self.max_duration}s (10 minutes)."
                        )
                    
                    logger.info(f"Video duration: {duration}s, title: {info.get('title', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Could not extract video info: {e}")
                    # Continue anyway - might still work
                
                # Now download
                ydl.download([url])
            
            logger.info("YouTube download completed")
            
            # Find the downloaded audio file (could be webm, m4a, opus, etc.)
            audio_files = []
            for ext in ['webm', 'm4a', 'opus', 'mp3', 'aac', 'ogg', 'mp4']:
                pattern = os.path.join(tmp_dir, f"*.{ext}")
                files = glob.glob(pattern)
                audio_files.extend(files)
            
            if not audio_files:
                # List what files we actually got
                all_files = os.listdir(tmp_dir)
                logger.error(f"No audio files found. Files in temp dir: {all_files}")
                raise FileNotFoundError(
                    "YouTube download succeeded but no audio file was found. "
                    "The video might not have an audio track."
                )
            
            # Use the first audio file found
            downloaded_file = audio_files[0]
            logger.info(f"Found downloaded audio file: {downloaded_file}")
            
            # Convert to WAV using pydub with bundled ffmpeg
            wav_path = os.path.join(tmp_dir, "converted_audio.wav")
            
            try:
                logger.info(f"Converting {downloaded_file} to WAV using bundled ffmpeg...")
                logger.info(f"Using ffmpeg at: {self.ffmpeg_config.ffmpeg_path}")
                
                # Load audio file (pydub will use our configured ffmpeg)
                audio = AudioSegment.from_file(downloaded_file)
                
                # Export as WAV with standard settings
                audio.export(
                    wav_path,
                    format="wav",
                    parameters=["-ac", "1"]  # Mono channel for analysis
                )
                logger.info(f"✅ Conversion successful: {wav_path}")
                
            except Exception as e:
                logger.error(f"pydub conversion failed: {e}")
                raise FileNotFoundError(
                    f"Audio conversion failed: {str(e)}. "
                    "This usually means ffmpeg is not properly configured. "
                    "Please ensure ffmpeg binaries are in bin/ffmpeg/ folder."
                )
            
            # Verify WAV file exists and has content
            if not os.path.exists(wav_path):
                raise FileNotFoundError("WAV file was not created")
            
            file_size = os.path.getsize(wav_path)
            if file_size < 1000:  # Less than 1KB is suspicious
                raise FileNotFoundError(
                    f"WAV file is too small ({file_size} bytes). Conversion may have failed."
                )
            
            logger.info(f"✅ WAV file ready: {wav_path} ({file_size} bytes)")
            
            return wav_path, tmp_dir
            
        except ValueError as e:
            # Video too long or invalid
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            raise
        
        except RuntimeError as e:
            # ffmpeg not available
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            raise
            
        except FileNotFoundError as e:
            # File not found or conversion failed
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            raise
            
        except Exception as e:
            # Any other error
            logger.error(f"YouTube download failed: {e}", exc_info=True)
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            
            # Provide helpful error message
            error_msg = str(e).lower()
            if "private" in error_msg or "unavailable" in error_msg:
                raise ValueError("This video is private or unavailable")
            elif "copyright" in error_msg:
                raise ValueError("This video is not available due to copyright restrictions")
            elif "age" in error_msg:
                raise ValueError("This video is age-restricted and cannot be downloaded")
            else:
                raise Exception(f"YouTube download failed: {str(e)}")
