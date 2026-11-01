# HirePilot AI

Web-based AI hiring workspace: **Next.js** dashboard (candidates, jobs, upload, analytics) and **FastAPI + LangChain** backend with **PostgreSQL** for persistence.

## Repository layout

| Path | Description |
|------|-------------|
| `frontend/` | Next.js 16 (App Router), Tailwind, Recharts |
| `backend/` | FastAPI, LangChain / OpenAI (optional key), PostgreSQL |
| `db/` | SQL schema and Docker Compose config |

## Prerequisites

- **Node.js** 20+ (for `frontend`)
- **Python** 3.10+ (for `backend`)
- **Docker** (for PostgreSQL)

## Quick start

### Step 1 — Start the database

```bash
docker compose up -d postgres
```

Wait a few seconds for Postgres to be ready.

### Step 2 — Start the backend

```bash
cd backend
pip install -e ".[dev]"
# .env is already present with defaults (DB URL, CORS, port).
# Optional: add OPENAI_API_KEY=sk-... to backend/.env for real AI.
# Without it the app works using mock AI responses.
bash run_dev.sh
```

- API: [http://localhost:4000](http://localhost:4000)
- Swagger docs: [http://localhost:4000/docs](http://localhost:4000/docs)

On startup the backend creates a **demo organization** in the database and loads any saved jobs, candidates and analysis results into memory.

### Step 3 — Start the frontend

```bash
cd frontend
npm install
# frontend/.env.local is already set to point to http://localhost:4000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How to use the app

1. **Upload & analyze** — pick or create a job, then upload a PDF/DOCX resume.
2. The backend runs AI analysis and saves everything to PostgreSQL.
3. **Candidates** — select the job to see the candidate list with match scores.
4. Click a candidate to see skills, match details, and the AI summary.
5. Use **Feedback & overrides** to change status — saved to the DB.
6. **Dashboard** — see the full hiring funnel across all jobs.

## Mock AI vs real AI

| Mode | When | Returns |
|------|------|---------|
| **Mock** | No `OPENAI_API_KEY` set (default) | Hard-coded scores and skill lists |
| **Real** | `OPENAI_API_KEY=sk-...` in `backend/.env` | Live OpenAI GPT responses |

The app is **fully usable in mock mode** — no API key required.

## Database persistence

- Data is stored in PostgreSQL via Docker and **survives backend restarts**.
- On every restart, jobs / candidates / analysis results are reloaded from the DB.
- Resume file bytes are not stored in DB — to re-analyze an old candidate after a restart, re-upload the file.

## Running tests

The backend has a full unit test suite covering all API endpoints. Tests use in-memory storage and **do not need a running database or an OpenAI key**.

### Install test dependencies (first time only)

```bash
cd backend
pip install pytest httpx
```

### Run all tests

```bash
cd backend
python3.10 -m pytest tests/ -v
```

### Run a single test file

```bash
# e.g. only jobs tests
python3.10 -m pytest tests/test_jobs.py -v

# e.g. only candidate tests
python3.10 -m pytest tests/test_candidates.py -v
```

### Test files

| File | API endpoints covered |
|------|-----------------------|
| `tests/test_health.py` | `GET /api/v1/health` |
| `tests/test_jobs.py` | Create job, list jobs, get job |
| `tests/test_candidates.py` | Upload, bulk-upload, parse, list, get, update status |
| `tests/test_analyze.py` | Analyze candidate, retry analysis |
| `tests/test_decision.py` | Get hiring decision |
| `tests/test_feedback.py` | Submit recruiter feedback |
| `tests/test_dashboard.py` | Dashboard stats |

### How tests handle the database

The `tests/conftest.py` mocks `create_async_engine` so tests run without a real database. Tests use the in-memory storage layer directly.

---

## Scripts

| Location | Command | Purpose |
|----------|---------|---------|
| root | `docker compose up -d postgres` | Start PostgreSQL |
| `frontend/` | `npm run dev` | Dev server (port 3000) |
| `frontend/` | `npm run build` | Production build |
| `backend/` | `bash run_dev.sh` | Dev API (auto-reload, port 4000) |
| `backend/` | `python3.10 -m pytest tests/ -v` | Run all tests |

## License

Add your organization's license as needed.


Command to run project

/hirepilot-ai - python mock_naukri_server.py
/hirepilot-ai- uvicorn backend.app.main:app --reload
/hirepilot-ai/frontend - npm run dev