from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from repository_coordinator_state_v1 import (
    AUTHORITY_EFFECT,
    StateError,
    append_event,
    canonical_json,
    make_event,
    parse_ledger,
    replay_events,
    sha256_text,
    verify_projection,
)

POLICY_SHA = "a" * 40
RECORDED = "2026-10-04T20:20:00Z"


def event(
    *,
    decision="ADMIT",
    kind="ISSUE",
    number=77,
    objective=77,
    supersedes=None,
    evidence=None,
):
    return make_event(
        decision=decision,
        subject_kind=kind,
        subject_number=number,
        objective_issue_number=objective,
        actor="humanaios-ui",
        evidence=evidence or [f"test evidence for {kind}#{number}"],
        recorded_at=RECORDED,
        source_policy_sha=POLICY_SHA,
        supersedes_event_id=supersedes,
    )


def ledger_text(events):
    return "".join(canonical_json(row) + "\n" for row in events)


def write_pair(tmp_path, events):
    ledger = tmp_path / "ADMISSION_LEDGER.jsonl"
    state = tmp_path / "COORDINATOR_STATE.json"
    text = ledger_text(events)
    ledger.write_text(text, encoding="utf-8")
    projection = replay_events(events, ledger_text=text)
    state.write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger, state, projection


def test_admit_revoke_readmit_replays_deterministically(tmp_path):
    first = event()
    revoked = event(
        decision="REVOKE",
        supersedes=first["event_id"],
        evidence=["operator revoked working-set standing"],
    )
    readmitted = event(
        decision="ADMIT",
        supersedes=revoked["event_id"],
        evidence=["operator restored working-set standing"],
    )
    ledger, state, projection = write_pair(tmp_path, [first, revoked, readmitted])
    verified = verify_projection(ledger, state)
    assert verified == projection
    assert verified["admitted_issue_numbers"] == [77]
    assert verified["active_event_ids"]["ISSUE#77"] == readmitted["event_id"]
    assert verified["merge_authority"] is False
    assert verified["authority_effect"] == AUTHORITY_EFFECT


def test_revoke_removes_standing(tmp_path):
    first = event(kind="PULL_REQUEST", number=707, objective=None)
    revoked = event(
        decision="REVOKE",
        kind="PULL_REQUEST",
        number=707,
        objective=None,
        supersedes=first["event_id"],
    )
    _, _, projection = write_pair(tmp_path, [first, revoked])
    assert projection["admitted_pull_request_numbers"] == []
    assert "PULL_REQUEST#707" not in projection["active_event_ids"]


def test_duplicate_event_id_fails():
    first = event()
    text = canonical_json(first) + "\n" + canonical_json(first) + "\n"
    with pytest.raises(StateError, match="duplicate event_id"):
        parse_ledger(text)


def test_malformed_event_fails():
    broken = event()
    broken["merge_authority"] = True
    with pytest.raises(StateError, match="merge authority"):
        parse_ledger(canonical_json(broken) + "\n")


def test_projection_tamper_fails(tmp_path):
    first = event()
    ledger, state, projection = write_pair(tmp_path, [first])
    projection["admitted_issue_numbers"] = [77, 999]
    state.write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(StateError, match="diverges"):
        verify_projection(ledger, state)


def test_ledger_prefix_tamper_is_detected_before_append(tmp_path):
    first = event()
    ledger, state, _ = write_pair(tmp_path, [first])
    original = ledger.read_text(encoding="utf-8")
    ledger.write_text(original.replace("test evidence", "tampered evidence"), encoding="utf-8")
    with pytest.raises(StateError, match="diverges"):
        append_event(
            ledger_path=ledger,
            state_path=state,
            decision="ADMIT",
            subject_kind="ISSUE",
            subject_number=88,
            objective_issue_number=88,
            actor="humanaios-ui",
            evidence=["new admission"],
            recorded_at="2026-10-04T20:21:00Z",
            source_policy_sha=POLICY_SHA,
        )


def test_append_preserves_prefix_and_updates_projection(tmp_path):
    first = event()
    ledger, state, before = write_pair(tmp_path, [first])
    old_text = ledger.read_text(encoding="utf-8")
    result = append_event(
        ledger_path=ledger,
        state_path=state,
        decision="ADMIT",
        subject_kind="PULL_REQUEST",
        subject_number=716,
        objective_issue_number=717,
        actor="humanaios-ui",
        evidence=["explicit working-set admission"],
        recorded_at="2026-10-04T20:22:00Z",
        source_policy_sha=POLICY_SHA,
    )
    new_text = ledger.read_text(encoding="utf-8")
    assert new_text.startswith(old_text)
    assert result["prior_ledger_sha256"] == sha256_text(old_text)
    verified = verify_projection(ledger, state)
    assert verified["admitted_issue_numbers"] == [77]
    assert verified["admitted_pull_request_numbers"] == [716]
    assert verified["ledger_event_count"] == before["ledger_event_count"] + 1


def test_repeat_admit_without_revoke_fails(tmp_path):
    first = event()
    ledger, state, _ = write_pair(tmp_path, [first])
    with pytest.raises(StateError, match="already-active"):
        append_event(
            ledger_path=ledger,
            state_path=state,
            decision="ADMIT",
            subject_kind="ISSUE",
            subject_number=77,
            objective_issue_number=77,
            actor="humanaios-ui",
            evidence=["duplicate admission"],
            recorded_at="2026-10-04T20:23:00Z",
            source_policy_sha=POLICY_SHA,
        )


def test_first_event_cannot_claim_supersession():
    row = event(supersedes="RCSEVT-OTHER")
    text = ledger_text([row])
    parsed = parse_ledger(text)
    with pytest.raises(StateError, match="first event"):
        replay_events(parsed, ledger_text=text)


def test_event_cannot_grant_merge_authority():
    row = event()
    row["merge_authority"] = True
    with pytest.raises(StateError):
        parse_ledger(canonical_json(row) + "\n")
