#!/usr/bin/env python3
"""Render GOVERNANCE_FILES.md from .gov-control/governance-files.yaml.

The markdown registry is a VIEW. The YAML is the SSOT. Hand-editing the markdown
is how GOVERNANCE_FILES.md came to mark eight present files 🔴 MISSING and to
describe REGISTERED.md in terms the ratified REGISTRY_SPEC.md contradicts, so CI
runs `--check` and blocks when the two disagree.

The `Status` column is DERIVED — it is computed by stat-ing the declared path at
render time and never read from the YAML. That is the whole point: a file cannot
be reported missing while it sits in the tree, because nobody types the answer.

Usage:
  python3 .gov-control/render.py           # write GOVERNANCE_FILES.md
  python3 .gov-control/render.py --check   # exit 1 if out of sync (CI mode)
  python3 .gov-control/render.py --smoke-test

Deps: PyYAML. No network; writes only GOVERNANCE_FILES.md.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "governance_files_renderer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(ROOT, ".gov-control", "governance-files.yaml")
OUTPUT = os.path.join(ROOT, "GOVERNANCE_FILES.md")

PRESENT = "✅ PRESENT"
MISSING = "🔴 MISSING"


def probe(path: str, root: str = ROOT) -> str:
    """Derive presence by looking. Never read from the SSOT.

    Resolved inside `root` first: `os.path.join(root, "/etc/passwd")` discards
    `root`, and `../` walks out, so a bare exists() would report an out-of-tree
    file as PRESENT in this repository's registry. validate.py rejects such a
    path outright (rule 0); this keeps the rendered view honest even if a
    renderer somehow runs on an SSOT the validator has not passed.
    """
    if os.path.isabs(path):
        return MISSING
    full = os.path.realpath(os.path.join(root, path))
    base = os.path.realpath(root)
    if full != base and not full.startswith(base + os.sep):
        return MISSING
    return PRESENT if os.path.exists(full) else MISSING


def _esc(text: object) -> str:
    """Flatten to a single markdown table cell."""
    s = " ".join(str(text or "").split())
    return s.replace("|", "\\|")


def render(data: dict, root: str = ROOT) -> str:
    lines: list[str] = []
    add = lines.append

    add("# GOVERNANCE_FILES.md — Governance File Registry (rendered view)")
    add("")
    add("> Rendered from `.gov-control/governance-files.yaml` (SSOT) by `.gov-control/render.py`.")
    add("> **Do not hand-edit — edit the SSOT.** CI blocks when the two disagree.")
    add("")
    add("**Purpose:** A view of every governance file, its structure, authority and location.")
    add("The SSOT is `.gov-control/governance-files.yaml`; this file is derived from it and")
    add("is not authoritative. Calling a rendered view the single source of truth is how a")
    add("maintainer ends up editing the output and losing the edit on the next render.  ")
    add(f"**Updated:** {_esc(data.get('updated'))}  ")
    add(f"**Authority:** {_esc(data.get('authority'))}  ")
    add(f"**Model:** {_esc(data.get('model'))}")
    add("")
    add("**Status is derived, not declared.** Each row's status is computed by stat-ing")
    add("the declared path when this file is rendered. There is no `status` field in the")
    add("SSOT to fall out of date, and `validate.py` rejects one if it is ever added.")
    add("")
    add("---")
    add("")
    add("## File Registry")
    add("")

    for section in data.get("sections") or []:
        add(f"### {_esc(section.get('title'))}")
        add("")
        if section.get("intro"):
            add(_esc(section["intro"]))
            add("")
        add("| File | Purpose | Format | Authority | R/W | Status |")
        add("|:-----|:--------|:-------|:----------|:----|:-------|")
        for f in section.get("files") or []:
            path = f.get("path", "")
            extra = []
            if f.get("ssot"):
                extra.append(f"SSOT: `{f['ssot']}`")
            if f.get("renderer"):
                extra.append(f"via `{f['renderer']}`")
            if f.get("spec"):
                extra.append(f"spec: `{f['spec']}`")
            purpose = _esc(f.get("purpose"))
            if extra:
                purpose = f"{purpose} ({'; '.join(extra)})"
            add(
                f"| **`{_esc(path)}`** | {purpose} | {_esc(f.get('format'))} "
                f"| {_esc(f.get('authority'))} | {_esc(f.get('rw'))} | {probe(path, root)} |"
            )
        add("")

    add("---")
    add("")
    add("## File Dependencies & Boot Order")
    add("")
    add("**§A (Session Open) — read in this order:**")
    add("")
    for s in data.get("boot_order_a") or []:
        add(f"{_esc(s.get('step'))}. **`{_esc(s.get('file'))}`** — {_esc(s.get('action'))}")
    add("")
    add("**Note:** CLAUDE.md authority context is assumed established before §A starts.")
    add("Boot order takes precedence over logical authority hierarchy; resource-based")
    add("gates enforce both.")
    add("")
    add("**§B (Session Close) — write/emit in this order:**")
    add("")
    for s in data.get("boot_order_b") or []:
        add(f"{_esc(s.get('step'))}. **`{_esc(s.get('file'))}`** — {_esc(s.get('action'))}")
    add("")
    add("---")
    add("")
    add("## Authorization Model (Resource-Based)")
    add("")
    add("All Z2 writes require:")
    add("")
    for i, req in enumerate(data.get("authorization_model") or [], 1):
        add(f"{i}. {_esc(req)}")
    add("")
    add("**No time-based gates.** Only resource-capacity and regulatory compliance.")
    add("")
    add("---")
    add("")
    add("## Status Symbols")
    add("")
    add(f"- {PRESENT} — path resolves at render time")
    add(f"- {MISSING} — declared here, absent from the tree. `validate.py` treats this as an")
    add("  ERROR and blocks the merge: either the file lands, or its row leaves the SSOT.")
    add("")
    add("There is no 🟡 state. A file is in the tree or it is not, and the renderer looks")
    add("rather than asking. The old symbol set carried NEW and STRUCTURED, which are")
    add("claims about intent rather than observations, and intent is what went stale.")
    add("")

    return "\n".join(lines)


def run_smoke_test() -> int:
    import tempfile

    sample = {
        "updated": "2026-01-01",
        "authority": "Z2",
        "model": "Resource-based",
        "sections": [{
            "key": "core",
            "title": "Core",
            "intro": "intro text",
            "files": [
                {"path": "here.md", "purpose": "a|pipe\nand newline", "format": "md",
                 "authority": "Z2", "rw": "Z1 read", "spec": "SPEC.md"},
                {"path": "gone.md", "purpose": "absent", "format": "md",
                 "authority": "Z2", "rw": "Z1 read"},
            ],
        }],
        "boot_order_a": [{"step": "A.1", "file": "here.md", "action": "pin"}],
        "boot_order_b": [{"step": "B.6", "file": "here.md", "action": "walk"}],
        "authorization_model": ["receipt"],
    }
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "here.md"), "w").close()
        out = render(sample, root=td)

    # Assert on the table CELL, not the string: the status legend at the foot of
    # the document mentions both symbols unconditionally.
    assert f"| {PRESENT} |" in out, "existing file not marked present"
    assert f"| {MISSING} |" in out, "absent file not marked missing"
    assert "a\\|pipe and newline" in out, "pipe/newline not escaped"
    assert "spec: `SPEC.md`" in out, "spec pointer dropped"
    assert out.count("\n|:---") >= 1, "no table rendered"
    # The guarantee worth asserting: presence tracks the filesystem, not the YAML.
    with tempfile.TemporaryDirectory() as td:
        flipped = render(sample, root=td)
    assert f"| {PRESENT} |" not in flipped, "status did not follow the filesystem"

    # An out-of-tree path must never render as PRESENT: os.path.join discards
    # root for an absolute path, so /etc/passwd would otherwise read as present
    # in this repository.
    with tempfile.TemporaryDirectory() as td:
        for escape in ("/etc/passwd", "../../../etc/passwd"):
            assert probe(escape, root=td) == MISSING, f"{escape} probed as PRESENT"
    print("smoke-test OK — renders, escapes cells, derives status from the tree.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render GOVERNANCE_FILES.md from its SSOT")
    ap.add_argument("--check", action="store_true", help="exit 1 if GOVERNANCE_FILES.md is out of sync")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(SSOT):
        print(f"::error::missing {os.path.relpath(SSOT, ROOT)}")
        return 1

    out = render(yaml.safe_load(open(SSOT, encoding="utf-8")) or {})

    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != out:
            print("::error::GOVERNANCE_FILES.md is out of sync with "
                  ".gov-control/governance-files.yaml — run "
                  "`python3 .gov-control/render.py` and commit.")
            return 1
        print("GOVERNANCE_FILES.md: in sync with the SSOT.")
        return 0

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {os.path.relpath(OUTPUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
