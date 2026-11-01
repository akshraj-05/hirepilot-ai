import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.uploaded_resume import UploadedResume


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    posted_job_id: str,
    original_filename: str,
    file_path: str,
    file_size_bytes: int,
    uploaded_by: str,
) -> UploadedResume:
    resume = UploadedResume(
        org_id=org_id,
        posted_job_id=posted_job_id,
        original_filename=original_filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        uploaded_by=uploaded_by,
        processing_status="pending",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def get(db: AsyncSession, resume_id: uuid.UUID) -> UploadedResume | None:
    return await db.get(UploadedResume, resume_id)


async def list_by_job(db: AsyncSession, posted_job_id: str) -> list[UploadedResume]:
    result = await db.execute(
        select(UploadedResume)
        .where(UploadedResume.posted_job_id == posted_job_id)
        .order_by(UploadedResume.created_at.desc())
    )
    return list(result.scalars().all())


async def list_by_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> list[UploadedResume]:
    result = await db.execute(
        select(UploadedResume)
        .where(UploadedResume.candidate_id == candidate_id)
        .order_by(UploadedResume.created_at.desc())
    )
    return list(result.scalars().all())


async def mark_processing(db: AsyncSession, resume_id: uuid.UUID) -> UploadedResume | None:
    return await update(db, resume_id, processing_status="processing")


async def mark_completed(
    db: AsyncSession,
    resume_id: uuid.UUID,
    candidate_id: uuid.UUID,
    parsed_resume_text: str,
) -> UploadedResume | None:
    return await update(
        db,
        resume_id,
        processing_status="completed",
        candidate_id=candidate_id,
        parsed_resume_text=parsed_resume_text,
        parsed_at=datetime.utcnow(),
    )


async def mark_failed(
    db: AsyncSession, resume_id: uuid.UUID, error_message: str
) -> UploadedResume | None:
    return await update(db, resume_id, processing_status="failed", error_message=error_message)


async def get_parsed_text_by_candidates(
    db: AsyncSession, candidate_ids: list[uuid.UUID]
) -> dict[uuid.UUID, str]:
    """Return {candidate_id: parsed_resume_text} for the given candidates."""
    if not candidate_ids:
        return {}
    result = await db.execute(
        select(UploadedResume.candidate_id, UploadedResume.parsed_resume_text)
        .where(
            UploadedResume.candidate_id.in_(candidate_ids),
            UploadedResume.parsed_resume_text.isnot(None),
        )
        .order_by(UploadedResume.created_at.desc())
    )
    mapping: dict[uuid.UUID, str] = {}
    for cid, text in result.all():
        if cid not in mapping:
            mapping[cid] = text
    return mapping


async def delete_by_candidate(db: AsyncSession, candidate_id: uuid.UUID) -> int:
    """Delete all uploaded_resumes for a candidate. Returns count deleted."""
    result = await db.execute(
        select(UploadedResume).where(UploadedResume.candidate_id == candidate_id)
    )
    rows = result.scalars().all()
    for resume in rows:
        await db.delete(resume)
    await db.commit()
    return len(rows)


async def update(db: AsyncSession, resume_id: uuid.UUID, **kwargs) -> UploadedResume | None:
    resume = await db.get(UploadedResume, resume_id)
    if not resume:
        return None
    for key, value in kwargs.items():
        setattr(resume, key, value)
    await db.commit()
    await db.refresh(resume)
    return resume
