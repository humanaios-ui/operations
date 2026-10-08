# AERC Phase 1 Stopping Rules and Decision Thresholds

**Research Proposal:** Issue #737  
**Authority:** Z2 may invoke stopping rules at any point during Phase 1  
**Status:** Preregistered; cannot be modified post-hoc without justification  

---

## 1. Hard Stop Conditions (Halt Pilot Immediately)

If **any** of these conditions are met during Phase 1, the pilot **halts immediately**. A decision to continue requires explicit Z2 override and documentation of why the rule is suspended.

### Rule 1.1: Measurement Reliability Failure
**Trigger:** Inter-rater agreement (Cohen's kappa) on primary dimension falls **below 0.60**  
**Action:** Stop scoring; revise rubric; retry on practice set

### Rule 1.2: False-Hold Rate Exceeds Tolerance
**Trigger:** False-hold rate exceeds **20%** across all cases  
**Action:** Stop; audit blocking logic; revise disposition heuristics

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
**Trigger:** Significant improvement in only one domain; not in other two  
**Result:** Domain-stratified findings published; recommend REVISE (domain-specific) or REJECT

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
**Trigger:** Measured benefit (e.g., +8% correctness) offset by cost  
**Result:** Compute cost-benefit ratio; recommend PROCEED with cost acknowledgment or REJECT

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

| Metric | Target | Acceptable Range |
|--------|--------|---|
| Token consumption (C vs B) | ≤ +10% | +5% to +15% |
| Blinding integrity | 100% | ≥ 98% |
| Data preservation | 100% | ≥ 99% |
| Evaluator credentials | 100% | ≥ 95% |

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
