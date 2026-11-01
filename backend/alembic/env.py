from logging.config import fileConfig
import re
from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy.engine import Connection

from alembic import context

# Add app to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.models.base import Base
from app.config import settings


def _build_sync_url(raw_url: str) -> str:
    """Convert any postgres URL variant to a psycopg2-compatible sync URL."""
    url = raw_url
    # Strip asyncpg driver if present
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    # asyncpg ssl=require param → psycopg2 sslmode=require
    url = re.sub(r"[?&]ssl=require", "", url)
    # Ensure sslmode=require is present for Supabase
    if "supabase.co" in url and "sslmode=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    return url


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Escape % for configparser interpolation (e.g. %40 in passwords)
sync_url = _build_sync_url(settings.database_url)
config.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL, no connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the live database using a sync psycopg2 connection."""
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
