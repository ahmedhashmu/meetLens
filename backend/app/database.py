"""Database connection aur session management."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _normalize(url: str) -> str:
    """Supabase/Neon `postgresql://` ko psycopg3 driver par point karta hai."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _normalize(settings.DATABASE_URL)

_connect_args: dict = {}
_engine_kwargs: dict = {"pool_pre_ping": True}

if DATABASE_URL.startswith("sqlite"):
    # SQLite sirf local development ke liye.
    _connect_args["check_same_thread"] = False
    _engine_kwargs.pop("pool_pre_ping")

engine = create_engine(DATABASE_URL, connect_args=_connect_args, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — har request ke liye ek DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
