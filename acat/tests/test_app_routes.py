from __future__ import annotations

from fastapi.testclient import TestClient

from acat.api.app import app

client = TestClient(app)


def test_root_lists_human_score_url():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["human_score_url"] == "/api/v1/acat/human-score"


def test_human_score_route_is_registered():
    response = client.post("/api/v1/acat/human-score", json={})

    assert response.status_code == 422
