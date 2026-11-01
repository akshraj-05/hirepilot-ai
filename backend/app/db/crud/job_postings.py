import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job_posting import JobPosting


async def create(
    db: AsyncSession,
    *,
    job_id: str,
    organization_id: uuid.UUID,
    role: str | None = None,
    description: str | None = None,
    date_posted: date | None = None,
    status: str = "draft",
) -> JobPosting:
    job = JobPosting(
        job_id=job_id,
        organization_id=organization_id,
        role=role,
        description=description,
        date_posted=date_posted,
        status=status,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get(db: AsyncSession, job_id: str) -> JobPosting | None:
    return await db.get(JobPosting, job_id)


async def list_by_org(
    db: AsyncSession,
    org_id: uuid.UUID,
    status: str | None = None,
) -> list[JobPosting]:
    q = select(JobPosting).where(JobPosting.organization_id == org_id)
    if status:
        q = q.where(JobPosting.status == status)
    result = await db.execute(q.order_by(JobPosting.date_posted.desc()))
    return list(result.scalars().all())


async def update(db: AsyncSession, job_id: str, **kwargs) -> JobPosting | None:
    job = await db.get(JobPosting, job_id)
    if not job:
        return None
    for key, value in kwargs.items():
        setattr(job, key, value)
    await db.commit()
    await db.refresh(job)
    return job


async def delete(db: AsyncSession, job_id: str) -> bool:
    job = await db.get(JobPosting, job_id)
    if not job:
        return False
    await db.delete(job)
    await db.commit()
    return True
