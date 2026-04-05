# Quran Shield

Audio analysis API that detects suspicious background sounds (music, subliminal audio) in audio files and YouTube videos.

## How It Works

1. **Input**: Upload an audio file or provide a YouTube URL
2. **Preprocessing**: Audio is converted to mono WAV and normalized
3. **Windowed Analysis**: Audio is divided into 0.5s overlapping frames; features (spectral centroid, RMS energy, zero-crossing rate, MFCCs) are extracted per frame
4. **Output**: Returns verdict (safe/suspicious), confidence score, and flagged segments with timestamps

## Requirements

- Python 3.9+
- FFmpeg must be installed separately (or will auto-download on first run)

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running

```bash
# Option 1: Using start script
python start.py

# Option 2: Using uvicorn directly
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Web UI at `http://localhost:8000/app`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173,http://localhost:3000` |
| `PORT` | Server port | `8000` |
| `MAX_FILE_SIZE_MB` | Maximum upload size | `50` |

## API Reference

### POST /api/analyze

Submit audio for analysis. Accepts either a file upload or YouTube URL.

**Request (file upload):**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@audio.mp3"
```

**Request (YouTube URL):**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=VIDEO_ID"
```

**Response (202 Accepted):**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing"
}
```

### GET /api/result/{task_id}

Poll for analysis results.

**Response (200 OK - completed):**
```json
{
  "success": true,
  "status": "done",
  "verdict": "suspicious",
  "confidence": 0.8731,
  "duration": 124.5,
  "summary": "2 suspicious segments found, first at 0:12.",
  "segments": [
    {
      "start": 12.4,
      "end": 14.1,
      "start_formatted": "0:12",
      "end_formatted": "0:14",
      "score": 0.87,
      "label": "music_overlay"
    }
  ],
  "features": {
    "spectral_centroid_mean": 1823.4521,
    "zcr_mean": 0.0421,
    "rms_mean": 0.0318
  }
}
```

**Response (202 Accepted - still processing):**
```json
{
  "success": true,
  "status": "processing"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Task not found"
}
```

## Running Tests

```bash
cd backend
pytest
```

## License

MIT
