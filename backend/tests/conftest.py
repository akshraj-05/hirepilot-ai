# conftest.py — shared setup that runs before every test file.
#
# The app uses PostgreSQL via asyncpg, but all API routes currently use
# in-memory storage (storage.py), not the database.
#
# We patch create_async_engine HERE (before any app module imports it) so
# tests get a mock engine and do not need a real database connection.

from unittest.mock import AsyncMock, MagicMock, patch

_mock_engine = MagicMock()
_mock_engine.dispose = AsyncMock(return_value=None)

# This runs before test files are imported, so the mock is in place
# when app.db.engine first calls create_async_engine().
patch("sqlalchemy.ext.asyncio.create_async_engine", return_value=_mock_engine).start()
