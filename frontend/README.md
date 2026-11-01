# HirePilot AI — Frontend

Next.js (App Router) dashboard for job postings, candidates, resume upload, and analytics (Recharts).

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

[http://localhost:3000](http://localhost:3000)

## Mock data

The app runs on **static mock data** in `utils/mockData.ts` until the API is integrated. Search the codebase for `TODO(mock-removal)` before removing mocks.

## Env

See `.env.example`. `NEXT_PUBLIC_API_URL` is reserved for future API calls.

## More

See the monorepo **[../README.md](../README.md)** for backend setup and MR notes.
