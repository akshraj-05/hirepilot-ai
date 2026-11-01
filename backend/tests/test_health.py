"""Tests for GET /api/v1/health"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_has_ok_true():
    response = client.get("/api/v1/health")
    assert response.json()["ok"] is True


def test_health_response_has_service_name():
    response = client.get("/api/v1/health")
    assert "service" in response.json()
