"""Async SQLAlchemy engine and session factory."""

import re

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _build_async_url(raw_url: str) -> str:
    """Normalise a postgres URL for asyncpg:
    - swap postgresql:// → postgresql+asyncpg://
    - replace psycopg2-style sslmode=require with asyncpg ssl=require
    """
    url = raw_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Remove psycopg2 sslmode param (not understood by asyncpg)
    url = re.sub(r"[?&]sslmode=[^&]*", "", url)
    # Add asyncpg ssl=require for Supabase if not already set
    if "supabase.co" in url and "ssl=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}ssl=require"
    return url


db_url = _build_async_url(settings.database_url)

engine = create_async_engine(
    db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
