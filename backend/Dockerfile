# ─── Build stage ──────────────────────────────────────────────────────────────
# Production equivalent on Railway: Railway builds from this Dockerfile automatically.

FROM python:3.11-slim AS base

# System dependencies for faster-whisper (ffmpeg for audio decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Skip Whisper model download on Railway (RAM constrained) — Deepgram handles
# voice in production. Set SKIP_WHISPER_DOWNLOAD=0 only for local Docker builds.
ARG SKIP_WHISPER_DOWNLOAD=1
RUN if [ "$SKIP_WHISPER_DOWNLOAD" = "0" ]; then \
    python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"; \
    fi

# Railway injects $PORT at runtime. The railway.toml startCommand uses $PORT.
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
