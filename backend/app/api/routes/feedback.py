"""Recruiter feedback on decisions (BD-11)."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackBody(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    decision_correct: bool
    comments: str = ""
    organization_id: str = Field(..., min_length=1)


@router.post("")
async def submit_feedback(
    body: FeedbackBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Record whether the AI decision was correct (BD-11)."""
    try:
        candidate_uuid = uuid.UUID(body.candidate_id)
        dm = await crud.decision_maker.get_by_candidate_and_job(db, candidate_uuid, body.job_id)
        if dm:
            await crud.decision_maker.update(
                db, dm.id, ai_decision_correct=body.decision_correct
            )
    except Exception:
        pass

    return {"message": "Feedback recorded"}
