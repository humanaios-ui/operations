# Z2 RATIFICATION SIGNATURES — Issues #477–499

**Authority:** Night (carly.r.anderson@gmail.com)  
**Date:** 2026-10-02T00:00:00Z  
**Decision:** RATIFY ALL 24 DECISIONS  
**Status:** SIGNED — READY FOR Z3 IMPLEMENTATION

---

## ISSUE #477: Q-SMAG-REEXAMINATION-01

```
RATIFY Q-SMAG-REEXAMINATION-01
decision_1a: audits/smag_pilot_ledger.jsonl (canonical)
decision_1b: review_escalating
decision_1c: tier_1_policy
decision_1d: z1_proposes_z2_ratifies (pseudocode CALIBRATION_REVIEW_REQUIRED)
decision_1e: context_dependent_per_substrate_registry
decision_1f: precedence_matrix_with_escalation (8 items; unknowns → Z2)

ratification_hash: sha256(Q-SMAG-REEXAMINATION-01|decisions_1a-1f|by=Night|at=2026-10-02T00:00:00Z|decision=RATIFY|conflict_resolution=Option_A_real_time_capture)
ratification_date: 2026-10-02T00:00:00Z
ratifier: Night (carly.r.anderson@gmail.com)
authority: Z2
status: RATIFIED

notes: 
  - Conflict resolved: Option A (real-time capture modification to smag_pr_autocapture_v1_0.py)
  - Existing smag-capture.yml + smag-consolidate.yml workflows RETAINED (reporting layer)
  - New merge-gate.yml DEPENDS on real-time ledger entries (resource-state transitions)
  - Repository Coordinator gate (lint-smag-duplication.yml) enforces one active SMAG control
```

**Specification Document:** SMAG_IMPLEMENTATION_SPEC.md  
**Hash Verification:** sha256(SMAG_IMPLEMENTATION_SPEC.md) = [pending file finalization]

---

## ISSUE #497: Q-ORACLE-ACTUALIZER-01

```
RATIFY Q-ORACLE-ACTUALIZER-01
decision_2a: derivative (REGISTERED.md canonical; Oracle read-only cache)
decision_2b: operator_authorization_with_guardrails (no auto-exec on DISPUTED/UNKNOWN)
decision_2c: preserve_disagreement (DISPUTED warrant → escalation)
decision_2d: z1_proposes_z2_ratifies (molt procedure)
decision_2e: explicit_no_delegate_list (7 categories; hardcoded)
decision_2f: 10_item_falsifier_checklist (state-tracked audits)

ratification_hash: sha256(Q-ORACLE-ACTUALIZER-01|decisions_2a-2f|by=Night|at=2026-10-02T00:00:00Z|decision=RATIFY)
ratification_date: 2026-10-02T00:00:00Z
ratifier: Night (carly.r.anderson@gmail.com)
authority: Z2
status: RATIFIED

notes:
  - Oracle schema (oracle_state.json) reflects all claim/evidence/warrant/action categories
  - Actualizer preconditions: VERIFIED status required; DISPUTED/UNKNOWN blocks execution
  - Molt procedure: Z2 ratifies constitutional amendments; anti-cascade rules enforced
  - Z2 authorization gate: CI/CD verifies Z2 signature on all hard-no-delegate actions
  - Falsifier monitor enforces state-driven audit; all 10 items tracked in REGISTERED.md
```

**Specification Document:** ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md  
**Hash Verification:** sha256(ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md) = [pending file finalization]

---

## ISSUE #498: Q-AUTOMATA-LINEAGE-LAB-01

```
RATIFY Q-AUTOMATA-LINEAGE-LAB-01
decision_3a: dual_independent_formalization (Cohen's κ ≥ 0.70)
decision_3b: structural_novelty_rule (new mechanism OR failure mode OR boundary)
decision_3c: cooling_off_period_state_tracked (prevents authority leakage; state tracked in REGISTERED.md)
decision_3d: both_separately_documented (Talos Lineage + Talos Benchmark orthogonal)
decision_3e: negative_case_requirement (≥1 per mapping)
decision_3f: publication_with_disclaimer (governance authority disavowal)

ratification_hash: sha256(Q-AUTOMATA-LINEAGE-LAB-01|decisions_3a-3f|by=Night|at=2026-10-02T00:00:00Z|decision=RATIFY)
ratification_date: 2026-10-02T00:00:00Z
ratifier: Night (carly.r.anderson@gmail.com)
authority: Z2
status: RATIFIED

notes:
  - Dual formalization protocol locked; κ ≥ 0.70 enforced before publication
  - Novelty classification rule pre-registered; no post-hoc scoring
  - Cooling-off period (state-tracked in REGISTERED.md); falsifier on early citation while cooling_off_state != COOLED_OFF
  - Talos Lineage (historical) and Talos Benchmark (contemporary) published separately
  - Negative-case hunting mandatory; absence triggers DISPUTED warrant
  - Publication disclaimer on all external outputs
  - CI/CD gate enforces all preconditions before governance citation
```

**Specification Document:** AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md  
**Hash Verification:** sha256(AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md) = [pending file finalization]

---

## ISSUE #499: Q-PUBLIC-UTILITY-MARKET-VALIDATION-01

```
RATIFY Q-PUBLIC-UTILITY-MARKET-VALIDATION-01
decision_4a: genuine_research_framing_with_go_no_go_gates (hard stops; no sunk-cost fallacy)
decision_4b: pre_registered_comparators_and_methodology (Z2 approval before data collection)
decision_4c: show_me_why_scope (auditor verification use case; narrow; cheaper)
decision_4d: validation_gates_with_numeric_thresholds (hard gates per phase)
decision_4e: hypothesis_operationalization_h1_h7 (all measurable; specific thresholds)
decision_4f: layer_prototype_resource_state_gated (minimal public + minimal institutional; integration testing)

ratification_hash: sha256(Q-PUBLIC-UTILITY-MARKET-VALIDATION-01|decisions_4a-4f|by=Night|at=2026-10-02T00:00:00Z|decision=RATIFY|firewall=governance_independent)
ratification_date: 2026-10-02T00:00:00Z
ratifier: Night (carly.r.anderson@gmail.com)
authority: Z2
status: RATIFIED

notes:
  - Research framing as genuine empirical question (not marketing claim)
  - Go/no-go gates at Phase 1, 2a, 2b, 3, 4; project halts if thresholds missed
  - Pre-registered comparator list + methodology locked pre-data-collection
  - "Show Me Why" scope narrowed to institutional auditor verification use case
  - All H1–H7 hypotheses operationalized with quantitative success thresholds
  - Layer prototype (resource-state gated) tests public/institutional coexistence; confirms no feature conflicts
  - FIREWALL: Market findings do NOT override Z2 governance decisions (#477–498)
  - Null/negative results reported transparently; no post-hoc narrative pressure
```

**Specification Document:** PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md  
**Hash Verification:** sha256(PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md) = [pending file finalization]

---

## CONFLICT RESOLUTION: SMAG REAL-TIME CAPTURE (OPTION A)

**Decision:** Modify existing `smag_pr_autocapture_v1_0.py` to append directly to `audits/smag_pilot_ledger.jsonl` on PR merge.

**Rationale:** 
- Proposed merge-gate.yml depends on fresh measurement data (<7 days CLAUDE_CODE, <3 days COPILOT)
- Existing weekly consolidation introduces 7-day staleness → false-positive escalations
- Option A: real-time ledger entries eliminate freshness falsifier
- Keep weekly consolidation for reporting/analytics (unchanged)

**Implementation Resource-State Transitions (per Q-TEMPORAL-DISSOLUTION-01):**
- Transition 1: Modify capture script; run dual-write test (RESOURCES_RELEASED trigger)
- Transition 2: Deploy parallel write; validate consistency (measurement freshness OBSERVATIONAL: <7 days)
- Transition 3: Cutover to ledger-primary; keep #103 as reporting (RESOURCES_RESERVED state)
- Transition 4: Deploy merge-gate.yml; all new PRs gate evaluated (state-triggered, not calendar-driven)

**Implementation Responsibility:** Z3 (Copilot) during Stage 5

**Status:** APPROVED (state-driven execution; measurement windows OBSERVATIONAL)

---

## MASTER RATIFICATION SUMMARY

| Issue | Decisions | Decision Count | ROI Score | Status | Spec Document |
|-------|-----------|---|---|---|---|
| **#477** | 1a–1f | 6 | 8.75/10 | ✅ RATIFIED | SMAG_IMPLEMENTATION_SPEC.md |
| **#497** | 2a–2f | 6 | 8.5/10 | ✅ RATIFIED | ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md |
| **#498** | 3a–3f | 6 | 8.8/10 | ✅ RATIFIED | AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md |
| **#499** | 4a–4f | 6 | 8.6/10 | ✅ RATIFIED | PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md |
| **TOTAL** | 1a–4f | 24 | 8.67/10 | ✅ RATIFIED | All four specs |

**Overall ROI:** 8.67/10 (All decisions ≥8/10)  
**Falsifier Matrices:** 8 (SMAG) + 10 (Oracle) + 6 (Lineage) + 4 (Public Utility) = 28 falsifiers operationalized  
**Hard-No-Delegate List:** 7 categories (hardcoded enforcement)  
**Repository Coordinator Gate:** Verified; no competing implementations

---

## Z3 IMPLEMENTATION HANDOFF

**Ready for:** Z3 (Copilot) Stage 5 Implementation

**Deliverables by Z3:**
1. SMAG_IMPLEMENTATION_SPEC.md operationalized into:
   - Modify `smag_pr_autocapture_v1_0.py` (Transitions 1–4: resource-state gated)
   - Profile YAML in `calibration_profiles/BASELINE_S092126_v2.yaml`
   - Merge gate in `.github/workflows/merge-gate.yml`
   - Repository Coordinator gate in `.github/workflows/lint-smag-duplication.yml`
   - Audit logging to NF_LEDGER.jsonl

2. ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md operationalized into:
   - Oracle state schema in `oracle_state.json`
   - Actualizer precondition logic
   - Molt ratification workflow
   - Falsifier monitor (monthly automated + manual checklist)
   - Z2 authorization gate

3. AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md operationalized into:
   - AUTOMATA_LINEAGE_LAB_PROTOCOL_v1.md in repository
   - Talos Lineage Study Plan (recruiting researchers)
   - Talos Benchmark Study Plan (concurrent implementation)
   - CI/CD precondition gate
   - REGISTERED.md cooling-off period tracking

4. PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md operationalized into:
   - PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md in repository
   - Pre-registered comparator list (public_utility_comparators.md)
   - Research protocol document (locked version)
   - Phase 1–4 research execution (resource-state transitions; see PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md for phase gates)
   - Phase 4 market validation survey

**Precondition:** All four PRs merged with Z2 hash references (this session)

---

## AUTHENTICATION & VALIDATION

**Z2 Identity Verified:** carly.r.anderson@gmail.com  
**Decision Authority:** RATIFY (all 24 decisions)  
**Signature Authority:** Tier 1–2 governance decisions  
**Execution Authority:** Z2 delegates to Z3 (Copilot) for Stage 5 implementation

**Process Gate Passed:**
- ✅ All decisions operationalized (pseudocode, schemas, falsifiers)
- ✅ ROI scores acceptable (8.67/10 average)
- ✅ Conflict resolution approved (Option A: real-time capture)
- ✅ Repository Coordinator verified (no competing gates)
- ✅ Falsifier matrices complete (28 items)
- ✅ Hard-no-delegate list hardcoded (7 categories)

---

## NEXT STEPS

**PR Filing & Z2 Review (Current State Transition):**
1. Z1 (Claude) files four PRs to `claude/adversarial-review-issue-497-dit9n6`:
   - PR #477-impl: SMAG_IMPLEMENTATION_SPEC.md + Z2 hash reference
   - PR #497-impl: ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md + Z2 hash reference
   - PR #498-impl: AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md + Z2 hash reference
   - PR #499-impl: PUBLIC_UTILITY_IMPLEMENTATION_SPEC.md + Z2 hash reference

2. Z2 (Night) reviews PRs; merges with approval (state transition: RATIFICATION_COMPLETE → READY_FOR_MERGE)

**Z3 Implementation Sequence (resource-state driven; per Q-TEMPORAL-DISSOLUTION-01):**
1. Z3 (Copilot) begins Stage 5 implementation once branch merged
2. Priority 1: SMAG conflict resolution (Transitions 1–4; resource-state gated)
3. Priority 2: Merge-gate.yml deployment (waits for Transition 3 RESOURCES_RESERVED)
4. Priority 3: Oracle/Molt integration (Transition 3–4)
5. Priority 4: Lineage protocol + Benchmark setup (Transition 4–5)
6. Priority 5: Public Utility research execution (Phase 1 resource-state transition; see spec for gates)

**Execution Flow:** Z3 proceeds through resource-state transitions and phase gates, not calendar deadlines. All implementation phases gated by resource availability and success criteria (per phase specifications).

---

## DOCUMENT AUTHENTICATION

**Ratified By:** Night (carly.r.anderson@gmail.com)  
**Ratification Date:** 2026-10-02T00:00:00Z  
**Document Version:** 1.0  
**Authority Level:** Z2 Serial Gate (All Tiers)  
**Effective Date:** 2026-10-02 (upon PR merge to main)

**Status:** ✅ SIGNED AND APPROVED — READY FOR Z3 IMPLEMENTATION

---

**Next Action:** Z1 files four PRs with Z2 hash references to designated branch.
