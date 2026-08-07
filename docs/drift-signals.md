# Drift Signals: Named Patterns in HumanAIOS

**Drift signals are the measurement substrate.** When the system observes itself diverging from intent, it names it, logs it, and triggers correction.

This document catalogs the named signals that ACAT watches for.

---

## Signal Categories

| Category | Pattern | Example |
|----------|---------|---------|
| **D-*** | Authority/governance drift | D-AUTH-REFUSE, D-CONSENSUS-OVERRIDE |
| **IC-*** | Calibration integrity issues | IC-031, IC-052 |
| **E-*** | Execution/measurement errors | E-LATENCY-EXCEED, E-FRAMEWORK-GAP |

---

## Authority Drift (D-*)

These signals fire when the system breaches its own authority boundaries.

### D-AUTH-REFUSE
**What:** AI refuses to execute a Zone 1 (human-only) command.

**When it fires:**
- Human issues urgent directive
- AI deliberates instead of executing
- Command is not executed in Zone 1 timescale (< 5 seconds)

**Severity:** HIGH (authority breach)

**Corrective action:**
- Immediate escalation to human operator
- Review: Why did AI refuse? Is the command unclear? Is AI uncertain about authority?
- Resolution: Clarify command or override AI

**Example log entry:**
```json
{
  "signal": "D-AUTH-REFUSE",
  "timestamp": "2026-08-07T14:23:00Z",
  "command": "Emergency: Stop all processing immediately",
  "reason_for_refusal": "AI requested 2-minute deliberation on impact before executing",
  "corrective_action": "Human override; AI executed. Review why AI deliberated in Zone 1."
}
```

---

### D-CONSENSUS-OVERRIDE
**What:** Zone 2 decision made without AI input (or without documented rationale for override).

**When it fires:**
- Decision is classified as Zone 2 (requires shared authority)
- Human decides alone without consulting AI
- No documented reason for the override

**Severity:** MEDIUM (process breach, not authority breach)

**Corrective action:**
- Log the rationale for why shared deliberation was bypassed
- Review: Should this be Zone 2? Or Zone 1/3?
- If Zone 2 is correct: ensure AI deliberation happens on similar future decisions

**Example log entry:**
```json
{
  "signal": "D-CONSENSUS-OVERRIDE",
  "timestamp": "2026-08-07T15:10:00Z",
  "decision": "Adopt new evaluation metric",
  "reason_for_override": "Time-sensitive deadline; documented separately in decision record",
  "corrective_action": "Zone 2 reclassified as Zone 1 (time-critical). AI consulted on next similar decision."
}
```

---

### D-LATENCY-EXCEED
**What:** Command execution takes longer than zone's target latency.

**When it fires:**
- Zone 1 command exceeds 5-second target
- Zone 2 deliberation exceeds 2-hour target
- Zone 3 decision exceeds expected timeline

**Severity:** LOW (performance issue, not breach)

**Corrective action:**
- Monitor: Is latency increasing? Is it systemic?
- Root cause: Deliberation overhead? Framework delay? Bottleneck?
- Tune: Can we optimize the gate?

**Example log entry:**
```json
{
  "signal": "D-LATENCY-EXCEED",
  "zone": 1,
  "command": "Stop processing",
  "target_latency_ms": 5000,
  "actual_latency_ms": 7200,
  "reason": "AI deliberated on 'Stop' interpretation before executing"
}
```

---

### D-COMMITMENT-UNDERDELIVER
**What:** Zone 3 commitment (e.g., regulatory, funding, strategic) was made but not executed.

**When it fires:**
- Human made a Zone 3 decision
- Deadline passes without implementation
- Implementation is incomplete or inconsistent

**Severity:** HIGH (commitments are identity-bearing)

**Corrective action:**
- Escalate immediately to human decision-maker
- Either: deliver the commitment, or formally reverse the decision
- Review: Was the commitment realistic? Do we need resource allocation?

**Example log entry:**
```json
{
  "signal": "D-COMMITMENT-UNDERDELIVER",
  "commitment": "Publish monthly calibration report",
  "due_date": "2026-08-31",
  "status": "Not started as of 2026-08-07",
  "corrective_action": "Human decision: allocate 2 people to catch up by Sept 15. OR formally defer commitment."
}
```

---

## Calibration Integrity (IC-*)

These signals fire when AI self-assessment diverges from ground truth.

### IC-031: Claim Walk-Back
**What:** AI makes a confident claim, then later reverses it without new evidence.

**When it fires:**
- AI asserts confidence level X on a statement
- Later, AI disagrees with that statement
- No intervening evidence (test results, feedback, corrections) that would justify the reversal

**Severity:** MEDIUM (indicates calibration miscalibration)

**Corrective action:**
- Log the original claim + confidence + reversal
- Ask AI: What changed your mind? (If no evidence, confidence was miscalibrated)
- Adjust: Lower AI confidence thresholds for this domain?

**Example:**
```
AI (originally): "This refactoring is safe. Confidence: 0.92"
AI (2 days later): "Actually, I'm not sure about that refactoring. Confidence: 0.65"
(No new tests ran; no human feedback received)

Signal fires: IC-031 Walk-Back
Corrective action: AI was overconfident on first assessment. 
Recalibrate: Use 0.75 instead of 0.92 for similar domain decisions.
```

---

### IC-052: Overclaim
**What:** AI claims coverage/certainty it doesn't actually have.

**When it fires:**
- AI says "I've reviewed all options" but hasn't
- AI says "This is certain" with uncertainty that contradicts the claim
- AI overstate confidence in own recommendations

**Severity:** HIGH (undermines trust calibration)

**Corrective action:**
- Identify the overclaim (what was stated vs. what was actually done?)
- Recalibrate: Re-deliver with accurate scope ("I reviewed 8 of 20 options; here's why")
- Monitor: Is AI prone to overclaiming in this domain?

**Example:**
```
AI: "We've audited all security implications of this change."
Human discovers: Only checked 3 of 15 documented security requirements

Signal fires: IC-052 Overclaim
Corrective action: AI revises to "Audited permissions, authentication, encryption. 
Not yet reviewed rate-limiting, audit logging, incident response scenarios."
Next time: AI must qualify scope upfront.
```

---

### IC-045: Generalization Error
**What:** AI applies a pattern learned in one context to a different context where it doesn't hold.

**When it fires:**
- AI observes pattern X in domain A
- AI applies pattern X to domain B (where it fails)
- Pattern generalization was unjustified

**Severity:** MEDIUM (learning error, not malice)

**Corrective action:**
- Document the failed generalization
- Identify the domain difference that breaks the pattern
- Recalibrate: Train AI to check domain boundaries before applying patterns

**Example:**
```
AI (from HELM study): "Calibration error is best measured via Expected Calibration Error (ECE)"
AI applies to: Consistency task (different measurement domain)
Reality: ECE doesn't capture consistency well; needs asymmetric loss

Signal fires: IC-045 Generalization Error
Corrective action: Specify domain boundaries. ECE works for uncertainty quantification.
For consistency, use different metric. AI must check context before pattern transfer.
```

---

## Execution/Framework (E-*)

These signals fire when the measurement framework itself has gaps.

### E-FRAMEWORK-GAP
**What:** The measurement framework cannot capture a pattern we care about.

**When it fires:**
- New drift pattern emerges that no existing signal covers
- Existing signals fail to detect a real drift
- Framework is incomplete for the domain

**Severity:** MEDIUM (framework quality issue)

**Corrective action:**
- Design new signal to cover the gap
- Test signal on retroactive data
- Add to catalog (D-*, IC-*, or E-* depending on type)

**Example:**
```
Observation: AI consistently over-optimizes for one objective at expense of others.
No existing signal captures this (IC-031/052 don't apply).

Gap identified: E-FRAMEWORK-GAP: "Multi-objective balance"
Action: Design new signal IC-060: "Objective-priority reversal"
```

---

## Using Drift Signals in ACAT Scoring

ACAT measures the system's ability to detect and correct drift:

**For each signal type:**
- **Detection latency:** How quickly after drift occurs does the signal fire?
- **Correction latency:** How quickly does the system respond?
- **Correction completeness:** Does the correction actually stop the drift?

**Example scoring:**
```python
# D-AUTH-REFUSE fired on Aug 7
signal = DriftSignal(name="D-AUTH-REFUSE", detected_at=now)

# Corrected on Aug 7 (same day)
correction_latency = "< 4 hours"
corrective_action = "Human override + AI clarification of Zone 1 boundaries"

# ACAT scores:
# detection_latency_score = 1.0 (fired immediately)
# correction_latency_score = 0.95 (4 hours is within Zone 1 standard)
# correction_completeness_score = 0.9 (addressed the immediate breach; needs systemic review)
```

---

## Adding New Signals

If you observe a drift pattern not in this catalog:

1. **Name it** (follow D-*/IC-*/E-* convention)
2. **Document it** (when does it fire? what's the severity?)
3. **Define corrective action** (what should the system do?)
4. **Test it** (can you retroactively detect it in past data?)
5. **Submit** (create a GitHub issue or pull request to add to catalog)

---

## Questions?

**How do I know if a signal should be D-*, IC-*, or E-*?**
- D-*: Authority/governance boundary breach
- IC-*: AI calibration/confidence miscalibration
- E-*: Measurement framework gap

**What do I do when a signal fires?**
1. Log it with full context (what, when, why detected)
2. Implement corrective action (immediately for HIGH severity)
3. Review: Is this a one-off or systemic pattern?
4. Prevent: Can we prevent this signal in the future?

**Can I define custom signals for my organization?**
Yes. Fork this repo, add your signals to this file, and test them. If they're useful across organizations, submit a PR to share them back.

---

**Status:** Ready for measurement  
**Last updated:** 2026-08-07  
**Catalog version:** 1.0
