# Quran Shield - Cloud Deployment Guide

This guide shows how to deploy Quran Shield to various cloud platforms for **zero-install web access**.

---

## 🚀 Quick Deploy Options

| Platform | Difficulty | Free Tier | Best For |
|----------|------------|-----------|----------|
| **Render** | ⭐ Easy | ✅ Yes | Recommended for beginners |
| **Railway** | ⭐ Easy | ✅ Yes (trial) | Fast deployment |
| **Fly.io** | ⭐⭐ Medium | ✅ Yes | Global edge deployment |
| **Docker** | ⭐⭐⭐ Advanced | N/A | Self-hosting |

---

## 1. Deploy to Render (Recommended)

### Why Render?
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy GitHub integration
- ✅ Built-in health checks

### Steps:

1. **Fork/Clone the repository**
   ```bash
   git clone https://github.com/omar512876/Quran-shield-.git
   cd Quran-shield-
   ```

2. **Create `render.yaml` in project root** (already included)

3. **Sign up at [render.com](https://render.com)**

4. **Create New Web Service**:
   - Connect your GitHub repository
   - Select `Quran-shield-`
   - Render will auto-detect `render.yaml`

5. **Configure**:
   - **Name**: `quran-shield`
   - **Region**: Select closest to you
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. **Add Environment Variables** (optional):
   ```
   LOG_LEVEL=INFO
   MAX_FILE_SIZE_MB=50
   ```

7. **Deploy**: Click "Create Web Service"

8. **Wait**: First deployment takes 5-10 minutes (FFmpeg auto-download)

9. **Access**: Your app will be at `https://quran-shield.onrender.com`

### render.yaml Configuration

```yaml
services:
  - type: web
    name: quran-shield
    env: python
    region: oregon
    plan: free
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
    envVars:
      - key: LOG_LEVEL
        value: INFO
      - key: MAX_FILE_SIZE_MB
        value: 50
      - key: CORS_ORIGINS
        value: "*"
```

---

## 2. Deploy to Railway

### Why Railway?
- ✅ Very fast deployment
- ✅ GitHub integration
- ✅ Automatic HTTPS
- ✅ $5 free trial credit

### Steps:

1. **Sign up at [railway.app](https://railway.app)**

2. **New Project** → **Deploy from GitHub repo**

3. **Select** `Quran-shield-` repository

4. **Configure**:
   - Railway auto-detects Python
   - Add these environment variables:
     ```
     PORT=8000
     LOG_LEVEL=INFO
     CORS_ORIGINS=*
     ```

5. **Settings** → **Networking**:
   - Generate Domain

6. **Deploy**: Railway automatically builds and deploys

7. **Access**: Your app at `https://quran-shield.up.railway.app`

### railway.json Configuration

Create `railway.json` in project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 3. Deploy to Fly.io

### Why Fly.io?
- ✅ Global edge deployment
- ✅ Free allowance
- ✅ Docker-based (full control)

### Steps:

1. **Install Fly CLI**:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux/Windows
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up**:
   ```bash
   flyctl auth signup
   ```

3. **Navigate to project**:
   ```bash
   cd Quran-shield-
   ```

4. **Launch app**:
   ```bash
   flyctl launch
   ```
   
   - App name: `quran-shield`
   - Region: Select closest
   - Don't deploy yet: `N`

5. **Update `fly.toml`** (auto-generated, modify):
   ```toml
   app = "quran-shield"
   primary_region = "sea"

   [build]
     dockerfile = "Dockerfile"

   [env]
     PORT = "8000"
     LOG_LEVEL = "INFO"

   [[services]]
     http_checks = []
     internal_port = 8000
     processes = ["app"]
     protocol = "tcp"

     [[services.ports]]
       port = 80
       handlers = ["http"]
       force_https = true

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]

     [services.concurrency]
       type = "connections"
       hard_limit = 25
       soft_limit = 20

   [[services.http_checks]]
     interval = 10000
     grace_period = "5s"
     method = "get"
     path = "/health"
     protocol = "http"
     timeout = 2000
   ```

6. **Deploy**:
   ```bash
   flyctl deploy
   ```

7. **Access**: `https://quran-shield.fly.dev`

---

## 4. Docker Self-Hosting

### Why Docker?
- ✅ Run anywhere
- ✅ Full control
- ✅ Reproducible builds
- ✅ Easy scaling

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend
COPY backend /app/backend

# Copy frontend
COPY frontend /app/frontend

# Install Python dependencies
RUN cd backend && pip install --no-cache-dir -r requirements.txt

# Create directory for FFmpeg
RUN mkdir -p /app/backend/bin/ffmpeg

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  quran-shield:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=*
      - MAX_FILE_SIZE_MB=50
    volumes:
      - ffmpeg-cache:/app/backend/bin/ffmpeg
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  ffmpeg-cache:
```

### Run with Docker

```bash
# Build
docker build -t quran-shield .

# Run
docker run -d \
  -p 8000:8000 \
  -e LOG_LEVEL=INFO \
  -e CORS_ORIGINS="*" \
  --name quran-shield \
  quran-shield

# Or with docker-compose
docker-compose up -d

# View logs
docker logs -f quran-shield

# Access
open http://localhost:8000/app
```

---

## 5. Vercel (Serverless - Advanced)

### Why Vercel?
- ✅ Free tier generous
- ✅ Auto-scaling
- ✅ Great for frontend
- ⚠️ 10s function timeout (may limit long videos)

### Steps:

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Create `vercel.json`**:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "backend/app/main.py",
         "use": "@vercel/python"
       },
       {
         "src": "frontend/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "backend/app/main.py"
       },
       {
         "src": "/(.*)",
         "dest": "frontend/$1"
       }
     ],
     "functions": {
       "backend/app/main.py": {
         "maxDuration": 10
       }
     }
   }
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

**Note**: Vercel has strict timeout limits. Best for quick audio analysis, may fail on long YouTube videos.

---

## 🔧 Post-Deployment Configuration

### 1. Environment Variables

Set these on your platform:

```env
# Required
PORT=8000

# Optional
LOG_LEVEL=INFO
DEBUG=False
MAX_FILE_SIZE_MB=50
CORS_ORIGINS=https://yourdomain.com  # Set to your domain in production
```

### 2. Custom Domain

**Render**:
- Dashboard → Settings → Custom Domains
- Add your domain
- Update DNS CNAME record

**Railway**:
- Project → Settings → Networking
- Add custom domain
- Update DNS

**Fly.io**:
```bash
flyctl certs add yourdomain.com
```

### 3. Monitoring

Add health check monitoring:
- **UptimeRobot**: Free, monitors `/health` endpoint
- **StatusCake**: Free tier available
- **Platform built-in**: Most platforms include monitoring

---

## 📊 Performance Optimization

### 1. CDN for Frontend

Use Cloudflare or similar CDN:
1. Point domain to your deployment
2. Enable caching for static assets
3. Enable compression

### 2. Caching

Add Redis for caching analysis results:

```python
# backend/app/services/cache.py
import redis

redis_client = redis.Redis(
    host='your-redis-host',
    port=6379,
    decode_responses=True
)

def cache_analysis(url_hash, result):
    redis_client.setex(f"analysis:{url_hash}", 3600, json.dumps(result))

def get_cached_analysis(url_hash):
    cached = redis_client.get(f"analysis:{url_hash}")
    return json.loads(cached) if cached else None
```

### 3. Background Jobs

For long-running analyses, use background workers:
- **Celery** with Redis/RabbitMQ
- **RQ** (Redis Queue)
- Platform-specific (Railway Background Workers)

---

## 🔒 Security Best Practices

### 1. CORS Configuration

Update `backend/.env`:
```env
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Rate Limiting

Add to `backend/app/main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze(...):
    ...
```

### 3. API Authentication (Optional)

For production with heavy usage:
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
```

---

## 🧪 Testing Deployment

After deployment:

```bash
# Test health endpoint
curl https://your-app.com/health

# Test analysis endpoint
curl -X POST https://your-app.com/api/analyze \
  -F "url=https://www.youtube.com/watch?v=EXAMPLE"

# Test with file
curl -X POST https://your-app.com/api/analyze \
  -F "file=@test.mp3"
```

---

## 📈 Cost Estimates

| Platform | Free Tier | Paid (monthly) |
|----------|-----------|----------------|
| Render | 750 hours/month | $7+ for always-on |
| Railway | $5 credit | $5/month pay-as-you-go |
| Fly.io | 3 VMs, 160GB transfer | $5-10/month |
| Docker (VPS) | N/A | $5-10/month (DigitalOcean, Linode) |
| Vercel | 100GB bandwidth | $20/month Pro |

---

## 🎯 Recommended Setup

**For Beginners**: Start with Render (free tier, easy setup)
**For Scale**: Use Railway or Fly.io (better performance)
**For Control**: Self-host with Docker on VPS
**For Serverless**: Vercel (if timeout limits acceptable)

---

## 🆘 Troubleshooting

### FFmpeg Download Fails on Server

**Symptom**: "FFmpeg not found and auto-download failed"

**Solution**:
1. Check server has internet access
2. Verify download URLs are accessible
3. Pre-download FFmpeg during build:
   ```yaml
   # In render.yaml or equivalent
   buildCommand: |
     cd backend
     pip install -r requirements.txt
     python -c "from app.utils.ffmpeg_manager import ensure_ffmpeg; ensure_ffmpeg()"
   ```

### Timeout on Long Videos

**Symptom**: Request times out after 30-60 seconds

**Solution**:
1. Increase timeout in platform settings
2. Implement background job processing
3. Add webhook callback for results

### Memory Issues

**Symptom**: "Out of memory" errors

**Solution**:
1. Upgrade to larger instance
2. Add streaming audio processing
3. Limit concurrent requests

---

**Need help?** Open an issue on GitHub or check platform-specific docs.
