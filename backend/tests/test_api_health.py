"""Tests for FastAPI backend application health endpoint."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app


def test_api_health():
    """Verifies that the /api/health endpoint returns 200 OK."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "SlothSort"
    assert "default_provider" in data


def test_api_providers_endpoint():
    """Verifies that the /api/providers endpoint returns list of provider health objects."""
    client = TestClient(app)
    response = client.get("/api/providers")

    assert response.status_code == 200
    providers = response.json()
    assert isinstance(providers, list)
    assert len(providers) >= 3

    provider_names = [p["provider_name"] for p in providers]
    assert any("Mock" in n for n in provider_names)
    assert any("Ollama" in n for n in provider_names)
    assert any("Gemini" in n for n in provider_names)


def test_cors_configuration():
    """Verifies that CORS origins default securely to local development URLs."""
    from backend.app.config import settings
    origins = settings.CORS_ORIGINS
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
