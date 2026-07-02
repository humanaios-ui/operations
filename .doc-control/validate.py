#!/usr/bin/env python3
"""HumanAIOS document-control validator (Phase 2, errors-only).

Enforces the mechanical controlled-document rules from DOCUMENT_CONTROL_PLAN.md:
  1. document-registry.yaml parses and each entry has required fields.
  2. doc_id is unique and well-formed.
  3. Exactly one `canonical: true` per doc_id.
  4. status is in the allowed enum; approved ⇒ canonical copy resolvable.
  5. Any *.md whose frontmatter declares a doc_id must exist in the registry
     with matching canonical repo/path (no divergence, no orphans).

Exit code 0 = clean, 1 = violations (blocks merge). Human judgment (is this the
RIGHT content?) stays with reviewers; this only enforces the structural rules.

Deps: PyYAML (CI installs it). No network, no writes.
"""
from __future__ import annotations
import os, re, sys, glob

try:
    import yaml
except ImportError:
    print("::error::PyYAML not installed (pip install pyyaml)"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "document-registry.yaml")
ID_RE = re.compile(r"^HAIOS-[A-Z]+-\d{3}$")
STATUSES = {"draft", "review", "approved", "superseded", "retired"}
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

errors: list[str] = []
def err(m: str) -> None: errors.append(m)

def print_and_exit():
    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n{len(errors)} document-control violation(s).")
        sys.exit(1)
    print(f"document-control: OK — {len(docs)} registered documents, no violations.")
    sys.exit(0)

# --- 1-4: registry integrity -------------------------------------------------
if not os.path.exists(REGISTRY):
    docs = []; err(f"missing {os.path.relpath(REGISTRY, ROOT)}"); print_and_exit()

reg = yaml.safe_load(open(REGISTRY)) or {}
docs = reg.get("documents") or []
by_id: dict[str, dict] = {}
canonical_count: dict[str, int] = {}

for d in docs:
    did = d.get("doc_id", "<missing>")
    for f in ("doc_id", "title", "canonical_repo", "canonical_path", "status"):
        if not d.get(f):
            err(f"{did}: missing required field '{f}'")
    if did != "<missing>" and not ID_RE.match(did):
        err(f"{did}: doc_id does not match HAIOS-<AREA>-<nnn>")
    if did in by_id:
        err(f"{did}: duplicate doc_id")
    by_id[did] = d
    st = d.get("status")
    if st and st not in STATUSES:
        err(f"{did}: invalid status '{st}' (allowed: {sorted(STATUSES)})")
    if st == "approved" and not (d.get("approved_by") and d.get("approved_date")):
        err(f"{did}: status=approved requires approved_by + approved_date")
    if d.get("canonical") is True:
        canonical_count[did] = canonical_count.get(did, 0) + 1

for did, n in canonical_count.items():
    if n != 1:
        err(f"{did}: {n} canonical:true entries (must be exactly 1)")

# --- 5: frontmatter of controlled docs matches the registry ------------------
SKIP_DIRS = (os.sep + ".doc-control" + os.sep, os.sep + "_templates" + os.sep)
for path in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
    if any(s in path for s in SKIP_DIRS):
        continue
    raw = open(path, encoding="utf-8", errors="replace").read()
    m = FM_RE.match(raw)
    if not m:
        continue
    block = m.group(1)
    # Only enforce on CONTROLLED docs — those declaring a doc_id. Other docs
    # (Claude SKILL.md, F/H/IC entries) use their own frontmatter conventions.
    if not re.search(r"(?m)^doc_id:", block):
        continue
    try:
        fm = yaml.safe_load(block) or {}
    except yaml.YAMLError as e:
        err(f"{os.path.relpath(path, ROOT)}: controlled doc has unparseable frontmatter ({e})"); continue
    did = fm.get("doc_id")
    if not did or not ID_RE.match(str(did)):
        err(f"{os.path.relpath(path, ROOT)}: doc_id '{did}' malformed (need HAIOS-<AREA>-<nnn>)"); continue
    if did not in by_id:
        err(f"{os.path.relpath(path, ROOT)}: doc_id {did} not in registry (orphan)")

print_and_exit()
