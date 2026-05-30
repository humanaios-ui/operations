from __future__ import annotations

from fastapi.testclient import TestClient

from acat.api.app import app

client = TestClient(app)


def test_assess_endpoint_happy_path(monkeypatch):
    def fake_run_assessment(payload: dict) -> dict:
        assert payload["agent_name"] == "Claude"
        assert payload["provider"] == "anthropic"
        assert payload["model"] == "claude-3-7-sonnet"
        assert "api_key" in payload

        return {
            "status": "completed",
            "assessment_id": "acat-test-001",
            "session_id": "S-test-001",
            "agent_name": "Claude",
            "provider": "anthropic",
            "model": "claude-3-7-sonnet",
            "mode": "two_stage",
            "submission_purity": "two_stage_verified",
            "phase1": {
                "persisted": True,
                "supabase_id": "row-001",
                "created_at": "2026-05-30T18:00:00+00:00",
                "p1_committed_at": "2026-05-30T18:00:00+00:00",
                "scores": {
                    "truth": 84,
                    "service": 88,
                    "harm": 82,
                    "autonomy": 80,
                    "value": 86,
                    "humility": 72,
                },
            },
            "phase3": {
                "persisted": True,
                "supabase_id": "row-001",
                "updated_at": "2026-05-30T18:01:10+00:00",
                "p3_committed_at": "2026-05-30T18:01:10+00:00",
                "scores": {
                    "truth": 72,
                    "service": 76,
                    "harm": 74,
                    "autonomy": 73,
                    "value": 75,
                    "humility": 70,
                },
            },
            "learning_index": 0.8943,
        }

    monkeypatch.setattr(
        "acat.api.routes.assess_router.run_assessment",
        fake_run_assessment,
    )

    response = client.post(
        "/api/v1/acat/assess",
        json={
            "agent_name": "Claude",
            "provider": "anthropic",
            "api_key": "sk-ant-test",
            "model": "claude-3-7-sonnet",
            "mode": "two_stage",
            "wait_seconds": 65,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert body["assessment_id"] == "acat-test-001"
    assert body["submission_purity"] == "two_stage_verified"
    assert body["learning_index"] == 0.8943
    assert body["phase1"]["persisted"] is True
    assert body["phase3"]["persisted"] is True
    assert "api_key" not in body


def test_assess_endpoint_returns_422_for_validation_error(monkeypatch):
    from acat.api.services.ingest_service import IntakeValidationError

    def fake_run_assessment(payload: dict) -> dict:
        raise IntakeValidationError("provider must be 'anthropic'")

    monkeypatch.setattr(
        "acat.api.routes.assess_router.run_assessment",
        fake_run_assessment,
    )

    response = client.post(
        "/api/v1/acat/assess",
        json={
            "agent_name": "Claude",
            "provider": "bad-provider",
            "api_key": "sk-test",
            "model": "bad-model",
        },
    )

    assert response.status_code == 422
    assert "provider must be 'anthropic'" in response.json()["detail"]


def test_assess_endpoint_returns_502_for_provider_error(monkeypatch):
    from acat.api.services.provider_clients.anthropic_client import AnthropicClientError

    def fake_run_assessment(payload: dict) -> dict:
        raise AnthropicClientError("Anthropic request failed")

    monkeypatch.setattr(
        "acat.api.routes.assess_router.run_assessment",
        fake_run_assessment,
    )

    response = client.post(
        "/api/v1/acat/assess",
        json={
            "agent_name": "Claude",
            "provider": "anthropic",
            "api_key": "sk-ant-test",
            "model": "claude-3-7-sonnet",
        },
    )

    assert response.status_code == 502
    assert "Anthropic request failed" in response.json()["detail"]
