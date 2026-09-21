#!/usr/bin/env python3
"""Integrity gate for the governance-file registry.

Rendering keeps GOVERNANCE_FILES.md honest about what the SSOT says. This file
keeps the SSOT honest about the tree. Without it, `render.py` would faithfully
publish a registry whose every row is wrong — it would just be wrong in sync.

Rules (all ERROR — each blocks the merge):

  1. Declared path exists. A row for a file that is not there is the original
     defect inverted: the registry claiming a file that never landed.
  2. No `status` key anywhere in the SSOT. Status is derived by stat-ing the
     path; a hand-set one is the drift vector this control plane removes, so it
     is rejected at the source rather than ignored at render time.
  3. Declared `spec:`, `ssot:` and `renderer:` targets exist. A pointer to a
     missing spec is how a definition conflict starts.
  4. Every boot-order step names a path the registry declares. A ritual step
     pointing at an undeclared file is a gap in the boot chain.
  5. No duplicate paths across sections — one row per file, one owner.
  6. Required fields present on every row.

Usage:
  python3 .gov-control/validate.py
  python3 .gov-control/validate.py --smoke-test

Deps: PyYAML. No network; read-only.
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

TOOL_NAME = "governance_files_validator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(ROOT, ".gov-control", "governance-files.yaml")

REQUIRED = ("path", "purpose", "format", "authority", "rw")


def resolve_in_tree(path: str, root: str) -> str | None:
    """Return the absolute path if it is inside `root`, else None.

    `os.path.join(root, "/etc/passwd")` discards `root` and returns
    `/etc/passwd`, and `../` walks out of the tree, so a bare
    `os.path.exists(os.path.join(root, path))` will happily confirm that a
    declared path "exists" while pointing outside the repository — satisfying
    rule 1 without the file being in the tree at all. Presence is only
    meaningful relative to this repository, so a path that leaves it is a
    registry error rather than a missing file.
    """
    if os.path.isabs(path) or (os.name == "nt" and os.path.splitdrive(path)[0]):
        return None
    full = os.path.realpath(os.path.join(root, path))
    base = os.path.realpath(root)
    if full != base and not full.startswith(base + os.sep):
        return None
    return full


def _find_status_keys(node: object, trail: str = "") -> list[str]:
    """Rule 2 is only worth having if it cannot be evaded by nesting."""
    hits: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            here = f"{trail}.{k}" if trail else str(k)
            if str(k).lower() == "status":
                hits.append(here)
            hits.extend(_find_status_keys(v, here))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits.extend(_find_status_keys(v, f"{trail}[{i}]"))
    return hits


def validate(data: dict, root: str = ROOT) -> list[str]:
    errors: list[str] = []
    declared: set[str] = set()

    for trail in _find_status_keys(data):
        errors.append(
            f"rule 2 — `status` key at {trail}: status is derived by looking at the "
            f"tree, never declared. Remove it; render.py computes presence."
        )

    for section in data.get("sections") or []:
        skey = section.get("key", "?")
        for f in section.get("files") or []:
            path = f.get("path")
            if not path:
                errors.append(f"rule 6 — row in section '{skey}' has no `path`")
                continue

            for field in REQUIRED:
                if not f.get(field):
                    errors.append(f"rule 6 — `{path}` is missing required field `{field}`")

            if path in declared:
                errors.append(f"rule 5 — `{path}` declared more than once; one row per file")
            declared.add(path)

            resolved = resolve_in_tree(path, root)
            if resolved is None:
                errors.append(
                    f"rule 0 — `{path}` is absolute or escapes the repository. Declared "
                    f"paths are repository-relative; presence outside the tree proves nothing."
                )
            elif not os.path.exists(resolved):
                errors.append(
                    f"rule 1 — `{path}` is declared in the registry but absent from the tree. "
                    f"Either land the file or remove its row."
                )

            for pointer in ("spec", "ssot", "renderer"):
                target = f.get(pointer)
                if not target:
                    continue
                target_resolved = resolve_in_tree(target, root)
                if target_resolved is None:
                    errors.append(
                        f"rule 0 — `{path}` points at {pointer} `{target}`, which is absolute "
                        f"or escapes the repository"
                    )
                elif not os.path.exists(target_resolved):
                    errors.append(
                        f"rule 3 — `{path}` points at {pointer} `{target}`, which does not exist"
                    )

    for key in ("boot_order_a", "boot_order_b"):
        for step in data.get(key) or []:
            ref = step.get("file")
            if ref and ref not in declared:
                errors.append(
                    f"rule 4 — {key} step {step.get('step')} names `{ref}`, "
                    f"which the registry does not declare"
                )

    return errors


def run_smoke_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, "real.md"), "w").close()

        clean = {
            "sections": [{"key": "core", "files": [
                {"path": "real.md", "purpose": "p", "format": "md",
                 "authority": "Z2", "rw": "Z1 read"},
            ]}],
            "boot_order_a": [{"step": "A.1", "file": "real.md", "action": "pin"}],
        }
        assert validate(clean, root=td) == [], validate(clean, root=td)

        dirty = {
            "sections": [{"key": "core", "files": [
                {"path": "real.md", "purpose": "p", "format": "md",
                 "authority": "Z2", "rw": "Z1 read", "status": "✅ EXISTS"},
                {"path": "ghost.md", "purpose": "p", "format": "md",
                 "authority": "Z2", "rw": "Z1 read", "spec": "nope.md"},
                {"path": "real.md", "purpose": "p", "format": "md",
                 "authority": "Z2"},
            ]}],
            "boot_order_a": [{"step": "A.1", "file": "undeclared.md", "action": "x"}],
        }
        errs = " | ".join(validate(dirty, root=td))
        for rule in ("rule 1", "rule 2", "rule 3", "rule 4", "rule 5", "rule 6"):
            assert rule in errs, f"{rule} not caught: {errs}"

        nested = {"sections": [{"key": "c", "files": [
            {"path": "real.md", "purpose": "p", "format": "md", "authority": "Z2",
             "rw": "r", "meta": {"status": "sneaky"}},
        ]}]}
        assert any("rule 2" in e for e in validate(nested, root=td)), "nested status escaped"

        # rule 0: a path that leaves the tree must not be able to satisfy rule 1.
        # os.path.join(root, "/etc/passwd") == "/etc/passwd", which exists on the
        # runner, so without containment this row would pass as PRESENT.
        for escape in ("/etc/passwd", "../../../etc/passwd"):
            out = {"sections": [{"key": "c", "files": [
                {"path": escape, "purpose": "p", "format": "md",
                 "authority": "Z2", "rw": "r"},
            ]}]}
            errs = validate(out, root=td)
            assert any("rule 0" in e for e in errs), f"{escape} escaped containment: {errs}"
            assert not any("rule 1" in e for e in errs), \
                f"{escape} reported as merely missing rather than out-of-tree"

        ptr = {"sections": [{"key": "c", "files": [
            {"path": "real.md", "purpose": "p", "format": "md", "authority": "Z2",
             "rw": "r", "spec": "/etc/passwd"},
        ]}]}
        assert any("rule 0" in e for e in validate(ptr, root=td)), "out-of-tree spec pointer escaped"

    print("smoke-test OK — catches out-of-tree paths, absent paths, declared status "
          "(incl. nested), dangling pointers, undeclared boot steps, duplicates, "
          "missing fields.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the governance-file registry")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(SSOT):
        print(f"::error::missing {os.path.relpath(SSOT, ROOT)}")
        return 1

    errors = validate(yaml.safe_load(open(SSOT, encoding="utf-8")) or {})
    for e in errors:
        print(f"::error::{e}")

    if errors:
        print(f"\n{len(errors)} error(s) — governance-file registry does not match the tree.")
        return 1

    print("governance-file registry: every declared path resolves; no hand-set status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
