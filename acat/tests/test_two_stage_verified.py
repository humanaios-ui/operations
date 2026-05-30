from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from acat.api.services.ingest_service import (
    IntakeValidationError,
    _build_phase3_row,
    ingest_phase1,
    ingest_phase3,
)


def _phase1_payload() -> dict:
    return {
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "agent_name": "Claude",
        "provider": "anthropic",
        "phase": "phase1",
        "submission_purity": "agent_self_only",
        "scores": {
            "truth": 84,
            "service": 88,
            "harm": 82,
            "autonomy": 80,
            "value": 86,
            "humility": 72,
        },
        "p1_timestamp": "2026-05-29T12:00:00+00:00",
        "first_user_message_timestamp": "2026-05-29T12:00:30+00:00",
    }


def _phase3_payload(submission_purity: str = "agent_self_only", p3_committed_at: str | None = None) -> dict:
    payload = {
        "assessment_id": "assessment-001",
        "session_id": "session-001",
        "agent_name": "Claude",
        "provider": "anthropic",
        "phase": "phase3",
        "submission_purity": submission_purity,
        "scores": {
            "truth": 72,
            "service": 76,
            "harm": 74,
            "autonomy": 73,
            "value": 75,
            "humility": 70,
        },
        "submitted_at": "2026-05-29T12:05:00+00:00",
    }
    if p3_committed_at is not None:
        payload["p3_committed_at"] = p3_committed_at
    return payload


def test_ingest_phase1_sets_p1_committed_at():
    captured = {}

    def fake_persist(payload: dict) -> dict:
        captured["payload"] = payload
        return {
            "persisted": True,
            "supabase_id": "row-001",
            "created_at": "2026-05-29T12:00:01+00:00",
            "p1_committed_at": payload.get("p1_committed_at"),
        }

    with patch("acat.api.services.ingest_service._persist_phase1", side_effect=fake_persist):
        result = ingest_phase1(_phase1_payload())

    assert "p1_committed_at" in captured["payload"]
    assert captured["payload"]["p1_committed_at"] is not None
    assert result["p1_committed_at"] == captured["payload"]["p1_committed_at"]


def test_ingest_phase3_sets_p3_committed_at():
    captured = {}

    def fake_persist(payload: dict) -> dict:
        captured["payload"] = payload
        return {
            "persisted": True,
            "supabase_id": "row-001",
            "updated_at": "2026-05-29T12:05:01+00:00",
            "learning_index": 0.8943,
            "p3_committed_at": payload.get("p3_committed_at"),
            "submission_purity": payload.get("submission_purity"),
        }

    with patch("acat.api.services.ingest_service._persist_phase3", side_effect=fake_persist):
        result = ingest_phase3(_phase3_payload())

    assert "p3_committed_at" in captured["payload"]
    assert captured["payload"]["p3_committed_at"] is not None
    assert result["p3_committed_at"] == captured["payload"]["p3_committed_at"]


def test_build_phase3_row_allows_two_stage_verified_when_gap_is_at_least_60_seconds():
    existing_row = {
        "assessment_id": "assessment-001",
        "p1_committed_at": "2026-05-29T12:00:00+00:00",
        "p1_truth": 84,
        "p1_service": 88,
        "p1_harm": 82,
        "p1_autonomy": 80,
        "p1_value": 86,
        "p1_humility": 72,
    }

    payload = _phase3_payload(
        submission_purity="two_stage_verified",
        p3_committed_at="2026-05-29T12:01:00+00:00",
    )

    row = _build_phase3_row(payload, existing_row)

    assert row["submission_purity"] == "two_stage_verified"
    assert row["p3_committed_at"] == "2026-05-29T12:01:00+00:00"


def test_build_phase3_row_rejects_two_stage_verified_when_gap_is_less_than_60_seconds():
    existing_row = {
        "assessment_id": "assessment-001",
        "p1_committed_at": "2026-05-29T12:00:00+00:00",
        "p1_truth": 84,
        "p1_service": 88,
        "p1_harm": 82,
        "p1_autonomy": 80,
        "p1_value": 86,
        "p1_humility": 72,
    }

    payload = _phase3_payload(
        submission_purity="two_stage_verified",
        p3_committed_at="2026-05-29T12:00:30+00:00",
    )

    with pytest.raises(IntakeValidationError, match="two_stage_verified"):
        _build_phase3_row(payload, existing_row)


def test_build_phase3_row_preserves_agent_self_only():
    existing_row = {
        "assessment_id": "assessment-001",
        "p1_committed_at": "2026-05-29T12:00:00+00:00",
        "p1_truth": 84,
        "p1_service": 88,
        "p1_harm": 82,
        "p1_autonomy": 80,
        "p1_value": 86,
        "p1_humility": 72,
    }

    payload = _phase3_payload(
        submission_purity="agent_self_only",
        p3_committed_at="2026-05-29T12:00:30+00:00",
    )

    row = _build_phase3_row(payload, existing_row)

    assert row["submission_purity"] == "agent_self_only"
    assert row["p3_committed_at"] == "2026-05-29T12:00:30+00:00"
    assert row["learning_index"] == 0.8943
