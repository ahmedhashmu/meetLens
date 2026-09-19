"""MeetLens backend ke smoke tests."""
from datetime import date

TRANSCRIPT = (
    "Client ne kaha ke dashboard ka design pasand aaya. "
    "Unhein budget ki thori concern hai. Hum agle hafte proposal bhejenge."
)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_signup_duplicate_email_rejected(client):
    payload = {"name": "A", "email": "dup@example.com", "password": "password123"}
    assert client.post("/auth/signup", json=payload).status_code == 201
    assert client.post("/auth/signup", json=payload).status_code == 409


def test_login_wrong_password(client, auth):
    response = client.post(
        "/auth/login", json={"email": "ahmed@example.com", "password": "ghalat-password"}
    )
    assert response.status_code == 401


def test_password_is_hashed_not_plaintext(client, auth):
    """Bilal wale code ka masla — password kabhi plaintext save nahi hona chahiye."""
    from app.database import get_db
    from app.main import app
    from app.models import User

    db = next(app.dependency_overrides[get_db]())
    user = db.query(User).filter(User.email == "ahmed@example.com").first()
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2")


def test_endpoints_need_login(client):
    for path in ("/clients", "/dashboard", "/followups"):
        assert client.get(path).status_code == 401


def test_client_crud(client, auth):
    created = client.post("/clients", json={"name": "Acme", "company": "Acme Ltd"}, headers=auth)
    assert created.status_code == 201
    cid = created.json()["id"]

    assert len(client.get("/clients", headers=auth).json()) == 1

    patched = client.patch(f"/clients/{cid}", json={"company": "Acme Pvt"}, headers=auth)
    assert patched.json()["company"] == "Acme Pvt"

    assert client.delete(f"/clients/{cid}", headers=auth).status_code == 204
    assert client.get(f"/clients/{cid}", headers=auth).status_code == 404


def test_other_users_client_is_hidden(client, auth, client_id):
    other = client.post(
        "/auth/signup",
        json={"name": "Wahaj", "email": "wahaj@example.com", "password": "password123"},
    ).json()
    headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/clients/{client_id}", headers=headers).status_code == 404


def test_meeting_create_and_search(client, auth, client_id):
    created = client.post(
        "/meetings",
        json={
            "client_id": client_id,
            "title": "Kickoff call",
            "meeting_date": str(date.today()),
            "transcript": TRANSCRIPT,
        },
        headers=auth,
    )
    assert created.status_code == 201, created.text

    timeline = client.get(f"/clients/{client_id}/timeline", headers=auth).json()
    assert len(timeline) == 1
    assert timeline[0]["title"] == "Kickoff call"

    hits = client.get("/search", params={"q": "proposal"}, headers=auth).json()
    assert hits["count"] == 1
    assert hits["results"][0]["matched_in"] == "transcript"


def test_analyze_without_api_key_returns_503(client, auth, client_id):
    meeting = client.post(
        "/meetings",
        json={
            "client_id": client_id,
            "title": "Call",
            "meeting_date": str(date.today()),
            "transcript": TRANSCRIPT,
        },
        headers=auth,
    ).json()

    response = client.post(f"/meetings/{meeting['id']}/analyze", headers=auth)
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_followup_lifecycle(client, auth, client_id):
    created = client.post(
        "/followups",
        json={"client_id": client_id, "text": "Proposal bhejna hai", "owner": "Ahmed"},
        headers=auth,
    )
    assert created.status_code == 201
    fid = created.json()["id"]

    assert len(client.get("/followups", params={"status": "pending"}, headers=auth).json()) == 1

    done = client.patch(f"/followups/{fid}", json={"status": "done"}, headers=auth).json()
    assert done["status"] == "done"
    assert done["completed_at"] is not None

    assert client.get("/followups", params={"status": "pending"}, headers=auth).json() == []


def test_dashboard_counts(client, auth, client_id):
    client.post(
        "/followups",
        json={"client_id": client_id, "text": "Call karna hai"},
        headers=auth,
    )
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
