#!/usr/bin/env python3
"""Repository Coordinator state v1.1 hardening.
Builder v1.7 compliant
HumanAIOS — REPOSITORY-COORDINATOR-STATE-02

Extends the v1 bootstrap ledger without rewriting it. Existing v1 ledgers and
projections remain valid until the first v2 event is appended. New v2 events
add a global sequence/hash chain, durable RCC command references, admission
scope, lifecycle termination, and deterministic projection metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import repository_coordinator_state_v1 as legacy

TOOL_NAME = "repository_coordinator_state_v1_1"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1
TOOL_SESSION = "REPOSITORY-COORDINATOR-STATE-02"

LEGACY_EVENT_SCHEMA = legacy.EVENT_SCHEMA
EVENT_SCHEMA = "humanaios.repository-coordinator-event.v2"
STATE_SCHEMA = "humanaios.repository-coordinator-state.v1.1"
AUTHORITY_EFFECT = legacy.AUTHORITY_EFFECT
STATE_BRANCH = legacy.STATE_BRANCH
SOURCE_LEDGER = legacy.SOURCE_LEDGER

DECISIONS = {"ADMIT", "REVOKE", "TERMINATE_MERGED", "TERMINATE_CLOSED"}
TERMINAL_DECISIONS = {"TERMINATE_MERGED", "TERMINATE_CLOSED"}
SUBJECT_KINDS = legacy.SUBJECT_KINDS


class StateError(legacy.StateError):
    pass


def canonical_json(value: Any) -> str:
    return legacy.canonical_json(value)


def sha256_text(text: str) -> str:
    return legacy.sha256_text(text)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StateError(message)


def legacy_event_hash(event: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event).encode("utf-8")).hexdigest()


def event_hash(event: dict[str, Any]) -> str:
    if event.get("schema") == EVENT_SCHEMA:
        return str(event["event_hash"])
    return legacy_event_hash(event)


def command_ref(source_kind: str, source_id: str) -> str:
    kind = source_kind.strip().upper().replace("_", "-")
    source = source_id.strip()
    _require(bool(kind) and bool(source), "command source kind and id are required")
    return f"RCC-{kind}-{source}"


def _hash_v2_payload(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("event_hash", None)
    payload.pop("event_id", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_v2_event(event: dict[str, Any], *, line_number: int | None = None) -> None:
    prefix = f"line {line_number}: " if line_number is not None else ""
    required = {
        "schema", "event_id", "sequence", "previous_event_hash", "event_hash",
        "command_ref", "decision", "subject_kind", "subject_number",
        "objective_issue_number", "admission_scope", "lane",
        "authority_effect", "merge_authority", "evidence", "source_locator",
        "recorded_at", "actor", "source_policy_sha", "supersedes_event_id",
    }
    missing = sorted(required - set(event))
    _require(not missing, prefix + f"missing v2 event fields: {missing}")
    _require(event["schema"] == EVENT_SCHEMA, prefix + "unsupported v2 event schema")
    _require(
        isinstance(event["sequence"], int)
        and not isinstance(event["sequence"], bool)
        and event["sequence"] > 0,
        prefix + "sequence must be a positive integer",
    )
    prev = event["previous_event_hash"]
    _require(
        prev is None or (
            isinstance(prev, str)
            and len(prev) == 64
            and all(ch in "0123456789abcdef" for ch in prev)
        ),
        prefix + "previous_event_hash must be null or lowercase sha256",
    )
    _require(event["decision"] in DECISIONS, prefix + "invalid decision")
    _require(event["subject_kind"] in SUBJECT_KINDS, prefix + "invalid subject_kind")
    if event["decision"] in TERMINAL_DECISIONS:
        _require(
            event["subject_kind"] == "PULL_REQUEST",
            prefix + "terminal lifecycle event must target PULL_REQUEST",
        )
    _require(
        isinstance(event["subject_number"], int)
        and not isinstance(event["subject_number"], bool)
        and event["subject_number"] > 0,
        prefix + "subject_number must be a positive integer",
    )
    objective = event["objective_issue_number"]
    _require(
        objective is None or (
            isinstance(objective, int)
            and not isinstance(objective, bool)
            and objective > 0
        ),
        prefix + "objective_issue_number must be null or positive integer",
    )
    _require(
        isinstance(event["admission_scope"], str) and event["admission_scope"].strip(),
        prefix + "admission_scope is required",
    )
    _require(
        event["authority_effect"] == AUTHORITY_EFFECT,
        prefix + "authority_effect must remain ADMISSION_ROUTING_ONLY",
    )
    _require(event["merge_authority"] is False, prefix + "merge authority must be false")
    _require(
        isinstance(event["command_ref"], str) and event["command_ref"].startswith("RCC-"),
        prefix + "command_ref must be RCC-*",
    )
    _require(
        isinstance(event["source_locator"], str) and event["source_locator"].strip(),
        prefix + "source_locator is required",
    )
    _require(
        isinstance(event["evidence"], list)
        and event["evidence"]
        and all(isinstance(x, str) and x.strip() for x in event["evidence"]),
        prefix + "evidence must be non-empty strings",
    )
    _require(
        isinstance(event["actor"], str) and event["actor"].strip(),
        prefix + "actor is required",
    )
    _require(
        isinstance(event["recorded_at"], str) and event["recorded_at"].strip(),
        prefix + "recorded_at is required",
    )
    _require(
        isinstance(event["source_policy_sha"], str)
        and legacy.SHA40_RE.fullmatch(event["source_policy_sha"]) is not None,
        prefix + "source_policy_sha must be a 40-char lowercase hex SHA",
    )
    supersedes = event["supersedes_event_id"]
    _require(
        supersedes is None
        or (isinstance(supersedes, str) and supersedes.startswith("RCSEVT-")),
        prefix + "supersedes_event_id must be null or RCSEVT-*",
    )
    expected_hash = _hash_v2_payload(event)
    _require(event["event_hash"] == expected_hash, prefix + "event_hash mismatch")
    _require(
        event["event_id"] == "RCSEVT-" + expected_hash[:16].upper(),
        prefix + "event_id does not match event_hash",
    )


def parse_ledger(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    ids: set[str] = set()
    seen_v2 = False
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StateError(f"line {line_number}: invalid JSON: {exc}") from exc
        _require(isinstance(event, dict), f"line {line_number}: event must be object")
        schema = event.get("schema")
        if schema == LEGACY_EVENT_SCHEMA:
            _require(not seen_v2, f"line {line_number}: legacy event cannot follow v2 event")
            legacy.validate_event(event, line_number=line_number)
        elif schema == EVENT_SCHEMA:
            seen_v2 = True
            validate_v2_event(event, line_number=line_number)
        else:
            raise StateError(f"line {line_number}: unsupported event schema {schema!r}")
        eid = str(event["event_id"])
        _require(eid not in ids, f"line {line_number}: duplicate event_id {eid}")
        ids.add(eid)
        events.append(event)
    _require(events, "ledger must contain at least one event")
    return events


def _replay_context(events: list[dict[str, Any]]) -> dict[str, Any]:
    active: dict[str, dict[str, Any]] = {}
    last_by_subject: dict[str, str] = {}
    commands: set[str] = set()
    previous_hash: str | None = None
    seen_v2 = False
    legacy_prefix_lines: list[str] = []

    for index, event in enumerate(events, start=1):
        schema = event["schema"]
        if schema == EVENT_SCHEMA:
            expected_previous = (
                sha256_text("".join(legacy_prefix_lines))
                if not seen_v2 and legacy_prefix_lines
                else previous_hash
            )
            seen_v2 = True
            validate_v2_event(event, line_number=index)
            _require(event["sequence"] == index, f"line {index}: sequence must equal {index}")
            _require(
                event["previous_event_hash"] == expected_previous,
                f"line {index}: previous_event_hash does not match ledger predecessor/legacy anchor",
            )
            cref = str(event["command_ref"])
            _require(cref not in commands, f"line {index}: duplicate command_ref {cref}")
            commands.add(cref)
        else:
            _require(not seen_v2, f"line {index}: legacy event cannot follow v2 event")
            legacy.validate_event(event, line_number=index)
            legacy_prefix_lines.append(canonical_json(event) + "\n")

        kind = str(event["subject_kind"])
        number = int(event["subject_number"])
        key = f"{kind}#{number}"
        eid = str(event["event_id"])
        prior = last_by_subject.get(key)
        supersedes = event.get("supersedes_event_id")
        if prior is None:
            _require(
                supersedes is None,
                f"line {index}: first event for {key} cannot supersede another event",
            )
        else:
            _require(
                supersedes == prior,
                f"line {index}: {eid} must supersede latest {key} event {prior}",
            )

        decision = str(event["decision"])
        if decision == "ADMIT":
            _require(key not in active, f"line {index}: cannot ADMIT already-active {key}")
            active[key] = {
                "event_id": eid,
                "objective_issue_number": event.get("objective_issue_number"),
                "admission_scope": (
                    event.get("admission_scope")
                    or (
                        f"objective:ISSUE#{event['objective_issue_number']}"
                        if event.get("objective_issue_number")
                        else f"subject:{key}"
                    )
                ),
                "command_ref": event.get("command_ref"),
            }
        else:
            _require(key in active, f"line {index}: cannot {decision} inactive subject {key}")
            active.pop(key)
        last_by_subject[key] = eid
        previous_hash = event_hash(event)

    if not seen_v2 and legacy_prefix_lines:
        previous_hash = sha256_text("".join(legacy_prefix_lines))

    return {
        "active": active,
        "last_by_subject": last_by_subject,
        "commands": commands,
        "last_event_hash": previous_hash,
        "seen_v2": seen_v2,
    }


def replay_events(
    events: list[dict[str, Any]],
    *,
    ledger_text: str,
    state_branch: str = STATE_BRANCH,
    source_ledger: str = SOURCE_LEDGER,
) -> dict[str, Any]:
    ctx = _replay_context(events)
    if not ctx["seen_v2"]:
        return legacy.replay_events(
            events,
            ledger_text=ledger_text,
            state_branch=state_branch,
            source_ledger=source_ledger,
        )

    active = ctx["active"]
    issues = sorted(int(k.split("#", 1)[1]) for k in active if k.startswith("ISSUE#"))
    prs = sorted(int(k.split("#", 1)[1]) for k in active if k.startswith("PULL_REQUEST#"))
    return {
        "active_event_ids": {
            key: value["event_id"] for key, value in sorted(active.items())
        },
        "active_admissions": dict(sorted(active.items())),
        "admitted_issue_numbers": issues,
        "admitted_pull_request_numbers": prs,
        "authority_effect": AUTHORITY_EFFECT,
        "consumed_command_refs": sorted(ctx["commands"]),
        "last_event_hash": ctx["last_event_hash"],
        "last_event_id": events[-1]["event_id"],
        "last_sequence": len(events),
        "ledger_event_count": len(events),
        "ledger_sha256": sha256_text(ledger_text),
        "merge_authority": False,
        "schema": STATE_SCHEMA,
        "source_ledger": source_ledger,
        "source_policy_sha": events[-1]["source_policy_sha"],
        "state_branch": state_branch,
    }


def verify_projection(ledger_path: Path, state_path: Path) -> dict[str, Any]:
    text = ledger_path.read_text(encoding="utf-8")
    events = parse_ledger(text)
    expected = replay_events(events, ledger_text=text)
    try:
        actual = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError(f"invalid state JSON: {exc}") from exc
    _require(isinstance(actual, dict), "state projection must be an object")
    _require(
        actual == expected,
        "materialized coordinator state diverges from deterministic ledger replay",
    )
    return expected


def make_event(
    *,
    decision: str,
    subject_kind: str,
    subject_number: int,
    objective_issue_number: int | None,
    admission_scope: str,
    command_ref_value: str,
    source_locator: str,
    actor: str,
    evidence: list[str],
    recorded_at: str,
    source_policy_sha: str,
    supersedes_event_id: str | None,
    sequence: int,
    previous_event_hash: str | None,
) -> dict[str, Any]:
    core = {
        "actor": actor.strip(),
        "admission_scope": admission_scope.strip(),
        "authority_effect": AUTHORITY_EFFECT,
        "command_ref": command_ref_value.strip(),
        "decision": decision.upper(),
        "evidence": [item.strip() for item in evidence if item.strip()],
        "lane": "WORKING_SET",
        "merge_authority": False,
        "objective_issue_number": objective_issue_number,
        "previous_event_hash": previous_event_hash,
        "recorded_at": recorded_at.strip(),
        "schema": EVENT_SCHEMA,
        "sequence": int(sequence),
        "source_locator": source_locator.strip(),
        "source_policy_sha": source_policy_sha.strip(),
        "subject_kind": subject_kind.upper(),
        "subject_number": int(subject_number),
        "supersedes_event_id": supersedes_event_id,
    }
    digest = hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()
    event = {"event_id": "RCSEVT-" + digest[:16].upper(), **core, "event_hash": digest}
    validate_v2_event(event)
    return event


def append_event(
    *,
    ledger_path: Path,
    state_path: Path,
    decision: str,
    subject_kind: str,
    subject_number: int,
    objective_issue_number: int | None,
    admission_scope: str,
    command_ref_value: str,
    source_locator: str,
    actor: str,
    evidence: list[str],
    recorded_at: str,
    source_policy_sha: str,
) -> dict[str, Any]:
    old_text = ledger_path.read_text(encoding="utf-8")
    old_events = parse_ledger(old_text)
    verified = verify_projection(ledger_path, state_path)
    ctx = _replay_context(old_events)

    _require(
        command_ref_value not in ctx["commands"],
        f"command_ref already consumed: {command_ref_value}",
    )
    key = f"{subject_kind.upper()}#{int(subject_number)}"
    decision = decision.upper()
    active = ctx["active"]
    if decision == "ADMIT":
        _require(key not in active, f"cannot ADMIT already-active subject {key}")
    else:
        _require(key in active, f"cannot {decision} inactive subject {key}")
    if decision in TERMINAL_DECISIONS:
        _require(
            subject_kind.upper() == "PULL_REQUEST",
            "terminal lifecycle event must target PULL_REQUEST",
        )

    if decision != "ADMIT" and not admission_scope.strip():
        admission_scope = str(active[key]["admission_scope"])

    event = make_event(
        decision=decision,
        subject_kind=subject_kind,
        subject_number=subject_number,
        objective_issue_number=objective_issue_number,
        admission_scope=admission_scope,
        command_ref_value=command_ref_value,
        source_locator=source_locator,
        actor=actor,
        evidence=evidence,
        recorded_at=recorded_at,
        source_policy_sha=source_policy_sha,
        supersedes_event_id=ctx["last_by_subject"].get(key),
        sequence=len(old_events) + 1,
        previous_event_hash=ctx["last_event_hash"],
    )
    new_text = old_text + canonical_json(event) + "\n"
    _require(new_text.startswith(old_text), "ledger prefix changed during append")
    new_events = old_events + [event]
    state = replay_events(new_events, ledger_text=new_text)
    ledger_path.write_text(new_text, encoding="utf-8")
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "event": event,
        "state": state,
        "prior_ledger_sha256": verified["ledger_sha256"],
    }


def apply_issue_command(
    *,
    policy_path: Path,
    ledger_path: Path,
    state_path: Path,
    issue_number: int,
    issue_body: str,
    comment_body: str,
    actor: str,
    comment_id: str,
    recorded_at: str,
    source_policy_sha: str,
    repository: str,
) -> dict[str, Any]:
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError(f"invalid policy JSON: {exc}") from exc
    route = (policy.get("state") or {}).get("issue_route") or {}
    _require(route.get("enabled") is True, "issue route is not enabled")
    _require(route.get("authority_effect") == AUTHORITY_EFFECT, "invalid issue-route authority")
    _require(route.get("merge_authority") is False, "issue route merge authority must be false")
    authorized = {str(x) for x in (policy.get("state") or {}).get("authorized_mutators") or []}
    _require(actor in authorized, f"actor {actor!r} is not authorized to mutate coordinator state")

    commands = route.get("commands") or {}
    command = comment_body or ""
    if command == str(commands.get("admit") or ""):
        decision = "ADMIT"
    elif command == str(commands.get("revoke") or ""):
        decision = "REVOKE"
    else:
        return {
            "should_mutate": False,
            "reason": "NOT_COORDINATOR_COMMAND",
            "authority_effect": AUTHORITY_EFFECT,
            "merge_authority": False,
        }

    rcc = command_ref("GITHUB-COMMENT", comment_id)
    verified = verify_projection(ledger_path, state_path)
    if rcc in set(verified.get("consumed_command_refs") or []):
        return {
            "should_mutate": False,
            "reason": "DUPLICATE_COMMAND",
            "command_ref": rcc,
            "authority_effect": AUTHORITY_EFFECT,
            "merge_authority": False,
        }

    key = f"ISSUE#{int(issue_number)}"
    active = (verified.get("active_event_ids") or {}).get(key)
    if decision == "ADMIT":
        required = str(route.get("required_admit_issue_state") or "ADMISSION_REQUESTED").upper()
        observed = legacy._issue_state(issue_body)
        _require(observed == required, f"issue state must be {required}; observed {observed or 'UNSET'}")
        if active:
            return {
                "should_mutate": False,
                "reason": "ALREADY_ADMITTED",
                "decision": decision,
                "command_ref": rcc,
                "authority_effect": AUTHORITY_EFFECT,
                "merge_authority": False,
            }
    elif not active:
        return {
            "should_mutate": False,
            "reason": "ALREADY_REVOKED_OR_NEVER_ADMITTED",
            "decision": decision,
            "command_ref": rcc,
            "authority_effect": AUTHORITY_EFFECT,
            "merge_authority": False,
        }

    locator = f"github:{repository}:issue:{int(issue_number)}:comment:{comment_id}"
    result = append_event(
        ledger_path=ledger_path,
        state_path=state_path,
        decision=decision,
        subject_kind="ISSUE",
        subject_number=int(issue_number),
        objective_issue_number=int(issue_number),
        admission_scope=f"objective:ISSUE#{int(issue_number)}",
        command_ref_value=rcc,
        source_locator=locator,
        actor=actor,
        evidence=[
            f"authorized exact issue-route command {command!r} by @{actor}",
            locator,
        ],
        recorded_at=recorded_at,
        source_policy_sha=source_policy_sha,
    )
    return {
        "should_mutate": True,
        "reason": "EVENT_APPENDED",
        "decision": decision,
        "command_ref": rcc,
        "event": result["event"],
        "state": result["state"],
        "authority_effect": AUTHORITY_EFFECT,
        "merge_authority": False,
    }


def reconcile_pr_lifecycle(
    *,
    ledger_path: Path,
    state_path: Path,
    pr_number: int,
    terminal_state: str,
    command_ref_value: str,
    source_locator: str,
    actor: str,
    recorded_at: str,
    source_policy_sha: str,
) -> dict[str, Any]:
    terminal = terminal_state.upper()
    _require(terminal in {"MERGED", "CLOSED"}, "terminal_state must be MERGED or CLOSED")
    verified = verify_projection(ledger_path, state_path)
    key = f"PULL_REQUEST#{int(pr_number)}"
    active = (verified.get("active_event_ids") or {}).get(key)
    if not active:
        return {
            "should_mutate": False,
            "reason": "PR_NOT_ACTIVE",
            "authority_effect": AUTHORITY_EFFECT,
            "merge_authority": False,
        }
    decision = "TERMINATE_MERGED" if terminal == "MERGED" else "TERMINATE_CLOSED"
    admission = (verified.get("active_admissions") or {}).get(key) or {}
    result = append_event(
        ledger_path=ledger_path,
        state_path=state_path,
        decision=decision,
        subject_kind="PULL_REQUEST",
        subject_number=int(pr_number),
        objective_issue_number=admission.get("objective_issue_number"),
        admission_scope=str(admission.get("admission_scope") or f"subject:{key}"),
        command_ref_value=command_ref_value,
        source_locator=source_locator,
        actor=actor,
        evidence=[f"GitHub PR #{int(pr_number)} reached terminal state {terminal}", source_locator],
        recorded_at=recorded_at,
        source_policy_sha=source_policy_sha,
    )
    return {
        "should_mutate": True,
        "reason": decision,
        "event": result["event"],
        "state": result["state"],
        "authority_effect": AUTHORITY_EFFECT,
        "merge_authority": False,
    }


def decision_receipt(
    *,
    gate_decision: dict[str, Any],
    created_at: str,
    source_run_id: str,
) -> dict[str, Any]:
    state_receipt = gate_decision.get("state_receipt") or {}
    payload = {
        "schema": "humanaios.repository-coordinator-decision-receipt.v1",
        "target_pr": gate_decision.get("target_pr"),
        "target_head_sha": gate_decision.get("target_head_sha"),
        "policy_ref": state_receipt.get("policy_ref"),
        "policy_sha": state_receipt.get("policy_sha"),
        "state_branch": state_receipt.get("state_branch"),
        "state_sha": state_receipt.get("state_sha"),
        "ledger_sha256": state_receipt.get("ledger_sha256"),
        "projection_sha256": state_receipt.get("projection_sha256"),
        "decision": gate_decision.get("gate"),
        "lane": gate_decision.get("lane"),
        "reason": gate_decision.get("reason"),
        "authority_effect": AUTHORITY_EFFECT,
        "merge_authority": False,
        "created_at": created_at,
        "source_run_id": str(source_run_id),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return {"receipt_id": "RCD-" + digest[:16].upper(), **payload, "receipt_sha256": digest}


def run_smoke_test() -> bool:
    """Exercise the authority boundary and deterministic receipt primitives."""
    assert command_ref("GITHUB-COMMENT", "123") == "RCC-GITHUB-COMMENT-123"
    receipt = decision_receipt(
        gate_decision={
            "target_pr": 1,
            "target_head_sha": "b" * 40,
            "gate": "PASS",
            "lane": "CONTROL_PLANE",
            "reason": "smoke",
            "state_receipt": {
                "policy_ref": "main",
                "policy_sha": "a" * 40,
                "state_branch": STATE_BRANCH,
                "state_sha": "c" * 40,
                "ledger_sha256": "1" * 64,
                "projection_sha256": "2" * 64,
            },
        },
        created_at="2026-01-01T00:00:00Z",
        source_run_id="smoke",
    )
    assert receipt["receipt_id"].startswith("RCD-")
    assert receipt["authority_effect"] == AUTHORITY_EFFECT
    assert receipt["merge_authority"] is False
    return True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", type=Path, required=True)
    verify.add_argument("--state", type=Path, required=True)

    append = sub.add_parser("append")
    append.add_argument("--ledger", type=Path, required=True)
    append.add_argument("--state", type=Path, required=True)
    append.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    append.add_argument("--subject-kind", choices=sorted(SUBJECT_KINDS), required=True)
    append.add_argument("--subject-number", type=int, required=True)
    append.add_argument("--objective-issue-number", type=int)
    append.add_argument("--admission-scope", required=True)
    append.add_argument("--command-ref", required=True)
    append.add_argument("--source-locator", required=True)
    append.add_argument("--actor", required=True)
    append.add_argument("--evidence", action="append", required=True)
    append.add_argument("--recorded-at", required=True)
    append.add_argument("--source-policy-sha", required=True)

    issue = sub.add_parser("issue-command")
    issue.add_argument("--policy", type=Path, required=True)
    issue.add_argument("--ledger", type=Path, required=True)
    issue.add_argument("--state", type=Path, required=True)
    issue.add_argument("--issue-number", type=int, required=True)
    issue.add_argument("--issue-body-file", type=Path, required=True)
    issue.add_argument("--comment-body", required=True)
    issue.add_argument("--actor", required=True)
    issue.add_argument("--comment-id", required=True)
    issue.add_argument("--recorded-at", required=True)
    issue.add_argument("--source-policy-sha", required=True)
    issue.add_argument("--repository", required=True)

    life = sub.add_parser("reconcile-pr")
    life.add_argument("--ledger", type=Path, required=True)
    life.add_argument("--state", type=Path, required=True)
    life.add_argument("--pr-number", type=int, required=True)
    life.add_argument("--terminal-state", choices=["MERGED", "CLOSED"], required=True)
    life.add_argument("--command-ref", required=True)
    life.add_argument("--source-locator", required=True)
    life.add_argument("--actor", required=True)
    life.add_argument("--recorded-at", required=True)
    life.add_argument("--source-policy-sha", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.smoke_test:
        print("PASS" if run_smoke_test() else "FAIL")
        return 0
    if not args.command:
        print("coordinator-state-v1.1=FAIL reason=command required")
        return 2
    try:
        if args.command == "verify":
            state = verify_projection(args.ledger, args.state)
            print(json.dumps({"verified": True, **state}, indent=2, sort_keys=True))
            return 0
        if args.command == "issue-command":
            result = apply_issue_command(
                policy_path=args.policy,
                ledger_path=args.ledger,
                state_path=args.state,
                issue_number=args.issue_number,
                issue_body=args.issue_body_file.read_text(encoding="utf-8"),
                comment_body=args.comment_body,
                actor=args.actor,
                comment_id=args.comment_id,
                recorded_at=args.recorded_at,
                source_policy_sha=args.source_policy_sha,
                repository=args.repository,
            )
        elif args.command == "reconcile-pr":
            result = reconcile_pr_lifecycle(
                ledger_path=args.ledger,
                state_path=args.state,
                pr_number=args.pr_number,
                terminal_state=args.terminal_state,
                command_ref_value=args.command_ref,
                source_locator=args.source_locator,
                actor=args.actor,
                recorded_at=args.recorded_at,
                source_policy_sha=args.source_policy_sha,
            )
        else:
            result = append_event(
                ledger_path=args.ledger,
                state_path=args.state,
                decision=args.decision,
                subject_kind=args.subject_kind,
                subject_number=args.subject_number,
                objective_issue_number=args.objective_issue_number,
                admission_scope=args.admission_scope,
                command_ref_value=args.command_ref,
                source_locator=args.source_locator,
                actor=args.actor,
                evidence=args.evidence,
                recorded_at=args.recorded_at,
                source_policy_sha=args.source_policy_sha,
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, StateError, ValueError) as exc:
        print(f"coordinator-state-v1.1=FAIL reason={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
