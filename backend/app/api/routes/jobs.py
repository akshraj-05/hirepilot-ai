"""Job CRUD (BD-03, BD-04, BD-05)."""

import uuid
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db import get_db
from app.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


class CreateJobBody(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    organization_id: str = Field(..., min_length=1)


@router.post("")
async def create_job(
    body: CreateJobBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    job_id = uuid.uuid4().hex[:16]
    org_uuid = uuid.UUID(body.organization_id)

    await crud.job_postings.create(
        db,
        job_id=job_id,
        organization_id=org_uuid,
        role=body.title,
        description=body.description,
        status="open",
    )

    # Trigger auto-sync from Naukri integration in background
    asyncio.create_task(
        _auto_sync_candidates(db, org_uuid, job_id, body.title, body.description)
    )

    return {"job_id": job_id}


@router.get("")
async def list_jobs(
    organization_id: str = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str]]:
    org_uuid = uuid.UUID(organization_id)
    rows = await crud.job_postings.list_by_org(db, org_uuid)
    return [
        {
            "job_id": job.job_id,
            "title": job.role or "",
            "job_description": job.description or "",
            "status": job.status or "draft",
            "date_posted": str(job.date_posted) if job.date_posted else str(job.created_at.date()),
        }
        for job in rows
    ]


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    organization_id: str = Query(..., description="Organization ID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    org_uuid = uuid.UUID(organization_id)
    job = await crud.job_postings.get(db, job_id)
    if job is None or str(job.organization_id) != str(org_uuid):
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "title": job.role or "",
        "description": job.description or "",
    }


class UpdateStatusBody(BaseModel):
    status: str = Field(..., pattern="^(open|closed|draft|paused)$")
    organization_id: str = Field(..., min_length=1)


@router.patch("/{job_id}/status")
async def update_job_status(
    job_id: str,
    body: UpdateStatusBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    org_uuid = uuid.UUID(body.organization_id)
    job = await crud.job_postings.get(db, job_id)
    if job is None or str(job.organization_id) != str(org_uuid):
        raise HTTPException(status_code=404, detail="Job not found")
    updated = await crud.job_postings.update(db, job_id, status=body.status)
    return {"job_id": job_id, "status": updated.status}


async def _auto_sync_candidates(
    db: AsyncSession,
    org_id: uuid.UUID,
    job_id: str,
    job_title: str,
    job_description: str,
) -> None:
    """Auto-sync ALL candidates from Naukri when a new job is created.

    Fetches all available candidates (no keyword filtering).
    The orchestration pipeline will calculate match scores based on job description and resume.
    """
    try:
        integration_service = IntegrationService(db)

        # Check if Naukri integration is active
        integration = await integration_service.get_integration(org_id, "naukri")
        if not integration:
            logger.debug(f"No active Naukri integration for org {org_id}")
            return

        # Fetch ALL candidates (no keyword filtering)
        # The orchestration pipeline will match them against the job description
        filters = {
            "keywords": None,  # Fetch all candidates
            "location": None,
            "experience_min_years": None,
            "experience_max_years": None,
            "skills": None,
        }

        logger.info(f"Auto-syncing ALL candidates from Naukri for job {job_id} (title: {job_title})")

        # Sync candidates from Naukri
        sync_log = await integration_service.sync_candidates(
            integration_id=integration.id,
            org_id=org_id,
            job_id=job_id,
            filters=filters,
            limit=100,  # Increased limit to fetch more candidates
        )

        logger.info(
            f"Auto-sync completed for job {job_id}: "
            f"{sync_log.candidates_processed} processed, "
            f"{sync_log.candidates_failed} failed, "
            f"{sync_log.candidates_deduplicated} deduplicated"
        )

    except Exception as e:
        logger.error(f"Failed to auto-sync candidates for job {job_id}: {e}", exc_info=True)
