# Quran Shield – Audio Analysis API

A FastAPI backend that accepts an uploaded audio file or a YouTube URL, extracts 14 acoustic features using [librosa](https://librosa.org/), and classifies the audio as **music** or **quran/speech** using a hand-calibrated multi-feature weighted scorer.

A zero-dependency vanilla-JS frontend is bundled at `/app`.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 + |
| System `ffmpeg` binary | any recent version |

> **Important:** `pydub` and `yt-dlp` both rely on the **system** `ffmpeg`/`ffprobe` binaries.  
> Install them separately before running the server:
> ```bash
> # Debian / Ubuntu
> sudo apt install ffmpeg
>
> # macOS (Homebrew)
> brew install ffmpeg
>
> # Windows – download from https://ffmpeg.org/download.html
> ```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Running the Server

```bash
uvicorn main:app --reload
```

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/app` | Web frontend (upload file or paste YouTube URL) |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc API reference |

---

## API Endpoint

### `POST /analyze`

Accepts `multipart/form-data` with **at least one** of:

| Field | Type | Description |
|---|---|---|
| `file` | file | Audio file (any format ffmpeg can decode: mp3, wav, ogg, m4a, …) |
| `url` | string | YouTube URL |

#### Success response `200`

```json
{
  "source":     "file",
  "filename":   "recording.mp3",
  "prediction": "music",
  "confidence": 0.742,
  "features": {
    "mfcc_mean":          -123.4567,
    "mfcc_std":            34.1234,
    "mfcc_delta_mean":      2.3456,
    "spectral_centroid":  3241.8,
    "spectral_bandwidth": 2187.3,
    "spectral_rolloff":   6543.2,
    "spectral_contrast":    28.9,
    "chroma_mean":          0.4312,
    "chroma_std":           0.2134,
    "zcr":                  0.0923,
    "rms":                  0.1045,
    "tempo":              120.0,
    "onset_mean":           0.8712,
    "onset_std":            0.9344
  },
  "reasoning": {
    "spectral_centroid": {"hz": 3241.8, "vote": 2.5},
    "chroma_std":        {"value": 0.2134, "vote": 2.0},
    "tempo":             {"bpm": 120.0,  "vote": 2.0}
  }
}
```

For a YouTube URL request, `source` is `"youtube"` and `url` is included instead of `filename`.

#### Error responses

| Status | Meaning |
|---|---|
| `400` | Neither `file` nor `url` was provided; or file is empty |
| `422` | Audio could not be decoded; or URL is not a valid http/https URL |
| `500` | Analysis failed (internal error) |

---

## Example

```bash
# Upload a local file
curl -X POST http://127.0.0.1:8000/analyze \
     -F "file=@audio.mp3"

# Analyze a YouTube video
curl -X POST http://127.0.0.1:8000/analyze \
     -F "url=https://www.youtube.com/watch?v=example"
```

---

## Classifier

The classifier is a **rule-based multi-feature weighted scorer** that assigns signed votes to 8 acoustic features.  A positive total score → `"music"`;  zero or negative → `"quran/speech"`.

| Feature | Weight | Music signal |
|---|---|---|
| Spectral centroid | HIGH | > 2 500 Hz |
| Chroma std | HIGH | > 0.16 |
| Tempo | HIGH | > 70 BPM |
| Onset strength std | MEDIUM | > 0.5 |
| Spectral contrast | MEDIUM | > 20 dB |
| MFCC delta mean | MEDIUM | > 2.0 |
| Spectral rolloff | MEDIUM | > 4 000 Hz |
| Zero-crossing rate | LOW | > 0.08 |

To replace this with a trained model, fit an `sklearn` classifier on the `features` dict returned by `extract_features()` and call it inside `classify_audio()`.
