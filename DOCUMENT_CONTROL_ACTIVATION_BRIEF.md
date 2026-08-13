---
doc_id: HAIOS-OPS-005
title: Document Control Activation Brief (A1-A3 Complete)
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-08-01
retention: permanent
---

# Document Control Activation Brief

**Status: LIVE as of 2026-07-29**

This brief explains what just activated, what it means for your practice, and what happens next.

---

## What Happened (A1-A3 Complete)

The S070126 audit found **71 diverged document pairs** (single files existing in multiple repos with conflicting versions) and **1653 uncontrolled files** in inboxes. This control system stops the divergence from recurring and makes document intake repeatable.

**Three foundational phases are now active:**

### A1: Registry Seeded ✅
- Every known controlled document has a `doc_id` (HAIOS-AREA-###)
- Each doc_id maps to one canonical location (the SSOT)
- 34 documents approved, 5 flagged for reconciliation, 37 excluded (code/config/binaries)
- Lives in `document-registry.yaml`

### A2: CI Gate Active ✅
- Any PR that touches `.md`, `YAML`, or the registry gets checked automatically
- Frontmatter schema enforced (doc_id, status, owner, approval required)
- Markdown syntax validated
- Broken internal links caught (external links deferred to Phase 6)
- **Gate outcome:** If schema broken or doc_id duplicated → PR blocked. Fix and re-push.

### A3: Scaffolding Ready ✅
- Template for new docs available
- Validator runs locally: `python3 .doc-control/validate.py`
- Team ownership matrix set up (CODEOWNERS)

---

## What This Means for Your Practice

### If You Own Docs in `REGISTERED.md` or `CURRENT.md`
- Your doc appears in the registry as `status: review`
- **Action by 2026-08-01:** Review the registry entry. Approve by setting `status: approved` + `approved_by: <your-name>` (edit via PR, merge needs CODEOWNERS approval)
- **If divergence exists** (inbox vs repo differ): The registry recommends which to keep. Merge the additive content into the canonical location, then approve.

### If You Create New Documents
- Add frontmatter header (copy from template in `/operations/docs/_templates/controlled-doc.md`)
- Assign a doc_id (HAIOS-AREA-###) — ask mesh-support if unsure of the area code
- Push to your branch → CI validates → merge after CODEOWNERS approval
- Registry is auto-updated on merge (or manually re-scanned during A6)

### If You Work in a Different Repo (humanaios, humanaios-internal, lasting-light-ai, empirica-foundation)
- **Phase 2** (Aug 5-11): Your repo gets the same CI gate + registry link
- **Phase 5** (Aug 12-18): The control hub (operations) publishes read-only registry views so you can reference docs without maintaining separate copies
- **Until then:** No action needed. CI won't block yet; control is pilot-phase on operations repo only.

---

## Next Steps (A4-A7): What's Queued

| Phase | What | When | Owner | Your Role |
|-------|------|------|-------|-----------|
| **A4** | Intake pipeline: Turn T1 triage into standing 4-gate process | Aug 5-11 | mesh-support | Contribute rules for your area's inbox files |
| **A5** | Extend CI to your repo | Aug 12-18 | mesh-support | Review docs marked for your area, approve frontmatter |
| **A6** | Drift monitor: Biweekly scans catch link rot + stale docs | Aug 19+ | autonomy + mesh-support | Respond to alerts in your area (fix/defer/supersede) |
| **A7** | Ratchet: Cross-repo uniform control + optional site publish | Later | mesh-support | (No action until Phase 6 completes) |

---

## FAQ

**Q: Why doc_id instead of just filenames?**  
A: Filenames can change; doc_id persists. The registry is stable and searchable by id.

**Q: What if I have a document outside the registry?**  
A: A4 (intake pipeline) will surface it. Until then, unregistered docs don't block CI — they'll be discovered in the next scan.

**Q: Can I delete a controlled document?**  
A: No. Mark it `superseded` or `retired` instead (preserves history, prevents silent loss). Only T3 compliance audits can remove old versions.

**Q: What about binary files (PDFs, .docx)?**  
A: Excluded from the registry. If you have a critical binary, register its metadata + a link location instead.

**Q: Who approves my document?**  
A: The CODEOWNERS group for your area (see `.github/CODEOWNERS`). Approval is a human decision, never automated.

---

## Links

- **Registry:** `operations/document-registry.yaml` (single source of truth)
- **Policy:** `operations/EXTERNAL_LINK_POLICY.md` (what to do with broken links)
- **Method:** `operations/DOCUMENT_CONTROL_PLAN.md` (full design + rationale)
- **Assignment:** `operations/.doc-control/MAINTAINER_ASSIGNMENT.md` (who owns infrastructure)

**Questions?** File an issue on the operations repo with tag `document-control/question`.
