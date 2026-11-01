# ChromaDB Integration — HirePilot AI

ChromaDB is the vector store for the agent pipeline. Each sub-agent is
responsible for its own embedding logic — the utility layer only provides
the client, the embedding function, and the named collections.

---

## Quick start

```bash
docker compose up -d chromadb

# Verify
curl http://localhost:8001/api/v1/heartbeat
# {"nanosecond heartbeat": <number>}
```

ChromaDB listens on **host port 8001** (container port 8000).
FastAPI keeps port 8000 for itself.

---

## File layout

```
backend/app/chroma/
  client.py       — get_chroma_client()      singleton HttpClient
  embeddings.py   — get_embedding_fn()       singleton EmbeddingFunction
  collections.py  — get_candidates_collection() / get_decisions_collection()
```

There is no CRUD layer. Each sub-agent calls the collection directly and owns
its own read/write logic.

---

## Configuration

Two independent provider knobs — chat and embeddings can use different services.

```ini
# backend/.env

# Chat LLM
LLM_PROVIDER=cerebras
CEREBRAS_API_KEY=your-key

# Embeddings (independent of LLM_PROVIDER)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-key
```

### EMBEDDING_PROVIDER options

| Value | Model | API key |
|-------|-------|---------|
| `local` **(default)** | `all-MiniLM-L6-v2` bundled in chromadb | None |
| `openai` | `text-embedding-3-small` | `OPENAI_API_KEY` |
| `gemini` | `models/text-embedding-004` | `GEMINI_API_KEY` |

`local` works with zero config — good for development and mock mode.

### Optional model overrides

```ini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small   # only when EMBEDDING_PROVIDER=openai
GEMINI_EMBEDDING_MODEL=models/text-embedding-004 # only when EMBEDDING_PROVIDER=gemini

CHROMA_HOST=localhost   # default
CHROMA_PORT=8001        # default
```

---

## Collections

### `candidates`
One document per candidate. The text stored (and embedded) is the raw resume text.

```
id       → candidate_id
document → resume text  ← this is what gets embedded
metadata → candidate_id, org_id, job_id, candidate_name
```

### `decisions`
One document per `(candidate, job)` pair. The text stored (and embedded) should
capture the full decision — status, score, reasons, and skill gaps — so that
semantic search returns contextually relevant results, not just label matches.

```
id       → "{candidate_id}__{job_id}"
document → decision text built by the agent  ← this is what gets embedded
metadata → candidate_id, job_id, org_id, status, match_score, ...
```

The sub-agent decides what goes into `document`. A good format:

```
"status: shortlist | score: 82 | reasons: Strong Python. Lacks Kubernetes. | matched: Python, FastAPI | missing: Kubernetes, Go"
```

---

## How agents use the primitives

Import the collection, then call ChromaDB's standard API directly.

### Store an embedding (write)

```python
from app.chroma.collections import get_candidates_collection

collection = get_candidates_collection()
collection.upsert(
    ids=["<candidate_id>"],
    documents=["<resume text>"],          # ChromaDB embeds this automatically
    metadatas=[{"candidate_id": "...", "org_id": "...", "job_id": "..."}],
)
```

```python
from app.chroma.collections import get_decisions_collection

collection = get_decisions_collection()
collection.upsert(
    ids=["<candidate_id>__<job_id>"],
    documents=["status: shortlist | score: 82 | reasons: ..."],
    metadatas=[{"candidate_id": "...", "job_id": "...", "status": "shortlist", "match_score": 82.0}],
)
```

### Query by semantic similarity (read)

```python
collection = get_candidates_collection()
results = collection.query(
    query_texts=["<job description or search phrase>"],
    n_results=5,
    where={"org_id": "<org_id>"},         # optional metadata filter
    include=["metadatas", "distances"],
)
# results["metadatas"][0] → list of metadata dicts
# results["distances"][0] → list of cosine distances (lower = more similar)
```

### Fetch by ID (read)

```python
result = collection.get(ids=["<candidate_id>"], include=["metadatas"])
metadata = result["metadatas"][0]  # None-check if it might not exist
```

### Delete

```python
collection.delete(ids=["<candidate_id>"])
```

---

## Data persistence

ChromaDB data is volume-mounted at `./data/chroma` on the host.
It survives container restarts unless that directory is deleted.

Postgres remains the source of truth for structured data (status overrides,
feedback, meetings). ChromaDB holds only vector representations — if the volume
is wiped, sub-agents re-populate it on their next run.
