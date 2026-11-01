"""Singleton ChromaDB HTTP client — analogous to db/engine.py."""

from __future__ import annotations

import chromadb
from chromadb import HttpClient

from app.config import settings

_client: HttpClient | None = None


def get_chroma_client() -> HttpClient:
    """Return the shared ChromaDB HTTP client. Created once, reused thereafter."""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    return _client
