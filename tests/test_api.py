"""Skeleton API tests: GET /health contract (no server needed)."""

from fastapi.testclient import TestClient

from tolstoy.api.app import app

client = TestClient(app)


def test_health_returns_skeleton_contract() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "skeleton"
    assert body["collection"] == "tolstoy-ru"
