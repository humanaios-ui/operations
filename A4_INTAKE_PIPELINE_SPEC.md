---
doc_id: HAIOS-PROC-005
title: A4 Intake Pipeline Specification
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-08-15
retention: permanent
---

# A4: Intake Pipeline Specification

**Timeline:** Aug 5-11, 2026  
**Owner:** mesh-support (automation) + area leads (triage rules)  
**Goal:** Turn the S070126 T1 inbox triage (1653 files) into a standing, repeatable 4-gate process.

---

## The S070126 T1 Triage (What We're Operationalizing)

The audit manually classified 1653 files in `_inbox_files*` into buckets:
1. **Type** — document vs. code vs. config vs. binary vs. other
2. **Owner** — which team/area should decide its fate
3. **Action** — keep (add to registry), reconcile (merge with existing), or exclude (code/binary)

**Result:** Every file got classified but most still sit in inbox unprocessed. A4 turns this into an automated pipeline that **processes new inbox files on a cadence** (weekly or on-push).

---

## 4-Gate Pipeline

```
_inbox/ ──1.classify──> 2.dedup-vs-registry ──> 3.reconcile ──> 4.register+place
         (type, owner)   (is this already a       (if diverged    (assign doc_id,
                          controlled doc?)         copy → merge)    frontmatter, canonical)
```

### Gate 1: Classify (Automatic)
- **Input:** New file in `_inbox/` or `_inbox_files*/`
- **Detection:** Filename extension + heuristics (header scan for Markdown, JSON schema for data files, etc.)
- **Output:** Tag with `(type:document | type:code | type:config | type:binary | type:other)` + `(owner:<area>)`
- **Routing:** Route to gate 2 for document-type; quarantine code/binary/config (excluded from control)

**Rules to define (by area):**
- **Operations:** CURRENT.md, REGISTERED.md, GOVERNANCE.md patterns → owner:ops
- **Research:** METHODS.*, VALIDATION.*, ACAT* → owner:research
- **Collab:** anything in collaborators/ or with S-XXXXXX date tag → owner:collab
- **Web:** .html, site/* → owner:web
- **Default:** owner:operations (escalate to CODEOWNERS)

### Gate 2: Dedup vs Registry
- **Input:** Document-type file + owner tag
- **Check:** Does `registry.yaml` already list a doc with matching name/content hash?
- **Outcome:**
  - **Match found:** Route to gate 3 (reconcile the versions)
  - **No match:** Route to gate 4 (register as new)
  - **Ambiguous:** Quarantine for human review (flag in GitHub issue)

### Gate 3: Reconcile (Human Decision)
- **Input:** Diverged pair — inbox copy vs. canonical repo copy
- **Analysis:** Size delta, line-by-line diff, last-modified date
- **Recommendation:** 
  - If repo is newer/complete → delete inbox copy, use repo canonical (most common)
  - If inbox is newer/additive → merge additive content into repo, then delete inbox
  - If truly different → flag for owner to decide, don't auto-merge
- **Process:** 
  - Create a GitHub PR showing the diff + recommendation
  - Tag CODEOWNERS for the area
  - Close PR if owner selects "use repo"; merge if "use inbox additive"
  - Inbox file moved to `_inbox_archive/` once resolved

### Gate 4: Register + Place
- **Input:** New document (no registry match)
- **Workflow:**
  1. Assign `doc_id` (HAIOS-AREA-XXX) — next available in the area
  2. Add frontmatter header (standard YAML)
  3. Set `status: draft` (owner must review + approve)
  4. Set `canonical_repo` + `canonical_path` (where the file lives or will live)
  5. Add entry to `registry.yaml`
  6. Move inbox file to canonical location (in appropriate repo)
  7. Create issue: "New document registered: HAIOS-XXX-NNN — review + approve"
- **Owner action:** Review in PR, add `approved_by` + set `status: approved`, merge

---

## Automation Tools

**Script:** `operations/scripts/intake_pipeline.py` (to create)
- Watches `_inbox_files*/` directories
- Runs gates 1-2 automatically
- Creates PRs for gate 3 (reconciliation) + gate 4 (registration)
- Runs on: weekly schedule (cron) + on-demand (`git push --force` a special branch)

**Trigger:**
```bash
# Manual trigger
empirica loop fire intake-pipeline

# Or via GitHub action
.github/workflows/intake-pipeline.yml runs weekly
```

**Output:**
- PRs created per diverged pair + per new document
- `_inbox_files*/` stays bounded (files move to archive after resolution)
- Registry grows as new documents are approved

---

## Success Criteria (End of A4)

- ✅ Pipeline script written + tested on historical data
- ✅ GitHub workflow active (`.github/workflows/intake-pipeline.yml`)
- ✅ Area-specific classification rules documented (by owner area)
- ✅ `_inbox_files*/` backlog reduced to ≤50 files (or 100% routed to PRs)
- ✅ Registry grows from 34 → ~50 approved documents (rest in draft/review)

---

## Handoff to A5

Once A4 is done, the intake pipeline runs continuously. A5 extends the CI gate (and registry link) to the other 4 repos, which means:
- New documents in those repos also hit the intake pipeline
- Cross-repo divergence is caught on the first commit (not three months later at audit)

---

## Rules Template (Copy for Your Area)

```yaml
# A4 Classification Rules — [AREA]

TYPE_RULES:
  - extension: [".md"]
    pattern: "METHODS|VALIDATION|ACAT"
    type: document
    owner: research
  
  - path_contains: "collaborators/"
    type: document
    owner: collab
  
  - extension: [".html"]
    type: document
    owner: web

# If none match, escalate to @humanaios-ui/operations
```

**Submit your area's rules as a PR comment on this activation brief by 2026-07-31.**
