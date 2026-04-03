"""Main audio analysis service orchestrator"""
import io
import os
import tempfile
import shutil
import librosa
import numpy as np
import logging
import time
from pydub import AudioSegment
from typing import Dict
from .feature_extractor import FeatureExtractor
from .classifier import AudioClassifier
from .youtube_downloader import YouTubeDownloader
from ..utils.ffmpeg_config import get_ffmpeg_config

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """
    Main service for audio analysis operations.
    
    Orchestrates the complete analysis pipeline:
    1. Audio loading and preprocessing
    2. Feature extraction
    3. Classification
    """
    
    def __init__(self):
        """Initialize the audio analyzer with required services."""
        logger.info("Initializing AudioAnalyzer...")
        start_time = time.time()
        
        # Configure ffmpeg for pydub before creating services
        ffmpeg_config = get_ffmpeg_config()
        if ffmpeg_config.is_available():
            ffmpeg_config.configure_pydub()
            logger.info("✅ FFmpeg configured successfully")
        else:
            logger.warning("⚠️ FFmpeg not available - some features may not work")
        
        self.feature_extractor = FeatureExtractor()
        self.classifier = AudioClassifier()
        self.youtube_downloader = YouTubeDownloader(ffmpeg_config=ffmpeg_config)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ AudioAnalyzer initialized in {elapsed:.2f}s")
    
    def _load_and_analyze_wav(self, wav_path: str) -> Dict:
        """
        Load a WAV file and perform complete analysis.
        
        Args:
            wav_path: Path to WAV file
            
        Returns:
            Dictionary containing prediction, confidence, features, and reasoning
        """
        start_time = time.time()
        logger.info(f"Loading audio from: {wav_path}")
        
        # Load audio file
        audio_signal, sample_rate = librosa.load(wav_path, sr=None, mono=True)
        load_time = time.time() - start_time
        logger.info(f"Audio loaded in {load_time:.2f}s: duration={len(audio_signal)/sample_rate:.2f}s, sr={sample_rate}")
        
        # Extract features
        feature_start = time.time()
        features = self.feature_extractor.extract_features(audio_signal, sample_rate)
        feature_time = time.time() - feature_start
        logger.info(f"Features extracted in {feature_time:.2f}s")
        
        # Classify
        classify_start = time.time()
        prediction, confidence, reasoning = self.classifier.classify(features)
        classify_time = time.time() - classify_start
        logger.info(f"Classification completed in {classify_time:.2f}s: {prediction} ({confidence:.3f})")
        
        total_time = time.time() - start_time
        logger.info(f"Total analysis time: {total_time:.2f}s")
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "features": {k: round(v, 4) for k, v in features.items()},
            "reasoning": reasoning,
            "processing_time_seconds": round(total_time, 2),
        }
    
    def analyze_file(self, audio_bytes: bytes, filename: str = None) -> Dict:
        """
        Analyze an uploaded audio file.
        
        Args:
            audio_bytes: Raw audio file bytes
            filename: Original filename (optional)
            
        Returns:
            Analysis results dictionary
            
        Raises:
            ValueError: If audio cannot be decoded
            Exception: If analysis fails
        """
        logger.info(f"Analyzing file: {filename or 'unknown'} ({len(audio_bytes)} bytes)")
        
        if not audio_bytes:
            raise ValueError("Audio file is empty")
        
        # Decode audio using pydub (supports many formats via ffmpeg)
        try:
            logger.info("Decoding audio file...")
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            logger.info(f"✅ Audio decoded: duration={len(audio_segment)/1000:.2f}s, channels={audio_segment.channels}, sample_width={audio_segment.sample_width}")
        except Exception as e:
            logger.error(f"❌ Audio decoding failed: {e}")
            raise ValueError(f"Could not decode audio file: {str(e)}")
        
        # Convert to WAV for librosa processing
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            logger.info(f"Converting to WAV: {tmp_path}")
            audio_segment.export(tmp_path, format="wav")
            
            # Analyze
            result = self._load_and_analyze_wav(tmp_path)
            result["source"] = "file"
            if filename:
                result["filename"] = filename
            
            logger.info(f"✅ File analysis complete: {result['prediction']} (confidence: {result['confidence']})")
            return result
            
        finally:
            # Cleanup temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                    logger.debug(f"Cleaned up temp file: {tmp_path}")
                except:
                    pass
    
    def analyze_youtube_url(self, url: str) -> Dict:
        """
        Analyze audio from a YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Analysis results dictionary
            
        Raises:
            Exception: If download or analysis fails
        """
        logger.info(f"Analyzing YouTube URL: {url}")
        tmp_dir = None
        try:
            # Download and convert to WAV
            wav_path, tmp_dir = self.youtube_downloader.download_to_wav(url)
            
            # Analyze
            result = self._load_and_analyze_wav(wav_path)
            result["source"] = "youtube"
            result["url"] = url
            
            logger.info(f"✅ YouTube analysis complete: {result['prediction']} (confidence: {result['confidence']})")
            return result
            
        finally:
            # Cleanup temporary directory
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {tmp_dir}")
