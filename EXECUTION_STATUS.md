---
doc_id: HAIOS-OPS-008
title: Document Control Execution Status (A1-A7)
revision: 1
status: approved
owner: "@humanaios-ui/operations"
approved_by: carly
approved_date: 2026-07-29
review_due: 2026-08-15
retention: permanent
---

# Execution Status: Document Control System (A1-A7)

**Last updated:** 2026-07-29 EOD  
**Overall status:** A1-A3 LIVE, A4-A7 STAGED (ready for deployment)

---

## Activation Summary

| Phase | Status | Deployment | Owner | Timeline |
|-------|--------|------------|-------|----------|
| **A1** | ✅ COMPLETE | Registry seeded (34 docs from 71 pairs) | mesh-support | 2026-07-02 |
| **A2** | ✅ COMPLETE | CI gate active (frontmatter + schema validation) | mesh-support | 2026-07-02 |
| **A3** | ✅ COMPLETE | Scaffolding live (schema, validator, templates) | mesh-support | 2026-07-02 |
| **A4** | 🟡 STAGED | Intake pipeline automation (script + workflow) | mesh-support | Aug 5-11 |
| **A5** | 🟡 STAGED | Multi-repo CI rollout (canary + 4 deployments) | mesh-support | Aug 12-15 |
| **A6** | 🟡 STAGED | Drift monitor automation (script + workflow) | mesh-support | Aug 19+ |
| **A7** | 🟡 PLANNED | Ratchet (advisory → error, cross-repo uniform) | mesh-support | TBD |

---

## What's Live Now (A1-A3)

### Registry ✅
- **File:** `document-registry.yaml`
- **Status:** 34 approved, 5 reconcile-needed, 37 excluded
- **Capacity:** Ready for 100+ documents
- **Use:** Central source of truth for document identity, ownership, approval

### CI Gate ✅
- **Location:** `.github/workflows/document-control.yml`
- **Scope:** Operations repo (other repos in A5)
- **Validation:**
  - Frontmatter schema (doc_id, status, owner, approval) → **ERROR blocks merge**
  - Unique doc_id per document → **ERROR blocks dual-canonical**
  - Markdown syntax + internal links → **ADVISORY (warns)**
- **Test:** Any PR touching `.md`, `YAML`, or registry gets validated automatically

### Governance ✅
- **CODEOWNERS:** `.github/CODEOWNERS` (approval ownership by area)
- **Maintainer assignment:** `.doc-control/MAINTAINER_ASSIGNMENT.md` (primary + backup)
- **External-link policy:** `EXTERNAL_LINK_POLICY.md` (fix/defer/supersede)
- **Review cycle:** All docs due for approval by 2026-08-01

---

## Staged for Deployment (A4-A7)

### A4: Intake Pipeline ⚙️

**Status:** Script complete, workflow staged, awaiting area rules

**Scripts:**
- `scripts/intake_pipeline.py` — 4-gate classifier (classify → dedup → reconcile → register)
- `.github/workflows/intake-pipeline.yml` — Weekly automation (Mon 3 AM)

**Activation requirements:**
- [ ] Collect area classification rules (due July 31)
- [ ] Test on historical data
- [ ] Gate 4 (register+place) PR creation logic (deferred to manual)

**Expected output (weekly):**
- Classified inbox files
- Diverged pair recommendations
- New document registrations (gated for manual approval)
- Reduced `_inbox_files*/` backlog (bounded intake)

**Timeline:** Aug 5-11 (implement + test during week 1 of A5-A7)

### A5: Multi-Repo Rollout ⚙️

**Status:** CI + CODEOWNERS templates ready, canary plan staged, rollout schedule confirmed

**Deployment schedule (one repo per day):**

| Date | Repo | Docs | Lead | Canary Date |
|------|------|------|------|------------|
| **Aug 12 (Mon)** | lasting-light-ai | 16 | @lasting-light-ai/research | Aug 9-11 |
| **Aug 13 (Tue)** | humanaios-internal | 9 | @humanaios-internal/ops | Aug 9-11 |
| **Aug 14 (Wed)** | empirica-foundation | 4 | @empirica-foundation/gov | Aug 9-11 |
| **Aug 15 (Thu)** | humanaios | 5 | @humanaios/core | Aug 9-11 |
| **Aug 16-18 (Fri-Sun)** | — | — | mesh-support (monitor) | — |

**Canary testing (Aug 9-11):**
- Shadow repo with same control setup
- Test PRs that violate + satisfy schema
- Verify validators + lychee behavior
- Document quirks (e.g., lychee config for relative URLs)

**Rollback plan:**
- If rollout causes blockage: disable workflow (revert to `.doc-control/ci/`)
- Low-cost recovery (1 revert)

**Timeline:** Aug 12-18 (one repo per day, buffer Aug 16-18)

### A6: Drift Monitor ⚙️

**Status:** Script complete, workflow staged, awaiting A5 completion

**Scripts:**
- `scripts/drift_monitor.py` — Biweekly scanner (link rot, stale docs, missing files)
- `.github/workflows/drift-monitor.yml` — Automated issues (Mon 2 AM)

**Activation requirements:**
- [ ] All 5 repos onboarded (A5 complete)
- [ ] First run: validate false-positive rate
- [ ] GitHub issues creation (requires workflow token config)

**Expected output (biweekly):**
- Novel drift detection (novel vs recurring noise suppression)
- Auto-generated GitHub issues (one per area)
- Actionable recommendations (fix/defer/supersede)
- MTTR tracking (turnaround ≤ 5 days)

**Timeline:** Aug 19+ (after A5, runs independently)

### A7: Ratchet (Phase Promotion) 📋

**Status:** Planned (deferred until A6 proves stable)

**What:** Promote advisory checks to errors

**Scope:**
- Vale prose style (warnings → errors)
- External link validation (lychee offline → lychee online strict)
- Cross-repo uniform control (all 5 repos same standards)

**Trigger:** A6 runs 2+ cycles with <5% false-positive rate

**Timeline:** TBD (dependent on A6 stability)

---

## Notifications Sent

**Targets:** All 5 humanaios practices

| Practice | File | Rollout Date | Key Action |
|----------|------|--------------|------------|
| lasting-light-ai | `NOTIFICATION_lasting-light-ai.md` | Aug 12 | Submit area rules by July 31 |
| humanaios-internal | `NOTIFICATION_humanaios-internal.md` | Aug 13 | Submit area rules + backup maintainer role |
| empirica-foundation | `NOTIFICATION_empirica-foundation.md` | Aug 14 | Scope boundary clarification (Aug 10) |
| humanaios | `NOTIFICATION_humanaios-core.md` | Aug 15 | Submit area rules, exclude source code |
| humanaios-ui | `PRACTICES_ANNOUNCEMENT.md` | (hub) | General announcement + TL;DR |

**Delivery:** Ready to send via Slack/email (copy from operations repo)

---

## Critical Path (Aug 5-18)

```
Week 1 (Aug 5-11):
  Mon 5   → A4 begins: area rules collection + intake pipeline test
  Fri 9   → Canary testing begins (A5 dry-run)
  
Week 2 (Aug 12-15):
  Mon 12  → A5 DAY 1: lasting-light-ai rollout
  Tue 13  → A5 DAY 2: humanaios-internal rollout
  Wed 14  → A5 DAY 3: empirica-foundation rollout
  Thu 15  → A5 DAY 4: humanaios rollout
  Fri 18  → A5 complete; A6 staging begins
  
Week 3+ (Aug 19):
  Mon 19  → A6 live: drift monitor first scan
  Mon 26  → A6 second scan (biweekly cadence begins)
```

---

## Success Criteria (Per Phase)

### A4 Success (End Aug 11)
- ✅ Pipeline script runs without errors on historical data
- ✅ Area classification rules collected (≥4 areas)
- ✅ Intake workflow active and tested
- ✅ `_inbox_files*/` backlog plan (target: <100 files or 100% routed to PRs)

### A5 Success (End Aug 15)
- ✅ All 5 repos have CI gate active
- ✅ All 5 repos have CODEOWNERS configured
- ✅ ≥80% of registered documents approved (frontmatter + signature)
- ✅ Zero merge blocks due to schema (all errors resolved)
- ✅ Canary issues documented + resolved

### A6 Success (End Aug 26, after 2nd run)
- ✅ Drift monitor script runs without errors
- ✅ Workflow creates GitHub issues automatically
- ✅ <5% false-positive rate (novel issues are actionable)
- ✅ Area owners responding to issues (MTTR <5 days)

---

## Known Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|-----------|
| Area rules not submitted by July 31 | Medium | Medium | Default fallback rules; can add later |
| CI too strict, blocks legitimate changes | Low | High | Canary testing (Aug 9-11) catches this |
| Drift monitor false positives | Medium | Medium | Novel-vs-recurring diff (suppresses noise) |
| External link checks timeout | Low | Medium | Lychee config: offline mode + skip external |
| GitHub workflow permissions missing | Low | High | Test workflow token config Aug 15-18 |

---

## Rollback Capabilities

**A1-A3:** Not needed (purely additive, no breaking changes)

**A4:** Can disable workflow by moving `.github/workflows/intake-pipeline.yml` → `.doc-control/ci/`

**A5:** Per-repo rollback: revert CI deployment commit, disables gate (data safe in registry)

**A6:** Disable workflow same as A4 (move to `.doc-control/ci/`)

All rollbacks are single-commit reverts with no data loss.

---

## Next Steps (Immediate)

- [ ] **Carly:** Approve execution timeline (Aug 5-18)
- [ ] **mesh-support:** Begin A4 intake pipeline testing
- [ ] **All practices:** Submit area classification rules by July 31
- [ ] **mesh-support:** Canary testing Aug 9-11
- [ ] **mesh-support:** A5 rollout Aug 12-15 (one per day)

---

## Contacts

| Role | Practice | Contact |
|------|----------|---------|
| **Primary Maintainer** | mesh-support | @empirica-mesh-support |
| **Backup Maintainer** | humanaios-ui/operations | @humanaios-ui/operations |
| **Questions** | — | File issue: `document-control/question` |

**Status check:** This document updated weekly (Fridays) through Aug 29.
