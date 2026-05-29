from acat.api.services.ingest_service import ingest_phase1


def test_ingest_phase1_accepts_valid_payload():
    result = ingest_phase1({
        "session_id": "s1",
        "agent_name": "Claude",
        "phase": "phase1",
        "scores": {
            "truth": 80,
            "service": 80,
            "harm": 80,
            "autonomy": 80,
            "value": 80,
            "humility": 80
        },
        "submission_purity": "clean"
    })
    assert result["status"] == "accepted"
