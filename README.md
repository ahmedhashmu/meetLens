# MeetLens

A full-stack web application that turns client meeting recordings and transcripts into summaries and tracked follow-up items, with AI-powered analysis. Built for the **Software Project Management** course — **Group 08, UBIT**.

## Overview

Consulting firms hold many client meetings but rarely keep a proper record of them. Notes end up in notebooks or loose files, and a few weeks later, when the same client gets in touch again, nobody remembers what was promised.

MeetLens fixes this. A user uploads a meeting recording or pastes its transcript. The system transcribes the audio, runs an AI analysis that extracts a summary, topics, client concerns and follow-up items, and stores everything under the client's name. Pending follow-ups are tracked with an owner, a due date and a status, and email reminders go out for items that are due.

### Key Principles

- **Client-Centric**: Every meeting, analysis and follow-up belongs to a client, giving a complete history of each relationship
- **Source vs. Derived Data**: The transcript is the source record; the AI analysis is stored separately and can be regenerated
- **Bounded AI**: The model has a single purpose, returns a fixed JSON schema, and is told never to invent facts
- **Per-User Isolation**: Users only ever see their own clients, meetings and follow-ups

## Tech Stack

### Frontend
- **Next.js 16** (App Router)
- **TypeScript**
- **React 19**
- **Supabase JS** client
- Deployed on **Vercel**

### Backend
- **Python 3.13+**
- **FastAPI** for the REST API
- **SQLAlchemy 2** for the database ORM
- **Pydantic** for request/response validation
- **Supabase Auth** for login — the backend verifies Supabase JWTs (PyJWT, ES256 via JWKS)
- Deployed on **Railway**

### AI Layer
- **OpenAI `gpt-4o-mini`** for meeting analysis (JSON mode)
- **OpenAI Whisper** (`whisper-1`) for speech-to-text

### Database
- **PostgreSQL** in production (Supabase)
- **SQLite** for local development (used automatically when `DATABASE_URL` is empty)

## Project Structure

```
meetLens/
├── frontend/                # Next.js application (Rafey)
│   ├── app/                 # App Router pages: dashboard, login, client detail
│   ├── lib/                 # Supabase client, auth context, analysis helper
│   └── package.json
├── backend/                 # Python FastAPI application (Ahmed)
│   ├── app/
│   │   ├── routers/         # auth, clients, meetings, followups, dashboard
│   │   ├── services/        # OpenAI, Whisper, email, security (Supabase JWT)
│   │   ├── models.py        # Database tables
│   │   ├── schemas.py       # Request/response models
│   │   ├── database.py      # Engine and session setup
│   │   └── main.py          # FastAPI entry point
│   ├── sql/                 # SQL to run once in Supabase
│   └── requirements.txt
├── tests/                   # Backend API tests, test plan, defect log (Wahaj)
├── docs/                    # SRS, WBS, design, user guide (Ayesha)
├── .env.example             # Environment variable template
└── README.md
```

## Getting Started

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.13+** and pip
- **PostgreSQL** (optional — SQLite is used for local dev)
- **OpenAI API key** (optional — only analysis and transcription need it)

### Local Development Setup

#### 1. Clone the repository

```bash
git clone https://github.com/ahmedhashmu/meetLens.git
cd meetLens
```

#### 2. Set up the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # then fill in real values
```

Key variables in `backend/.env`:

```env
DATABASE_URL=                       # leave empty for local SQLite
SUPABASE_URL=https://your-project.supabase.co
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1
FRONTEND_URL=http://localhost:3000
```

On local SQLite the tables are created automatically. On Supabase, run the files in `backend/sql/` once in the SQL Editor. Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs are available at `http://localhost:8000/docs`.

#### 3. Set up the frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_or_publishable_key
```

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### Running Tests

From the repository root:

```bash
python -m pytest tests -q
```

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Dashboard   │  │Client Detail │  │ Login/Signup │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │
│  │  Clients & │ │  Analysis  │ │ Follow-ups │ │ Search & │  │
│  │  Meetings  │ │   Engine   │ │ & Reminders│ │ Dashboard│  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Layer (OpenAI)                         │
│        Whisper (speech-to-text) · GPT (JSON analysis)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (PostgreSQL)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │Users/Clients │  │   Meetings   │  │  Analyses &  │       │
│  │              │  │ (transcripts)│  │  Follow-ups  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Meeting Ingestion**: User pastes a transcript, or uploads audio → Whisper converts it to text → stored as a meeting under the client
2. **Analysis**: User triggers analysis → transcript sent to the model → JSON validated and cleaned → summary, topics and concerns saved on the meeting; follow-ups saved as tracked items (re-analysing replaces the old AI follow-ups instead of duplicating them)
3. **Tracking**: Follow-ups move from `pending` to `done`; overdue items are flagged; due items trigger an email reminder
4. **Dashboard**: Counts, recent meetings, upcoming follow-ups and keyword search across transcripts and summaries

### Data Model

| Table | Purpose |
|---|---|
| `auth.users` | App users — managed by Supabase Auth |
| `clients` | A user's clients — name, company, email, notes |
| `meetings` | One meeting per row — title, date, source (`paste` / `audio`), transcript, and its AI analysis (summary, topics, concerns, model, analysed time) |
| `followups` | Action items — body, owner, due date, status (`pending` / `done` / `dropped`), source (`ai` / `manual`), completion and reminder timestamps |

### API Endpoints

| Method & Route | Purpose |
|---|---|
| `GET /auth/me` | Current user from the Supabase token (signup/login happen in the frontend via Supabase) |
| `GET POST /clients` · `GET PATCH DELETE /clients/{id}` | Client CRUD |
| `GET /clients/{id}/timeline` | A client's meeting history |
| `POST /meetings` | Create a meeting from a pasted transcript |
| `POST /meetings/upload` | Upload audio → Whisper → transcript |
| `POST /meetings/{id}/analyze` | Run AI analysis on a meeting |
| `GET POST /followups` · `PATCH DELETE /followups/{id}` | Follow-up tracker (filter by client, status, overdue) |
| `POST /followups/remind` | Email a reminder for due/overdue follow-ups |
| `GET /dashboard` · `GET /search?q=` | Dashboard counts and keyword search |
| `GET /health` | Health check |

#### Example: `POST /meetings/{id}/analyze`

**Response:**
```json
{
  "summary": "The client liked the dashboard design but is concerned about the budget...",
  "topics": ["dashboard design", "budget", "proposal"],
  "concerns": ["budget is tight"],
  "model_used": "gpt-4o-mini",
  "analyzed_at": "2026-10-09T10:15:00Z"
}
```

Follow-up items extracted by the analysis are saved to the `followups` table and returned by `GET /followups`.

## AI Usage Explanation

### Bounded Agent Design

The analysis step is constrained so its output is predictable and testable:

1. **Structured Prompt**: The system prompt specifies exactly four JSON keys and their types
2. **JSON Mode**: The model is called with `response_format = json_object` and low temperature (0.2)
3. **Validation & Cleaning**: Every field is type-checked, trimmed and length-capped; a missing summary is rejected
4. **Hard Limits**: At most 10 topics, 10 concerns and 15 follow-ups; transcripts are capped at 48,000 characters
5. **No Invention**: The prompt forbids facts not in the transcript and requires `null` for unknown owners and dates
6. **Retry Logic**: Up to 3 attempts before returning a clear error
7. **Graceful Degradation**: Without an API key, analysis and transcription return `503` while the rest of the app keeps working

## Deployment

### Frontend — Vercel

Set these environment variables in the Vercel dashboard (type **Config**, since they are public by design), then redeploy:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Backend — Railway

Set these environment variables in Railway:

- `DATABASE_URL`
- `SUPABASE_URL`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `WHISPER_MODEL`
- `FRONTEND_URL` (the Vercel URL, for CORS)
- `ENVIRONMENT=production`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` (optional, for reminders)

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

In production the app refuses to start without `SUPABASE_URL`, since it could not verify logins.

## Engineering Decisions

### Ownership Checks on Every Request

Every client, meeting and follow-up lookup goes through an ownership helper. A record that belongs to another user returns `404`, not `403`, so the API never reveals that it exists.

### One Login, One Database

The frontend and backend share one Supabase project. Users sign in with Supabase Auth; the frontend sends the Supabase access token to the backend, which verifies it against the project's public keys (JWKS). There is no second user table or password store.

### Source vs. Derived Data

Transcripts are the source record. The AI analysis fields can be regenerated at any time by re-running the analysis, without touching the transcript. AI follow-ups are marked `source = ai`, so re-analysis replaces only those and never the user's own items.

### Secrets Never in the Repository

All keys come from environment variables. `.env` files are git-ignored, and `.env.example` holds placeholders only.

### Scalability at 10× Usage

Primary bottleneck: OpenAI calls (analysis and Whisper run inside the request).

Solutions:
- Move analysis and transcription to a background job queue
- Store audio in object storage instead of memory
- Rate-limit analysis per user

Secondary bottlenecks: keyword search with `ILIKE`, unpaginated lists.

Solutions:
- PostgreSQL full-text search indexes
- Pagination on clients, meetings and follow-ups

## Assumptions and Limitations

### Assumptions

- Meetings are in English
- Recordings are uploaded after the meeting (no live capture)
- Each client belongs to a single user (no shared team workspaces)

### Limitations

- No live transcription, and no Zoom / Google Meet integration
- Audio files are limited to 25 MB (Whisper API limit)
- Email reminders are sent on request, not on a schedule
- Schema changes are plain SQL files in `backend/sql/`, run by hand in Supabase (no migration tool yet)
- The frontend currently reads Supabase directly with a placeholder keyword-based analysis; connecting it to the FastAPI backend is in progress
- No mobile app, payments or full CRM features (out of scope)

## Testing

Backend API tests use an isolated SQLite database per test and cover:

- Health check
- Login required on protected endpoints; forged tokens rejected
- Current user read from the Supabase token
- Client CRUD and per-user isolation
- Meeting creation, timeline and keyword search
- Analysis returns `503` without an API key
- Re-analysis does not duplicate follow-ups (OpenAI mocked)
- Follow-up lifecycle (pending → done → dropped), cross-user meeting rejected, dashboard counts
- Invalid audio formats rejected

```bash
python -m pytest tests -q
```

## Team

| Member | Seat No. | Role |
|---|---|---|
| Syed Bilal | B24110006144 | Project manager — schedule, task board, weekly minutes |
| Ahmed Hashmi | B24110006080 | Backend & AI — FastAPI, Whisper, prompts |
| Abdul Rafey Ali Khan | B24110006004 | Frontend — Next.js/TypeScript screens and wireframes |
| Ayesha | B24110006048 | Database & documentation — schema, SRS, user guide |
| Wahaj | B24110006105 | Testing & deployment — test cases, defect log, deployment |

## Timeline (14 weeks)

| Phase | Weeks | Work |
|---|---|---|
| Initiation | 1–2 | Charter, repo and task board setup, requirement gathering |
| Planning | 3–4 | SRS, WBS, Gantt chart, risk register |
| Design | 5 | Architecture, database schema, wireframes |
| Development 1 | 6–8 | Login, clients, transcript upload |
| Development 2 | 9–10 | Whisper audio-to-text and OpenAI analysis |
| Development 3 | 11–12 | Dashboard, follow-up tracker, reminders, search |
| Testing | 13 | Testing, bug fixing, deployment (Vercel + Railway) |
| Closing | 14 | Documentation, presentation, demo |

## Working Rules

- Short WhatsApp update on Monday, Wednesday and Friday
- One meeting every Sunday, maximum one hour; the project manager writes the minutes
- Nothing is merged into `main` without review
- API keys live in environment variables and are never pushed to the repository

## License

This project was created for the Software Project Management course at UBIT, University of Karachi.
