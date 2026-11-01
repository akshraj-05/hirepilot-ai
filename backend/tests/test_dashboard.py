"""Tests for /api/dashboard — BD-12 Dashboard Stats"""

import app.storage as storage
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def clear():
    storage.CANDIDATES.clear()
    storage.JOBS.clear()
    storage.APPLICATIONS.clear()
    storage.FEEDBACK.clear()


def add_application(org="org_1", job_id="job_1", candidate_id="c1", status="REVIEW"):
    key = storage.application_key(org, job_id, candidate_id)
    storage.APPLICATIONS[key] = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "organization_id": org,
        "match_score": 75,
        "status": status,
    }


# ── BD-12 Dashboard Stats ─────────────────────────────────────────────────────

def test_dashboard_returns_200():
    clear()
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.status_code == 200


def test_dashboard_returns_zeros_when_no_candidates():
    clear()
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    data = response.json()
    assert data["total"] == 0
    assert data["shortlisted"] == 0
    assert data["rejected"] == 0
    assert data["review"] == 0


def test_dashboard_counts_total_correctly():
    clear()
    add_application(candidate_id="c1", status="SHORTLIST")
    add_application(candidate_id="c2", status="REVIEW")
    add_application(candidate_id="c3", status="REJECT")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["total"] == 3


def test_dashboard_counts_shortlisted_correctly():
    clear()
    add_application(candidate_id="c1", status="SHORTLIST")
    add_application(candidate_id="c2", status="SHORTLIST")
    add_application(candidate_id="c3", status="REVIEW")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["shortlisted"] == 2


def test_dashboard_counts_rejected_correctly():
    clear()
    add_application(candidate_id="c1", status="REJECT")
    add_application(candidate_id="c2", status="REVIEW")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["rejected"] == 1


def test_dashboard_counts_review_correctly():
    clear()
    add_application(candidate_id="c1", status="REVIEW")
    add_application(candidate_id="c2", status="REVIEW")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["review"] == 2


def test_dashboard_filters_by_job():
    clear()
    add_application(org="org_1", job_id="job_1", candidate_id="c1", status="SHORTLIST")
    add_application(org="org_1", job_id="job_2", candidate_id="c2", status="SHORTLIST")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["total"] == 1


def test_dashboard_filters_by_org():
    clear()
    add_application(org="org_1", job_id="job_1", candidate_id="c1", status="SHORTLIST")
    add_application(org="org_2", job_id="job_1", candidate_id="c2", status="SHORTLIST")
    response = client.get("/api/dashboard?organization_id=org_1&job_id=job_1")
    assert response.json()["total"] == 1


def test_dashboard_missing_params_returns_422():
    clear()
    response = client.get("/api/dashboard")
    assert response.status_code == 422
