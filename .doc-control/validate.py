#!/usr/bin/env python3
"""HumanAIOS document-control validator (Phase 2, errors-only).

Enforces the mechanical controlled-document rules from DOCUMENT_CONTROL_PLAN.md:
  1. document-registry.yaml parses and each entry has required fields.
  2. doc_id is unique and well-formed.
  3. Exactly one `canonical: true` per doc_id.
  4. status is in the allowed enum; approved ⇒ canonical copy resolvable.
  5. Any *.md whose frontmatter declares a doc_id must exist in the registry
     with matching canonical repo/path (no divergence, no orphans).
  6. A document canonical to THIS repo resolves on disk (no dead entries).
  7. review_due parses as an ISO date; overdue is a warning, not a block.
  8. The registry's own `counts:` block matches reality — the header cannot lie.

Exit code 0 = clean, 1 = violations (blocks merge). Human judgment (is this the
RIGHT content?) stays with reviewers; this only enforces the structural rules.

Deps: PyYAML (CI installs it). No network, no writes.
"""
from __future__ import annotations
import os, re, sys, glob
from datetime import date

try:
    import yaml
except ImportError:
    print("::error::PyYAML not installed (pip install pyyaml)"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "document-registry.yaml")
ID_RE = re.compile(r"^HAIOS-[A-Z]+-\d{3}$")
STATUSES = {"draft", "review", "approved", "superseded", "retired"}
FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
# This checkout. Documents canonical to a SIBLING repo cannot be resolved from
# here, so rule 6 only applies to entries claiming this one.
THIS_REPO = "operations"
# A doc that is obsolete on purpose may have had its file removed.
GONE_OK = {"superseded", "retired"}

errors: list[str] = []
warnings: list[str] = []
def err(m: str) -> None: errors.append(m)
def warn(m: str) -> None: warnings.append(m)

def print_and_exit():
    for w in warnings:
        print(f"::warning::{w}")
    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n{len(errors)} document-control violation(s), {len(warnings)} warning(s).")
        sys.exit(1)
    print(f"document-control: OK — {len(docs)} registered documents, no violations "
          f"({len(warnings)} advisory warning(s)).")
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

    # --- 6: a document canonical to THIS repo must resolve on disk ----------
    path = d.get("canonical_path")
    if path and d.get("canonical_repo") == THIS_REPO and st not in GONE_OK:
        if not os.path.exists(os.path.join(ROOT, path)):
            err(f"{did}: canonical_path '{path}' does not exist in {THIS_REPO} (status={st})")

    # --- 7: review_due must be a real date; overdue is advisory ------------
    raw_due = d.get("review_due")
    if raw_due:
        try:
            due = date.fromisoformat(str(raw_due))
        except ValueError:
            err(f"{did}: review_due '{raw_due}' is not an ISO date (YYYY-MM-DD)")
        else:
            if due < date.today() and st not in GONE_OK:
                warn(f"{did}: review overdue since {due.isoformat()} (status={st})")

for did, n in canonical_count.items():
    if n != 1:
        err(f"{did}: {n} canonical:true entries (must be exactly 1)")

# --- 8: the registry's own counts block must match reality ------------------
declared_counts = reg.get("counts") or {}
actual_counts = {
    "documents": len(docs),
    "excluded": len(reg.get("excluded") or []),
    "needs_reconcile": sum(1 for d in docs if d.get("needs_reconcile")),
}
for key, actual in actual_counts.items():
    if key in declared_counts and declared_counts[key] != actual:
        err(f"counts.{key} says {declared_counts[key]} but the registry holds {actual}")

# --- 4b: known content-accuracy issues block approval -----------------------
def _norm(s: str) -> str:
    return re.sub(r"\.[a-z]+$", "", s or "").upper().replace("-", "_")
_flagged = {}
for f in (reg.get("known_accuracy_issues") or []):
    if f.get("blocks_approval"):
        _flagged[_norm(f.get("doc", ""))] = f.get("issue", "accuracy issue")
for d in docs:
    norm_title = _norm(d.get("title", ""))
    if d.get("status") == "approved" and norm_title in _flagged:
        err(f"{d.get('doc_id')}: cannot be approved — known accuracy issue: {_flagged.get(norm_title, 'accuracy issue')}")

# --- 5: frontmatter of controlled docs matches the registry ------------------
# Control-system internals are governed by CODEOWNERS, not by doc-control
# itself — the same reason document-registry.yaml is not a registered document.
SKIP_DIRS = (
    os.sep + ".doc-control" + os.sep,
    os.sep + ".tool-control" + os.sep,
    os.sep + "_templates" + os.sep,
)
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
