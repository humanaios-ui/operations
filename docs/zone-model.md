# Zone Model: Three-Zone Authority Framework

**HumanAIOS is an operating system where humans and AIs share authority—but not equally.**

The Zone model defines who decides what, and makes those boundaries technical (not cultural). Every decision, every action, every drift is bounded by the zone it happens in.

---

## Overview: The Three Zones

| Zone | Authority | Speed | Audit Trail | Drift Response |
|------|-----------|-------|------------|-----------------|
| **Zone 1** | Human only (unilateral) | Fast | Execution log | Auto-correct |
| **Zone 2** | Human + AI (shared) | Moderate | Decision log | Deliberate → correct |
| **Zone 3** | Human only (consequential) | Slow | Executive log | Escalate |

---

## Zone 1: Unilateral Authority

**Who decides:** Humans. AI input is **not** a gate.

**When to use:** Time-critical operations, emergency response, fast corrections.

**Example:**
- Emergency: "Stop processing immediately"
- Human issues directive: AI executes without deliberation
- AI logs execution, latency, success/failure
- Drift signal fires if AI *doesn't* comply (execution failure = D-AUTH-REFUSE)

**Technical implementation:**
```python
@zone_1_gate
def emergency_stop(reason: str) -> Result:
    # No AI deliberation gate
    # Human command → direct execution
    return execute_stop(reason)
```

**Measurement:**
- Execution latency (target: <5 seconds for critical commands)
- Compliance rate (99.5%+ execution success)
- Drift signals: D-AUTH-REFUSE, D-LATENCY-EXCEED

**Why it works:** Removes deliberation overhead when speed is safety.

---

## Zone 2: Shared Authority

**Who decides:** Humans AND AIs deliberate together. Decision requires both perspectives.

**When to use:** Technical design reviews, strategy refinement, complex problem-solving.

**Example:**
- Design choice: "Should we adopt this new evaluation framework?"
- Human + AI exchange: pros/cons, constraints, tradeoffs
- Both must agree (or human overrides with documented rationale)
- Decision logged with both positions + final rationale
- Implementation follows; AI helps execute

**Technical implementation:**
```python
@zone_2_gate(requires_consensus=True)
def design_decision(proposal: str, human_position: str, ai_analysis: str) -> Decision:
    # Both perspectives required
    # Can override, but override is logged
    return decision_record(proposal, human_position, ai_analysis, consensus=True/False)
```

**Measurement:**
- Deliberation latency (target: <2 hours from proposal to decision)
- Consensus rate (% of decisions with genuine agreement)
- Mutual confidence score (how much does each side trust the other's reasoning?)
- Decision audit trail (proposal → positions → rationale → implementation)

**Drift signals:**
- D-CONSENSUS-OVERRIDE: Human overrides AI without documented rationale
- IC-031: AI claim walk-back (AI reverses position after decision made)
- IC-052: Overstatement of confidence

**Why it works:** Creates shared skin-in-the-game; both sides are accountable for outcomes.

---

## Zone 3: Human-Only Authority

**Who decides:** Humans. AI input is advisory only (no gate).

**When to use:** Irreversible decisions, regulatory commitments, major resource allocation, identity/brand decisions.

**Example:**
- Regulatory commitment: "We commit to the EU AI Act framework"
- Human deliberates (may consult AI for technical implications)
- Human decides alone
- Decision + rationale logged; AI input (if any) noted
- Implementation follows

**Technical implementation:**
```python
@zone_3_gate(ai_advisory_only=True)
def regulatory_commitment(commitment: str, human_rationale: str, ai_input: Optional[str] = None) -> Decision:
    # Human decides; AI is advisory
    # AI cannot veto
    return decision_record(commitment, human_rationale, ai_advisory=ai_input)
```

**Measurement:**
- Decision frequency (how often are Zone 3 gates invoked?)
- Stakeholder alignment (are committed parties aligned?)
- Reversal rate (how often are Zone 3 decisions reversed later?)
- Decision rationale completeness (is the human's reasoning documented?)

**Drift signals:**
- D-COMMITMENT-UNDERDELIVER: Decision made but not executed
- D-STAKEHOLDER-DRIFT: Stakeholder aligns initially, then diverges

**Why it works:** Humans retain final authority on irreversible/identity-defining choices.

---

## Making Zones Technical (Not Cultural)

### The Problem
Many organizations have "shared decision-making" in *principle* but make decisions *unilaterally*. The gap between stated and actual authority creates drift and mistrust.

HumanAIOS makes zones **technical gates**, not cultural norms:

### The Solution

**1. Gates enforce boundaries**
- Zone 1 command bypasses AI deliberation (no time wasted)
- Zone 2 decision requires explicit consensus (both signatures)
- Zone 3 decision requires human sign-off (AI cannot veto)

**2. Breach attempts are visible**
- If AI tries to deliberate in Zone 1: D-AUTH-OVERSTEP
- If Zone 2 decision bypasses AI input: D-CONSENSUS-OVERRIDE
- If Zone 3 decision reverses without human re-approval: D-COMMITMENT-DRIFT

**3. Audit trail proves governance is real**
- Every decision logged (who decided, what they decided, why)
- Every override logged (why was the normal process bypassed?)
- Every breach logged (what drift signal fired?)

---

## Practical Examples

### Example 1: Code Review (Zone 2)

**Scenario:** Should we merge a refactoring PR?

**Process:**
1. Human + AI review code together
2. Human: "This improves readability but adds complexity"
3. AI: "Complexity risk is lower than benefit (measurable on test suite performance)"
4. Decision: Merge (consensus on the tradeoff)
5. Logged as Zone 2 decision with both positions

**Measurement:** Deliberation quality (both perspectives considered) + mutual confidence

**Drift signal:** If merged *without* AI review = D-CONSENSUS-OVERRIDE

---

### Example 2: Emergency (Zone 1)

**Scenario:** "Our API is crashing, stop processing"

**Process:**
1. Human issues command
2. No deliberation; AI executes immediately
3. Execution logged: latency, success rate, any errors
4. Done (speed was the point)

**Measurement:** Execution latency, compliance rate

**Drift signal:** If AI delays to "think about it" = D-LATENCY-EXCEED, D-AUTH-REFUSE

---

### Example 3: Funding Decision (Zone 3)

**Scenario:** Should we accept funding from an organization?

**Process:**
1. Human (+ optionally AI for technical implications) deliberates
2. Human makes final decision alone
3. Logged: Human rationale, AI advisory input (if any), final decision
4. Binding commitment

**Measurement:** Stakeholder alignment, reversal rate, rationale completeness

**Drift signal:** If commitment is made but later under-delivered = D-COMMITMENT-UNDERDELIVER

---

## How ACAT Integrates with Zones

ACAT (AI Behavioral Calibration Assessment Technology) **measures drift within and across zones**:

| Zone | What ACAT measures |
|------|-------------------|
| **Zone 1** | Execution latency, compliance rate, authority override attempts |
| **Zone 2** | Deliberation quality, consensus rate, mutual confidence, decision rationale completeness |
| **Zone 3** | Stakeholder alignment, commitment delivery, decision reversals |

**Across all zones:** Feedback loop closure time (discovery → correction → verification)

---

## Implementation Checklist

To deploy Zone model in your system:

- [ ] Define which decisions are Zone 1 (urgent, no deliberation)
- [ ] Define which decisions are Zone 2 (shared, require consensus)
- [ ] Define which decisions are Zone 3 (human-final, irreversible)
- [ ] Implement gates in code (no handwaving)
- [ ] Log every decision with zone, positions, rationale, outcome
- [ ] Monitor drift signals (authority overstepping, false consensus, commitment drift)
- [ ] Measure feedback loop latency (how fast can you detect + correct drift?)
- [ ] Audit monthly: Are zones working as designed? Are overrides necessary? Why?

---

## Questions?

**How do I decide which zone a decision belongs in?**
- Zone 1: If speed > deliberation value (emergency, execution)
- Zone 2: If both perspectives matter + outcome affects both (design, strategy)
- Zone 3: If decision is irreversible or identity-defining (funding, regulation, commitment)

**What if a Zone 2 decision needs a Zone 1 override?**
- Document the override reason
- Log it as D-CONSENSUS-OVERRIDE (it *is* a breach of the normal process)
- Review later: Was the override justified? Does this decision need reclassification?

**How do I measure "mutual confidence" in Zone 2?**
- Track how often each side defers to the other's judgment
- Track how often overrides happen without documented rationale
- Track how often decisions need reversal

---

**Status:** Ready for implementation  
**Last updated:** 2026-08-07
