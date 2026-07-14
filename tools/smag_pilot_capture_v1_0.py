#!/usr/bin/env python3
"""
smag_pilot_capture_v1_0.py
Builder v1.7 compliant
HumanAIOS

SMAG pilot ledger capture tool (issue #98).

Records predicted-vs-measured calibration rows for the SMAG pilot study.
Each row captures:
  pr          — PR number or label
  task        — Short task description
  substrate   — Agent that did the work (e.g. "Claude Code", "Copilot")
  predicted   — Acceptance criteria / expected outcome (stated before work)
  measured    — Actual outcome (gate results, merge outcome, etc.)
  gap         — Divergence type (e.g. "count-exact", "over-claimed", "under-scope")
  session     — Session ID (optional, e.g. "S-070826")

Output: JSONL rows appended to outputs/smag_pilot_ledger.jsonl
        Markdown table render: python smag_pilot_capture_v1_0.py --render

Usage:
  # Append a row from JSON:
  python smag_pilot_capture_v1_0.py --input row.json
  python smag_pilot_capture_v1_0.py --pr 98 --task "behavioral gate" \\
      --substrate Copilot \\
      --predicted "gate blocks dead-code + docstring-only; CI blocks new violations" \\
      --measured "gate delivered; 28 pre-existing violations grandfathered" \\
      --gap "pre-existing corpus noise not counted as gap"

  # Render the ledger as a Markdown table:
  python smag_pilot_capture_v1_0.py --render

  # Smoke test:
  python smag_pilot_capture_v1_0.py --smoke-test
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "smag_pilot_capture"
TOOL_VERSION = "1.0.0"

# Default ledger path (relative to repo root, resolved at runtime).
# Placed in audits/ (tracked) not outputs/ (gitignored) because the SMAG
# pilot ledger is durable research data, not a run-time report artifact.
_DEFAULT_LEDGER = Path(__file__).resolve().parents[1] / "audits" / "smag_pilot_ledger.jsonl"

REQUIRED_FIELDS = {"pr", "task", "substrate", "predicted", "measured"}
ALL_FIELDS = list(REQUIRED_FIELDS) + ["gap", "session", "timestamp"]


class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def build_row(spec: dict) -> dict:
    """
    Validate and normalise a raw spec dict into a ledger row.

    Required keys: pr, task, substrate, predicted, measured.
    Optional keys: gap (default ''), session (default '').
    Always adds: timestamp (UTC ISO-8601).
    """
    missing = REQUIRED_FIELDS - set(spec.keys())
    if missing:
        raise SpecLoadFailed(f"Missing required fields: {sorted(missing)}")

    return {
        "pr": str(spec["pr"]).strip(),
        "task": str(spec["task"]).strip(),
        "substrate": str(spec["substrate"]).strip(),
        "predicted": str(spec["predicted"]).strip(),
        "measured": str(spec["measured"]).strip(),
        "gap": str(spec.get("gap", "")).strip(),
        "session": str(spec.get("session", "")).strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def append_row(row: dict, ledger_path: Path) -> None:
    """Append a single JSON row to the JSONL ledger file."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_ledger(ledger_path: Path) -> list[dict]:
    """Load all rows from the JSONL ledger file. Returns [] if absent."""
    if not ledger_path.exists():
        return []
    rows = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # skip malformed lines
    return rows


def render_markdown(rows: list[dict]) -> str:
    """Render ledger rows as a Markdown table (matching TRACKING_BOARD format)."""
    if not rows:
        return "_No SMAG pilot rows recorded yet._\n"
    lines = [
        "| # | PR | Task | Substrate | Predicted | Measured | Gap | Session |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, row in enumerate(rows, start=1):
        def col(k: str) -> str:
            v = str(row.get(k, "")).replace("|", "&#124;")
            return v[:80] + ("…" if len(v) > 80 else "")

        lines.append(
            f"| {i} | {col('pr')} | {col('task')} | {col('substrate')} "
            f"| {col('predicted')} | {col('measured')} | {col('gap')} | {col('session')} |"
        )
    return "\n".join(lines) + "\n"


def load_input(source: str | None) -> dict:
    """Load a spec dict from a JSON file path or stdin."""
    if source is None or source == "-":
        raw = sys.stdin.read()
    else:
        p = Path(source)
        if not p.is_file():
            raise SpecLoadFailed(f"Input file not found: {source}")
        raw = p.read_text(encoding="utf-8")
    if not raw.strip():
        raise SpecLoadFailed("Empty input")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Invalid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return spec


def write_report(output: dict, output_dir: str, filename: str | None = None) -> str:
    """Write a JSON report and return the path."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = filename or f"smag_pilot_{ts}.json"
    path = p / fname
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    """Human-readable summary."""
    print(f"[{TOOL_NAME} v{TOOL_VERSION}] status={output.get('status')} "
          f"row_count={output.get('row_count', '?')}")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    """Minimal compliance smoke test — roundtrip a row through build/append/load/render."""
    import tempfile

    sample_spec = {
        "pr": "smoke-1",
        "task": "smoke test task",
        "substrate": "TestAgent",
        "predicted": "smoke passes",
        "measured": "smoke passed",
        "gap": "none",
        "session": "S-SMOKE",
    }

    try:
        row = build_row(sample_spec)
        assert row["pr"] == "smoke-1", "pr mismatch"
        assert "timestamp" in row, "timestamp missing"

        with tempfile.TemporaryDirectory() as d:
            lp = Path(d) / "test_ledger.jsonl"
            append_row(row, lp)
            rows = load_ledger(lp)
            assert len(rows) == 1, f"expected 1 row, got {len(rows)}"
            assert rows[0]["task"] == "smoke test task", "task mismatch"

            md = render_markdown(rows)
            assert "smoke test task" in md, "markdown missing task"
            assert "| 1 |" in md, "markdown missing row number"

        # Test missing-field validation
        try:
            build_row({"pr": "x"})
            print("  FAILED: expected SpecLoadFailed for missing fields", file=sys.stderr)
            return False
        except SpecLoadFailed:
            pass

        print("✓ Smoke test PASSED", file=sys.stderr)
        return True
    except Exception as exc:
        print(f"✗ Smoke test FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"SMAG Pilot Capture v{TOOL_VERSION} — record predicted-vs-measured rows"
    )
    parser.add_argument("--input", "-i", help="Path to JSON spec file (or '-' for stdin)")
    parser.add_argument("--pr", help="PR number or label")
    parser.add_argument("--task", help="Short task description")
    parser.add_argument("--substrate", help="Agent/substrate (e.g. 'Copilot', 'Claude Code')")
    parser.add_argument("--predicted", help="Predicted outcome (acceptance criteria)")
    parser.add_argument("--measured", help="Measured outcome (gate/merge result)")
    parser.add_argument("--gap", default="", help="Gap type / divergence note")
    parser.add_argument("--session", default="", help="Session ID (e.g. S-070826)")
    parser.add_argument(
        "--ledger",
        default=str(_DEFAULT_LEDGER),
        help=f"Path to JSONL ledger file (default: {_DEFAULT_LEDGER})",
    )
    parser.add_argument("--render", action="store_true", help="Print ledger as Markdown table")
    parser.add_argument("--output", "-o", default="outputs/", help="Report output directory")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    ledger_path = Path(args.ledger)

    if args.render:
        rows = load_ledger(ledger_path)
        print(render_markdown(rows))
        sys.exit(0)

    # Build spec from --input file or from individual flags
    if args.input:
        try:
            spec = load_input(args.input)
        except SpecLoadFailed as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        inline_keys = ("pr", "task", "substrate", "predicted", "measured", "gap", "session")
        spec = {k: getattr(args, k) for k in inline_keys if getattr(args, k) is not None}

    if not spec:
        parser.print_help()
        sys.exit(1)

    try:
        row = build_row(spec)
    except SpecLoadFailed as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    append_row(row, ledger_path)
    print(f"Appended row to {ledger_path}", file=sys.stderr)

    output = {
        "status": "ok",
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": row["timestamp"],
        "row_count": len(load_ledger(ledger_path)),
        "row": row,
    }
    rp = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")


if __name__ == "__main__":
    main()
