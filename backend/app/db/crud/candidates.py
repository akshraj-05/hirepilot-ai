import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.candidate import Candidate
from app.db.models.decision_maker import DecisionMaker
from app.db.models.uploaded_resume import UploadedResume


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    name: str | None = None,
    email: str | None = None,
    mobile_number: str | None = None,
    title: str | None = None,
    years_experience: int | None = None,
    experience_summary: str | None = None,
    project_summary: str | None = None,
    work_summary: str | None = None,
    skills: list[str] | None = None,
) -> Candidate:
    candidate = Candidate(
        org_id=org_id,
        name=name,
        email=email,
        mobile_number=mobile_number,
        title=title,
        years_experience=years_experience,
        experience_summary=experience_summary,
        project_summary=project_summary,
        work_summary=work_summary,
        skills=skills,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def get(db: AsyncSession, candidate_id: uuid.UUID) -> Candidate | None:
    return await db.get(Candidate, candidate_id)


async def get_by_email(db: AsyncSession, org_id: uuid.UUID, email: str) -> Candidate | None:
    result = await db.execute(
        select(Candidate).where(Candidate.org_id == org_id, Candidate.email == email)
    )
    return result.scalar_one_or_none()


async def list_by_org(db: AsyncSession, org_id: uuid.UUID) -> list[Candidate]:
    result = await db.execute(
        select(Candidate).where(Candidate.org_id == org_id).order_by(Candidate.created_at.desc())
    )
    return list(result.scalars().all())


async def list_by_job(db: AsyncSession, org_id: uuid.UUID, job_id: str) -> list[Candidate]:
    """Return candidates for a job — matched via uploaded_resumes OR decision_maker."""
    result = await db.execute(
        select(Candidate)
        .outerjoin(UploadedResume, (UploadedResume.candidate_id == Candidate.id) & (UploadedResume.posted_job_id == job_id))
        .outerjoin(DecisionMaker, (DecisionMaker.candidate_id == Candidate.id) & (DecisionMaker.posted_job_id == job_id))
        .where(
            Candidate.org_id == org_id,
            or_(
                UploadedResume.candidate_id.isnot(None),
                DecisionMaker.candidate_id.isnot(None),
            ),
        )
        .distinct()
        .order_by(Candidate.created_at.desc())
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, candidate_id: uuid.UUID, **kwargs) -> Candidate | None:
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        return None
    for key, value in kwargs.items():
        setattr(candidate, key, value)
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def delete(db: AsyncSession, candidate_id: uuid.UUID) -> bool:
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        return False
    await db.delete(candidate)
    await db.commit()
    return True
