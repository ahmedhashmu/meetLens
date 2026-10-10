"""AI provider chunta hai — Gemini (free) ya OpenAI. Dono ek hi OpenAI SDK se chalte hain."""
from fastapi import HTTPException

from app.config import settings

# Gemini ka OpenAI-compatible endpoint
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

NO_KEY_DETAIL = "AI key set nahi hai (GEMINI_API_KEY ya OPENAI_API_KEY), is liye ye kaam nahi ho sakta."


def get_client():
    """(client, chat model, provider) wapas karta hai."""
    from openai import OpenAI

    if settings.ai_provider == "gemini":
        client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url=GEMINI_BASE_URL)
        return client, settings.GEMINI_MODEL, "gemini"
    if settings.ai_provider == "openai":
        return OpenAI(api_key=settings.OPENAI_API_KEY), settings.OPENAI_MODEL, "openai"
    raise HTTPException(status_code=503, detail=NO_KEY_DETAIL)


def extra_options(provider: str) -> dict:
    """Gemini by default bohot der "sochta" hai (~100s); low rakhne se ~6s mein jawab aata hai."""
    return {"reasoning_effort": "low"} if provider == "gemini" else {}
