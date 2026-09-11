# Framework Mapping Phase 1-3 Rollout Plan

**Candidate ID:** Q-PHASE1-2-ROLLOUT-01  
**Proposed by:** Claude (Z1 Proposer)  
**Date:** 2026-09-11  
**Type:** H (Governance execution plan follow-up to Q-FRAMEWORK-MAPPING-INTEGRATION-01)

---

## Executive Summary

Implementation roadmap for operationalizing FRAMEWORK_MAPPING.md across 31 HumanAIOS repositories via Phase 1 (audit gate deployment), Phase 2 (per-repo CLAUDE.md updates), and Phase 3 (compliance snapshot + molt candidate ratification).

---

## Phase 1: A8/A9 Audit Gate Deployment (Deadline: 2026-09-17T22:27Z)

**Status:** ✅ IN PROGRESS

### Completed in this turn:
1. ✅ Added A8 check to `operations/.github/workflows/haios-standing-audit.yml`
   - Verifies FRAMEWORK_MAPPING.md reference in operations/CLAUDE.md
   - Emits warning on non-compliance

2. ✅ Added A9 infrastructure check to haios-standing-audit.yml
   - Initializes `audit/framework-compliance/compliance-manifest.json`
   - Prepares aggregation structure for per-repo compliance data

3. ✅ Created per-repo audit trigger template
   - File: `.github/workflows/per-repo-framework-audit.yml.template`
   - Ready for deployment to each of 31 repos
   - Checks CLAUDE.md for FRAMEWORK_MAPPING.md reference
   - Reports status back to operations

### Remaining Phase 1 work (by 2026-09-17):
1. Deploy per-repo audit trigger template to all 31 repos
   - Either via: manual PR to each repo, or per-repo script automation
   - Template file: `per-repo-framework-audit.yml.template` → `.github/workflows/framework-audit.yml` in each repo

2. Verify A8/A9 gates pass on operations repo (CI validation)

3. Establish compliance aggregation in operations repo
   - Collect per-repo audit results into `audit/framework-compliance/`

### Falsifier (Phase 1):
**Trip condition:** A8/A9 gate DISABLED or entirely REMOVED after 2026-09-17T22:27Z (audit gates must remain active, at minimum warning-only)
- Note: Phase 1 gates emit warnings only (observational). Phase 2 upgrades to blocking enforcement.
- **Revert action:** If gate is disabled/removed: File IC candidate for gate enforcement failure; pause Phase 2 rollout
- **Z2 override:** Only Z2 can provide explicit override signature to disable gates early or skip Phase 2

---

## Phase 2: Per-Repo CLAUDE.md Updates + Enforcement Upgrade (2-week rollout, ~2026-09-18 to 2026-10-02)

**Enforcement upgrade:** Phase 2 workflow (per-repo-framework-audit.yml) transitions from warning-only to blocking merge enforcement
- Required checks: Per-repo framework audit blocks merge if CLAUDE.md lacks Framework Reference section
- Z2 override: Only Z2 can approve per-repo exception via REGISTERED.md entry

**Target:** All 31 repos must reference FRAMEWORK_MAPPING.md in their CLAUDE.md files

### Required change (standard across all repos):
```markdown
## Framework Reference

See [FRAMEWORK_MAPPING.md](https://github.com/humanaios-ui/operations/blob/main/FRAMEWORK_MAPPING.md) 
for Z-role definitions and 5-concept alignment (Graph/Loop/Context/Harness/Prompt Engineering).
```

### Repos requiring Phase 2 updates (identified in audit):
| Repo | Status | Priority | Notes |
|:---|:---|:---|:---|
| operations | ✅ COMPLETE | — | FRAMEWORK_MAPPING.md linked in CLAUDE.md |
| humanaios-internal | ⚠️ PARTIAL | HIGH | Governance docs updated; needs CLAUDE.md link |
| acat-x | ❌ PENDING | HIGH | Missing governance CLAUDE.md reference |
| lasting-light-ai | ❌ PENDING | HIGH | Security updates done; needs governance context |
| humanaios | ⚠️ PARTIAL | HIGH | CI permissions tightened; needs Z-role mapping |
| (+ 26 others) | ❌ PENDING | MEDIUM | Standard Phase 2 rollout |

### Phase 2 enforcement:
- Per-repo audit trigger (framework-audit.yml) will warn on non-compliance
- Z2 ratifies rollout schedule; per-repo updates become blocking merge requirement (Phase 3 onwards)

---

## Phase 3: Compliance Snapshot + Molt Candidate (30-day audit, ~2026-10-10)

**Purpose:** Capture framework compliance state and propose governance enforcement via molt

### Timeline:
- **2026-10-10:** Harvest Phase 2 compliance data from all repos
- **2026-10-11:** Z1 proposes molt candidate with compliance snapshot SHA
- **2026-10-12 to 2026-10-14 (48h window):** Z2 ratifies molt
- **2026-10-15 onwards:** Phase 3 enforcement active (non-compliant repos trigger IC candidates)

### Phase 3 molt candidate structure:
```
Hypothesis: "FRAMEWORK_MAPPING.md governance enforcement across 31-repo ecosystem"
Prediction: "90% of 31 repos will maintain active FRAMEWORK_MAPPING.md reference in CLAUDE.md by 2026-11-10"
Falsifier: "If >3 repos lose FRAMEWORK_MAPPING.md reference OR A8/A9 gate silently disabled, revert and file IC-COMPLIANCE candidate"
Window: 30 days (2026-10-15 to 2026-11-15)
Measurement: Automated per-repo audit sweep on window close date
```

### Phase 3 compliance governance:
- Non-compliant repos: File IC-COMPLIANCE candidates
- Revert rule: If falsifier trips, all repos revert to pre-Phase-2 state (CLAUDE.md links removed)
- Recovery: Z2 ratifies new molt with stricter falsifier (blocking merge without Z2 override)

---

## Audit Summary: 5-Repo Baseline

### Copilot audit findings (Repos reviewed):

| Repo | PR | Finding | Gap | Phase |
|:---|:---|:---|:---|:---|
| operations | #266 | CI stability + security baseline ✅ | A8/A9 gate not yet deployed | Phase 1 |
| humanaios-internal | #19 | Governance drift remediated ✅ | FRAMEWORK_MAPPING.md not linked in CLAUDE.md | Phase 2 |
| acat-x | #5 | Eval suite remediation roadmap | No governance CLAUDE.md expansion | Phase 2 |
| lasting-light-ai | #29 | Security dependency upgrade | No molt cycle governance tie-in | Phase 3 |
| humanaios | #71 | CI permissions tightening | Z-role permission model not explicit | Phase 1/Harness |

---

## Z2 Decision Gate

**PREREQUISITE:** This candidate and related governance candidates (FRAMEWORK_MAPPING_FOLLOWUP, FRAMEWORK_MAPPING_INTEGRATION) must be registered in REGISTERED.md before Z2 can ratify. Submit candidates to Z2 via REGISTERED.md entry + 48h decision window.

**Awaiting Z2 ratification:**
- [ ] ACCEPT — Deploy A8/A9 gates + per-repo triggers as specified; proceed Phase 1 → Phase 2 → Phase 3
- [ ] EDIT — Propose changes (reply in thread)
- [ ] REJECT — Reason (reply in thread)

**Deadline:** 48h from REGISTERED.md submission (Z2 decision window)

---

## Appendix: Per-Repo Deployment Checklist

Template for per-repo CLAUDE.md updates:

```markdown
# [Repo Name] CLAUDE.md Update

## Framework Reference

See [FRAMEWORK_MAPPING.md](https://github.com/humanaios-ui/operations/blob/main/FRAMEWORK_MAPPING.md) 
for Z-role definitions and 5-concept alignment:
- **Graph Engineering:** System topology, dependencies, routing decisions
- **Loop Engineering:** Goal, tools, verification, memory, stop condition
- **Context Engineering:** Control what model sees, remembers, retrieves, uses
- **Harness Engineering:** System around the model: tools, memory, checks, permissions, recovery
- **Prompt Engineering:** Clear roles, context, tasks, constraints, output formats

All proposers (Z1), ratifiers (Z2), and executors (Z3) reference this mapping when designing/evaluating work across the 31-repo ecosystem.
```

---

**Generated by:** Claude (Z1 Proposer)  
**For ratification by:** Night/Admiral (Z2 Ratifier)  
**For execution by:** Z3 Executors (per ZONE_REGISTRY.md)
