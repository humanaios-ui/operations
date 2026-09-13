#!/usr/bin/env python3
"""HumanAIOS tool-manifest scanner / refresher.

Walks the registered tool roots, extracts each tool's declared metadata, and
writes `tools-manifest.yaml` (the SSOT). Mirrors the `.doc-control` pattern:
the manifest is the single source of truth, this script keeps its MECHANICAL
fields honest, and `validate.py` gates merges on it.

Two classes of field:

  DERIVED  — re-read from the file on every scan (version, interface, smoke
             test, builder markers, declared category/zone). Never hand-edit;
             the scan overwrites them.
  CURATED  — set by a human and PRESERVED across scans (status, owner, purpose,
             zone/category when the file declares none, review_due, notes).

tool_id is allocated once per path and never reused, so a tool keeps its id
across renames of its metadata (a path change is a new tool — retire the old
entry rather than silently re-pointing an id).

Usage:
  python3 .tool-control/scan.py              # refresh tools-manifest.yaml
  python3 .tool-control/scan.py --check      # exit 1 if the manifest is stale
  python3 .tool-control/scan.py --smoke-test # self-test, no writes

Deps: PyYAML. No network, no writes outside tools-manifest.yaml.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "tool_manifest_scanner"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "infrastructure_tool"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "tools-manifest.yaml")
MCP_CONFIG = os.path.join(ROOT, ".mcp.json")
TOOLS_README = os.path.join(ROOT, "tools", "README.md")

# Roots scanned for tools. `tools/tests` (tests, not tools) and `tools/skills`
# (skills — governed by SKILL_REGISTRY.md, a separate registry) are excluded by
# EXCLUDE_DIRS below rather than by omission, so the exclusion is auditable.
SCAN_ROOTS = ["tools", "scripts", "bin"]
EXCLUDE_DIRS = {"__pycache__", "tests", "skills", "node_modules", ".git"}
SCAN_EXTS = {".py", ".js", ".sh"}

ID_PREFIX = "HAIOS-TOOL-"
MCP_ID_PREFIX = "HAIOS-MCP-"

# Curated fields survive a rescan; everything else is re-derived from the file.
CURATED_FIELDS = (
    "status",
    "owner",
    "purpose",
    "category",
    "zone",
    "review_due",
    "notes",
    "supersedes",
    "superseded_by",
    "approved_by",
    "approved_date",
    "ratified_by",
    "pending_ratification",
)

# Capture a quoted string or a bare token. Stops at `;` because several tools
# declare all their constants on one line (`TOOL_CATEGORY="x"; TOOL_ZONE=1`),
# and at `#` so a trailing comment does not become part of the value.
_CONST_RE = {
    k: re.compile(r"""(?m)(?:^|;)\s*%s\s*=\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^\s;#]+)""" % k)
    for k in ("TOOL_NAME", "TOOL_VERSION", "TOOL_CATEGORY", "TOOL_ZONE", "TOOL_SESSION")
}
# A declared category is only trusted if it looks like one. Template files
# (tool_scaffolder) carry placeholders such as `{tool_type}`; those fall back to
# the curated value rather than polluting the category vocabulary.
_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Module docstring: skip the shebang, encoding line, comments and blank lines,
# then take the first triple-quoted string. `(?s)` so the body may span lines.
_DOCSTRING_RE = re.compile(
    r"(?s)\A(?:\s*(?:#[^\n]*)?\n)*\s*[rRuUbB]{0,2}(?P<q>\"{3}|'{3})(?P<body>.*?)(?P=q)"
)
_SMOKE_RE = re.compile(r"smoke[-_ ]?test", re.I)
_BUILDER_RE = re.compile(r"Builder v1\.7 compliant", re.I)
_README_ROW_RE = re.compile(
    r"^\|\s*`([^`]+\.(?:py|js|sh))`\s*\|\s*`?([a-z_]*)`?\s*\|\s*(.*?)\s*\|\s*$", re.M
)


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------
def _literal(raw: str) -> Any:
    """Parse a constant's right-hand side; fall back to the raw string."""
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return raw.strip().strip("\"'")


def _module_docstring(src: str) -> str:
    """The module docstring, found textually rather than by parsing.

    Deliberately NOT `ast.parse` + `ast.get_docstring`. The tool corpus is
    heterogeneous and some files parse differently across interpreter versions:
    `tools/acat_sdt_analytics_v1_0.py` puts a backslash inside an f-string
    expression, which is a SyntaxError before Python 3.12 and legal from 3.12
    (PEP 701). Extracting via the parser therefore made the manifest depend on
    which interpreter ran the scan — CI (3.14) produced a different manifest
    than a 3.11 developer machine, and `--check` reported a phantom "stale".
    A regex sees the same bytes on every version.
    """
    m = _DOCSTRING_RE.match(src)
    return m.group("body") if m else ""


def _docstring_summary(src: str, path: str) -> str:
    """First meaningful line of the module docstring (or the shebang comment)."""
    if path.endswith(".py"):
        doc = _module_docstring(src)
        for line in doc.splitlines():
            line = line.strip()
            if line and not _BUILDER_RE.search(line) and not line.startswith("HumanAIOS"):
                return line
        return ""
    for line in src.splitlines()[:12]:
        line = line.strip()
        if line.startswith("#") and not line.startswith("#!"):
            stripped = line.lstrip("# ").strip()
            if stripped:
                return stripped
    return ""


def _readme_purposes() -> dict[str, tuple[str, str]]:
    """Harvest {filename: (category, purpose)} from the tools/README.md tables.

    The README is the existing human-written catalog; reusing it seeds the
    manifest with real prose instead of empty fields.
    """
    if not os.path.exists(TOOLS_README):
        return {}
    out: dict[str, tuple[str, str]] = {}
    for fname, cat, purpose in _README_ROW_RE.findall(open(TOOLS_README, encoding="utf-8").read()):
        if fname in ("File", "file"):
            continue
        out.setdefault(fname, (cat.strip(), purpose.strip()))
    return out


def extract(path: str) -> dict[str, Any]:
    """Read one tool file and return its DERIVED metadata."""
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    src = open(path, encoding="utf-8", errors="replace").read()
    consts = {}
    for key, rx in _CONST_RE.items():
        m = rx.search(src)
        if m:
            consts[key] = _literal(m.group(1))
    cat = consts.get("TOOL_CATEGORY")
    if not (isinstance(cat, str) and _CATEGORY_RE.match(cat)):
        consts.pop("TOOL_CATEGORY", None)
    if not isinstance(consts.get("TOOL_ZONE"), int) or consts.get("TOOL_ZONE") not in (1, 2, 3):
        consts.pop("TOOL_ZONE", None)

    has_main = "__main__" in src
    has_argparse = "argparse" in src or "process.argv" in src or path.endswith(".sh")
    rec: dict[str, Any] = {
        "path": rel,
        "declared_name": consts.get("TOOL_NAME"),
        "declared_version": consts.get("TOOL_VERSION"),
        "declared_category": consts.get("TOOL_CATEGORY"),
        "declared_zone": consts.get("TOOL_ZONE"),
        "session": consts.get("TOOL_SESSION"),
        "interface": "cli" if (has_argparse and has_main) else ("module" if path.endswith(".py") else "script"),
        "smoke_test": bool(_SMOKE_RE.search(src)),
        "builder_markers": bool(
            _BUILDER_RE.search(src)
            and consts.get("TOOL_NAME")
            and consts.get("TOOL_VERSION")
            and has_main
            and _SMOKE_RE.search(src)
        ),
        "lang": {".py": "python", ".js": "node", ".sh": "bash"}.get(os.path.splitext(path)[1], "other"),
        "summary": _docstring_summary(src, path),
    }
    return {k: v for k, v in rec.items() if v not in (None, "", False) or k in ("smoke_test", "builder_markers")}


def discover() -> list[str]:
    """Every scannable tool file under SCAN_ROOTS, sorted for stable output."""
    found: list[str] = []
    for root_name in SCAN_ROOTS:
        base = os.path.join(ROOT, root_name)
        if not os.path.isdir(base):
            if os.path.isfile(base):
                found.append(base)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                ext = os.path.splitext(fn)[1]
                if ext in SCAN_EXTS:
                    found.append(full)
                elif not ext and os.access(full, os.X_OK) and os.path.isfile(full):
                    found.append(full)  # extensionless executable, e.g. bin/acat-score
    return sorted(found)


def scan_mcp_servers(existing: list[dict]) -> list[dict]:
    """Register the MCP servers declared in .mcp.json.

    MCP servers are tools the agent can call, so they belong in the manifest,
    but their metadata (scope, data classification, approval) is entirely
    curated — the config file says nothing about trust.
    """
    if not os.path.exists(MCP_CONFIG):
        return existing
    cfg = json.load(open(MCP_CONFIG, encoding="utf-8"))
    servers = cfg.get("mcpServers") or {}
    by_name = {e.get("server"): e for e in existing}
    out: list[dict] = []
    next_n = max([_id_num(e.get("server_id", "")) for e in existing] or [0])
    for name in sorted(servers):
        spec = servers[name]
        entry = dict(by_name.get(name) or {})
        if not entry.get("server_id"):
            next_n += 1
            entry["server_id"] = f"{MCP_ID_PREFIX}{next_n:03d}"
        entry["server"] = name
        entry["transport"] = spec.get("type", "stdio")
        endpoint = spec.get("url") or " ".join([spec.get("command", "")] + list(spec.get("args") or []))
        entry["endpoint"] = endpoint.strip()
        entry.setdefault("status", "draft")
        entry.setdefault("zone", 1)
        entry.setdefault("data_classification", "UNCLASSIFIED — set before approval")
        entry.setdefault("scope", "unscoped — set before approval")
        entry.setdefault("notes", "")
        out.append(entry)
    # Keep registered servers that are no longer in .mcp.json, marked for review.
    for name, entry in by_name.items():
        if name and name not in servers:
            entry = dict(entry)
            entry["notes"] = (entry.get("notes") or "") + " [not present in .mcp.json — retire or restore]"
            out.append(entry)
    return sorted(out, key=lambda e: e.get("server_id", ""))


def _id_num(tool_id: str) -> int:
    m = re.search(r"(\d+)$", tool_id or "")
    return int(m.group(1)) if m else 0


# --------------------------------------------------------------------------
# manifest assembly
# --------------------------------------------------------------------------
def build(prev: dict) -> dict:
    """Merge a fresh scan into the previous manifest, preserving curated fields."""
    prev_tools = {t.get("path"): t for t in (prev.get("tools") or [])}
    excluded = {e.get("path") for e in (prev.get("excluded") or [])}
    readme = _readme_purposes()
    next_n = max([_id_num(t.get("tool_id", "")) for t in prev_tools.values()] or [0])

    tools: list[dict] = []
    for path in discover():
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel in excluded:
            continue
        derived = extract(path)
        old = prev_tools.get(rel, {})
        entry: dict[str, Any] = {}

        if old.get("tool_id"):
            entry["tool_id"] = old["tool_id"]
        else:
            next_n += 1
            entry["tool_id"] = f"{ID_PREFIX}{next_n:03d}"

        entry["name"] = derived.get("declared_name") or old.get("name") or _stem(rel)
        entry["path"] = rel
        entry["version"] = derived.get("declared_version") or "unversioned"

        # category/zone: file declaration wins, else curated value, else the
        # README catalog, else explicitly unclassified (a validator warning).
        fname = os.path.basename(rel)
        rd_cat, rd_purpose = readme.get(fname, ("", ""))
        entry["category"] = derived.get("declared_category") or old.get("category") or rd_cat or "unclassified"
        entry["zone"] = derived.get("declared_zone") or old.get("zone") or 1
        entry["status"] = old.get("status") or _default_status(rel)
        entry["interface"] = derived.get("interface", "module")
        entry["lang"] = derived.get("lang", "other")
        entry["smoke_test"] = bool(derived.get("smoke_test"))
        entry["builder_markers"] = bool(derived.get("builder_markers"))

        purpose = old.get("purpose") or rd_purpose or derived.get("summary") or ""
        if purpose:
            entry["purpose"] = purpose
        for field in CURATED_FIELDS:
            if field in entry:
                continue  # already set above (status/category/zone/purpose)
            if old.get(field):
                entry[field] = old[field]
        if derived.get("session"):
            entry["session"] = derived["session"]
        tools.append(entry)

    manifest = {
        "version": 1,
        "generated_by": f"{TOOL_NAME} v{TOOL_VERSION}",
        "id_scheme": f"{ID_PREFIX}<nnn> (tools) · {MCP_ID_PREFIX}<nnn> (MCP servers)",
        "scan_roots": SCAN_ROOTS,
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "counts": {},
        "categories": sorted({t["category"] for t in tools}),
        "tools": tools,
        "mcp_servers": scan_mcp_servers(prev.get("mcp_servers") or []),
        "excluded": prev.get("excluded") or [],
    }
    manifest["counts"] = {
        "tools": len(tools),
        "mcp_servers": len(manifest["mcp_servers"]),
        "excluded": len(manifest["excluded"]),
        "builder_markers_present": sum(1 for t in tools if t["builder_markers"]),
        "unclassified": sum(1 for t in tools if t["category"] == "unclassified"),
    }
    return manifest


def _stem(rel: str) -> str:
    return os.path.splitext(os.path.basename(rel))[0]


def _default_status(rel: str) -> str:
    """New entries land in `draft`; approval is the owner's act, never a scan's.

    Files that name themselves archived are the one safe automatic call.
    """
    name = os.path.basename(rel).upper()
    if "ARCHIVED" in name or "_DEPRECATED" in name:
        return "archived"
    return "draft"


HEADER = """\
# HumanAIOS — Tool Manifest (Single Source of Truth)
#
# Companion to document-registry.yaml (documents) and SKILL_REGISTRY.md (skills).
# Registers every executable tool in this repo plus the MCP servers the agent
# may call. TOOLS_MANIFEST.md is RENDERED from this file — edit here, not there.
#
# Mechanical fields (version, interface, smoke_test, builder_markers, lang) are
# refreshed by `.tool-control/scan.py` and must not be hand-edited.
# Curated fields (status, owner, purpose, category, zone, review_due, notes)
# are preserved across scans and are where human judgment lives.
#
# status: draft -> review -> approved | deprecated | archived
#   `approved` is the OWNER's act and is never set by a scan (no self-grant),
#   matching the document-control rule in document-registry.yaml.
"""


def write(manifest: dict) -> str:
    body = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=100)
    return HEADER + "---\n" + body


def _first_difference(old: dict, new: dict) -> str:
    """Describe the first place two manifests disagree, for an actionable error."""
    old_tools = {t.get("path"): t for t in (old.get("tools") or [])}
    new_tools = {t.get("path"): t for t in (new.get("tools") or [])}
    for path in sorted(set(new_tools) - set(old_tools)):
        return f"'{path}' is on disk but not in the manifest"
    for path in sorted(set(old_tools) - set(new_tools)):
        return f"'{path}' is in the manifest but no longer on disk"
    for path in sorted(new_tools):
        before, after = old_tools[path], new_tools[path]
        for key in sorted(set(before) | set(after)):
            if before.get(key) != after.get(key):
                return f"{path}: {key} {before.get(key)!r} -> {after.get(key)!r}"
    for key in ("counts", "categories", "mcp_servers", "excluded", "scan_roots", "excluded_dirs"):
        if old.get(key) != new.get(key):
            return f"top-level '{key}' differs: {old.get(key)!r} -> {new.get(key)!r}"
    return "metadata header differs"


def load_prev() -> dict:
    if os.path.exists(MANIFEST):
        return yaml.safe_load(open(MANIFEST, encoding="utf-8")) or {}
    return {}


# --------------------------------------------------------------------------
def run_smoke_test() -> int:
    """Self-test: extraction and id allocation behave on this file itself."""
    rec = extract(os.path.abspath(__file__))
    assert rec["declared_name"] == TOOL_NAME, rec
    assert rec["declared_version"] == TOOL_VERSION, rec
    assert rec["declared_zone"] == 1, rec
    assert rec["interface"] == "cli", rec
    assert rec["smoke_test"] is True, rec
    assert _id_num("HAIOS-TOOL-042") == 42
    # `;`-separated declarations and template placeholders are handled.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "probe.py")
        open(p, "w").write(
            '"""Probe tool — one-line summary."""\n'
            'TOOL_NAME = "probe"; TOOL_CATEGORY = "audit_tool"; TOOL_ZONE = 1\n'
            'TOOL_VERSION = "2.1.0"  # trailing comment\n'
        )
        r = extract(p)
        assert r["declared_category"] == "audit_tool", r
        assert r["declared_version"] == "2.1.0", r
        assert r["declared_zone"] == 1, r
        assert r["summary"] == "Probe tool — one-line summary.", r
        open(p, "w").write('TOOL_NAME = "t"\nTOOL_CATEGORY = "{tool_type}"\nTOOL_ZONE = "x"\n')
        r = extract(p)
        assert "declared_category" not in r, r
        assert "declared_zone" not in r, r

        # Regression: docstring extraction must not depend on the interpreter
        # version. A backslash inside an f-string expression is a SyntaxError
        # before 3.12 and legal from 3.12 (PEP 701); parsing-based extraction
        # made CI and local machines disagree. See _module_docstring.
        open(p, "w").write(
            '#!/usr/bin/env python3\n'
            '# -*- coding: utf-8 -*-\n'
            '"""Version-independent summary.\n\nmore text\n"""\n'
            'x = f"{chr(92)}"\n'
            'def broken(:\n'
        )
        r = extract(p)
        assert r["summary"] == "Version-independent summary.", r
        import ast as _ast
        try:
            _ast.parse(open(p).read())
            parses = True
        except SyntaxError:
            parses = False
        assert not parses, "probe should be unparseable, proving extraction is parser-free"
    assert _default_status("tools/x_ARCHIVED_2026-07-16.py") == "archived"
    assert _default_status("tools/x.py") == "draft"
    found = discover()
    assert found, "discover() found no tools"
    assert not any("__pycache__" in p for p in found)
    assert not any("/tools/tests/" in p.replace(os.sep, "/") for p in found)
    print(f"smoke-test OK — {len(found)} tool files discoverable, extraction sane.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan tool roots and refresh tools-manifest.yaml")
    ap.add_argument("--check", action="store_true", help="exit 1 if the manifest is stale (CI mode)")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    manifest = build(load_prev())
    out = write(manifest)

    if args.check:
        # Compare the DATA, not the bytes: the SSOT is the structure, and a
        # PyYAML or formatting difference between a developer machine and CI is
        # not staleness. `_first_difference` names what actually changed so a
        # failure is actionable instead of just "stale".
        current = load_prev()
        if current != manifest:
            print("::error::tools-manifest.yaml is stale — run `python3 .tool-control/scan.py` and commit.")
            print(f"::error::first difference: {_first_difference(current, manifest)}")
            return 1
        print(f"tool-manifest: up to date — {manifest['counts']['tools']} tools, "
              f"{manifest['counts']['mcp_servers']} MCP servers.")
        return 0

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write(out)
    c = manifest["counts"]
    print(f"wrote {os.path.relpath(MANIFEST, ROOT)} — {c['tools']} tools "
          f"({c['builder_markers_present']} with Builder v1.7 markers, "
          f"{c['unclassified']} unclassified), "
          f"{c['mcp_servers']} MCP servers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
