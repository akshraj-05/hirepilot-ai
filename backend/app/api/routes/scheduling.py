"""Candidate invitation URL: pick one offered slot, then auto-schedule the meeting."""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import crud, get_db
from app.services import google_auth, google_calendar, google_gmail

log = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


class CreateInviteBody(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    posted_job_id: str = Field(..., min_length=1)
    proposed_slots: list[str] = Field(..., min_length=1, max_length=20)


class ChooseSlotBody(BaseModel):
    selected_slot: str = Field(..., min_length=1)


def _parse_iso_naive(s: str) -> datetime:
    raw = s.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(raw)
    return dt.replace(tzinfo=None)


def _normalize_slots(proposed: list[Any]) -> list[str]:
    out: list[str] = []
    for p in proposed:
        try:
            dt = _parse_iso_naive(str(p))
            out.append(dt.isoformat(timespec="seconds"))
        except ValueError:
            continue
    return out


def _match_choice(proposed: list[Any], selected: str) -> datetime | None:
    try:
        want = _parse_iso_naive(selected)
    except ValueError:
        return None
    for p in proposed:
        try:
            if _parse_iso_naive(str(p)) == want:
                return _parse_iso_naive(str(p))
        except ValueError:
            continue
    return None


@router.post("/invites")
async def create_invite(
    body: CreateInviteBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    raw_id = (body.candidate_id or "").strip()
    try:
        cid = uuid.UUID(raw_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "candidate_id must be a UUID (example: "
                '"550e8400-e29b-41d4-a716-446655440000"). '
                "Copy the candidate id from GET /api/candidates?organization_id=demo-org&job_id=YOUR_JOB "
                "or from the candidate page URL /candidates/<uuid>."
            ),
        ) from exc

    cand = await crud.candidates.get(db, cid)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not cand.email:
        raise HTTPException(
            status_code=400,
            detail="Candidate email not available. Please update the candidate record.",
        )

    job = await crud.job_postings.get(db, body.posted_job_id)
    if not job or str(job.organization_id) != str(cand.org_id):
        raise HTTPException(status_code=404, detail="Job not found")

    parsed: list[str] = []
    for s in body.proposed_slots:
        try:
            raw = s.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw).replace(tzinfo=None)
            parsed.append(dt.isoformat(timespec="seconds"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid datetime: {s!r}") from exc

    inv = await crud.availability_invites.create(
        db,
        org_id=cand.org_id,
        candidate_id=cid,
        posted_job_id=body.posted_job_id,
        proposed_slots=parsed,
    )
    token = str(inv.token)

    origin = request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    frontend_base = origin if origin else settings.frontend_url
    scheduling_url = f"{frontend_base}/scheduling/{token}"
    job_title = job.role if job else body.posted_job_id
    candidate_name = cand.name or "Candidate"

    html_body = google_gmail.build_scheduling_email_html(
        candidate_name=candidate_name,
        job_title=job_title,
        scheduling_url=scheduling_url,
    )

    try:
        sent = await google_gmail.send_email(
            to=cand.email,
            subject=f"Schedule Your Interview — {job_title}",
            html_body=html_body,
        )
    except Exception as exc:
        log.exception("Gmail send failed — rolling back invite")
        await crud.availability_invites.delete(db, inv)
        raise HTTPException(status_code=500, detail=f"Email send failed: {exc}") from exc

    if not sent:
        await crud.availability_invites.delete(db, inv)
        raise HTTPException(
            status_code=503,
            detail="Google account not connected. Please connect Google first.",
        )

    return {"token": token, "path": f"/scheduling/{token}"}


@router.get("/invites/invited-candidates")
async def list_invited_candidate_ids(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return all candidate IDs with active invites, including their tokens."""
    invites = await crud.availability_invites.get_active_invites_summary(db)
    return {
        "invites": [
            {
                "candidate_id": str(inv.candidate_id),
                "token": str(inv.token),
                "status": inv.status,
            }
            for inv in invites
        ],
    }


@router.get("/invites/check")
async def check_candidate_invite(
    candidate_id: str,
    posted_job_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check if a candidate already has an active (open/confirmed) invite.

    When posted_job_id is provided the check is scoped to that specific job,
    so a candidate invited for Job A is not blocked from being invited for Job B.
    """
    try:
        cid = uuid.UUID(candidate_id)
    except ValueError:
        return {"has_invite": False}

    if posted_job_id:
        inv = await crud.availability_invites.get_latest_by_candidate_and_job(
            db, cid, posted_job_id
        )
    else:
        inv = await crud.availability_invites.get_latest_by_candidate(db, cid)

    if not inv or inv.status not in ("open", "confirmed"):
        return {"has_invite": False}
    return {
        "has_invite": True,
        "status": inv.status,
        "token": str(inv.token),
    }


@router.get("/invites/{token}")
async def get_invite(token: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    inv = await crud.availability_invites.get_by_token(db, token)
    if not inv:
        raise HTTPException(status_code=404, detail="Link not found")

    cand = await crud.candidates.get(db, inv.candidate_id)
    job = await crud.job_postings.get(db, inv.posted_job_id)

    out: dict[str, Any] = {
        "status": inv.status,
        "proposed_slots": _normalize_slots(inv.proposed_slots or []),
        "job_title": job.role if job else inv.posted_job_id,
        "candidate_name": (cand.name if cand else "Candidate") or "Candidate",
    }
    if inv.status == "confirmed" and inv.selected_slot:
        out["selected_slot"] = inv.selected_slot.isoformat()
    return out


@router.post("/invites/{token}/send-email")
async def send_invite_email(
    token: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Send the scheduling link to the candidate's email via Gmail API."""
    inv = await crud.availability_invites.get_by_token(db, token)
    if not inv:
        raise HTTPException(status_code=404, detail="Link not found")

    cand = await crud.candidates.get(db, inv.candidate_id)
    if not cand or not cand.email:
        raise HTTPException(
            status_code=400,
            detail="Candidate email not available. Please update the candidate record.",
        )

    job = await crud.job_postings.get(db, inv.posted_job_id)
    job_title = job.role if job else inv.posted_job_id
    candidate_name = cand.name or "Candidate"

    origin = request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    frontend_base = origin if origin else settings.frontend_url
    scheduling_url = f"{frontend_base}/scheduling/{token}"

    html_body = google_gmail.build_scheduling_email_html(
        candidate_name=candidate_name,
        job_title=job_title,
        scheduling_url=scheduling_url,
    )

    try:
        sent = await google_gmail.send_email(
            to=cand.email,
            subject=f"Schedule Your Interview — {job_title}",
            html_body=html_body,
        )
    except Exception as exc:
        log.exception("Gmail send failed")
        raise HTTPException(status_code=500, detail=f"Email send failed: {exc}") from exc

    if not sent:
        raise HTTPException(
            status_code=503,
            detail="Google account not connected. Please connect Google first.",
        )

    return {"message": f"Scheduling email sent to {cand.email}"}


@router.post("/invites/{token}/choose")
async def choose_slot(
    token: uuid.UUID,
    body: ChooseSlotBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    inv = await crud.availability_invites.get_by_token(db, token)
    if not inv:
        raise HTTPException(status_code=404, detail="Link not found")
    if inv.status != "open":
        raise HTTPException(status_code=409, detail="This link has already been used")

    chosen = _match_choice(inv.proposed_slots or [], body.selected_slot)
    if chosen is None:
        raise HTTPException(status_code=400, detail="Pick one of the listed slots")

    await crud.availability_invites.confirm_slot(db, inv, selected_slot=chosen)

    cand = await crud.candidates.get(db, inv.candidate_id)
    job = await crud.job_postings.get(db, inv.posted_job_id)
    candidate_name = (cand.name if cand else "Candidate") or "Candidate"
    candidate_email = cand.email if cand else None
    job_title = job.role if job else inv.posted_job_id

    user_email = google_auth.get_user_email()

    attendee_emails: list[str] = []
    if user_email:
        attendee_emails.append(user_email)
    if candidate_email:
        attendee_emails.append(candidate_email)

    meeting_link: str | None = None
    event_id: str | None = None

    try:
        event = await google_calendar.create_event(
            summary=f"Interview — {job_title} — {candidate_name}",
            description=f"Interview for the {job_title} position with {candidate_name}.\nScheduled via HirePilot AI.",
            start_time=chosen,
            duration_mins=30,
            attendee_emails=attendee_emails,
        )
        if event:
            meeting_link = event.get("hangoutLink")
            event_id = event.get("id")
    except Exception:
        log.exception("Google Calendar event creation failed (non-blocking)")

    meeting_record = None
    try:
        meeting_record = await crud.scheduled_meetings.create(
            db,
            org_id=inv.org_id,
            candidate_id=inv.candidate_id,
            posted_job_id=inv.posted_job_id,
            title=f"Interview — {job_title} — {candidate_name}",
            meeting_type="screening",
            scheduled_at=chosen,
            duration_mins=30,
            interviewer_name=user_email or "HR Team",
            interviewer_email=user_email or "",
            meeting_link=meeting_link,
        )
    except Exception:
        log.exception("Meeting DB record creation failed (non-blocking)")

    return {
        "message": "Slot confirmed. Meeting scheduled!",
        "selected_slot": chosen.isoformat(),
        "meeting_link": meeting_link,
        "calendar_event_id": event_id,
        "meeting_id": str(meeting_record.id) if meeting_record else None,
    }
