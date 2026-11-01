import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


async def create(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    email: str,
    password_hash: str,
    name: str | None = None,
    role: str = "recruiter",
) -> User:
    user = User(org_id=org_id, email=email, password_hash=password_hash, name=name, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_by_org(db: AsyncSession, org_id: uuid.UUID) -> list[User]:
    result = await db.execute(
        select(User).where(User.org_id == org_id).order_by(User.created_at)
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, user_id: uuid.UUID, **kwargs) -> User | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete(db: AsyncSession, user_id: uuid.UUID) -> bool:
    user = await db.get(User, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
