"""Audio file ko Whisper API se transcript mein badalta hai."""
import base64
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


# Gemini ko audio ka format batana padta hai; ye wale woh samajhta hai
GEMINI_AUDIO_FORMATS = {".mp3": "mp3", ".mpeg": "mp3", ".mpga": "mp3", ".wav": "wav", ".m4a": "aac"}
GEMINI_MAX_MB = 14  # base64 ke baad ~20 MB, jo Gemini ki inline limit hai


def transcribe(audio_bytes: bytes, filename: str) -> str:
    """Audio bytes se transcript text wapas karta hai (Gemini ya OpenAI Whisper)."""
    from openai import OpenAIError

    from app.services.ai_client import extra_options, get_client

    client, model, provider = get_client()

    try:
        if provider == "gemini":
            text = _transcribe_gemini(client, model, audio_bytes, filename, extra_options(provider))
        else:
            buffer = io.BytesIO(audio_bytes)
            buffer.name = filename
            result = client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL, file=buffer, response_format="text"
            )
            text = result if isinstance(result, str) else getattr(result, "text", "")
    except OpenAIError as exc:
        logger.warning("Transcription failed for %s: %s", filename, exc)
        raise HTTPException(status_code=502, detail=f"Transcription fail ho gayi: {exc}") from exc

    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Audio mein koi baat samajh nahi aayi.")
    return text


def _transcribe_gemini(client, model: str, audio_bytes: bytes, filename: str, options: dict) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    fmt = GEMINI_AUDIO_FORMATS.get(ext)
    if fmt is None:
        allowed = ", ".join(sorted(GEMINI_AUDIO_FORMATS))
        raise HTTPException(status_code=400, detail=f"Gemini ke saath sirf ye formats chalte hain: {allowed}")
    if len(audio_bytes) > GEMINI_MAX_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File {GEMINI_MAX_MB} MB se bari hai.")

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        **options,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Transcribe this meeting recording word for word. "
                        "Put each speaker on a new line. Return only the transcript.",
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {"data": base64.b64encode(audio_bytes).decode(), "format": fmt},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""
