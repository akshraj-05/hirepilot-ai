"""Candidate CRUD, resume upload (BD-01, BD-08–BD-10, BD-13)."""

import io
import json
import uuid
import zipfile
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import Orchestrator
from app.db import crud
from app.db import get_db
from app.db.engine import AsyncSessionLocal
from app.services.resume_text import extract_resume_text

router = APIRouter(prefix="/candidates", tags=["candidates"])

_BATCH_SIZE = 10

def _parse_pg_array(val) -> list:
    """Convert PostgreSQL array string or Python list to a clean Python list."""
    if val is None:
        return []
    if isinstance(val, list):
        # Check if the list is character-by-character (each item is single char)
        # This can happen when a string is stored in ARRAY column
        if val and len(val) > 2 and all(isinstance(item, str) and len(item) == 1 for item in val[:5]):
            # Reconstruct the original string and parse
            reconstructed = ''.join(val)
            try:
                parsed = json.loads(reconstructed)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                elif isinstance(parsed, dict):
                    return [str(v) for v in parsed.values() if v]
            except (json.JSONDecodeError, ValueError):
                # Try extracting strings between quotes
                import re
                matches = re.findall(r'"([^"]*)"', reconstructed)
                if matches:
                    return matches
            return []
        # If first item is a JSON string, try to parse it
        if val and isinstance(val[0], str) and (val[0].startswith('[') or val[0].startswith('{')):
            try:
                parsed = json.loads(val[0])
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                elif isinstance(parsed, dict):
                    return [str(v) for v in parsed.values() if v]
            except (json.JSONDecodeError, ValueError):
                pass
        # Return as-is if it looks like a normal array of strings
        return [str(item) for item in val if item]
    if isinstance(val, str):
        val = val.strip()
        # Handle PostgreSQL array format: {"value1","value2"}
        if val.startswith("{") and val.endswith("}"):
            val = val[1:-1]  # strip { }
            # split by comma but respect quoted strings
            import csv
            reader = csv.reader([val], quotechar='"')
            return [item.strip() for item in next(reader) if item.strip()]
    return []

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _process_zip(
    content: bytes,
    job_id: str,
    organization_id: str,
) -> AsyncGenerator[str, None]:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            entries: list[tuple[str, str, bytes]] = []
            for name in zf.namelist():
                if name.startswith("__MACOSX") or name.endswith("/"):
                    continue
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                if ext in {"pdf", "docx"}:
                    filename = name.split("/")[-1]
                    entries.append((filename, ext, zf.read(name)))
    except zipfile.BadZipFile:
        yield _sse({"type": "error", "message": "Invalid ZIP file."})
        return

    if not entries:
        yield _sse({"type": "error", "message": "No PDF or DOCX files found in the ZIP."})
        return

    total = len(entries)
    yield _sse({"type": "start", "total": total})

    org_uuid = uuid.UUID(organization_id)

    async with AsyncSessionLocal() as db:
        org = await crud.organizations.get(db, org_uuid)
        org_name = org.name if org else organization_id

    orchestrator = Orchestrator()
    success = 0
    skipped = 0

    for batch_start in range(0, total, _BATCH_SIZE):
        batch = entries[batch_start: batch_start + _BATCH_SIZE]

        for i, (filename, ext, file_bytes) in enumerate(batch):
            current = batch_start + i + 1
            try:
                resume_text = extract_resume_text(file_bytes, ext)
                if len(resume_text.strip()) < 20:
                    raise ValueError("Could not extract enough text from file")

                async with AsyncSessionLocal() as db:
                    db_candidate = await crud.candidates.create(db, org_id=org_uuid)
                    db_resume = await crud.uploaded_resumes.create(
                        db,
                        org_id=org_uuid,
                        posted_job_id=job_id,
                        original_filename=filename,
                        file_path="",
                        file_size_bytes=len(file_bytes),
                        uploaded_by="system",
                    )
                    await crud.uploaded_resumes.mark_completed(
                        db, db_resume.id, db_candidate.id, resume_text
                    )
                    candidate_id = str(db_candidate.id)

                state = await orchestrator.run(
                    job_id=job_id,
                    candidates=[candidate_id],
                    organization_id=organization_id,
                    organization_name=org_name,
                )

                success += 1
                warnings: list[str] = []
                if state["decision_maker"]["status"] == "failed":
                    warnings.append("DecisionMaker failed")
                if state["insight_agent"]["status"] == "failed":
                    warnings.append("InsightAgent failed")

                evt: dict = {
                    "type": "progress",
                    "current": current,
                    "total": total,
                    "filename": filename,
                    "status": "success",
                }
                if warnings:
                    evt["reason"] = "; ".join(warnings)
                yield _sse(evt)

            except Exception as exc:
                skipped += 1
                yield _sse({
                    "type": "progress",
                    "current": current,
                    "total": total,
                    "filename": filename,
                    "status": "skipped",
                    "reason": str(exc),
                })

    yield _sse({"type": "complete", "total": total, "success": success, "skipped": skipped})


@router.get("")
async def list_candidates(
    organization_id: str = Query(..., description="Organization ID"),
    job_id: str = Query(..., description="Job ID"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """BD-08: list candidates for a job."""
    rows = await crud.candidates.list_by_job(db, uuid.UUID(organization_id), job_id)
    result = []
    for c in rows:
        dm = await crud.decision_maker.get_by_candidate_and_job(db, c.id, job_id)
        result.append({
            "id": str(c.id),
            "name": c.name or "Unknown",
            "score": round(float(dm.match_score)) if dm and dm.match_score is not None else 0,
            "status": (dm.override_status or dm.status or "REVIEW").upper() if dm else "REVIEW",
            "phone_number": c.mobile_number or "",
            "summary": c.experience_summary or "",
            "source_platform": c.source_platform or "manual",  # Return source platform (naukri, linkedin, etc.)
        })
    return result


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str | None = Form(default=None),
    job_id: str = Form(...),
    organization_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """BD-01: upload resume, extract text, and persist to DB."""
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"pdf", "docx"}:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")

    content = await file.read()
    await file.close()

    try:
        resume_text = extract_resume_text(bytes(content), ext)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read resume file: {exc}") from exc

    if len(resume_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Could not extract enough text from this file.")

    org_uuid = uuid.UUID(organization_id)

    db_candidate = await crud.candidates.create(
        db,
        org_id=org_uuid,
        name=candidate_name,
    )
    candidate_id = str(db_candidate.id)

    db_resume = await crud.uploaded_resumes.create(
        db,
        org_id=org_uuid,
        posted_job_id=job_id,
        original_filename=filename,
        file_path="",
        file_size_bytes=len(content),
        uploaded_by="system",
    )

    await crud.uploaded_resumes.mark_completed(
        db, db_resume.id, db_candidate.id, resume_text,
    )

    return {
        "candidate_id": candidate_id,
        "message": "Resume uploaded and parsed successfully",
    }


@router.post("/bulk-upload")
async def bulk_upload(
    files: list[UploadFile] = File(...),
    job_id: str = Form(...),
    organization_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """BD-13: upload multiple resumes, then run full AI pipeline on all at once."""
    org_uuid = uuid.UUID(organization_id)
    candidate_ids: list[str] = []

    # Step 1: save all resumes to DB
    for file in files:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in {"pdf", "docx"}:
            await file.close()
            continue
        content = await file.read()
        await file.close()

        try:
            resume_text = extract_resume_text(bytes(content), ext)
        except Exception:
            continue
        if len(resume_text.strip()) < 20:
            continue

        db_candidate = await crud.candidates.create(db, org_id=org_uuid)
        db_resume = await crud.uploaded_resumes.create(
            db,
            org_id=org_uuid,
            posted_job_id=job_id,
            original_filename=filename,
            file_path="",
            file_size_bytes=len(content),
            uploaded_by="system",
        )
        await crud.uploaded_resumes.mark_completed(
            db, db_resume.id, db_candidate.id, resume_text,
        )
        candidate_ids.append(str(db_candidate.id))

    # Step 2: run full AI pipeline on all saved candidates at once
    if candidate_ids:
        org = await crud.organizations.get(db, org_uuid)
        org_name = org.name if org else organization_id
        orchestrator = Orchestrator()
        await orchestrator.run(
            job_id=job_id,
            candidates=candidate_ids,
            organization_id=organization_id,
            organization_name=org_name,
        )

    return {"message": "Bulk upload successful", "count": len(candidate_ids)}


@router.post("/zip-upload")
async def zip_upload_stream(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    organization_id: str = Form(...),
) -> StreamingResponse:
    """Accept a ZIP of resumes, process in batches of 10, stream SSE progress."""
    content = await file.read()
    await file.close()
    return StreamingResponse(
        _process_zip(content, job_id, organization_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class UpdateStatusBody(BaseModel):
    status: str = Field(..., min_length=1)


@router.patch("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: str,
    body: UpdateStatusBody,
    organization_id: str = Query(..., description="Organization ID"),
    job_id: str = Query(..., description="Job ID"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """BD-10: update status for a candidate."""
    try:
        cid = uuid.UUID(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid candidate ID")

    candidate = await crud.candidates.get(db, cid)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

    try:
        dm = await crud.decision_maker.get_by_candidate_and_job(db, cid, job_id)
        if dm:
            await crud.decision_maker.update(
                db, dm.id, override_status=body.status.lower()
            )
    except Exception:
        pass

    return {"message": "Status updated"}


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    organization_id: str | None = Query(default=None),
    job_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """BD-09: candidate detail with match info."""
    try:
        cid = uuid.UUID(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid candidate ID")

    candidate = await crud.candidates.get(db, cid)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

    dm = None
    if job_id:
        dm = await crud.decision_maker.get_by_candidate_and_job(db, cid, job_id)

    return {
        "id": str(candidate.id),
        "name": candidate.name or "Unknown",
        "email": candidate.email,
        "mobile_number": candidate.mobile_number,
        "title": candidate.title,
        "years_experience": candidate.years_experience,
        "experience_summary": candidate.experience_summary,
        "project_summary": candidate.project_summary,
        "work_summary": candidate.work_summary,
        "skills": candidate.skills or [],
        "score": round(float(dm.match_score)) if dm and dm.match_score is not None else 0,
        "status": (dm.override_status or dm.status or "REVIEW").upper() if dm else "REVIEW",
        "matched_skills": dm.skills_overlap_with_jd or [] if dm else [],
        "missing_skills": dm.skills_missing_from_resume or [] if dm else [],
        "summary": candidate.experience_summary or "",
        "decision_reasons": dm.decision_reasons or [] if dm else [],
        "red_flags": _parse_pg_array(candidate.red_flags),
        "green_flags": _parse_pg_array(candidate.green_flags),
    }
