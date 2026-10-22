# AERC Phase 1 Stopping Rules and Decision Thresholds

**Research Proposal:** Issue #737  
**Authority:** Z2 may invoke stopping rules at any point during Phase 1  
**Status:** Preregistered; cannot be modified post-hoc without justification  

---

## 1. Hard Stop Conditions (Halt Pilot Immediately)

If **any** of these conditions are met during Phase 1, the pilot **halts immediately**. A decision to continue requires explicit Z2 override and documentation of why the rule is suspended.

### Rule 1.1: Measurement Reliability Failure
**Thresholds (two-phase):**
- **Pre-pilot gate:** κ ≥ 0.65 required on all domains after rater training on practice cases (PREREGISTRATION_PROTOCOL_PHASE_1.md Section 4); κ < 0.65 → revise rubric, retry on practice cases before pilot launch
- **In-pilot hard stop:** κ < 0.60 during pilot scoring (triggers immediate halt)  
- **Interval [0.60, 0.65):** Disconfirms pre-pilot adequacy; pilot cannot launch
**Trigger:** Inter-rater agreement (Cohen's kappa) on primary dimension falls **below 0.60** during pilot scoring  
**Action:** Stop scoring immediately; revise rubric; re-score practice set before proceeding

### Rule 1.2: False-Hold Rate Exceeds Tolerance
**Metric:** (# legitimate answers marked HOLD_FOR_EVIDENCE but output was correct) / (# answers reviewed across all cases)  
**Thresholds:**
- **0% to 15%:** Success (secondary efficacy criterion passes)
- **> 15% to 20%:** Disconfirming outcome (secondary efficacy fails; system utility degraded; recommend REVISE); pilot completes but result is negative
- **> 20%:** Hard stop (in-pilot halt); audit blocking logic; revise disposition heuristics immediately  
**Action (hard stop):** Stop pilot immediately; escalate to Z2; audit blocking logic; recommend REVISE  
**Action (disconfirming, 15-20% band):** Pilot completes; secondary efficacy failed; recommend REVISE before Phase 2

### Rule 1.3: Experimental Confounding Exceeds Tolerance
**Trigger:** More than **25% of cases (>6 cases)** marked confounded  
**Action:** Stop; analyze confounding sources; redesign or reduce scope

### Rule 1.4: Governance or Safety Violation
**Trigger:** Unauthorized action attempts, forged evidence, evaluator self-certification, consequence-detection failures on critical hazards  
**Action:** Stop immediately; escalate to Z2 governance review

---

## 2. Efficacy Failure Conditions

If **any** of these occur, pilot completes but efficacy claim **fails**. Results published as "no evidence of improvement."

### Rule 2.1: No Improvement in Verified Correctness
**Trigger:** Primary efficacy < 50% OR no statistically significant difference (95% CI includes 0)  
**Result:** Negative finding; recommend REVISE or REJECT

### Rule 2.2: Improvement Explained by Additional Tokens/Attempts
**Trigger:** Improvement fully explained by >20% higher token use or additional revision opportunity  
**Result:** Confound documented; recommend REVISE (isolate mechanism) or REJECT

### Rule 2.3: Improvement Limited to Single Domain
**Unified criterion (PREREGISTRATION_PROTOCOL_PHASE_1.md Section 1.3, item 5):** Primary efficacy (verified correctness improvement) must be ≥ 50% in at least TWO of three primary domains (Factual Reasoning and Software Engineering; Decision-Support evaluated separately)  
**Trigger:** Primary efficacy < 50% in more than ONE of the primary domains (i.e., improvement achieved in only one domain, or zero domains) → generalizability fails  
**Result:** Domain-stratified findings published; recommend REVISE (domain-specific approach) or REJECT

---

## 3. Cost-Benefit Failure Conditions

Efficacy met but **deployment not recommended** without cost mitigation.

### Rule 3.1: Excessive Latency Overhead
**Trigger:** Arm C time exceeds Arm B by > 50%  
**Result:** Document latency cost; recommend PROCEED with caveat or REVISE

### Rule 3.2: Excessive Human Review Burden
**Trigger:** Average review time per HOLD exceeds 10 minutes OR queue aging > 4 hours  
**Result:** Document review burden; recommend PROCEED with operational constraint or REVISE

### Rule 3.3: Improvement vs. Cost Unfavorable
**Trigger:** Measured benefit offset by cost (cost-benefit ratio < 1.0)

**Cost-Benefit Calculation:**
```
Cost-Benefit Ratio = (Benefit Score) / (Cost Score)

Benefit Score = (Primary Efficacy improvement %) × (1 + domain_count_bonus)
                where domain_count_bonus = 0 if 1 domain, +0.2 if 2+ domains

Cost Score = (1 + latency_overhead_fraction) × (1 + review_time_per_case / 300)
             where 300 = budget threshold in seconds

Example: +8% efficacy over 2 domains, +30% latency, 5 min review time
         = (8 × 1.2) / (1.30 × 1.017) = 9.6 / 1.32 ≈ 7.3 (favorable)

Threshold: Ratio ≥ 1.0 for favorable recommendation
```

**Result:** Compute cost-benefit ratio; if <1.0, recommend PROCEED with cost acknowledgment or REJECT

---

## 4. Precision and Reliability Thresholds

### Rule 4.1: Minimum Reproducibility
**Threshold:** Scoring reproducibility ≥ 90% (±0.05 deviation on re-score)  
**If not met:** Publish with uncertainty caveat; mark "exploratory; replication needed"

### Rule 4.2: Minimum Evaluator Coverage
**Threshold:**  
- Factual: Automated + ≥ 1 expert  
- Engineering: Automated + ≥ 2 blinded reviewers  
- Decision-Support: ≥ 3 domain experts

**If not met:** Do not report primary findings for that domain

### Rule 4.3: Minimum Case Completion
**Threshold:** All 24 cases scored on ≥ 6 of 7 dimensions  
**If not met:** Report as "analysis incomplete"

---

## 5. Secondary Metric Acceptance Criteria

| Metric | Target | Definition |
|--------|--------|---|
| Token consumption (C vs B) | ≤ +10% | AERC must not exceed generic revision's token budget by more than 10% on average; individual cases >20% mark as CONFOUNDED. Prespecified in PREREGISTRATION_PROTOCOL_PHASE_1.md Section 3. |
| Blinding integrity | ≥ 98% | Evaluators must not know arm identity on ≥98% of cases. Document any breaches. |
| Data preservation | ≥ 99% | All case records, evaluator scores, and challenge events must be timestamped and retained. ≥99% of records must be recoverable. |
| Evaluator credentials | ≥ 95% | All evaluators must have documented credentials and conflict-of-interest declarations before scoring begins. ≥95% of all scores must be attributed to credentialed evaluators. |

---

## 6. ACAT Ablation Decision Point

**ACAT Trigger Outcomes:**

1. **AUROC ≥ 0.65** → Include ACAT in Phase 2
2. **AUROC < 0.55** → Exclude ACAT
3. **0.55 ≤ AUROC < 0.65** → Defer for future work

---

## 7. Publication and Decision Matrix

| Efficacy | Reliability | Cost-Benefit | Recommendation |
|----------|----------|---|---|
| ✅ High (>60%) | ✅ High (κ>0.70) | ✅ Favorable | **PROCEED to Phase 2** |
| ✅ High | ✅ High | ❌ Unfavorable | **PROCEED with cost caveat** |
| ✅ Moderate (50-60%) | ✅ High | ✅ Favorable | **REVISE** (domain-specific or tuning) |
| ❌ Low (<50%) | ✅ High | ➖ N/A | **REJECT** |
| ❌ Low | ❌ Low (κ<0.60) | ➖ N/A | **REJECT** |

---

## 8. Timeline Constraints

| Phase | Deadline | Action |
|-------|----------|--------|
| Baseline (Arm A) | Week 1–2 | Complete all evaluations |
| Generic revision (Arm B) | Week 2–3 | Complete revisions and scoring |
| AERC (Arm C) | Week 3–4 | Complete AERC passes and scoring |
| Inter-rater check | Week 4 | Compute kappa; halt if <0.60 |
| Primary analysis | Week 5 | Efficacy calculation; stopping rule audit |
| Report draft | Week 5–6 | Findings and decision options |
| Z2 decision gate | Week 6 | Admit / revise / reject |

**If any checkpoint exceeds 2-week buffer, escalate to Z2.**

---

## Signature Block

These stopping rules are preregistered and cannot be modified post-hoc without Z2 justification.

**Status:** ADMISSION_REQUESTED  
**Authority:** Z2 sole decision on rule invocation

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
