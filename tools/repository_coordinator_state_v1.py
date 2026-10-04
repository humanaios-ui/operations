#!/usr/bin/env python3
"""Repository Coordinator state ledger + deterministic projection.
Builder v1.7 compliant
HumanAIOS — REPOSITORY-COORDINATOR-STATE-01

The state branch is evidence/state, not policy and never merge authority.

Canonical branch contract:
  repository-coordinator-state/
    ADMISSION_LEDGER.jsonl   append-oriented event history
    COORDINATOR_STATE.json   deterministic replay projection

This tool is intentionally filesystem-only. Workflows may fetch exact branch
content and run this trusted default-branch implementation against it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TOOL_NAME = "repository_coordinator_state"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1
TOOL_SESSION = "REPOSITORY-COORDINATOR-STATE-01"

EVENT_SCHEMA = "humanaios.repository-coordinator-event.v1"
STATE_SCHEMA = "humanaios.repository-coordinator-state.v1"
STATE_BRANCH = "repository-coordinator-state"
SOURCE_LEDGER = "ADMISSION_LEDGER.jsonl"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

DECISIONS = {"ADMIT", "REVOKE"}
SUBJECT_KINDS = {"ISSUE", "PULL_REQUEST"}
LANES = {"WORKING_SET"}
AUTHORITY_EFFECT = "ADMISSION_ROUTING_ONLY"


class StateError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StateError(message)


def validate_event(event: dict[str, Any], *, line_number: int | None = None) -> None:
    prefix = f"line {line_number}: " if line_number is not None else ""
    required = {
        "schema",
        "event_id",
        "decision",
        "subject_kind",
        "subject_number",
        "objective_issue_number",
        "lane",
        "authority_effect",
        "merge_authority",
        "evidence",
        "recorded_at",
        "actor",
        "source_policy_sha",
        "supersedes_event_id",
    }
    missing = sorted(required - set(event))
    _require(not missing, prefix + f"missing event fields: {missing}")
    _require(event["schema"] == EVENT_SCHEMA, prefix + "unsupported event schema")
    _require(str(event["event_id"]).startswith("RCSEVT-"), prefix + "invalid event_id")
    _require(event["decision"] in DECISIONS, prefix + "invalid decision")
    _require(event["subject_kind"] in SUBJECT_KINDS, prefix + "invalid subject_kind")
    _require(
        isinstance(event["subject_number"], int)
        and not isinstance(event["subject_number"], bool)
        and event["subject_number"] > 0,
        prefix + "subject_number must be a positive integer",
    )
    objective = event["objective_issue_number"]
    _require(
        objective is None
        or (
            isinstance(objective, int)
            and not isinstance(objective, bool)
            and objective > 0
        ),
        prefix + "objective_issue_number must be null or positive integer",
    )
    _require(event["lane"] in LANES, prefix + "unsupported lane")
    _require(
        event["authority_effect"] == AUTHORITY_EFFECT,
        prefix + "event authority_effect must be ADMISSION_ROUTING_ONLY",
    )
    _require(event["merge_authority"] is False, prefix + "merge authority must be false")
    evidence = event["evidence"]
    _require(
        isinstance(evidence, list)
        and evidence
        and all(isinstance(item, str) and item.strip() for item in evidence),
        prefix + "evidence must be a non-empty list of strings",
    )
    _require(
        isinstance(event["recorded_at"], str) and event["recorded_at"].strip(),
        prefix + "recorded_at is required",
    )
    _require(
        isinstance(event["actor"], str) and event["actor"].strip(),
        prefix + "actor is required",
    )
    _require(
        isinstance(event["source_policy_sha"], str)
        and SHA40_RE.fullmatch(event["source_policy_sha"]) is not None,
        prefix + "source_policy_sha must be a 40-char lowercase hex SHA",
    )
    supersedes = event["supersedes_event_id"]
    _require(
        supersedes is None
        or (isinstance(supersedes, str) and supersedes.startswith("RCSEVT-")),
        prefix + "supersedes_event_id must be null or RCSEVT-*",
    )


def parse_ledger(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    ids: set[str] = set()
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StateError(f"line {line_number}: invalid JSON: {exc}") from exc
        _require(isinstance(event, dict), f"line {line_number}: event must be object")
        validate_event(event, line_number=line_number)
        event_id = str(event["event_id"])
        _require(event_id not in ids, f"line {line_number}: duplicate event_id {event_id}")
        ids.add(event_id)
        events.append(event)
    _require(events, "ledger must contain at least one event")
    return events


def replay_events(
    events: list[dict[str, Any]],
    *,
    ledger_text: str,
    state_branch: str = STATE_BRANCH,
    source_ledger: str = SOURCE_LEDGER,
) -> dict[str, Any]:
    active: dict[str, str] = {}
    last_by_subject: dict[str, str] = {}

    for index, event in enumerate(events, start=1):
        validate_event(event, line_number=index)
        kind = str(event["subject_kind"])
        number = int(event["subject_number"])
        key = f"{kind}#{number}"
        event_id = str(event["event_id"])
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
                f"line {index}: {event_id} must supersede latest {key} event {prior}",
            )

        if event["decision"] == "ADMIT":
            active[key] = event_id
        else:
            _require(
                key in active,
                f"line {index}: cannot REVOKE inactive subject {key}",
            )
            active.pop(key)
        last_by_subject[key] = event_id

    admitted_issues = sorted(
        int(key.split("#", 1)[1])
        for key in active
        if key.startswith("ISSUE#")
    )
    admitted_prs = sorted(
        int(key.split("#", 1)[1])
        for key in active
        if key.startswith("PULL_REQUEST#")
    )

    return {
        "active_event_ids": dict(sorted(active.items())),
        "admitted_issue_numbers": admitted_issues,
        "admitted_pull_request_numbers": admitted_prs,
        "authority_effect": AUTHORITY_EFFECT,
        "last_event_id": events[-1]["event_id"],
        "ledger_event_count": len(events),
        "ledger_sha256": sha256_text(ledger_text),
        "merge_authority": False,
        "schema": STATE_SCHEMA,
        "source_ledger": source_ledger,
        "source_policy_sha": events[-1]["source_policy_sha"],
        "state_branch": state_branch,
    }


def load_and_replay(ledger_path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    text = ledger_path.read_text(encoding="utf-8")
    events = parse_ledger(text)
    return text, events, replay_events(events, ledger_text=text)


def verify_projection(ledger_path: Path, state_path: Path) -> dict[str, Any]:
    _, _, expected = load_and_replay(ledger_path)
    try:
        actual = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateError(f"invalid state JSON: {exc}") from exc
    _require(isinstance(actual, dict), "state projection must be an object")
    if actual != expected:
        raise StateError(
            "materialized coordinator state diverges from deterministic ledger replay"
        )
    return expected


def make_event(
    *,
    decision: str,
    subject_kind: str,
    subject_number: int,
    objective_issue_number: int | None,
    actor: str,
    evidence: list[str],
    recorded_at: str,
    source_policy_sha: str,
    supersedes_event_id: str | None,
) -> dict[str, Any]:
    core = {
        "actor": actor.strip(),
        "authority_effect": AUTHORITY_EFFECT,
        "decision": decision.upper(),
        "evidence": [item.strip() for item in evidence if item.strip()],
        "lane": "WORKING_SET",
        "merge_authority": False,
        "objective_issue_number": objective_issue_number,
        "recorded_at": recorded_at.strip(),
        "schema": EVENT_SCHEMA,
        "source_policy_sha": source_policy_sha.strip(),
        "subject_kind": subject_kind.upper(),
        "subject_number": int(subject_number),
        "supersedes_event_id": supersedes_event_id,
    }
    digest = hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()[:16].upper()
    event = {"event_id": f"RCSEVT-{digest}", **core}
    validate_event(event)
    return event


def append_event(
    *,
    ledger_path: Path,
    state_path: Path,
    decision: str,
    subject_kind: str,
    subject_number: int,
    objective_issue_number: int | None,
    actor: str,
    evidence: list[str],
    recorded_at: str,
    source_policy_sha: str,
) -> dict[str, Any]:
    old_text = ledger_path.read_text(encoding="utf-8")
    old_events = parse_ledger(old_text)
    verify_projection(ledger_path, state_path)

    key = f"{subject_kind.upper()}#{int(subject_number)}"
    last_by_subject: dict[str, str] = {}
    active: set[str] = set()
    for prior in old_events:
        prior_key = f"{prior['subject_kind']}#{prior['subject_number']}"
        last_by_subject[prior_key] = prior["event_id"]
        if prior["decision"] == "ADMIT":
            active.add(prior_key)
        else:
            active.discard(prior_key)

    decision = decision.upper()
    if decision == "REVOKE":
        _require(key in active, f"cannot REVOKE inactive subject {key}")
    if decision == "ADMIT":
        _require(key not in active, f"cannot ADMIT already-active subject {key}")

    event = make_event(
        decision=decision,
        subject_kind=subject_kind,
        subject_number=subject_number,
        objective_issue_number=objective_issue_number,
        actor=actor,
        evidence=evidence,
        recorded_at=recorded_at,
        source_policy_sha=source_policy_sha,
        supersedes_event_id=last_by_subject.get(key),
    )
    _require(
        event["event_id"] not in {row["event_id"] for row in old_events},
        f"generated duplicate event_id {event['event_id']}",
    )

    line = canonical_json(event) + "\n"
    new_text = old_text + line
    _require(new_text.startswith(old_text), "ledger prefix changed during append")

    new_events = old_events + [event]
    state = replay_events(new_events, ledger_text=new_text)
    ledger_path.write_text(new_text, encoding="utf-8")
    state_path.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"event": event, "state": state, "prior_ledger_sha256": sha256_text(old_text)}


def run_smoke_test() -> bool:
    first = make_event(
        decision="ADMIT",
        subject_kind="ISSUE",
        subject_number=1,
        objective_issue_number=1,
        actor="smoke",
        evidence=["smoke-test admission"],
        recorded_at="2026-01-01T00:00:00Z",
        source_policy_sha="a" * 40,
        supersedes_event_id=None,
    )
    text = canonical_json(first) + "\n"
    events = parse_ledger(text)
    state = replay_events(events, ledger_text=text)
    assert state["admitted_issue_numbers"] == [1]
    assert state["merge_authority"] is False
    assert state["authority_effect"] == AUTHORITY_EFFECT
    return True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", type=Path, required=True)
    verify.add_argument("--state", type=Path, required=True)

    replay = sub.add_parser("replay")
    replay.add_argument("--ledger", type=Path, required=True)
    replay.add_argument("--state", type=Path, required=True)

    append = sub.add_parser("append")
    append.add_argument("--ledger", type=Path, required=True)
    append.add_argument("--state", type=Path, required=True)
    append.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    append.add_argument("--subject-kind", choices=sorted(SUBJECT_KINDS), required=True)
    append.add_argument("--subject-number", type=int, required=True)
    append.add_argument("--objective-issue-number", type=int)
    append.add_argument("--actor", required=True)
    append.add_argument("--evidence", action="append", required=True)
    append.add_argument("--recorded-at", required=True)
    append.add_argument("--source-policy-sha", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.smoke_test:
        print("PASS" if run_smoke_test() else "FAIL")
        return 0
    if not args.command:
        print("coordinator-state=FAIL reason=command required")
        return 2
    try:
        if args.command == "verify":
            state = verify_projection(args.ledger, args.state)
            print(json.dumps({
                "verified": True,
                "ledger_sha256": state["ledger_sha256"],
                "ledger_event_count": state["ledger_event_count"],
                "admitted_issue_count": len(state["admitted_issue_numbers"]),
                "admitted_pull_request_count": len(state["admitted_pull_request_numbers"]),
                "authority_effect": state["authority_effect"],
                "merge_authority": state["merge_authority"],
            }, indent=2, sort_keys=True))
            return 0

        if args.command == "replay":
            _, _, state = load_and_replay(args.ledger)
            args.state.write_text(
                json.dumps(state, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0

        result = append_event(
            ledger_path=args.ledger,
            state_path=args.state,
            decision=args.decision,
            subject_kind=args.subject_kind,
            subject_number=args.subject_number,
            objective_issue_number=args.objective_issue_number,
            actor=args.actor,
            evidence=args.evidence,
            recorded_at=args.recorded_at,
            source_policy_sha=args.source_policy_sha,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, StateError, ValueError) as exc:
        print(f"coordinator-state=FAIL reason={exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
