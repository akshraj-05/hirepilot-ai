"""
PostgreSQL pgvector-based vector store.
Provides a ChromaDB-like interface for vector operations using Supabase PostgreSQL.

Usage:
    store = await PgvectorStore.create()
    collection = await store.get_or_create_collection("candidates")
    await collection.add(ids, documents, embeddings, metadatas)
    results = await collection.query(query_embeddings)
"""

from __future__ import annotations

from typing import Any

import asyncpg
from app.config import settings


class PgvectorCollection:
    """A Pgvector collection similar to ChromaDB Collection."""

    def __init__(
        self,
        name: str,
        connection: asyncpg.Connection,
        embedding_dimension: int = 384,  # Default for all-MiniLM-L6-v2
    ):
        self.name = name
        self.connection = connection
        self.embedding_dimension = embedding_dimension
        self.table_name = f"vector_{name}"

    async def _init_table(self) -> None:
        """Create table if it doesn't exist."""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id TEXT PRIMARY KEY,
            document TEXT,
            embedding vector({self.embedding_dimension}),
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_embedding
            ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """
        await self.connection.execute(create_table_sql)

    async def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents with embeddings to collection."""
        if metadatas is None:
            metadatas = [{} for _ in ids]

        for id_, document, embedding, metadata in zip(
            ids, documents, embeddings, metadatas
        ):
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await self.connection.execute(
                f"""
                INSERT INTO {self.table_name} (id, document, embedding, metadata)
                VALUES ($1, $2, $3::vector, $4)
                ON CONFLICT (id) DO UPDATE SET
                    document = $2,
                    embedding = $3::vector,
                    metadata = $4,
                    updated_at = NOW()
                """,
                id_,
                document,
                embedding_str,
                metadata,
            )

    async def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query collection by embedding similarity."""
        if not query_embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        results = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        for query_embedding in query_embeddings:
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            where_clause = ""
            where_params = []

            if where:
                conditions = []
                i = 1
                for key, value in where.items():
                    conditions.append(f"metadata->>'{key}' = ${i}")
                    where_params.append(str(value))
                    i += 1
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)

            sql = f"""
            SELECT id, document, metadata,
                   1 - (embedding <=> $1::vector) as similarity
            FROM {self.table_name}
            {where_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT {n_results}
            """

            rows = await self.connection.fetch(sql, embedding_str, *where_params)

            ids_list = []
            docs_list = []
            metas_list = []
            distances_list = []

            for row in rows:
                ids_list.append(row["id"])
                docs_list.append(row["document"])
                metas_list.append(dict(row["metadata"]))
                distances_list.append(1 - row["similarity"])  # Convert similarity to distance

            results["ids"].append(ids_list)
            results["documents"].append(docs_list)
            results["metadatas"].append(metas_list)
            results["distances"].append(distances_list)

        return results

    async def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Upsert documents with embeddings."""
        await self.add(ids, documents, embeddings, metadatas)

    async def delete(self, ids: list[str]) -> None:
        """Delete documents by IDs."""
        placeholders = ",".join(f"${i}" for i in range(1, len(ids) + 1))
        await self.connection.execute(
            f"DELETE FROM {self.table_name} WHERE id IN ({placeholders})",
            *ids,
        )

    async def count(self) -> int:
        """Count documents in collection."""
        result = await self.connection.fetchval(
            f"SELECT COUNT(*) FROM {self.table_name}"
        )
        return result or 0


class PgvectorStore:
    """PostgreSQL pgvector store for managing multiple collections."""

    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        self._collections: dict[str, PgvectorCollection] = {}

    @classmethod
    async def create(cls) -> PgvectorStore:
        """Create a new PgvectorStore instance."""
        # Parse DATABASE_URL to extract connection params
        db_url = settings.database_url
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        elif db_url.startswith("postgresql://"):
            pass
        else:
            raise ValueError(f"Unsupported DATABASE_URL: {db_url}")

        connection = await asyncpg.connect(db_url)

        # Enable pgvector extension
        await connection.execute("CREATE EXTENSION IF NOT EXISTS vector")

        store = cls(connection)
        return store

    async def get_or_create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> PgvectorCollection:
        """Get or create a collection."""
        if name in self._collections:
            return self._collections[name]

        collection = PgvectorCollection(name, self.connection)
        await collection._init_table()
        self._collections[name] = collection
        return collection

    async def close(self) -> None:
        """Close the connection."""
        await self.connection.close()
