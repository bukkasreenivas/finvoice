"""
Voice router — audio transcription endpoint.

POST /voice/transcribe — accepts an audio file upload, returns a transcript.

The frontend records audio using the browser MediaRecorder API and POSTs it as
a multipart form upload. The transcript is returned and displayed to the user
for confirmation before being sent to the chat endpoint. This confirmation step
is a deliberate UX decision: it prevents Whisper transcription errors from
silently reaching the agents.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import TranscribeResponse
from backend.tools import whisper as whisper_tool

router = APIRouter(prefix="/voice", tags=["voice"])

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB — approximately 10 minutes at 128 kbps
ALLOWED_CONTENT_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/wav",
    "audio/mpeg",
    "audio/mp4",
    "application/octet-stream",  # some browsers send this for webm
}


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file from the browser MediaRecorder"),
) -> TranscribeResponse:
    """
    Transcribe an audio file to text.

    The active transcription backend is selected automatically:
    - Local development: faster-whisper on CPU
    - Production: Deepgram Nova-2 API

    Returns the transcript and which backend was used.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {file.content_type}. "
                   f"Supported formats: webm, ogg, wav, mp3, mp4.",
        )

    audio_bytes = await file.read()

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Audio file exceeds the 10 MB limit. Please record a shorter clip.",
        )

    if len(audio_bytes) < 100:
        raise HTTPException(
            status_code=400,
            detail="Audio file appears to be empty or corrupt.",
        )

    # Run transcription in a thread pool executor to avoid blocking the event loop.
    # faster-whisper is synchronous and CPU-bound.
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        _transcribe_sync,
        audio_bytes,
        file.filename or "audio.webm",
    )

    return result


def _transcribe_sync(audio_bytes: bytes, filename: str) -> TranscribeResponse:
    """
    Synchronous wrapper called from the executor.
    For the Deepgram path, runs an asyncio event loop internally.
    """
    import asyncio

    return asyncio.run(whisper_tool.transcribe(audio_bytes, filename))
