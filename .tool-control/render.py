#!/usr/bin/env python3
"""Render TOOLS_MANIFEST.md from tools-manifest.yaml.

The markdown index is a VIEW. `tools-manifest.yaml` is the SSOT. Editing the
markdown by hand is how the old TOOLS_MANIFEST.md drifted to describing 6 of
143 tools, so CI runs `--check` and blocks when the two disagree.

Usage:
  python3 .tool-control/render.py           # write TOOLS_MANIFEST.md
  python3 .tool-control/render.py --check   # exit 1 if out of sync (CI mode)
  python3 .tool-control/render.py --smoke-test

Deps: PyYAML. No network; writes only TOOLS_MANIFEST.md.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan import CATEGORIES  # noqa: E402  (one definition of the vocabulary)

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "tool_manifest_renderer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "infrastructure_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "tools-manifest.yaml")
OUTPUT = os.path.join(ROOT, "TOOLS_MANIFEST.md")

CATEGORY_TITLES = {
    "connector_tool": "Connectors",
    "security_gate_tool": "Security gates",
    "governance_tool": "Governance",
    "calibration_tool": "Calibration",
    "audit_tool": "Audit",
    "validation_tool": "Validation",
    "diagnostic_tool": "Diagnostics",
    "orchestrator_tool": "Orchestration",
    "infrastructure_tool": "Infrastructure",
    "monitoring_tool": "Monitoring",
    "analytics_tool": "Analytics",
    "research_tool": "Research",
    "pipeline_tool": "Pipelines",
    "reporting_tool": "Reporting",
    "dependency": "Dependencies (imported, not invoked)",
    "template_tool": "Templates",
    "unclassified": "Unclassified — blocks the gate",
}


def _esc(text: str) -> str:
    """Keep a cell from breaking the table."""
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _flags(tool: dict) -> str:
    out = []
    if tool.get("pending_ratification"):
        out.append("**pending-Z2**")
    if not tool.get("builder_markers"):
        out.append("no-builder-markers")
    if not tool.get("smoke_test"):
        out.append("no-smoke-test")
    if tool.get("superseded_by"):
        out.append(f"superseded-by {tool['superseded_by']}")
    return ", ".join(out) or "—"


def render(manifest: dict) -> str:
    tools = manifest.get("tools") or []
    counts = manifest.get("counts") or {}
    servers = manifest.get("mcp_servers") or []
    excluded = manifest.get("excluded") or []

    by_status: dict[str, int] = {}
    for t in tools:
        by_status[t.get("status", "?")] = by_status.get(t.get("status", "?"), 0) + 1

    lines: list[str] = []
    add = lines.append

    add("# HumanAIOS — Tool Manifest")
    add("")
    add("> Rendered from `tools-manifest.yaml` (SSOT) by `.tool-control/render.py`.")
    add("> **Do not hand-edit — edit the manifest.** CI blocks when the two disagree.")
    add("")
    add(f"**{counts.get('tools', len(tools))} registered tools** · "
        f"{counts.get('mcp_servers', len(servers))} MCP servers · "
        f"{len(excluded)} excluded · "
        f"{counts.get('builder_markers_present', 0)} carrying Builder v1.7 markers")
    add("")
    add("**Status:** `draft` = registered, not yet reviewed · `review` = under owner review · "
        "`approved` = owner-verified (human gate) · `deprecated`/`archived` = retained, not for new use.")
    add("")
    add("Approval is the owner's act and is never set by a scan — the same no-self-grant "
        "rule `document-registry.yaml` uses for documents.")
    add("")

    # --- summary ---
    add("## Summary")
    add("")
    add("| metric | value |")
    add("|---|---|")
    add(f"| Registered tools | {counts.get('tools', len(tools))} |")
    for status in ("draft", "review", "approved", "deprecated", "archived"):
        if by_status.get(status):
            add(f"| — status `{status}` | {by_status[status]} |")
    add(f"| Builder v1.7 markers present | {counts.get('builder_markers_present', 0)} |")
    add(f"| Uncategorized | {counts.get('unclassified', 0)} |")
    add(f"| MCP servers | {counts.get('mcp_servers', len(servers))} |")
    add("")

    # --- open Z2 items ---
    pending = [t for t in tools if t.get("pending_ratification")]
    if pending:
        add("## ⚠️ Open Z2 items — self-declared authority without ratification")
        add("")
        add("These tools declare Zone 2/3 (ratify / Night-executes) authority with no Z2 hash "
            "on record. Z1 cannot grant it. Each must either gain a `ratified_by` reference or "
            "have its declaration corrected to Zone 1.")
        add("")
        add("| tool_id | path | zone | note |")
        add("|---|---|---|---|")
        for t in sorted(pending, key=lambda x: x["tool_id"]):
            add(f"| {t['tool_id']} | `{_esc(t['path'])}` | {t.get('zone')} | {_esc(t.get('notes', ''))} |")
        add("")

    # --- tools by category ---
    groups: dict[str, list[dict]] = {}
    for t in tools:
        groups.setdefault(t.get("category", "unclassified"), []).append(t)

    def group_key(name: str) -> tuple[int, str]:
        # unclassified last — it is the work queue, not the catalog.
        return (1 if name == "unclassified" else 0, name)

    for category in sorted(groups, key=group_key):
        entries = sorted(groups[category], key=lambda x: x["tool_id"])
        title = CATEGORY_TITLES.get(category, category.replace("_", " ").title())
        add(f"## {title} — `{category}` ({len(entries)})")
        add("")
        add("| tool_id | tool | path | ver | zone | status | flags | purpose |")
        add("|---|---|---|---|---|---|---|---|")
        for t in entries:
            add("| {id} | {name} | `{path}` | {ver} | {zone} | {status} | {flags} | {purpose} |".format(
                id=t["tool_id"],
                name=_esc(t.get("name", "")),
                path=_esc(t.get("path", "")),
                ver=_esc(str(t.get("version", ""))),
                zone=t.get("zone", ""),
                status=t.get("status", ""),
                flags=_flags(t),
                purpose=_esc(t.get("purpose", "—")) or "—",
            ))
        add("")

    # --- MCP servers ---
    add(f"## MCP servers ({len(servers)})")
    add("")
    add("External tool surfaces the agent may call. Registered here because an MCP server is a "
        "tool with a network boundary: `scope` and `data_classification` must be set by an owner "
        "before a server can reach `approved`.")
    add("")
    add("| server_id | server | transport | endpoint | zone | status | scope | data classification |")
    add("|---|---|---|---|---|---|---|---|")
    for s in servers:
        add("| {id} | {srv} | {tr} | `{ep}` | {zone} | {status} | {scope} | {dc} |".format(
            id=s.get("server_id", ""),
            srv=_esc(s.get("server", "")),
            tr=_esc(s.get("transport", "")),
            ep=_esc(s.get("endpoint", "")),
            zone=s.get("zone", ""),
            status=s.get("status", ""),
            scope=_esc(s.get("scope", "")),
            dc=_esc(s.get("data_classification", "")),
        ))
    add("")

    if excluded:
        add(f"## Excluded from tool-control ({len(excluded)})")
        add("")
        add("| path | reason |")
        add("|---|---|")
        for e in excluded:
            add(f"| `{_esc(e.get('path', ''))}` | {_esc(e.get('reason', ''))} |")
        add("")

    add("---")
    add("")
    add("**Scan roots:** " + ", ".join(f"`{r}`" for r in manifest.get("scan_roots", [])) +
        " · **excluded dirs:** " + ", ".join(f"`{d}`" for d in manifest.get("excluded_dirs", [])) +
        " (`tools/skills/` is governed by `SKILL_REGISTRY.md`). Also not tools, mirroring "
        "`_skip_reason` in `tools/builder_compliance_scanner_v1.0.py`: `test_*`/`*_test` modules, "
        "`__init__.py`, and `_`-prefixed private/shared helper directories. Archived tools stay "
        "registered at `status: archived`.")
    add("")
    add("## Category vocabulary")
    add("")
    add("A category says what a tool **does to the system**, not what subject it concerns — "
        "\"ACAT\" is a subject, `audit_tool` is a role. The set is closed: an entry outside it, "
        "or left `unclassified`, fails the gate. Extending it is a reviewed change to "
        "`CATEGORIES` in `.tool-control/scan.py`.")
    add("")
    add("| category | meaning | count |")
    add("|---|---|---|")
    for name, meaning in sorted(CATEGORIES.items()):
        if name == "unclassified":
            continue
        add(f"| `{name}` | {_esc(meaning)} | {len(groups.get(name, []))} |")
    add("")
    add("**Builder v1.7 markers** is a cheap presence heuristic (header, `TOOL_NAME`, "
        "`TOOL_VERSION`, main guard, smoke test) computed over every registered tool, including "
        "the `.js`/`.sh` and `scripts/`/`bin/` files. It is **not** the compliance verdict: the "
        "authoritative check is `tools/builder_compliance_scanner_v1.0.py`, gated by "
        "`.github/workflows/builder-lint.yml` over its own corpus (`tools/**`, excluding tests, "
        "archived and private modules). Where the two differ, the scanner is right.")
    add("")
    add("**Adding a tool:** write it to the Builder v1.7 standard (`TOOLS_TEMPLATE.md`), run "
        "`python3 .tool-control/scan.py` to register it, then set its curated fields "
        "(owner, purpose, category) in `tools-manifest.yaml`. CI blocks an unregistered tool.")
    add("")
    return "\n".join(lines)


def run_smoke_test() -> int:
    sample = {
        "counts": {"tools": 1, "mcp_servers": 1, "builder_markers_present": 0, "unclassified": 1},
        "scan_roots": ["tools"],
        "excluded_dirs": ["tests"],
        "tools": [{
            "tool_id": "HAIOS-TOOL-001", "name": "t", "path": "tools/t.py", "version": "1.0.0",
            "category": "unclassified", "zone": 2, "status": "draft",
            "pending_ratification": True, "notes": "needs Z2", "purpose": "a|pipe\nand newline",
        }],
        "mcp_servers": [{"server_id": "HAIOS-MCP-001", "server": "s", "transport": "http",
                         "endpoint": "https://example.invalid", "zone": 1, "status": "draft",
                         "scope": "x", "data_classification": "y"}],
        "excluded": [],
    }
    out = render(sample)
    assert "Open Z2 items" in out, out
    assert "HAIOS-TOOL-001" in out
    assert "a\\|pipe and newline" in out, "pipe/newline not escaped"
    assert out.count("\n|---") >= 3
    print("smoke-test OK — renders, escapes cells, surfaces open Z2 items.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render TOOLS_MANIFEST.md from tools-manifest.yaml")
    ap.add_argument("--check", action="store_true", help="exit 1 if TOOLS_MANIFEST.md is out of sync")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(MANIFEST):
        print(f"::error::missing {os.path.relpath(MANIFEST, ROOT)} — run .tool-control/scan.py")
        return 1

    out = render(yaml.safe_load(open(MANIFEST, encoding="utf-8")) or {})

    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != out:
            print("::error::TOOLS_MANIFEST.md is out of sync with tools-manifest.yaml — "
                  "run `python3 .tool-control/render.py` and commit.")
            return 1
        print("TOOLS_MANIFEST.md: in sync with the manifest.")
        return 0

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {os.path.relpath(OUTPUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
