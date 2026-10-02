from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ADAPTER_PATH = TOOLS / "control_plane_github_adapter_v0_1.py"
OBSERVER_PATH = TOOLS / "control_plane_custody_observer_v0_1.py"

adapter_spec = importlib.util.spec_from_file_location("control_plane_github_adapter", ADAPTER_PATH)
assert adapter_spec and adapter_spec.loader
adapter = importlib.util.module_from_spec(adapter_spec)
adapter_spec.loader.exec_module(adapter)

observer_spec = importlib.util.spec_from_file_location("control_plane_custody_observer", OBSERVER_PATH)
assert observer_spec and observer_spec.loader
observer = importlib.util.module_from_spec(observer_spec)
observer_spec.loader.exec_module(observer)


def test_positive_ai_watermark_is_preserved():
    raw = adapter.adapt_bundle({
        "source_type": "commit",
        "repository": "humanaios-ui/operations",
        "payload": {
            "sha": "7" * 40,
            "message": "humanaios-origin: ai-agent; agent=ChatGPT; purpose=test",
            "sender": {"login": "humanaios-ui"},
            "committed_at": "2026-10-01T00:00:00Z",
        },
    })
    assert raw["carrier_account"] == "humanaios-ui"
    assert raw["actor_origin"]["origin_class"] == "KNOWN_AI"
    assert raw["actor_origin"]["agent"] == "ChatGPT"


def test_plain_shared_account_does_not_become_human():
    raw = adapter.adapt_bundle({
        "source_type": "commit",
        "repository": "humanaios-ui/operations",
        "payload": {
            "sha": "8" * 40,
            "message": "ordinary commit",
            "sender": {"login": "humanaios-ui"},
            "committed_at": "2026-10-01T00:00:00Z",
        },
    })
    assert raw["actor_origin"]["origin_class"] == "SHARED_ACCOUNT_ORIGIN_UNKNOWN"


def test_bot_login_is_known_bot():
    raw = adapter.adapt_bundle({
        "source_type": "workflow_run",
        "repository": "humanaios-ui/operations",
        "payload": {
            "id": 123,
            "name": "quality-baseline",
            "head_sha": "a" * 40,
            "conclusion": "success",
            "actor": {"login": "github-actions[bot]"},
            "updated_at": "2026-10-01T00:00:00Z",
        },
    })
    assert raw["actor_origin"]["origin_class"] == "KNOWN_BOT"


def test_authority_and_decision_default_to_unknown():
    raw = adapter.adapt_bundle({
        "source_type": "pr_comment",
        "repository": "humanaios-ui/operations",
        "payload": {
            "id": 1,
            "body": "review note",
            "user": {"login": "humanaios-ui"},
            "created_at": "2026-10-01T00:00:00Z",
        },
    })
    assert raw["authority_evidence"]["state"] == "UNKNOWN"
    assert raw["custody"]["decision"] == "UNKNOWN"
    receipt = observer.normalize_observation(raw)
    assert receipt["custody_state"] == "UNKNOWN"
    assert receipt["authority_effect"] == "NONE"


def test_ref_error_can_carry_mechanical_boundary_without_authority():
    raw = adapter.adapt_bundle({
        "source_type": "ref_error",
        "repository": "humanaios-ui/operations",
        "payload": {
            "ref": "refs/heads/example",
            "message": "Repository rule violations found; cannot force-push",
            "sender": {"login": "humanaios-ui"},
        },
        "boundary": {
            "state": "MECHANICAL",
            "mechanism": "repository ruleset",
            "evidence_refs": ["api-error:422"],
        },
        "decision_custodian": "repository ruleset",
        "information_custodians": ["ChatGPT"],
        "evidence_refs": ["api-error:422"],
    })
    receipt = observer.normalize_observation(raw)
    assert receipt["boundary"]["state"] == "MECHANICAL"
    assert receipt["authority_effect"] == "NONE"


def test_pr593_fixture_adapts_and_validates():
    fixture = ROOT / "experiments" / "control-plane-custody" / "CPC-002" / "pr-593-github-evidence.json"
    bundles = adapter.load_bundles(fixture)
    observations = [adapter.adapt_bundle(bundle) for bundle in bundles]
    receipts = [observer.normalize_observation(item) for item in observations]
    assert len(receipts) >= 5
    by_id = {item["event_id"]: item for item in receipts}
    assert by_id["CPC-001-002"]["object"]["immutable_ref"] == "7b4461866e7eed00fd7960a254d6719d3ff08315"
    assert by_id["CPC-001-003"]["actor_origin"]["origin_class"] == "KNOWN_BOT"
    assert by_id["CPC-001-006"]["actor_origin"]["origin_class"] == "SHARED_ACCOUNT_ORIGIN_UNKNOWN"
    assert all(item["authority_effect"] == "NONE" for item in receipts)


def test_fixture_read_is_non_mutating():
    fixture = ROOT / "experiments" / "control-plane-custody" / "CPC-002" / "pr-593-github-evidence.json"
    before = fixture.read_bytes()
    _ = [adapter.adapt_bundle(bundle) for bundle in adapter.load_bundles(fixture)]
    assert fixture.read_bytes() == before
