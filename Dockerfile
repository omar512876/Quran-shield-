FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version

# Create app user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/backend/bin/ffmpeg && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy backend requirements first for better caching
COPY --chown=appuser:appuser backend/requirements.txt /app/backend/

# Install Python dependencies
RUN pip install --upgrade pip && \
    cd backend && \
    pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser backend /app/backend
COPY --chown=appuser:appuser frontend /app/frontend

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
