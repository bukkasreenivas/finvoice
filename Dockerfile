FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend/ as a package directory so Python resolves
# "from backend.config import settings" and similar absolute imports.
# PYTHONPATH=/app is set explicitly so uvicorn always finds the package
# regardless of how the process is invoked.
COPY backend/ ./backend/

ENV PYTHONPATH=/app

EXPOSE 8000

# Entry point: backend is a package inside /app so uvicorn uses backend.main
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
