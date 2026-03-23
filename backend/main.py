"""
FinVoice — FastAPI application entrypoint.

Startup sequence:
  1. Initialise the database (create tables, enable pgvector extension).
  2. Register routers for chat and voice endpoints.
  3. Configure CORS so the React frontend (Vercel) can connect to this backend (Railway).

Local:      uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Production: uvicorn main:app --host 0.0.0.0 --port 8000 (Railway sets PORT automatically)

API docs available at /docs (Swagger) and /redoc (ReDoc) in development.
"""

from __future__ import annotations

import os

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models.database import init_db
from backend.routers import chat, voice

log = structlog.get_logger()


# ─── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="FinVoice API",
    description=(
        "Voice-first multi-agent personal finance assistant for the Indian market. "
        "Supervisor agent routes queries to Spending Analyst, Investment Advisor, "
        "Tax Optimizer, or Budget Planner. Responses stream token-by-token over WebSocket."
    ),
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)


# ─── CORS ─────────────────────────────────────────────────────────────────────
# In production, restrict origins to the Vercel frontend domain.
# In development, allow all origins for ease of local testing.

_origins = (
    ["*"]
    if not settings.is_production
    else [
        os.environ.get("RAILWAY_BACKEND_URL", ""),
        "https://finvoice.vercel.app",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Lifecycle ────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup() -> None:
    log.info("finvoice.startup", environment=settings.ENVIRONMENT)
    try:
        await init_db()
        log.info("finvoice.db_ready")
    except Exception as exc:  # noqa: BLE001
        # Database may not yet be configured (e.g. Railway deploy before
        # Supabase env vars are set). Log the error and continue — the
        # health check must still pass so Railway marks the deploy live.
        # DB-dependent endpoints will return 503 until DATABASE_URL is set.
        log.warning("finvoice.db_unavailable", error=str(exc))


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(chat.router)
app.include_router(voice.router)


# ─── Health check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["ops"])
async def health() -> dict:
    """
    Health check used by Railway and Docker Compose.
    Returns 200 when the application is ready to accept traffic.
    """
    return {"status": "ok", "version": "0.1.0"}


@app.get("/", tags=["ops"])
async def root() -> dict:
    return {
        "name": "FinVoice API",
        "docs": "/docs",
        "health": "/health",
    }
