"""
Test health check endpoints.
Written in TDD Red phase - these will fail initially.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from app.main import app

    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """Health endpoint returns 200 OK status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_response_has_status_ok(client):
    """Health response contains status: ok."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_response_has_version(client):
    """Health response contains version field."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_legacy_health_endpoint_still_works(client):
    """Legacy GET /health still works for backward compatibility."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
