"""Tests for /api/orchestrator — full agent pipeline endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.state import OrchestratorState, build_initial_state
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _completed_state(job_id="job_1", candidate_id="c1") -> OrchestratorState:
    """Return a fully completed OrchestratorState for mocking."""
    state = build_initial_state(job_id=job_id, candidates=[candidate_id])
    state["resume_analyzer"]["status"] = "completed"
    state["resume_analyzer"]["analyzed_candidates"] = [
        '{"name": "Jane Doe", "email": "jane@example.com", "skills": ["Python"]}'
    ]
    state["decision_maker"]["status"] = "completed"
    state["decision_maker"]["decisions"] = ["CANDIDATE_ID: c1 | DECISION: PROCEED | REASON: Strong fit"]
    state["insight_agent"]["status"] = "completed"
    state["insight_agent"]["insights"] = ["- Strong Python background across candidates"]
    return state


def _mock_orchestrator(return_value=None, side_effect=None):
    """Create a mock orchestrator with a mocked run method."""
    mock = MagicMock()
    mock.run = AsyncMock(return_value=return_value, side_effect=side_effect)
    return mock


# ── Success ──────────────────────────────────────────────────────────────────


def test_orchestrator_returns_200_on_success():
    state = _completed_state()
    with patch(
        "app.api.routes.orchestrator._get_orchestrator",
        return_value=_mock_orchestrator(return_value=state),
    ):
        response = client.post("/api/orchestrator", json={
            "candidate_id": "c1",
            "job_id": "job_1",
        })
    assert response.status_code == 200


def test_orchestrator_returns_all_agent_results():
    state = _completed_state()
    with patch(
        "app.api.routes.orchestrator._get_orchestrator",
        return_value=_mock_orchestrator(return_value=state),
    ):
        response = client.post("/api/orchestrator", json={
            "candidate_id": "c1",
            "job_id": "job_1",
        })
    data = response.json()
    assert data["job_id"] == "job_1"
    assert data["candidates"] == ["c1"]
    assert data["resume_analyzer"]["status"] == "completed"
    assert len(data["resume_analyzer"]["analyzed_candidates"]) == 1
    assert data["decision_maker"]["status"] == "completed"
    assert len(data["decision_maker"]["decisions"]) == 1
    assert data["insight_agent"]["status"] == "completed"
    assert len(data["insight_agent"]["insights"]) == 1


# ── Pipeline failure ─────────────────────────────────────────────────────────


def test_orchestrator_returns_500_when_pipeline_fails():
    with patch(
        "app.api.routes.orchestrator._get_orchestrator",
        return_value=_mock_orchestrator(
            side_effect=RuntimeError("ResumeAnalyzer failed or produced no results — aborting pipeline."),
        ),
    ):
        response = client.post("/api/orchestrator", json={
            "candidate_id": "c1",
            "job_id": "job_1",
        })
    assert response.status_code == 500
    assert "ResumeAnalyzer failed" in response.json()["detail"]


def test_orchestrator_returns_500_when_decision_maker_fails():
    with patch(
        "app.api.routes.orchestrator._get_orchestrator",
        return_value=_mock_orchestrator(
            side_effect=RuntimeError("DecisionMaker failed or produced no decisions — aborting pipeline."),
        ),
    ):
        response = client.post("/api/orchestrator", json={
            "candidate_id": "c1",
            "job_id": "job_1",
        })
    assert response.status_code == 500
    assert "DecisionMaker failed" in response.json()["detail"]


# ── Validation ───────────────────────────────────────────────────────────────


def test_orchestrator_missing_candidate_id_returns_422():
    response = client.post("/api/orchestrator", json={
        "job_id": "job_1",
    })
    assert response.status_code == 422


def test_orchestrator_missing_job_id_returns_422():
    response = client.post("/api/orchestrator", json={
        "candidate_id": "c1",
    })
    assert response.status_code == 422


def test_orchestrator_empty_body_returns_422():
    response = client.post("/api/orchestrator", json={})
    assert response.status_code == 422


def test_orchestrator_empty_candidate_id_returns_422():
    response = client.post("/api/orchestrator", json={
        "candidate_id": "",
        "job_id": "job_1",
    })
    assert response.status_code == 422


def test_orchestrator_empty_job_id_returns_422():
    response = client.post("/api/orchestrator", json={
        "candidate_id": "c1",
        "job_id": "",
    })
    assert response.status_code == 422
