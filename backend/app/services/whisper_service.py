"""Audio file ko Whisper API se transcript mein badalta hai."""
import io
import logging

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}


def validate_audio(filename: str | None, size_bytes: int) -> str:
    """Filename aur size check karta hai, saaf extension wapas karta hai."""
    if not filename or "." not in filename:
        raise HTTPException(status_code=400, detail="Audio file ka naam ghalat hai.")

    ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400, detail=f"Ye format support nahi hai. Allowed: {allowed}"
        )

    max_bytes = settings.MAX_AUDIO_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File {settings.MAX_AUDIO_MB} MB se bari hai."
        )
    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="Audio file khaali hai.")

    return ext


def transcribe(audio_bytes: bytes, filename: str) -> str:
    """Audio bytes se transcript text wapas karta hai."""
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY set nahi hai, is liye transcription nahi ho sakti.",
        )

    from openai import OpenAI, OpenAIError

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    buffer = io.BytesIO(audio_bytes)
    buffer.name = filename

    try:
        result = client.audio.transcriptions.create(
            model=settings.WHISPER_MODEL, file=buffer, response_format="text"
        )
    except OpenAIError as exc:
        logger.warning("Whisper failed for %s: %s", filename, exc)
        raise HTTPException(status_code=502, detail=f"Transcription fail ho gayi: {exc}") from exc

    text = result if isinstance(result, str) else getattr(result, "text", "")
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Audio mein koi baat samajh nahi aayi.")
    return text
