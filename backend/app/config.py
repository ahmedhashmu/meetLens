"""Environment variables se saari settings load karta hai.

Koi bhi secret is file mein hardcode NAHI hoga. Sab kuch .env se aayega.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Database -------------------------------------------------
    # Supabase / Neon PostgreSQL ki connection string.
    # Khaali chhor dein to local development ke liye SQLite use hogi.
    DATABASE_URL: str = "sqlite:///./meetlens.db"

    # ---- Auth (Supabase) ------------------------------------------
    # Login Supabase karta hai, backend sirf uska token verify karta hai.
    # SUPABASE_URL se public keys (JWKS) le kar token check hota hai.
    SUPABASE_URL: str | None = None
    # Sirf purane HS256 projects aur tests ke liye. Naye projects ko zaroorat nahi.
    SUPABASE_JWT_SECRET: str | None = None

    # ---- AI -------------------------------------------------------
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    WHISPER_MODEL: str = "whisper-1"

    # ---- Frontend / CORS ------------------------------------------
    # Comma se alag kar ke ek se zyada URL bhi de sakte hain.
    FRONTEND_URL: str = "http://localhost:3000"

    # ---- Audio uploads --------------------------------------------
    UPLOAD_DIR: str = "uploads"
    MAX_AUDIO_MB: int = 25  # Whisper API ki apni limit 25 MB hai

    # ---- Email reminders ------------------------------------------
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # ---- App ------------------------------------------------------
    ENVIRONMENT: str = "development"

    @property
    def cors_origins(self) -> list[str]:
        return [u.strip() for u in self.FRONTEND_URL.split(",") if u.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def ai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def email_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production and not (s.SUPABASE_URL or s.SUPABASE_JWT_SECRET):
        raise RuntimeError(
            "SUPABASE_URL production mein zaroori hai, warna login verify nahi ho sakta. "
            ".env ya Railway ke variables mein daalein."
        )
    return s


settings = get_settings()
