#!/usr/bin/env python3
"""HumanAIOS tool-manifest validator (Phase 1, errors-only).

The merge gate for `tools-manifest.yaml`, built to the same contract as
`.doc-control/validate.py`: enforce the MECHANICAL rules, leave the judgment
calls (is this tool any good? should it be Zone 2?) to human reviewers.

ERRORS (block merge):
  1. tools-manifest.yaml parses; every tool has the required fields.
  2. tool_id / server_id unique and well-formed.
  3. Every registered path exists on disk (no dead entries).
  4. Every tool file on disk is registered or explicitly excluded (COVERAGE —
     this is the rule whose absence let TOOLS_MANIFEST.md drift to 6 of 143).
  5. status in the allowed enum; `approved` requires approved_by + approved_date.
  6. Manifest version matches the file's own TOOL_VERSION (no stale manifest).
  7. Zone 2/3 tools carry a ratification reference — Z2/Z3 authority is granted
     by Night, never self-declared (CLAUDE.md, "Cannot execute without Z2 hash").
  8. Every server in .mcp.json is registered; an `approved` MCP server must have
     a real scope + data_classification, not the placeholder.

WARNINGS (advisory now, `--strict` to block; promote in a later phase):
  - category `unclassified`
  - missing Builder v1.7 markers
  - missing owner / purpose on a non-draft tool
  - review_due in the past

Exit 0 = clean, 1 = violations, 2 = harness failure.
Deps: PyYAML. No network, no writes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402  (shared discovery rules — one definition, not two)

TOOL_NAME = "tool_manifest_validator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

ROOT = scan.ROOT
MANIFEST = scan.MANIFEST
MCP_CONFIG = scan.MCP_CONFIG

TOOL_ID_RE = re.compile(r"^HAIOS-TOOL-\d{3,}$")
MCP_ID_RE = re.compile(r"^HAIOS-MCP-\d{3,}$")
STATUSES = {"draft", "review", "approved", "deprecated", "archived"}
REQUIRED = ("tool_id", "name", "path", "version", "category", "zone", "status")
PLACEHOLDER = re.compile(r"set before approval", re.I)

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def _parse_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def validate(manifest: dict) -> None:
    tools = manifest.get("tools") or []
    if not tools:
        err("tools-manifest.yaml has no `tools` — run .tool-control/scan.py")
        return

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()

    for t in tools:
        tid = t.get("tool_id", "<missing>")
        for field in REQUIRED:
            if t.get(field) in (None, ""):
                err(f"{tid}: missing required field '{field}'")

        if tid != "<missing>" and not TOOL_ID_RE.match(tid):
            err(f"{tid}: tool_id does not match HAIOS-TOOL-<nnn>")
        if tid in seen_ids:
            err(f"{tid}: duplicate tool_id")
        seen_ids.add(tid)

        path = t.get("path") or ""
        if path in seen_paths:
            err(f"{tid}: duplicate path '{path}'")
        seen_paths.add(path)

        full = os.path.join(ROOT, path)
        exists = os.path.exists(full)
        status = t.get("status")

        # 3. dead entries. An archived tool may legitimately have been deleted;
        #    anything else must still be on disk.
        if not exists and status != "archived":
            err(f"{tid}: registered path '{path}' does not exist (status={status})")

        # 5. status enum + approval gate
        if status and status not in STATUSES:
            err(f"{tid}: invalid status '{status}' (allowed: {sorted(STATUSES)})")
        if status == "approved" and not (t.get("approved_by") and t.get("approved_date")):
            err(f"{tid}: status=approved requires approved_by + approved_date")

        # 6. manifest version vs the file's own declaration
        if exists:
            declared = scan.extract(full).get("declared_version")
            if declared and t.get("version") and str(declared) != str(t["version"]):
                err(f"{tid}: manifest version {t['version']} != TOOL_VERSION {declared} "
                    f"in {path} — rerun .tool-control/scan.py")

        # 7. elevated zone needs a ratification reference. A pre-existing
        #    self-declared Zone 2/3 tool may carry `pending_ratification: true`
        #    to stay visible as an open Z2 item instead of silently passing —
        #    but it can never reach `approved` on that basis.
        zone = t.get("zone")
        if isinstance(zone, int) and zone > 1 and not t.get("ratified_by"):
            if t.get("pending_ratification") and status != "approved":
                warn(f"{tid}: zone={zone} self-declared, awaiting Z2 ratification ({path})")
            else:
                err(f"{tid}: zone={zone} requires 'ratified_by' (Z2 hash / ratification doc) "
                    f"— Zone 2/3 authority is not self-declared")
        if zone not in (1, 2, 3):
            err(f"{tid}: zone '{zone}' invalid (must be 1, 2 or 3)")

        # --- advisory ---
        if t.get("category") == "unclassified":
            warn(f"{tid}: category is 'unclassified' ({path})")
        if not t.get("builder_markers"):
            warn(f"{tid}: missing Builder v1.7 markers ({path})")
        if status not in ("draft", "archived"):
            if not t.get("owner"):
                warn(f"{tid}: status={status} without an owner")
            if not t.get("purpose"):
                warn(f"{tid}: status={status} without a purpose")
        due = _parse_date(t.get("review_due")) if t.get("review_due") else None
        if t.get("review_due") and due is None:
            err(f"{tid}: review_due '{t['review_due']}' is not an ISO date (YYYY-MM-DD)")
        elif due and due < date.today() and status != "archived":
            warn(f"{tid}: review overdue since {due.isoformat()}")


def validate_coverage(manifest: dict) -> None:
    """4. Every tool on disk is registered or explicitly excluded.

    Kept separate from validate() because it reads the real working tree —
    the per-entry rules must stay testable against synthetic manifests.
    """
    registered = {t.get("path") for t in (manifest.get("tools") or [])}
    excluded = {e.get("path") for e in (manifest.get("excluded") or [])}
    for full in scan.discover():
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        if rel not in registered and rel not in excluded:
            err(f"unregistered tool '{rel}' — add it to tools-manifest.yaml "
                f"(run .tool-control/scan.py) or list it under `excluded:`")


def validate_mcp(manifest: dict) -> None:
    """8. MCP servers: registered, unique, and scoped before approval."""
    servers = manifest.get("mcp_servers") or []
    seen: set[str] = set()
    for s in servers:
        sid = s.get("server_id", "<missing>")
        if not MCP_ID_RE.match(str(sid)):
            err(f"{sid}: server_id does not match HAIOS-MCP-<nnn>")
        if sid in seen:
            err(f"{sid}: duplicate server_id")
        seen.add(sid)
        for field in ("server", "transport", "endpoint", "status"):
            if not s.get(field):
                err(f"{sid}: missing required field '{field}'")
        if s.get("status") not in STATUSES:
            err(f"{sid}: invalid status '{s.get('status')}'")
        if s.get("status") == "approved":
            for field in ("scope", "data_classification"):
                value = str(s.get(field) or "")
                if not value or PLACEHOLDER.search(value):
                    err(f"{sid}: status=approved requires a real '{field}' "
                        f"(still the placeholder)")

    if os.path.exists(MCP_CONFIG):
        try:
            configured = set((json.load(open(MCP_CONFIG, encoding="utf-8")).get("mcpServers") or {}))
        except json.JSONDecodeError as exc:
            err(f".mcp.json does not parse: {exc}")
            return
        registered = {s.get("server") for s in servers}
        for name in sorted(configured - registered):
            err(f"MCP server '{name}' is in .mcp.json but not in tools-manifest.yaml "
                f"— run .tool-control/scan.py")


def run_smoke_test() -> int:
    """Self-test the rules against synthetic manifests (no repo state)."""
    global errors, warnings
    errors, warnings = [], []
    validate({"tools": [{
        "tool_id": "BAD-ID", "name": "x", "path": "tools/does_not_exist_xyz.py",
        "version": "1.0.0", "category": "audit_tool", "zone": 2, "status": "approved",
    }]})
    joined = " | ".join(errors)
    assert "tool_id does not match" in joined, joined
    assert "does not exist" in joined, joined
    assert "requires approved_by" in joined, joined
    assert "requires 'ratified_by'" in joined, joined

    # pending_ratification downgrades to a warning, but never for `approved`.
    base = {"tool_id": "HAIOS-TOOL-001", "name": "x", "path": ".tool-control/scan.py",
            "version": scan.TOOL_VERSION, "category": "audit_tool", "zone": 2}
    errors, warnings = [], []
    validate({"tools": [dict(base, status="draft", pending_ratification=True)]})
    assert not errors, errors
    assert any("awaiting Z2 ratification" in w for w in warnings), warnings
    errors, warnings = [], []
    validate({"tools": [dict(base, status="approved", pending_ratification=True,
                             approved_by="x", approved_date="2026-01-01")]})
    assert any("requires 'ratified_by'" in e for e in errors), errors

    errors, warnings = [], []
    validate_mcp({"mcp_servers": [{
        "server_id": "HAIOS-MCP-001", "server": "s", "transport": "http",
        "endpoint": "https://example.invalid", "status": "approved",
        "scope": "unscoped — set before approval", "data_classification": "x",
    }]})
    assert any("still the placeholder" in e for e in errors), errors

    errors, warnings = [], []
    print("smoke-test OK — id, existence, approval, zone and MCP rules all fire.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate tools-manifest.yaml")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(MANIFEST):
        print(f"::error::missing {os.path.relpath(MANIFEST, ROOT)} — run .tool-control/scan.py")
        return 1

    manifest = yaml.safe_load(open(MANIFEST, encoding="utf-8")) or {}
    validate(manifest)
    validate_coverage(manifest)
    validate_mcp(manifest)

    if args.strict:
        errors.extend(warnings)
        warnings.clear()

    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")

    n_tools = len(manifest.get("tools") or [])
    n_mcp = len(manifest.get("mcp_servers") or [])
    if errors:
        print(f"\n{len(errors)} tool-manifest violation(s), {len(warnings)} warning(s).")
        return 1
    print(f"tool-manifest: OK — {n_tools} registered tools, {n_mcp} MCP servers, "
          f"no violations ({len(warnings)} advisory warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
