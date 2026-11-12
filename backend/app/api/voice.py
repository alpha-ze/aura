"""
Voice API — POST /api/voice
Receives audio, transcribes via Whisper (local), returns transcript.
Returns 503 with a helpful message if faster-whisper is not installed.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

import structlog

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])


class TranscriptResponse(BaseModel):
    transcript: str
    confidence: float = 1.0
    provider: str


@router.post("", response_model=TranscriptResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> TranscriptResponse:
    """
    Transcribe audio to text using faster-whisper (local, offline).

    Install voice support:
        pip install faster-whisper

    If not installed, returns 503 with installation instructions.
    """
    # Check faster-whisper is available FIRST — give a clear 503, not a crash
    try:
        from faster_whisper import WhisperModel  # type: ignore  # noqa: F401
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Voice recognition not installed",
                "message": "Install faster-whisper to enable voice input.",
                "install": "pip install faster-whisper",
                "note": "Text input works without this package.",
            },
        )

    # Validate audio content type
    content_type = audio.content_type or ""
    if not any(t in content_type for t in ("audio", "video/webm")):
        raise HTTPException(status_code=415, detail="Unsupported audio format.")

    audio_bytes = await audio.read()
    if len(audio_bytes) < 500:
        raise HTTPException(status_code=400, detail="Audio too short or empty.")

    try:
        from app.config import settings
        model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")

        suffix = ".webm" if "webm" in content_type else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            segments, _ = model.transcribe(tmp_path, beam_size=5)
            transcript = " ".join(seg.text.strip() for seg in segments).strip()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if not transcript:
            raise HTTPException(status_code=422, detail="No speech detected in audio.")

        log.info("audio_transcribed", bytes=len(audio_bytes), preview=transcript[:60])
        return TranscriptResponse(transcript=transcript, provider="whisper_local")

    except HTTPException:
        raise
    except Exception as exc:
        log.exception("transcription_error")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")
