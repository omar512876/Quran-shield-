"""
Audio Analysis Service - Suspicious Sound Detection Pipeline (ENGINE v3)

This module implements the core audio analysis pipeline for detecting suspicious
background sounds (music overlays, subliminal audio) in audio files and YouTube videos.

Detection Pipeline (THREE-SIGNAL + HPSS):
1. INPUT: Audio file (via upload) or YouTube URL (via yt-dlp download)
2. PREPROCESSING: Convert to mono WAV, normalize sample rate
3. SOURCE SEPARATION: Split audio into harmonic and percussive components using HPSS
4. VOICE ACTIVITY DETECTION: Identify frames where voice is present (top 40% RMS)
5. THREE-SIGNAL ANOMALY DETECTION (requires 2-of-3 corroboration):
   - Spectral Centroid: Most reliable. Pure voice ~1200-2000 Hz, music pushes >2500 Hz
   - Spectral Flatness: Detects tonal music overlays (energy spreads across frequencies)
   - Percussive Ratio: Detects drums/beats (pure recitation has no percussion)
6. OUTPUT: Verdict (safe/suspicious), confidence score, flagged segments with
   timestamps and labels (music_overlay, subliminal, noise)

Calibration Data (April 2026):
- CLEAN Quran: centroid ~1608 Hz, zcr ~0.03, rms ~0.055
- SUSPICIOUS music: centroid ~4300 Hz (2.7x higher), zcr ~0.067

Why this approach works:
- Spectral centroid is the most reliable single signal (2.7x separation)
- Requiring 2-of-3 signals provides corroborating evidence, reducing false positives
- HPSS physically separates harmonic (voice, melody) from percussive (drums, beats)
- Voice Activity Detection naturally excludes silence/breath without arbitrary thresholds
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
    Analyze audio for suspicious background sounds using THREE-SIGNAL detection.
    
    ENGINE v3: HPSS + Spectral Centroid + Spectral Flatness + Percussive Ratio
    
    Three independent signals, requiring 2-of-3 corroboration:
    1. Spectral Centroid: Most reliable. Pure voice ~1200-2000 Hz, music >2500 Hz
    2. Spectral Flatness: Detects broadband music overlays
    3. Percussive Ratio: Detects drums/beats via HPSS separation
    
    Args:
        audio_signal: Mono audio signal as numpy array
        sr: Sample rate of the audio
        
    Returns:
        Dictionary containing verdict, confidence, duration, and suspicious segments
    """
    # Confirm ENGINE v3 is running
    print("=" * 60)
    print("ENGINE v3 - Three-signal detector active")
    print("Signals: spectral_centroid, spectral_flatness, percussive_ratio")
    print("Rule: 2-of-3 signals required for flagging")
    print("=" * 60)
    logger.info("ENGINE v3 - Three-signal detector active")
    
    # Frame parameters
    frame_length_sec = 0.5
    hop_length_sec = 0.25  # 50% overlap
    frame_length_samples = int(frame_length_sec * sr)
    hop_length_samples = int(hop_length_sec * sr)
    
    # Calculate total duration
    total_duration = len(audio_signal) / sr
    
    # ==========================================================================
    # STEP 1: HARMONIC-PERCUSSIVE SOURCE SEPARATION (HPSS)
    # ==========================================================================
    # Split audio into harmonic (voice, melodic) and percussive (drums, beats)
    # Pure Quran recitation should have near-zero percussive energy
    logger.info("Performing HPSS decomposition...")
    harmonic, percussive = librosa.effects.hpss(audio_signal)
    
    # ==========================================================================
    # STEP 2: FRAME-BASED FEATURE EXTRACTION
    # ==========================================================================
    n_frames = max(1, int(np.ceil((len(audio_signal) - frame_length_samples) / hop_length_samples)) + 1)
    
    # Per-frame storage
    frame_timestamps = []
    rms_values = []
    flatness_values = []
    harmonic_rms_values = []
    percussive_rms_values = []
    spectral_centroids = []
    zcrs = []
    
    for i in range(n_frames):
        start_sample = i * hop_length_samples
        end_sample = min(start_sample + frame_length_samples, len(audio_signal))
        
        frame = audio_signal[start_sample:end_sample]
        harm_frame = harmonic[start_sample:end_sample]
        perc_frame = percussive[start_sample:end_sample]
        
        # Skip frames that are too short
        if len(frame) < frame_length_samples // 2:
            continue
        
        # Pad frames if needed
        if len(frame) < frame_length_samples:
            frame = np.pad(frame, (0, frame_length_samples - len(frame)), mode='constant')
            harm_frame = np.pad(harm_frame, (0, frame_length_samples - len(harm_frame)), mode='constant')
            perc_frame = np.pad(perc_frame, (0, frame_length_samples - len(perc_frame)), mode='constant')
        
        # Frame timestamp
        frame_timestamps.append(i * hop_length_sec)
        
        # RMS energy (for VAD and features)
        rms = float(np.sqrt(np.mean(frame ** 2)))
        rms_values.append(rms)
        
        # Harmonic and Percussive RMS
        harm_rms = float(np.sqrt(np.mean(harm_frame ** 2)))
        perc_rms = float(np.sqrt(np.mean(perc_frame ** 2)))
        harmonic_rms_values.append(harm_rms)
        percussive_rms_values.append(perc_rms)
        
        # Spectral flatness - KEY FEATURE
        # Low for pure voice (energy in harmonics), high for music (broadband)
        flatness = librosa.feature.spectral_flatness(y=frame)
        flatness_values.append(float(np.mean(flatness)))
        
        # Spectral centroid (for features output)
        centroid = librosa.feature.spectral_centroid(y=frame, sr=sr)
        spectral_centroids.append(float(np.mean(centroid)))
        
        # Zero-crossing rate (for features output)
        zcr = librosa.feature.zero_crossing_rate(frame)
        zcrs.append(float(np.mean(zcr)))
    
    # Convert to numpy arrays
    frame_timestamps = np.array(frame_timestamps)
    rms_values = np.array(rms_values)
    flatness_values = np.array(flatness_values)
    harmonic_rms_values = np.array(harmonic_rms_values)
    percussive_rms_values = np.array(percussive_rms_values)
    spectral_centroids = np.array(spectral_centroids)
    zcrs = np.array(zcrs)
    
    actual_n_frames = len(rms_values)
    
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
    
    # ==========================================================================
    # STEP 3: VOICE ACTIVITY DETECTION (VAD)
    # ==========================================================================
    # Use top 40% of RMS frames as "voice active" - this naturally excludes
    # silence and breath without arbitrary thresholds
    # (Changed from 60% to avoid including too many low-energy frames)
    rms_threshold = np.percentile(rms_values, 60)  # Top 40% = above 60th percentile
    voice_active_mask = rms_values >= rms_threshold
    
    # Also exclude warmup (first 1.0s) and end artifacts (last 5%)
    warmup_time = 1.0
    end_threshold = total_duration * 0.95
    
    valid_mask = (
        voice_active_mask & 
        (frame_timestamps >= warmup_time) & 
        (frame_timestamps < end_threshold)
    )
    
    valid_indices = np.where(valid_mask)[0]
    
    if len(valid_indices) == 0:
        return {
            "verdict": "safe",
            "confidence": 0.0,
            "duration": round(total_duration, 4),
            "summary": "No suspicious sounds detected.",
            "segments": [],
            "features": {
                "spectral_centroid_mean": round(float(np.mean(spectral_centroids)), 4),
                "zcr_mean": round(float(np.mean(zcrs)), 4),
                "rms_mean": round(float(np.mean(rms_values)), 4)
            }
        }
    
    # ==========================================================================
    # STEP 4: COMPUTE BASELINE STATISTICS ON VOICE-ACTIVE FRAMES
    # ==========================================================================
    valid_flatness = flatness_values[valid_mask]
    valid_harm_rms = harmonic_rms_values[valid_mask]
    valid_perc_rms = percussive_rms_values[valid_mask]
    valid_centroids = spectral_centroids[valid_mask]
    
    # Median values as baseline (robust to outliers)
    median_flatness = np.median(valid_flatness)
    median_centroid = np.median(valid_centroids)
    
    # Percussive ratio: perc_rms / (harm_rms + epsilon)
    percussive_ratios = percussive_rms_values / (harmonic_rms_values + 1e-8)
    valid_perc_ratios = percussive_ratios[valid_mask]
    median_perc_ratio = np.median(valid_perc_ratios)
    
    logger.info(f"Baseline stats: median_centroid={median_centroid:.2f}Hz, median_flatness={median_flatness:.6f}, median_perc_ratio={median_perc_ratio:.6f}")
    
    # ==========================================================================
    # DIAGNOSTIC REPORT - Print feature statistics for calibration
    # ==========================================================================
    print(f"=== DIAGNOSTIC REPORT ===")
    print(f"Total frames: {len(frame_timestamps)}")
    print(f"Voice active frames: {sum(voice_active_mask)}")
    print(f"median_centroid: {median_centroid:.2f} Hz")
    print(f"p90_centroid: {np.percentile(spectral_centroids, 90):.2f} Hz")
    print(f"p95_centroid: {np.percentile(spectral_centroids, 95):.2f} Hz")
    print(f"median_flatness: {median_flatness:.6f}")
    print(f"median_perc_ratio: {median_perc_ratio:.6f}")
    print(f"max_flatness: {np.max(flatness_values):.6f}")
    print(f"max_perc_ratio: {np.max(percussive_ratios):.6f}")
    print(f"p75_flatness: {np.percentile(flatness_values, 75):.6f}")
    print(f"p90_flatness: {np.percentile(flatness_values, 90):.6f}")
    print(f"p95_flatness: {np.percentile(flatness_values, 95):.6f}")
    print(f"p75_perc_ratio: {np.percentile(percussive_ratios, 75):.6f}")
    print(f"p90_perc_ratio: {np.percentile(percussive_ratios, 90):.6f}")
    print(f"p95_perc_ratio: {np.percentile(percussive_ratios, 95):.6f}")
    
    # ==========================================================================
    # STEP 5: THREE-SIGNAL ANOMALY DETECTION
    # ==========================================================================
    # A frame is suspicious if AT LEAST 2 of these 3 signals are triggered:
    #
    # SIGNAL 1 - Spectral Centroid (most reliable):
    #   centroid > 2.5x median_centroid AND centroid > 2500 Hz
    #   Rationale: pure voice sits at 1200-2000 Hz, music adds high-freq content
    #
    # SIGNAL 2 - Spectral Flatness:
    #   flatness > 4x median_flatness AND flatness > 0.15
    #   Rationale: pure voice is 0.02-0.08, music > 0.15
    #
    # SIGNAL 3 - Percussive Ratio:
    #   perc_ratio > 5x median_perc_ratio AND percussive_rms > 0.01
    #   Rationale: pure recitation has no drums/beats
    
    centroid_ratio_threshold = 2.5
    centroid_absolute_floor = 2500  # Hz
    flatness_ratio_threshold = 4.0
    flatness_absolute_floor = 0.15
    perc_ratio_threshold = 5.0
    perc_absolute_floor = 0.01
    
    flagged_frames = []
    frame_signals = []  # Track which signals triggered per frame
    
    # Counters for diagnostics
    frames_flagged_centroid = 0
    frames_flagged_flatness = 0
    frames_flagged_perc = 0
    frames_flagged_2plus = 0
    
    for i in valid_indices:
        signals_triggered = 0
        triggered_signals = []
        
        # SIGNAL 1: Spectral Centroid
        centroid_val = spectral_centroids[i]
        centroid_ratio = centroid_val / (median_centroid + 1e-10)
        centroid_suspicious = (centroid_ratio > centroid_ratio_threshold and 
                               centroid_val > centroid_absolute_floor)
        if centroid_suspicious:
            signals_triggered += 1
            triggered_signals.append('centroid')
            frames_flagged_centroid += 1
        
        # SIGNAL 2: Spectral Flatness
        flatness_val = flatness_values[i]
        flatness_ratio = flatness_val / (median_flatness + 1e-10)
        flatness_suspicious = (flatness_ratio > flatness_ratio_threshold and 
                               flatness_val > flatness_absolute_floor)
        if flatness_suspicious:
            signals_triggered += 1
            triggered_signals.append('flatness')
            frames_flagged_flatness += 1
        
        # SIGNAL 3: Percussive Ratio
        perc_ratio = percussive_ratios[i] / (median_perc_ratio + 1e-10)
        perc_suspicious = (perc_ratio > perc_ratio_threshold and 
                          percussive_rms_values[i] > perc_absolute_floor)
        if perc_suspicious:
            signals_triggered += 1
            triggered_signals.append('perc')
            frames_flagged_perc += 1
        
        # Require 2-of-3 signals for flagging (corroborating evidence)
        if signals_triggered >= 2:
            flagged_frames.append(i)
            frame_signals.append({
                'index': i,
                'signals': triggered_signals,
                'centroid': centroid_val,
                'flatness': flatness_val,
                'perc_ratio': percussive_ratios[i]
            })
            frames_flagged_2plus += 1
    
    print(f"frames_flagged_centroid: {frames_flagged_centroid}")
    print(f"frames_flagged_flatness: {frames_flagged_flatness}")
    print(f"frames_flagged_perc: {frames_flagged_perc}")
    print(f"frames_flagged_2plus_signals: {frames_flagged_2plus}")
    print(f"=========================")
    
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
                "rms_mean": round(float(np.mean(rms_values)), 4)
            }
        }
    
    flagged_frames = np.array(flagged_frames)
    logger.info(f"Flagged {len(flagged_frames)} frames with 2+ signals")
    
    # ==========================================================================
    # STEP 6: SEGMENT MERGING
    # ==========================================================================
    # Merge consecutive flagged frames within 1.0s gap
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
    
    # ==========================================================================
    # STEP 7: BUILD RESULT SEGMENTS WITH THREE-SIGNAL SCORING
    # ==========================================================================
    # New scoring formula:
    #   signals_triggered = count of signals flagged (1, 2, or 3)
    #   base_score = signals_triggered / 3.0
    #   For each triggered signal, compute excess:
    #     centroid_excess = centroid / 2500
    #     flatness_excess = flatness / 0.15
    #     perc_excess = perc_ratio / median_perc_ratio / 5
    #   score = min(1.0, base_score * mean(excess values))
    
    result_segments = []
    segment_scores = []
    
    min_segment_duration = 0.5  # Minimum 0.5 seconds
    verdict_threshold = 0.55  # Score threshold for suspicious verdict
    
    # Build lookup for frame signals
    frame_signals_lookup = {fs['index']: fs for fs in frame_signals}
    
    for start_frame, end_frame in segments:
        start_time = round(start_frame * hop_length_sec, 4)
        end_time = round((end_frame + 1) * hop_length_sec + (frame_length_sec - hop_length_sec), 4)
        end_time = min(end_time, round(total_duration, 4))
        
        # Filter out short segments
        segment_duration = end_time - start_time
        if segment_duration < min_segment_duration:
            continue
        
        # Calculate segment score using three-signal weighted formula
        seg_scores = []
        seg_signal_counts = {'centroid': 0, 'flatness': 0, 'perc': 0}
        
        for fi in range(start_frame, end_frame + 1):
            if fi in frame_signals_lookup:
                fs = frame_signals_lookup[fi]
                signals_triggered = len(fs['signals'])
                base_score = signals_triggered / 3.0
                
                excess_values = []
                for sig in fs['signals']:
                    if sig == 'centroid':
                        excess_values.append(fs['centroid'] / centroid_absolute_floor)
                        seg_signal_counts['centroid'] += 1
                    elif sig == 'flatness':
                        excess_values.append(fs['flatness'] / flatness_absolute_floor)
                        seg_signal_counts['flatness'] += 1
                    elif sig == 'perc':
                        excess_values.append(fs['perc_ratio'] / (median_perc_ratio + 1e-10) / perc_ratio_threshold)
                        seg_signal_counts['perc'] += 1
                
                if excess_values:
                    frame_score = min(1.0, base_score * np.mean(excess_values))
                    seg_scores.append(frame_score)
        
        if not seg_scores:
            continue
        
        segment_score = np.mean(seg_scores)
        
        # Only include segments with score >= verdict threshold
        if segment_score < verdict_threshold:
            continue
        
        segment_scores.append(segment_score)
        
        # Determine label based on which signal dominates in the segment
        dominant_signal = max(seg_signal_counts, key=seg_signal_counts.get)
        
        # Check if flatness spike is narrow-band (potential subliminal)
        seg_centroid_std = np.std(spectral_centroids[start_frame:end_frame + 1])
        narrow_band = seg_centroid_std < 200
        
        if dominant_signal == 'flatness' and narrow_band and seg_signal_counts['perc'] == 0:
            label = "subliminal"
        elif dominant_signal == 'perc':
            label = "music_overlay"  # Drums/beats detected
        elif dominant_signal == 'centroid' or dominant_signal == 'flatness':
            label = "music_overlay"  # Tonal music detected (high centroid or flatness)
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
    
    # ==========================================================================
    # STEP 8: FINAL VERDICT
    # ==========================================================================
    n_segments = len(result_segments)
    confidence = float(np.mean(segment_scores)) if segment_scores else 0.0
    
    # Build summary string
    if n_segments == 0:
        summary = "No suspicious sounds detected."
    elif n_segments == 1:
        summary = f"1 suspicious segment found at {result_segments[0]['start_formatted']}."
    else:
        summary = f"{n_segments} suspicious segments found, first at {result_segments[0]['start_formatted']}."
    
    verdict = "suspicious" if n_segments > 0 else "safe"
    
    logger.info(f"Analysis complete: {verdict}, {n_segments} segments, confidence={confidence:.4f}")
    
    return {
        "verdict": verdict,
        "confidence": round(confidence, 4),
        "duration": round(total_duration, 4),
        "summary": summary,
        "segments": result_segments,
        "features": {
            "spectral_centroid_mean": round(float(np.mean(spectral_centroids)), 4),
            "zcr_mean": round(float(np.mean(zcrs)), 4),
            "rms_mean": round(float(np.mean(rms_values)), 4)
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
