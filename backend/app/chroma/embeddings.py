"""
Embedding function factory — returns the right ChromaDB EmbeddingFunction
based on EMBEDDING_PROVIDER in config.

  local  → chromadb.utils.embedding_functions.DefaultEmbeddingFunction
           (all-MiniLM-L6-v2, bundled, no API key)
  openai → chromadb.utils.embedding_functions.OpenAIEmbeddingFunction
  gemini → chromadb.utils.embedding_functions.GoogleGenerativeAiEmbeddingFunction

All three implement chromadb.EmbeddingFunction so callers are provider-agnostic.
"""

from __future__ import annotations

from chromadb import EmbeddingFunction
from chromadb.utils import embedding_functions

from app.config import settings

_embedding_fn: EmbeddingFunction | None = None


def get_embedding_fn() -> EmbeddingFunction:
    """Singleton embedding function; provider selected by EMBEDDING_PROVIDER env var."""
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn

    provider = settings.embedding_provider.lower()

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for embedding_provider=openai."
            )
        _embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.openai_embedding_model,
        )

    elif provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is required for embedding_provider=gemini."
            )
        _embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_embedding_model,
        )

    else:  # "local" — default, no API key needed
        _embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    return _embedding_fn
