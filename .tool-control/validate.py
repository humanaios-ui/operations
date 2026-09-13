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
  7. Zone 2/3 tools carry a ratification reference, AND that reference resolves
     to a committed ruling naming both the hash and the tool — Z2/Z3 authority is
     granted by Night, never self-declared (CLAUDE.md, "Cannot execute without Z2
     hash"). Presence alone is not a signature: Z1 writes the manifest.
  8. Every server in .mcp.json is registered; an `approved` MCP server must have
     a real scope + data_classification, not the placeholder.
  9. Every category is drawn from the controlled vocabulary, and none is
     `unclassified` — the backlog was worked to zero, so the gate ratchets.

WARNINGS (advisory now, `--strict` to block; promote in a later phase):
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
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

ROOT = scan.ROOT
MANIFEST = scan.MANIFEST
MCP_CONFIG = scan.MCP_CONFIG

TOOL_ID_RE = re.compile(r"^HAIOS-TOOL-\d{3,}$")
MCP_ID_RE = re.compile(r"^HAIOS-MCP-\d{3,}$")
STATUSES = {"draft", "review", "approved", "deprecated", "archived"}
REQUIRED = ("tool_id", "name", "path", "version", "category", "zone", "status")

# A value that only looks filled in. Both the explanatory phrase AND the bare
# placeholder tokens must be rejected, or an approval can be obtained by
# deleting the suffix and leaving "unscoped" / "UNCLASSIFIED" behind.
PLACEHOLDER = re.compile(r"set before approval", re.I)
PLACEHOLDER_VALUES = {"", "-", "none", "n/a", "tbd", "unset", "unknown",
                      "unscoped", "unclassified"}

# Zone 2/3 claims that are RECORDED as open Z2 items rather than enforced as
# ratified. This lives in CODEOWNER-protected CODE, not in the manifest: if the
# exemption were a manifest field alone, any new Zone 2/3 tool could grant
# itself the warning path, which is the exact self-grant this gate exists to
# prevent. Adding a path here is a reviewed change to the gate itself, and it
# never carries a tool to `approved`.
#
#   tools/message_calibration_v1_0.py — predates this control system; still open.
#
# `.z1-control/ratify.py` was here until 2026-09-13, when Night ratified its
# Zone 2 declaration (z1-inbox/2026-09-13/Z2_RULING_ZONE2_RATIFY_TOOL.md). It
# now carries a real `ratified_by` and needs no exemption — which is the whole
# point of the list: entries leave it by being decided, not by being forgotten.
#
# Deliberately NOT named "legacy": an entry arrived here the day it was added.
UNRATIFIED_ZONE_CLAIMS = frozenset({
    "tools/message_calibration_v1_0.py",
})

# Where a ratification ruling has to live to count. Rulings are committed
# markdown under z1-inbox/, which `*.md` in CODEOWNERS puts behind review.
RULING_ROOT = "z1-inbox/"

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def repo_file(path: str) -> tuple[str, str]:
    """Resolve a registry path inside the repo. Returns (abspath, problem).

    A registry is hand-edited YAML, so a path in it is untrusted input to this
    gate. Without containment an entry like `/etc/passwd` or `../../something`
    resolves to a real file and satisfies the existence rule while naming
    nothing in this checkout; a directory would pass too. Both would let the
    structural gate bless an entry that is not a tool here.
    """
    if not path or os.path.isabs(path) or "\\" in path:
        return "", "must be a relative path inside the repository"
    full = os.path.realpath(os.path.join(ROOT, path))
    root = os.path.realpath(ROOT)
    if full != root and not full.startswith(root + os.sep):
        return full, "resolves outside the repository"
    if os.path.isdir(full):
        return full, "is a directory, not a file"
    return full, ""


def _placeholder(value) -> bool:
    """True if a field is blank, a placeholder token, or still says 'set before…'."""
    text = str(value or "").strip()
    return (not text) or text.lower() in PLACEHOLDER_VALUES or bool(PLACEHOLDER.search(text))


def _parse_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def verify_ratification(tid: str, path: str, hash_value: str, ruling) -> None:
    """Rule 7, second half: `ratified_by` has to be checkable, not merely present.

    The first half refuses a self-declared Zone 2/3 tool that carries no `ratified_by`.
    But Z1 writes the manifest, so a field satisfied by *any* non-empty string
    re-creates the same self-grant one line later: type a slug, pass the gate.
    Presence is not a signature.

    This is not cryptography — the repo has no key for Z2. It is the weaker but
    real property that the claim resolves: the hash must name a committed ruling
    under `z1-inbox/`, and that ruling must contain both the hash and the tool's
    path. A reviewer can then read the decision the field asserts, and inventing
    a `ratified_by` now costs a CODEOWNER-reviewed document that says the thing.

    (`.z1-control/ratify.py` signs candidate blocks with a real sha256. Tool-zone
    rulings have no equivalent yet — see Q-TOOLCONTROL-03. When they do, this is
    where the recomputation belongs.)

    Added after review found that the first half, alone, could be satisfied by
    any string Z1 typed — the same self-grant one field over.
    """
    if not ruling:
        err(f"{tid}: 'ratified_by' is set but 'ratification_ruling' is missing — a "
            f"ratification hash must point at the document that records the decision, "
            f"or it is a value Z1 typed for itself")
        return

    ruling = str(ruling)
    full, problem = repo_file(ruling)
    if problem or not os.path.isfile(full):
        err(f"{tid}: ratification_ruling '{ruling}' {problem or 'does not exist'} — the "
            f"ratification cannot be read, so it does not count")
        return
    if not ruling.startswith(RULING_ROOT):
        err(f"{tid}: ratification_ruling '{ruling}' is outside '{RULING_ROOT}' — rulings "
            f"live where Z2 records them, not anywhere a file can be written")
        return

    with open(full, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if hash_value not in text:
        err(f"{tid}: ratification_ruling '{ruling}' does not contain the hash "
            f"'{hash_value}' — the manifest and the ruling disagree")
    if path not in text:
        err(f"{tid}: ratification_ruling '{ruling}' does not name '{path}' — a ruling "
            f"about some other tool does not ratify this one")


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

        full, problem = repo_file(path)
        status = t.get("status")
        if problem:
            err(f"{tid}: path '{path}' {problem}")
            exists = False
        else:
            exists = os.path.isfile(full)

        # 3. dead entries. An archived tool may legitimately have been deleted;
        #    anything else must still be on disk.
        if not exists and not problem and status != "archived":
            hint = " (flagged missing_from_tree — retire it explicitly by setting " \
                   "status: archived, or remove the entry)" if t.get("missing_from_tree") else ""
            err(f"{tid}: registered path '{path}' does not exist (status={status}){hint}")

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
            recorded_open = path in UNRATIFIED_ZONE_CLAIMS
            if t.get("pending_ratification") and recorded_open and status != "approved":
                warn(f"{tid}: zone={zone} self-declared, awaiting Z2 ratification ({path})")
            elif t.get("pending_ratification") and not recorded_open:
                err(f"{tid}: zone={zone} sets 'pending_ratification' but '{path}' is not a "
                    f"recorded open Z2 claim — a tool cannot grant itself the Z2 waiver; "
                    f"record a 'ratified_by' or declare zone 1")
            else:
                err(f"{tid}: zone={zone} requires 'ratified_by' (Z2 hash / ratification doc) "
                    f"— Zone 2/3 authority is not self-declared")
        elif isinstance(zone, int) and zone > 1:
            # …and if it IS set, it has to resolve — see verify_ratification.
            verify_ratification(tid, path, str(t["ratified_by"]), t.get("ratification_ruling"))
        if zone not in (1, 2, 3):
            err(f"{tid}: zone '{zone}' invalid (must be 1, 2 or 3)")

        # 9. category is drawn from the controlled vocabulary. Blocking, not
        #    advisory: the backlog was worked to zero, so the only way an
        #    `unclassified` entry appears now is a tool added without one.
        #    A gate that ratchets is the point — it cannot silently refill.
        category = t.get("category")
        if category == "unclassified":
            err(f"{tid}: category is 'unclassified' ({path}) — assign one of "
                f"{sorted(c for c in scan.CATEGORIES if c != 'unclassified')}")
        elif not isinstance(category, str):
            # Falsy-but-present values (0, False, []) slip past the required-field
            # check, which only rejects None and "", and would reach the renderer.
            err(f"{tid}: category must be a string, got {category!r} ({path})")
        elif category not in scan.CATEGORIES:
            err(f"{tid}: category '{category}' is not in the controlled vocabulary "
                f"({path}) — use an existing category, or extend CATEGORIES in "
                f".tool-control/scan.py as a reviewed change")

        # --- advisory ---
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
            # Same approval contract as tools and documents — an approval must
            # be attributable, or it is indistinguishable from a self-grant.
            if not (s.get("approved_by") and s.get("approved_date")):
                err(f"{sid}: status=approved requires approved_by + approved_date")
            for field in ("scope", "data_classification"):
                if _placeholder(s.get(field)):
                    err(f"{sid}: status=approved requires a real '{field}' "
                        f"(got {s.get(field)!r})")


def validate_mcp_config(manifest: dict) -> None:
    """Every server in .mcp.json is registered.

    Separate from validate_mcp() for the same reason validate_coverage() is
    separate: it reads the real working tree, and the per-entry rules must stay
    testable against synthetic manifests.
    """
    if not os.path.exists(MCP_CONFIG):
        return
    try:
        configured = set((json.load(open(MCP_CONFIG, encoding="utf-8")).get("mcpServers") or {}))
    except json.JSONDecodeError as exc:
        err(f".mcp.json does not parse: {exc}")
        return
    registered = {s.get("server") for s in (manifest.get("mcp_servers") or [])}
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

    # pending_ratification records an open Z2 claim; it is not a self-service waiver.
    legacy = sorted(UNRATIFIED_ZONE_CLAIMS)[0]
    # Read the real declared version so rule 6 (manifest vs file) is satisfied
    # and the assertions below isolate the rule each one is actually testing.
    legacy_version = scan.extract(os.path.join(ROOT, legacy)).get("declared_version")
    base = {"tool_id": "HAIOS-TOOL-001", "name": "x", "path": legacy,
            "version": legacy_version, "category": "audit_tool", "zone": 2}
    errors, warnings = [], []
    validate({"tools": [dict(base, status="draft", pending_ratification=True)]})
    assert not errors, errors
    assert any("awaiting Z2 ratification" in w for w in warnings), warnings
    # …and it never survives to `approved`, even on the grandfathered path.
    errors, warnings = [], []
    validate({"tools": [dict(base, status="approved", pending_ratification=True,
                             approved_by="x", approved_date="2026-01-01")]})
    assert any("requires 'ratified_by'" in e for e in errors), errors
    # A NEW Zone 2 tool cannot set the flag to buy itself the warning path.
    errors, warnings = [], []
    validate({"tools": [dict(base, path="tools/brand_new_zone2.py", status="draft",
                             pending_ratification=True)]})
    assert any("cannot grant itself" in e for e in errors), errors

    # Categories are a closed vocabulary, and the backlog stays at zero.
    for cat, expect in (("unclassified", "category is 'unclassified'"),
                        ("made_up_thing", "not in the controlled vocabulary")):
        errors, warnings = [], []
        validate({"tools": [dict(base, path=legacy, zone=1, status="draft",
                                 category=cat)]})
        assert any(expect in e for e in errors), (cat, errors)

    # A path outside the repo, or a directory, is never a valid tool entry.
    for bad, expect in (("/etc/passwd", "relative path"),
                        ("../outside.py", "outside the repository"),
                        ("tools", "is a directory")):
        errors, warnings = [], []
        validate({"tools": [dict(base, path=bad, zone=1, status="draft")]})
        assert any(expect in e for e in errors), (bad, errors)

    # An approved MCP server needs attribution AND real scope/classification —
    # stripping the "set before approval" suffix must not buy an approval.
    mcp = {"server_id": "HAIOS-MCP-001", "server": "s", "transport": "http",
           "endpoint": "https://example.invalid", "status": "approved"}
    errors, warnings = [], []
    validate_mcp({"mcp_servers": [dict(mcp, scope="unscoped — set before approval",
                                       data_classification="UNCLASSIFIED")]})
    joined = " | ".join(errors)
    assert "requires a real 'scope'" in joined, joined
    assert "requires a real 'data_classification'" in joined, joined
    assert "requires approved_by" in joined, joined
    errors, warnings = [], []
    validate_mcp({"mcp_servers": [dict(mcp, scope="read-only corpus tables",
                                       data_classification="internal",
                                       approved_by="carly", approved_date="2026-09-13")]})
    assert not errors, errors

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
    validate_mcp_config(manifest)

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
