# Quran Shield – Audio Analysis API

A clean FastAPI backend for audio analysis. Accepts an uploaded audio file or a YouTube URL.

## Requirements

- Python 3.9+

## Installation

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

## Endpoint

### `POST /analyze`

Accepts `multipart/form-data` with at least one of:

| Field  | Type | Description |
|--------|------|-------------|
| `file` | file | Audio file to upload |
| `url`  | string | YouTube URL |

**Responses:**

- File uploaded → `{"source": "file", "filename": "<name>"}`
- URL provided → `{"source": "url", "url": "<url>"}`
- Neither provided → `400 {"error": "Please provide an audio file or a YouTube URL."}`

## Example

```bash
# Upload a file
curl -X POST http://127.0.0.1:8000/analyze \
     -F "file=@audio.mp3"

# Pass a YouTube URL
curl -X POST http://127.0.0.1:8000/analyze \
     -F "url=https://www.youtube.com/watch?v=example"
```
