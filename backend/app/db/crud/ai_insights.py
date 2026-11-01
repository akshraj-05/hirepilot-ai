import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_insight import AIInsight


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    posted_job_id: str | None = None,
    category: str,
    insight: str,
    recommendation: str,
    skill_name: str | None = None,
    affected_count: int | None = None,
) -> AIInsight:
    ai_insight = AIInsight(
        org_id=org_id,
        posted_job_id=posted_job_id,
        category=category,
        insight=insight,
        recommendation=recommendation,
        skill_name=skill_name,
        affected_count=affected_count,
    )
    db.add(ai_insight)
    await db.commit()
    await db.refresh(ai_insight)
    return ai_insight


async def get(db: AsyncSession, insight_id: uuid.UUID) -> AIInsight | None:
    return await db.get(AIInsight, insight_id)


async def list_by_job(
    db: AsyncSession,
    posted_job_id: str,
    category: str | None = None,
) -> list[AIInsight]:
    q = select(AIInsight).where(AIInsight.posted_job_id == posted_job_id)
    if category:
        q = q.where(AIInsight.category == category)
    result = await db.execute(q.order_by(AIInsight.created_at.desc()))
    return list(result.scalars().all())


async def list_by_org(db: AsyncSession, org_id: uuid.UUID) -> list[AIInsight]:
    """Returns all insights for an org — used for the 'All Jobs' view."""
    result = await db.execute(
        select(AIInsight)
        .where(AIInsight.org_id == org_id)
        .order_by(AIInsight.created_at.desc())
    )
    return list(result.scalars().all())


async def delete(db: AsyncSession, insight_id: uuid.UUID) -> bool:
    insight = await db.get(AIInsight, insight_id)
    if not insight:
        return False
    await db.delete(insight)
    await db.commit()
    return True
