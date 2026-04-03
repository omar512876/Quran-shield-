# Quran Shield 🛡️

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Quran Shield** is an AI-powered audio analysis tool that detects whether an audio file or YouTube video contains **music** or **pure Quran/speech recitation**. It uses advanced audio processing and machine learning techniques to provide accurate classification.

**✨ ZERO-INSTALL WEB APP**: Deploy to the cloud in minutes with **no manual setup required**! Works as a fully web-based service that users can access from any browser.

---

## 🌐 Use Online (Zero Install)

**Want to skip installation entirely?** Deploy Quran Shield to the cloud and use it as a web app:

### One-Click Cloud Deployment

| Platform | Deployment Time | Free Tier | One-Click Deploy |
|----------|-----------------|-----------|------------------|
| **Render** | ~10 min | ✅ Yes | [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy) |
| **Railway** | ~5 min | ✅ Trial | [Deploy to Railway](https://railway.app/new) |
| **Fly.io** | ~8 min | ✅ Yes | Use CLI: `flyctl launch` |

**See full deployment guide**: [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md)

Once deployed, users can:
- ✅ Access from any device with a web browser
- ✅ No Python, FFmpeg, or any installation needed
- ✅ Paste YouTube URLs or upload audio files instantly
- ✅ Get AI-powered classification in seconds

---

## ✨ Features

- 🌐 **Zero-Install Web App**: Deploy to cloud, use from browser - no installation needed!
- 🎵 **Music Detection**: Identifies musical background in audio
- 📿 **Quran/Speech Classification**: Detects pure recitation without music
- 📁 **File Upload**: Supports MP3, WAV, OGG, M4A, FLAC, AAC, and more
- 🔗 **YouTube Support**: Direct analysis from YouTube URLs
- ⚡ **Automatic FFmpeg**: FFmpeg automatically downloaded - works out of the box!
- 🌍 **Cross-Platform**: Auto-downloads correct binaries for Windows, Linux, and macOS
- 🎯 **High Accuracy**: Multi-feature weighted classifier with 14+ acoustic features
- 🚀 **REST API**: Full-featured API for integration
- 🐳 **Docker Ready**: One command to run in container
- ☁️ **Cloud Deployable**: Ready-to-deploy configs for Render, Railway, Fly.io, Vercel
- 📊 **Detailed Analysis**: Confidence scores and feature breakdowns
- 🔍 **Comprehensive Logging**: Full request and performance tracking
- 🛡️ **Robust Error Handling**: Graceful failure with meaningful error messages
- 📴 **Offline Capable**: After first run, works without internet

---

## 🚀 Quick Start (Local Development)

### Option 1: Traditional Setup

**Prerequisites:** Python 3.9+ only (FFmpeg downloads automatically)

### Installation

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/omar512876/Quran-shield-.git
   cd Quran-shield-
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

**That's it!** On first run, FFmpeg will be automatically downloaded to `backend/bin/ffmpeg/`.

The application will be available at:
- **Web UI**: http://localhost:8000/app
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Option 2: Docker (Recommended for Production)

**Prerequisites:** Docker and Docker Compose

```bash
# Clone repository
git clone https://github.com/omar512876/Quran-shield-.git
cd Quran-shield-

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Access at http://localhost:8000/app
```

**Benefits:**
- ✅ Consistent environment across platforms
- ✅ Easy scaling and deployment
- ✅ Persistent FFmpeg binaries across restarts
- ✅ Production-ready configuration

---

## 📦 Automatic FFmpeg Download

### How It Works

The application includes an intelligent FFmpeg manager that:

1. **First checks** `backend/bin/ffmpeg/` for existing binaries
2. **Falls back** to `imageio-ffmpeg` if installed
3. **Checks** system PATH for installed FFmpeg
4. **Automatically downloads** platform-specific binaries if not found:
   - **Windows**: Downloads from BtbN/FFmpeg-Builds
   - **Linux**: Downloads from BtbN/FFmpeg-Builds  
   - **macOS**: Downloads from evermeet.cx

### What You'll See

On first startup with no FFmpeg:
```
INFO - Detecting FFmpeg binaries...
INFO - FFmpeg not found. Downloading...
INFO - Downloading FFmpeg from https://github.com/BtbN/FFmpeg-Builds/...
INFO - Downloaded to backend/bin/ffmpeg/ffmpeg.zip
INFO - Extracting archive...
INFO - Copied ffmpeg to backend/bin/ffmpeg/ffmpeg
INFO - Copied ffprobe to backend/bin/ffmpeg/ffprobe
INFO - Made ffmpeg executable
INFO - Made ffprobe executable
INFO - ✅ FFmpeg downloaded successfully
INFO - ✅ FFmpeg: /path/to/backend/bin/ffmpeg/ffmpeg
INFO - ✅ FFprobe: /path/to/backend/bin/ffmpeg/ffprobe
```

On subsequent startups:
```
INFO - Detecting FFmpeg binaries...
INFO - ✅ FFmpeg found in project directory
INFO - ✅ FFmpeg: /path/to/backend/bin/ffmpeg/ffmpeg
INFO - ✅ FFprobe: /path/to/backend/bin/ffmpeg/ffprobe
```

### Offline Mode

After the first successful download, the application works completely offline!

---

---

## 🏗️ Architecture

### Backend (Python + FastAPI)
```
backend/
├── app/
│   ├── main.py              # FastAPI app with lifespan management
│   ├── config.py            # Configuration settings
│   ├── routes/              # API endpoints
│   │   ├── audio.py         # Audio analysis routes (with dependency injection)
│   │   └── health.py        # Health check routes
│   ├── services/            # Business logic
│   │   ├── audio_analyzer.py      # Main orchestration (singleton)
│   │   ├── feature_extractor.py   # Feature extraction (enhanced validation)
│   │   ├── classifier.py          # Classification logic (error handling)
│   │   └── youtube_downloader.py  # YouTube handling
│   ├── models/              # Data models
│   │   └── audio.py         # Pydantic models
│   └── utils/               # Utilities
│       ├── ffmpeg_config.py # FFmpeg auto-detection (imageio-ffmpeg)
│       └── validators.py    # Input validation
└── requirements.txt         # Includes imageio-ffmpeg
```

### Frontend (Vanilla HTML/CSS/JS)
```
frontend/
└── index.html               # Single-page application with enhanced UX
```

---

## 📖 API Usage

### Analyze Audio File

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@audio.mp3"
```

### Analyze YouTube URL

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"
```

### Response Example

```json
{
  "source": "file",
  "filename": "audio.mp3",
  "prediction": "music",
  "confidence": 0.847,
  "processing_time_seconds": 1.23,
  "features": {
    "spectral_centroid": 3241.8,
    "tempo": 120.0,
    "chroma_std": 0.2134,
    "mfcc_mean": -123.45,
    ...
  },
  "reasoning": {
    "spectral_centroid": {"value": 3241.8, "vote": 2.5},
    "tempo": {"value": 120.0, "vote": 2.0},
    ...
  }
}
```

---

## 🎯 How It Works

### 1. Feature Extraction
The system extracts **14 acoustic features** using `librosa`:

| Feature | Purpose | Music Indicator |
|---------|---------|-----------------|
| **Spectral Centroid** | Brightness of sound | Higher = more music |
| **Chroma Std** | Harmonic variation | Higher = more music |
| **Tempo** | Rhythmic pulse | Higher = more music |
| **Onset Strength** | Beat detection | Higher variation = more music |
| **Spectral Contrast** | Peak-valley difference | Higher = more music |
| **MFCC Delta** | Timbral changes | Faster = more music |
| **Zero-Crossing Rate** | Noisiness/percussion | Higher = more music |
| And more... | | |

### 2. Classification
A **multi-feature weighted classifier** assigns votes to each feature:
- **Positive votes** → Music characteristics
- **Negative votes** → Speech/Quran characteristics

The final score determines the prediction:
- `Score > 0` → **Music**
- `Score ≤ 0` → **Quran/Speech**

### 3. Confidence Calculation
Confidence is normalized based on how far the score is from the decision boundary.

---

## 🛠️ Troubleshooting

### FFmpeg Download Issues

**Problem**: "FFmpeg not found and auto-download failed"

**Solutions**:

1. **Check internet connection**: The first run requires internet to download FFmpeg
   ```bash
   # Test connection
   curl -I https://github.com
   ```

2. **Manual download**: If auto-download fails, download manually:
   - **Windows**: [FFmpeg Windows Builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - **Linux**: [FFmpeg Linux Builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - **macOS**: [FFmpeg macOS](https://evermeet.cx/ffmpeg/)
   
   Extract and place `ffmpeg` and `ffprobe` in `backend/bin/ffmpeg/`

3. **Use system FFmpeg**: Install FFmpeg system-wide:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   winget install FFmpeg
   ```

4. **Check logs**: Look for detailed error messages:
   ```bash
   tail -f logs/app.log  # if using file logging
   ```

**Problem**: "Permission denied" on Linux/macOS

**Solution**: Make binaries executable:
```bash
chmod +x backend/bin/ffmpeg/ffmpeg
chmod +x backend/bin/ffmpeg/ffprobe
```

### Audio Processing Issues

**Problem**: "Audio appears to be silent or contains no signal"

**Solution**: The audio file may be corrupted, have very low volume, or be in an unsupported format. Try:
- Re-exporting the audio in a standard format (MP3, WAV)
- Increasing the volume
- Testing with a different audio file

**Problem**: "Audio too short: X.XXs (minimum 0.5s required)"

**Solution**: Audio must be at least 0.5 seconds long for analysis. Upload a longer clip.

### YouTube Issues

**Problem**: "Video is too long"

**Solution**: The application limits YouTube videos to 10 minutes to prevent excessive processing. Use a shorter video or clip.

**Problem**: "This video is private or unavailable"

**Solution**: The video may be:
- Deleted or made private
- Age-restricted
- Region-locked
- Copyright-blocked

Try a different video or download the audio manually and upload it as a file.

---

## 🔧 Configuration

Edit `backend/.env` to customize:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (comma-separated origins)
# ⚠️ Set to your domain in production, not "*"
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO

# Audio Processing
MAX_FILE_SIZE_MB=50
```

---

## 📊 Improvement Ideas

### Current: Rule-Based Classifier
The current system uses hand-calibrated thresholds with robust error handling and validation.

### Future: Machine Learning Model

For even better accuracy, you can train a machine learning model. Here's how:

#### Step 1: Collect Labeled Dataset

```python
# Collect samples
music_samples = [...]  # List of music audio files
quran_samples = [...]  # List of Quran recitation files
```

#### Step 2: Extract Features

```python
from backend.app.services import FeatureExtractor, AudioAnalyzer
import librosa
import numpy as np

extractor = FeatureExtractor()

X = []  # Feature vectors
y = []  # Labels (0 = quran, 1 = music)

for audio_file in music_samples:
    signal, sr = librosa.load(audio_file, sr=22050)
    features = extractor.extract_features(signal, sr)
    X.append(list(features.values()))
    y.append(1)

for audio_file in quran_samples:
    signal, sr = librosa.load(audio_file, sr=22050)
    features = extractor.extract_features(signal, sr)
    X.append(list(features.values()))
    y.append(0)

X = np.array(X)
y = np.array(y)
```

#### Step 3: Train ML Classifier

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.2%}")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(model, 'classifier_model.pkl')
```

#### Step 4: Replace AudioClassifier

```python
# backend/app/services/classifier.py

import joblib
import numpy as np

class AudioClassifier:
    def __init__(self):
        self.model = joblib.load('classifier_model.pkl')
    
    def classify(self, features):
        X = np.array([list(features.values())])
        prediction = self.model.predict(X)[0]
        confidence = self.model.predict_proba(X)[0][prediction]
        
        label = "music" if prediction == 1 else "quran/speech"
        return label, confidence, {}
```

#### Step 5: Retrain and Deploy

- Collect more samples over time
- Periodically retrain the model
- Version your models
- A/B test rule-based vs ML classifier

---

## 🛡️ What Was Fixed / Improved

### Original Issues → Solutions:

✅ **Manual FFmpeg installation** → Auto-bundled via imageio-ffmpeg
✅ **No error handling** → Comprehensive validation and meaningful errors  
✅ **Per-request instantiation** → Singleton pattern with dependency injection  
✅ **No logging** → Full request/performance/classification logging  
✅ **File loaded before validation** → Content-Length header check first  
✅ **Double ffmpeg config** → Single initialization passed via constructor  
✅ **CORS wildcard no warning** → Startup warning when CORS="*"  
✅ **Monolithic structure** → Clean modular architecture  
✅ **No health endpoint** → `/health` and `/` endpoints  
✅ **Basic UI** → Enhanced with better UX and error display  
✅ **No type safety** → Pydantic models throughout  
✅ **Hard to test** → Separated services for unit testing  

### New Enhancements:

🎨 **Zero-Setup FFmpeg** with imageio-ffmpeg bundled binaries  
📊 **Processing Time Metrics** in API responses  
🔍 **Audio Validation** (silence detection, minimum duration, format checks)  
⚡ **Performance Logging** (load time, feature extraction time, classification time)  
🛡️ **Edge Case Handling** in feature extraction and classification  
🚨 **Meaningful Error Messages** for all failure scenarios  
📚 **Comprehensive Documentation** with troubleshooting guide  
🔒 **Production Ready** with CORS warnings and security best practices  

---

## 🧪 Testing

### Local Testing

Test the API locally:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with sample audio
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@sample.mp3"

# Test with YouTube URL
curl -X POST http://localhost:8000/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"
```

### Deployment Testing

After deploying to cloud, test your deployment:

```bash
# Install test dependencies
pip install numpy requests

# Run comprehensive test suite
python test_deployment.py https://your-app.onrender.com

# Example output:
# ============================================================
#                  QURAN SHIELD DEPLOYMENT TEST SUITE
# ============================================================
# 
# ✓ Health check passed: OK
# ✓ Error handling tests passed (3/3)
# ✓ File upload analysis succeeded!
# ⚠️ YouTube analysis may timeout on free-tier platforms
# 
# ✅ DEPLOYMENT IS FUNCTIONAL
```

The test suite automatically validates:
- ✅ Health endpoint accessibility
- ✅ Error handling (invalid inputs)
- ✅ File upload processing
- ✅ YouTube URL processing (may timeout on free tiers)
- ✅ API response structure
- ✅ FFmpeg availability

---

## ☁️ Cloud Deployment

### Quick Deploy

Deploy to production cloud platform in minutes with **zero manual setup**:

```bash
# Option 1: Render (Recommended)
# Just push to GitHub and connect in Render dashboard
# render.yaml is pre-configured

# Option 2: Docker to any cloud
docker build -t quran-shield .
docker push your-registry/quran-shield
# Deploy to your platform

# Option 3: Railway
# Connect GitHub repo, Railway auto-detects configuration

# Option 4: Fly.io
flyctl launch
flyctl deploy
```

**Full deployment guide**: See [CLOUD_DEPLOYMENT_GUIDE.md](CLOUD_DEPLOYMENT_GUIDE.md) for:
- Step-by-step instructions for each platform
- Environment variable configuration
- Custom domain setup
- Performance optimization tips
- Cost estimates and free tier limits
- Troubleshooting common deployment issues

### Deployment Files Included

This repository includes ready-to-deploy configurations:

- `render.yaml` - Render platform configuration
- `railway.json` - Railway platform configuration  
- `fly.toml` - Fly.io configuration
- `Dockerfile` - Docker container build
- `docker-compose.yml` - Local Docker development
- `vercel.json` - Vercel serverless deployment
- `test_deployment.py` - Automated deployment testing

### Cloud Deployment Features

When deployed to cloud:
- ✅ **Zero-Install**: Users access via web browser, no installation
- ✅ **Auto-Scaling**: Handles multiple concurrent requests
- ✅ **HTTPS**: Automatic SSL certificates
- ✅ **Global CDN**: Fast access worldwide
- ✅ **Auto-Restart**: Automatic recovery from crashes
- ✅ **Health Checks**: Platform monitors uptime
- ✅ **Persistent Storage**: FFmpeg binaries cached across restarts

### Production Configuration

For production deployment, update environment variables:

```env
# backend/.env (production)
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
MAX_FILE_SIZE_MB=50
```

**Security best practices**:
- Set CORS_ORIGINS to your specific domain (not "*")
- Enable rate limiting for public deployments
- Use environment secrets for sensitive data
- Monitor logs for unusual activity
- Keep dependencies updated

---

## 📝 License

MIT License - feel free to use this project for any purpose.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

## 🙏 Acknowledgments

- **librosa** - Audio analysis library
- **FastAPI** - Modern Python web framework
- **yt-dlp** - YouTube download tool
- **pydub** - Audio processing library
- **imageio-ffmpeg** - Cross-platform FFmpeg binaries

---

**Made with ❤️ for the Muslim community**
