"""Coverage for the fail-closed write-gate (audit S-062726 P0-URGENT mitigation)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from acat.api.app import app
from acat.api.security import require_write_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def _use_real_gate():
    # conftest installs a no-op override; remove it so these tests hit the real gate.
    app.dependency_overrides.pop(require_write_token, None)
    yield


def test_no_token_configured_pauses_writes(monkeypatch):
    monkeypatch.delenv("ACAT_WRITE_TOKEN", raising=False)
    r = client.post("/api/v1/acat/intake/phase1", json={"scores": {}})
    assert r.status_code == 503


def test_missing_header_is_unauthorized(monkeypatch):
    monkeypatch.setenv("ACAT_WRITE_TOKEN", "secret")
    r = client.post("/api/v1/acat/intake/phase1", json={"scores": {}})
    assert r.status_code == 401


def test_wrong_token_is_unauthorized(monkeypatch):
    monkeypatch.setenv("ACAT_WRITE_TOKEN", "secret")
    r = client.post(
        "/api/v1/acat/assess",
        headers={"X-ACAT-Write-Token": "nope"},
        json={},
    )
    assert r.status_code == 401


def test_correct_token_passes_gate(monkeypatch):
    monkeypatch.setenv("ACAT_WRITE_TOKEN", "secret")
    r = client.post(
        "/api/v1/acat/intake/phase1",
        headers={"X-ACAT-Write-Token": "secret"},
        json={"scores": {}},
    )
    # gate passed -> normal validation path (not 401/503)
    assert r.status_code not in (401, 503)


def test_read_endpoint_is_ungated(monkeypatch):
    monkeypatch.delenv("ACAT_WRITE_TOKEN", raising=False)
    assert client.get("/api/v1/acat/health").status_code == 200
