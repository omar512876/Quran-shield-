import io
import os
import shutil
import tempfile
from typing import Optional
from urllib.parse import urlparse

import librosa
import numpy as np
import yt_dlp
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydub import AudioSegment

app = FastAPI(title="Quran Shield — Audio Analysis API")

# ── Fix: mount frontend at /app, not / (avoids clobbering API routes) ──────────
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

# ── CORS: wildcard OK for local dev, replace in production ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g. ["https://yourdomain.com"] in production
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# Extracts 15+ acoustic features using librosa (100% open source, runs locally).
# ═══════════════════════════════════════════════════════════════════════════════

def extract_features(y: np.ndarray, sr: int) -> dict:
    """
    Extract a rich set of acoustic features from a mono audio signal.

    Returns a flat dict of named floats ready for classification.
    These same features can be used as input to a trained sklearn model
    (see train_model.py).
    """

    # ── MFCCs (Mel-Frequency Cepstral Coefficients) ─────────────────────────
    # Captures timbre and tonal texture. The most discriminative features
    # for speech vs music classification in research literature.
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_mean = float(np.mean(mfccs))
    mfcc_std = float(np.std(mfccs))

    # MFCC delta = rate of change over time.
    # Music has faster, more complex MFCC variation than monotone speech.
    mfcc_delta = librosa.feature.delta(mfccs)
    mfcc_delta_mean = float(np.mean(np.abs(mfcc_delta)))

    # ── Spectral centroid ───────────────────────────────────────────────────
    # The "brightness" of the sound. Music instruments tend to push
    # energy higher than a human voice (especially Quran recitation).
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_centroid = float(np.mean(centroid))

    # ── Spectral bandwidth ──────────────────────────────────────────────────
    # How spread out the spectrum is around the centroid.
    # Music spans a wider frequency range.
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    spectral_bandwidth = float(np.mean(bandwidth))

    # ── Spectral rolloff ────────────────────────────────────────────────────
    # The frequency below which 85% of spectral energy falls.
    # Higher rolloff = more high-frequency content = more likely music.
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
    spectral_rolloff = float(np.mean(rolloff))

    # ── Spectral contrast ───────────────────────────────────────────────────
    # Difference in energy between spectral peaks and valleys.
    # Music has strong harmonic peaks (high contrast).
    # Speech is smoother (lower contrast).
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    spectral_contrast = float(np.mean(contrast))

    # ── Chroma features ─────────────────────────────────────────────────────
    # Pitch class energy distribution (C, C#, D, ..., B).
    # Music has rich, varied chroma patterns.
    # Quran recitation centers on fewer pitch classes.
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_mean = float(np.mean(chroma))
    chroma_std = float(np.std(chroma))

    # ── Zero crossing rate ──────────────────────────────────────────────────
    # How often the signal crosses zero. Higher = noisier / more percussive.
    zcr = librosa.feature.zero_crossing_rate(y)
    zcr_mean = float(np.mean(zcr))

    # ── RMS energy ──────────────────────────────────────────────────────────
    # Average loudness across the clip.
    rms = librosa.feature.rms(y=y)
    rms_mean = float(np.mean(rms))

    # ── Tempo ───────────────────────────────────────────────────────────────
    # Beat tracker. Music has a clear BPM; Quran recitation is arrhythmic.
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo)

    # ── Onset strength ──────────────────────────────────────────────────────
    # Detects sudden energy bursts (drum hits, note onsets).
    # Higher variance in onsets = more rhythmic = more likely music.
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = float(np.mean(onset_env))
    onset_std = float(np.std(onset_env))

    return {
        "mfcc_mean": mfcc_mean,
        "mfcc_std": mfcc_std,
        "mfcc_delta_mean": mfcc_delta_mean,
        "spectral_centroid": spectral_centroid,
        "spectral_bandwidth": spectral_bandwidth,
        "spectral_rolloff": spectral_rolloff,
        "spectral_contrast": spectral_contrast,
        "chroma_mean": chroma_mean,
        "chroma_std": chroma_std,
        "zcr": zcr_mean,
        "rms": rms_mean,
        "tempo": tempo,
        "onset_mean": onset_mean,
        "onset_std": onset_std,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-FEATURE WEIGHTED CLASSIFIER
#
# Each feature casts a signed vote:  positive (+) = music
#                                    negative (−) = quran/speech
#
# Final score > 0 → music   |   score ≤ 0 → quran/speech
#
# This is a hand-calibrated linear scorer — much stronger than a single
# centroid threshold. Replace classify_audio() with a trained sklearn model
# (see train_model.py) once you have labelled data.
# ═══════════════════════════════════════════════════════════════════════════════

def _vote(value: float, thresholds: list[tuple]) -> float:
    """
    Map a scalar value to a vote using a stepwise threshold table.

    thresholds = [(upper_bound, vote), ...] sorted descending.
    The first threshold the value exceeds wins.
    The last entry's vote is the default (catch-all).
    """
    for bound, vote in thresholds:
        if value > bound:
            return vote
    return thresholds[-1][1]


def classify_audio(features: dict) -> tuple[str, float, dict]:
    """
    Run the multi-feature weighted classifier.

    Returns:
        prediction   — "music" or "quran/speech"
        confidence   — float in [0, 1]
        reasoning    — per-feature breakdown for transparency
    """
    score = 0.0
    reasoning = {}

    # ── 1. Spectral centroid ─────────────────────────────────────────────────
    # Weight: HIGH.  Centroid is the strongest single predictor.
    v = _vote(features["spectral_centroid"], [
        (3500, +2.5),
        (2500, +1.5),
        (1800, +0.5),
        (1200, -0.5),
        (-999, -1.5),
    ])
    score += v
    reasoning["spectral_centroid"] = {"hz": round(features["spectral_centroid"], 1), "vote": v}

    # ── 2. Chroma std (harmonic variety) ─────────────────────────────────────
    # Weight: HIGH.  Music spreads energy across pitch classes; Quran does not.
    v = _vote(features["chroma_std"], [
        (0.22, +2.0),
        (0.16, +1.0),
        (0.10,  0.0),
        (-999, -1.0),
    ])
    score += v
    reasoning["chroma_std"] = {"value": round(features["chroma_std"], 4), "vote": v}

    # ── 3. Tempo ─────────────────────────────────────────────────────────────
    # Weight: HIGH.  Music has a clear pulse; Quran recitation is free-form.
    v = _vote(features["tempo"], [
        (100, +2.0),
        (70,  +1.0),
        (50,  +0.5),
        (30,  -0.5),
        (-999, -1.0),
    ])
    score += v
    reasoning["tempo"] = {"bpm": round(features["tempo"], 1), "vote": v}

    # ── 4. Onset strength std ────────────────────────────────────────────────
    # Weight: MEDIUM.  Regular strong beats = music.
    v = _vote(features["onset_std"], [
        (0.8, +1.5),
        (0.5, +0.5),
        (-999, -0.5),
    ])
    score += v
    reasoning["onset_std"] = {"value": round(features["onset_std"], 4), "vote": v}

    # ── 5. Spectral contrast ─────────────────────────────────────────────────
    # Weight: MEDIUM.  Musical harmonics create strong spectral peaks.
    v = _vote(features["spectral_contrast"], [
        (30, +1.5),
        (20, +0.5),
        (10, -0.5),
        (-999, -1.0),
    ])
    score += v
    reasoning["spectral_contrast"] = {"value": round(features["spectral_contrast"], 2), "vote": v}

    # ── 6. MFCC delta (temporal complexity) ──────────────────────────────────
    # Weight: MEDIUM.  Faster MFCC changes = richer temporal structure = music.
    v = _vote(features["mfcc_delta_mean"], [
        (5.0, +1.0),
        (2.0, +0.5),
        (-999, -0.5),
    ])
    score += v
    reasoning["mfcc_delta_mean"] = {"value": round(features["mfcc_delta_mean"], 4), "vote": v}

    # ── 7. Spectral rolloff ──────────────────────────────────────────────────
    # Weight: MEDIUM.  High rolloff = more energy in high frequencies = music.
    v = _vote(features["spectral_rolloff"], [
        (6000, +1.5),
        (4000, +0.5),
        (2500,  0.0),
        (-999, -0.5),
    ])
    score += v
    reasoning["spectral_rolloff"] = {"hz": round(features["spectral_rolloff"], 1), "vote": v}

    # ── 8. Zero crossing rate ─────────────────────────────────────────────────
    # Weight: LOW.  High ZCR may indicate percussion or noise layers.
    v = _vote(features["zcr"], [
        (0.15, +1.0),
        (0.08,  0.0),
        (-999, -0.5),
    ])
    score += v
    reasoning["zcr"] = {"value": round(features["zcr"], 4), "vote": v}

    # ── Confidence: how far from zero (normalised) ───────────────────────────
    max_possible = 13.0  # sum of all maximum positive votes above
    confidence = min(abs(score) / max_possible, 1.0)

    prediction = "music" if score > 0 else "quran/speech"

    return prediction, round(confidence, 3), reasoning


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO LOADING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _is_valid_url(value: str) -> bool:
    try:
        r = urlparse(value)
        return r.scheme in ("http", "https") and bool(r.netloc)
    except ValueError:
        return False


def _analyze_wav(wav_path: str) -> dict:
    """Load a WAV file, extract features, and classify."""
    y, sr = librosa.load(wav_path, sr=None, mono=True)
    features = extract_features(y, sr)
    prediction, confidence, reasoning = classify_audio(features)
    return {
        "prediction": prediction,
        "confidence": confidence,
        "features": {k: round(v, 4) for k, v in features.items()},
        "reasoning": reasoning,
    }


def _download_youtube_to_wav(url: str) -> tuple[str, str]:
    """
    Download the best audio track from a YouTube URL using yt-dlp (open source).
    Returns (path_to_wav, tmp_dir) — caller must clean up tmp_dir.
    """
    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    wav_path = os.path.join(tmp_dir, "audio.wav")
    if not os.path.exists(wav_path):
        raise FileNotFoundError("yt-dlp downloaded the file but WAV conversion failed.")

    return wav_path, tmp_dir


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/analyze")
async def analyze(
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
):
    """
    Analyse an audio clip and classify it as 'music' or 'quran/speech'.

    Accepts:
      - file  (multipart upload)  — any format pydub/ffmpeg can decode
      - url   (form field)        — a YouTube URL

    Returns:
      {
        "source":     "file" | "youtube",
        "prediction": "music" | "quran/speech",
        "confidence": 0.0–1.0,
        "features":   { ... },
        "reasoning":  { feature: { value, vote } }
      }
    """

    # ── Branch 1: file upload ────────────────────────────────────────────────
    if file is not None:
        try:
            audio_bytes = await file.read()
        except Exception as exc:
            return JSONResponse(400, {"error": f"Could not read uploaded file: {exc}"})

        if not audio_bytes:
            return JSONResponse(400, {"error": "Uploaded file is empty."})

        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as exc:
            return JSONResponse(422, {"error": f"Could not decode audio: {exc}"})

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            audio_segment.export(tmp_path, format="wav")
            result = _analyze_wav(tmp_path)
            result["source"] = "file"
            result["filename"] = file.filename
            return result
        except Exception as exc:
            return JSONResponse(500, {"error": f"Analysis failed: {exc}"})
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # ── Branch 2: YouTube URL ────────────────────────────────────────────────
    if url is not None:
        if not _is_valid_url(url):
            return JSONResponse(422, {"error": "URL is not valid (must start with http/https)."})

        tmp_dir = None
        try:
            wav_path, tmp_dir = _download_youtube_to_wav(url)
            result = _analyze_wav(wav_path)
            result["source"] = "youtube"
            result["url"] = url
            return result
        except Exception as exc:
            return JSONResponse(500, {"error": f"YouTube analysis failed: {exc}"})
        finally:
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    # ── Neither provided ─────────────────────────────────────────────────────
    return JSONResponse(400, {"error": "Please provide an audio file or a YouTube URL."})