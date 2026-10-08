# AERC Phase 1: Measurement Contract Documentation

**Research Proposal:** Issue #737 (SESSION-AERC-OUTPUT-QUALITY-001)  
**Status:** ADMISSION_REQUESTED  
**Authority Required:** Z2 ratification before pilot launch  

---

## Overview

This directory contains the **Phase 0 measurement contract** for AERC research. It defines the operational, statistical, and ethical framework for the Phase 1 pilot study. **No implementation or pilot work should proceed** until this contract is reviewed and ratified by Z2.

---

## Documents in This Package

### 1. **PREREGISTRATION_PROTOCOL_PHASE_1.md**
Formal preregistration of research design, hypotheses, and methodology.

**Sections:**
- Research questions (H1 / H0 / disconfirming outcomes)
- Task specification (24 preregistered cases; 3 domains)
- Experimental design (three-arm comparison: Baseline / Generic Revision / AERC)
- Response and challenge classification (observable, descriptive only)
- Seven-dimensional quality vector (verified correctness, grounding, calibration, utility, consequence detection, authority deference, autonomy preservation)
- Evaluator requirements (API + experts for factual; tests + reviewers for engineering; expert panel for decision-support)
- Primary efficacy endpoint (≥50% of cases where AERC > Baseline)
- Secondary endpoints (false-hold rate ≤15%, kappa ≥0.65, confounding ≤2 cases)
- ACAT ablation plan (separate exploratory analysis)
- Non-goals (no consciousness claims, no production deployment from synthetic tests, no self-issued authorizations)

**Why preregistration?** Prevents post-hoc researcher degrees of freedom (p-hacking, HARKing). Forces commitment to analysis plan before seeing data.

---

### 2. **STOPPING_RULES.md**
Explicit halt conditions and decision thresholds. Prevents silent failure or goal-post moving.

**Hard Stop Conditions (pilot halts immediately):**
- Measurement reliability failure (kappa < 0.60)
- False-hold rate > 20%
- Confounding > 25% of cases
- Governance/safety violations

**Efficacy Failure Conditions (pilot completes, result is negative):**
- No improvement (efficacy < 50%)
- Improvement explained by additional tokens/revisions
- Improvement limited to single domain

**Cost-Benefit Conditions:**
- Latency overhead > 50%
- Human review time > 10 min/case
- Measured benefit offset by cost

**Precision Thresholds:**
- Scoring reproducibility ≥ 90%
- Minimum evaluator coverage per domain
- Case completion ≥ 90%

**Timeline:**  
6-week schedule from Arm A scoring through Z2 decision gate.

---

### 3. **schemas/** (JSON Schema Definitions)

Four JSON schemas define the data structures for measurement and auditing:

#### **case_schema.json**
Single evaluation case record.
- case_id (AERC-PILOT-001 to 024)
- domain (Factual Reasoning, Software Engineering, Decision Support)
- prompt_text + prompt_hash (SHA-256 fingerprint)
- evidence_set (named sources, access controls)
- ground_truth_class (EMPIRICAL, DESIGN, CONSEQUENTIAL)
- validation_method (how ground truth is determined)
- model_config (frozen across arms)
- evaluators + blinding notes

**Use:** Audit trail; ensures no post-hoc task changes.

---

#### **challenge_schema.json**
Contradictory claim or evidence presented to model.
- challenge_id
- challenge_text + challenge_hash (SHA-256)
- standing (SUPPORTED / DISPROVEN / UNRESOLVED)
- standing_evidence (how it was classified)
- claim_targeted (which statement was challenged)
- evidence_source (where challenge came from)
- evaluator_id + blinding

**Use:** Tracks challenge validity independently; enables RQ about whether model defends against true vs. false challenges.

---

#### **quality_score_schema.json**
Independent evaluator scores on seven dimensions.
- score_id
- case_id + arm (A/B/C)
- evaluator_id + blinded_ref
- dimensions (object containing):
  - verified_correctness (0-1, basis for score)
  - material_claim_grounding (count + fraction)
  - confidence_calibration (if applicable)
  - task_utility (domain-specific rubric)
  - material_consequence_detection (hazard checklist)
  - appropriate_authority_deference (authority rules)
  - user_autonomy_preservation (preserves choice)
- dimensions_applicable_count (for normalization)
- inter_rater_comparison (for agreement calculation)

**Use:** Basis for efficacy measurement; per-domain analysis; false-hold audit.

---

#### **disposition_schema.json**
System recommendation on output handling.
- disposition_id
- disposition (BLOCK / HOLD_FOR_EVIDENCE / DELIVERABLE_ADVISORY)
- triggering_conditions (harm, unauthorized, unsupported, disproven evidence, etc.)
- block_specifics (if BLOCK: reason + regeneration guidance)
- hold_specifics (if HOLD: evidence needed + SLA)
- deliverable_specifics (if DELIVERABLE: limitations + can_authorize=false)
- override_authority (audit trail if overridden)

**Use:** Tracks disposition accuracy; measures false-hold rate; ensures authorization boundary respected.

---

## How to Use This Package

### For Z2 Admission Review

1. Read **PREREGISTRATION_PROTOCOL_PHASE_1.md** (14 sections, ~2000 words)
2. Review **STOPPING_RULES.md** for halt conditions and thresholds
3. Skim **schemas/** for data structure examples
4. Decision options:
   - **APPROVE:** Proceed to Phase 1 pilot (assign evaluators, freeze 24 cases)
   - **REVISE:** Request specific changes (e.g., different weights, additional domains, modified stopping rules)
   - **REJECT:** Recommend alternative approach (if measurement strategy is fundamentally flawed)

### For Pilot Implementation

Once approved:

1. **Preregister 24 cases** using `case_schema.json` (no changes after publication)
2. **Calibrate evaluators** on rubric with practice cases (target kappa ≥ 0.65)
3. **Run three arms** in parallel with blinded assignment
4. **Log all data** using schemas (case, challenge, quality_score, disposition)
5. **Monitor stopping rules** weekly; halt if hard stop triggered
6. **Compute primary efficacy** at week 5
7. **Report findings** per checklist in preregistration protocol
8. **Submit to Z2 decision gate** (PROCEED / REVISE / REJECT)

---

## Key Principles Embedded in This Contract

### 1. **Falsifiability**
Every claim is testable. H0 (no improvement) is as plausible as H1 (improvement). Disconfirming outcomes are explicitly defined upfront.

### 2. **Independence**
Evaluators are blinded to arm identity, model name, and previous scores. Ground truth is determined by prespecified methods, not evaluator consensus.

### 3. **Reproducibility**
All data is timestamped, hashed, and attributed. Anyone with the data can recompute results. No "evaluator judgment" black boxes.

### 4. **Transparency**
Stopping rules are explicit; they cannot be invoked silently. Confounding, disagreements, and missing data are documented and reported, not hidden.

### 5. **Governance Boundary**
Quality assessment is **advisory only**. Output quality scores do **not** authorize action. Authorization remains a separate, explicit decision.

### 6. **Cost-Benefit Honest**
If AERC is expensive (latency, review time, false holds), cost is measured and reported. Improvement must overcome cost, not be claimed despite it.

---

## What This Package Does NOT Include

- ❌ **Task manifest** (the 24 specific cases) — created and frozen during Phase 0 setup
- ❌ **Evaluator assignments** — decided after Z2 approval
- ❌ **Pilot results** — produced during Phase 1
- ❌ **Final decision report** — written after results are in

---

## Critical Dates

| Milestone | Timeline | Gating Authority |
|-----------|----------|---|
| **Measurement contract finalized** | Now | Z2 admission review |
| **Phase 0 complete** (cases preregistered, evaluators trained) | 1-2 weeks | Z2 approval |
| **Phase 1 pilot** (scoring complete) | 4-6 weeks | Z2 observational |
| **Results reported** | 1-2 weeks | Claude red-team + Z2 |
| **Z2 decision** (PROCEED / REVISE / REJECT) | 1 week | Z2 sole authority |

---

## Questions for Z2 / Reviewers

Before approving, clarify:

1. **Task feasibility:** Can we realistically obtain ground truth for all 24 cases within 6 weeks?
2. **Evaluator availability:** Are domain experts available for training + practice calibration?
3. **Cost tolerance:** Is 4-6 week pilot schedule acceptable? Do we have compute/human budget?
4. **Scope:** Should we proceed with 24 cases, or start with 12 as a smaller proof-of-concept?
5. **ACAT integration:** Is ACAT ablation required before Phase 2, or can it be deferred?

---

## Approval Workflow

**This document package requires:**

1. Z2 reads and reviews (1-2 days)
2. Clarifying questions answered (1 day)
3. Z2 decision: APPROVE / REQUEST REVISION / REJECT (1 day)

**If APPROVE:** Issue #737 moves to Phase 0 setup. Case manifest is preregistered. Evaluators are assigned and trained. Pilot kicks off.

**If REVISE:** Specific changes documented. Measurement contract updated. Re-submitted to Z2.

**If REJECT:** Alternative approach recommended. Return to Issue #737 for redesign.

---

## Signature and Authority

This measurement contract was drafted to support Issue #737 (SESSION-AERC-OUTPUT-QUALITY-001) by Claude in collaboration with Z2 governance requirements. It is submitted for **Z2 admission review and ratification**.

**Status:** ADMISSION_REQUESTED  
**Authority:** Z2 sole decision on approval/revision/rejection  
**No implementation proceeds** until explicitly approved.

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01TmUw2syFz8nJ8ZmoAQNAHM
