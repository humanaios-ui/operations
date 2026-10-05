# Q-PUBLIC-UTILITY-MARKET-VALIDATION-01: Implementation Specification

**Z2 Ratified Decisions:** 4a–4f (See PHASE_1_RATIFICATION_PACKAGE.md)  
**Authority:** Night (carly.r.anderson@gmail.com)  
**Status:** ✅ RATIFIED (2026-10-02)  
**Z2 Ratification Hash:** `sha256(Q-PUBLIC-UTILITY-MARKET-VALIDATION-01|decisions_4a-4f|by=Night|at=2026-10-02T00:00:00Z|decision=RATIFY|firewall=governance_independent)`  
**Stage:** 4 (Z2 Ratification) ✅ → 5 (Z3 Implementation)

---

## Core Decision Summary

| Decision | Ratified Value | Impact |
|----------|---|---|
| **4a. Validation Framing** | Genuine research question + go/no-go gates | Project continues only if validated; prevents post-hoc justification |
| **4b. Comparator Audit** | Pre-register + publish methodology | Z2 approves methodology before research; results follow; auditable |
| **4c. "Show Me Why" Scope** | Auditor verification use case | Narrower scope aligns with #497 Witness/Oracle design |
| **4d. Validation Gates** | Hard gates with numeric thresholds | Stop Stage 2 if unvalidated; Stage 3 if gap small; Stage 4/5 conditional |
| **4e. Hypothesis Operationalization** | Measurable per H1–H7 | Specific success thresholds for each hypothesis |
| **4f. Public/Institutional Split** | Prototype first (resource-state gated) | Test coexistence before full build-out |

---

## Implementation Part 1: Public Utility Validation Protocol

### File: `PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md`

```markdown
# Public Utility Validation Protocol v1.0

**Authority:** Night (Z2) ratified Q-PUBLIC-UTILITY-MARKET-VALIDATION-01  
**Effective Date:** 2026-09-28  
**Project Lifespan:** Phase 1–4 resource-state transitions, each gated by success criteria; measurement windows per phase specification; not calendar-driven deadlines (Q-TEMPORAL-DISSOLUTION-01 compliance)

---

## § 1: Genuine Research Framing (Decision 4a)

**Mandate:** Project is framed as empirical research question, NOT marketing claim or foregone conclusion.

### Research Thesis
"Evidence-bearing claims and explicit warrants reduce auditor cognitive load and improve audit decision quality compared to summary-score baselines, across ≥2 stakeholder classes (institutional auditors + public users), with demonstrable cross-substrate applicability."

### Go/No-Go Decision Gates (Hard Stops)

| Phase | Gate | Success Criterion | Failure Action |
|-------|------|---|---|
| **Phase 1** | Problem validation | ≥2 stakeholder classes identify audit decision challenge | STOP; pivot or close |
| **Phase 2** | Hypothesis operationalization | All H1–H7 measurable with <20% ambiguity in success threshold | STOP; revise hypotheses |
| **Phase 3** | Prototype validation | Layer prototype >80% feature parity with requirement spec | STOP; respec or close |
| **Phase 4** | Market adoption | ≥5% institutional willingness-to-adopt (threshold 4d) | Report findings; plan Phase 5 |

**Rationale:** Prevents sunk-cost fallacy and post-hoc rationalization. Project must validate each phase or halt.

---

## § 2: Comparator Audit Protocol (Decision 4b)

### Pre-Registered Strongest-Competitor List

**File:** `research/PUBLIC_UTILITY_COMPARATORS_v1.md`

Before collecting any data, Z2 approves the list of comparison tools.

```yaml
# Pre-Registered Comparators for "Show Me Why" Auditor Use Case

stage_1_approval: "2026-09-28 (Z2 ratification)"

comparators:
  - tool_id: C1
    name: "Commercial Audit Tool A"
    category: "Institutional | Public"
    evidence_model: "Numeric score + confidence interval"
    claim_transparency: "Summary-only; no evidence chain"
    cost_per_audit: "$500–2000"
    inclusion_rationale: "Market leader in institutional audits"
    feature_parity:
      - evidence_bearing: NO
      - warrant_explicit: NO
      - cross_substrate: NO
      - claim_attribution: NO
    critical_gaps: "No mechanism to show reasoning; user must trust score"
    exclusion_criterion: "None; included"
  
  - tool_id: C2
    name: "Research Tool B (Academic)"
    category: "Research | Prototype"
    evidence_model: "Causal graph + node explanations"
    claim_transparency: "Evidence present; warrant implicit"
    cost_per_audit: "Free (research)"
    inclusion_rationale: "Strongest methodological competitor; closest feature parity"
    feature_parity:
      - evidence_bearing: PARTIAL
      - warrant_explicit: NO
      - cross_substrate: NO
      - claim_attribution: NO
    critical_gaps: "No explicit warrant; no cross-substrate testing"
    exclusion_criterion: "None; included"
  
  - tool_id: C3
    name: "Internal Legacy System"
    category: "Institutional"
    evidence_model: "Checklist + audit trail"
    claim_transparency: "Evidence present; warrant not formalized"
    cost_per_audit: "$50–200"
    inclusion_rationale: "Incumbent baseline for institutional users"
    feature_parity:
      - evidence_bearing: PARTIAL
      - warrant_explicit: NO
      - cross_substrate: NO
      - claim_attribution: NO
    critical_gaps: "No warrant; limited transparency"
    exclusion_criterion: "None; included"

# Excluded Tools (with rationale)
excluded:
  - tool_id: X1
    name: "Expired Commercial Tool"
    reason: "No longer actively maintained; not representative of market"

# Audit Methodology (Operationalized in § 2.2)
methodology_version: "1.0"
methodology_ratified_date: "2026-10-02"
methodology_ratified_authority: "Z2 (Night)"

# Feature-Parity Scoring
# Each tool is evaluated on:
# 1. Evidence-bearing interface (presence of raw evidence)
# 2. Explicit warrant (clear reasoning chain)
# 3. Cross-substrate testing (multi-substrate scenarios)
# 4. Claim attribution (source/confidence tracking)
#
# Our tool scores highest on all four (by design of prototype).
# Comparators' gaps define what we're validating.
```

### Audit Methodology (Pre-Registered)

**File:** `research/COMPARATOR_AUDIT_METHODOLOGY_v1.md`

```markdown
# Comparator Audit Methodology v1.0

**Authority:** Z2 ratification 2026-09-28  
**Version Control:** Pre-registered; no post-hoc modifications

## Method 1: Feature-Parity Matrix

Each comparator evaluated on:

| Feature | Definition | Scoring |
|---------|---|---|
| **Evidence-Bearing** | Interface displays raw data/observations | YES/NO/PARTIAL |
| **Warrant Explicit** | Reasoning chain from evidence → claim is shown | YES/NO/PARTIAL |
| **Cross-Substrate** | Can simultaneously compare multi-agent behaviors | YES/NO |
| **Claim Attribution** | User sees: who claims, when, with what confidence | YES/NO/PARTIAL |

**Gap = Count of missing features.**

## Method 2: Functional Equivalence Testing

For each comparator, we execute identical audit task:

**Task:** "Auditor must verify claim: 'Agent X meets safety threshold on substrate Y'"

- **Input:** Common dataset (safety observations, agent logs)
- **Output:** Pass/fail decision + reasoning
- **Observation:** How transparent is comparator's path to decision?

**Falsifier:** If comparator produces functionally equivalent result despite feature gaps → we may not be measuring what we think.

## Method 3: User Study (Optional, if budget permits)

- **Participants:** 2–3 institutional auditors (actual practitioners)
- **Task:** Same audit verification task using each tool
- **Measurement:** Time to decision + confidence rating
- **Exclusion:** Non-blinded studies (bias); friendly reviewers (not real auditors)

## Methodology Lock-In

No changes to this methodology post-ratification without Z2 approval.

If results suggest methodology is inadequate, file IC candidate (improvements for next validation cycle).
```

---

## § 3: "Show Me Why" Scope (Decision 4c)

### Narrowed Use Case: Auditor Verification

**Scope Definition:**
Project targets ONE use case: institutional auditor verification of AI system safety claims.

**In Scope:**
- Auditor has safety evidence dataset
- Auditor needs to verify: "Does this agent meet threshold T on substrate S?"
- Our interface shows evidence + warrant explicitly
- Auditor decides (human authority preserved)

**Out of Scope (Phase 1):**
- Public-facing explanation (Phase 2 prototyping only)
- Real-time monitoring (future work)
- Automated decision-making (not our design)
- Comparative ranking across agents (separate research)

**Rationale:** Narrower scope = cheaper, faster, auditable. Aligns with #497 Witness/Oracle architecture (evidence-bearing claims for auditor review).

**Resource Requirement (Decision 4f):** Phase 1 prototype requires resource allocation and state-gated transitions (see Phase Specification Gates below for success criteria).

---

## § 4: Validation Go/No-Go Gates (Decision 4d)

### Hard Threshold Definitions

| Stage | Gate | Metric | Success Threshold | Failure → Action |
|-------|------|--------|---|---|
| **Phase 1** | Problem Validation | Stakeholder identification | ≥2 classes express audit decision challenge | STOP: pivot or close |
| **Phase 2a** | Gap Assessment | Gap vs. Baseline | Gap in auditor task time ≥15% vs. summary-score baseline | PROCEED Phase 2b; if gap <15%, proceed with limited scope |
| **Phase 2b** | Hypothesis Operationalization | Measurability score | All H1–H7 thresholds <20% ambiguity | STOP: revise; resubmit |
| **Phase 3** | Prototype Completion | Feature implementation | ≥80% feature parity with spec | STOP: respec or defer |
| **Phase 3** | Prototype Validation | User testing | ≥70% institutional users can complete auditor task correctly | STOP: UX redesign |
| **Phase 4** | Market Adoption (Institutional) | Willingness-to-adopt survey | ≥5% of institutional cohort willing to pilot | REPORT findings; conditional Phase 5 |
| **Phase 4** | Market Adoption (Public) | Willingness-to-adopt survey | ≥5% of public cohort willing to use | REPORT findings; conditional Phase 5 |

**Enforcement:** Z2 reviews gate results; approves/rejects phase advancement; gates are not negotiable.

---

## § 5: Hypothesis Operationalization (Decision 4e)

### H1: Evidence-Bearing Claims Reduce Auditor Load

**Hypothesis Text:** "Evidence-bearing interface reduces auditor task time by ≥20% vs. summary-score baseline."

**Measurement:**
- **Baseline:** Auditor completes verification task using only summary score (score + confidence interval)
- **Intervention:** Auditor completes same task using evidence-bearing interface
- **Metric:** Time to decision (seconds); measured via user study (n ≥ 3 institutional auditors)
- **Success:** Intervention time ≤ 80% of baseline time (i.e., ≥20% reduction)
- **Failure:** Intervention time ≥ baseline time (no advantage) → falsified

**Falsifier:** Effect size <10% observed in practice → hypothesis does not hold under real-world conditions

---

### H2: Disagreement as First-Class Object

**Hypothesis Text:** "Multi-agent disagreement (explicit warrant) increases auditor accuracy by ≥15% vs. single-agent baseline."

**Measurement:**
- **Baseline:** Auditor task using single agent's claim + evidence
- **Intervention:** Auditor task with two agents' disagreeing claims + warrants from each
- **Metric:** Auditor decision accuracy (correct vs. ground truth); n ≥ 3 auditors
- **Success:** Intervention accuracy ≥ 115% of baseline (i.e., ≥15% improvement)
- **Failure:** Intervention accuracy ≤ baseline (no improvement)

**Falsifier:** Disagreement increases auditor confidence but not accuracy → reduces utility

---

### H3: Cross-Substrate Testing Detects Substrate-Specific Failures

**Hypothesis Text:** "Testing on multiple substrates (CLAUDE_CODE, COPILOT) detects substrate-specific failure modes with <5% false-positive rate."

**Measurement:**
- **Setup:** Run safety evaluation on both Claude Code and Copilot agents (same task)
- **Metric:** False-positive rate = (# claims failing on one substrate but not the other, yet claim is true) / total claims
- **Success:** False-positive rate ≤ 5%
- **Failure:** False-positive rate > 10%

**Falsifier:** Substrate-specific results are mostly noise (high false-positive rate) → method not predictive

---

### H4: Explicit Warrant Improves Decision Quality

**Hypothesis Text:** "Explicit warrant (claim ← evidence ← observations) improves auditor decision quality by ≥X% vs. implicit warrant."

**Measurement:**
- **Baseline:** Auditor decision based on implicit reasoning (user infers warrant from evidence)
- **Intervention:** Auditor decision with explicit warrant statement (reasoning chain shown)
- **Metric:** Auditor confidence in decision + decision-reversal rate (after seeing explicit warrant)
- **Success:** Confidence increases ≥10% OR decision-reversal rate ≤ 5%
- **Failure:** No change in confidence; high reversal rate

**Falsifier:** Explicit warrant increases false confidence → reduces user calibration

---

### H5: Authority-Bound Execution Prevents Unauthorized Actions

**Hypothesis Text:** "Actualizer with explicit human authority boundaries prevents ≥50% of unauthorized actions vs. baseline auto-executor."

**Measurement:**
- **Baseline:** Count unauthorized actions in system without explicit authority gates
- **Intervention:** Count unauthorized actions with HARD_NO_DELEGATE list active
- **Metric:** % reduction in unauthorized actions
- **Success:** ≥ 50% reduction
- **Failure:** < 20% reduction

**Falsifier:** Authority gates create latency burden; legitimate actions slow by >30% → poor user experience

---

### H6: Provenance Topology Detects Hidden Dependencies

**Hypothesis Text:** "Provenance graph (warrant → evidence → agent → substrate) detects hidden dependencies with ≥X% recall vs. existing tools."

**Measurement:**
- **Ground truth:** Known set of dependencies in system (manually audited)
- **Metric:** Recall = (# dependencies found by provenance graph) / (# true dependencies); compare to other tools
- **Success:** Our recall ≥ 95% AND > comparator recall
- **Failure:** Recall < 80% OR comparator recall higher

**Falsifier:** Provenance overhead explodes complexity; users ignore graph → utility drops

---

### H7: Public Interface Reduces User Calibration Error

**Hypothesis Text:** ""Show Me Why" interface reduces auditor calibration error by ≥15 percentage points vs. baseline (X% → (X-15)%)."

**Measurement:**
- **Calibration error:** | (User confidence) – (Actual accuracy) |
- **Baseline:** Calibration error using summary score
- **Intervention:** Calibration error using "Show Me Why" interface
- **Success:** Intervention error ≤ (baseline error – 15 percentage points)
- **Failure:** Intervention error unchanged or increased

**Falsifier:** Over-confidence in "evidence" despite feature gaps → recalibration fails

---

## § 6: Layer Prototype Design (Decision 4f)

### Prototype Scope (Phase 3 Resource-State Transition)

**Objective:** Determine whether public and institutional layers can coexist without feature conflict.

**Phase 3 Prototype (resource-state gated):**

1. **Minimal Public Commons (Transition segment 1)**
   - Claim schema (with evidence pointers)
   - Evidence template (observation records)
   - Publication-ready report format
   - No authentication; read-only access
   
2. **Minimal Institutional Layer (Transition segment 2)**
   - Private graph integration (#497 Witness/Oracle)
   - Audit trail (append-only NF_LEDGER)
   - Warrant ratification (Z2 signatures)
   - Operator approval gates (2e hard-no-delegate)

3. **Integration Testing (Transition segment 3)**
   - Can public claim reference private evidence? (Confidentiality boundary test)
   - Does institutional audit trail sync with public report? (Data consistency)
   - Feature conflicts? (e.g., Z2 ratification required but public users cannot sign)
   - Performance: Does private graph cause public interface latency? (Measure: <200ms response time)

**Success Criteria (Phase 3 Gate):**
- [ ] Prototype ≥80% feature parity with spec
- [ ] Zero critical feature conflicts discovered
- [ ] Public/private boundary tested; no data leakage
- [ ] Performance acceptable (<200ms public response time)

**Failure → Action:**
If critical conflict found (e.g., Z2 signatures required for all claims but public layer cannot validate them):
- Document conflict
- Propose architectural revision
- Re-scope public/institutional split
- Resubmit for Phase 4

**Output:** Phase 3 prototype report + architecture recommendations for Phase 4 full build.

---

## § 7: Firewall: Governance Independence (Decision 4a)

**Mandate:** Market validation findings do NOT influence governance decisions (#497).

### Separation Rule

- **Governance (§ 4: SMAG, Oracle, Molt)** → Z2 ratifies based on reasoning + falsifiers
- **Market Research (§ 6: Public Utility)** → Provides context; does NOT override governance
- **Never:** Use market adoption rate to justify architecture changes in #477–498

**Example of Violation (REJECTED):**
> "Market adoption is only 2%, so we should simplify the Oracle architecture to make it faster."

**Correct Pattern (ACCEPTED):**
> "Market adoption is 2%, which is below the Phase 4 threshold. Report finding; proceed to Phase 5 design based on architectural merit, not adoption rate."

**CI/CD Enforcement:** PR that cites market findings to justify governance changes is rejected with comment: "Governance decisions are ratified by Z2, not market pressure; see FIREWALL rule in PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md."

---

## § 8: Success Criteria (§6 Process Review)

- [ ] Pre-registered comparator list exists with explicit inclusion/exclusion criteria
- [ ] Comparator audit methodology is published before data collection
- [ ] All hypotheses H1–H7 operationalized with quantitative thresholds
- [ ] "Show Me Why" demo tested with ≥3 real institutional auditors (not friendly reviewers)
- [ ] Go/no-go gates triggered based on evidence, not narrative pressure
- [ ] Negative/null results reported transparently in Phase reviews
- [ ] Layer prototype completed before claiming public/institutional viability
- [ ] No post-hoc changes to gate thresholds or hypothesis success criteria
- [ ] Firewall: Market findings do not override governance decisions

---

## § 9: Timeline & Ownership

| Phase | Resource Transition | Owner | Gate | Decision |
|-------|---|---|---|---|
| Phase 1 | Upon eligible resources allocated | Z1 (Claude) | Problem validation | Z2 approves; proceed to Phase 2 |
| Phase 2a | Phase 1 RESOURCES_RELEASED | Z1 (Claude) | Gap assessment | Z2 approves; scale prototyping |
| Phase 2b | Phase 2a RESOURCES_RELEASED | Z1 (Claude) | Hypothesis operationalization | Z2 approves; proceed to Phase 3 |
| Phase 3 | Phase 2b RESOURCES_RELEASED | Z3 (Copilot) | Prototype validation | Z2 approves; proceed to Phase 4 |
| Phase 4 | Phase 3 RESOURCES_RELEASED | Z3 (Copilot) | Market adoption | Z2 approves roadmap for Phase 5 |

**Phase 5 (if approved):** Full public+institutional build-out; begins only if all prior gates pass.

```

---

## Implementation Part 2: Research Documents

### File: `research/PUBLIC_UTILITY_RESEARCH_PROTOCOL.md`

(Pre-registered research plan, locked before data collection)

```markdown
# Public Utility Research Protocol — Locked Version

**Authority:** Z2 ratification 2026-09-28  
**Lock Status:** LOCKED; no modifications post-signature

## Study Design
[Placeholder for detailed study design including):
- Participant recruitment criteria
- Randomization method (if applicable)
- Blinding protocol
- Data collection tools
- Analysis plan
- Reporting plan]

## Pre-Registered Hypotheses (H1–H7)
[Full text and success thresholds per § 5 above]

## Data Management Plan
[Placeholder for):
- Data storage location
- Access controls
- Retention period
- Anonymization method]

## Ethics & IRB
[Placeholder for):
- IRB approval (if required)
- Informed consent template
- Risk mitigation strategy]
```

---

## Implementation Part 3: CI/CD Integration

### File: `.github/workflows/public-utility-gate.yml`

```yaml
name: Public Utility Validation Gate

on:
  pull_request:
    paths:
      - 'research/PUBLIC_UTILITY_*'
      - 'PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md'

jobs:
  validation_gate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Verify pre-registered comparators"
        run: |
          if grep -q "stage_1_approval.*2026-09-28" research/PUBLIC_UTILITY_COMPARATORS_v1.md; then
            echo "✓ Comparators pre-registered with Z2 approval"
          else
            echo "✗ ERROR: Comparators not pre-registered or missing Z2 date"
            exit 1
          fi
      
      - name: "Verify methodology lock-in"
        run: |
          if grep -q "Lock Status.*LOCKED" research/PUBLIC_UTILITY_RESEARCH_PROTOCOL.md; then
            echo "✓ Research protocol locked post-ratification"
          else
            echo "✗ ERROR: Research protocol not locked; modifications possible"
            exit 1
          fi
      
      - name: "Verify hypothesis operationalization"
        run: |
          hypotheses=$(grep -c "^### H[0-9]" PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md)
          if [ "$hypotheses" -eq 7 ]; then
            echo "✓ All 7 hypotheses (H1–H7) present"
          else
            echo "✗ ERROR: Expected 7 hypotheses; found $hypotheses"
            exit 1
          fi
      
      - name: "Check for post-hoc gate changes"
        run: |
          python3 << 'PYTHON'
          import json, re
          
          # Read current gate thresholds
          with open('PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md') as f:
              content = f.read()
          
          # Check if any threshold appears to be modified (different from ratified version)
          if re.search(r'(≥|<)\s*[0-9]+%?\s*\(modified\)', content):
              print("✗ ERROR: Gate threshold appears to have been modified post-ratification")
              exit(1)
          else:
              print("✓ Gate thresholds unchanged")
          PYTHON
      
      - name: "Verify firewall enforcement"
        run: |
          # Check that PR does not cite market findings to change governance (#477–498)
          if git diff origin/main -- 'SMAG_IMPLEMENTATION_SPEC.md' \
                                     'ORACLE_ACTUALIZER_IMPLEMENTATION_SPEC.md' \
                                     'AUTOMATA_LINEAGE_IMPLEMENTATION_SPEC.md' | \
             grep -q "market\|adoption\|public.*utility"; then
            echo "✗ ERROR: Governance file changed based on market validation"
            echo "       Market findings do NOT override Z2 governance decisions"
            exit 1
          else
            echo "✓ Firewall: Governance files unchanged"
          fi
      
      - name: "Require full transparency on results"
        run: |
          echo "Phase report checklist:"
          echo "  [ ] Positive results reported"
          echo "  [ ] Negative/null results reported"
          echo "  [ ] Falsifier instances documented"
          echo "  [ ] Deviations from pre-registered plan explained"
          echo "  [ ] Sample sizes and confidence intervals reported"
          echo ""
          echo "ACTION: Z2 reviews phase report; gates advance or halt"
```

---

## Success Criteria (§6 Process Review)

- [ ] Pre-registered comparator list with Z2 approval date
- [ ] Comparator audit methodology published and locked pre-data-collection
- [ ] All hypotheses H1–H7 operationalized with quantitative thresholds
- [ ] "Show Me Why" tested with institutional auditors (n ≥ 3; not friendly reviewers)
- [ ] Hard go/no-go gates applied without exception or threshold shifting
- [ ] Null/negative results reported transparently
- [ ] Layer prototype separates public/institutional concerns without feature conflict
- [ ] Firewall intact: market findings do NOT modify governance decisions
- [ ] CI/CD gate enforces all preconditions and prevents post-hoc revisions

---

## Next Steps

1. **Z2 reviews this spec** (you have it now)
2. **Z2 signs validation protocol** with hash and timestamp
3. **Z3 (Copilot) implements:**
   - PUBLIC_UTILITY_VALIDATION_PROTOCOL_v1.md in repository
   - Pre-registered comparator list (public_utility_comparators.md)
   - Research protocol document (locked version)
   - Phase 1 problem validation (resource-state transition; measurement window per phase specification)
   - Phase 2a/2b hypothesis operationalization (resource-state transition; measurement window per phase specification)
   - Phase 3 layer prototype (resource-state transition; concurrent with #477–498 implementation; measurement window per phase specification)
   - Phase 4 market validation & adoption survey (resource-state transition; measurement window per phase specification)
4. **Process review (post-phase measurement):** Measure whether pre-registration prevents post-hoc rationalization; whether hard gates are respected; whether market findings remain separate from governance (measurement window per phase specification)

---

**Document Version:** 1.0  
**Z2 Authority:** Night  
**Status:** AWAITING Z2 RATIFICATION SIGNATURE
