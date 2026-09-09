#!/usr/bin/env python3
"""
smag_predict_lint.py
Builder v1.7 compliant - smag_predict_lint
HumanAIOS - S-090926-smag-predict-lint

Refuse a PR body that carries no pinned `smag_p:` probability and audit ledger
rows for prediction-calibration VOIDs.

Usage:
  python3 tools/smag_predict_lint.py --body-file /tmp/pr_body.md
  printf '%s' "$PR_BODY" | python3 tools/smag_predict_lint.py
  python3 tools/smag_predict_lint.py --ledger audits/smag_pilot_ledger.jsonl --enforce
  python3 tools/smag_predict_lint.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "smag_predict_lint"
TOOL_VERSION = "1.0.0"
DEFAULT_LEDGER = "audits/smag_pilot_ledger.jsonl"
SMAG_P = re.compile(r"(?im)^\s*smag_p\s*:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*$")
VOID_PREDICTION = "VOID: missing smag_p"
VOID_GAP = "VOID: missing pinned probability"


class SpecLoadFailed(Exception):
    """Raised when a PR body or ledger cannot be loaded."""


def load_input(source: str | None) -> str:
    """Load text from a file path or stdin (`-`)."""
    if source in (None, "-"):
        raw = sys.stdin.read()
    else:
        path = Path(source)
        if not path.is_file():
            raise SpecLoadFailed(f"Input file not found: {source}")
        raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise SpecLoadFailed("Empty PR body")
    return raw


def extract_smag_probability(text: str) -> str | None:
    """Return the pinned `smag_p` value from PR body text, if present."""
    match = SMAG_P.search(text or "")
    return match.group(1) if match else None


def is_pinned_prediction(value: str) -> bool:
    """Return whether a ledger `predicted` field is a single pinned probability."""
    return SMAG_P.fullmatch((value or "").strip()) is not None


def normalize_prediction(probability: str | None) -> str:
    """Normalize a pinned probability to the ledger `predicted` form."""
    return f"smag_p:{probability}" if probability is not None else VOID_PREDICTION


def lint_pr_body(text: str) -> dict:
    """Lint a PR body and report whether a pinned prediction is present."""
    probability = extract_smag_probability(text)
    if probability is None:
        return {
            "status": "VOID",
            "prediction": VOID_PREDICTION,
            "message": "Missing required `smag_p:` line in PR body.",
        }
    return {
        "status": "PASS",
        "prediction": normalize_prediction(probability),
        "probability": float(probability),
        "message": "Pinned `smag_p:` probability found.",
    }


def load_rows(path: Path) -> list[dict]:
    """Load JSONL ledger rows, skipping malformed lines."""
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows

def find_void_rows(rows: list[dict]) -> list[dict]:
    """Return ledger rows whose `predicted` field is not a pinned probability."""
    return [row for row in rows if not is_pinned_prediction(str(row.get("predicted", "")))]


def write_report(output: dict, output_dir: str) -> str:
    """Write a JSON report and return the report path."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = path / f"{TOOL_NAME}_{stamp}.json"
    report.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(report)


def run_smoke_test() -> bool:
    """Exercise body linting and ledger VOID detection."""
    try:
        ok = lint_pr_body("## What & why\nsmag_p: 0.40\n")
        assert ok["status"] == "PASS"
        assert ok["prediction"] == "smag_p:0.40"

        bad = lint_pr_body("## What & why\nNo probability here.\n")
        assert bad["status"] == "VOID"
        assert bad["prediction"] == VOID_PREDICTION

        rows = [
            {"pr": "1", "predicted": "smag_p:0.40"},
            {"pr": "2", "predicted": VOID_PREDICTION},
            {"pr": "3", "predicted": "dependabot changelog"},
            {"pr": "4", "predicted": "Outcome: landed\nsmag_p:0.40"},
        ]
        voids = find_void_rows(rows)
        assert [row["pr"] for row in voids] == ["2", "3", "4"]
        print("✓ Smoke test PASSED")
        return True
    except Exception as exc:
        print(f"✗ Smoke test FAILED: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint SMAG predictions for pinned probabilities.")
    parser.add_argument("source", nargs="?", default="-", help="PR body file path or '-' for stdin")
    parser.add_argument("--body-file", help="Explicit PR body file path")
    parser.add_argument("--ledger", help="Audit an existing SMAG ledger instead of a PR body")
    parser.add_argument("--enforce", action="store_true", help="Exit non-zero when VOID rows are found")
    parser.add_argument("--output", default="", help="Optional output directory for JSON report")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    if args.ledger:
        rows = load_rows(Path(args.ledger))
        voids = find_void_rows(rows)
        output = {
            "status": "PASS" if not voids else "VOID",
            "rows": len(rows),
            "void_rows": len(voids),
            "sample_prs": [str(row.get("pr", "?")) for row in voids[:10]],
        }
        print(f"rows={output['rows']} with_smag_p={output['rows'] - output['void_rows']} void={output['void_rows']}")
        if output["sample_prs"]:
            print(f"VOID rows (missing smag_p): {', '.join(output['sample_prs'])}")
        if args.output:
            print(f"report={write_report(output, args.output)}")
        return 2 if args.enforce and voids else 0

    try:
        body = load_input(args.body_file or args.source)
    except SpecLoadFailed as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output = lint_pr_body(body)
    if args.output:
        print(f"report={write_report(output, args.output)}")
    print(output["prediction"])
    if output["status"] != "PASS":
        print(f"::error title=Missing smag_p::{output['message']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
