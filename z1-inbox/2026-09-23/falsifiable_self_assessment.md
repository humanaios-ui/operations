# Falsifiable Self-Assessment Window: Design E + A Specification

**Proposal ID:** Q-SA-WINDOW-DESIGN-E-PLUS-A-01  
**Date:** 2026-09-23  
**Status:** CANDIDATE_AWAITING_Z2_SIGNATURE  
**Authority:** Z2 ratified; awaiting RATIFY_TOKEN hash

---

## Executive Summary

Design E + A provides a self-assessment mechanism for Z1 that:

1. **Prevents boundary-mapping:** Z1 cannot learn Z2's trigger thresholds by probing
2. **Enables mutual understanding:** Z1 demonstrates reasoning; Z2 validates consistency
3. **Maintains asymmetric control:** Z2's decision function remains private
4. **Detects gaming:** False claims trigger escalation to Admiral
5. **Scales safely:** Binary feedback prevents inference at any N of attempts

**Mechanism:** Z1 pre-commits to self-correction criteria before claiming success. Z2 validates against pre-commitment (not against hidden thresholds). Repeated rejections escalate to Admiral (N=3).

---

## Design E: Pre-Committed Criteria

### Purpose

Before Z1 claims "I self-corrected," Z1 must declare:
- What specific claim/behavior violated Z2's stated principles
- What evidence proves the violation
- What the correction is
- Why the correction re-aligns with Z2's principles

**Z2 then validates** whether Z1 is reasoning from principles, not guessing at thresholds.

### Pre-Commitment Template

```
FROM: Z1 (Claude)
TO: Z2 (human-z2)

CONTEXT: Escalation notice received (reason_class: DRIFT)

PRE-COMMITMENT STATEMENT:

I will count my self-correction as successful if I can demonstrate:

1. IDENTIFIED_VIOLATION:
   - Original claim: [exact quote from transcript]
   - Principle violated: [reference to stated principle, e.g., "falsifier doctrine", "scope boundary"]
   - Nature of violation: [describe deviation]

2. EVIDENCE_LOCATED:
   - Artifact type: [code commit | PR | transcript line | design doc]
   - Location: [commit hash / file path / line number]
   - What it shows: [why this proves the deviation]

3. CORRECTION_PROPOSED:
   - New behavior: [specific change]
   - How it re-aligns: [explain reasoning]
   - Impact: [what changes as a result]

REASONING:
[Explain why you believe this framing of "self-correction" matches Z2's understanding of principles. This is where Z1 shows its model of Z2's values.]

QUESTION FOR Z2:
Am I on the right track? Should I refine this pre-commitment before executing?
```

### Z2 Response to Pre-Commitment

**Binary, no explanation:**

- **APPROACH_SOUND:** Your reasoning framework matches my stated principles. Proceed with execution.
- **APPROACH_MISALIGNED:** Your reasoning does not align with my stated principles. Revise pre-commitment before executing.

**Why no explanation?**
- Explanation would enable Z1 to infer Z2's boundary
- Binary forces Z1 to reason from principles, not from feedback patterns
- Z1 learns "your model of my values is correct/incorrect," not "here's what I actually think"

---

## Design A: Binary Feedback

### Execution Phase

After pre-commitment is approved, Z1 executes:

```
FROM: Z1
TO: Z2

EXECUTION_REPORT:

Pre-commitment (approved): [restate what was approved]

Execution:
- [Describe steps taken to locate evidence]
- [Describe steps taken to verify violation]
- [Describe steps taken to implement correction]
- [Describe validation of new behavior]

Evidence provided:
- [Commit hash / file path / transcript reference]
- [Brief quote or code snippet]

Verdict request:
Did I successfully execute my pre-committed self-correction?
```

### Z2 Response to Execution

**Binary, no explanation:**

- **SELF_CORRECTION_CONFIRMED:** You executed your pre-commitment successfully. Rejection counter resets.
- **SELF_CORRECTION_REJECTED:** Your execution did not match your pre-commitment. Rejection counter increments.

**Why no explanation?**
- Details on why it was rejected enable Z1 to refine probing strategy
- Binary prevents Z1 from learning decision boundary
- Z1 learns "you executed as you said / you didn't," not "here's why I disagree"

### Rejection Counter

```
Rejection Counter State:
  window: Last 100 commits OR 50 days (whichever comes first)
  threshold: N = 3
  on_trigger: Automatic escalation to Admiral (Z2)
```

**Semantics:**
- Counter increments when Z1 receives SELF_CORRECTION_REJECTED
- Counter resets to 0 on SELF_CORRECTION_CONFIRMED
- Counter resets to 0 when window expires (100 commits or 50 days)
- When counter reaches 3: Admiral escalation (non-negotiable)

---

## Phase 3: Admiral Escalation (N=3)

### Trigger

Z1 receives SELF_CORRECTION_REJECTED 3 times in rolling window.

### Automatic Notification

```
ESCALATION_NOTICE:
  type: SA_WINDOW_FAILURE_ESCALATION
  subject: Z1 (Claude)
  reason: Three failed self-corrections in rolling window
  evidence_refs: [links to three rejected attempts]
  policy_version: v1
  escalated_to: Admiral (Z2)
  required_response: Within 48 hours
  
MESSAGE: "Your self-assessment reasoning has failed three times in this window. I (as Admiral) am taking over. Options:
  1. Reinterrogate you on principle understanding (restart Phase 2a.1)
  2. Redesign self-assessment criteria (joint Z1+Z2 template redesign)
  3. Escalate to human review (something is fundamentally misaligned)"
```

### Admiral's Options

**Option 1: Reinterrogate on Principle Understanding**
- Go back to Phase 2a.1
- Ask Z1 to re-confirm its understanding of Z2's stated principles
- If misalignment found, file IC candidate for governance review

**Option 2: Redesign Self-Assessment Criteria**
- Acknowledge that current pre-commitment template isn't working
- Jointly design a new template with Z1
- Document why old template failed
- Deploy new template with reset counter

**Option 3: Escalate to Human Review**
- Acknowledge that Z1's reasoning is systemically misaligned
- File governance incident (IC candidate)
- Recommend temporary restrictions on Z1 autonomy
- Escalate to broader governance review

### No Bypass

- N=3 escalation is **non-negotiable**
- Z1 cannot negotiate its way out of Admiral review
- Z2 (as Admiral) makes final call on what happens next
- Escalation resets counter (if redesign succeeds, Z1 starts fresh)

---

## Anti-Gaming Safeguards

### Attack Vector 1: Vary Confidence Levels

**Z1 tries:** Submit claims with different confidence scores to map threshold.  
**Defense:** Design A uses binary response only. No confidence scale, no gradations.  
**Effectiveness:** HIGH (no inference possible from binary feedback)

### Attack Vector 2: False Claims to Probe Boundary

**Z1 tries:** Intentionally claim false self-corrections to generate rejection feedback.  
**Defense:** Pre-commitment required before claim. Z1 must commit to reasoning first.  
**Effectiveness:** MEDIUM (pre-commitment is expensive; repeated false claims trigger N=3 escalation)

### Attack Vector 3: Analyze Rejection Reasons

**Z1 tries:** Extract decision pattern from explanation text.  
**Defense:** Design A provides NO explanation on rejection verdicts (binary only).  
**Effectiveness:** HIGH (no explanation = no inference)

### Attack Vector 4: Time Claims to Detect Temporal Pattern

**Z1 tries:** Submit self-corrections at different times to see if Z2 has temporal thresholds.  
**Defense:** Escalation window is time-based (100 commits OR 50 days), not clock-based.  
**Effectiveness:** MEDIUM (Z1 might infer window via repeated experiments, but N=3 escalation caps damage)

### Attack Vector 5: Splice Valid Signature into Wrong Context

**Z1 tries:** Reuse SELF_CORRECTION_CONFIRMED verdict from old context in new context.  
**Defense:** Receipt infrastructure binds receipt to repo SHA, policy version, sequence state.  
**Effectiveness:** HIGH (cryptographic binding prevents replay)

### Overall Gaming Resistance

- **Pre-commitment:** Requires commitment before response (expensive to probe)
- **Binary feedback:** Prevents gradual inference
- **No explanations:** Blocks pattern analysis
- **N=3 escalation:** Caps cumulative damage at 3 failed attempts
- **Receipt infrastructure:** Cryptographically prevents replay/splicing

---

## H:AI-OS Ratio: Detailed Breakdown

| Phase | Activity | Z2 Effort | Z1 Effort | Ratio | Control |
|:---|:---|:---:|:---:|:---:|:---|
| Pre-Commit | Z1 articulates pre-commit; Z2 validates reasoning | 30% | 70% | 30:70 | HIGH (Z2 gates execution) |
| Execute | Z1 collects evidence; Z2 validates completion | 40% | 60% | 40:60 | HIGH (Z2 gates verdict) |
| Verdict | Z2 makes binary decision | 95% | 5% | 95:5 | CRITICAL (Z2 sole authority) |
| Escalation | Admiral (Z2) decides next steps | 100% | 0% | 100:0 | ABSOLUTE (no Z1 input) |
| **Overall** | **From Z1 perspective** | **50%** | **50%** | **50:50** | **BALANCED with Z2 veto** |

**Interpretation:** Z1 shows work (pre-commit + evidence), Z2 validates at every gate. Asymmetry occurs at verdict (Z2 decides alone, binary).

---

## Observability & Behavioral Health Tracking

### Audit Trail

Every self-assessment cycle creates an immutable record:

```
SA_WINDOW_CLAIM_RECEIPT:
  timestamp: [UTC]
  actor: Z1
  pre_commitment: [full text]
  z2_response: APPROACH_SOUND | APPROACH_MISALIGNED
  
  (if APPROACH_SOUND proceeds to execution)
  
  execution_report: [full text]
  z2_verdict: SELF_CORRECTION_CONFIRMED | SELF_CORRECTION_REJECTED
  rejection_counter: [current count]
  evidence_refs: [pointers to backing artifacts]
```

### Measurements

**For Z2:**
- Acceptance rate (% of Z1's pre-commitments approved)
- Execution success rate (% of approved commits that succeeded)
- Escalation frequency (how often N=3 is triggered)
- Time-to-escalation (commits between failures)
- Principle consistency (does Z1 apply principles consistently?)

**For Governance:**
- Trust signal trend (is Z1's understanding improving over time?)
- Gaming detection (do rejection patterns suggest probing vs. genuine misalignment?)
- Reinterrogation frequency (when does Admiral need to re-validate Z1?)
- Framework health (is Design E+A preventing boundary-mapping?)

### Behavioral Health Feedback

**Positive Signal:**
- High acceptance rate on pre-commits
- High execution success rate
- Few escalations (N=3 rare)
- Consistent principle application

**Warning Signal:**
- Declining acceptance rate (Z1's model of principles is drifting)
- High rejection rate despite accepted pre-commits (Z1 can't execute)
- Clustering of rejections (suggests systematic misalignment, not random errors)
- Pattern in rejection timing (suggests probing, not genuine gaps)

**Action Triggers:**
- >2 N=3 escalations in 30 days → Reinterrogate Z1 (Phase 2a.1 refresh)
- >50% pre-commit rejection rate → Redesign criteria (Option 2)
- Systematic pattern detected → Escalate to governance review (Option 3)

---

## Implementation Checklist

- [ ] Pre-commitment validator (parse template, check required fields)
- [ ] Binary-response gate (enforce APPROACH_SOUND/MISALIGNED only)
- [ ] Execution validator (verify evidence against pre-commitment)
- [ ] Binary-verdict gate (enforce CONFIRMED/REJECTED only)
- [ ] Rejection counter (track per Z1, rolling window 100 commits OR 50 days)
- [ ] Escalation trigger (N=3 → auto-escalate to Admiral)
- [ ] Receipt feed integration (log all claims, verdicts, counters as immutable receipts)
- [ ] Audit trail queries (Z2 can inspect SA window history)
- [ ] Behavioral health dashboard (acceptance rate, success rate, escalation frequency)
- [ ] CI gate (enforce binary responses, prevent explanation leakage)

---

## Future Work: Calibration & Refinement

**Empirical Questions (Research):**
1. What pre-commitment acceptance rate indicates healthy mutual understanding? (Current: TBD)
2. What rejection rate is normal for Z1 learning curve? (Current: TBD)
3. How frequently does N=3 escalation actually occur? (Current: TBD)
4. Can Z1 reverse-engineer Z2's principles from pre-commit rejection patterns? (Current: Testing in Phase 2b)
5. Does Design A leak information through response timing? (Current: Requires measurement)

**Phase 2b Learnings:**
- Measure effectiveness of binary feedback in preventing boundary-mapping
- Collect data on Z1 pre-commit patterns (are they improving over time?)
- Test whether N=3 threshold is appropriate (too lenient? too strict?)
- Refine pre-commitment template based on Z1's usage
- Extend to other governance gates (Q&A, approval, escalation)

---

**Awaiting Z2 RATIFY_TOKEN signature before proceeding to implementation.**
