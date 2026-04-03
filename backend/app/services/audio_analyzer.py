"""Main audio analysis service orchestrator"""
import io
import os
import tempfile
import shutil
import librosa
import numpy as np
from pydub import AudioSegment
from typing import Dict
from .feature_extractor import FeatureExtractor
from .classifier import AudioClassifier
from .youtube_downloader import YouTubeDownloader
from ..utils.ffmpeg_config import get_ffmpeg_config


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
        # Configure ffmpeg for pydub before creating services
        ffmpeg_config = get_ffmpeg_config()
        if ffmpeg_config.is_available():
            ffmpeg_config.configure_pydub()
        
        self.feature_extractor = FeatureExtractor()
        self.classifier = AudioClassifier()
        self.youtube_downloader = YouTubeDownloader()
    
    def _load_and_analyze_wav(self, wav_path: str) -> Dict:
        """
        Load a WAV file and perform complete analysis.
        
        Args:
            wav_path: Path to WAV file
            
        Returns:
            Dictionary containing prediction, confidence, features, and reasoning
        """
        # Load audio file
        audio_signal, sample_rate = librosa.load(wav_path, sr=None, mono=True)
        
        # Extract features
        features = self.feature_extractor.extract_features(audio_signal, sample_rate)
        
        # Classify
        prediction, confidence, reasoning = self.classifier.classify(features)
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "features": {k: round(v, 4) for k, v in features.items()},
            "reasoning": reasoning,
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
        if not audio_bytes:
            raise ValueError("Audio file is empty")
        
        # Decode audio using pydub (supports many formats via ffmpeg)
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as e:
            raise ValueError(f"Could not decode audio file: {str(e)}")
        
        # Convert to WAV for librosa processing
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            
            audio_segment.export(tmp_path, format="wav")
            
            # Analyze
            result = self._load_and_analyze_wav(tmp_path)
            result["source"] = "file"
            if filename:
                result["filename"] = filename
            
            return result
            
        finally:
            # Cleanup temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
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
        tmp_dir = None
        try:
            # Download and convert to WAV
            wav_path, tmp_dir = self.youtube_downloader.download_to_wav(url)
            
            # Analyze
            result = self._load_and_analyze_wav(wav_path)
            result["source"] = "youtube"
            result["url"] = url
            
            return result
            
        finally:
            # Cleanup temporary directory
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
