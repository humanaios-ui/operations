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

### **s1: CI Gate Wire-up** (merge-gate.yml integration)

**Task:** Add calibration_profile lookup to `.github/workflows/merge-gate.yml` merge gate CI workflow.

**Acceptance criteria:**
- Gate queries calibration_profiles/BASELINE_S092126.json
- Gate extracts review_bar and merge_pause_threshold for substrate
- Gate enforces review_bar before merge approval
- Gate logs gap_rate and raises auto-pause alert if gap_rate > merge_pause_threshold

**Current status:** BLOCKED_AWAITING_Z2_SIGN_OFF (in profile JSON)

**Owner:** (Unassigned per ZONE_REGISTRY.md)

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

**Acceptance criteria:**
- smag-consolidate.yml runs monthly (2026-10-21 first cycle)
- Runs tools/smag_gap_analysis_v1_0.py → generates gap_report
- Runs tools/smag_feedback_v1_0.py → generates lessons + feedback
- Runs tools/calibration_profile_generator.py → generates updated profile + diffs
- Opens PR with Z2-ratification-signature requirement
- CI validates profile conformance to schema (depends on Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 decision)

**Current status:** PENDING_Z2_DECISION (in profile JSON)

**Owner:** Z1 proposer (Claude) to build automation; Z3 executor to run workflow

---

## Dependency Graph

```
START
  |
  +--- s1 (CI gate wire-up)
  |      |
  |      +---> [Go gate: Gate validates successfully on test PR?]
  |             |
  |             +---> s2 & s3 (parallel)
  |                    |
  |                    +--- s2 (Intent-OS binding)
  |                    |     |
  |                    |     +---> [Go gate: Intent-OS endpoint queryable?]
  |                    |            |
  |                    |            +---> Validation complete
  |                    |
  |                    +--- s3 (Monthly automation)
  |                          |
  |                          +---> [Go gate: Profile generation + PR opening successful?]
  |                                 |
  |                                 +---> Validation complete
  |
END (2026-10-21 first monthly cycle deadline)
```

---

## Sequencing Recommendation

### **Phase 1: s1 Execution (this week)**

**Start:** Immediately after Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 is resolved (Option A/B chosen)

**Tasks:**
1. Z3 s1 owner checks out operations repo at pinned BASELINE_S092126.json commit
2. Z3 s1 owner creates `.github/workflows/merge-gate.yml` changes:
   - Add profile lookup step (curl to GitHub raw or local read)
   - Parse substrate from PR metadata (from SMAG ledger or canonical mapping)
   - Extract review_bar + merge_pause_threshold
   - Enforce review_bar gate
   - Log gap_rate comparison
3. Z3 s1 owner tests on 3 test PRs (manual verification)
4. Z3 s1 owner creates PR with Z2 hash (awaiting ratification)
5. **Go/No-Go Gate:** CI validation passes? YES → proceed to Phase 2; NO → debug and re-test

**Deliverable:** PR with merge-gate.yml changes, test results logged

---

### **Phase 2: s2/s3 Parallel Execution (next week, after Phase 1 Go)**

**s2 (Intent-OS binding):**
1. Z3 s2 owner creates Intent-OS capability manifest entry (likely `/intent-os/manifests/calibration-profiles.yaml`)
2. Registers BASELINE_S092126.json as queryable endpoint
3. Wires `noreply@anthropic.com` machine identity to capability
4. Tests `/api/calibration-profiles/human:humanaios-ui` endpoint (manual query)
5. Creates PR with Z2 hash
6. **Go/No-Go Gate:** Endpoint returns valid profile? CI passes schema validation? YES → proceed; NO → debug

**Deliverable:** PR with Intent-OS manifest changes, endpoint test results

**s3 (Monthly automation):**
1. Z1 builds tools/calibration_profile_generator.py (if not exists)
2. Z1 updates smag-consolidate.yml to call generator after gap analysis
3. Generator creates new profile candidate (compares gap_rate vs merge_pause_threshold)
4. Generator opens PR to REGISTERED.md with Z2-ratification-signature requirement
5. Z1 tests on mock SMAG data (2026-09-21 baseline ledger)
6. Creates PR with Z2 hash
7. **Go/No-Go Gate:** Profile generation succeeds? PR opener test passes? CI schema validation OK? YES → proceed; NO → debug

**Deliverable:** PR with smag-consolidate.yml + generator changes, test results

---

### **Phase 3: Integration & First Monthly Cycle (2026-10-21)**

1. All three PRs merged to main
2. First smag-consolidate.yml monthly run triggers (2026-10-21 or first business day after)
3. Monthly gap analysis runs on 30 days of data (2026-09-21 → 2026-10-21)
4. Profile generator produces updated BASELINE_S092126_V1_0.json (if gap_rate changed)
5. Z2 reviews + ratifies (or renews same profile)
6. Z3 s1 gate enforces updated profile in merge gate
7. Z3 s2 Intent-OS binding queries updated profile
8. Cycle repeats monthly

---

## Timeline & Milestones

| Date | Task | Owner | Criteria |
|:-----|:-----|:------|:---------|
| 2026-09-21 | Z2 decision: Schema + sequencing | Z2 (Night) | Ratify both ICs or request edits |
| 2026-09-22–2026-09-24 | s1 implementation + testing | Z3 s1 owner (TBD) | PR opened, CI passes, test PRs validated |
| 2026-09-25 (Go gate s1) | s1 PR merged to main | Z3 s1 owner | merge-gate.yml active |
| 2026-09-25–2026-09-27 | s2 + s3 parallel implementation | Z3 s2 + Z1/Z3 s3 | Both PRs opened, CI passes |
| 2026-09-28 (Go gate s2/s3) | s2 + s3 PRs merged to main | Z3 s2 + Z1/Z3 s3 | Intent-OS binding active, automation ready |
| 2026-10-21 | First monthly cycle | Z3 s1 + Z1/s3 automation | smag-consolidate.yml runs, gap analysis completes, profile updates ratified |

---

## Critical Dependencies

### **Prerequisite: Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01**

Z2 must decide schema approach (Option A or B) **before** s2/s3 executors can:
- Validate profile output from generator (s3)
- Register profile in Intent-OS manifest (s2)

**Blocker resolution:** Once Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01 is ratified, Z1 updates schema files and s2/s3 can proceed.

### **Prerequisite: WITNESS_STATE Schema Conformance**

If Z2 chooses Option A, WITNESS_STATE_V0_1.schema.json must be updated to v0.2 before:
- s3 can output profiles from generator
- s2 can bind to Intent-OS (Intent-OS may validate against WITNESS schema)

### **Z3 Executor Assignment**

Per ZONE_REGISTRY.md, s1/s2/s3 executor roles are TBD. Z2 must assign:
- s1 owner (CI/CD specialist)
- s2 owner (Intent-OS integration specialist)
- s3 automation owner (Python + workflow automation)

**Impact:** Without assignments, 2026-10-21 deadline is unachievable.

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
