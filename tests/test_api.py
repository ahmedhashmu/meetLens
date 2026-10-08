"""MeetLens backend ke smoke tests."""
import uuid
from datetime import date

import jwt
from conftest import make_token

from app.services import openai_service

TRANSCRIPT = (
    "Client ne kaha ke dashboard ka design pasand aaya. "
    "Unhein budget ki thori concern hai. Hum agle hafte proposal bhejenge."
)


def _meeting(client, auth, client_id, title="Kickoff call"):
    response = client.post(
        "/meetings",
        json={
            "client_id": client_id,
            "title": title,
            "meeting_date": str(date.today()),
            "transcript": TRANSCRIPT,
        },
        headers=auth,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_endpoints_need_login(client):
    for path in ("/clients", "/dashboard", "/followups", "/auth/me"):
        assert client.get(path).status_code == 401


def test_token_with_wrong_secret_rejected(client):
    fake = jwt.encode(
        {"sub": str(uuid.uuid4()), "aud": "authenticated"}, "kisi-aur-ka-secret-jo-32-bytes-se-lamba-hai", algorithm="HS256"
    )
    response = client.get("/clients", headers={"Authorization": f"Bearer {fake}"})
    assert response.status_code == 401


def test_me_returns_token_user(client):
    user_id = str(uuid.uuid4())
    response = client.get("/auth/me", headers=make_token(user_id, "wahaj@example.com"))
    assert response.status_code == 200
    assert response.json() == {"id": user_id, "email": "wahaj@example.com"}


def test_client_crud(client, auth):
    created = client.post("/clients", json={"name": "Acme", "company": "Acme Ltd"}, headers=auth)
    assert created.status_code == 201
    cid = created.json()["id"]

    assert len(client.get("/clients", headers=auth).json()) == 1

    patched = client.patch(f"/clients/{cid}", json={"company": "Acme Pvt"}, headers=auth)
    assert patched.json()["company"] == "Acme Pvt"

    assert client.delete(f"/clients/{cid}", headers=auth).status_code == 204
    assert client.get(f"/clients/{cid}", headers=auth).status_code == 404


def test_client_name_cannot_be_set_to_null(client, auth, client_id):
    response = client.patch(f"/clients/{client_id}", json={"name": None}, headers=auth)
    assert response.status_code == 422


def test_other_users_client_is_hidden(client, client_id):
    assert client.get(f"/clients/{client_id}", headers=make_token()).status_code == 404


def test_meeting_create_and_search(client, auth, client_id):
    _meeting(client, auth, client_id)

    timeline = client.get(f"/clients/{client_id}/timeline", headers=auth).json()
    assert len(timeline) == 1
    assert timeline[0]["title"] == "Kickoff call"

    hits = client.get("/search", params={"q": "proposal"}, headers=auth).json()
    assert hits["count"] == 1
    assert hits["results"][0]["matched_in"] == "transcript"


def test_analyze_without_api_key_returns_503(client, auth, client_id):
    meeting = _meeting(client, auth, client_id)
    response = client.post(f"/meetings/{meeting['id']}/analyze", headers=auth)
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_reanalyze_does_not_duplicate_followups(client, auth, client_id, monkeypatch):
    monkeypatch.setattr(
        openai_service,
        "analyse_transcript",
        lambda transcript: openai_service.AnalysisResult(
            summary="Client ko design pasand aaya, budget ki fikr hai.",
            topics=["design", "budget"],
            concerns=["budget"],
            followups=[{"text": "Proposal bhejna", "owner": "Ahmed", "due_date": "2026-10-20"}],
            model_used="test-model",
        ),
    )
    meeting = _meeting(client, auth, client_id)
    client.post(
        "/followups",
        json={"client_id": client_id, "meeting_id": meeting["id"], "body": "Haath se likha"},
        headers=auth,
    )

    first = client.post(f"/meetings/{meeting['id']}/analyze", headers=auth)
    assert first.status_code == 200, first.text
    assert first.json()["summary"].startswith("Client ko design")
    client.post(f"/meetings/{meeting['id']}/analyze", headers=auth)

    items = client.get("/followups", params={"client_id": client_id}, headers=auth).json()
    assert sorted(f["body"] for f in items) == ["Haath se likha", "Proposal bhejna"]
    ai_item = next(f for f in items if f["source"] == "ai")
    assert ai_item["owner"] == "Ahmed"
    assert ai_item["due_date"] == "2026-10-20"

    detail = client.get(f"/meetings/{meeting['id']}", headers=auth).json()
    assert detail["topics"] == ["design", "budget"]


def test_followup_lifecycle(client, auth, client_id):
    created = client.post(
        "/followups",
        json={"client_id": client_id, "body": "Proposal bhejna hai", "owner": "Ahmed"},
        headers=auth,
    )
    assert created.status_code == 201
    fid = created.json()["id"]

    assert len(client.get("/followups", params={"status": "pending"}, headers=auth).json()) == 1

    done = client.patch(f"/followups/{fid}", json={"status": "done"}, headers=auth).json()
    assert done["status"] == "done"
    assert done["completed_at"] is not None

    dropped = client.patch(f"/followups/{fid}", json={"status": "dropped"}, headers=auth).json()
    assert dropped["status"] == "dropped"
    assert dropped["completed_at"] is None

    assert client.get("/followups", params={"status": "pending"}, headers=auth).json() == []


def test_followup_cannot_use_another_users_meeting(client, auth, client_id):
    other = make_token()
    other_client = client.post("/clients", json={"name": "Doosra"}, headers=other).json()
    other_meeting = _meeting(client, other, other_client["id"])

    response = client.post(
        "/followups",
        json={"client_id": client_id, "meeting_id": other_meeting["id"], "body": "Chori"},
        headers=auth,
    )
    assert response.status_code == 404


def test_dashboard_counts(client, auth, client_id):
    client.post("/followups", json={"client_id": client_id, "body": "Call karna hai"}, headers=auth)
    data = client.get("/dashboard", headers=auth).json()
    assert data["total_clients"] == 1
    assert data["pending_followups"] == 1


def test_bad_audio_format_rejected(client, auth, client_id):
    response = client.post(
        "/meetings/upload",
        data={"client_id": client_id, "title": "Call", "meeting_date": str(date.today())},
        files={"audio": ("notes.txt", b"hello world", "text/plain")},
        headers=auth,
    )
    assert response.status_code == 400
