"""Audio feature extraction service"""
import numpy as np
import librosa
from typing import Dict
from ..config import settings


class FeatureExtractor:
    """
    Extracts acoustic features from audio signals using librosa.
    
    This class implements a comprehensive feature extraction pipeline
    that captures timbral, spectral, rhythmic, and harmonic characteristics
    of audio signals, optimized for distinguishing music from speech.
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
        """
        features = {}
        
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
        
        # Tempo: rhythmic regularity
        tempo, _ = librosa.beat.beat_track(y=audio_signal, sr=sr)
        features["tempo"] = float(np.squeeze(tempo))
        
        # Onset strength: sudden energy bursts (note attacks, drum hits)
        onset_env = librosa.onset.onset_strength(y=audio_signal, sr=sr)
        features["onset_mean"] = float(np.mean(onset_env))
        features["onset_std"] = float(np.std(onset_env))
        
        return features
