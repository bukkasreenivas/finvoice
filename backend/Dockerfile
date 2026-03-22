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

# Download the Whisper base model at build time so it is available at runtime
# without a network call. Skipped in CI by setting SKIP_WHISPER_DOWNLOAD=1.
ARG SKIP_WHISPER_DOWNLOAD=0
RUN if [ "$SKIP_WHISPER_DOWNLOAD" = "0" ]; then \
    python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"; \
    fi

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
