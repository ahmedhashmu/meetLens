# Frontend — Next.js (TypeScript)

**Owner:** Abdul Rafey Ali Khan
**Deploy:** Vercel

## Chalane ka tareeqa

```bash
cd frontend
npm install
cp ../.env.example .env.local     # phir Supabase ki asli values daalein
npm run dev                       # http://localhost:3000
```

Zaroori env variables (Supabase → Project Settings → API):

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

## Vercel par deploy

1. vercel.com → **Add New → Project** → GitHub se `meetLens` import karein
2. **Root Directory** = `frontend` (ye zaroori hai, warna build fail hogi)
3. **Environment Variables** mein upar wale dono daal dein
4. **Deploy**

## Screens

| Route | Kaam |
|---|---|
| `/` | Counts + client add karna + clients ki list |
| `/clients/[id]` | Client ki timeline, transcript paste karna, follow-up tracker |

## Files

```
frontend/
├── app/
│   ├── layout.tsx              # header + global styles
│   ├── page.tsx                # dashboard + clients
│   ├── clients/[id]/page.tsx   # client detail
│   └── globals.css
└── lib/
    ├── supabase.ts             # Supabase client + types
    └── analyze.ts              # DEMO ke liye aarzi analysis
```

## ⚠️ Zaroori baat — `lib/analyze.ts`

Abhi transcript ki analysis **browser mein keyword matching se** hoti hai, AI se nahi.
Ye sirf demo dikhane ke liye hai.

Asli AI analysis `backend/app/services/openai_service.py` mein likhi hui hai.
Jab backend Railway par deploy ho jaye to `analyze.ts` hata kar us API ko call karna hai.
