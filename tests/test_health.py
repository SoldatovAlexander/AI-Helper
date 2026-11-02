"""Offline smoke tests for the Docker-ready API bootstrap."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_is_available_without_deepseek_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-helper"}


def test_openapi_exposes_health_but_not_unimplemented_generate():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/generate" not in paths
