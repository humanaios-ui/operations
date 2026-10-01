#!/usr/bin/env python3
"""
Control-Plane Custody Observer — v0.1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · CPC-001

Normalize replayable control-plane observations and derive custody state.

This tool is intentionally read-only and authority-neutral:
OBSERVATION != AUTHORITY
PROVENANCE != AUTHORITY
CUSTODY != AUTHORITY
BOUNDARY_ENFORCEMENT != AUTHORITY

Usage:
  python3 tools/control_plane_custody_observer_v0_1.py --input specimen.json
  python3 tools/control_plane_custody_observer_v0_1.py --input specimen.json --output receipts.json
  python3 tools/control_plane_custody_observer_v0_1.py --smoke-test
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jsonschema import Draft202012Validator, FormatChecker


TOOL_NAME = "control_plane_custody_observer"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "CPC-001"
TOOL_ZONE = 1

SCHEMA_ID = "humanaios.control-plane-custody-event.v0.1"
ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "control_plane_custody_event_v0_1.schema.json"

UNKNOWN = "UNKNOWN"
ALLOWED_ORIGIN_CLASSES = {
    "VERIFIED_HUMAN_AUTHORITY",
    "KNOWN_HUMAN",
    "KNOWN_AI",
    "KNOWN_BOT",
    "SHARED_ACCOUNT_ORIGIN_UNKNOWN",
    "EXTERNAL_ACTOR",
    "UNKNOWN",
}
ALLOWED_AUTHORITY_STATES = {"VERIFIED", "CLAIMED", "NONE", "UNKNOWN"}
ALLOWED_BOUNDARY_STATES = {"MECHANICAL", "PROCEDURAL", "ABSENT", "UNKNOWN"}
ALLOWED_OUTCOME_STATES = {"SUCCEEDED", "REFUSED", "FAILED", "OBSERVED", "UNKNOWN"}


class ObservationError(ValueError):
    """Raised when an observation cannot be normalized without overclaiming."""


def _principal(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else UNKNOWN


def _unique_strings(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def derive_custody_state(
    execution: Any,
    decision: Any,
    information: Iterable[Any],
) -> str:
    """Derive a conservative custody state from named custodians.

    Rules:
    - unknown execution/decision/information => UNKNOWN
    - execution == decision => COLLAPSED
    - any other overlap between execution/decision and information => MIXED
    - all known and role sets disjoint => SEPARATED
    """
    exe = _principal(execution)
    dec = _principal(decision)
    info = [_principal(x) for x in information]
    info_set = set(info)

    if exe == UNKNOWN or dec == UNKNOWN or not info or UNKNOWN in info_set:
        return "UNKNOWN"
    if exe == dec:
        return "COLLAPSED"
    if exe in info_set or dec in info_set:
        return "MIXED"
    return "SEPARATED"


def _require_enum(value: Any, allowed: set[str], field: str) -> str:
    text = str(value or "").strip().upper()
    if text not in allowed:
        raise ObservationError(f"{field}: invalid value {value!r}")
    return text


def normalize_observation(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Return a schema-valid observation receipt without granting authority."""
    if not isinstance(raw, dict):
        raise ObservationError("observation must be an object")

    if raw.get("authority_effect") not in (None, "NONE"):
        raise ObservationError("authority_effect must be NONE")

    event_id = str(raw.get("event_id") or "").strip()
    repository = str(raw.get("repository") or "").strip()
    action = str(raw.get("action") or "").strip()
    if not event_id or not repository or not action:
        raise ObservationError("event_id, repository, and action are required")

    obj = raw.get("object") or {}
    if not isinstance(obj, dict) or not str(obj.get("type") or "").strip() or not str(obj.get("id") or "").strip():
        raise ObservationError("object.type and object.id are required")

    outcome = raw.get("outcome") or {}
    if not isinstance(outcome, dict):
        raise ObservationError("outcome must be an object")
    outcome_state = _require_enum(outcome.get("state"), ALLOWED_OUTCOME_STATES, "outcome.state")
    outcome_summary = str(outcome.get("summary") or "").strip()
    if not outcome_summary:
        raise ObservationError("outcome.summary is required")

    origin = raw.get("actor_origin") or {}
    if not isinstance(origin, dict):
        raise ObservationError("actor_origin must be an object")
    origin_class = _require_enum(
        origin.get("origin_class"), ALLOWED_ORIGIN_CLASSES, "actor_origin.origin_class"
    )

    authority = raw.get("authority_evidence") or {}
    if not isinstance(authority, dict):
        raise ObservationError("authority_evidence must be an object")
    authority_state = _require_enum(
        authority.get("state"), ALLOWED_AUTHORITY_STATES, "authority_evidence.state"
    )

    boundary = raw.get("boundary") or {}
    if not isinstance(boundary, dict):
        raise ObservationError("boundary must be an object")
    boundary_state = _require_enum(
        boundary.get("state"), ALLOWED_BOUNDARY_STATES, "boundary.state"
    )

    custody = raw.get("custody") or {}
    if not isinstance(custody, dict):
        raise ObservationError("custody must be an object")
    execution = _principal(custody.get("execution"))
    decision = _principal(custody.get("decision"))
    information = _unique_strings(custody.get("information") or [UNKNOWN])
    if not information:
        information = [UNKNOWN]

    evidence_refs = _unique_strings(raw.get("evidence_refs") or [])
    if not evidence_refs:
        raise ObservationError("at least one evidence_ref is required")

    receipt: Dict[str, Any] = {
        "schema": SCHEMA_ID,
        "event_id": event_id,
        "observed_at": raw.get("observed_at"),
        "repository": repository,
        "object": {
            "type": str(obj.get("type")).strip(),
            "id": str(obj.get("id")).strip(),
            "url": obj.get("url"),
            "immutable_ref": obj.get("immutable_ref"),
        },
        "action": action,
        "outcome": {
            "state": outcome_state,
            "summary": outcome_summary,
            "consequence_ref": outcome.get("consequence_ref"),
        },
        "carrier_account": raw.get("carrier_account"),
        "actor_origin": {
            "origin_class": origin_class,
            "agent": origin.get("agent"),
            "evidence": _unique_strings(origin.get("evidence") or []),
        },
        "authority_evidence": {
            "state": authority_state,
            "scope": authority.get("scope"),
            "refs": _unique_strings(authority.get("refs") or []),
        },
        "boundary": {
            "state": boundary_state,
            "mechanism": boundary.get("mechanism"),
            "evidence_refs": _unique_strings(boundary.get("evidence_refs") or []),
        },
        "custody": {
            "execution": execution,
            "decision": decision,
            "information": information,
        },
        "custody_state": derive_custody_state(execution, decision, information),
        "evidence_refs": evidence_refs,
        "uncertainty": _unique_strings(raw.get("uncertainty") or []),
        "authority_effect": "NONE",
    }

    validate_receipt(receipt)
    return receipt


def validate_receipt(receipt: Dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(receipt), key=lambda e: list(e.path))
    if errors:
        joined = "; ".join(error.message for error in errors)
        raise ObservationError(f"schema validation failed: {joined}")


def load_observations(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text().strip()
    if not text:
        raise ObservationError("input is empty")
    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ObservationError("JSON input must be an array")
        return data
    rows: List[Dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ObservationError(f"line {line_number}: expected object")
        rows.append(item)
    return rows


def render(receipts: List[Dict[str, Any]]) -> str:
    return json.dumps(receipts, indent=2, sort_keys=True) + "\n"


def smoke_test() -> int:
    assert derive_custody_state("executor", "decider", ["witness"]) == "SEPARATED"
    assert derive_custody_state("same", "same", ["witness"]) == "COLLAPSED"
    assert derive_custody_state("executor", "decider", ["executor"]) == "MIXED"
    assert derive_custody_state("UNKNOWN", "decider", ["witness"]) == "UNKNOWN"

    sample = normalize_observation({
        "event_id": "smoke-1",
        "observed_at": "2026-10-01T00:00:00Z",
        "repository": "owner/repo",
        "object": {
            "type": "pull_request",
            "id": "1",
            "url": "https://github.com/owner/repo/pull/1",
            "immutable_ref": "a" * 40,
        },
        "action": "OBSERVE",
        "outcome": {"state": "OBSERVED", "summary": "smoke observation"},
        "carrier_account": "github-actions[bot]",
        "actor_origin": {
            "origin_class": "KNOWN_BOT",
            "agent": "github-actions",
            "evidence": ["bot login"],
        },
        "authority_evidence": {"state": "NONE", "scope": None, "refs": []},
        "boundary": {"state": "MECHANICAL", "mechanism": "test gate", "evidence_refs": ["run:1"]},
        "custody": {
            "execution": "github-actions",
            "decision": "workflow-policy",
            "information": ["observer"],
        },
        "evidence_refs": ["run:1"],
        "uncertainty": [],
    })
    assert sample["authority_effect"] == "NONE"
    assert sample["custody_state"] == "SEPARATED"

    try:
        normalize_observation({
            **sample,
            "schema": SCHEMA_ID,
            "authority_effect": "MERGE",
        })
        raise AssertionError("authority escalation should fail")
    except ObservationError:
        pass

    print("smoke-test OK — custody classification and authority-neutral schema hold.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return smoke_test()
    if args.input is None:
        parser.error("--input is required unless --smoke-test is used")

    receipts = [normalize_observation(item) for item in load_observations(args.input)]
    text = render(receipts)
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
