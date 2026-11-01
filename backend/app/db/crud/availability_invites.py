import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.availability_invite import AvailabilityInvite


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    candidate_id: uuid.UUID,
    posted_job_id: str,
    proposed_slots: list[str],
) -> AvailabilityInvite:
    row = AvailabilityInvite(
        org_id=org_id,
        candidate_id=candidate_id,
        posted_job_id=posted_job_id,
        proposed_slots=proposed_slots,
        status="open",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_by_token(db: AsyncSession, token: uuid.UUID) -> AvailabilityInvite | None:
    result = await db.execute(select(AvailabilityInvite).where(AvailabilityInvite.token == token))
    return result.scalar_one_or_none()


async def get_latest_by_candidate(
    db: AsyncSession, candidate_id: uuid.UUID
) -> AvailabilityInvite | None:
    result = await db.execute(
        select(AvailabilityInvite)
        .where(AvailabilityInvite.candidate_id == candidate_id)
        .order_by(AvailabilityInvite.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_by_candidate_and_job(
    db: AsyncSession, candidate_id: uuid.UUID, posted_job_id: str
) -> AvailabilityInvite | None:
    result = await db.execute(
        select(AvailabilityInvite)
        .where(
            AvailabilityInvite.candidate_id == candidate_id,
            AvailabilityInvite.posted_job_id == posted_job_id,
        )
        .order_by(AvailabilityInvite.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_active_invites_summary(
    db: AsyncSession,
) -> list[AvailabilityInvite]:
    """Return the latest active invite per candidate (open or confirmed)."""
    result = await db.execute(
        select(AvailabilityInvite)
        .where(AvailabilityInvite.status.in_(("open", "confirmed")))
        .order_by(AvailabilityInvite.created_at.desc())
    )
    seen: set[uuid.UUID] = set()
    out: list[AvailabilityInvite] = []
    for inv in result.scalars().all():
        if inv.candidate_id not in seen:
            seen.add(inv.candidate_id)
            out.append(inv)
    return out


async def delete(db: AsyncSession, invite: AvailabilityInvite) -> None:
    await db.delete(invite)
    await db.commit()


async def confirm_slot(
    db: AsyncSession,
    invite: AvailabilityInvite,
    *,
    selected_slot: datetime,
) -> AvailabilityInvite:
    invite.status = "confirmed"
    invite.selected_slot = selected_slot
    await db.commit()
    await db.refresh(invite)
    return invite
