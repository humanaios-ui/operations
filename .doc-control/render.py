#!/usr/bin/env python3
"""Render CONTROLLED_DOCUMENTS.md from document-registry.yaml.

CONTROLLED_DOCUMENTS.md has always CLAIMED to be rendered from the registry
("Do not hand-edit — edit the registry") but no renderer existed, so it was
maintained by hand and drifted: it described 34 controlled documents while the
registry held 46. This closes that loop, and CI runs `--check` so the two can
no longer disagree.

Usage:
  python3 .doc-control/render.py           # write CONTROLLED_DOCUMENTS.md
  python3 .doc-control/render.py --check   # exit 1 if out of sync (CI mode)
  python3 .doc-control/render.py --smoke-test

Deps: PyYAML. No network; writes only CONTROLLED_DOCUMENTS.md.
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

TOOL_NAME = "doc_registry_renderer"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "infrastructure_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "document-registry.yaml")
OUTPUT = os.path.join(ROOT, "CONTROLLED_DOCUMENTS.md")

AREA_TITLES = {
    "WEB": "Site Pages",
    "COLLAB": "Collaborator Reports",
    "RES": "Research",
    "OPS": "Operations / State",
    "PROC": "Process / Runbooks",
    "GOV": "Governance",
    "ENG": "Engagement / External",
    "DOC": "Uncategorized",
}


def _esc(text: str) -> str:
    return (str(text) if text is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def _flags(doc: dict) -> str:
    out = []
    if doc.get("needs_reconcile"):
        out.append("needs-reconcile")
    if doc.get("superseded_by"):
        out.append(f"superseded-by {doc['superseded_by']}")
    return ", ".join(out) or "—"


def render(registry: dict) -> str:
    docs = registry.get("documents") or []
    excluded = registry.get("excluded") or []
    holds = registry.get("known_accuracy_issues") or []

    by_status: dict[str, int] = {}
    for d in docs:
        by_status[d.get("status", "?")] = by_status.get(d.get("status", "?"), 0) + 1

    lines: list[str] = []
    add = lines.append

    add("# HumanAIOS — Controlled Documents Index")
    add("")
    add("> Rendered from `document-registry.yaml` (SSOT) by `.doc-control/render.py`.")
    add("> **Do not hand-edit — edit the registry.** CI blocks when the two disagree.")
    add("")
    blocking = sum(1 for h in holds if h.get("blocks_approval"))
    add(f"**{len(docs)} controlled documents** · {len(excluded)} excluded · "
        f"{blocking} content-accuracy holds")
    add("")
    add("**Status:** `draft` = Z1 draft, not yet submitted · `review` = seeded, pending owner "
        "verification · `approved` = owner-verified (human gate) · `superseded`/`retired` = "
        "obsolete (retained).")
    add("")
    add("Approval is the owner's act and is never automated — no self-grant.")
    add("")

    add("## Summary")
    add("")
    add("| metric | value |")
    add("|---|---|")
    add(f"| Controlled documents | {len(docs)} |")
    for status in ("draft", "review", "approved", "superseded", "retired"):
        if by_status.get(status):
            add(f"| — status `{status}` | {by_status[status]} |")
    add(f"| Needing reconciliation | {sum(1 for d in docs if d.get('needs_reconcile'))} |")
    add(f"| Content-accuracy holds | {blocking} |")
    add(f"| Excluded | {len(excluded)} |")
    add("")

    # --- documents by area, largest area first (stable tie-break on name) ---
    groups: dict[str, list[dict]] = {}
    for d in docs:
        groups.setdefault(d.get("area", "DOC"), []).append(d)

    for area in sorted(groups, key=lambda a: (-len(groups[a]), a)):
        entries = sorted(groups[area], key=lambda x: str(x.get("doc_id", "")))
        title = AREA_TITLES.get(area, area.title())
        add(f"## {title} — `{area}` ({len(entries)})")
        add("")
        add("| doc_id | title | repo | canonical path | status | flags |")
        add("|---|---|---|---|---|---|")
        for d in entries:
            add("| {did} | {title} | {repo} | `{path}` | {status} | {flags} |".format(
                did=_esc(d.get("doc_id")),
                title=_esc(d.get("title")),
                repo=_esc(d.get("canonical_repo")),
                path=_esc(d.get("canonical_path")),
                status=_esc(d.get("status")),
                flags=_flags(d),
            ))
        add("")

    # --- reconciliation queue ---
    pending = [d for d in docs if d.get("needs_reconcile")]
    if pending:
        add(f"## Reconciliation queue ({len(pending)})")
        add("")
        add("Documents whose inbox copy diverged from the repo copy and need a merge decision "
            "before they can be approved.")
        add("")
        add("| doc_id | canonical path | recommendation |")
        add("|---|---|---|")
        for d in sorted(pending, key=lambda x: str(x.get("doc_id", ""))):
            add(f"| {_esc(d.get('doc_id'))} | `{_esc(d.get('canonical_path'))}` | "
                f"{_esc(d.get('reconcile_recommendation') or d.get('recommendation'))} |")
        add("")

    # --- review schedule ---
    # Deliberately date-INDEPENDENT: the rendered file must be reproducible, or
    # CI's --check would start failing on the day a document tips overdue with
    # nobody having changed anything. `validate.py` does the "is it overdue
    # today" call, where a moving answer belongs.
    scheduled = [d for d in docs
                 if d.get("review_due") and d.get("status") not in ("superseded", "retired")]
    if scheduled:
        add(f"## Review schedule ({len(scheduled)})")
        add("")
        add("Earliest due first. Anything dated before today is overdue — `.doc-control/validate.py` "
            "flags those on every run. The review itself is the owner's act.")
        add("")
        add("| review due | doc_id | canonical path | status |")
        add("|---|---|---|---|")
        for d in sorted(scheduled, key=lambda x: (str(x.get("review_due")), str(x.get("doc_id")))):
            add(f"| {_esc(d.get('review_due'))} | {_esc(d.get('doc_id'))} | "
                f"`{_esc(d.get('canonical_path'))}` | {_esc(d.get('status'))} |")
        add("")

    # --- accuracy holds ---
    if holds:
        add(f"## ⚠️ Content-accuracy holds ({blocking}) — block approval")
        add("")
        add("From the S070126 docs/ content-accuracy audit (separate content-curation workstream "
            "— referenced, not re-audited). A doc matching one of these **cannot reach "
            "`approved`** until fixed (enforced by `validate.py`).")
        add("")
        add("| document | issue | severity |")
        add("|---|---|---|")
        for h in holds:
            add(f"| {_esc(h.get('doc'))} | {_esc(h.get('issue'))} | {_esc(h.get('severity'))} |")
        add("")

    # --- excluded, summarized by repo ---
    if excluded:
        add(f"## Excluded from doc-control ({len(excluded)})")
        add("")
        add("Source code, config, and binaries surfaced by the audit but governed by normal code "
            "review / manual binary handling — **not** controlled documents.")
        add("")
        per_repo: dict[str, dict[str, int]] = {}
        for e in excluded:
            repo = e.get("repo", "?")
            bucket = per_repo.setdefault(repo, {})
            bucket[e.get("scope", "?")] = bucket.get(e.get("scope", "?"), 0) + 1
        add("| repo | excluded | scope |")
        add("|---|---|---|")
        for repo in sorted(per_repo):
            total = sum(per_repo[repo].values())
            add(f"| {_esc(repo)} | {total} | {', '.join(sorted(per_repo[repo]))} |")
        add("")

    add("---")
    add("")
    add("**Adding a controlled document:** add an entry to `document-registry.yaml` with "
        "`status: draft`, run `python3 .doc-control/render.py`, and commit both. "
        "`.doc-control/validate.py` gates the structural rules; the owner sets `approved`.")
    add("")
    return "\n".join(lines)


def run_smoke_test() -> int:
    sample = {
        "documents": [
            {"doc_id": "HAIOS-GOV-001", "title": "A|B", "area": "GOV", "canonical_repo": "operations",
             "canonical_path": "GOVERNANCE.md", "status": "review", "needs_reconcile": True,
             "reconcile_recommendation": "merge additive content"},
            {"doc_id": "HAIOS-RES-001", "title": "R", "area": "RES", "canonical_repo": "operations",
             "canonical_path": "R.md", "status": "approved"},
        ],
        "excluded": [{"path": "x.py", "repo": "operations", "scope": "code"}],
        "known_accuracy_issues": [{"doc": "X", "issue": "off by 25x", "severity": "high",
                                   "blocks_approval": True}],
    }
    out = render(sample)
    assert "2 controlled documents" in out, out
    assert "Reconciliation queue (1)" in out, out
    assert "A\\|B" in out, "pipe not escaped"
    assert "Content-accuracy holds (1)" in out, out
    print("smoke-test OK — renders areas, reconciliation queue, holds; escapes cells.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Render CONTROLLED_DOCUMENTS.md from document-registry.yaml")
    ap.add_argument("--check", action="store_true", help="exit 1 if CONTROLLED_DOCUMENTS.md is out of sync")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(REGISTRY):
        print(f"::error::missing {os.path.relpath(REGISTRY, ROOT)}")
        return 1

    out = render(yaml.safe_load(open(REGISTRY, encoding="utf-8")) or {})

    if args.check:
        current = open(OUTPUT, encoding="utf-8").read() if os.path.exists(OUTPUT) else ""
        if current != out:
            print("::error::CONTROLLED_DOCUMENTS.md is out of sync with document-registry.yaml — "
                  "run `python3 .doc-control/render.py` and commit.")
            return 1
        print("CONTROLLED_DOCUMENTS.md: in sync with the registry.")
        return 0

    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {os.path.relpath(OUTPUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
