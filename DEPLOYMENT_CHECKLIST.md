# Quran Shield - Deployment Checklist

Use this checklist when deploying Quran Shield to production.

---

## 📋 Pre-Deployment Checklist

### Code Review
- [ ] All tests pass locally
- [ ] No hardcoded secrets or API keys
- [ ] Environment variables properly configured
- [ ] CORS settings reviewed (not using wildcard "*" in production)
- [ ] Error messages don't expose sensitive information
- [ ] Logging level appropriate for production (INFO or WARNING)

### Local Testing
- [ ] Run application locally: `python -m uvicorn backend.app.main:app --reload`
- [ ] Test file upload with various formats (MP3, WAV, M4A)
- [ ] Test YouTube URL analysis
- [ ] Verify error handling (invalid inputs, oversized files)
- [ ] Check health endpoint: `curl http://localhost:8000/health`
- [ ] Review logs for any warnings

### Documentation
- [ ] README.md is up to date
- [ ] Deployment guide reviewed
- [ ] API documentation accessible at `/docs`
- [ ] Environment variables documented in `.env.example`

---

## 🚀 Deployment Steps

### Choose Your Platform

Select one deployment method:

#### Option A: Render (Recommended for Beginners)

- [ ] Create account at [render.com](https://render.com)
- [ ] Connect GitHub repository
- [ ] Create new Web Service
- [ ] Verify `render.yaml` configuration:
  ```yaml
  buildCommand: "cd backend && pip install --upgrade pip && pip install -r requirements.txt"
  startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  ```
- [ ] Set environment variables:
  - `LOG_LEVEL=INFO`
  - `MAX_FILE_SIZE_MB=50`
  - `CORS_ORIGINS=your-domain.com` (or keep "*" for testing)
- [ ] Enable persistent disk for FFmpeg binaries (optional but recommended)
- [ ] Deploy and wait for build (5-10 minutes)

#### Option B: Railway

- [ ] Create account at [railway.app](https://railway.app)
- [ ] New Project → Deploy from GitHub repo
- [ ] Railway auto-detects Python
- [ ] Add environment variables:
  ```
  PORT=8000
  LOG_LEVEL=INFO
  CORS_ORIGINS=*
  ```
- [ ] Settings → Networking → Generate Domain
- [ ] Deploy

#### Option C: Fly.io

- [ ] Install Fly CLI: `brew install flyctl` (macOS) or `curl -L https://fly.io/install.sh | sh`
- [ ] Sign up: `flyctl auth signup`
- [ ] Navigate to project: `cd Quran-shield-`
- [ ] Launch: `flyctl launch`
  - App name: `quran-shield` (or your choice)
  - Region: Select closest to your users
  - Don't deploy yet: `N`
- [ ] Review `fly.toml` configuration
- [ ] Deploy: `flyctl deploy`
- [ ] Wait for deployment (5-10 minutes)

#### Option D: Docker (Self-Hosted)

- [ ] Ensure Docker and Docker Compose installed
- [ ] Review `Dockerfile` and `docker-compose.yml`
- [ ] Set environment variables in `docker-compose.yml` or `.env` file
- [ ] Build: `docker-compose build`
- [ ] Run: `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Configure reverse proxy (nginx) for HTTPS
- [ ] Set up firewall rules
- [ ] Configure auto-restart on server reboot

#### Option E: Vercel (Serverless)

- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] Review `vercel.json` configuration
- [ ] Deploy: `vercel`
- [ ] Note: 10s timeout limit, may not work for long YouTube videos

---

## ✅ Post-Deployment Verification

### Immediate Checks (First 5 Minutes)

- [ ] Deployment completed without errors
- [ ] Application is accessible at deployment URL
- [ ] Health endpoint responds: `curl https://your-app.com/health`
- [ ] Health response includes `"status": "OK"`
- [ ] Health response shows `"ffmpeg_available": true` (may be false on first request)

### Functional Testing (15-30 Minutes)

- [ ] Run automated test suite:
  ```bash
  python test_deployment.py https://your-app.com
  ```
- [ ] All critical tests pass (health, error handling, file upload)
- [ ] Manual test: Upload small audio file via web UI
- [ ] Manual test: Analyze short YouTube URL (if not timed out)
- [ ] Verify error messages are user-friendly
- [ ] Test on mobile device

### Performance Testing

- [ ] First request (cold start): < 120 seconds
- [ ] Subsequent requests (warm): < 30 seconds
- [ ] File upload (5MB): < 20 seconds
- [ ] YouTube analysis (3 min video): < 60 seconds
- [ ] Memory usage stable (not growing over time)

### Security Verification

- [ ] CORS settings appropriate for production
- [ ] HTTPS enabled (automatic on most platforms)
- [ ] No sensitive data in logs
- [ ] File size limits enforced (default 50MB)
- [ ] Invalid inputs rejected properly

### Monitoring Setup

- [ ] Add health check monitoring:
  - [ ] UptimeRobot (free): `https://uptimerobot.com`
  - [ ] Or platform built-in monitoring
  - [ ] Set check interval: 5 minutes
  - [ ] Alert email/SMS configured
- [ ] Review platform logs regularly
- [ ] Set up log aggregation (optional: Papertrail, Logtail)

---

## 🔧 Configuration & Optimization

### Environment Variables (Production)

Update these for production deployment:

```env
# Required
PORT=8000

# Recommended
LOG_LEVEL=INFO
DEBUG=False
MAX_FILE_SIZE_MB=50

# Security (IMPORTANT!)
CORS_ORIGINS=https://yourdomain.com  # Replace with your domain, NOT "*"
```

### Custom Domain Setup

If using custom domain:

**Render:**
- [ ] Dashboard → Settings → Custom Domains
- [ ] Add your domain
- [ ] Update DNS CNAME record to point to Render URL
- [ ] Wait for DNS propagation (5-60 minutes)
- [ ] Verify SSL certificate auto-generated

**Railway:**
- [ ] Project → Settings → Networking
- [ ] Add custom domain
- [ ] Update DNS records as instructed
- [ ] Wait for SSL certificate

**Fly.io:**
- [ ] Run: `flyctl certs add yourdomain.com`
- [ ] Follow DNS setup instructions
- [ ] Verify: `flyctl certs show yourdomain.com`

### Performance Optimization

- [ ] Enable platform auto-scaling (if available)
- [ ] Configure instance size appropriately:
  - Free tier: OK for testing/low traffic
  - Light usage: 512MB RAM, 1 CPU
  - Medium usage: 1GB RAM, 1-2 CPU
  - Heavy usage: 2GB+ RAM, 2+ CPU
- [ ] Consider adding Redis for caching (optional)
- [ ] Use CDN for static assets (optional: Cloudflare)

---

## 🐛 Troubleshooting

### Deployment Fails

**Symptom**: Build fails during deployment

**Check:**
- [ ] Review build logs for specific error
- [ ] Verify `requirements.txt` is valid
- [ ] Check Python version compatibility (3.9+)
- [ ] Ensure all files committed to Git

**Symptom**: App crashes on startup

**Check:**
- [ ] Review runtime logs
- [ ] Verify environment variables set correctly
- [ ] Check port binding (`$PORT` variable used)
- [ ] Ensure start command is correct

### FFmpeg Issues

**Symptom**: "FFmpeg not found" errors

**Solutions:**
- [ ] Check if first request has enough time to download FFmpeg (may take 40-80s)
- [ ] Verify server has internet access for download
- [ ] Check platform logs for download errors
- [ ] Consider pre-downloading FFmpeg during build:
  ```yaml
  buildCommand: |
    cd backend
    pip install -r requirements.txt
    python -c "from app.utils.ffmpeg_manager import ensure_ffmpeg; ensure_ffmpeg()"
  ```

### Timeout Issues

**Symptom**: Requests timeout after 30-60 seconds

**Solutions:**
- [ ] Increase platform timeout limit (if possible)
- [ ] Test with shorter videos
- [ ] Consider upgrading to paid tier with higher limits
- [ ] Implement background job processing for long tasks

### Memory Issues

**Symptom**: "Out of memory" errors

**Solutions:**
- [ ] Upgrade to larger instance size
- [ ] Reduce `MAX_FILE_SIZE_MB`
- [ ] Limit concurrent requests
- [ ] Add memory monitoring

---

## 📊 Monitoring & Maintenance

### Daily Checks
- [ ] Application is accessible
- [ ] No error spikes in logs
- [ ] Response times normal

### Weekly Checks
- [ ] Review error logs
- [ ] Check resource usage trends
- [ ] Verify disk space (if using persistent storage)
- [ ] Review uptime reports

### Monthly Checks
- [ ] Update dependencies: `pip list --outdated`
- [ ] Review security advisories
- [ ] Check for platform updates
- [ ] Review and optimize costs

### Quarterly Checks
- [ ] Full security audit
- [ ] Performance testing
- [ ] Documentation updates
- [ ] Backup/restore testing

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ **Health endpoint returns 200 OK**
✅ **FFmpeg auto-download works on first run**
✅ **File upload analysis completes in < 30 seconds**
✅ **YouTube analysis works (or gracefully times out on free tier)**
✅ **Error handling is robust and user-friendly**
✅ **Application is accessible 24/7 (except during deployments)**
✅ **Logs show no critical errors**
✅ **Automated tests pass: `python test_deployment.py`**
✅ **CORS configured appropriately for production**
✅ **Monitoring alerts configured**

---

## 📞 Getting Help

If you encounter issues:

1. **Check platform docs**:
   - [Render Docs](https://render.com/docs)
   - [Railway Docs](https://docs.railway.app)
   - [Fly.io Docs](https://fly.io/docs)

2. **Review logs**: All platforms provide log viewing
   - Look for errors, warnings, stack traces
   - Note timestamps of issues

3. **Test locally**: Reproduce issue on local machine if possible

4. **GitHub Issues**: Open issue with:
   - Platform used
   - Error messages
   - Steps to reproduce
   - Relevant logs

5. **Platform support**: Most platforms have community forums or support tickets

---

## ✅ Final Checklist

Before considering deployment complete:

- [ ] Application accessible at public URL
- [ ] Health check passes
- [ ] Automated tests pass
- [ ] Manual testing completed
- [ ] Monitoring configured
- [ ] Custom domain set up (if applicable)
- [ ] CORS configured for production
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Documentation updated with deployment URL
- [ ] Team/users notified of new deployment

---

**Congratulations!** 🎉 Your Quran Shield web application is now live and accessible to users worldwide!

**Share your deployment:**
- Add URL to README.md
- Share on social media
- Add to portfolio
- Submit to app directories

---

**Last Updated**: January 2025
**Version**: 2.0 (Web Deployment)
