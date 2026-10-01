from __future__ import annotations

from fastapi.testclient import TestClient

from acat.api.app import app

client = TestClient(app)


def test_root_lists_human_score_url():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["human_score_url"] == "/api/v1/acat/human-score"


def test_human_score_route_is_registered(monkeypatch):
    monkeypatch.setenv("ACAT_WRITE_TOKEN", "test-token")
    response = client.post(
        "/api/v1/acat/human-score",
        json={},
        headers={"X-ACAT-Write-Token": "test-token"},
    )

    assert response.status_code == 422
