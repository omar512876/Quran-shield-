# Quran Shield - Quick Setup Guide

## 🚀 Get Started in 2 Minutes!

This project is now **READY TO RUN** with zero manual configuration!

---

## Prerequisites

- **Python 3.9+** only!  
  (No need to install FFmpeg - it's bundled automatically!)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/omar512876/Quran-shield-.git
cd Quran-shield-

# 2. Install dependencies (this includes bundled FFmpeg!)
cd backend
pip install -r requirements.txt

# 3. Run the application
python -m uvicorn app.main:app --reload
```

That's it! Open your browser to **http://localhost:8000/app**

---

## What You'll See

```
INFO - Quran Shield - Audio Analysis API v2.0.0 starting...
INFO - Debug mode: False
INFO - CORS origins: ['*']
⚠️  WARNING: CORS is open to all origins. Set CORS_ORIGINS in .env for production.
INFO - Initializing AudioAnalyzer...
INFO - ✅ Using imageio-ffmpeg bundled binary: /path/to/ffmpeg
INFO - ✅ FFmpeg configured successfully
INFO - FeatureExtractor initialized: sample_rate=22050, n_mfcc=13
INFO - ✅ YouTubeDownloader initialized with ffmpeg support
INFO - ✅ AudioAnalyzer initialized in 0.45s
INFO - ✅ AudioAnalyzer initialized and cached
INFO - ✅ Frontend mounted at /app from /path/to/frontend
INFO - Application startup complete.
```

---

## Available Endpoints

- **Web UI**: http://localhost:8000/app
- **API Documentation**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health

---

## Test It Out

### Upload a File:
1. Go to http://localhost:8000/app
2. Click "Choose File"
3. Select an audio file (MP3, WAV, etc.)
4. Click "Analyze Audio"

### Or Use a YouTube URL:
1. Paste a YouTube URL (e.g., `https://youtube.com/watch?v=...`)
2. Click "Analyze Audio"

---

## Example API Call

```bash
# Analyze a file
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@test.mp3"

# Analyze YouTube URL
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"
```

---

## Response Example

```json
{
  "source": "file",
  "filename": "test.mp3",
  "prediction": "music",
  "confidence": 0.847,
  "processing_time_seconds": 1.23,
  "features": {
    "spectral_centroid": 3241.8,
    "tempo": 120.0,
    "chroma_std": 0.2134
  },
  "reasoning": {
    "spectral_centroid": {"value": 3241.8, "vote": 2.5},
    "tempo": {"value": 120.0, "vote": 2.0}
  }
}
```

---

## Optional Configuration

Create `backend/.env` to customize:

```env
# Server
HOST=0.0.0.0
PORT=8000

# CORS - Set to your domain in production!
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=INFO

# Limits
MAX_FILE_SIZE_MB=50
```

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the backend directory
cd backend
pip install -r requirements.txt
```

### Port already in use
```bash
# Use a different port
uvicorn app.main:app --port 8001
```

### FFmpeg errors (rare)
```bash
# Verify imageio-ffmpeg
python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"

# Should print path to FFmpeg binary
```

---

## Next Steps

- ✅ Read the full [README.md](README.md) for detailed documentation
- ✅ See [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) for all enhancements
- ✅ Check `/docs` endpoint for interactive API documentation
- ✅ Deploy to production (see README for production setup)

---

**Everything is pre-configured and ready to go!**  
**No manual FFmpeg installation, no complex setup - just install and run!**

Made with ❤️ for the Muslim community
