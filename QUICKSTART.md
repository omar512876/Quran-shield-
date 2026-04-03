# 🚀 QUICK START GUIDE

## For Impatient Developers 😉

### 1️⃣ Install (30 seconds)
```bash
cd Quran-shield-/backend
pip install -r requirements.txt
```

### 2️⃣ Run (5 seconds)
```bash
cd Quran-shield-
python start.py
```

### 3️⃣ Use (Instant)
Open browser: **http://localhost:8000/app**

---

## 📦 What You Get

| URL | What It Does |
|-----|--------------|
| http://localhost:8000/app | 🌐 Web Interface (Upload + Analyze) |
| http://localhost:8000/docs | 📖 Interactive API Docs (Swagger) |
| http://localhost:8000/redoc | 📚 API Reference (ReDoc) |
| http://localhost:8000/health | ✅ Health Check |

---

## 🎯 Quick Examples

### Web Interface
1. Go to http://localhost:8000/app
2. Upload audio file OR paste YouTube URL
3. Click "Analyze Audio"
4. Get instant results ✨

### API (cURL)
```bash
# Analyze audio file
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@myaudio.mp3"

# Analyze YouTube video
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"
```

### API (Python)
```python
import requests

# Analyze file
with open("audio.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/analyze",
        files={"file": f}
    )
    print(response.json())

# Analyze YouTube
response = requests.post(
    "http://localhost:8000/api/analyze",
    data={"url": "https://www.youtube.com/watch?v=EXAMPLE"}
)
print(response.json())
```

### API (JavaScript)
```javascript
// Analyze file
const formData = new FormData();
formData.append('file', audioFileInput.files[0]);

const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  body: formData
});
const result = await response.json();
console.log(result);
```

---

## 🎨 Response Format

```json
{
  "source": "file",
  "filename": "audio.mp3",
  "prediction": "music",          // or "quran/speech"
  "confidence": 0.847,             // 0.0 to 1.0
  "features": {
    "spectral_centroid": 3241.8,   // Hz
    "tempo": 120.0,                 // BPM
    "chroma_std": 0.2134,          // Harmonic variation
    // ... 11 more features
  },
  "reasoning": {
    "spectral_centroid": {
      "value": 3241.8,
      "vote": 2.5                   // Positive = music
    },
    "tempo": {
      "value": 120.0,
      "vote": 2.0
    }
    // ... more features
  }
}
```

---

## ⚙️ Configuration (Optional)

Create `backend/.env`:
```env
PORT=8000
DEBUG=False
CORS_ORIGINS=*
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
```

---

## ❓ Troubleshooting

### "Module not found"
```bash
pip install -r backend/requirements.txt
```

### "ffmpeg not found"
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
Download from https://ffmpeg.org/download.html
```

### Port already in use
```bash
# Change port in .env or:
uvicorn app.main:app --port 8080
```

---

## 📊 Interpreting Results

| Prediction | Meaning |
|------------|---------|
| **music** | Audio contains musical instruments, beats, or background music |
| **quran/speech** | Pure speech/recitation without music |

| Confidence | Interpretation |
|------------|----------------|
| > 0.8 | Very confident |
| 0.5 - 0.8 | Confident |
| < 0.5 | Less certain (borderline case) |

**Key Features to Watch:**
- **Spectral Centroid > 2500 Hz** → Likely music
- **Tempo > 100 BPM** → Likely music
- **Chroma Std > 0.16** → Likely music

---

## 🔥 Pro Tips

1. **Better accuracy with longer clips** (30+ seconds recommended)
2. **MP3/WAV work best** (but any format ffmpeg supports works)
3. **YouTube URLs** are automatically converted to audio
4. **Check reasoning** field to see why decision was made
5. **Confidence score** indicates certainty level

---

## 🆘 Need More Help?

- 📖 Read the full [README.md](README.md)
- 📋 Check the [AUDIT_REPORT.md](AUDIT_REPORT.md) for detailed explanations
- 🐛 Open an issue on GitHub
- 📧 Contact the maintainers

---

**That's it! You're ready to detect music in Quran recitations! 🎉**
