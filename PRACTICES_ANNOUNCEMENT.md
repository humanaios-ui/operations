# HumanAIOS Document Control System: ACTIVATION ANNOUNCEMENT

**Date:** 2026-07-29  
**Status:** A1-A3 Live. A4-A7 Queued (Aug 5-18)  
**Audience:** All humanaios practices

---

## TL;DR

The S070126 audit found 71 diverged document pairs and 1653 uncontrolled files. **We've deployed a standing system to prevent this from recurring.** As of today:

- ✅ **34 controlled documents registered** with unique IDs (HAIOS-AREA-###)
- ✅ **CI gate active** — all PRs that touch docs get validated for schema + single-source-of-truth
- ✅ **Template + scaffolding ready** — new documents can be created immediately

**Your action required by 2026-08-01:** Review your docs in `document-registry.yaml`. Approve by setting `status: approved` in a PR.

---

## What This Means for Your Practice

### If You Own Documents
- Example: `METHODS.md`, `CURRENT.md`, `GOVERNANCE.md`, partnership agreements, site pages
- **Action:** Find your doc in the registry (search by title). Create a PR to add frontmatter (copy template) + set `status: approved`
- **Timeline:** Do this by Aug 1 so A4 (intake pipeline) can start fresh

### If You Create New Documents
- Start with the template: `/operations/docs/_templates/controlled-doc.md`
- Add frontmatter header (doc_id, status, owner, approval)
- Push to branch → CI validates → merge after CODEOWNERS approves
- New document gets registered automatically

### If You Work in a Non-Operations Repo
- **Until Aug 12:** No CI gate on your repo yet. You can still create docs normally.
- **Starting Aug 12:** Your repo gets the same control system (one repo per day, Aug 12-15)
- **Your action:** Day before your rollout, be ready to review + approve docs in your repo

---

## Three Reads (Pick Your Depth)

| Depth | Document | Time |
|-------|----------|------|
| **TL;DR** | DOCUMENT_CONTROL_ACTIVATION_BRIEF.md (this page) | 5 min |
| **My Area's Rollout** | A5_MULTI_REPO_ROLLOUT_PLAN.md (find your repo's day) | 10 min |
| **How It Works** | DOCUMENT_CONTROL_PLAN.md (full design + rationale) | 20 min |

---

## Timeline (Next 3 Weeks)

| Week | Phase | Your Role |
|------|-------|-----------|
| **Week 1 (Aug 5-11)** | A4: Intake pipeline | Submit classification rules for your area (comment on A4 spec by July 31) |
| **Week 2 (Aug 12-18)** | A5: Multi-repo rollout | Your repo goes live on assigned day — be ready to approve docs |
| **Week 3+ (Aug 19)** | A6: Drift monitor | Respond to document maintenance alerts (fix links, refresh stale docs) |

---

## Where to Send Questions

- **"How do I approve my document?"** → See DOCUMENT_CONTROL_ACTIVATION_BRIEF.md FAQ
- **"What's my area code (GOV, PROC, RES, etc.)?"** → See A4_INTAKE_PIPELINE_SPEC.md rules template
- **"When does my repo roll out?"** → See A5_MULTI_REPO_ROLLOUT_PLAN.md (find your repo)
- **"Can I delete a controlled document?"** → DOCUMENT_CONTROL_PLAN.md §3.3 (answer: mark superseded, never delete)
- **"What about external links that break?"** → EXTERNAL_LINK_POLICY.md (fix/defer/supersede — no silent removal)

**File an issue:** `humanaios-ui/operations` with tag `document-control/question`

---

## Key Decisions (Already Made — FYI)

✅ Scope: All 5 humanaios repos  
✅ Control hub: humanaios-ui/operations  
✅ Primary maintainer: empirica-mesh-support  
✅ Backup maintainer: humanaios-ui/operations (if mesh-support unavailable)  
✅ External links: Fix/defer/supersede (no silent removal) — advisory now, error phase 6  
✅ Binary files: Excluded from control (metadata only)  

---

## Alignment with HumanAIOS Governance

This system:
- **Mirrors empirica's epistemic artifact model** (doc_id ≈ finding_id, version tracking)
- **Integrates with Foundation governance** (mesh-support is cross-practice plumbing)
- **Supports 12 Traditions compliance** (documented decision-making, single source of truth)
- **Enables audit trails** (every approval is timestamped + attributed)

---

## Questions for Your Area (Submit by July 31)

Comment on `A4_INTAKE_PIPELINE_SPEC.md` with:
1. **Your area name** (e.g., "Research", "Collaboration")
2. **Key document patterns** (e.g., "anything in collaborators/ folder", "files named METHODS.md")
3. **Your team's CODEOWNERS group** (who approves docs in your area?)

**Example response:**
```
Area: Research
Patterns: METHODS.*, VALIDATION.*, ACAT*, methodology.html
CODEOWNERS: @lasting-light-ai/research
```

---

**Full activation details:** See DOCUMENT_CONTROL_ACTIVATION_BRIEF.md in the operations repo.

**Questions?** File an issue tagged `document-control/question` on humanaios-ui/operations.
