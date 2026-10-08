# Backend — FastAPI (Python)

**Owner:** Ahmed Hashmi
**Deploy:** Railway (abhi deploy nahi hua)

FastAPI API server + saara AI ka kaam.

## Chalane ka tareeqa

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env          # phir asli values daalein
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

`DATABASE_URL` khaali chhor dein to local SQLite ban jati hai — Supabase ke baghair bhi chalta hai.
`OPENAI_API_KEY` ke baghair sab kuch chalta hai siwaye analysis/transcription ke (wo 503 deti hain).

## Tests

```bash
.venv/bin/python -m pytest ../tests -q     # 14 tests
```

## API

| Route | Kaam |
|---|---|
| `GET /auth/me` | Supabase token se current user (login/signup frontend par Supabase karta hai) |
| `GET POST /clients` · `GET PATCH DELETE /clients/{id}` | Clients CRUD |
| `GET /clients/{id}/timeline` | Client ki meetings ki timeline |
| `POST /meetings` | Transcript paste karke meeting banana |
| `POST /meetings/upload` | Audio upload → Whisper → transcript |
| `POST /meetings/{id}/analyze` | OpenAI se summary, topics, concerns, follow-ups |
| `GET POST /followups` · `PATCH DELETE /followups/{id}` | Follow-up tracker |
| `POST /followups/remind` | Due follow-ups ki email reminder |
| `GET /dashboard` · `GET /search` | Counts aur keyword search |

## Structure

```
backend/app/
├── main.py         # FastAPI + CORS
├── config.py       # env variables (koi secret hardcode nahi)
├── database.py     # SQLAlchemy — Supabase/Neon ya SQLite
├── models.py       # clients, meetings, followups (Supabase wali tables)
├── schemas.py      # request/response models
├── deps.py         # auth + ownership checks
├── routers/        # auth, clients, meetings, followups, dashboard
└── services/
    ├── security.py         # Supabase JWT verify
    ├── openai_service.py   # summary, topics, concerns, follow-ups
    ├── whisper_service.py  # audio → transcript
    └── email_service.py    # follow-up reminders
```

## Zaroori baatein

- CORS mein Vercel ka URL allow karna hoga (`FRONTEND_URL`), warna browser calls block karega.
- Har user sirf apne clients dekh sakta hai — ownership check `deps.py` mein hai.
- Production mein `SUPABASE_URL` na ho to app start hi nahi hogi.
- Supabase par naye columns ke liye `sql/` ki files SQL Editor mein chalani hain.
