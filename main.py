import io
import re
import tempfile
import os

import librosa
import numpy as np
import yt_dlp
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydub import AudioSegment
from typing import Optional
from urllib.parse import urlparse

app = FastAPI(title="Audio Analysis API")

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


# Regex that matches the most common YouTube URL formats:
#   https://www.youtube.com/watch?v=VIDEO_ID
#   https://youtu.be/VIDEO_ID
#   https://youtube.com/shorts/VIDEO_ID
_YOUTUBE_URL_RE = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)"
    r"[\w\-]{11}",
    re.IGNORECASE,
)


def _is_youtube_url(value: str) -> bool:
    """Return True if *value* looks like a YouTube video URL."""
    return bool(_YOUTUBE_URL_RE.search(value))


def _download_youtube_audio(youtube_url: str) -> str:
    """Download the audio track of a YouTube video and return a WAV file path.

    Steps:
        1. Use yt-dlp to download the best audio-only stream to a temp file
           (yt-dlp will pick m4a/webm/mp4 depending on what YouTube offers).
        2. Convert the downloaded file to WAV with pydub (which calls ffmpeg).
        3. Delete the intermediate download file.
        4. Return the path to the WAV file (caller is responsible for cleanup).

    Raises:
        RuntimeError: if the download or conversion fails.
    """
    # Create a temporary directory to hold the downloaded audio
    tmp_dir = tempfile.mkdtemp()
    # yt-dlp output template – we let it choose the extension
    output_template = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        # Download only audio; prefer m4a → mp4 → best available
        "format": "bestaudio/best",
        "outtmpl": output_template,
        # Do not print download progress to stdout
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as exc:
        raise RuntimeError(f"yt-dlp download failed: {exc}") from exc

    # Find the file yt-dlp actually wrote (extension varies)
    downloaded_files = [
        os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)
    ]
    if not downloaded_files:
        raise RuntimeError("yt-dlp did not produce any output file.")

    downloaded_path = downloaded_files[0]

    # Convert the downloaded audio file to WAV so librosa can read it
    wav_path = os.path.join(tmp_dir, "audio.wav")
    try:
        audio_segment = AudioSegment.from_file(downloaded_path)
        audio_segment.export(wav_path, format="wav")
    except Exception as exc:
        raise RuntimeError(f"Audio conversion to WAV failed: {exc}") from exc
    finally:
        # Remove the intermediate download file regardless of success
        if os.path.exists(downloaded_path):
            os.remove(downloaded_path)

    return wav_path


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

        # --- YouTube URL handling ---
        if _is_youtube_url(url):
            wav_path = None
            try:
                # Download the audio track and convert it to WAV
                wav_path = _download_youtube_audio(url)
                result = _analyze_audio(wav_path)
            except RuntimeError as exc:
                return JSONResponse(
                    status_code=500,
                    content={"error": str(exc)},
                )
            except Exception as exc:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"YouTube analysis failed: {exc}"},
                )
            finally:
                # Always clean up the temporary WAV file and its directory
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
                    tmp_dir = os.path.dirname(wav_path)
                    if os.path.isdir(tmp_dir):
                        try:
                            os.rmdir(tmp_dir)
                        except OSError:
                            pass  # directory not empty — leave it

            return result

        # Non-YouTube URL: return the URL as-is (existing behaviour)
        return {"source": "url", "url": url}

    return JSONResponse(
        status_code=400,
        content={"error": "Please provide an audio file or a YouTube URL."},
    )
