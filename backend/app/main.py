"""MeetLens API — FastAPI entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import DATABASE_URL, Base, engine
from app.routers import auth, clients, dashboard, followups, meetings

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Sirf local SQLite par tables khud banti hain. Supabase par tables pehle se hain
    # (aur extra columns backend/sql/ ki files se aate hain), wahan kuch nahi banate.
    if DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MeetLens API",
    description="Client meetings ko summary aur follow-up items mein badalne wali API.",
    version="0.1.0",
    lifespan=lifespan,
)

# Vercel wala frontend allow karna zaroori hai, warna browser calls block karega.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(meetings.router)
app.include_router(followups.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "ai_enabled": settings.ai_enabled,
        "email_enabled": settings.email_enabled,
    }
