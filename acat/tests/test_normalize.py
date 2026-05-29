from acat.api.services.normalize_service import normalize_phase1_payload


def test_normalize_phase1_adds_canonical_name():
    result = normalize_phase1_payload({
        "session_id": "s1",
        "agent_name": " Claude ",
        "phase": "phase1",
        "scores": {},
        "submission_purity": "clean"
    })
    assert result["agent_name_canonical"] == "claude"
