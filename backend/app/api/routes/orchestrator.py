"""Orchestrator endpoint — single entry point for the full agent pipeline."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import Orchestrator
from app.db import crud, get_db

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

_orchestrator: Orchestrator | None = None


def _get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


class OrchestratorBody(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    organization_id: str = Field(..., min_length=1)


@router.post("")
async def run_orchestrator(body: OrchestratorBody, db: AsyncSession = Depends(get_db)) -> dict:
    """Run the full agent pipeline: ResumeAnalyzer → DecisionMaker → InsightAgent."""
    org = await crud.organizations.get(db, uuid.UUID(body.organization_id))
    organization_name = org.name if org else body.organization_id

    try:
        state = await _get_orchestrator().run(
            job_id=body.job_id,
            candidates=[body.candidate_id],
            organization_id=body.organization_id,
            organization_name=organization_name,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "job_id": state["job_id"],
        "candidates": state["candidates"],
        "resume_analyzer": {
            "status": state["resume_analyzer"]["status"],
            "analyzed_candidates": state["resume_analyzer"]["analyzed_candidates"],
        },
        "decision_maker": {
            "status": state["decision_maker"]["status"],
            "decisions": state["decision_maker"]["decisions"],
        },
        "insight_agent": {
            "status": state["insight_agent"]["status"],
            "insights": state["insight_agent"]["insights"],
        },
    }
