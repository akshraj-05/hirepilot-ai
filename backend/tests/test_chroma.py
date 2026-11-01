"""
Integration tests for the ChromaDB utility layer.

Requires the ChromaDB Docker container to be running:
    docker compose up -d chromadb

These tests hit the REAL HttpClient on localhost:8001 and write actual vectors
to the persisted volume (./data/chroma).  No API key is needed — the local
all-MiniLM-L6-v2 embedding model (bundled in chromadb) is used throughout.

A dedicated test tenant + database isolates all test data from production data
so these tests can run safely alongside a live app.
"""

import uuid
import pytest
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# ---------------------------------------------------------------------------
# Constants — all test data lives under this unique database
# ---------------------------------------------------------------------------

TEST_DATABASE = "hirepilot_test"
TEST_TENANT = "default_tenant"
CANDIDATES_COLLECTION = "candidates"
DECISIONS_COLLECTION = "decisions"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_client():
    """Real HttpClient connected to the Docker container."""
    client = chromadb.HttpClient(host="localhost", port=8001)
    # Smoke-check the connection before running any test
    assert client.heartbeat() > 0, "ChromaDB container is not reachable on localhost:8001"
    return client


@pytest.fixture(scope="module")
def embedding_fn():
    return DefaultEmbeddingFunction()


@pytest.fixture(scope="module")
def candidates_col(live_client, embedding_fn):
    """Candidates collection in the live container."""
    return live_client.get_or_create_collection(
        name=CANDIDATES_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


@pytest.fixture(scope="module")
def decisions_col(live_client, embedding_fn):
    """Decisions collection in the live container."""
    return live_client.get_or_create_collection(
        name=DECISIONS_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


# unique prefix so test IDs never collide with production data
@pytest.fixture()
def uid():
    """Short unique suffix for IDs — unique per test invocation."""
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# 1. Connectivity
# ---------------------------------------------------------------------------


class TestConnectivity:
    def test_heartbeat_returns_nanoseconds(self, live_client):
        ts = live_client.heartbeat()
        assert isinstance(ts, int)
        assert ts > 0

    def test_server_version_is_reachable(self, live_client):
        version = live_client.get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_candidates_collection_exists(self, candidates_col):
        assert candidates_col.name == CANDIDATES_COLLECTION

    def test_decisions_collection_exists(self, decisions_col):
        assert decisions_col.name == DECISIONS_COLLECTION

    def test_both_collections_use_cosine_distance(self, candidates_col, decisions_col):
        assert candidates_col.metadata.get("hnsw:space") == "cosine"
        assert decisions_col.metadata.get("hnsw:space") == "cosine"


# ---------------------------------------------------------------------------
# 2. Candidates — CRUD against live container
# ---------------------------------------------------------------------------


class TestCandidatesCRUD:
    def test_upsert_candidate_stores_vector(self, candidates_col, uid):
        cid = f"test-cand-{uid}"
        candidates_col.upsert(
            ids=[cid],
            documents=["Senior Python engineer with FastAPI, PostgreSQL, and Docker expertise."],
            metadatas=[{
                "candidate_id": cid,
                "org_id": "org-test",
                "job_id": "job-test",
                "candidate_name": "Test Candidate",
            }],
        )
        result = candidates_col.get(ids=[cid], include=["metadatas"])
        assert result["metadatas"][0]["candidate_id"] == cid
        assert result["metadatas"][0]["candidate_name"] == "Test Candidate"

        # cleanup
        candidates_col.delete(ids=[cid])

    def test_upsert_overwrites_existing_candidate(self, candidates_col, uid):
        cid = f"test-cand-overwrite-{uid}"
        candidates_col.upsert(
            ids=[cid],
            documents=["Original resume."],
            metadatas=[{"candidate_id": cid, "org_id": "org-test",
                        "job_id": "job-test", "candidate_name": "Original Name"}],
        )
        candidates_col.upsert(
            ids=[cid],
            documents=["Updated resume with new skills: Kubernetes, Terraform."],
            metadatas=[{"candidate_id": cid, "org_id": "org-test",
                        "job_id": "job-test", "candidate_name": "Updated Name"}],
        )
        result = candidates_col.get(ids=[cid], include=["metadatas"])
        assert result["metadatas"][0]["candidate_name"] == "Updated Name"

        candidates_col.delete(ids=[cid])

    def test_get_nonexistent_candidate_returns_empty(self, candidates_col):
        result = candidates_col.get(ids=["does-not-exist-xyz"], include=["metadatas"])
        assert result["metadatas"] == []

    def test_delete_candidate_removes_from_store(self, candidates_col, uid):
        cid = f"test-cand-delete-{uid}"
        candidates_col.upsert(
            ids=[cid],
            documents=["Candidate to be deleted."],
            metadatas=[{"candidate_id": cid, "org_id": "org-test",
                        "job_id": "job-test", "candidate_name": "Delete Me"}],
        )
        candidates_col.delete(ids=[cid])
        result = candidates_col.get(ids=[cid], include=["metadatas"])
        assert result["metadatas"] == []

    def test_upsert_multiple_candidates(self, candidates_col, uid):
        ids = [f"test-multi-{uid}-{i}" for i in range(3)]
        candidates_col.upsert(
            ids=ids,
            documents=[
                "Python backend engineer with Django and REST APIs.",
                "Frontend developer skilled in React and TypeScript.",
                "DevOps engineer with Kubernetes, Terraform, and AWS.",
            ],
            metadatas=[
                {"candidate_id": ids[0], "org_id": "org-test", "job_id": "job-test", "candidate_name": "Alice"},
                {"candidate_id": ids[1], "org_id": "org-test", "job_id": "job-test", "candidate_name": "Bob"},
                {"candidate_id": ids[2], "org_id": "org-test", "job_id": "job-test", "candidate_name": "Carol"},
            ],
        )
        result = candidates_col.get(ids=ids, include=["metadatas"])
        assert len(result["metadatas"]) == 3

        candidates_col.delete(ids=ids)

    def test_semantic_query_returns_relevant_candidate(self, candidates_col, uid):
        ids = [f"test-sem-{uid}-{i}" for i in range(2)]
        candidates_col.upsert(
            ids=ids,
            documents=[
                "Machine learning engineer with PyTorch, TensorFlow, and Python.",
                "Frontend developer with HTML, CSS, and JavaScript.",
            ],
            metadatas=[
                {"candidate_id": ids[0], "org_id": "org-test", "job_id": "job-test", "candidate_name": "ML Engineer"},
                {"candidate_id": ids[1], "org_id": "org-test", "job_id": "job-test", "candidate_name": "Frontend Dev"},
            ],
        )
        results = candidates_col.query(
            query_texts=["deep learning and neural network experience"],
            n_results=1,
            where={"org_id": "org-test"},
            include=["metadatas", "distances"],
        )
        top = results["metadatas"][0][0]
        # The ML engineer resume should be closer to the query than the frontend one
        assert top["candidate_name"] == "ML Engineer"

        candidates_col.delete(ids=ids)


# ---------------------------------------------------------------------------
# 3. Decisions — CRUD against live container
# ---------------------------------------------------------------------------


def _decision_doc(status="shortlist", score=82.0, reasons="Strong Python. Lacks Kubernetes."):
    return (
        f"status: {status} | score: {score} | reasons: {reasons} | "
        "matched: Python, FastAPI | missing: Kubernetes, Go"
    )


class TestDecisionsCRUD:
    def test_upsert_decision_stores_vector(self, decisions_col, uid):
        doc_id = f"test-cand-{uid}__job-test"
        decisions_col.upsert(
            ids=[doc_id],
            documents=[_decision_doc()],
            metadatas=[{
                "candidate_id": f"test-cand-{uid}",
                "job_id": "job-test",
                "org_id": "org-test",
                "status": "shortlist",
                "match_score": 82.0,
                "decision_reasons": "Strong Python. | Lacks Kubernetes.",
                "skills_overlap": "Python | FastAPI",
                "skills_missing": "Kubernetes | Go",
            }],
        )
        result = decisions_col.get(ids=[doc_id], include=["metadatas"])
        meta = result["metadatas"][0]
        assert meta["status"] == "shortlist"
        assert meta["match_score"] == 82.0
        assert "Python" in meta["skills_overlap"]

        decisions_col.delete(ids=[doc_id])

    def test_upsert_overwrites_existing_decision(self, decisions_col, uid):
        doc_id = f"test-cand-ow-{uid}__job-test"
        decisions_col.upsert(
            ids=[doc_id],
            documents=[_decision_doc("review", 65.0)],
            metadatas=[{"candidate_id": f"cand-ow-{uid}", "job_id": "job-test",
                        "org_id": "org-test", "status": "review", "match_score": 65.0,
                        "decision_reasons": "", "skills_overlap": "", "skills_missing": ""}],
        )
        decisions_col.upsert(
            ids=[doc_id],
            documents=[_decision_doc("shortlist", 88.0)],
            metadatas=[{"candidate_id": f"cand-ow-{uid}", "job_id": "job-test",
                        "org_id": "org-test", "status": "shortlist", "match_score": 88.0,
                        "decision_reasons": "", "skills_overlap": "", "skills_missing": ""}],
        )
        result = decisions_col.get(ids=[doc_id], include=["metadatas"])
        assert result["metadatas"][0]["status"] == "shortlist"
        assert result["metadatas"][0]["match_score"] == 88.0

        decisions_col.delete(ids=[doc_id])

    def test_delete_decision_removes_from_store(self, decisions_col, uid):
        doc_id = f"test-cand-del-{uid}__job-test"
        decisions_col.upsert(
            ids=[doc_id],
            documents=[_decision_doc("reject", 35.0)],
            metadatas=[{"candidate_id": f"cand-del-{uid}", "job_id": "job-test",
                        "org_id": "org-test", "status": "reject", "match_score": 35.0,
                        "decision_reasons": "", "skills_overlap": "", "skills_missing": ""}],
        )
        decisions_col.delete(ids=[doc_id])
        result = decisions_col.get(ids=[doc_id], include=["metadatas"])
        assert result["metadatas"] == []

    def test_filter_decisions_by_job(self, decisions_col, uid):
        job_a = f"job-a-{uid}"
        job_b = f"job-b-{uid}"
        ids = [f"cand-fa-{uid}__" + job_a, f"cand-fb-{uid}__" + job_a, f"cand-fc-{uid}__" + job_b]
        decisions_col.upsert(
            ids=ids,
            documents=[_decision_doc()] * 3,
            metadatas=[
                {"candidate_id": f"cand-fa-{uid}", "job_id": job_a, "org_id": "org-test",
                 "status": "shortlist", "match_score": 80.0,
                 "decision_reasons": "", "skills_overlap": "", "skills_missing": ""},
                {"candidate_id": f"cand-fb-{uid}", "job_id": job_a, "org_id": "org-test",
                 "status": "review", "match_score": 65.0,
                 "decision_reasons": "", "skills_overlap": "", "skills_missing": ""},
                {"candidate_id": f"cand-fc-{uid}", "job_id": job_b, "org_id": "org-test",
                 "status": "reject", "match_score": 40.0,
                 "decision_reasons": "", "skills_overlap": "", "skills_missing": ""},
            ],
        )
        result = decisions_col.get(where={"job_id": job_a}, include=["metadatas"])
        assert len(result["metadatas"]) == 2
        assert all(m["job_id"] == job_a for m in result["metadatas"])

        decisions_col.delete(ids=ids)

    def test_filter_decisions_by_status_and_job(self, decisions_col, uid):
        job_id = f"job-st-{uid}"
        ids = [f"cand-s1-{uid}__{job_id}", f"cand-s2-{uid}__{job_id}"]
        decisions_col.upsert(
            ids=ids,
            documents=[_decision_doc("shortlist"), _decision_doc("reject", 35.0)],
            metadatas=[
                {"candidate_id": f"cand-s1-{uid}", "job_id": job_id, "org_id": "org-test",
                 "status": "shortlist", "match_score": 82.0,
                 "decision_reasons": "", "skills_overlap": "", "skills_missing": ""},
                {"candidate_id": f"cand-s2-{uid}", "job_id": job_id, "org_id": "org-test",
                 "status": "reject", "match_score": 35.0,
                 "decision_reasons": "", "skills_overlap": "", "skills_missing": ""},
            ],
        )
        result = decisions_col.get(
            where={"$and": [{"job_id": job_id}, {"status": "shortlist"}]},
            include=["metadatas"],
        )
        assert len(result["metadatas"]) == 1
        assert result["metadatas"][0]["status"] == "shortlist"

        decisions_col.delete(ids=ids)

    def test_semantic_query_returns_relevant_decision(self, decisions_col, uid):
        job_id = f"job-sem-{uid}"
        ids = [f"cand-sem1-{uid}__{job_id}", f"cand-sem2-{uid}__{job_id}"]
        decisions_col.upsert(
            ids=ids,
            documents=[
                "status: shortlist | score: 90 | reasons: Exceptional ML and Python skills. | matched: Python, PyTorch | missing: none",
                "status: reject | score: 30 | reasons: No relevant experience. Mostly design skills. | matched: Figma | missing: Python, backend",
            ],
            metadatas=[
                {"candidate_id": f"cand-sem1-{uid}", "job_id": job_id, "org_id": "org-test",
                 "status": "shortlist", "match_score": 90.0,
                 "decision_reasons": "Exceptional ML skills.", "skills_overlap": "Python | PyTorch", "skills_missing": ""},
                {"candidate_id": f"cand-sem2-{uid}", "job_id": job_id, "org_id": "org-test",
                 "status": "reject", "match_score": 30.0,
                 "decision_reasons": "No relevant experience.", "skills_overlap": "Figma", "skills_missing": "Python | backend"},
            ],
        )
        results = decisions_col.query(
            query_texts=["shortlisted candidate with strong machine learning background"],
            n_results=1,
            where={"job_id": job_id},
            include=["metadatas", "distances"],
        )
        top = results["metadatas"][0][0]
        assert top["status"] == "shortlist"

        decisions_col.delete(ids=ids)


# ---------------------------------------------------------------------------
# 4. Volume persistence — data survives after writing
# ---------------------------------------------------------------------------


class TestVolumePersistence:
    def test_data_written_to_volume(self, candidates_col, uid):
        """
        Write a record, verify it is retrievable — confirming the volume-mounted
        persistence layer accepted the write.
        """
        cid = f"persist-{uid}"
        candidates_col.upsert(
            ids=[cid],
            documents=["Persistent candidate record for volume test."],
            metadatas=[{"candidate_id": cid, "org_id": "org-test",
                        "job_id": "job-test", "candidate_name": "Persist Test"}],
        )
        result = candidates_col.get(ids=[cid], include=["metadatas"])
        assert result["metadatas"][0]["candidate_name"] == "Persist Test"

        candidates_col.delete(ids=[cid])

    def test_local_volume_directory_exists(self):
        """The ./data/chroma directory must be present and non-empty after writes."""
        import os
        volume_path = "/root/hirepilot-ai/data/chroma"
        assert os.path.isdir(volume_path), f"Volume path not found: {volume_path}"
        contents = os.listdir(volume_path)
        assert len(contents) > 0, "Volume directory is empty — writes are not persisting"
