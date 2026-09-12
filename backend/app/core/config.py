"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"  # Default for development
    
    # LLM Configuration
    LLM_PROVIDER: Literal["openai", "xai"] = "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None
    XAI_API_KEY: str | None = None
    
    # Authentication
    JWT_SECRET: str = "d687019fcd2ef40a5710aa556ec1902c8b3a4f5e6d7c8b9a0e1f2d3c4b5a6978"  # Default for development
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Changed to 1 hour to match JWT implementation
    
    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()