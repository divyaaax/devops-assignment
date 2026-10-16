"""
Unit tests for application health check endpoints.
Verifies GET /health, GET /health/, and POST /health/ contracts.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_get():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "backend"


def test_health_get_trailing_slash():
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_post_compatibility():
    response = client.post("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
