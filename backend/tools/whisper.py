"""
Voice transcription tool.

In local development, audio is transcribed using faster-whisper running on CPU.
In production (ENVIRONMENT=production with DEEPGRAM_API_KEY set), the audio is
sent to the Deepgram API which is more reliable on constrained Railway free tier
RAM. The active backend is selected automatically via the config.

faster-whisper docs: https://github.com/SYSTRAN/faster-whisper
Deepgram docs:       https://developers.deepgram.com/docs
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import httpx

from backend.config import settings
from backend.models.schemas import TranscribeResponse


# ─── Model singleton ──────────────────────────────────────────────────────────
# faster-whisper loads the model weights into memory once and reuses them.
# Loading on first use avoids slowing down application startup.

_whisper_model = None

WHISPER_MODEL_SIZE = "base"  # base is small enough for CPU demo use


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",
        )
    return _whisper_model


# ─── Transcription ────────────────────────────────────────────────────────────


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> TranscribeResponse:
    """
    Transcribe audio bytes to text.
    Delegates to Deepgram in production, faster-whisper locally.
    """
    if settings.use_deepgram:
        return await _transcribe_deepgram(audio_bytes, filename)
    return _transcribe_whisper(audio_bytes)


def _transcribe_whisper(audio_bytes: bytes) -> TranscribeResponse:
    """
    Transcribe using self-hosted faster-whisper.
    Runs synchronously — acceptable because the WebSocket endpoint receives
    the transcription in a background thread via asyncio.run_in_executor.
    """
    model = _get_whisper_model()
    t0 = time.monotonic()

    audio_file = io.BytesIO(audio_bytes)
    segments, info = model.transcribe(
        audio_file,
        language="hi" if _is_hindi_likely(audio_bytes) else None,
        task="transcribe",
        beam_size=5,
    )

    transcript = " ".join(seg.text.strip() for seg in segments)
    duration = time.monotonic() - t0

    return TranscribeResponse(
        transcript=transcript.strip(),
        duration_seconds=round(duration, 2),
        backend="whisper",
    )


async def _transcribe_deepgram(audio_bytes: bytes, filename: str) -> TranscribeResponse:
    """
    Transcribe using the Deepgram Nova-2 model.
    Deepgram free tier: 45 minutes per month. Sufficient for demo use.
    """
    t0 = time.monotonic()

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.deepgram.com/v1/listen",
            headers={
                "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
                "Content-Type": "audio/webm",
            },
            params={
                "model": "nova-2",
                "language": "hi-Latn",  # Hindi with Latin script fallback
                "punctuate": "true",
                "smart_format": "true",
            },
            content=audio_bytes,
        )
        response.raise_for_status()

    duration = time.monotonic() - t0
    data = response.json()
    transcript = (
        data.get("results", {})
        .get("channels", [{}])[0]
        .get("alternatives", [{}])[0]
        .get("transcript", "")
    )

    return TranscribeResponse(
        transcript=transcript.strip(),
        duration_seconds=round(duration, 2),
        backend="deepgram",
    )


# ─── Language detection ───────────────────────────────────────────────────────


def _is_hindi_likely(audio_bytes: bytes) -> bool:
    """
    Placeholder for language detection.
    In a future iteration this would run a lightweight language-ID model.
    For now, returns False and lets Whisper auto-detect the language.
    """
    return False
