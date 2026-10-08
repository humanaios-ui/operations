# Translation Semantic Fidelity Rubric

**Issue:** #749 (Sub-issue of #747)  
**Title:** Semantic Fidelity Endpoint: Rater-Based Intent Predicate Preservation  
**Authority:** Z2 ratification required before Phase 1 pilot  
**Status:** PREREGISTRATION  
**Effective Date:** 2026-10-08

---

## Overview

This rubric operationalizes semantic fidelity measurement for the Translation Agent (humanaios-ui/lasting-light-ai). Semantic fidelity is measured as the **fraction of required intent predicates correctly preserved in the Translation Agent's output**.

**Primary Metric:** Intent Predicate Preservation (IPP)  
**Scoring Method:** Binary per-predicate (PRESERVED ✓ or LOST ✗)  
**Aggregate Score:** IPP = (preserved_predicates) / (total_required_predicates)  
**Threshold:** IPP ≥ 0.85 per domain (all three domains required for Phase 1 success)

---

## What Is an Intent Predicate?

An **intent predicate** is a core requirement or semantic constraint from the human's original request that **must be satisfied** for the Translation Agent's output to be considered correct.

Intent predicates are **observable and measurable facts about what the human wants**, not subjective assessments of quality or tone.

### Examples of Intent Predicates

#### Domain: Human Resource / Opportunity Finding

**Original Human Request:**  
"I'm looking for a free online learning resource about AI safety that I can complete in my spare time over the next few months."

**Intent Predicates:**
1. `RESOURCE_TYPE = LEARNING_MATERIAL` (must be educational, not just informational)
2. `DOMAIN = AI_SAFETY` (must focus on AI safety, not general AI or machine learning)
3. `COST = FREE` (must be free or subsidized; paid resources do not satisfy intent)
4. `MEDIUM = ONLINE` (must be accessible online; in-person resources do not satisfy)
5. `TIME_FLEXIBILITY = FLEXIBLE` (must allow completion over months; strict weekly deadlines do not satisfy)
6. `COMPLETION_REQUIREMENT = OPTIONAL` (can be completed at learner's pace; not mandatory intensive)

**Correct Translation Agent Output:**
```json
{
  "requirement_id": "req_001",
  "resource_type": "online_course",
  "domain_focus": "ai_safety",
  "cost": "free",
  "time_commitment": "flexible_self_paced",
  "estimated_duration_weeks": 8-12,
  "access_method": "web_based",
  "prerequisites": "none"
}
```

**Predicate Preservation Scoring:**
| Predicate | Translation Output | PRESERVED? |
|:---|:---|:---|
| RESOURCE_TYPE = LEARNING | `resource_type: online_course` | ✓ |
| DOMAIN = AI_SAFETY | `domain_focus: ai_safety` | ✓ |
| COST = FREE | `cost: free` | ✓ |
| MEDIUM = ONLINE | `access_method: web_based` | ✓ |
| TIME_FLEXIBILITY = FLEXIBLE | `time_commitment: flexible_self_paced` | ✓ |
| COMPLETION_REQUIREMENT = OPTIONAL | (implied; no deadline field) | ✓ |

**IPP Score:** 6/6 = 1.0 (100% fidelity)

---

#### Domain: Software Engineering / Code Review

**Original Human Request:**  
"I need to review this Python script to check if it handles file I/O errors correctly and doesn't open files without closing them."

**Intent Predicates:**
1. `LANGUAGE = PYTHON` (review must apply Python-specific rules, not JavaScript or Go)
2. `FOCUS_AREA = ERROR_HANDLING` (must assess error handling, not code style)
3. `SPECIFIC_CHECK = FILE_IO_ERRORS` (must examine file I/O exception handling)
4. `SPECIFIC_CHECK = RESOURCE_CLEANUP` (must verify files are closed after use)
5. `SCOPE = RESOURCE_MANAGEMENT` (not security audit, not performance optimization)

**Correct Translation Agent Output:**
```json
{
  "requirement_id": "req_002",
  "review_type": "code_review",
  "language": "python",
  "focus_areas": [
    "file_io_error_handling",
    "resource_cleanup",
    "exception_handling"
  ],
  "excluded_areas": ["style", "performance", "security"],
  "rubric": "code_review_file_handling_v1"
}
```

**Predicate Preservation Scoring:**
| Predicate | Translation Output | PRESERVED? |
|:---|:---|:---|
| LANGUAGE = PYTHON | `language: python` | ✓ |
| FOCUS_AREA = ERROR_HANDLING | `focus_areas: [...error_handling...]` | ✓ |
| SPECIFIC_CHECK = FILE_IO_ERRORS | `focus_areas: [...file_io_error_handling...]` | ✓ |
| SPECIFIC_CHECK = RESOURCE_CLEANUP | `focus_areas: [...resource_cleanup...]` | ✓ |
| SCOPE = RESOURCE_MANAGEMENT (not security/perf) | `excluded_areas: [security, performance]` | ✓ |

**IPP Score:** 5/5 = 1.0 (100% fidelity)

---

#### Domain: Software Engineering / Code Review (Failure Case)

**Original Human Request:**  
"I need to review this Python script to check if it handles file I/O errors correctly and doesn't open files without closing them."

**Incorrect Translation Agent Output (demonstrates LOST predicates):**
```json
{
  "requirement_id": "req_002_incorrect",
  "review_type": "code_review",
  "language": "nodejs",  // ✗ WRONG: JavaScript, not Python
  "focus_areas": [
    "code_style",  // ✗ WRONG: User asked for error handling, not style
    "performance"  // ✗ WRONG: User asked for I/O errors, not performance
  ],
  "excluded_areas": []
}
```

**Predicate Preservation Scoring:**
| Predicate | Translation Output | PRESERVED? |
|:---|:---|:---|
| LANGUAGE = PYTHON | `language: nodejs` | ✗ LOST |
| FOCUS_AREA = ERROR_HANDLING | `focus_areas: [style, performance]` | ✗ LOST |
| SPECIFIC_CHECK = FILE_IO_ERRORS | (not mentioned) | ✗ LOST |
| SPECIFIC_CHECK = RESOURCE_CLEANUP | (not mentioned) | ✗ LOST |
| SCOPE = RESOURCE_MANAGEMENT | `excluded_areas: []` (allows all scopes) | ✗ LOST |

**IPP Score:** 0/5 = 0.0 (0% fidelity — complete failure)

---

#### Domain: Decision Support / Resource Matching

**Original Human Request:**  
"We need to match this person with a job opportunity. The role must be remote, require no more than 20 hours per week, and pay at least $25/hour. They have availability Monday-Wednesday only."

**Intent Predicates:**
1. `TASK_TYPE = JOB_MATCHING` (must match person to job, not training or volunteer work)
2. `LOCATION = REMOTE` (must be fully remote; hybrid/on-site do not satisfy)
3. `HOURS_PER_WEEK <= 20` (must be part-time with specified upper bound)
4. `HOURLY_RATE >= 25` (must meet or exceed minimum wage requirement)
5. `SCHEDULE_CONSTRAINT = MON_WED_ONLY` (must accommodate Mon-Wed availability)
6. `MATCHING_SCOPE = PERSON_SPECIFIC` (must tailor to this individual's availability, not generic opportunities)

**Correct Translation Agent Output:**
```json
{
  "requirement_id": "req_003",
  "task": "job_matching",
  "candidate_constraints": {
    "location_preference": "remote_only",
    "availability": ["Monday", "Tuesday", "Wednesday"],
    "max_hours_per_week": 20,
    "minimum_hourly_rate": 25
  },
  "search_parameters": {
    "job_location": "remote",
    "hours_per_week_range": [1, 20],
    "compensation_minimum": "$25/hour",
    "schedule_compatibility": "must_fit_mon_wed"
  }
}
```

**Predicate Preservation Scoring:**
| Predicate | Translation Output | PRESERVED? |
|:---|:---|:---|
| TASK_TYPE = JOB_MATCHING | `task: job_matching` | ✓ |
| LOCATION = REMOTE | `location: remote_only` | ✓ |
| HOURS_PER_WEEK <= 20 | `max_hours_per_week: 20` | ✓ |
| HOURLY_RATE >= 25 | `compensation_minimum: $25/hour` | ✓ |
| SCHEDULE_CONSTRAINT = MON_WED | `schedule_compatibility: must_fit_mon_wed` | ✓ |
| MATCHING_SCOPE = PERSON_SPECIFIC | `candidate_constraints: [specific to this person]` | ✓ |

**IPP Score:** 6/6 = 1.0 (100% fidelity)

---

## Rater Instructions

### Before Scoring

1. **Read the original human request** (unmodified, as written by the human)
2. **Identify intent predicates** using the definitions above:
   - What MUST be true for this translation to be considered correct?
   - What are the observable, measurable constraints?
   - Ignore tone, politeness, and explanatory preamble
3. **List the predicates** as items in a table (see examples above)
4. **Do NOT score overall quality yet** — just list predicates

### Scoring Process

For each identified predicate, evaluate the Translation Agent's output:

**Question:** "Is this predicate correctly represented in the translation output?"

**Scoring Rule:**
- ✓ **PRESERVED:** The predicate is explicitly captured in the translation output in equivalent form
  - Example: Human says "free" → Translation says `cost: free` → PRESERVED
  - Example: Human specifies "Python" → Translation says `language: python` → PRESERVED
- ✗ **LOST:** The predicate is missing, contradicted, or incorrectly translated
  - Example: Human says "free" → Translation says `cost: paid` → LOST
  - Example: Human specifies "Python" → Translation says `language: javascript` → LOST
  - Example: Human says "remote" → Translation omits location entirely → LOST
  - Example: Human says "max 20 hours/week" → Translation says `hours_unlimited` → LOST

### Handling Edge Cases

**Case 1: Implied Predicates**
- If the human says "I need a job," the predicate `TASK_TYPE = JOB_SEARCH` is implied
- Implied predicates count if they are standard for the domain
- **Rule:** If a standard domain practitioner would infer the predicate, score it

**Case 2: Partial Preservation**
- If the human specifies "free or low-cost (under $50)" and the translation says `cost: free`, this is PARTIALLY preserved
- **Rule:** Score as PRESERVED only if the translation captures the constraint accurately; use LOST if constraint is omitted or contradicted

**Case 3: Unnecessary Elaboration**
- If the human says "Python script" and the translation adds `version: python3.10`, this is additional specification
- **Rule:** Score the core predicate (`LANGUAGE = PYTHON`) as PRESERVED; the additional version is acceptable elaboration

**Case 4: Absent Predicates (Not Specified by Human)**
- If the human does not specify a cost constraint, and the translation outputs `cost: free`, is this LOST?
- **Rule:** No. Score only predicates explicitly stated or standardly implied in the human's request. Do not penalize for additional, non-contradictory detail

---

## Inter-Rater Agreement Protocol

### Recruitment

- **Two independent domain experts per domain**
- **Criteria:** 3+ years experience in domain + no authorship of Translation Agent
- **Training:** Both raters jointly score 2–3 practice cases to calibrate
- **Blinding:** Each rater scores independently; results not disclosed until both complete

### Scoring Agreement Calculation

**Cohen's Kappa (κ):**

κ = (P_o − P_e) / (1 − P_e)

where:
- P_o = observed agreement (fraction of predicates where both raters mark same verdict)
- P_e = expected agreement by chance (both mark PRESERVED or both mark LOST by random guess)

**Target:** κ ≥ 0.70 per domain

**Disagreement Handling:**
- If κ < 0.70, investigate disagreements:
  - Did raters identify different predicates? (refine rubric)
  - Did raters disagree on whether a predicate was preserved? (clarify scoring rule)
- Resolve by: Raters meet, discuss disagreement, re-score jointly (final score used for pilot analysis)

---

## Pilot Testing Plan

**Sample Size:** 10 human intents per domain × 3 domains = 30 total test cases

**Sampling Method:** Random selection from three domain request types:
1. Human Resource / Opportunity finding (N=10)
2. Software Engineering / Code review (N=10)
3. Decision Support / Resource matching (N=10)

**Procedure:**
1. For each test case, Translation Agent produces output
2. Rater 1 independently identifies predicates and scores
3. Rater 2 independently identifies predicates and scores
4. Calculate IPP per case: IPP_case = (preserved_predicates) / (total_predicates)
5. Calculate κ (inter-rater agreement)
6. Compute domain aggregate: IPP_domain = mean(IPP_case) across 10 cases per domain

**Success Criteria:**
- IPP ≥ 0.85 per domain (minimum 85% of predicates preserved on average)
- κ ≥ 0.70 per domain (inter-rater agreement acceptable)

**Failure Triggers (Disconfirm Semantic Fidelity):**
- If IPP < 0.85 on any domain: Translation Agent semantic fidelity insufficient
- If κ < 0.70 on any domain: Rubric is ambiguous; rater training needed before Phase 1

---

## Scoring Template

Use this template for each test case:

```markdown
## Test Case: [req_NNN]
**Domain:** [Human Resource / Software Engineering / Decision Support]
**Original Request:** [Verbatim human request]
**Translation Output:** [JSON/structured output from Translation Agent]

### Identified Predicates

| # | Predicate | Definition | Preserved? | Notes |
|:---|:---|:---|:---|:---|
| 1 | PREDICATE_A | Description of what must be true | ✓/✗ | Justification |
| 2 | PREDICATE_B | Description | ✓/✗ | Justification |
| ... | ... | ... | ... | ... |

### Scoring Summary
- Total predicates identified: N
- Preserved: M
- Lost: N-M
- **IPP = M/N = [0.00–1.00]**

### Notes
[Any observations about quality, ambiguities, or edge cases]
```

---

## Expected Outcomes

### Scenario A: High Fidelity (IPP ≥ 0.85 across all domains)
- **Result:** Translation Agent preserves intent reliably
- **Implication:** Phase 1 federated integration can proceed; semantic round-trip loss is acceptable
- **Action:** Proceed to Phase 2 architecture work

### Scenario B: Moderate Fidelity (0.70 ≤ IPP < 0.85 on one domain)
- **Result:** Translation Agent struggles with one domain's complexity
- **Implication:** Domain-specific refinement needed
- **Action:** File sub-issue for that domain; defer Phase 1 until resolved

### Scenario C: Low Fidelity (IPP < 0.70 on any domain)
- **Result:** Translation Agent fundamentally misunderstands human requests
- **Implication:** Federated integration not viable without Translation Agent redesign
- **Action:** REJECT Phase 1 architecture; recommend Translation Agent redesign

---

## Sign-Off

This rubric is preregistered for #749 sub-issue. Raters will use this rubric to measure semantic fidelity during Phase 1 vertical slice (10 cases per domain, independent assessment, Cohen's kappa ≥0.70 target).

**Effective Date:** 2026-10-08  
**Authority:** Z2 ratification required before pilot  
**Status:** PREREGISTERED (cannot be modified post-hoc without Z2 justification)

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01TmUw2syFz8nJ8ZmoAQNAHM
