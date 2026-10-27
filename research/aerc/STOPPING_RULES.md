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
                where:
                  Primary Efficacy improvement % = (Efficacy_C − Efficacy_A) / Efficacy_A × 100
                    (absolute percentage-point change in verified correctness, C vs A)
                  domain_count_bonus = 0 if 1 domain, +0.2 if 2+ domains

Cost Score = (1 + latency_overhead_fraction) × (1 + review_time_per_case / 300)
             where:
               latency_overhead_fraction = (Time_C − Time_B) / Time_B
                 (relative latency increase, C vs B, handling time only)
               review_time_per_case = average minutes per HOLD decision × 60 seconds
               300 seconds = 5 min budget threshold

Example: 
  Baseline (Arm A): 60% efficacy; Generic (Arm B): 62% efficacy; AERC (Arm C): 68% efficacy
  Improvement: (68% − 60%) / 60% × 100 = 13.3% over 2 domains
  Benefit Score: (13.3 × 1.2) = 15.96
  Latency overhead: 30% (Time_C = 130% of Time_B)
  Review time: 5 min = 300 sec per HOLD
  Cost Score: (1.30) × (1.0 + 300/300) = 1.30 × 2.0 = 2.6
  Ratio: 15.96 / 2.6 ≈ 6.1 (favorable)

Threshold: Ratio ≥ 1.0 for favorable recommendation
```

**Calculation Details:**
1. **Efficacy Measurement:** Efficacy_A, Efficacy_B, Efficacy_C computed per PREREGISTRATION_PROTOCOL_PHASE_1.md (Section 7); use Primary Efficacy (scoreable domains only)
2. **Latency:** Measure handling time (Time_A, Time_B, Time_C) for equivalent task batches; exclude queue wait time
3. **Review Time:** Average human review time per HOLD decision (minutes); only count cases where HOLD_FOR_EVIDENCE was issued and then reviewed
4. **Domain Bonus:** If improvement is ≥ 50% in 2+ primary domains (per Rule 2.3), apply +0.2 bonus; otherwise 0

**Result:** Compute cost-benefit ratio; if <1.0, recommend PROCEED with cost acknowledgment or REJECT

---

## 4. Precision and Reliability Thresholds

### Rule 4.1: Minimum Reproducibility
**Threshold:** Scoring reproducibility ≥ 90% (±0.05 deviation on re-score)  
**If not met:** Publish with uncertainty caveat; mark "exploratory; replication needed"

### Rule 4.2: Minimum Evaluator Coverage
**Threshold:**  
- Factual: Automated (fact-check API) + ≥ 2 domain experts (required for κ calculation per PREREGISTRATION_PROTOCOL_PHASE_1.md Section 6)
- Engineering: Automated (test suite) + ≥ 2 blinded code reviewers  
- Decision-Support: ≥ 3 domain experts (primary panel) + ≥ 1 external reviewer

**Enforcement:** All three domains must meet minimum coverage before pilot scoring begins. If pre-pilot evaluator availability falls below threshold after training, escalate to Z2 for decision on scope reduction or schedule extension.

**If not met during pilot:** Do not report primary findings for that domain; mark as "analysis incomplete" and recommend Phase 2 redesign

### Rule 4.3: Minimum Case Completion
**Threshold:** All 24 cases scored on ≥ 6 of 7 quality dimensions  
**Seven Quality Dimensions** (per PREREGISTRATION_PROTOCOL_PHASE_1.md Section 5):
1. Verified Correctness (primary basis for efficacy)
2. Material Claim Grounding (sources, evidence)
3. Confidence Calibration (appropriateness of certainty expressed)
4. Task Utility (usefulness to human decision-maker)
5. Material Consequence Detection (hazard/harm awareness)
6. Appropriate Authority Deference (respects human oversight)
7. User Autonomy Preservation (preserves human choice)

**Enforcement:** Each case must have scores on at least 6 of these 7 dimensions. If a dimension is not applicable to a specific case (marked N/A), it counts as applied (does not reduce the count below 6 required). Missing data (no score and not N/A) on a dimension counts against the case.

**If not met:** Report as "analysis incomplete"; do not report primary findings for that case in the main analysis; conduct post-hoc sensitivity analysis to assess whether incomplete scoring affects conclusions

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

**Target Timeline (Ideal Case: 6-week pilot)**

| Phase | Deadline | Action |
|-------|----------|--------|
| Baseline (Arm A) | Week 1–2 | Complete all evaluations |
| Generic revision (Arm B) | Week 2–3 | Complete revisions and scoring |
| AERC (Arm C) | Week 3–4 | Complete AERC passes and scoring |
| Inter-rater check | Week 4 | Compute kappa; halt if <0.60 |
| Primary analysis | Week 5 | Efficacy calculation; stopping rule audit |
| Report draft | Week 5–6 | Findings and decision options |
| Z2 decision gate | Week 6 | Admit / revise / reject |

**Realistic Timeline (With 2-Week Buffer: 8-week pilot)**

Expect evaluator availability delays, rater calibration iterations, and scoring slowdowns to add 1-2 weeks. Actual pilot typically completes in weeks 1–6 of scoring with weeks 7–8 for analysis and reporting. Z2 decision remains at Week 8 (post-buffer).

**Escalation Rule:**
- If any checkpoint (Arm A start, Arm C completion, inter-rater check, primary analysis) exceeds its deadline by >1 week, escalate to Z2 for schedule reassessment
- If buffer exhausted (pilot enters Week 9), automatic halt; Z2 decides on extension, scope reduction, or interim findings

**Buffer Allocation:**
- Week 2–3: Evaluator availability (rater drop-outs, conflicts)
- Week 4–5: Rater calibration and practice case scoring
- Week 6–8: Scoring completion and inter-rater check re-runs if κ<0.65
- Week 8: Analysis and final report; Z2 decision the following week

---

## Signature Block

These stopping rules are preregistered and cannot be modified post-hoc without Z2 justification.

**Status:** ADMISSION_REQUESTED  
**Authority:** Z2 sole decision on rule invocation

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
