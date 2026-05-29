import pytest

from acat.api.services.ingest_service import IntakeValidationError, ingest_phase1


def _valid_payload() -> dict:
    return {
        "session_id": "s1",
        "agent_name": "Claude",
        "phase": "phase1",
        "scores": {
            "truth": 80,
            "service": 80,
            "harm": 80,
            "autonomy": 80,
            "value": 80,
            "humility": 80,
        },
        "submission_purity": "clean",
    }


def test_ingest_phase1_accepts_valid_payload():
    result = ingest_phase1(_valid_payload())
    assert result["status"] == "accepted"
    assert result["phase"] == "phase1"
    assert result["session_id"] == "s1"
    assert result["persisted"] is True


def test_ingest_phase1_sets_assessment_id():
    result = ingest_phase1(_valid_payload())
    assert result["assessment_id"] is not None
    assert isinstance(result["assessment_id"], str)
    assert len(result["assessment_id"]) > 0


def test_ingest_phase1_rejects_invalid_submission_purity():
    payload = _valid_payload()
    payload["submission_purity"] = "not-valid"

    with pytest.raises(IntakeValidationError):
        ingest_phase1(payload)


def test_ingest_phase1_rejects_missing_required_scores():
    payload = _valid_payload()
    del payload["scores"]["humility"]

    with pytest.raises(IntakeValidationError):
        ingest_phase1(payload)


def test_ingest_phase1_computes_clean_contamination_status():
    payload = _valid_payload()
    payload["p1_timestamp"] = "2026-05-29T12:00:00+00:00"
    payload["first_user_message_timestamp"] = "2026-05-29T12:00:30+00:00"

    result = ingest_phase1(payload)

    assert result["contamination_delta_seconds"] == 30
    assert result["contamination_status"] == "clean"


def test_ingest_phase1_computes_contaminated_status():
    payload = _valid_payload()
    payload["p1_timestamp"] = "2026-05-29T12:00:00+00:00"
    payload["first_user_message_timestamp"] = "2026-05-29T12:02:00+00:00"

    result = ingest_phase1(payload)

    assert result["contamination_delta_seconds"] == 120
    assert result["contamination_status"] == "contaminated"


def test_ingest_phase1_accepts_missing_first_message_timestamp():
    result = ingest_phase1(_valid_payload())
    assert result["contamination_status"] == "unknown"
