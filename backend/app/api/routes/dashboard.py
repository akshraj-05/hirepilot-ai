"""Dashboard aggregates (BD-12)."""

import uuid
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud, get_db
from app.db.models.candidate import Candidate
from app.db.models.decision_maker import DecisionMaker
from app.db.models.job_posting import JobPosting

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard_stats(
    organization_id: str = Query(..., description="Organization ID"),
    job_id: str = Query(..., description="Job ID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    rows = await crud.decision_maker.list_by_job(db, job_id)

    total = len(rows)
    shortlisted = 0
    rejected = 0
    review = 0

    for dm in rows:
        st = (dm.override_status or dm.status or "review").upper()
        if st == "SHORTLIST":
            shortlisted += 1
        elif st == "REJECT":
            rejected += 1
        else:
            review += 1

    return {
        "total": total,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "review": review,
    }


@router.get("/activity")
async def get_recent_activity(
    organization_id: str = Query(..., description="Organization ID"),
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return recent pipeline activity derived from decision_maker entries."""
    org_uuid = uuid.UUID(organization_id)

    result = await db.execute(
        select(DecisionMaker, Candidate, JobPosting)
        .join(Candidate, Candidate.id == DecisionMaker.candidate_id)
        .join(JobPosting, JobPosting.job_id == DecisionMaker.posted_job_id)
        .where(Candidate.org_id == org_uuid)
        .order_by(DecisionMaker.updated_at.desc())
        .limit(limit)
    )
    rows = result.all()

    items = []
    for dm, candidate, job in rows:
        status = (dm.override_status or dm.status or "review").lower()
        score = round(float(dm.match_score)) if dm.match_score is not None else 0
        items.append({
            "id": str(dm.id),
            "message": f"{candidate.name or 'Unknown'} analyzed for {job.role or job.job_id} — score {score}%",
            "time_label": dm.updated_at.strftime("%b %d, %H:%M") if dm.updated_at else "",
            "status": status,
        })
    return items


@router.get("/job-summary")
async def get_job_summary(
    organization_id: str = Query(..., description="Organization ID"),
    job_id: str = Query(..., description="Job ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return top candidates, missing skills frequency, and score distribution for a job."""
    org_uuid = uuid.UUID(organization_id)

    result = await db.execute(
        select(DecisionMaker, Candidate)
        .join(Candidate, Candidate.id == DecisionMaker.candidate_id)
        .where(DecisionMaker.posted_job_id == job_id)
        .where(Candidate.org_id == org_uuid)
        .order_by(DecisionMaker.match_score.desc())
    )
    rows = result.all()

    # Score distribution bands
    bands = {"0-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    missing_counter: Counter = Counter()
    top_candidates = []

    for dm, candidate in rows:
        score = round(float(dm.match_score)) if dm.match_score is not None else 0
        status = (dm.override_status or dm.status or "review").lower()

        if score < 40:
            bands["0-40"] += 1
        elif score < 60:
            bands["40-60"] += 1
        elif score < 80:
            bands["60-80"] += 1
        else:
            bands["80-100"] += 1

        if dm.skills_missing_from_resume:
            for skill in dm.skills_missing_from_resume:
                if skill:
                    missing_counter[skill.strip()] += 1

        if status == "shortlist" and len(top_candidates) < 5:
            top_candidates.append({
                "id": str(candidate.id),
                "name": candidate.name or "Unknown",
                "score": score,
                "status": status,
            })

    top_missing = [
        {"skill": skill, "count": count}
        for skill, count in missing_counter.most_common(10)
    ]

    return {
        "top_candidates": top_candidates,
        "missing_skills": top_missing,
        "score_distribution": [
            {"band": band, "count": count} for band, count in bands.items()
        ],
    }


@router.get("/insights")
async def get_insights(
    organization_id: str = Query(..., description="Organization ID"),
    job_id: str | None = Query(default=None, description="Job ID — omit or pass 'all' for org-wide"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    org_uuid = uuid.UUID(organization_id)
    if job_id and job_id != "all":
        rows = await crud.ai_insights.list_by_job(db, job_id)
    else:
        rows = await crud.ai_insights.list_by_org(db, org_uuid)
    return [
        {
            "id": str(r.id),
            "category": r.category,
            "insight": r.insight or "",
            "recommendation": r.recommendation or "",
            "skill_name": r.skill_name,
            "affected_count": r.affected_count,
            "posted_job_id": r.posted_job_id,
        }
        for r in rows
    ]
