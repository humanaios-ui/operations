from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import repository_coordinator_state_v1 as legacy
from repository_coordinator_state_v1_1 import (
    AUTHORITY_EFFECT,
    EVENT_SCHEMA,
    STATE_SCHEMA,
    StateError,
    append_event,
    apply_issue_command,
    canonical_json,
    command_ref,
    decision_receipt,
    event_hash,
    legacy_event_hash,
    parse_ledger,
    reconcile_pr_lifecycle,
    replay_events,
    verify_projection,
)

POLICY_SHA = "a" * 40


def legacy_event(*, kind="ISSUE", number=1, objective=1):
    return legacy.make_event(
        decision="ADMIT",
        subject_kind=kind,
        subject_number=number,
        objective_issue_number=objective,
        actor="humanaios-ui",
        evidence=["legacy bootstrap"],
        recorded_at="2026-10-04T20:20:00Z",
        source_policy_sha=POLICY_SHA,
        supersedes_event_id=None,
    )


def write_legacy_pair(tmp_path, events):
    ledger = tmp_path / "ADMISSION_LEDGER.jsonl"
    state = tmp_path / "COORDINATOR_STATE.json"
    text = "".join(canonical_json(row) + "\n" for row in events)
    ledger.write_text(text, encoding="utf-8")
    projection = legacy.replay_events(events, ledger_text=text)
    state.write_text(json.dumps(projection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger, state, projection


def write_policy(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({
        "state": {
            "authorized_mutators": ["humanaios-ui"],
            "issue_route": {
                "enabled": True,
                "subject_kind": "ISSUE",
                "commands": {
                    "admit": "/coordinator admit",
                    "revoke": "/coordinator revoke",
                },
                "required_admit_issue_state": "ADMISSION_REQUESTED",
                "authority_effect": AUTHORITY_EFFECT,
                "merge_authority": False,
            },
        }
    }, indent=2) + "\n", encoding="utf-8")
    return path


def test_legacy_v1_projection_remains_valid_without_rewrite(tmp_path):
    ledger, state, projection = write_legacy_pair(tmp_path, [legacy_event()])
    verified = verify_projection(ledger, state)
    assert verified == projection
    assert verified["schema"] == legacy.STATE_SCHEMA


def test_first_v2_event_chains_from_last_legacy_event(tmp_path):
    first = legacy_event()
    ledger, state, _ = write_legacy_pair(tmp_path, [first])
    result = append_event(
        ledger_path=ledger,
        state_path=state,
        decision="ADMIT",
        subject_kind="PULL_REQUEST",
        subject_number=726,
        objective_issue_number=726,
        admission_scope="objective:ISSUE#726",
        command_ref_value="RCC-GITHUB-ACTIONS-100",
        source_locator="github:run:100",
        actor="humanaios-ui",
        evidence=["explicit admission"],
        recorded_at="2026-10-06T03:20:00Z",
        source_policy_sha=POLICY_SHA,
    )
    event = result["event"]
    assert event["schema"] == EVENT_SCHEMA
    assert event["sequence"] == 2
    assert event["previous_event_hash"] == legacy_event_hash(first)
    assert event["event_hash"] == event_hash(event)
    verified = verify_projection(ledger, state)
    assert verified["schema"] == STATE_SCHEMA
    assert verified["last_sequence"] == 2
    assert verified["last_event_hash"] == event["event_hash"]
    assert 726 in verified["admitted_pull_request_numbers"]


def test_duplicate_rcc_is_rejected_even_after_other_state_changes(tmp_path):
    first = legacy_event()
    ledger, state, _ = write_legacy_pair(tmp_path, [first])
    append_event(
        ledger_path=ledger,
        state_path=state,
        decision="ADMIT",
        subject_kind="PULL_REQUEST",
        subject_number=726,
        objective_issue_number=726,
        admission_scope="objective:ISSUE#726",
        command_ref_value="RCC-GITHUB-ACTIONS-100",
        source_locator="github:run:100",
        actor="humanaios-ui",
        evidence=["explicit admission"],
        recorded_at="2026-10-06T03:20:00Z",
        source_policy_sha=POLICY_SHA,
    )
    with pytest.raises(StateError, match="command_ref already consumed"):
        append_event(
            ledger_path=ledger,
            state_path=state,
            decision="REVOKE",
            subject_kind="PULL_REQUEST",
            subject_number=726,
            objective_issue_number=726,
            admission_scope="objective:ISSUE#726",
            command_ref_value="RCC-GITHUB-ACTIONS-100",
            source_locator="github:run:100",
            actor="humanaios-ui",
            evidence=["replayed command"],
            recorded_at="2026-10-06T03:21:00Z",
            source_policy_sha=POLICY_SHA,
        )


def test_issue_comment_rcc_is_idempotent(tmp_path):
    ledger, state, _ = write_legacy_pair(tmp_path, [legacy_event()])
    policy = write_policy(tmp_path)
    first = apply_issue_command(
        policy_path=policy,
        ledger_path=ledger,
        state_path=state,
        issue_number=726,
        issue_body="**State:** ADMISSION_REQUESTED",
        comment_body="/coordinator admit",
        actor="humanaios-ui",
        comment_id="98765",
        recorded_at="2026-10-06T03:22:00Z",
        source_policy_sha=POLICY_SHA,
        repository="humanaios-ui/operations",
    )
    assert first["should_mutate"] is True
    duplicate = apply_issue_command(
        policy_path=policy,
        ledger_path=ledger,
        state_path=state,
        issue_number=726,
        issue_body="**State:** ADMISSION_REQUESTED",
        comment_body="/coordinator admit",
        actor="humanaios-ui",
        comment_id="98765",
        recorded_at="2026-10-06T03:22:00Z",
        source_policy_sha=POLICY_SHA,
        repository="humanaios-ui/operations",
    )
    assert duplicate["should_mutate"] is False
    assert duplicate["reason"] == "DUPLICATE_COMMAND"
    assert duplicate["command_ref"] == command_ref("GITHUB-COMMENT", "98765")


def test_issue_command_requires_exact_body(tmp_path):
    ledger, state, before = write_legacy_pair(tmp_path, [legacy_event()])
    policy = write_policy(tmp_path)
    original = ledger.read_text(encoding="utf-8")
    for body in (" /coordinator admit", "/coordinator admit ", "\n/coordinator admit"):
        result = apply_issue_command(
            policy_path=policy,
            ledger_path=ledger,
            state_path=state,
            issue_number=726,
            issue_body="**State:** ADMISSION_REQUESTED",
            comment_body=body,
            actor="humanaios-ui",
            comment_id="whitespace",
            recorded_at="2026-10-06T03:22:00Z",
            source_policy_sha=POLICY_SHA,
            repository="humanaios-ui/operations",
        )
        assert result["should_mutate"] is False
        assert result["reason"] == "NOT_COORDINATOR_COMMAND"
    assert ledger.read_text(encoding="utf-8") == original
    assert verify_projection(ledger, state) == before


def test_global_chain_detects_reorder_or_delete(tmp_path):
    ledger, state, _ = write_legacy_pair(tmp_path, [legacy_event()])
    for n in (726, 727):
        append_event(
            ledger_path=ledger,
            state_path=state,
            decision="ADMIT",
            subject_kind="PULL_REQUEST",
            subject_number=n,
            objective_issue_number=n,
            admission_scope=f"objective:ISSUE#{n}",
            command_ref_value=f"RCC-GITHUB-ACTIONS-{n}",
            source_locator=f"github:run:{n}",
            actor="humanaios-ui",
            evidence=["explicit admission"],
            recorded_at=f"2026-10-06T03:{n-700:02d}:00Z",
            source_policy_sha=POLICY_SHA,
        )
    rows = [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines()]
    tampered = [rows[0], rows[2], rows[1]]
    with pytest.raises(StateError, match="previous_event_hash|legacy event cannot follow"):
        replay_events(tampered, ledger_text="".join(canonical_json(x)+"\n" for x in tampered))
    deleted = [rows[0], rows[2]]
    with pytest.raises(StateError, match="sequence|previous_event_hash"):
        replay_events(deleted, ledger_text="".join(canonical_json(x)+"\n" for x in deleted))


def test_terminal_pr_lifecycle_removes_active_standing(tmp_path):
    ledger, state, _ = write_legacy_pair(
        tmp_path,
        [legacy_event(kind="PULL_REQUEST", number=707, objective=None)],
    )
    result = reconcile_pr_lifecycle(
        ledger_path=ledger,
        state_path=state,
        pr_number=707,
        terminal_state="MERGED",
        command_ref_value="RCC-GITHUB-PR-LIFECYCLE-707-merged",
        source_locator="github:pull:707:closed",
        actor="github-actions[bot]",
        recorded_at="2026-10-06T03:30:00Z",
        source_policy_sha=POLICY_SHA,
    )
    assert result["should_mutate"] is True
    assert result["event"]["decision"] == "TERMINATE_MERGED"
    verified = verify_projection(ledger, state)
    assert 707 not in verified["admitted_pull_request_numbers"]


def test_terminal_unadmitted_pr_is_noop(tmp_path):
    ledger, state, _ = write_legacy_pair(tmp_path, [legacy_event()])
    result = reconcile_pr_lifecycle(
        ledger_path=ledger,
        state_path=state,
        pr_number=999,
        terminal_state="CLOSED",
        command_ref_value="RCC-GITHUB-PR-LIFECYCLE-999-closed",
        source_locator="github:pull:999:closed",
        actor="github-actions[bot]",
        recorded_at="2026-10-06T03:30:00Z",
        source_policy_sha=POLICY_SHA,
    )
    assert result["should_mutate"] is False
    assert result["reason"] == "PR_NOT_ACTIVE"


def test_decision_receipt_binds_policy_state_and_target():
    gate = {
        "target_pr": 726,
        "target_head_sha": "b" * 40,
        "gate": "PASS",
        "lane": "CONTROL_PLANE",
        "reason": "bounded control-plane change",
        "state_receipt": {
            "policy_ref": "main",
            "policy_sha": "a" * 40,
            "state_branch": "repository-coordinator-state",
            "state_sha": "c" * 40,
            "ledger_sha256": "1" * 64,
            "projection_sha256": "2" * 64,
        },
    }
    receipt = decision_receipt(
        gate_decision=gate,
        created_at="2026-10-06T03:40:00Z",
        source_run_id="1234",
    )
    assert receipt["receipt_id"].startswith("RCD-")
    assert receipt["target_pr"] == 726
    assert receipt["policy_sha"] == "a" * 40
    assert receipt["state_sha"] == "c" * 40
    assert receipt["merge_authority"] is False
