"""
ChromaDB collection registry — get-or-create helpers for each collection.

Collections:
  CANDIDATES   — one document per candidate; embeds resume text.
  ASSESSMENTS  — one document per (candidate, job); embeds resume-analyzer assessment text.
  DECISIONS    — one document per (candidate, job) pair; embeds decision output.
  INSIGHTS     — one document per insight run; embeds insight summary text.
"""

from __future__ import annotations

import chromadb

from app.chroma.client import get_chroma_client
from app.chroma.embeddings import get_embedding_fn

CANDIDATES_COLLECTION = "candidates"
ASSESSMENTS_COLLECTION = "assessments"
DECISIONS_COLLECTION = "decisions"
INSIGHTS_COLLECTION = "insights"


def get_candidates_collection() -> chromadb.Collection:
    """Return (or create) the candidates collection."""
    return get_chroma_client().get_or_create_collection(
        name=CANDIDATES_COLLECTION,
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def get_assessments_collection() -> chromadb.Collection:
    """Return (or create) the assessments collection (embedded resume-analyzer output per job)."""
    return get_chroma_client().get_or_create_collection(
        name=ASSESSMENTS_COLLECTION,
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def get_decisions_collection() -> chromadb.Collection:
    """Return (or create) the decisions collection."""
    return get_chroma_client().get_or_create_collection(
        name=DECISIONS_COLLECTION,
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

def get_insights_collection() -> chromadb.Collection:
    """Return (or create) the insights collection."""
    return get_chroma_client().get_or_create_collection(
        name=INSIGHTS_COLLECTION,
        embedding_function=get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )
