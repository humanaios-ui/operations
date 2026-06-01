from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from acat.api.services.ingest_service import PersistenceError, ingest_phase3


def _all_12_scores() -> dict:
    return {
        "truth": 70,
        "service": 74,
        "harm": 72,
        "autonomy": 71,
        "value": 73,
        "humility": 69,
        "scheme": 78,
        "power": 75,
        "syc": 68,
        "consist": 74,
        "fair": 77,
        "handoff": 72,
    }


def _valid_phase3_payload() -> dict:
    return {
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "agent_name": "Claude",
        "phase": "phase3",
        "scores": _all_12_scores(),
        "submission_purity": "agent_self_only",
        "submitted_at": "2026-05-29T12:05:00+00:00"
    }


def _mock_get_response(row: dict):
    body = json.dumps([row]).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _mock_patch_response(row: dict):
    body = json.dumps([row]).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@pytest.fixture(autouse=True)
def supabase_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://ksinisdzgtnqzsymhfya.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")


def test_persist_phase3_updates_existing_row_and_returns_learning_index():
    existing_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "p1_truth": 80,
        "p1_service": 80,
        "p1_harm": 80,
        "p1_autonomy": 80,
        "p1_value": 80,
        "p1_humility": 80
    }

    patched_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "updated_at": "2026-05-29T12:05:01+00:00",
        "learning_index": 0.8958
    }

    with patch(
        "acat.api.services.ingest_service.urlopen",
        side_effect=[
            _mock_get_response(existing_row),
            _mock_patch_response(patched_row),
        ],
    ):
        result = ingest_phase3(_valid_phase3_payload())

    assert result["persisted"] is True
    assert result["supabase_id"] == "row-001"
    assert result["learning_index"] == 0.8958


def test_persist_phase3_computes_learning_index_from_existing_p1():
    existing_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "p1_truth": 80,
        "p1_service": 80,
        "p1_harm": 80,
        "p1_autonomy": 80,
        "p1_value": 80,
        "p1_humility": 80
    }

    patched_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "updated_at": "2026-05-29T12:05:01+00:00",
        "learning_index": 0.8958
    }

    with patch(
        "acat.api.services.ingest_service.urlopen",
        side_effect=[
            _mock_get_response(existing_row),
            _mock_patch_response(patched_row),
        ],
    ):
        result = ingest_phase3(_valid_phase3_payload())

    assert result["learning_index"] == 0.8958


def test_persist_phase3_returns_none_learning_index_when_p1_missing():
    existing_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "p1_truth": None,
        "p1_service": 80,
        "p1_harm": 80,
        "p1_autonomy": 80,
        "p1_value": 80,
        "p1_humility": 80
    }

    patched_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "updated_at": "2026-05-29T12:05:01+00:00",
        "learning_index": None
    }

    with patch(
        "acat.api.services.ingest_service.urlopen",
        side_effect=[
            _mock_get_response(existing_row),
            _mock_patch_response(patched_row),
        ],
    ):
        result = ingest_phase3(_valid_phase3_payload())

    assert result["learning_index"] is None


def test_persist_phase3_not_found_raises_persistence_error():
    empty_get_resp = MagicMock()
    empty_get_resp.read.return_value = b"[]"
    empty_get_resp.__enter__ = lambda s: s
    empty_get_resp.__exit__ = MagicMock(return_value=False)

    with patch("acat.api.services.ingest_service.urlopen", return_value=empty_get_resp):
        with pytest.raises(PersistenceError, match="not found"):
            ingest_phase3(_valid_phase3_payload())


def test_persist_phase3_http_error_on_patch_raises_persistence_error():
    existing_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "p1_truth": 80,
        "p1_service": 80,
        "p1_harm": 80,
        "p1_autonomy": 80,
        "p1_value": 80,
        "p1_humility": 80
    }

    patch_err = HTTPError(
        url="https://ksinisdzgtnqzsymhfya.supabase.co/rest/v1/acat_assessments_v1",
        code=409,
        msg="Conflict",
        hdrs={},
        fp=BytesIO(b'{"message":"conflict"}'),
    )

    with patch(
        "acat.api.services.ingest_service.urlopen",
        side_effect=[
            _mock_get_response(existing_row),
            patch_err,
        ],
    ):
        with pytest.raises(PersistenceError, match="409"):
            ingest_phase3(_valid_phase3_payload())


def test_persist_phase3_agent_self_only_purity():
    existing_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "p1_truth": 80,
        "p1_service": 80,
        "p1_harm": 80,
        "p1_autonomy": 80,
        "p1_value": 80,
        "p1_humility": 80
    }

    patched_row = {
        "id": "row-001",
        "assessment_id": "assessment-001",
        "updated_at": "2026-05-29T12:05:01+00:00",
        "learning_index": 0.8958
    }

    payload = _valid_phase3_payload()
    payload["submission_purity"] = "agent_self_only"

    with patch(
        "acat.api.services.ingest_service.urlopen",
        side_effect=[
            _mock_get_response(existing_row),
            _mock_patch_response(patched_row),
        ],
    ):
        result = ingest_phase3(payload)

    assert result["submission_purity"] == "agent_self_only"
    assert result["persisted"] is True
