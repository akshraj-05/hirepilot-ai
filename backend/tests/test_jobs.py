"""Tests for /api/jobs — BD-03 Create Job, BD-04 List Jobs, BD-05 Get Job"""

import app.storage as storage
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def clear():
    storage.CANDIDATES.clear()
    storage.JOBS.clear()
    storage.APPLICATIONS.clear()
    storage.FEEDBACK.clear()


# ── BD-03 Create Job ──────────────────────────────────────────────────────────

def test_create_job_returns_200():
    clear()
    response = client.post("/api/jobs", json={
        "title": "Backend Engineer",
        "description": "Python developer needed.",
        "organization_id": "org_1",
    })
    assert response.status_code == 200


def test_create_job_returns_job_id():
    clear()
    response = client.post("/api/jobs", json={
        "title": "Backend Engineer",
        "description": "Python developer needed.",
        "organization_id": "org_1",
    })
    assert "job_id" in response.json()


def test_create_job_missing_title_returns_422():
    clear()
    response = client.post("/api/jobs", json={
        "description": "Python developer needed.",
        "organization_id": "org_1",
    })
    assert response.status_code == 422


def test_create_job_missing_description_returns_422():
    clear()
    response = client.post("/api/jobs", json={
        "title": "Backend Engineer",
        "organization_id": "org_1",
    })
    assert response.status_code == 422


# ── BD-04 List Jobs ───────────────────────────────────────────────────────────

def test_list_jobs_returns_200():
    clear()
    client.post("/api/jobs", json={
        "title": "Backend Engineer",
        "description": "Python developer needed.",
        "organization_id": "org_1",
    })
    response = client.get("/api/jobs?organization_id=org_1")
    assert response.status_code == 200


def test_list_jobs_returns_created_job():
    clear()
    client.post("/api/jobs", json={
        "title": "Frontend Engineer",
        "description": "React developer needed.",
        "organization_id": "org_1",
    })
    response = client.get("/api/jobs?organization_id=org_1")
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["job_description"] == "React developer needed."


def test_list_jobs_filters_by_org():
    clear()
    client.post("/api/jobs", json={
        "title": "Job A",
        "description": "For org_1",
        "organization_id": "org_1",
    })
    client.post("/api/jobs", json={
        "title": "Job B",
        "description": "For org_2",
        "organization_id": "org_2",
    })
    response = client.get("/api/jobs?organization_id=org_1")
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["job_description"] == "For org_1"


def test_list_jobs_missing_org_returns_422():
    clear()
    response = client.get("/api/jobs")
    assert response.status_code == 422


# ── BD-05 Get Job ─────────────────────────────────────────────────────────────

def test_get_job_returns_200():
    clear()
    created = client.post("/api/jobs", json={
        "title": "DevOps Engineer",
        "description": "Kubernetes expert.",
        "organization_id": "org_1",
    })
    job_id = created.json()["job_id"]
    response = client.get(f"/api/jobs/{job_id}?organization_id=org_1")
    assert response.status_code == 200


def test_get_job_returns_correct_data():
    clear()
    created = client.post("/api/jobs", json={
        "title": "DevOps Engineer",
        "description": "Kubernetes expert.",
        "organization_id": "org_1",
    })
    job_id = created.json()["job_id"]
    response = client.get(f"/api/jobs/{job_id}?organization_id=org_1")
    data = response.json()
    assert data["title"] == "DevOps Engineer"
    assert data["description"] == "Kubernetes expert."
    assert data["job_id"] == job_id


def test_get_job_wrong_org_returns_404():
    clear()
    created = client.post("/api/jobs", json={
        "title": "DevOps Engineer",
        "description": "Kubernetes expert.",
        "organization_id": "org_1",
    })
    job_id = created.json()["job_id"]
    response = client.get(f"/api/jobs/{job_id}?organization_id=org_other")
    assert response.status_code == 404


def test_get_job_nonexistent_returns_404():
    clear()
    response = client.get("/api/jobs/nonexistent-id?organization_id=org_1")
    assert response.status_code == 404
