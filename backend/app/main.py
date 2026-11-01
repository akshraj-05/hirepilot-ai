"""FastAPI entrypoint — HirePilot AI API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import auth, candidates, dashboard, feedback, google_auth, health, jobs, meetings, orchestrator, scheduling, integrations
from app.config import settings
from app.db.engine import AsyncSessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="HirePilot AI API",
    description="Backend for AI-assisted hiring (FastAPI + LangChain + PostgreSQL).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_API_PREFIXES = ("/api/v1", "/api")

app.include_router(health.router, prefix="/api/v1")
for _p in _API_PREFIXES:
    app.include_router(auth.router, prefix=_p)
    app.include_router(candidates.router, prefix=_p)
    app.include_router(jobs.router, prefix=_p)
    app.include_router(feedback.router, prefix=_p)
    app.include_router(dashboard.router, prefix=_p)
    app.include_router(meetings.router, prefix=_p)
    app.include_router(scheduling.router, prefix=_p)
    app.include_router(orchestrator.router, prefix=_p)
    app.include_router(google_auth.router, prefix=_p)
    app.include_router(integrations.router, prefix=_p)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "HirePilot AI API",
        "docs": "/docs",
        "api": "/api/v1",
    }
