import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.activity_log import ActivityLog


async def get(db: AsyncSession, log_id: uuid.UUID) -> ActivityLog | None:
    return await db.get(ActivityLog, log_id)


async def log(
    db: AsyncSession,
    *,
    actor: str,
    action: str,
    message: str,
    posted_job_id: str | None = None,
    candidate_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        posted_job_id=posted_job_id,
        candidate_id=candidate_id,
        actor=actor,
        action=action,
        message=message,
        meta=metadata,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_by_job(
    db: AsyncSession, posted_job_id: str, limit: int = 50
) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.posted_job_id == posted_job_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_by_candidate(
    db: AsyncSession, candidate_id: uuid.UUID, limit: int = 50
) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.candidate_id == candidate_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_recent(db: AsyncSession, limit: int = 100) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
