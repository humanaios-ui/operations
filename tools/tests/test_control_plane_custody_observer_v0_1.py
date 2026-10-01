from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "control_plane_custody_observer_v0_1.py"
SCHEMA_PATH = ROOT / "schemas" / "control_plane_custody_event_v0_1.schema.json"


spec = importlib.util.spec_from_file_location("control_plane_custody_observer", TOOL_PATH)
assert spec and spec.loader
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)


def raw_event(**overrides):
    event = {
        "event_id": "evt-1",
        "observed_at": "2026-10-01T03:41:02Z",
        "repository": "humanaios-ui/operations",
        "object": {
            "type": "pull_request",
            "id": "593",
            "url": "https://github.com/humanaios-ui/operations/pull/593",
            "immutable_ref": "7b4461866e7eed00fd7960a254d6719d3ff08315",
        },
        "action": "RESTACK",
        "outcome": {"state": "SUCCEEDED", "summary": "branch restacked"},
        "carrier_account": "humanaios-ui",
        "actor_origin": {
            "origin_class": "KNOWN_AI",
            "agent": "ChatGPT",
            "evidence": ["explicit watermark"],
        },
        "authority_evidence": {"state": "NONE", "scope": None, "refs": []},
        "boundary": {
            "state": "MECHANICAL",
            "mechanism": "branch rules",
            "evidence_refs": ["issue:620"],
        },
        "custody": {
            "execution": "GitHub Git Data API",
            "decision": "ChatGPT",
            "information": ["humanaios-ui repository"],
        },
        "evidence_refs": ["commit:7b4461866e7e"],
        "uncertainty": [],
    }
    event.update(overrides)
    return event


def test_custody_derivation():
    assert observer.derive_custody_state("exec", "decide", ["info"]) == "SEPARATED"
    assert observer.derive_custody_state("same", "same", ["info"]) == "COLLAPSED"
    assert observer.derive_custody_state("exec", "decide", ["exec"]) == "MIXED"
    assert observer.derive_custody_state("exec", "UNKNOWN", ["info"]) == "UNKNOWN"


def test_normalizer_never_grants_authority():
    receipt = observer.normalize_observation(raw_event())
    assert receipt["authority_effect"] == "NONE"
    with pytest.raises(observer.ObservationError):
        observer.normalize_observation(raw_event(authority_effect="MERGE"))


def test_unknowns_remain_unknown():
    event = raw_event()
    event["custody"] = {
        "execution": "",
        "decision": "workflow-policy",
        "information": ["observer"],
    }
    receipt = observer.normalize_observation(event)
    assert receipt["custody"]["execution"] == "UNKNOWN"
    assert receipt["custody_state"] == "UNKNOWN"


def test_schema_rejects_non_none_authority_effect():
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    receipt = observer.normalize_observation(raw_event())
    validator.validate(receipt)
    receipt["authority_effect"] = "MERGE"
    with pytest.raises(ValidationError):
        validator.validate(receipt)


def test_specimen_replays_without_mutation(tmp_path):
    specimen = ROOT / "experiments" / "control-plane-custody" / "CPC-001" / "pr-593-observations.json"
    before = specimen.read_bytes()
    rows = observer.load_observations(specimen)
    receipts = [observer.normalize_observation(row) for row in rows]
    output = tmp_path / "receipts.json"
    output.write_text(observer.render(receipts))
    assert specimen.read_bytes() == before
    assert len(receipts) >= 7
    assert all(row["authority_effect"] == "NONE" for row in receipts)
