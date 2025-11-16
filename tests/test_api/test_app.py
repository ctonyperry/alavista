"""Tests for FastAPI app creation and basic endpoints."""

from fastapi.testclient import TestClient

from interfaces.api.app import create_app


def test_create_app():
    """Test app creation."""
    app = create_app()
    assert app is not None
    assert app.title == "Alavista API"


def test_health_check():
    """Test health check endpoint."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
