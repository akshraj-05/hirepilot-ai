"""Tests for /api/feedback — BD-11 Submit Recruiter Feedback"""

import app.storage as storage
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def clear():
    storage.CANDIDATES.clear()
    storage.JOBS.clear()
    storage.APPLICATIONS.clear()
    storage.FEEDBACK.clear()


# ── BD-11 Submit Feedback ─────────────────────────────────────────────────────

def test_submit_feedback_returns_200():
    clear()
    response = client.post("/api/feedback", json={
        "candidate_id": "c1",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": True,
        "comments": "Great match.",
    })
    assert response.status_code == 200


def test_submit_feedback_returns_message():
    clear()
    response = client.post("/api/feedback", json={
        "candidate_id": "c1",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": True,
        "comments": "Great match.",
    })
    assert response.json()["message"] == "Feedback recorded"


def test_submit_feedback_stores_in_memory():
    clear()
    client.post("/api/feedback", json={
        "candidate_id": "c1",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": False,
        "comments": "Not a good fit.",
    })
    assert len(storage.FEEDBACK) == 1
    assert storage.FEEDBACK[0]["decision_correct"] is False
    assert storage.FEEDBACK[0]["comments"] == "Not a good fit."


def test_submit_multiple_feedbacks():
    clear()
    client.post("/api/feedback", json={
        "candidate_id": "c1",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": True,
        "comments": "First feedback.",
    })
    client.post("/api/feedback", json={
        "candidate_id": "c2",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": False,
        "comments": "Second feedback.",
    })
    assert len(storage.FEEDBACK) == 2


def test_submit_feedback_without_comments():
    clear()
    response = client.post("/api/feedback", json={
        "candidate_id": "c1",
        "job_id": "job_1",
        "organization_id": "org_1",
        "decision_correct": True,
    })
    assert response.status_code == 200


def test_submit_feedback_missing_required_fields_returns_422():
    clear()
    response = client.post("/api/feedback", json={
        "candidate_id": "c1",
    })
    assert response.status_code == 422
