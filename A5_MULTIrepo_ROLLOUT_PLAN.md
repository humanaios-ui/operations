---
doc_id: HAIOS-OPS-006
title: A5 Multi-Repo Rollout Plan
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-08-15
retention: permanent
---

# A5: Multi-Repo Rollout Plan

**Timeline:** Aug 12-18, 2026 (one repo per business day)  
**Owner:** mesh-support  
**Scope:** Extend CI gate + registry link to the other 4 humanaios repos  

---

## Repos & Order (Audit-Derived Sequence)

From the S070126 T3 audit scope, rollout order reflects document density:

| Day | Repo | Docs in Registry | Rollout Action | Lead |
|-----|------|------------------|-----------------|------|
| **Aug 12 (Mon)** | lasting-light-ai | 16 | Deploy CI + update registry links | @lasting-light-ai/research |
| **Aug 13 (Tue)** | humanaios-internal | 9 | Deploy CI + cascade owner approvals | @humanaios-internal/ops |
| **Aug 14 (Wed)** | empirica-foundation | 4 | Deploy CI + brief empirica-foundation on scope | @empirica-foundation/gov |
| **Aug 15 (Thu)** | humanaios | 5 | Deploy CI + core-repo final pass | @humanaios/core |
| **Aug 16-18 (Fri-Sun)** | — | — | Buffer: monitor rollout health, fix issues | mesh-support |

**Total:** 5 repos, all with synchronized control by end of week.

---

## Rollout Checklist (Per Repo)

For each repo on its assigned day:

### Pre-Rollout (Day Before)
- [ ] Fork the CI workflow from operations (`.github/workflows/document-control.yml`)
- [ ] Copy `.doc-control/` scaffolding (schema, validator, templates)
- [ ] Update registry to point to repo as canonical (for its 4-16 documents)
- [ ] Draft CODEOWNERS for the repo's docs
- [ ] Notify area lead 24h in advance

### Activation Day (Morning)
- [ ] Commit CI + scaffolding + CODEOWNERS
- [ ] Announce in Slack/email: "Document control active on [REPO] as of [TIME]"
- [ ] Tag known doc owners to review frontmatter
- [ ] Monitor for CI failures (first PRs will likely hit validation issues)

### First Week Post-Rollout
- [ ] Expected: 5-10 PRs from owners adding/fixing frontmatter
- [ ] Triage any CI failures (schema vs. user error)
- [ ] Approve + merge frontmatter fixes
- [ ] Update registry with new approvals

---

## Per-Repo Integration Notes

### lasting-light-ai (Research, 16 docs)
- Contains: ACAT_PROMPT, METHODS, VALIDATION, methodology.html, etc.
- Challenge: Binary file (ACAT_RESEARCH_PAPER_S-040926.docx) is in registry but CI can't validate binaries
- Action: Mark binary as `excluded` in schema validator (skip frontmatter check)
- Lead: @lasting-light-ai/research

### humanaios-internal (Collab, 9 docs)
- Contains: Collaboration reports, OPERATOR_RUNBOOK, partnership agreements
- Challenge: Some docs are HTML (exported from Google Docs) — lychee may see relative URLs as broken
- Action: Configure lychee to skip relative-path validation for exported docs
- Lead: @humanaios-internal/ops

### empirica-foundation (Cross-org, 4 docs)
- Contains: Research/evaluation docs (minimal governance/process docs here)
- Challenge: Scope interaction — empirica-foundation is org-wide, not humanaios-specific
- Action: Keep humanaios-specific docs in humanaios repo; empirica-foundation uses empirica's own control system (separate)
- Lead: @empirica-foundation/gov (brief: humanaios control doesn't override empirica's)

### humanaios (Core, 5 docs)
- Contains: schema.sql, core config, maybe one README or CONTRIBUTING
- Challenge: Source code (schema.sql) should NOT be registered as a controlled document
- Action: Exclude .sql + .py + .js from registry; keep only documentation
- Lead: @humanaios/core

---

## Canary Testing (Aug 9-11)

Before day 1 rollout, mesh-support runs a canary test on a shadow repo:
1. Fork operations repo control setup
2. Create test PRs that violate + satisfy the CI gate
3. Verify validator catches schema errors
4. Verify markdownlint + lychee work as advisory
5. Document any quirks (e.g., lychee false positives)

**Canary output:** Runbook for rollout (e.g., "lychee flags relative URLs; add `.lychee.toml` exception")

---

## Success Criteria (End of A5)

- ✅ All 5 repos have CI gate active
- ✅ All 5 repos have CODEOWNERS configured
- ✅ Registry reflects all 5 repos as canonical sources
- ✅ ≥80% of registered documents have frontmatter + approval
- ✅ Zero merge blocks due to validator (all schema errors resolved)
- ✅ Intake pipeline operational (A4) feeds new docs into registry

---

## Transition to A6

Once A5 is complete, the drift monitor (A6) can safely run across all 5 repos:
- Biweekly scans for link rot (now catching cross-repo links)
- Staleness detection (documents past `review_due`)
- Registry divergence (mismatches between registry + filesystem)

---

## Rollback Plan

If a repo's rollout causes critical CI blockage:
1. Disable the workflow: move `.github/workflows/document-control.yml` → `.doc-control/ci/` (disables CI)
2. Revert the commit: `git revert <activation-commit>`
3. Assess the root cause
4. Fix in canary environment
5. Re-roll in next cycle (no deadline pressure)

Rollback is low-cost (1 revert) and always available.
