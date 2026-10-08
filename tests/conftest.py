"""Pytest setup — har test ke liye alag SQLite database.

Login Supabase karta hai, is liye tests mein hum khud Supabase jaisa token
(HS256, test secret ke saath) bana lete hain.
"""
import os
import sys
import uuid
from pathlib import Path

# Settings import hone se pehle — asli database ya asli Supabase kabhi use na ho
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory, koi file nahi banti
os.environ["SUPABASE_JWT_SECRET"] = "test-secret-for-pytest-only-0123456789"
os.environ.pop("OPENAI_API_KEY", None)

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


def make_token(user_id: str | None = None, email: str = "ahmed@example.com") -> dict:
    """Supabase jaisa access token bana kar Authorization header wapas karta hai."""
    token = jwt.encode(
        {"sub": user_id or str(uuid.uuid4()), "email": email, "aud": "authenticated"},
        os.environ["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path/'test.db'}", connect_args={"check_same_thread": False}
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    """Ek logged-in user ka Authorization header."""
    return make_token()


@pytest.fixture
def client_id(client, auth):
    response = client.post("/clients", json={"name": "Acme Corp", "company": "Acme"}, headers=auth)
    assert response.status_code == 201, response.text
    return response.json()["id"]
