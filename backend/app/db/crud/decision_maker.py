import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.decision_maker import DecisionMaker


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    candidate_id: uuid.UUID,
    posted_job_id: str,
    match_score: float | None = None,
    skills_overlap_with_jd: list[str] | None = None,
    skills_missing_from_resume: list[str] | None = None,
    status: str | None = None,
    decision_reasons: list[str] | None = None,
) -> DecisionMaker:
    decision = DecisionMaker(
        org_id=org_id,
        candidate_id=candidate_id,
        posted_job_id=posted_job_id,
        match_score=match_score,
        skills_overlap_with_jd=skills_overlap_with_jd,
        skills_missing_from_resume=skills_missing_from_resume,
        status=status,
        decision_reasons=decision_reasons,
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    return decision


async def get(db: AsyncSession, decision_id: uuid.UUID) -> DecisionMaker | None:
    return await db.get(DecisionMaker, decision_id)


async def get_by_candidate_and_job(
    db: AsyncSession, candidate_id: uuid.UUID, posted_job_id: str
) -> DecisionMaker | None:
    result = await db.execute(
        select(DecisionMaker).where(
            DecisionMaker.candidate_id == candidate_id,
            DecisionMaker.posted_job_id == posted_job_id,
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def list_by_candidate(
    db: AsyncSession,
    candidate_id: uuid.UUID,
) -> list[DecisionMaker]:
    result = await db.execute(
        select(DecisionMaker)
        .where(DecisionMaker.candidate_id == candidate_id)
        .order_by(DecisionMaker.match_score.desc())
    )
    return list(result.scalars().all())


async def list_by_job(
    db: AsyncSession,
    posted_job_id: str,
    status: str | None = None,
) -> list[DecisionMaker]:
    q = select(DecisionMaker).where(DecisionMaker.posted_job_id == posted_job_id)
    if status:
        q = q.where(DecisionMaker.status == status)
    result = await db.execute(q.order_by(DecisionMaker.match_score.desc()))
    return list(result.scalars().all())


async def update(db: AsyncSession, decision_id: uuid.UUID, **kwargs) -> DecisionMaker | None:
    decision = await db.get(DecisionMaker, decision_id)
    if not decision:
        return None
    for key, value in kwargs.items():
        setattr(decision, key, value)
    await db.commit()
    await db.refresh(decision)
    return decision
