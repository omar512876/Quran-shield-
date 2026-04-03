# Quran Shield - Quick Reference

One-page reference for common tasks and commands.

---

## 🚀 Quick Start Commands

### Local Development
```bash
# Clone and setup
git clone https://github.com/omar512876/Quran-shield-.git
cd Quran-shield-/backend
pip install -r requirements.txt

# Run server
python -m uvicorn app.main:app --reload

# Access
# Web UI: http://localhost:8000/app
# API Docs: http://localhost:8000/docs
```

### Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🌐 Cloud Deployment

### Render
```bash
# Push to GitHub, then:
# 1. Go to render.com
# 2. New Web Service
# 3. Connect repo
# 4. Deploy (auto-detects render.yaml)
```

### Railway
```bash
# Push to GitHub, then:
# 1. Go to railway.app
# 2. New Project → Deploy from GitHub
# 3. Select repo → Deploy
```

### Fly.io
```bash
flyctl auth signup
flyctl launch
flyctl deploy
```

### Docker (Any Cloud)
```bash
docker build -t quran-shield .
docker run -p 8000:8000 quran-shield
```

---

## 🧪 Testing

### Local API Testing
```bash
# Health check
curl http://localhost:8000/health

# File upload
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@sample.mp3"

# YouTube URL
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"
```

### Deployment Testing
```bash
python test_deployment.py https://your-app.com
```

---

## 📁 Project Structure

```
Quran-shield-/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment config
│   │   ├── routes/
│   │   │   ├── audio.py            # Main analysis endpoint
│   │   │   └── health.py           # Health check
│   │   ├── services/
│   │   │   ├── audio_analyzer.py   # Main orchestrator
│   │   │   ├── feature_extractor.py # Audio features
│   │   │   ├── classifier.py       # Classification logic
│   │   │   └── youtube_downloader.py # YouTube handling
│   │   └── utils/
│   │       ├── ffmpeg_manager.py   # FFmpeg auto-download
│   │       ├── ffmpeg_config.py    # FFmpeg configuration
│   │       └── validators.py       # Input validation
│   └── requirements.txt
├── frontend/
│   ├── index.html                  # Original UI
│   └── index_web.html              # Modern web UI
├── Dockerfile                      # Docker container build
├── docker-compose.yml              # Docker compose config
├── render.yaml                     # Render deployment config
├── railway.json                    # Railway deployment config
├── fly.toml                        # Fly.io deployment config
├── vercel.json                     # Vercel deployment config
└── test_deployment.py              # Deployment test suite
```

---

## 🔑 Environment Variables

### Local (.env)
```env
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=DEBUG
CORS_ORIGINS=*
MAX_FILE_SIZE_MB=50
```

### Production
```env
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
MAX_FILE_SIZE_MB=50
```

---

## 🛠️ Common Tasks

### Update Dependencies
```bash
cd backend
pip install --upgrade pip
pip list --outdated
pip install -U package-name
pip freeze > requirements.txt
```

### View Logs
```bash
# Local (stdout)
python -m uvicorn app.main:app --reload

# Docker
docker-compose logs -f

# Render/Railway/Fly
# Check platform dashboard
```

### Restart Service
```bash
# Local: Ctrl+C, then restart

# Docker
docker-compose restart

# Render: Auto-restarts on push

# Fly.io
flyctl apps restart
```

### Check FFmpeg
```bash
# Inside backend/
python -c "from app.utils.ffmpeg_manager import ensure_ffmpeg; print(ensure_ffmpeg())"
```

---

## 📊 API Endpoints

### GET /health
**Response:**
```json
{
  "status": "OK",
  "ffmpeg_available": true
}
```

### POST /api/analyze
**Request (File):**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@audio.mp3"
```

**Request (URL):**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://youtube.com/watch?v=xyz"
```

**Response:**
```json
{
  "success": true,
  "prediction": "quran/speech",
  "confidence": 0.85,
  "source": "file",
  "filename": "audio.mp3",
  "processing_time_seconds": 12.5,
  "features": { ... },
  "reasoning": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Audio too short: 0.3s (minimum 0.5s required)"
}
```

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| FFmpeg not found | Wait for auto-download (40-80s first run) |
| Port already in use | Change PORT in .env or kill process |
| Import errors | `pip install -r requirements.txt` |
| CORS errors | Update CORS_ORIGINS in .env |
| 413 Payload Too Large | Increase MAX_FILE_SIZE_MB |
| Slow YouTube download | Normal for long videos, or timeout |
| Docker build fails | `docker system prune -a` then rebuild |

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `QUICKSTART_GUIDE.md` | 2-minute local setup |
| `CLOUD_DEPLOYMENT_GUIDE.md` | Cloud deployment instructions |
| `DEPLOYMENT_CHECKLIST.md` | Pre/post deployment checklist |
| `WEB_DEPLOYMENT_SUMMARY.md` | Web deployment summary |
| `FFMPEG_AUTO_DOWNLOAD.md` | FFmpeg technical details |
| `IMPROVEMENTS_SUMMARY.md` | All bug fixes and enhancements |
| `CHANGELOG.md` | Version history |

---

## 🔗 Useful Links

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Librosa Docs**: https://librosa.org/doc/latest/index.html
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Render**: https://render.com/docs
- **Railway**: https://docs.railway.app
- **Fly.io**: https://fly.io/docs
- **Docker**: https://docs.docker.com

---

## 💡 Tips & Best Practices

### Development
- Use `--reload` for hot reload during development
- Check `/docs` endpoint for interactive API testing
- Use `LOG_LEVEL=DEBUG` for detailed logs locally

### Production
- Set `DEBUG=False` always
- Use specific CORS_ORIGINS (not "*")
- Enable platform monitoring/alerts
- Keep dependencies updated
- Test deployment with `test_deployment.py`

### Performance
- First request is slow (FFmpeg download)
- Use persistent storage for FFmpeg binaries
- Consider Redis for caching repeated URLs
- Upgrade instance size for heavy traffic

### Security
- Never commit `.env` files
- Use environment secrets for sensitive data
- Validate all user inputs
- Keep file size limits reasonable
- Monitor for abuse/spam

---

## 🎯 Deployment Decision Tree

```
Need to deploy?
│
├─ For testing/personal use?
│  └─ Use Render (free tier) → Easy setup
│
├─ For production (low/medium traffic)?
│  └─ Use Railway → Fast & reliable
│
├─ Need global edge deployment?
│  └─ Use Fly.io → Multi-region
│
├─ Want full control/privacy?
│  └─ Use Docker on VPS → Self-hosted
│
└─ Only quick file analysis (no long videos)?
   └─ Use Vercel → Serverless
```

---

## 📞 Quick Support

1. **Check logs first** - Most issues show in logs
2. **Try locally** - Reproduce issue on local machine
3. **Review docs** - Check relevant documentation file
4. **Test deployment** - Run `test_deployment.py`
5. **GitHub Issues** - Open issue with details

---

**Version**: 2.0 (Web Deployment)
**Last Updated**: January 2025
**License**: MIT
