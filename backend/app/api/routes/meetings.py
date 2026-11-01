"""Scheduled meetings CRUD."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud, get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])


class CreateMeetingBody(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    posted_job_id: str = Field(..., min_length=1)
    organization_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    meeting_type: str = Field(..., min_length=1)
    scheduled_at: str = Field(..., min_length=1)
    duration_mins: int = Field(default=30, ge=5)
    interviewer_name: str = Field(..., min_length=1)
    interviewer_email: str = Field(..., min_length=1)
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None


def _row_to_dict(m) -> dict[str, Any]:
    return {
        "id": str(m.id),
        "org_id": str(m.org_id),
        "candidate_id": str(m.candidate_id),
        "posted_job_id": m.posted_job_id,
        "title": m.title or "",
        "meeting_type": m.meeting_type or "screening",
        "status": m.status or "scheduled",
        "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else "",
        "duration_mins": m.duration_mins or 30,
        "meeting_link": m.meeting_link,
        "location": m.location,
        "interviewer_name": m.interviewer_name or "",
        "interviewer_email": m.interviewer_email or "",
        "notes": m.notes,
        "created_at": m.created_at.isoformat() if m.created_at else "",
        "updated_at": m.updated_at.isoformat() if m.updated_at else "",
    }


# DB enum values vs frontend values
_TYPE_TO_DB = {
    "phone_screen": "screening",
    "hr_round": "behavioral",
    "offer": "culture_fit",
    "technical": "technical",
    "final": "final",
}
_TYPE_FROM_DB = {v: k for k, v in _TYPE_TO_DB.items()}


@router.post("")
async def create_meeting(
    body: CreateMeetingBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        raw = body.scheduled_at.replace("Z", "+00:00")
        scheduled_dt = datetime.fromisoformat(raw).replace(tzinfo=None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Bad date format: {exc}") from exc

    db_type = _TYPE_TO_DB.get(body.meeting_type, body.meeting_type)

    meeting = await crud.scheduled_meetings.create(
        db,
        org_id=uuid.UUID(body.organization_id),
        candidate_id=uuid.UUID(body.candidate_id),
        posted_job_id=body.posted_job_id,
        title=body.title,
        meeting_type=db_type,
        scheduled_at=scheduled_dt,
        duration_mins=body.duration_mins,
        interviewer_name=body.interviewer_name,
        interviewer_email=body.interviewer_email,
        meeting_link=body.meeting_link,
        location=body.location,
        notes=body.notes,
    )

    result = _row_to_dict(meeting)
    result["meeting_type"] = _TYPE_FROM_DB.get(result["meeting_type"], result["meeting_type"])
    return result


@router.get("")
async def list_meetings(
    organization_id: str = Query(default="demo-org"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = await crud.scheduled_meetings.list_by_org(db, uuid.UUID(organization_id))
    out = []
    for m in rows:
        d = _row_to_dict(m)
        d["meeting_type"] = _TYPE_FROM_DB.get(d["meeting_type"], d["meeting_type"])
        out.append(d)
    return out


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    deleted = await crud.scheduled_meetings.delete(db, uuid.UUID(meeting_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting deleted"}
