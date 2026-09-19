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

    # ---- Auth -----------------------------------------------------
    # Production mein ye .env se aana ZAROORI hai.
    SECRET_KEY: str = "dev-only-insecure-key-change-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 ghante

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
    if s.is_production and s.SECRET_KEY == Settings.model_fields["SECRET_KEY"].default:
        raise RuntimeError(
            "SECRET_KEY production mein default nahi chhor sakte. "
            ".env ya Railway ke variables mein asli value daalein."
        )
    return s


settings = get_settings()
