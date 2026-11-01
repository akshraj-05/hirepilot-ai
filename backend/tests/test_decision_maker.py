"""
Tests for the Decision Maker agent and Chroma integration.

Architecture coverage:
  • Batch assessment embeddings → assessments collection
  • JD-grounded semantic retrieval → decisions collection + APPLICATIONS fallback
  • Structured decisions persisted for InsightAgent

Unit tests mock the LLM. Integration tests require Chroma on localhost:8001 or are skipped.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.decision_maker import (
    _build_decision_rag_from_chroma,
    _build_decision_rag_from_storage,
    _parse_decision_json,
    _peer_row_from_chroma_decision_metadata,
    _resolve_decision_rag,
    decisions_list_from_parsed,
    run_decision_maker_agent,
)
from app.agents.state import build_initial_state
from app.agents.sub_agents.decision_maker import DecisionMaker
from app.chroma.collections import (
    ASSESSMENTS_COLLECTION,
    DECISIONS_COLLECTION,
    get_assessments_collection,
    get_decisions_collection,
)
from app.storage import APPLICATIONS, JOBS


def _chromadb_live() -> bool:
    try:
        client = chromadb.HttpClient(host="localhost", port=8001)
        return client.heartbeat() > 0
    except Exception:
        return False


CHROMADB_LIVE = _chromadb_live()


@pytest.fixture
def isolated_applications():
    snapshot = dict(APPLICATIONS)
    APPLICATIONS.clear()
    yield APPLICATIONS
    APPLICATIONS.clear()
    APPLICATIONS.update(snapshot)


@pytest.fixture
def isolated_jobs():
    snapshot = dict(JOBS)
    yield JOBS
    JOBS.clear()
    JOBS.update(snapshot)


def _fake_decision_json(candidate_id: str = "cand-a") -> str:
    return json.dumps(
        {
            "candidate_id": candidate_id,
            "match_score": 82,
            "skills_overlap_with_jd": ["Python", "FastAPI"],
            "skills_missing_from_resume": ["Kubernetes"],
            "status": "shortlist",
            "decision_reasons": ["Strong backend fit", "Gap: orchestration"],
            "override_status": None,
        }
    )


def test_parse_decision_json_strips_markdown_fence():
    raw = 'Here:\n```json\n{"candidate_id":"x","match_score":70}\n```'
    assert _parse_decision_json(raw) == {"candidate_id": "x", "match_score": 70}


def test_parse_decision_json_array():
    raw = '[{"candidate_id":"a","match_score":80},{"candidate_id":"b","match_score":40}]'
    parsed = _parse_decision_json(raw)
    assert len(parsed) == 2
    assert parsed[0]["candidate_id"] == "a"


def test_parse_decision_json_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        _parse_decision_json("")


def test_decisions_list_from_parsed_object_and_list():
    one = {"candidate_id": "1", "match_score": 50}
    assert len(decisions_list_from_parsed(one)) == 1
    assert "candidate_id" in decisions_list_from_parsed(one)[0]

    two = [{"candidate_id": "1"}, {"candidate_id": "2"}]
    lines = decisions_list_from_parsed(two)
    assert len(lines) == 2


def test_peer_row_from_chroma_decision_metadata_splits_pipe_fields():
    m = {
        "candidate_id": "c1",
        "match_score": 77.0,
        "status": "review",
        "skills_overlap": "Python | FastAPI",
        "skills_missing": "Go | Rust",
    }
    row = _peer_row_from_chroma_decision_metadata(m)
    assert row["candidate_id"] == "c1"
    assert row["match_score"] == 77.0
    assert row["matched_skills"] == ["Python", "FastAPI"]
    assert row["missing_skills"] == ["Go", "Rust"]


def test_decision_document_text_for_chroma_formats_row():
    row = {
        "status": "shortlist",
        "match_score": 88,
        "decision_reasons": ["A", "B"],
        "skills_overlap_with_jd": ["X"],
        "skills_missing_from_resume": ["Y"],
    }
    text = DecisionMaker._decision_document_text_for_chroma(row)
    assert "shortlist" in text and "88" in text
    assert "X" in text and "Y" in text


def test_build_decision_rag_from_storage_respects_exclude(isolated_applications):
    key = ("org-x", "job-x", "peer-1")
    APPLICATIONS[key] = {
        "match_score": 70,
        "status": "review",
        "matched_skills": ["Python"],
        "missing_skills": ["K8s"],
    }
    empty = _build_decision_rag_from_storage(
        "org-x", "job-x", exclude_candidate_ids=frozenset({"peer-1"})
    )
    assert empty["similar_decisions_same_jd"] == []

    full = _build_decision_rag_from_storage("org-x", "job-x", exclude_candidate_ids=None)
    assert len(full["similar_decisions_same_jd"]) == 1
    assert full["similar_decisions_same_jd"][0]["candidate_id"] == "peer-1"


def test_resolve_decision_rag_falls_back_when_chroma_empty(isolated_applications):
    APPLICATIONS[("org-f", "job-f", "hist-1")] = {
        "match_score": 60,
        "status": "review",
        "matched_skills": ["SQL"],
        "missing_skills": ["Go"],
    }
    with patch("app.agents.decision_maker._build_decision_rag_from_chroma", return_value=None):
        rag = _resolve_decision_rag(
            "org-f",
            "job-f",
            job_description="We need a backend engineer with SQL.",
            exclude_candidate_ids=frozenset({"current"}),
        )
    assert len(rag["similar_decisions_same_jd"]) == 1
    assert rag["similar_decisions_same_jd"][0]["candidate_id"] == "hist-1"


def test_resolve_decision_rag_prefers_chroma_when_non_empty(isolated_applications):
    APPLICATIONS[("org-f", "job-f", "hist-1")] = {
        "match_score": 1,
        "status": "reject",
        "matched_skills": [],
        "missing_skills": [],
    }
    chroma_payload = {
        "similar_decisions_same_jd": [
            {
                "candidate_id": "from-chroma",
                "match_score": 90.0,
                "status": "shortlist",
                "matched_skills": ["Rust"],
                "missing_skills": [],
            }
        ]
    }
    with patch(
        "app.agents.decision_maker._build_decision_rag_from_chroma",
        return_value=chroma_payload,
    ):
        rag = _resolve_decision_rag("org-f", "job-f", "any jd", exclude_candidate_ids=None)
    assert rag["similar_decisions_same_jd"][0]["candidate_id"] == "from-chroma"


def test_run_decision_maker_agent_parses_single_object():
    async def _run():
        mock_llm = MagicMock(spec=ChatOpenAI)
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=_fake_decision_json()))

        with patch("app.agents.decision_maker.get_chat_model", return_value=mock_llm):
            return await run_decision_maker_agent(
                job_description="Senior Python engineer",
                candidate_resume_assessment_json='{"resume_analysis":{"skills":["Python"]}}',
                organization_id="org1",
                job_id="job1",
                rag_results={"similar_decisions_same_jd": []},
            )

    parsed = asyncio.run(_run())
    assert parsed["candidate_id"] == "cand-a"
    assert parsed["match_score"] == 82
    assert "Python" in parsed["skills_overlap_with_jd"]


def test_run_decision_maker_agent_passes_resolved_rag_to_llm():
    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=_fake_decision_json()))

    rag = {"similar_decisions_same_jd": [{"candidate_id": "p1", "match_score": 50}]}

    async def _run():
        with patch("app.agents.decision_maker.get_chat_model", return_value=mock_llm):
            await run_decision_maker_agent(
                job_description="JD text",
                candidate_resume_assessment_json="{}",
                organization_id="o",
                job_id="j",
                rag_results=rag,
            )

    asyncio.run(_run())
    assert mock_llm.ainvoke.called


def test_decision_maker_run_end_to_end_mocked_llm(isolated_jobs):
    jid = f"job-dm-{uuid.uuid4().hex[:8]}"
    org = "org-dm-test"
    isolated_jobs[jid] = {
        "description": "Looking for Python and FastAPI experience.",
        "organization_id": org,
        "title": "Backend Engineer",
    }

    parsed = json.loads(_fake_decision_json("cand-99"))
    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=json.dumps(parsed)))

    agent = DecisionMaker()
    state = build_initial_state(
        job_id=jid,
        candidates=["cand-99"],
        organization_id=org,
        organization_name="TestCo",
    )
    state["resume_analyzer"]["analyzed_candidates"] = [
        "Skills: Python, FastAPI. Experience: 5 years backend."
    ]

    async def _run():
        with patch("app.agents.decision_maker.get_chat_model", return_value=mock_llm):
            await agent.run(state)

    asyncio.run(_run())

    assert state["decision_maker"]["status"] == "completed"
    assert len(state["decision_maker"]["decisions"]) == 1

    if CHROMADB_LIVE:
        client = chromadb.HttpClient(host="localhost", port=8001)
        ac = client.get_collection(ASSESSMENTS_COLLECTION)
        dc = client.get_collection(DECISIONS_COLLECTION)
        aid = f"cand-99__{jid}"
        assert ac.get(ids=[aid], include=["metadatas"])["metadatas"]
        assert dc.get(ids=[aid], include=["metadatas"])["metadatas"]
        ac.delete(ids=[aid])
        dc.delete(ids=[aid])


def test_decision_maker_run_raises_when_llm_invalid_json(isolated_jobs):
    jid = f"job-bad-{uuid.uuid4().hex[:8]}"
    isolated_jobs[jid] = {"description": "x", "organization_id": "o", "title": "T"}

    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="not json"))

    agent = DecisionMaker()
    state = build_initial_state(job_id=jid, candidates=["c1"], organization_id="o", organization_name="Co")
    state["resume_analyzer"]["analyzed_candidates"] = ["analysis"]

    async def _run():
        with patch("app.agents.decision_maker.get_chat_model", return_value=mock_llm):
            await agent.run(state)

    with pytest.raises(RuntimeError, match="DecisionMaker failed"):
        asyncio.run(_run())
    assert state["decision_maker"]["status"] == "failed"


@pytest.mark.skipif(
    not CHROMADB_LIVE,
    reason="ChromaDB not running on localhost:8001",
)
class TestDecisionMakerChromaIntegration:
    """Requires `docker compose up -d chromadb`."""

    def test_assessment_batch_upsert_and_metadata(self):
        uid = uuid.uuid4().hex[:8]
        job_id = f"job-chroma-{uid}"
        cid = f"cand-{uid}"
        org_id = f"org-{uid}"

        agent = DecisionMaker()
        agent._upsert_candidate_assessments_to_chroma(
            org_id,
            job_id,
            [cid],
            ["Assessment: Python expert with API design skills."],
        )

        col = get_assessments_collection()
        doc_id = f"{cid}__{job_id}"
        got = col.get(ids=[doc_id], include=["metadatas", "documents"])
        assert got["metadatas"][0]["candidate_id"] == cid
        assert got["metadatas"][0]["job_id"] == job_id
        assert "Python" in got["documents"][0]

        col.delete(ids=[doc_id])

    def test_decision_upsert_then_jd_query_returns_peer(self):
        uid = uuid.uuid4().hex[:8]
        job_id = f"job-chroma-{uid}"
        cid_peer = f"peer-{uid}"
        org_id = f"org-{uid}"

        jd = "We need a senior machine learning engineer with PyTorch and Python."

        col = get_decisions_collection()
        doc_id = f"{cid_peer}__{job_id}"
        col.upsert(
            ids=[doc_id],
            documents=[
                "status: shortlist | score: 92 | reasons: Strong PyTorch and Python. "
                "| matched: Python, PyTorch | missing: MLOps"
            ],
            metadatas=[
                {
                    "candidate_id": cid_peer,
                    "job_id": job_id,
                    "org_id": org_id,
                    "role_title": "ML Engineer",
                    "status": "shortlist",
                    "match_score": 92.0,
                    "decision_reasons": "Strong ML",
                    "skills_overlap": "Python | PyTorch",
                    "skills_missing": "MLOps",
                }
            ],
        )

        rag = _build_decision_rag_from_chroma(
            jd,
            org_id,
            job_id,
            exclude_candidate_ids=frozenset({f"batch-{uid}"}),
        )
        assert rag is not None
        peers = rag["similar_decisions_same_jd"]
        assert any(p["candidate_id"] == cid_peer for p in peers)

        col.delete(ids=[doc_id])

    def test_chroma_rag_excludes_current_batch_candidates(self):
        uid = uuid.uuid4().hex[:8]
        job_id = f"job-excl-{uid}"
        org_id = f"org-{uid}"
        current = f"current-{uid}"
        other = f"other-{uid}"

        col = get_decisions_collection()
        ids_list = [f"{current}__{job_id}", f"{other}__{job_id}"]
        col.upsert(
            ids=ids_list,
            documents=[
                "status: reject | score: 40 | reasons: weak | matched: X | missing: Y",
                "status: shortlist | score: 85 | reasons: strong Python | matched: Python | missing: Go",
            ],
            metadatas=[
                {
                    "candidate_id": current,
                    "job_id": job_id,
                    "org_id": org_id,
                    "role_title": "Dev",
                    "status": "reject",
                    "match_score": 40.0,
                    "decision_reasons": "",
                    "skills_overlap": "",
                    "skills_missing": "",
                },
                {
                    "candidate_id": other,
                    "job_id": job_id,
                    "org_id": org_id,
                    "role_title": "Dev",
                    "status": "shortlist",
                    "match_score": 85.0,
                    "decision_reasons": "",
                    "skills_overlap": "Python",
                    "skills_missing": "Go",
                },
            ],
        )

        rag = _build_decision_rag_from_chroma(
            "Python backend developer role",
            org_id,
            job_id,
            exclude_candidate_ids=frozenset({current}),
        )
        assert rag is not None
        cids = {p["candidate_id"] for p in rag["similar_decisions_same_jd"]}
        assert current not in cids
        assert other in cids

        col.delete(ids=ids_list)
