import pytest

from acat.api.services.normalize_service import normalize_phase1_payload


def test_normalize_phase1_adds_canonical_name():
    result = normalize_phase1_payload(
        {
            "session_id": "s1",
            "agent_name": " Claude ",
            "phase": "phase1",
            "scores": {},
            "submission_purity": "agent_self_only",
        }
    )
    assert result["agent_name_canonical"] == "claude"


def test_normalize_phase1_preserves_raw_agent_name():
    result = normalize_phase1_payload(
        {
            "session_id": "s1",
            "agent_name": " Claude-Sonnet-4-6 ",
            "phase": "phase1",
            "scores": {},
            "submission_purity": "agent_self_only",
        }
    )
    assert result["agent_name_raw"] == " Claude-Sonnet-4-6 "


def test_normalize_phase1_keeps_quality_flags_empty_for_valid_purity():
    result = normalize_phase1_payload(
        {
            "session_id": "s1",
            "agent_name": "Claude",
            "phase": "phase1",
            "scores": {},
            "submission_purity": "external_only",
        }
    )
    assert result["quality_flags"] == []


def test_normalize_phase1_builds_dedupe_key():
    result = normalize_phase1_payload(
        {
            "session_id": "s1",
            "agent_name": "Claude",
            "phase": "phase1",
            "scores": {},
            "submission_purity": "agent_self_only",
            "rater_id": "r1",
        }
    )
    assert result["dedupe_key"] == "s1:phase1:r1"


def test_normalize_phase1_rejects_invalid_submission_purity():
    with pytest.raises(ValueError):
        normalize_phase1_payload(
            {
                "session_id": "s1",
                "agent_name": "Claude",
                "phase": "phase1",
                "scores": {},
                "submission_purity": "bad-value",
            }
        )
