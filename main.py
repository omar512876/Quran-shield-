import io
import tempfile
import os

import librosa
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydub import AudioSegment
from typing import Optional
from urllib.parse import urlparse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Audio Analysis API")

# ── Added by gbt-5.2  ──
# Serve frontend folder at root URL
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Allow the local frontend to call this API from any origin.
# This is safe for a local development environment.
# In production, replace ["*"] with your actual frontend origin, e.g.:
#   allow_origins=["https://your-frontend-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Spectral centroid threshold (in Hz) for music vs. speech classification.
# Typical speech sits below ~2,000 Hz while music tends to be higher.
MUSIC_CENTROID_THRESHOLD_HZ = 2000.0


def _is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except ValueError:
        return False


def _analyze_audio(wav_path: str) -> dict:
    """Load a WAV file with librosa and extract audio features.

    Returns a dict with:
        - spectral_centroid: mean spectral centroid in Hz
        - zcr: mean zero-crossing rate
        - prediction: 'music' or 'speech'
    """
    # Load the WAV file (mono, native sample rate)
    y, sr = librosa.load(wav_path, sr=None, mono=True)

    # Extract spectral centroid (shape: 1 × frames) and take the mean
    centroid_frames = librosa.feature.spectral_centroid(y=y, sr=sr)
    mean_centroid = float(np.mean(centroid_frames))

    # Extract zero-crossing rate (shape: 1 × frames) and take the mean
    zcr_frames = librosa.feature.zero_crossing_rate(y)
    mean_zcr = float(np.mean(zcr_frames))

    # Simple classification: high spectral centroid → music, else → speech
    prediction = "music" if mean_centroid > MUSIC_CENTROID_THRESHOLD_HZ else "speech"

    return {
        "prediction": prediction,
        "details": {
            "spectral_centroid": mean_centroid,
            "zcr": mean_zcr,
        },
    }


@app.post("/analyze")
async def analyze(
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
):
    if file is not None:
        # Read the uploaded bytes
        try:
            audio_bytes = await file.read()
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to read uploaded file: {exc}"},
            )

        if not audio_bytes:
            return JSONResponse(
                status_code=400,
                content={"error": "Uploaded file is empty."},
            )

        # Convert the audio to WAV using pydub (relies on ffmpeg under the hood)
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as exc:
            return JSONResponse(
                status_code=422,
                content={"error": f"Could not decode audio file: {exc}"},
            )

        # Write the converted WAV to a temporary file so librosa can read it
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                audio_segment.export(tmp_path, format="wav")

            result = _analyze_audio(tmp_path)
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"error": f"Audio analysis failed: {exc}"},
            )
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        return result

    if url is not None:
        if not _is_valid_url(url):
            return JSONResponse(
                status_code=422,
                content={"error": "The provided URL is not valid."},
            )
        return {"source": "url", "url": url}

    return JSONResponse(
        status_code=400,
        content={"error": "Please provide an audio file or a YouTube URL."},
    )
