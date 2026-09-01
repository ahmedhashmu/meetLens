# MeetLens

Client meeting recordings aur transcripts ko summary + follow-up items mein convert karne wali web application.

**Software Project Management — Group 08 — UBIT**

---

## Problem

Consulting firms bohot client meetings karti hain lekin unka proper record nahi rakhtin. Notes notebook ya loose file mein likhe jate hain, toh kuch hafton baad jab wohi client dobara contact kare, kisi ko yaad nahi hota kya promise kiya tha.

## Solution

User meeting ki recording upload karta hai ya transcript paste karta hai. AI model summary, concerns aur follow-up items return karta hai. Sab kuch client ke naam ke neeche save hota hai aur pending items ki email reminder jati hai.

## Objectives

- Clients add karna aur unke meeting transcripts / audio files upload karna
- OpenAI API se summary, topics, concerns aur follow-up items generate karna
- Har client ki past meetings ka timeline dikhana
- Follow-up items ko owner, due date aur status ke saath track karna + email reminders
- App ko public URL par deploy karna

## Scope

**In scope:** signup/login, client records, transcript paste, audio upload, AI summary aur follow-up extraction, follow-up tracker, client timeline, dashboard, keyword search, email reminders

**Out of scope:** live transcription, Zoom/Google Meet integration, mobile app, full CRM features, English ke ilawa languages, payments

## Tech Stack

| Area | Tool |
|---|---|
| Repository | GitHub — ek repo, paanchon members contributors |
| Frontend | **TypeScript** — Next.js + React, deployed on **Vercel** |
| Backend | **Python** — FastAPI, hosted on **Railway** |
| Database | **Neon** (PostgreSQL) |
| AI model | OpenAI API — summary, topics, concerns, follow-ups |
| Speech to text | OpenAI Whisper API |

Frontend TypeScript mein hai kyunke Vercel usi ke liye bana hai. Backend Python mein hai kyunke AI ka saara kaam (Whisper, OpenAI prompts) Python mein karna aasan hai. Dono HTTP API se baat karte hain.

## Team

| Member | Seat No. | Role |
|---|---|---|
| Syed Bilal | B24110006144 | Project manager — schedule, task board, weekly minutes |
| Ahmed Hashmi | B24110006080 | Backend & AI — FastAPI, Whisper, prompts |
| Abdul Rafey Ali Khan | B24110006004 | Frontend — Next.js/TypeScript screens aur wireframes |
| Ayesha | B24110006048 | Database & documentation — Neon schema, SRS, user guide |
| Wahaj | B24110006105 | Testing & deployment — test cases, defect log, deployment |

## Repository Structure

```
meetLens/
├── backend/      # Python — FastAPI + AI        (Ahmed)
├── frontend/     # TypeScript — Next.js         (Rafey)
├── docs/         # SRS, WBS, design, user guide (Ayesha)
├── tests/        # test cases, defect log       (Wahaj)
└── README.md
```

## Timeline (14 weeks)

| Phase | Weeks | Work |
|---|---|---|
| Initiation | 1–2 | Charter, repo aur task board setup, requirement gathering |
| Planning | 3–4 | SRS, WBS, Gantt chart, risk register |
| Design | 5 | Architecture, database schema, wireframes |
| Development 1 | 6–8 | Login, clients, transcript upload |
| Development 2 | 9–10 | Whisper audio-to-text aur OpenAI analysis |
| Development 3 | 11–12 | Dashboard, follow-up tracker, reminders, search |
| Testing | 13 | Testing, bug fixing, deployment (Vercel + Railway) |
| Closing | 14 | Documentation, presentation, demo |

## Working Rules

- Monday, Wednesday aur Friday ko WhatsApp par short update
- Har Sunday ek meeting, maximum ek ghanta, minutes project manager likhega
- Kisi bhi cheez ko review ke baghair `main` branch mein merge nahi kiya jayega
- API keys environment variables mein rahengi, repo mein kabhi push nahi hongi

## Status

🟡 **Week 1–2 — Initiation.** Repo setup ho chuka hai. Requirement gathering jaari hai.
