# Frontend — Next.js (TypeScript)

**Owner:** Abdul Rafey Ali Khan
**Deploy:** Vercel

Next.js app jo backend FastAPI ki API ko call karti hai. Sirf UI ka kaam — AI aur database ka koi kaam yahan nahi hota.

## Planned structure

```
frontend/
├── app/
│   ├── login/             # login / signup
│   ├── dashboard/         # counts, pending follow-ups
│   ├── clients/           # client list + timeline
│   ├── upload/            # transcript paste / audio upload
│   └── followups/         # follow-up tracker
├── components/            # reusable UI
├── lib/api.ts             # backend ko call karne wale functions
├── package.json
└── next.config.js
```

## Kaam ka order

- Week 5 — wireframes (`docs/wireframes/` mein)
- Week 6–8 — login, clients, upload screens
- Week 11–12 — dashboard, follow-ups, search

## Backend se connection

Frontend backend ko `NEXT_PUBLIC_API_URL` par call karega:

- Local: `http://localhost:8000`
- Production: Railway wala URL

## Seekhne ke liye (Rafey ke liye)

- TypeScript basics
- Next.js App Router (`app/` folder routing)
- `fetch` se API call karna
- Tailwind CSS styling ke liye

> Abhi khaali hai. Pehle wireframes banenge, phir Week 6 se `create-next-app` chalega.
