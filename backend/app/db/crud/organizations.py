import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.organization import Organization


async def create(
    db: AsyncSession,
    *,
    name: str,
    slug: str,
    domain: str | None = None,
    logo_url: str | None = None,
) -> Organization:
    org = Organization(name=name, slug=slug, domain=domain, logo_url=logo_url)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def get(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
    return await db.get(Organization, org_id)


async def get_by_slug(db: AsyncSession, slug: str) -> Organization | None:
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession) -> list[Organization]:
    result = await db.execute(select(Organization))
    return list(result.scalars().all())


async def update(db: AsyncSession, org_id: uuid.UUID, **kwargs) -> Organization | None:
    org = await db.get(Organization, org_id)
    if not org:
        return None
    for key, value in kwargs.items():
        setattr(org, key, value)
    await db.commit()
    await db.refresh(org)
    return org


async def delete(db: AsyncSession, org_id: uuid.UUID) -> bool:
    org = await db.get(Organization, org_id)
    if not org:
        return False
    await db.delete(org)
    await db.commit()
    return True
