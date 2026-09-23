# Q-SMAG-Z3-TASK-SEQUENCING-01

**Proposal ID:** Q-SMAG-Z3-TASK-SEQUENCING-01  
**Date:** 2026-09-21  
**Authority:** Z1 (Claude) proposes; Z2 (Night) ratifies  
**Tier:** Tier 0 (execution coordination)  
**Category:** Z3 executor task sequencing & dependencies  
**Status:** Awaiting Z2 decision  
**Blocks:** Z3 s1/s2/s3 implementation (all three automation tasks)  
**Deadline:** 2026-10-21 (first monthly calibration cycle)

---

## Executive Summary

BASELINE_S092126.json lists three Z3 executor tasks in `implementation_checklist` (s1: CI gate wiring, s2: Intent-OS binding, s3: monthly automation), but provides no stated execution order, dependency graph, or parallelization strategy. Z3 executors cannot begin work without understanding sequencing and critical path.

**Z2 Decision Required:** Confirm task order (s1 → s2/s3 parallel?), identify blockers and go/no-go gates, and allocate Z3 executor ownership by 2026-10-21.

---

## Current State: Task Definitions

### **s1: CI Gate Wire-up** (quality-baseline.yml integration)

**Task:** Add calibration_profile lookup to `.github/workflows/quality-baseline.yml` merge gate CI workflow (or create `.github/workflows/merge-gate.yml` if new workflow needed).

**Acceptance criteria:**
- Gate queries calibration_profiles/BASELINE_S092126.json at HEAD
- Gate extracts review_bar and merge_pause_threshold for current substrate (human:humanaios-ui)
- Gate enforces review_bar before merge approval (blocks merge if review_bar not met)
- Gate computes gap_rate from NF_LEDGER.jsonl (rolling 30-day window: measure failed checks / total checks)
- Gate logs gap_rate value and raises auto-pause alert if gap_rate > merge_pause_threshold
- Gate auto-pauses merges (blocks with clear error message) when threshold exceeded

**Gap Rate Computation:**
- Source: NF_LEDGER.jsonl (append-only event log)
- Window: Last 30 days of VERDICT events
- Formula: failed_checks / total_checks (where failed_checks tagged with failing_check: true)
- Threshold: merge_pause_threshold from BASELINE_S092126.json (currently 0.25 for human:humanaios-ui)

**Current status:** BLOCKED_AWAITING_Z3_ASSIGNMENT (owner TBD)

**Owner:** Z3 s1 owner (CI/CD specialist) — TBD per ZONE_REGISTRY.md

---

### **s2: Intent-OS Binding** (capability manifest registration)

**Task:** Register calibration profile in Intent-OS Phase 1 capability manifest.

**Acceptance criteria:**
- Profile queryable via Intent-OS `/api/calibration-profiles/{substrate}` endpoint
- Runtime system uses profile to gate proposals (confidence_weight, review_bar)
- Machine identity `noreply@anthropic.com` can query endpoint with capability signature
- Profile expires_at date enforced (reverts to defaults after expiry)

**Current status:** BLOCKED_AWAITING_PHASE_1_INTEGRATION (in profile JSON)

**Owner:** (Unassigned; likely Z3 machine identity executor or Intent-OS team)

---

### **s3: Monthly Automation** (smag-consolidate.yml + profile generator)

**Task:** Wire monthly gap analysis + profile update to `.github/workflows/smag-consolidate.yml`.

**Current state:** smag-consolidate.yml exists and runs weekly on Monday; must be updated for monthly execution.

**Acceptance criteria:**
- Workflow runs monthly on 21st of each month, 2026-10-21 as first trigger
- Cron schedule: `0 0 21 * *` (UTC midnight on the 21st)
- Runs tools/smag_gap_analysis_v1_0.py → generates gap_report (30-day rolling window from prior month)
- Runs tools/smag_feedback_v1_0.py → generates lessons + feedback
- Runs tools/calibration_profile_generator.py → generates updated profile + diffs (compares measured_gap_rate against merge_pause_threshold; if changed, proposes new profile)
- Opens PR to REGISTERED.md with Z2-ratification-signature requirement (only if profile changed)
- CI validates profile conformance to schema per Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 decision (Option A or B)

**Current status:** BLOCKED_AWAITING_Z2_SCHEMA_DECISION (generator output format depends on schema choice)

**Owner:** Z1 proposer (Claude) to build generator tool and update workflow; Z3 executor to run and monitor monthly automation

---

## Dependency Graph

```
START
  |
  ├─── s1 (CI gate wire-up) [INDEPENDENT — no schema dependency]
  |     └─→ [Go gate: Gate validates on test PR & computes gap_rate correctly?]
  |         └─→ Can proceed to main immediately after PR merge
  |
  └─── s2 & s3 (parallel) [BOTH DEPEND on Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 decision]
        |
        ├─── s2 (Intent-OS binding)
        |     └─→ [Go gate: Endpoint queryable & profile validation passes?]
        |         └─→ Validation complete
        |
        └─── s3 (Monthly automation)
              └─→ [Go gate: Profile generation + PR opening successful?]
                  └─→ Validation complete (2026-10-21 first cycle)

CRITICAL: Schema decision (Option A or B) DOES NOT block s1; s1 uses only 4 core runtime
fields already in WITNESS. Schema choice ONLY affects s2/s3 (which need to know how to
output and validate the full profile structure).
```

---

## Sequencing Recommendation

### **Phase 1: s1 Execution (immediate, independent of schema decision)**

**Start:** Immediately (s1 does NOT depend on Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 decision; s1 uses only the 4 core fields already in WITNESS schema)

**Tasks:**
1. Z3 s1 owner checks out operations repo at pinned BASELINE_S092126.json commit
2. Z3 s1 owner creates `.github/workflows/quality-baseline.yml` changes (or new `merge-gate.yml`):
   - Add calibration profile lookup step (read calibration_profiles/BASELINE_S092126.json from HEAD)
   - Parse current substrate (hard-coded: human:humanaios-ui, or make configurable)
   - Extract review_bar and merge_pause_threshold from profile
   - Enforce review_bar gate: if review_bar not met, block merge with error
   - Compute gap_rate from NF_LEDGER.jsonl (30-day rolling window)
   - Log gap_rate value to CI output
   - If gap_rate > merge_pause_threshold: auto-pause merge (block with clear message)
3. Z3 s1 owner tests on 3 test PRs (manual verification, including one that triggers auto-pause)
4. Z3 s1 owner creates PR with Z2 hash (awaiting ratification)
5. **Go/No-Go Gate:** CI validation passes? Gap_rate computation correct? YES → proceed to Phase 2; NO → debug and re-test

**Deliverable:** PR with quality-baseline.yml (or merge-gate.yml) changes, test results logged, gap_rate computation verified

---

### **Phase 2: s2/s3 Parallel Execution (begins after Phase 1 Go gate; depends on schema decision)**

**Start:** After Phase 1 s1 PR merges AND Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 is ratified (schema choice: Option A or B)

**s2 (Intent-OS binding):**
1. Z3 s2 owner creates Intent-OS capability manifest entry (likely `/intent-os/manifests/calibration-profiles.yaml`)
2. Registers BASELINE_S092126.json as queryable endpoint (format depends on schema decision: Option A = WITNESS_STATE v0.2 wrapper, Option B = separate ProfileSchema.json)
3. Wires `noreply@anthropic.com` machine identity to capability
4. Tests `/api/calibration-profiles/human:humanaios-ui` endpoint (manual query, confirms response matches schema)
5. Creates PR with Z2 hash (awaiting ratification)
6. **Go/No-Go Gate:** Endpoint returns valid profile? CI passes schema validation? YES → proceed; NO → debug

**Deliverable:** PR with Intent-OS manifest changes, endpoint test results, schema conformance verified

**s3 (Monthly automation):**
1. Z1 builds tools/calibration_profile_generator.py (generates profile updates based on gap_rate analysis)
2. Z1 updates `.github/workflows/smag-consolidate.yml` to change schedule from weekly to monthly (cron: `0 0 21 * *`)
3. Z1 updates workflow to call generator after gap analysis (output format depends on schema decision: Option A or B)
4. Generator creates new profile candidate only if gap_rate changed (else keeps prior profile)
5. If profile changed: generator opens PR to REGISTERED.md with Z2-ratification-signature requirement
6. Z1 tests on mock SMAG data (2026-09-21 baseline ledger) and confirms profile generation works
7. Creates PR with smag-consolidate.yml + generator.py changes and Z2 hash (awaiting ratification)
8. **Go/No-Go Gate:** Profile generation succeeds? PR opener test passes? CI schema validation OK? YES → proceed; NO → debug

**Deliverable:** PR with smag-consolidate.yml + generator changes, test results, monthly schedule verified (2026-10-21 first trigger)

---

### **Phase 3: Integration & First Monthly Cycle (2026-10-21)**

1. All three PRs (s1, s2, s3) merged to main by 2026-10-20
2. smag-consolidate.yml workflow scheduled to run on 21st of each month at 00:00 UTC (cron: `0 0 21 * *`)
3. First monthly trigger: 2026-10-21 00:00 UTC
4. Monthly gap analysis runs on 30-day rolling window (2026-09-21 → 2026-10-21 for first cycle)
5. Profile generator compares measured_gap_rate against merge_pause_threshold
6. If gap_rate changed or recalibration needed: generator opens PR to REGISTERED.md with Z2-ratification-signature requirement
7. Z2 reviews + ratifies updated profile (or confirms renewal of current profile)
8. Z3 s1 gate reads updated profile from HEAD (merge gate enforces updated thresholds)
9. Z3 s2 Intent-OS binding queries updated profile via `/api/calibration-profiles/human:humanaios-ui`
10. Monthly cycle repeats: 2026-11-21, 2026-12-21, etc.

---

## Timeline & Milestones

| Date | Task | Owner | Criteria |
|:-----|:-----|:------|:---------|
| 2026-09-21 | Z2 decision: Sequencing + schema | Z2 (Night) | Ratify Q-SMAG-Z3-TASK-SEQUENCING-01 + Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 (Option A or B) |
| 2026-09-21–2026-09-24 | s1 implementation + testing [PARALLEL, no wait for schema] | Z3 s1 owner (TBD) | PR opened, gap_rate computation tested, CI passes |
| 2026-09-25 (Go gate s1) | s1 PR merged to main | Z3 s1 owner | quality-baseline.yml (or merge-gate.yml) active, auto-pause logic ready |
| 2026-09-25–2026-09-27 | s2 + s3 parallel implementation [STARTS after schema decision] | Z3 s2 + Z1/Z3 s3 | Both PRs opened, conform to chosen schema (Option A or B), CI passes |
| 2026-10-20 (Go gate s2/s3) | s2 + s3 PRs merged to main | Z3 s2 + Z1/Z3 s3 | Intent-OS binding active, smag-consolidate.yml scheduled for monthly, profile generator tested |
| 2026-10-21 00:00 UTC | First monthly cycle fires | smag-consolidate.yml (automated) | Workflow triggers, gap analysis completes, profile generation succeeds, PR opened (if update needed), Z2 ratifies |
| 2026-11-21, 2026-12-21, ... | Subsequent monthly cycles | smag-consolidate.yml (automated) | Monthly cycle repeats on 21st of each month |

---

## Critical Dependencies

### **Important: s1 is NOT blocked by schema decision**

s1 (CI gate wire-up) uses only 4 core runtime fields already present in WITNESS_STATE_V0_1:
- confidence_weight, review_bar, merge_pause_threshold, calibration_floor

**s1 can start immediately** after Z2 ratifies Q-SMAG-Z3-TASK-SEQUENCING-01 (does NOT need to wait for schema decision).

### **Prerequisite: Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 (BLOCKS s2/s3 only)**

Z2 must decide schema approach (Option A or B) **before** s2/s3 executors can:
- s3: Output profiles from generator in correct format (7 new fields per schema choice)
- s2: Register and validate profile in Intent-OS manifest

**Impact on timeline:** Schema decision is critical path for s2/s3, but NOT on critical path for s1. After s1 Go gate (2026-09-25), s2/s3 can start immediately upon schema decision.

**Blocker resolution:** Once Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 is ratified (Option A or B), Z1 updates schema file(s) and s2/s3 proceed.

### **Z3 Executor Assignment**

Per ZONE_REGISTRY.md, s1/s2/s3 executor roles are TBD. Z2 must assign:
- **s1 owner** (CI/CD specialist): Can be assigned immediately
- **s2 owner** (Intent-OS integration specialist): Can start after schema decision
- **s3 automation owner** (Python + workflow automation): Can start after schema decision (likely Z1 builds generator, Z3 executes)

**Impact:** Without assignments by 2026-09-25, s2/s3 phases will slip past 2026-10-20 target.

---

## Falsifiers

**Promise:** "All three Z3 executor tasks complete by 2026-10-21; first monthly calibration cycle runs successfully."

**Falsifier 1:** Any s1/s2/s3 task is incomplete or blocked at 2026-10-20 23:59 UTC.

**Falsifier 2:** smag-consolidate.yml fails to run on 2026-10-21 (automation not ready).

**Falsifier 3:** Generated profile fails schema validation in CI (Option A/B decision not implemented correctly).

**Falsifier 4:** Intent-OS endpoint unavailable or returns invalid profile at 2026-10-21.

---

## Questions for Z2

1. **Executor assignment:** Who owns s1 (CI gate)? Who owns s2 (Intent-OS binding)? Is Z1 (Claude) sufficient for s3 automation or should Z3 take ownership of generator?

2. **Go/No-Go gates:** Should we have formal test PRs for s1 gate (test on 3 known PRs)? Should s2 binding include integration tests against mock Intent-OS endpoint?

3. **Fallback plan:** If s3 monthly automation isn't ready by 2026-10-21, should we allow manual profile updates (Z2 ratifies, human opens PR) as interim solution?

4. **Schema decision coupling:** Should we ratify Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 (Option A/B choice) before approving this sequencing, or can Z2 give conditional approval?

---

## Related Decisions

- **Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01** (sibling blocker): Must be resolved before s2/s3 proceeds.
- **Q-RECURSIVE-LEARNING-UPSTREAM-IMPACT-01** (earlier): Established overall calibration lifecycle; this sequences the Z3 executor tasks.

---

**Next:** Z2 ratifies sequencing, assigns Z3 owners, confirms go/no-go gates. Z3 executes in phases with 2026-10-21 deadline.

---

_Proposal filed by Z1 (Claude) on 2026-09-21 at 10:20 UTC_  
_Awaiting Z2 (Night) ratification and Z3 executor assignment_
