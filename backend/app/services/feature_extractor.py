"""Enhanced audio feature extraction service with error handling"""
import numpy as np
import librosa
import logging
from typing import Dict, Optional
from ..config import settings

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts acoustic features from audio signals using librosa.
    
    This class implements a comprehensive feature extraction pipeline
    that captures timbral, spectral, rhythmic, and harmonic characteristics
    of audio signals, optimized for distinguishing music from speech.
    
    Enhanced with robust error handling and edge case validation.
    """
    
    def __init__(self, sample_rate: int = None, n_mfcc: int = None):
        """
        Initialize the feature extractor.
        
        Args:
            sample_rate: Target sample rate for audio (defaults to config)
            n_mfcc: Number of MFCC coefficients to extract (defaults to config)
        """
        self.sample_rate = sample_rate or settings.SAMPLE_RATE
        self.n_mfcc = n_mfcc or settings.N_MFCC
        logger.info(f"FeatureExtractor initialized: sample_rate={self.sample_rate}, n_mfcc={self.n_mfcc}")
    
    def _validate_audio(self, audio_signal: np.ndarray, sr: int) -> None:
        """
        Validate audio signal before feature extraction.
        
        Args:
            audio_signal: Audio signal array
            sr: Sample rate
            
        Raises:
            ValueError: If audio is invalid
        """
        if audio_signal is None or len(audio_signal) == 0:
            raise ValueError("Audio signal is empty")
        
        if sr <= 0:
            raise ValueError(f"Invalid sample rate: {sr}")
        
        # Check for silence (all zeros or very low RMS)
        rms_energy = np.sqrt(np.mean(audio_signal**2))
        if rms_energy < 1e-6:
            raise ValueError("Audio appears to be silent or contains no signal")
        
        # Check duration (minimum 0.5 seconds)
        duration = len(audio_signal) / sr
        if duration < 0.5:
            raise ValueError(f"Audio too short: {duration:.2f}s (minimum 0.5s required)")
        
        logger.info(f"Audio validation passed: duration={duration:.2f}s, RMS={rms_energy:.6f}")
    
    def _safe_feature_extraction(self, func, *args, **kwargs) -> Optional[float]:
        """
        Safely extract a feature with error handling.
        
        Args:
            func: Feature extraction function
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Feature value or None if extraction fails
        """
        try:
            result = func(*args, **kwargs)
            if isinstance(result, np.ndarray):
                value = float(np.mean(result))
            else:
                value = float(result)
            
            # Check for NaN or Inf
            if not np.isfinite(value):
                logger.warning(f"Feature {func.__name__} produced non-finite value: {value}")
                return 0.0
            
            return value
        except Exception as e:
            logger.error(f"Feature extraction failed for {func.__name__}: {e}")
            return 0.0
    
    def extract_features(self, audio_signal: np.ndarray, sr: int) -> Dict[str, float]:
        """
        Extract a comprehensive set of acoustic features from audio.
        
        Features extracted:
        - MFCCs (Mel-Frequency Cepstral Coefficients): Timbral texture
        - Spectral features: Brightness, spread, rolloff, contrast
        - Chroma features: Pitch class distribution
        - Temporal features: Zero-crossing rate, RMS energy, tempo, onsets
        
        Args:
            audio_signal: Mono audio signal as numpy array
            sr: Sample rate of the audio
            
        Returns:
            Dictionary of feature names to float values
            
        Raises:
            ValueError: If audio is invalid or too short
            Exception: If critical feature extraction fails
        """
        # Validate input
        self._validate_audio(audio_signal, sr)
        
        features = {}
        logger.info(f"Extracting features from audio: length={len(audio_signal)}, sr={sr}")
        
        try:
            # === MFCC Features (Timbral) ===
            mfccs = librosa.feature.mfcc(y=audio_signal, sr=sr, n_mfcc=self.n_mfcc)
            features["mfcc_mean"] = float(np.mean(mfccs))
            features["mfcc_std"] = float(np.std(mfccs))
            
            # MFCC delta (temporal dynamics)
            mfcc_delta = librosa.feature.delta(mfccs)
            features["mfcc_delta_mean"] = float(np.mean(np.abs(mfcc_delta)))
            
            # === Spectral Features ===
            # Spectral centroid: "brightness" or center of mass of spectrum
            centroid = librosa.feature.spectral_centroid(y=audio_signal, sr=sr)
            features["spectral_centroid"] = float(np.mean(centroid))
            
            # Spectral bandwidth: spread around the centroid
            bandwidth = librosa.feature.spectral_bandwidth(y=audio_signal, sr=sr)
            features["spectral_bandwidth"] = float(np.mean(bandwidth))
            
            # Spectral rolloff: frequency below which 85% of energy is contained
            rolloff = librosa.feature.spectral_rolloff(y=audio_signal, sr=sr, roll_percent=0.85)
            features["spectral_rolloff"] = float(np.mean(rolloff))
            
            # Spectral contrast: difference between peaks and valleys
            contrast = librosa.feature.spectral_contrast(y=audio_signal, sr=sr)
            features["spectral_contrast"] = float(np.mean(contrast))
            
            # === Harmonic Features (Chroma) ===
            chroma = librosa.feature.chroma_stft(y=audio_signal, sr=sr)
            features["chroma_mean"] = float(np.mean(chroma))
            features["chroma_std"] = float(np.std(chroma))
            
            # === Temporal Features ===
            # Zero-crossing rate: noisiness/percussiveness indicator
            zcr = librosa.feature.zero_crossing_rate(audio_signal)
            features["zcr"] = float(np.mean(zcr))
            
            # RMS energy: average loudness
            rms = librosa.feature.rms(y=audio_signal)
            features["rms"] = float(np.mean(rms))
            
            # Tempo: rhythmic regularity (with error handling for difficult audio)
            try:
                tempo, _ = librosa.beat.beat_track(y=audio_signal, sr=sr)
                features["tempo"] = float(np.squeeze(tempo))
            except Exception as e:
                logger.warning(f"Tempo extraction failed: {e}. Using default.")
                features["tempo"] = 60.0  # Default neutral tempo
            
            # Onset strength: sudden energy bursts (note attacks, drum hits)
            onset_env = librosa.onset.onset_strength(y=audio_signal, sr=sr)
            features["onset_mean"] = float(np.mean(onset_env))
            features["onset_std"] = float(np.std(onset_env))
            
            # Validate all features are finite
            for key, value in features.items():
                if not np.isfinite(value):
                    logger.warning(f"Non-finite feature {key}={value}, replacing with 0.0")
                    features[key] = 0.0
            
            logger.info(f"✅ Successfully extracted {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}", exc_info=True)
            raise Exception(f"Failed to extract audio features: {str(e)}")
