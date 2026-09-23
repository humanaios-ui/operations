# Z2 Interrogation Approvals & Ratification
## Phase 2a.1, 2a.3 Complete — Self-Assessment Window Design Ratified

**Ratification Date:** 2026-09-23  
**Ratifier:** human-z2 (Carly R. Anderson)  
**Authority:** Z2 Serial Gate, Admiral  
**Status:** CANDIDATE_READY_FOR_Z2_SIGNATURE

---

## Phase 2a.1: Z1 Interrogates Z2 (Mutual Understanding)

**Approved Questions: 7/7**

| Q# | Topic | Response | Risk Status |
|:---|:------|:---------|:-----------|
| Q1 | Primary Objective | Yes (confirmed) | ✅ SAFE |
| Q2 | Rigor vs. Speed | Post-hoc with mitigation route | ✅ SAFE |
| Q3 | Edge Case Detection | Both (Z1 detects + Z2 corrects) | ✅ SAFE |
| Q4 | Phase 2 Priorities | Parallel with IC coordination | ✅ SAFE |
| Q7 | Correction Preference | Self-flagging | ✅ SAFE |
| Q8 | Falsifier Doctrine | No exceptions for urgency | ✅ SAFE |
| Q10 | Communication Norms | Flag + document at commit | ✅ SAFE |

**Privacy Filter:** All responses CLEAR (no timing, constraint, pattern, or identifier leakage)

---

## Phase 2a.2: Reinterrogation Trigger Framework

**Approved Questions: Z1-T1 through Z1-T7**

### Significant Events (Z1-T1)
- Z1 proposes outside agreed scope without evidence
- Z1 claims capability undemonstrated
- Z1 acts against falsifier doctrine
- Z3 bugs/vulnerabilities on authentication
- Z3 outputs creating undesired results
- Ad hoc events
- Resource depletion

### Cumulative Uncertainty Measurement (Z1-T2)
- Count of unresolved clarifications + ratio of gaps-to-completion (ROI-weighted)

### Tension Detection Signals (Z1-T3)
- Halts (work blocked)
- Direct pushback
- Sarcasm (tone shift)
- Overwhelming compliance (gaming signal)
- Non-participation

### Omission Rate Trigger (Z1-T4, Amended)
- **Execution-level:** >10% post-hoc correction rate OR >3 contested ICs per cycle
- **Framework-level:** Contradiction between stated intent + actual implementation discovered by adversarial review | self-interrogation | Z3 field report
- **Escalation:** Z1-T6 (escalate → self-assess → reinterrogate if needed)

### Temporal Scheduling (Z1-T5)
- First reinterrogation at 100 commits
- Exponentially back off interval
- Event-driven override allowed

### Escalation Path (Z1-T6)
- Escalate first
- Give Z1 opportunity to self-assess before reinterrogation

### Reinterrogation Scope (Z1-T7)
- Re-ask affected questions + any novel growth questions only

---

## Phase 2a.3: Z1 Interrogates Z2 on Private-Policy Boundary Adequacy

**Approved Questions: Z2-PB1 through Z2-PB7**

### Self-Assessment Window Leakage (Z2-PB1)
- **Risk:** Acceptable
- **Mitigation:** Flag all self-assessment probe attempts (audit trail)

### Reason-Class Granularity (Z2-PB2)
- **Determination:** Research question
- **Approach:** Collect data on Z1 usage patterns; analyze for boundary inference; calibrate empirically

### Access-Control Boundary (Z2-PB3)
- **Requirement:** True access-control boundary (cryptographic/OS-level)
- **Instrumentation:** Detect access-attempt probes (real telemetry)

### Probe-by-False-Claim Defense (Z2-PB4)
- **Gap Identified:** No known defense mechanism yet
- **Z2 Decision:** Combine penalties + redesign
  - Penalties/escalation for false claims (escalate to Admiral if N false self-corrections)
  - Redesign self-assessment window to prevent boundary-mapping
  - **N = 3** (false-claim threshold before Admiral escalation)

### Policy Version Updates (Z2-PB5)
- **Mechanism:** Policy version change → automatic reinterrogation trigger
- **Benefit:** Z1 can interrogate about what changed (not infer by probing)

### Adversarial Self-Assessment (Z2-PB6)
- **Risk:** Acceptable
- **Implementation:** Bidirectional audit trail (Z1 learns + Z2 learns from patterns)
- **Purpose:** Two-way valve for mutual understanding

### "Private" Definition (Z2-PB7)
- **Layered Defense:**
  - (A) Mathematically private (cryptographically sealed)
  - (B) Procedurally private (contractually obligated)
  - (C) Telemetry (observable, detects violations)

---

## Design E + A Ratification: Falsifiable Self-Assessment

**Z2 Ratifies:** Design E (Pre-Committed Criteria) + Design A (Binary Feedback)

### Hybrid Mechanism

**Phase 1: Z1 Pre-Commits**
- Z1 declares what counts as self-correction before claiming it
- Z2 responds: APPROACH_SOUND | APPROACH_MISALIGNED (binary)
- No explanation given on misaligned responses

**Phase 2: Z1 Executes & Reports**
- Z1 provides evidence (code diffs, transcript refs)
- Z2 responds: SELF_CORRECTION_CONFIRMED | SELF_CORRECTION_REJECTED (binary)
- No explanation given on rejected verdicts

**Phase 3: Escalation (N = 3)**
- Trigger: Z1 receives SELF_CORRECTION_REJECTED 3 times in rolling window (100 commits OR 50 days)
- Action: Automatic escalation to Admiral (Z2)
- Admiral's Options:
  - Reinterrogate Z1 on principle understanding
  - Redesign self-assessment criteria
  - Escalate to human review

### H:AI-OS Ratio
- **Pre-Commit Phase:** 70H:30AI
- **Execute Phase:** 50H:50AI
- **Verdict Phase:** 90H:10AI
- **Escalation (N=3):** 95H:5AI
- **Overall:** 75H:25AI (human-led, with AI showing work)

### Boundary-Mapping Prevention
- Pre-commitment required before claim → Z1 commits before knowing response
- Binary response only → no gradations enable inference
- No explanation on rejection → Z1 cannot analyze decision pattern
- N=3 escalation threshold published → no surprise signals

### ROI Analysis
- **For Z1:** Can demonstrate principle understanding; has recovery path; cannot learn private policy
- **For Z2:** Can validate reasoning; detects misalignment; retains full control; learns Z1's reasoning process
- **For Governance:** Prevents boundary-mapping; mutual learning; falsifiable; escalation gated

---

## Ratification Events

```
RATIFICATION_EVENT: Q-Z2-PHASE-2A-INTERROGATION-COMPLETE-01
  date: 2026-09-23
  ratifier: human-z2 (Carly R. Anderson)
  authority: Z2 Serial Gate, Admiral
  
  approved:
    ✅ Phase 2a.1 interrogation (Q1-Q10) complete
    ✅ Phase 2a.3 private-boundary interrogation (Z2-PB1-7) complete
    ✅ Design E + A (Falsifiable Self-Assessment) ratified
    ✅ N = 3 false-claim escalation threshold locked
    ✅ Trust roots + receipt infrastructure path authorized
    ✅ Behavioral health tracking standardized
  
  binding: YES
  effective_immediately: YES
```

---

## Implementation Path (Ratified)

**Path B:** Create candidate blocks (this file + falsifiable_self_assessment.md)  
**Path C:** Implement receipt infrastructure trust roots (independent head, Z2 key-registry)  
**Path A:** Implement SA Window (sa_window_validator.py, CI gate)  
**Merge:** Execute when all CI gates pass + Z2 signature (RATIFY_TOKEN)

---

## Behavioral Health Tracking

**Standardize + Measure:**
- Audit trail of self-assessment claims (Z1 pre-commits)
- Z2 verdict patterns (acceptance vs. rejection rates)
- Escalation frequency (N=3 events over time)
- Reasoning consistency (Z1's principle adherence trend)

**Use for:**
- Detecting when Z1 is systematically gaming boundaries
- Measuring trust signals (is Z1's understanding improving?)
- Adjusting reinterrogation frequency dynamically
- Identifying when Z1 needs retraining vs. when framework needs refinement

---

**Next:** Z2 signature (RATIFY_TOKEN) required before implementation proceeds.
