"""ChromaDB vector store wrapper for compatibility."""

from __future__ import annotations

from app.chroma.client import get_chroma_client
from app.chroma.embeddings import get_embedding_fn


class ChromaVectorStore:
    """ChromaDB vector store wrapper."""

    def __init__(self):
        self._client = get_chroma_client()
        self._embedding_fn = get_embedding_fn()
        self._collections: dict = {}

    def get_or_create_collection(self, name: str, **kwargs):
        """Get or create a collection in ChromaDB."""
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                embedding_function=self._embedding_fn,
                metadata=kwargs.get("metadata", {"hnsw:space": "cosine"}),
            )
        return self._collections[name]

    def close(self) -> None:
        """Close the ChromaDB client (no-op for HTTP client)."""
        pass
