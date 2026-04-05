"""
Audio Analysis Service - Suspicious Sound Detection Pipeline

This module implements the core audio analysis pipeline for detecting suspicious
background sounds (music overlays, subliminal audio) in audio files and YouTube videos.

Detection Pipeline:
1. INPUT: Audio file (via upload) or YouTube URL (via yt-dlp download)
2. PREPROCESSING: Convert to mono WAV, normalize sample rate
3. WINDOWED ANALYSIS: Divide into 0.5s overlapping frames, extract features:
   - Spectral centroid (brightness)
   - Spectral contrast (peak-valley difference)
   - RMS energy (loudness)
   - Zero-crossing rate (noisiness)
   - MFCC deltas (timbral changes)
4. OUTPUT: Verdict (safe/suspicious), confidence score, flagged segments with
   timestamps and labels (music_overlay, subliminal, noise)

The analysis uses z-score normalization across frames to detect anomalous segments
that deviate significantly from the audio's baseline characteristics.
"""
import io
import os
import tempfile
import shutil
import librosa
import numpy as np
import logging
import time
from pydub import AudioSegment
from typing import Dict, List, Tuple, Optional
from .feature_extractor import FeatureExtractor
from .classifier import AudioClassifier
from .youtube_downloader import YouTubeDownloader
from ..utils.ffmpeg_config import get_ffmpeg_config

logger = logging.getLogger(__name__)


def _format_seconds(s: float) -> str:
    """
    Convert total seconds to "m:ss" format.
    
    Examples: 74.3 → "1:14", 9.0 → "0:09", 130.0 → "2:10"
    """
    total_seconds = int(s)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def _analyze_audio(audio_signal: np.ndarray, sr: int) -> Dict:
    """
    Analyze audio for suspicious background sounds using frame-based analysis.
    
    Divides audio into overlapping frames and computes per-frame features,
    then flags anomalous segments based on z-score deviations.
    
    Args:
        audio_signal: Mono audio signal as numpy array
        sr: Sample rate of the audio
        
    Returns:
        Dictionary containing verdict, confidence, duration, and suspicious segments
    """
    # Frame parameters: 0.5s frames with 50% overlap
    frame_length_sec = 0.5
    hop_length_sec = 0.25  # 50% overlap
    frame_length_samples = int(frame_length_sec * sr)
    hop_length_samples = int(hop_length_sec * sr)
    
    # Calculate total duration
    total_duration = len(audio_signal) / sr
    
    # Calculate number of frames
    n_frames = max(1, int(np.ceil((len(audio_signal) - frame_length_samples) / hop_length_samples)) + 1)
    
    # Storage for per-frame features
    spectral_centroids = []
    spectral_contrasts = []
    rms_energies = []
    zcrs = []
    mfcc_deltas = []
    
    # Extract features for each frame
    for i in range(n_frames):
        start_sample = i * hop_length_samples
        end_sample = min(start_sample + frame_length_samples, len(audio_signal))
        frame = audio_signal[start_sample:end_sample]
        
        # Skip frames that are too short
        if len(frame) < frame_length_samples // 2:
            continue
        
        # Pad frame if needed
        if len(frame) < frame_length_samples:
            frame = np.pad(frame, (0, frame_length_samples - len(frame)), mode='constant')
        
        # Spectral centroid
        centroid = librosa.feature.spectral_centroid(y=frame, sr=sr)
        spectral_centroids.append(float(np.mean(centroid)))
        
        # Spectral contrast (mean across bands)
        contrast = librosa.feature.spectral_contrast(y=frame, sr=sr)
        spectral_contrasts.append(float(np.mean(contrast)))
        
        # RMS energy
        rms = librosa.feature.rms(y=frame)
        rms_energies.append(float(np.mean(rms)))
        
        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(frame)
        zcrs.append(float(np.mean(zcr)))
        
        # MFCC delta (mean of delta of first 13 MFCCs)
        mfccs = librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=13)
        mfcc_delta = librosa.feature.delta(mfccs)
        mfcc_deltas.append(float(np.mean(np.abs(mfcc_delta))))
    
    # Convert to numpy arrays
    spectral_centroids = np.array(spectral_centroids)
    spectral_contrasts = np.array(spectral_contrasts)
    rms_energies = np.array(rms_energies)
    zcrs = np.array(zcrs)
    mfcc_deltas = np.array(mfcc_deltas)
    
    actual_n_frames = len(spectral_centroids)
    
    if actual_n_frames == 0:
        return {
            "verdict": "safe",
            "confidence": 0.0,
            "duration": round(total_duration, 4),
            "summary": "No suspicious sounds detected.",
            "segments": [],
            "features": {
                "spectral_centroid_mean": 0.0,
                "zcr_mean": 0.0,
                "rms_mean": 0.0
            }
        }
    
    # Z-score normalization for each feature
    def z_score_normalize(arr: np.ndarray) -> np.ndarray:
        std = np.std(arr)
        if std < 1e-10:
            return np.zeros_like(arr)
        return (arr - np.mean(arr)) / std
    
    z_centroids = z_score_normalize(spectral_centroids)
    z_contrasts = z_score_normalize(spectral_contrasts)
    z_rms = z_score_normalize(rms_energies)
    z_zcrs = z_score_normalize(zcrs)
    z_mfcc_deltas = z_score_normalize(mfcc_deltas)
    
    # Compute per-frame suspicion score
    # Mean of absolute z-scores across 5 features, then sigmoid transformation
    def sigmoid_transform(x: float) -> float:
        return 1.0 / (1.0 + np.exp(-x + 2))
    
    suspicion_scores = []
    for i in range(actual_n_frames):
        mean_abs_z = np.mean([
            abs(z_centroids[i]),
            abs(z_contrasts[i]),
            abs(z_rms[i]),
            abs(z_zcrs[i]),
            abs(z_mfcc_deltas[i])
        ])
        score = sigmoid_transform(mean_abs_z)
        score = np.clip(score, 0.0, 1.0)
        suspicion_scores.append(score)
    
    suspicion_scores = np.array(suspicion_scores)
    
    # Flag frames where suspicion score > 0.55
    threshold = 0.55
    flagged_frames = np.where(suspicion_scores > threshold)[0]
    
    if len(flagged_frames) == 0:
        return {
            "verdict": "safe",
            "confidence": 0.0,
            "duration": round(total_duration, 4),
            "summary": "No suspicious sounds detected.",
            "segments": [],
            "features": {
                "spectral_centroid_mean": round(float(np.mean(spectral_centroids)), 4),
                "zcr_mean": round(float(np.mean(zcrs)), 4),
                "rms_mean": round(float(np.mean(rms_energies)), 4)
            }
        }
    
    # Merge consecutive flagged frames separated by less than 1 second
    # 1 second = 4 frames at 0.25s hop
    merge_gap_frames = int(1.0 / hop_length_sec)
    
    segments: List[Tuple[int, int]] = []
    current_start = flagged_frames[0]
    current_end = flagged_frames[0]
    
    for frame_idx in flagged_frames[1:]:
        if frame_idx - current_end <= merge_gap_frames:
            current_end = frame_idx
        else:
            segments.append((current_start, current_end))
            current_start = frame_idx
            current_end = frame_idx
    segments.append((current_start, current_end))
    
    # Convert frame indices to timestamps and determine labels
    result_segments = []
    segment_scores = []
    
    for start_frame, end_frame in segments:
        start_time = round(start_frame * hop_length_sec, 4)
        end_time = round((end_frame + 1) * hop_length_sec + (frame_length_sec - hop_length_sec), 4)
        end_time = min(end_time, round(total_duration, 4))
        
        # Calculate segment score (mean of suspicion scores in segment)
        segment_suspicion = suspicion_scores[start_frame:end_frame + 1]
        segment_score = float(np.mean(segment_suspicion))
        segment_scores.append(segment_score)
        
        # Determine label based on which z-score dominates
        segment_z_centroid = np.mean(np.abs(z_centroids[start_frame:end_frame + 1]))
        segment_z_rms = np.mean(np.abs(z_rms[start_frame:end_frame + 1]))
        segment_z_others = np.mean([
            np.mean(np.abs(z_contrasts[start_frame:end_frame + 1])),
            np.mean(np.abs(z_zcrs[start_frame:end_frame + 1])),
            np.mean(np.abs(z_mfcc_deltas[start_frame:end_frame + 1]))
        ])
        
        # Label logic: centroid dominates → music_overlay; RMS dominates → subliminal; else → noise
        if segment_z_centroid >= segment_z_rms and segment_z_centroid >= segment_z_others:
            label = "music_overlay"
        elif segment_z_rms >= segment_z_centroid and segment_z_rms >= segment_z_others:
            label = "subliminal"
        else:
            label = "noise"
        
        result_segments.append({
            "start": round(start_time, 4),
            "end": round(end_time, 4),
            "start_formatted": _format_seconds(start_time),
            "end_formatted": _format_seconds(end_time),
            "score": round(segment_score, 4),
            "label": label
        })
    
    # Calculate overall confidence (mean suspicion score of flagged segments)
    confidence = float(np.mean(segment_scores)) if segment_scores else 0.0
    
    # Build summary string
    n_segments = len(result_segments)
    if n_segments == 0:
        summary = "No suspicious sounds detected."
    elif n_segments == 1:
        summary = f"1 suspicious segment found at {result_segments[0]['start_formatted']}."
    else:
        summary = f"{n_segments} suspicious segments found, first at {result_segments[0]['start_formatted']}."
    
    return {
        "verdict": "suspicious" if n_segments > 0 else "safe",
        "confidence": round(confidence, 4),
        "duration": round(total_duration, 4),
        "summary": summary,
        "segments": result_segments,
        "features": {
            "spectral_centroid_mean": round(float(np.mean(spectral_centroids)), 4),
            "zcr_mean": round(float(np.mean(zcrs)), 4),
            "rms_mean": round(float(np.mean(rms_energies)), 4)
        }
    }


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
            Dictionary containing verdict, confidence, duration, and suspicious segments
        """
        start_time = time.time()
        logger.info(f"Loading audio from: {wav_path}")
        
        # Load audio file
        audio_signal, sample_rate = librosa.load(wav_path, sr=None, mono=True)
        load_time = time.time() - start_time
        logger.info(f"Audio loaded in {load_time:.2f}s: duration={len(audio_signal)/sample_rate:.2f}s, sr={sample_rate}")
        
        # Perform frame-based suspicious audio analysis
        analyze_start = time.time()
        result = _analyze_audio(audio_signal, sample_rate)
        analyze_time = time.time() - analyze_start
        logger.info(f"Analysis completed in {analyze_time:.2f}s: {result['verdict']} (confidence: {result['confidence']})")
        
        total_time = time.time() - start_time
        logger.info(f"Total analysis time: {total_time:.2f}s")
        
        # Add processing time to result
        result["processing_time_seconds"] = round(total_time, 2)
        
        return result
    
    def analyze_file(self, audio_bytes: bytes, filename: Optional[str] = None) -> Dict:
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
            
            logger.info(f"✅ File analysis complete: {result['verdict']} (confidence: {result['confidence']})")
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
            
            logger.info(f"✅ YouTube analysis complete: {result['verdict']} (confidence: {result['confidence']})")
            return result
            
        finally:
            # Cleanup temporary directory
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temp directory: {tmp_dir}")
