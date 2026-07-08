"""
HumanAIOS — Hybrid Tool Template (Builder v1.7 + FastMCP Dual-Mode)
Builder v1.7 compliant

Single Python module with two entrypoints:
  - CLI:  python tool_template.py --input fixture.json --report out.json
  - MCP:  fastmcp run tool_template.py --serve  (stdio default)

Copy this template for each Zone 1 tool. Replace TOOL_* constants and implement
run(spec: dict) -> dict with pure business logic.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Builder v1.7 compliant
# ---------------------------------------------------------------------------
TOOL_NAME = "tool_template"
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "template"
TOOL_SESSION = "zone1"


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when input spec cannot be loaded or validated."""


# ---------------------------------------------------------------------------
# Input / output helpers
# ---------------------------------------------------------------------------
def load_input(path: str | None) -> dict:
    """Load input spec from JSON file or stdin."""
    if path is None or path == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.isfile(path):
            raise SpecLoadFailed(f"Input file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    if not raw.strip():
        raise SpecLoadFailed("Empty input")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Invalid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return spec


def write_report(out: dict, path: str) -> None:
    """Write report JSON atomically."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, path)


def print_summary(out: dict) -> None:
    """Human-readable summary to stderr (safe for MCP stdio)."""
    status = out.get("status", "UNKNOWN")
    duration = out.get("duration_ms", "?")
    print(f"[{TOOL_NAME} v{TOOL_VERSION}] status={status} duration={duration}ms",
          file=sys.stderr)


# ---------------------------------------------------------------------------
# Core business logic (pure function — no side effects beyond intended ones)
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Execute tool business logic.

    Args:
        spec: Input specification dict.

    Returns:
        Result dict with at least 'status', 'started_at', 'finished_at'.
    """
    started = datetime.now(timezone.utc).isoformat()
    # --- implement tool logic here ---
    result_payload = {"echo": spec.get("message", "no message")}
    # ---------------------------------
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": "ok",
        "started_at": started,
        "finished_at": finished,
        "result": result_payload,
    }


def aggregate(results: list[dict]) -> dict:
    """Aggregate multiple run results into a single report."""
    statuses = [r.get("status") for r in results]
    ok_count = statuses.count("ok")
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "aggregate": True,
        "total": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Quick validation that run() works with a sample spec."""
    try:
        sample = {"message": "smoke test"}
        out = run(sample)
        assert out.get("status") == "ok", f"Unexpected status: {out.get('status')}"
        assert "result" in out, "Missing result field"
        print("[smoke] PASSED", file=sys.stderr)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# MCP surface
# ---------------------------------------------------------------------------
from fastmcp import FastMCP  # noqa: E402

mcp = FastMCP(TOOL_NAME)


@mcp.tool(name=TOOL_NAME, description="Template tool — echo a message.")
def tool_template(spec: dict) -> dict:
    """MCP tool wrapper around run()."""
    return run(spec)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    p.add_argument("--input", required=False, help="Path to input JSON (default: stdin)")
    p.add_argument("--smoke", action="store_true", help="Run smoke test and exit")
    p.add_argument("--serve", action="store_true", help="Run as MCP server over stdio")
    p.add_argument("--report", default=f"reports/{TOOL_NAME}.json", help="Report output path")
    args = p.parse_args()

    if args.serve:
        mcp.run()  # stdio default
        return

    if args.smoke:
        sys.exit(0 if run_smoke_test() else 1)

    spec = load_input(args.input)
    out = run(spec)
    write_report(out, args.report)
    print_summary(out)


if __name__ == "__main__":
    main()
