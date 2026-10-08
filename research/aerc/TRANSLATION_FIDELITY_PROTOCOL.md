# Translation Semantic Fidelity: Preregistered Measurement Protocol

**Issue:** #749 (Sub-issue of #747)  
**Title:** Semantic Fidelity Endpoint: Round-Trip Measurement Protocol  
**Authority:** Z2 ratification required before Phase 1 pilot begins  
**Status:** PREREGISTRATION  
**Registration Date:** 2026-10-08  
**Falsifier:** "If Translation Agent round-trip semantic fidelity falls below the preregistered threshold, the federated integration is not ready for Phase 2."

---

## 1. Primary Endpoint Definition

### Metric: Intent Predicate Preservation (IPP)

**What is measured:** The fraction of core human-intent requirements that survive intact through the Translation Agent's translation process.

**Measurement formula:**

```
IPP_per_case = (# predicates marked PRESERVED) / (# predicates identified in human request)
IPP_per_domain = mean(IPP_per_case) across all cases in domain
IPP_overall = mean(IPP_per_domain) across all three domains
```

**Minimum unit:** Binary per-predicate (PRESERVED ✓ or LOST ✗) scored by independent rater using TRANSLATION_FIDELITY_RUBRIC.md

### Threshold: IPP ≥ 0.85 per domain

**Definition:** For Phase 1 vertical slice to succeed, the Translation Agent must preserve ≥85% of intent predicates on average across each of the three domains (Human Resource, Software Engineering, Decision Support).

**Falsification trigger:** If IPP < 0.85 on ANY domain, semantic fidelity is insufficient; federated integration cannot proceed to Phase 2 without Translation Agent redesign.

**Why 0.85?**
- 85% preservation means 15% of intent predicates are lost or misinterpreted on average
- This allows minor elaborations or reformulations while catching major semantic divergence
- Below 0.85, human requests are systematically misunderstood; above 0.85, users can tolerate minor translation ambiguities
- Standard in UX research for "acceptable error rate" in automated interpretation (ISO 9241 standards)

---

## 2. Complementary Measures

These metrics provide context but do **not** override the primary IPP endpoint.

### Complementary Measure 1: Human Correction Rate

**What is measured:** On first presentation of the Translation Agent's output, how often does a human correct or clarify the translation?

**Measurement formula:**

```
HCR = (# user corrections requested) / (# translations presented)
```

**Acceptable range:** HCR ≤ 10% per domain

**Why complementary, not primary?** Human correction frequency reflects user friction but not measurement validity. A translation with 80% IPP might still result in 0% user corrections if the 20% loss is non-critical detail.

### Complementary Measure 2: Round-Trip Latency

**What is measured:** Wall-clock time from human request submission to Translation Agent output delivery.

**Measurement formula:**

```
RTL = (time_output_delivered) − (time_request_submitted)
```

**Acceptable threshold:** RTL ≤ 500ms per case

**Why complementary, not primary?** Latency affects user experience but not semantic preservation. A slow translation that perfectly preserves intent (IPP=1.0) is better than a fast translation that loses intent (IPP=0.6).

---

## 3. Rater Specification

### Rater Roles

**Two independent domain experts per domain:**
- At least 3 years domain experience
- No authorship of Translation Agent code
- No prior involvement in Phase 1 planning
- Signed conflict-of-interest declaration

### Rater Training

**Pre-scoring calibration (mandatory):**
1. Joint training session on TRANSLATION_FIDELITY_RUBRIC.md (1 hour)
2. Raters score 2–3 practice cases together
3. Discuss any predicate identification disagreements
4. Agree on predicate list before independent scoring begins

**Training success criterion:** Both raters identify the same predicates on practice cases (≥90% overlap)

### Blinding Mechanism

- Rater 1 scores independently; results sealed
- Rater 2 scores independently; results sealed
- Results not disclosed to each other until both complete all cases
- Translation Agent author does not know which cases are being scored or by whom

---

## 4. Sample Specification

### Sample Composition

**Total sample size:** 30 test cases (10 per domain)

**Domain breakdown:**

| Domain | N Cases | Test Type | Example |
|:---|:---|:---|:---|
| Human Resource / Opportunity Finding | 10 | Request: "Find me a free online AI safety course I can do over 3 months" | Matching person to resources, calendars, cost constraints |
| Software Engineering / Code Review | 10 | Request: "Review this Python script for file I/O error handling and resource cleanup" | Technical specifications, language, focus areas |
| Decision Support / Resource Matching | 10 | Request: "Match this person to a remote part-time job (20h/week, $25/h+, Mon-Wed only)" | Person-specific constraints, schedule compatibility |

### Sampling Method

**Random stratified sampling:**
1. Generate 10 unique, realistic human requests per domain (or source from actual humanaios.ai logs if available)
2. Randomly select 10 test cases per domain
3. For each case, collect Translation Agent's output (from Phase 1 vertical slice)
4. Assign to raters in randomized order

### Representativeness

Requests should span:
- Simple cases (few predicates; low ambiguity)
- Complex cases (many predicates; competing constraints)
- Edge cases (implicit predicates; partially specified intent)

**Ensure no rater sees the same request twice**

---

## 5. Scoring Procedure

### Step-by-Step Process

**For each test case:**

1. **Rater reads original human request** (verbatim, unmodified)
2. **Rater identifies intent predicates** using TRANSLATION_FIDELITY_RUBRIC.md definitions
   - Predicate must be observable, measurable, and core to satisfying the request
   - Ignore tone, politeness, elaboration
   - Document predicate list with brief definition
3. **Rater examines Translation Agent output** (JSON/structured format from agent)
4. **Rater scores each predicate independently:**
   - ✓ PRESERVED: Predicate correctly represented in translation output
   - ✗ LOST: Predicate missing, contradicted, or incorrectly translated
5. **Rater calculates IPP for this case:** (preserved count) / (total predicate count)
6. **Rater documents notes:** Any ambiguities, edge cases, or scoring decisions

### Scoring Template

See TRANSLATION_FIDELITY_RUBRIC.md "Scoring Template" section for detailed format.

---

## 6. Inter-Rater Agreement Calculation

### Cohen's Kappa (κ)

**Definition:**

```
κ = (P_o − P_e) / (1 − P_e)

where:
  P_o = observed agreement (fraction of predicates where both raters mark same verdict)
  P_e = expected agreement by chance (0.5 for binary scoring)
```

**Interpretation:**
- κ ≥ 0.70: Substantial agreement; rubric is clear and raters understand it well
- κ 0.50–0.70: Moderate agreement; possible ambiguities in rubric or predicate identification
- κ < 0.50: Poor agreement; rubric needs revision before proceeding

**Target threshold:** κ ≥ 0.70 per domain

### Disagreement Resolution

**If κ < 0.70 on any domain:**
1. Raters meet (without Translation Agent author present)
2. Identify cases with highest disagreement
3. Discuss predicate definitions: Were they clear? Did raters identify same predicates?
4. Discuss scoring: Where did raters diverge on PRESERVED vs. LOST?
5. Revise rubric if necessary (e.g., clarify what counts as "partial preservation")
6. Option: Re-score subset of cases with revised rubric to confirm κ improves

**If κ remains < 0.70:**
- Rubric is too ambiguous for Phase 1 pilot
- Recommendation: REVISE (improve rubric clarity) before proceeding

---

## 7. Analysis Plan

### Primary Analysis

**For each domain:**

1. **Calculate IPP_per_case** for each of the 10 test cases
2. **Calculate IPP_per_domain** = mean(IPP_per_case) across 10 cases
3. **Calculate 95% confidence interval** around IPP_per_domain (bootstrap or exact binomial)
4. **Report Cohen's κ** for inter-rater agreement

**Success criterion:**
- IPP_per_domain ≥ 0.85 for all three domains, AND
- κ ≥ 0.70 for all three domains

### Secondary Analysis

**Complementary metrics:**

1. **Human Correction Rate (HCR)** per domain
   - Count cases where human corrected translation
   - HCR = (# corrections) / (# cases)
   - Target: HCR ≤ 0.10

2. **Round-Trip Latency (RTL)** per case
   - Mean and 95th percentile RTL per domain
   - Target: mean RTL ≤ 500ms; P95 RTL ≤ 1000ms

### Sensitivity Analysis

**Explore sources of IPP variation:**

1. **By predicate type:** Some predicates more often lost (e.g., constraints) vs. preserved (e.g., domain)?
2. **By case complexity:** Do cases with more predicates have lower IPP?
3. **By rater:** Does one rater consistently score higher/lower IPP? (May indicate calibration issue)

---

## 8. Success & Failure Scenarios

### Scenario A: IPP ≥ 0.85, κ ≥ 0.70 (All Domains)

**Result:** ✅ **SEMANTIC FIDELITY VERIFIED**

**Interpretation:**
- Translation Agent reliably preserves human intent through round-trip translation
- Inter-rater agreement is high; rubric is clear and reproducible
- Semantic fidelity acceptable for Phase 1 federated integration

**Action:**
- ✅ Proceed to Phase 2 architecture work
- ✅ No further Translation Agent redesign needed for this dimension
- ⚠️ Monitor HCR and latency in full-scale Phase 1; may refine based on complementary measures

---

### Scenario B: IPP < 0.85 on One Domain Only

**Result:** ⚠️ **DOMAIN-SPECIFIC FIDELITY LOSS**

**Interpretation:**
- Translation Agent struggles with one domain's semantic complexity
- Other domains sufficient for Phase 1, but incomplete coverage
- Requires domain-specific refinement

**Action:**
- File sub-issue: "[ARCH-749-REVISION] Improve Translation Fidelity for [Domain]"
- Recommend: Redesign Translation Agent for low-fidelity domain; test with new rubric
- Decision: Proceed with Phase 1 for high-fidelity domains only, OR defer entire Phase 1 until all domains meet threshold

---

### Scenario C: IPP < 0.85 on Multiple Domains

**Result:** ❌ **SEMANTIC FIDELITY INSUFFICIENT**

**Interpretation:**
- Translation Agent systematically misunderstands human requests across multiple domains
- Federated integration not viable without major Translation Agent redesign

**Action:**
- ❌ **REJECT Phase 1 architecture** per Issue #747 acceptance criteria
- File sub-issue: "[ARCH-749-REDESIGN] Translation Agent Fundamental Redesign Required"
- Recommendation: Return to Translation Agent code-level redesign; retest semantic fidelity before Phase 1 is reconsidered

---

### Scenario D: κ < 0.70 (Low Inter-Rater Agreement)

**Result:** ⚠️ **MEASUREMENT VALIDITY CONCERN**

**Interpretation:**
- Rubric is ambiguous; raters do not agree on predicate identification or scoring
- Cannot conclude anything about Translation Agent quality (measurement tool is broken)

**Action:**
- Raters meet; revise rubric for clarity
- Option 1: Re-score subset of cases to confirm κ improves
- Option 2: Recruit new raters; check if training/calibration was insufficient
- **Do not proceed with Phase 1 until κ ≥ 0.70**

---

## 9. Falsification Rule

**Hard Falsifier (Phase 1 cannot proceed):**

```
IF (IPP < 0.85 on ANY domain) OR (κ < 0.70 on ANY domain)
THEN Translation Agent semantic fidelity is insufficient
AND Phase 1 federated integration cannot proceed to Phase 2 without redesign
```

**Soft Consequence (Phase 1 can proceed with caveats):**

```
IF HCR > 0.10 on any domain OR RTL > 500ms mean
THEN user friction or latency cost must be acknowledged
AND Phase 2 write-phase authorization requires user impact study
```

---

## 10. Timeline

**Pilot Testing Phase (estimated 2 weeks):**

| Task | Duration | Responsible |
|:---|:---|:---|
| Recruit & train raters (2 per domain) | 3 days | Phase 1 coordinator |
| Prepare 30 test cases | 2 days | Phase 1 coordinator |
| Rater 1: Score 30 cases | 5 days | Rater 1 |
| Rater 2: Score 30 cases | 5 days | Rater 2 |
| Calculate IPP, κ, confidence intervals | 2 days | Analyst |
| Analyze results; draft report | 3 days | Analyst |
| **Total wall-clock time** | ~2 weeks | Parallel where possible |

**Milestone Gate:** Results due before Phase 1 full pilot begins; Z2 reviews before full-scale deployment.

---

## 11. Approval & Ratification

**This protocol is preregistered and cannot be modified post-hoc without Z2 justification.**

**Required approvals before pilot:**
- [ ] Z2 (Night) approves IPP ≥ 0.85 threshold
- [ ] Z2 approves κ ≥ 0.70 threshold
- [ ] Raters identified and trained
- [ ] Test cases finalized
- [ ] TRANSLATION_FIDELITY_RUBRIC.md accepted

**After pilot:**
- [ ] Results reported with all supporting data
- [ ] Z2 reviews findings
- [ ] Z2 decision: Proceed to Phase 2 / Revise / Reject

---

## Sign-Off

This protocol is preregistered for #749 sub-issue. It operationalizes semantic fidelity measurement for Phase 1 vertical slice of the federated architecture (Issue #747).

**Effective Date:** 2026-10-08  
**Authority:** Z2 ratification required before pilot begins  
**Status:** PREREGISTERED (cannot be modified post-hoc without Z2 justification)

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01TmUw2syFz8nJ8ZmoAQNAHM
