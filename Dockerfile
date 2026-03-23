FROM python:3.11-slim

# Adding curl busts all subsequent Docker layer cache on Railway,
# forcing a clean rebuild that picks up backend/__init__.py and
# all subdirectory __init__.py files correctly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set PYTHONPATH early so every subsequent layer inherits it.
ENV PYTHONPATH=/app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend/ as a package directory so Python resolves
# "from backend.config import settings" and similar absolute imports.
COPY backend/ ./backend/

# Explicitly ensure every directory under backend/ is a Python package.
# This guards against a cached COPY layer that predates __init__.py files.
RUN find /app/backend -type d -exec touch {}/__init__.py \; \
    && echo "--- backend package structure ---" \
    && find /app/backend -name "*.py" | sort

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
