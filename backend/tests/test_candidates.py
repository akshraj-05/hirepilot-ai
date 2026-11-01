"""Tests for /api/candidates — BD-01 Upload, BD-02 Parse, BD-08 List, BD-09 Get, BD-10 Status, BD-13 Bulk"""

import io
from unittest.mock import patch

import app.storage as storage
from app.config import settings
from app.main import app
from app.schemas.resume_parse import ParsedResume
from fastapi.testclient import TestClient

client = TestClient(app)

# Minimal valid DOCX bytes (just enough for the file-type check to pass)
FAKE_DOCX = b"PK\x03\x04" + b"\x00" * 100   # PK header (zip magic) mimics a DOCX

# A resume text long enough to pass the 20-char minimum
LONG_RESUME_TEXT = "Senior Software Engineer with 7 years of experience in Python, FastAPI, Docker, PostgreSQL, AWS."


def clear():
    storage.CANDIDATES.clear()
    storage.JOBS.clear()
    storage.APPLICATIONS.clear()
    storage.FEEDBACK.clear()


def add_candidate(candidate_id="c1", name="Jane Doe"):
    """Directly insert a candidate into in-memory storage for tests that need one."""
    storage.CANDIDATES[candidate_id] = {
        "id": candidate_id,
        "candidate_id": candidate_id,
        "candidate_name": name,
        "resume_filename": "resume.docx",
        "resume_ext": "docx",
        "resume_content": FAKE_DOCX,
        "skills": ["Python", "FastAPI"],
    }


def add_application(org="org_1", job_id="job_1", candidate_id="c1", score=80, status="SHORTLIST"):
    key = storage.application_key(org, job_id, candidate_id)
    storage.APPLICATIONS[key] = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "organization_id": org,
        "match_score": score,
        "status": status,
    }


# ── BD-01 Upload Resume ───────────────────────────────────────────────────────

def test_upload_resume_returns_200():
    clear()
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200


def test_upload_resume_returns_candidate_id():
    clear()
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"candidate_name": "John Smith"},
    )
    assert "candidate_id" in response.json()
    assert response.json()["message"] == "Resume uploaded successfully"


def test_upload_resume_stores_candidate_name():
    clear()
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"candidate_name": "John Smith"},
    )
    candidate_id = response.json()["candidate_id"]
    assert storage.CANDIDATES[candidate_id]["candidate_name"] == "John Smith"


def test_upload_resume_rejects_txt_file():
    clear()
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.txt", io.BytesIO(b"some text"), "text/plain")},
    )
    assert response.status_code == 400


def test_upload_resume_accepts_pdf():
    clear()
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("resume.pdf", io.BytesIO(FAKE_DOCX), "application/pdf")},
    )
    assert response.status_code == 200


# ── BD-13 Bulk Upload ─────────────────────────────────────────────────────────

def test_bulk_upload_returns_200():
    clear()
    response = client.post(
        "/api/candidates/bulk-upload",
        files=[
            ("files", ("r1.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("r2.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ],
    )
    assert response.status_code == 200


def test_bulk_upload_returns_count():
    clear()
    response = client.post(
        "/api/candidates/bulk-upload",
        files=[
            ("files", ("r1.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("r2.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ],
    )
    assert response.json()["count"] == 2


def test_bulk_upload_skips_invalid_file_types():
    clear()
    response = client.post(
        "/api/candidates/bulk-upload",
        files=[
            ("files", ("r1.docx", io.BytesIO(FAKE_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("r2.txt", io.BytesIO(b"plain text"), "text/plain")),
        ],
    )
    # Only the docx should be counted; txt is skipped
    assert response.json()["count"] == 1


# ── BD-02 Parse Resume ────────────────────────────────────────────────────────

def test_parse_resume_returns_200_with_mock_when_no_api_key():
    # Without an API key the service returns mock parsed data (not 503).
    clear()
    add_candidate()
    settings.openai_api_key = None
    with patch("app.api.routes.candidates.extract_resume_text", return_value=LONG_RESUME_TEXT):
        response = client.post("/api/candidates/c1/parse")
    assert response.status_code == 200
    assert "skills" in response.json()


def test_parse_resume_returns_200_with_mock():
    clear()
    add_candidate()
    fake_result = ParsedResume(
        skills=["Python", "FastAPI"],
        experience="5 years backend development",
        education="B.Tech Computer Science",
    )
    settings.openai_api_key = "fake-key"
    with patch("app.api.routes.candidates.extract_resume_text", return_value=LONG_RESUME_TEXT):
        with patch("app.api.routes.candidates.parse_resume_structured", return_value=fake_result):
            response = client.post("/api/candidates/c1/parse")
    settings.openai_api_key = None
    assert response.status_code == 200


def test_parse_resume_returns_skills():
    clear()
    add_candidate()
    fake_result = ParsedResume(
        skills=["Python", "FastAPI", "Docker"],
        experience="5 years backend development",
        education="B.Tech Computer Science",
    )
    settings.openai_api_key = "fake-key"
    with patch("app.api.routes.candidates.extract_resume_text", return_value=LONG_RESUME_TEXT):
        with patch("app.api.routes.candidates.parse_resume_structured", return_value=fake_result):
            response = client.post("/api/candidates/c1/parse")
    settings.openai_api_key = None
    data = response.json()
    assert "Python" in data["skills"]
    assert "experience" in data
    assert "education" in data


def test_parse_resume_nonexistent_candidate_returns_404():
    clear()
    settings.openai_api_key = "fake-key"
    response = client.post("/api/candidates/nonexistent/parse")
    settings.openai_api_key = None
    assert response.status_code == 404


# ── BD-08 List Candidates ─────────────────────────────────────────────────────

def test_list_candidates_returns_200():
    clear()
    add_candidate()
    add_application()
    response = client.get("/api/candidates?organization_id=org_1&job_id=job_1")
    assert response.status_code == 200


def test_list_candidates_returns_correct_candidate():
    clear()
    add_candidate(candidate_id="c1", name="Alice")
    add_application(candidate_id="c1", score=85, status="SHORTLIST")
    response = client.get("/api/candidates?organization_id=org_1&job_id=job_1")
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice"
    assert data[0]["score"] == 85
    assert data[0]["status"] == "SHORTLIST"


def test_list_candidates_missing_params_returns_422():
    clear()
    response = client.get("/api/candidates")
    assert response.status_code == 422


def test_list_candidates_empty_when_no_applications():
    clear()
    add_candidate()
    response = client.get("/api/candidates?organization_id=org_1&job_id=job_1")
    assert response.json() == []


# ── BD-09 Get Candidate ───────────────────────────────────────────────────────

def test_get_candidate_returns_200():
    clear()
    add_candidate()
    response = client.get("/api/candidates/c1")
    assert response.status_code == 200


def test_get_candidate_returns_correct_name():
    clear()
    add_candidate(candidate_id="c1", name="Jane Doe")
    response = client.get("/api/candidates/c1")
    assert response.json()["name"] == "Jane Doe"


def test_get_candidate_returns_score_and_status_when_application_exists():
    clear()
    add_candidate()
    add_application(score=90, status="SHORTLIST")
    response = client.get("/api/candidates/c1?organization_id=org_1&job_id=job_1")
    data = response.json()
    assert data["score"] == 90
    assert data["status"] == "SHORTLIST"


def test_get_candidate_nonexistent_returns_404():
    clear()
    response = client.get("/api/candidates/nonexistent")
    assert response.status_code == 404


# ── BD-10 Update Candidate Status ─────────────────────────────────────────────

def test_update_status_returns_200():
    clear()
    add_candidate()
    add_application()
    response = client.patch(
        "/api/candidates/c1/status?organization_id=org_1&job_id=job_1",
        json={"status": "REJECT"},
    )
    assert response.status_code == 200


def test_update_status_changes_status():
    clear()
    add_candidate()
    add_application(status="REVIEW")
    client.patch(
        "/api/candidates/c1/status?organization_id=org_1&job_id=job_1",
        json={"status": "SHORTLIST"},
    )
    key = storage.application_key("org_1", "job_1", "c1")
    assert storage.APPLICATIONS[key]["status"] == "SHORTLIST"


def test_update_status_nonexistent_candidate_returns_404():
    clear()
    response = client.patch(
        "/api/candidates/nonexistent/status?organization_id=org_1&job_id=job_1",
        json={"status": "REJECT"},
    )
    assert response.status_code == 404
