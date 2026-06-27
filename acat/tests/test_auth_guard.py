"""Tests for the acat/ write-guard middleware (S-062726 · auth reopen)."""
from fastapi.testclient import TestClient

from acat.api.app import app

client = TestClient(app)

# A mutating endpoint that returns 422 on an empty body once the request passes the guard
# (so "not 401 and not 503" reliably proves the guard let it through to the route).
WRITE_PATH = "/api/v1/acat/human-score"


def test_keyless_write_allowed_when_no_keys_configured(monkeypatch):
    monkeypatch.delenv("ACAT_API_KEYS", raising=False)
    monkeypatch.delenv("ACAT_WRITES_PAUSED", raising=False)
    r = client.post(WRITE_PATH, json={})
    assert r.status_code not in (401, 503)


def test_pause_returns_503(monkeypatch):
    monkeypatch.setenv("ACAT_WRITES_PAUSED", "1")
    r = client.post(WRITE_PATH, json={})
    assert r.status_code == 503


def test_key_required_when_configured(monkeypatch):
    monkeypatch.delenv("ACAT_WRITES_PAUSED", raising=False)
    monkeypatch.setenv("ACAT_API_KEYS", "secret-key-1,secret-key-2")
    # missing key -> 401
    assert client.post(WRITE_PATH, json={}).status_code == 401
    # invalid key -> 401
    assert client.post(WRITE_PATH, json={}, headers={"X-ACAT-Key": "nope"}).status_code == 401
    # valid key -> passes the guard (reaches the route)
    ok = client.post(WRITE_PATH, json={}, headers={"X-ACAT-Key": "secret-key-1"})
    assert ok.status_code not in (401, 503)


def test_get_endpoints_never_guarded(monkeypatch):
    monkeypatch.setenv("ACAT_API_KEYS", "secret-key-1")
    monkeypatch.setenv("ACAT_WRITES_PAUSED", "1")
    assert client.get("/api/v1/acat/health").status_code == 200
