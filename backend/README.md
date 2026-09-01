# Backend — FastAPI (Python)

**Owner:** Ahmed Hashmi
**Deploy:** Railway

FastAPI API server + saara AI ka kaam. Frontend isay HTTP se call karta hai.

## Planned structure

```
backend/
├── app/
│   ├── main.py            # FastAPI entry point + CORS (Vercel URL allow)
│   ├── config.py          # env variables load
│   ├── database.py        # Neon connection
│   ├── models.py          # users, clients, meetings, followups
│   ├── schemas.py         # request / response models
│   ├── routers/           # auth, clients, meetings, followups
│   └── services/
│       ├── openai_service.py    # summary, topics, concerns, follow-ups
│       ├── whisper_service.py   # audio → transcript
│       └── email_service.py     # follow-up reminders
└── requirements.txt
```

## Kaam ka order

- Week 6–8 — auth, clients CRUD, transcript save
- Week 9–10 — Whisper transcription + OpenAI analysis
- Week 11–12 — follow-up tracker, search, email reminders

## Zaroori baat

CORS mein Vercel ka frontend URL allow karna hoga, warna browser API calls block kar dega.

> Abhi khaali hai. Code Week 6 se shuru hoga — pehle DB schema final karna hai.
