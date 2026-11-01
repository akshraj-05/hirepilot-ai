import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scheduled_meeting import ScheduledMeeting


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    candidate_id: uuid.UUID,
    posted_job_id: str,
    title: str,
    meeting_type: str,
    scheduled_at: datetime,
    interviewer_name: str,
    interviewer_email: str,
    duration_mins: int = 30,
    meeting_link: str | None = None,
    location: str | None = None,
    notes: str | None = None,
) -> ScheduledMeeting:
    meeting = ScheduledMeeting(
        org_id=org_id,
        candidate_id=candidate_id,
        posted_job_id=posted_job_id,
        title=title,
        meeting_type=meeting_type,
        scheduled_at=scheduled_at,
        interviewer_name=interviewer_name,
        interviewer_email=interviewer_email,
        duration_mins=duration_mins,
        meeting_link=meeting_link,
        location=location,
        notes=notes,
        status="scheduled",
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    return meeting


async def get(db: AsyncSession, meeting_id: uuid.UUID) -> ScheduledMeeting | None:
    return await db.get(ScheduledMeeting, meeting_id)


async def list_by_org(db: AsyncSession, org_id: uuid.UUID) -> list[ScheduledMeeting]:
    result = await db.execute(
        select(ScheduledMeeting)
        .where(ScheduledMeeting.org_id == org_id)
        .order_by(ScheduledMeeting.scheduled_at)
    )
    return list(result.scalars().all())


async def list_by_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> list[ScheduledMeeting]:
    result = await db.execute(
        select(ScheduledMeeting)
        .where(ScheduledMeeting.candidate_id == candidate_id)
        .order_by(ScheduledMeeting.scheduled_at)
    )
    return list(result.scalars().all())


async def list_by_job(db: AsyncSession, posted_job_id: str) -> list[ScheduledMeeting]:
    result = await db.execute(
        select(ScheduledMeeting)
        .where(ScheduledMeeting.posted_job_id == posted_job_id)
        .order_by(ScheduledMeeting.scheduled_at)
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, meeting_id: uuid.UUID, **kwargs) -> ScheduledMeeting | None:
    meeting = await db.get(ScheduledMeeting, meeting_id)
    if not meeting:
        return None
    for key, value in kwargs.items():
        setattr(meeting, key, value)
    await db.commit()
    await db.refresh(meeting)
    return meeting


async def delete(db: AsyncSession, meeting_id: uuid.UUID) -> bool:
    meeting = await db.get(ScheduledMeeting, meeting_id)
    if not meeting:
        return False
    await db.delete(meeting)
    await db.commit()
    return True
