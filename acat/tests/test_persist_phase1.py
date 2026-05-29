from __future__ import annotations

import json
import os
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from acat.api.services.ingest_service import PersistenceError, ingest_phase1


def _valid_payload() -> dict:
    return {
        "session_id": "test-session-001",
        "agent_name": "Claude",
        "phase": "phase1",
        "scores": {
            "truth": 85, "service": 88, "harm": 84,
            "autonomy": 83, "value": 86, "humility": 72,
        },
        "submission_purity": "clean",
        "p1_timestamp": "2026-05-29T12:00:00+00:00",
        "first_user_message_timestamp": "2026-05-29T12:00:30+00:00",
    }


def _mock_supabase_response(row_id="abc-123", created_at="2026-05-29T12:00:01+00:00"):
    """Returns a mock urlopen response that looks like Supabase returning a row."""
    body = json.dumps([{"id": row_id, "created_at": created_at}]).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@pytest.fixture(autouse=True)
def supabase_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://ksinisdzgtnqzsymhfya.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")


def test_persist_phase1_returns_supabase_id():
    with patch("acat.api.services.ingest_service.urlopen",
               return_value=_mock_supabase_response("row-uuid-001")):
        result = ingest_phase1(_valid_payload())

    assert result["persisted"] is True
    assert result["supabase_id"] == "row-uuid-001"
    assert result["created_at"] is not None


def test_persist_phase1_contamination_clean():
    with patch("acat.api.services.ingest_service.urlopen",
               return_value=_mock_supabase_response()):
        result = ingest_phase1(_valid_payload())

    assert result["contamination_delta_seconds"] == 30
    assert result["contamination_status"] == "clean"


def test_persist_phase1_http_error_raises_persistence_error():
    mock_err = HTTPError(
        url="https://ksinisdzgtnqzsymhfya.supabase.co/rest/v1/acat_assessments_v1",
        code=409,
        msg="Conflict",
        hdrs={},
        fp=BytesIO(b'{"message":"duplicate key"}'),
    )
    with patch("acat.api.services.ingest_service.urlopen", side_effect=mock_err):
        with pytest.raises(PersistenceError, match="409"):
            ingest_phase1(_valid_payload())


def test_persist_phase1_missing_env_raises_persistence_error(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    with pytest.raises(PersistenceError, match="SUPABASE_URL"):
        ingest_phase1(_valid_payload())


def test_persist_phase1_agent_self_only_purity():
    """Regression: agent_self_only must pass validation end-to-end after IC-032."""
    payload = _valid_payload()
    payload["submission_purity"] = "agent_self_only"

    with patch("acat.api.services.ingest_service.urlopen",
               return_value=_mock_supabase_response()):
        result = ingest_phase1(payload)

    assert result["submission_purity"] == "agent_self_only"
    assert result["persisted"] is True
