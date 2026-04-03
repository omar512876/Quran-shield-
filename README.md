# Quran Shield 🛡️

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Quran Shield** is an AI-powered audio analysis tool that detects whether an audio file or YouTube video contains **music** or **pure Quran/speech recitation**. It uses advanced audio processing and machine learning techniques to provide accurate classification.

---

## ✨ Features

- 🎵 **Music Detection**: Identifies musical background in audio
- 📿 **Quran/Speech Classification**: Detects pure recitation without music
- 📁 **File Upload**: Supports MP3, WAV, OGG, M4A, FLAC, AAC, and more
- 🔗 **YouTube Support**: Direct analysis from YouTube URLs
- 🎯 **High Accuracy**: Multi-feature weighted classifier with 14+ acoustic features
- 🌐 **Modern Web UI**: Clean, responsive interface
- 🚀 **REST API**: Full-featured API for integration
- 📊 **Detailed Analysis**: Confidence scores and feature breakdowns

---

## 🏗️ Architecture

### Backend (Python + FastAPI)
```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration settings
│   ├── routes/              # API endpoints
│   │   ├── audio.py         # Audio analysis routes
│   │   └── health.py        # Health check routes
│   ├── services/            # Business logic
│   │   ├── audio_analyzer.py      # Main orchestration
│   │   ├── feature_extractor.py   # Feature extraction
│   │   ├── classifier.py          # Classification logic
│   │   └── youtube_downloader.py  # YouTube handling
│   ├── models/              # Data models
│   │   └── audio.py         # Pydantic models
│   └── utils/               # Utilities
│       └── validators.py    # Input validation
└── requirements.txt
```

### Frontend (Vanilla HTML/CSS/JS)
```
frontend/
└── index.html               # Single-page application
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9 or higher**
2. **ffmpeg** (system dependency)
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

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

3. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

### Running the Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- **Web UI**: http://localhost:8000/app
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

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

## 🔧 Configuration

Edit `backend/.env` to customize:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (comma-separated origins)
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO

# Audio Processing
MAX_FILE_SIZE_MB=50
```

---

## 📊 Improvement Ideas

### Current: Rule-Based Classifier
The current system uses hand-calibrated thresholds.

### Future: ML Model
For better accuracy, train a machine learning model:

1. **Collect labeled dataset**
   - Music samples
   - Quran recitation samples

2. **Extract features** using `FeatureExtractor`

3. **Train classifier** (sklearn)
   ```python
   from sklearn.ensemble import RandomForestClassifier
   
   model = RandomForestClassifier()
   model.fit(X_train, y_train)
   ```

4. **Replace** `AudioClassifier` with trained model

---

## 🛡️ What Was Fixed / Improved

### Original Issues:
✅ **Monolithic structure** → Now modular with clean architecture  
✅ **No health endpoint** → Added `/health` and `/` endpoints  
✅ **Poor logging** → Structured logging with levels  
✅ **No configuration** → Environment-based config  
✅ **Frontend at `/app`** → Kept, but documented  
✅ **Basic UI** → Enhanced with better UX and styling  
✅ **No error details** → Comprehensive error handling  
✅ **No API prefix** → Routes now under `/api/`  
✅ **No type safety** → Added Pydantic models  
✅ **Hard to test** → Separated services for unit testing  

### Improvements:
🎨 **Modern UI** with gradients, animations, and better feedback  
📦 **Modular Code** separated into routes, services, models, utils  
🔒 **Better Security** with input validation and XSS protection  
📚 **Clear Documentation** with detailed README and code comments  
⚡ **Production Ready** with logging, health checks, and config  

---

## 🧪 Testing

To test the API:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with sample audio
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@sample.mp3"
```

---

## 📝 License

MIT License - feel free to use this project for any purpose.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

## 🙏 Acknowledgments

- **librosa** - Audio analysis library
- **FastAPI** - Modern Python web framework
- **yt-dlp** - YouTube download tool
- **pydub** - Audio processing library

---

**Made with ❤️ for the Muslim community**
