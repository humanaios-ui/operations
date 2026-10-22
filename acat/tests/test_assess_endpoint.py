from __future__ import annotations

import time

from fastapi.testclient import TestClient

from acat.api.app import app

client = TestClient(app)

_WRITE_TOKEN = "test-token"
_WRITE_HEADERS = {"X-ACAT-Write-Token": _WRITE_TOKEN}


def _poll_until_done(job_id: str, timeout_seconds: float = 2.0) -> dict:
    """Poll GET /assess/{job_id} until the background job leaves 'running'.

    /assess is asynchronous: POST returns a job_id immediately and the
    actual assessment (or its failure) is only visible via polling.
    """
    deadline = time.monotonic() + timeout_seconds
    result = {"status": "running"}
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/acat/assess/{job_id}")
        result = response.json()
        if result["status"] != "running":
            return result
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} still running after {timeout_seconds}s")


def test_assess_endpoint_happy_path(monkeypatch):
    monkeypatch.setenv("ACAT_WRITE_TOKEN", _WRITE_TOKEN)

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
        headers=_WRITE_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    job_id = response.json()["job_id"]

    body = _poll_until_done(job_id)

    assert body["status"] == "completed"
    assert body["assessment_id"] == "acat-test-001"
    assert body["submission_purity"] == "two_stage_verified"
    assert body["learning_index"] == 0.8943
    assert body["phase1"]["persisted"] is True
    assert body["phase3"]["persisted"] is True
    assert "api_key" not in body


def test_assess_endpoint_returns_422_for_validation_error(monkeypatch):
    # Schema validation (assess_router's synchronous call to
    # validate_assess_request) runs before the background job is even
    # queued, so an invalid provider is rejected on the POST itself --
    # no run_assessment mock needed or reachable here.
    monkeypatch.setenv("ACAT_WRITE_TOKEN", _WRITE_TOKEN)

    response = client.post(
        "/api/v1/acat/assess",
        json={
            "agent_name": "Claude",
            "provider": "bad-provider",
            "api_key": "sk-test",
            "model": "bad-model",
        },
        headers=_WRITE_HEADERS,
    )

    assert response.status_code == 422
    assert "provider" in response.json()["detail"]


def test_assess_endpoint_reports_provider_error_via_poll(monkeypatch):
    # run_assessment only runs in the background job thread, so a provider
    # error can no longer surface as an HTTP 502 on the POST itself (there
    # is nothing left listening for the exception at that point) -- it
    # lands in the polled job record as status "failed" instead.
    from acat.api.services.provider_clients.anthropic_client import AnthropicClientError

    monkeypatch.setenv("ACAT_WRITE_TOKEN", _WRITE_TOKEN)

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
        headers=_WRITE_HEADERS,
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    body = _poll_until_done(job_id)

    assert body["status"] == "failed"
    assert "Anthropic request failed" in body["error"]
