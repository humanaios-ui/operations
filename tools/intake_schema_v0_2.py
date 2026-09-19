#!/usr/bin/env python3
"""
Intake Schema v0.2
Builder v1.7 compliant · validation_tool
HumanAIOS · S-051726-02

Validate intent intake rows carrying authorship, falsifier, probability,
calibration-check, and optional IC-SCOPE-05 gate fields.

Usage:
  python intake_schema_v0_2.py --input intake_template.jsonl
  python intake_schema_v0_2.py --input '{"intent_name":"Example",...}'
  python intake_schema_v0_2.py --smoke-test
  python intake_schema_v0_2.py --help
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_NAME     = "intake_schema_v0_2"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION  = "S-051726-02"
TOOL_ZONE     = 1

ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
HEX_64_RE = re.compile(r"^[0-9a-f]{64}$")
DID_RE = re.compile(r"^did:[a-z0-9]+:[A-Za-z0-9._:%-]+$")
CALIBRATION_STATUSES = {"ENDORSE", "REVISE", "SKIPPED"}


class SpecLoadFailed(Exception):
    """Raised when input cannot be loaded or parsed."""


def _load_jsonl(path: Path) -> dict[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SpecLoadFailed(f"Cannot parse JSONL row {line_no} in {path}: {exc}") from exc
        if not isinstance(row, dict):
            raise SpecLoadFailed(f"JSONL row {line_no} in {path} must be an object")
        rows.append(row)
    return {"rows": rows}


def load_input(source: str) -> dict:
    """Load input from a file path or raw JSON string."""
    path = Path(source)
    if path.exists():
        if path.suffix == ".jsonl":
            return _load_jsonl(path)
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SpecLoadFailed(f"Cannot parse {path}: {exc}") from exc
        if not isinstance(loaded, (dict, list)):
            raise SpecLoadFailed(f"{path} must contain a JSON object or array")
        return {"rows": loaded} if isinstance(loaded, list) else loaded

    try:
        loaded = json.loads(source)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Input is neither a valid path nor valid JSON: {exc}") from exc
    if not isinstance(loaded, (dict, list)):
        raise SpecLoadFailed("Input JSON must be an object or array")
    return {"rows": loaded} if isinstance(loaded, list) else loaded


def _rows_from_input(data: dict) -> list[dict[str, Any]]:
    if "rows" in data:
        rows = data["rows"]
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise SpecLoadFailed("'rows' must be a list of objects")
        return rows
    return [data]


def _is_non_trivial_text(value: Any) -> bool:
    return isinstance(value, str) and len(value.split()) >= 5


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_iso_timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(ISO_TIMESTAMP_RE.match(value))


def _validate_gate_hashes(row: dict[str, Any], errors: list[str]) -> None:
    gate_fields = ("scope_hash", "scope_sig", "criteria_hash")
    present = [field for field in gate_fields if row.get(field) is not None]
    if not present:
        return
    if len(present) != len(gate_fields):
        errors.append("scope_hash, scope_sig, and criteria_hash must be provided together")
        return
    for field in gate_fields:
        if not isinstance(row[field], str) or not HEX_64_RE.match(row[field]):
            errors.append(f"{field} must be a 64-character lowercase hex string")


def _validate_row(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not _is_non_empty_string(row.get("intent_name")):
        errors.append("intent_name must be a non-empty string")

    for field in (
        "problem",
        "proposed_outcome",
        "affected_users_and_systems",
        "constraints",
        "falsifier",
    ):
        if not _is_non_trivial_text(row.get(field)):
            errors.append(f"{field} must be a non-trivial string")

    if not isinstance(row.get("status"), str) or not row["status"].strip():
        errors.append("status must be a non-empty string")

    if not _is_iso_timestamp(row.get("submitted_at")):
        errors.append("submitted_at must be an ISO 8601 timestamp")

    open_questions = row.get("open_questions")
    if not isinstance(open_questions, list) or not all(isinstance(item, str) and item.strip() for item in open_questions):
        errors.append("open_questions must be a list of non-empty strings")

    smag_p = row.get("smag_p")
    if not isinstance(smag_p, (int, float)) or isinstance(smag_p, bool) or not 0 <= float(smag_p) <= 1:
        errors.append("smag_p must be a number in [0,1]")

    authorship = row.get("author")
    if not isinstance(authorship, dict):
        errors.append("author must be an object")
    else:
        display_name = authorship.get("name")
        originator_did = authorship.get("originator_did")
        if not isinstance(display_name, str) and not isinstance(originator_did, str):
            errors.append("author must include name or originator_did")
        if originator_did is not None and (not isinstance(originator_did, str) or not DID_RE.match(originator_did)):
            errors.append("author.originator_did must be a DID string such as did:key:...")
        if authorship.get("signature") is not None:
            if not isinstance(authorship["signature"], str) or not authorship["signature"].strip():
                errors.append("author.signature must be a non-empty string when present")
            if not isinstance(originator_did, str):
                errors.append("author.signature requires author.originator_did")
        if isinstance(display_name, str) and not display_name.strip():
            errors.append("author.name must be non-empty when present")

    calibration = row.get("calibration_check")
    if not isinstance(calibration, dict):
        errors.append("calibration_check must be an object")
    else:
        status = calibration.get("status")
        if status not in CALIBRATION_STATUSES:
            errors.append(f"calibration_check.status must be one of {sorted(CALIBRATION_STATUSES)}")
        reviewed_at = calibration.get("reviewed_at")
        if status in {"ENDORSE", "REVISE"} and not _is_iso_timestamp(reviewed_at):
            errors.append("calibration_check.reviewed_at must be present for ENDORSE/REVISE")
        if calibration.get("note") is not None and not isinstance(calibration.get("note"), str):
            errors.append("calibration_check.note must be a string when present")

    if bool(row.get("architecture_change")):
        if not isinstance(calibration, dict) or calibration.get("status") == "SKIPPED":
            errors.append("architecture_change rows require a non-skipped calibration_check")

    _validate_gate_hashes(row, errors)

    if isinstance(authorship, dict) and isinstance(authorship.get("originator_did"), str) and not authorship.get("signature"):
        warnings.append("author.originator_did is present without author.signature; authorship is not cryptographically bound")

    if isinstance(calibration, dict) and calibration.get("status") == "SKIPPED":
        warnings.append("calibration_check is skipped; intake should flag AMBIGUITY before architectural use")

    return {
        "row": row_index,
        "id": row.get("intent_name", f"row-{row_index}"),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


def run(data: dict) -> dict:
    """Validate one or more intake rows."""
    rows = _rows_from_input(data)
    items = [_validate_row(row, index) for index, row in enumerate(rows, start=1)]
    error_count = sum(len(item["errors"]) for item in items)
    warning_count = sum(len(item["warnings"]) for item in items)

    status = "FAIL" if error_count else ("WARN" if warning_count else "PASS")
    return {
        "status": status,
        "items": items,
        "warnings": [
            f"row {item['row']}: {warning}"
            for item in items
            for warning in item["warnings"]
        ],
        "summary": {
            "rows": len(items),
            "passed": sum(1 for item in items if item["status"] == "PASS"),
            "failed": sum(1 for item in items if item["status"] == "FAIL"),
            "error_count": error_count,
            "warning_count": warning_count,
        },
    }


def aggregate(run_result: dict, source: str) -> dict:
    """Assemble final output dict with standard Builder v1.7 envelope."""
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "session": TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "result": run_result.get("status", "FAIL"),
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    """Write JSON report to output_dir. Returns file path."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = path / f"{TOOL_NAME}_{stamp}.json"
    report_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(report_path)


def print_summary(output: dict) -> None:
    """Print human-readable summary to stdout."""
    bar = "=" * 60
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict : {output.get('result', 'UNKNOWN')}")
    for key, value in output.get("summary", {}).items():
        print(f" {key:<14}: {value}")
    if output.get("warnings"):
        print("\n Warnings:")
        for warning in output["warnings"]:
            print(f"   WARN  {warning}")
    if output.get("items"):
        print(f"\n Items ({len(output['items'])}):")
        for item in output["items"][:20]:
            print(f"   {item['status']:<6} row {item['row']}: {item['id']}")
            for error in item["errors"]:
                print(f"          ERROR {error}")
    print(f"{bar}\n")


def run_smoke_test() -> bool:
    """Minimal self-test."""
    try:
        valid_row = {
            "intent_name": "SSI-backed intake mitigation",
            "author": {"originator_did": "did:key:z6MkhazExampleDid", "signature": "base64-ed25519-sig"},
            "status": "draft",
            "submitted_at": "2026-09-09T00:00:00Z",
            "problem": "Current intake can restate the symptom but still miss when the originator's intent changes under pressure.",
            "proposed_outcome": "Add explicit falsifier, probability, and calibration checks so intake separates authorship from endorsement.",
            "affected_users_and_systems": "Originators, intake operators, and the intake schema consumer use the same structured fields.",
            "constraints": "Calibration must work without requiring legal identity and must stay compatible with DID-based authorship.",
            "open_questions": ["What drift threshold should trigger re-declaration?"],
            "falsifier": "If ten intakes cannot distinguish stable from drifting endorsements, the added gates are insufficient.",
            "smag_p": 0.9,
            "calibration_check": {
                "status": "ENDORSE",
                "reviewed_at": "2026-09-09T00:05:00Z",
                "note": "Re-read after scenario pressure and still endorsed.",
            },
            "architecture_change": True,
        }
        valid_result = run(valid_row)
        assert valid_result["status"] == "PASS", f"Expected PASS, got {valid_result['status']}"

        invalid_row = dict(valid_row)
        invalid_row["smag_p"] = 1.5
        invalid_row["author"] = {"signature": "sig-without-did"}
        invalid_row["calibration_check"] = {"status": "SKIPPED"}
        invalid_result = run(invalid_row)
        assert invalid_result["status"] == "FAIL", "Expected FAIL for invalid row"
        assert invalid_result["summary"]["error_count"] >= 3, "Expected multiple validation errors"

        output = aggregate(valid_result, "_smoke")
        assert output["tool"] == TOOL_NAME
        assert output["version"] == TOOL_VERSION

        try:
            load_input("/nonexistent/path/that/cannot/exist.json")
            assert False, "Should have raised SpecLoadFailed"
        except SpecLoadFailed:
            pass

        print("✓ Smoke test PASSED")
        return True
    except AssertionError as exc:
        print(f"✗ Smoke test FAILED: {exc}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Smoke test ERROR: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Intake Schema v0.2 validator")
    parser.add_argument("--input", "-i", help="Path to input file or inline JSON string")
    parser.add_argument("--output", "-o", default="outputs/", help="Directory for JSON report output")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        data = load_input(args.input)
    except SpecLoadFailed as exc:
        print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
        sys.exit(2)

    run_result = run(data)
    output = aggregate(run_result, args.input)
    report_path = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {report_path}")
    sys.exit(0 if output["result"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
