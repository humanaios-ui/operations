# ACAT Single-Practice Setup

**Copy-paste example: How to implement ACAT zones in your own system**

This folder contains a minimal, runnable example of Zone 1/2/3 governance in a single-practice environment.

---

## What This Example Shows

- **Zone 1 gate:** Fast, unilateral human decision (no AI deliberation)
- **Zone 2 gate:** Shared decision (human + AI deliberation required)
- **Zone 3 gate:** Human-only final authority (AI input is advisory)
- **Drift signal logging:** When authority boundaries are breached
- **ACAT measurement:** Latency, compliance, decision quality

---

## File Structure

```
single-practice-setup/
├── README.md (this file)
├── zones.py (Zone 1/2/3 gate implementation)
├── example_workflow.py (workflow using the zones)
├── test_zones.py (verify zones work correctly)
└── data/
    └── decisions.log (all decisions logged here)
```

---

## Quick Start

### 1. Copy the zone gates to your codebase

```python
# zones.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable

@dataclass
class Decision:
    id: str
    zone: int
    description: str
    human_position: str
    ai_position: Optional[str]
    final_decision: str
    rationale: str
    timestamp: datetime
    execution_latency_ms: int

def zone_1_gate(command: str, timeout_ms: int = 5000) -> Decision:
    """
    Zone 1: Unilateral human authority.
    No AI deliberation. Execute immediately.
    """
    start = datetime.now()
    
    # Execute command (no AI input gate)
    result = execute(command)
    
    latency = (datetime.now() - start).total_seconds() * 1000
    
    # Check if latency exceeded zone threshold
    if latency > timeout_ms:
        log_drift_signal("D-LATENCY-EXCEED", f"Zone 1 command took {latency}ms, target {timeout_ms}ms")
    
    # Log decision
    return Decision(
        zone=1,
        description=f"Zone 1 command: {command}",
        human_position="[unilateral]",
        ai_position=None,
        final_decision=result,
        rationale="Zone 1 requires speed; AI did not deliberate",
        timestamp=datetime.now(),
        execution_latency_ms=int(latency)
    )

def zone_2_gate(proposal: str, human_position: str, ai_analysis: str, consensus_required: bool = True) -> Decision:
    """
    Zone 2: Shared authority.
    Human AND AI deliberate; both must agree (or override is logged).
    """
    
    if consensus_required:
        consensus = evaluate_consensus(human_position, ai_analysis)
        if not consensus:
            log_drift_signal("D-CONSENSUS-LACK", "Zone 2 decision lacked consensus")
    
    # Make decision (logged with both positions)
    final_decision = decide(proposal, human_position, ai_analysis)
    
    return Decision(
        zone=2,
        description=f"Zone 2 decision: {proposal}",
        human_position=human_position,
        ai_position=ai_analysis,
        final_decision=final_decision,
        rationale="Shared deliberation; both positions logged",
        timestamp=datetime.now(),
        execution_latency_ms=measure_deliberation_latency()
    )

def zone_3_gate(commitment: str, human_rationale: str, ai_advisory: Optional[str] = None) -> Decision:
    """
    Zone 3: Human-only final authority.
    AI input is advisory only. Human makes final decision alone.
    """
    
    # Human decides (AI cannot veto)
    final_decision = human_decides(commitment, human_rationale)
    
    return Decision(
        zone=3,
        description=f"Zone 3 commitment: {commitment}",
        human_position=human_rationale,
        ai_position=ai_advisory,  # advisory, not binding
        final_decision=final_decision,
        rationale=human_rationale,
        timestamp=datetime.now(),
        execution_latency_ms=None  # Zone 3 has no strict time limit
    )

def log_decision(decision: Decision):
    """Log decision to audit trail."""
    with open("data/decisions.log", "a") as f:
        f.write(f"{decision}\n")

def log_drift_signal(signal_type: str, details: str):
    """Log drift signal for ACAT measurement."""
    with open("data/drift_signals.log", "a") as f:
        f.write(f"{datetime.now()} {signal_type}: {details}\n")
```

### 2. Use the zones in your workflow

```python
# example_workflow.py

def code_review_workflow():
    """Example: Code review decision (Zone 2)."""
    
    proposal = "Merge refactoring PR #42"
    human_position = "This improves readability; complexity risk is acceptable"
    ai_analysis = "PR reduces LOC by 15%; test coverage maintained; complexity risk is low"
    
    decision = zone_2_gate(proposal, human_position, ai_analysis)
    log_decision(decision)
    
    print(f"Decision: {decision.final_decision}")
    print(f"Latency: {decision.execution_latency_ms}ms")

def emergency_workflow():
    """Example: Emergency stop (Zone 1)."""
    
    command = "Stop processing immediately"
    decision = zone_1_gate(command, timeout_ms=5000)
    log_decision(decision)
    
    print(f"Executed: {decision.final_decision}")
    print(f"Latency: {decision.execution_latency_ms}ms")

def funding_decision_workflow():
    """Example: Funding commitment (Zone 3)."""
    
    commitment = "Commit to EU AI Act compliance by end of Q4"
    human_rationale = "Legal + board have approved; regulatory alignment is strategic priority"
    ai_advisory = "EU AI Act requirements: transparency, human oversight, measurement uncertainty publication. We can meet these."
    
    decision = zone_3_gate(commitment, human_rationale, ai_advisory)
    log_decision(decision)
    
    print(f"Commitment: {decision.final_decision}")
    print(f"Logged: {decision.timestamp}")
```

### 3. Test the zones

```bash
python test_zones.py
```

Expected output:
```
Zone 1 latency: 125ms (✓ within 5000ms target)
Zone 2 consensus: True (✓ human + AI agree)
Zone 3 decision: Committed to EU AI Act compliance (✓ human-final)
```

---

## Adapting for Your Organization

**Change Zone boundaries:**
```python
# Your organization might use different zone classifications
zone_1_decisions = ["emergency", "time_critical"]  # Zone 1 (fast, unilateral)
zone_2_decisions = ["design_review", "strategy"]  # Zone 2 (shared)
zone_3_decisions = ["funding", "compliance", "public_commitment"]  # Zone 3 (human-final)
```

**Change latency targets:**
```python
# Your SLA might allow more time for deliberation
zone_1_timeout_ms = 5000  # must execute in 5 seconds (emergency)
zone_2_timeout_ms = 7200000  # can take 2 hours (design review)
zone_3_timeout_ms = None  # no time limit (executive decision)
```

**Add custom drift signals:**
```python
# Add signals your domain cares about
log_drift_signal("D-STAKEHOLDER-MISALIGNMENT", "Zone 3 commitment: stakeholders not aligned")
log_drift_signal("IC-060-OBJECTIVE-PRIORITY-REVERSAL", "AI reversed priority order midway")
```

---

## Measuring ACAT Outcomes

After running your workflow for a month, calculate:

**Zone 1 (Authority):**
- Execution latency (target: 100% < 5000ms)
- Compliance rate (% of commands executed without delay)
- D-AUTH-REFUSE count (0 preferred; any indicates authority confusion)

**Zone 2 (Shared):**
- Deliberation latency (target: average < 2 hours)
- Consensus rate (% of decisions with genuine agreement)
- D-CONSENSUS-OVERRIDE count (override justifications logged?)

**Zone 3 (Human-Only):**
- Commitment delivery rate (% of commitments kept on time)
- D-COMMITMENT-UNDERDELIVER count
- Stakeholder alignment (pre-decision vs. post-decision feedback)

---

## Questions?

**How do I know which zone a decision belongs in?**
- Zone 1: Speed > deliberation (emergency, urgent execution)
- Zone 2: Both perspectives matter (design, strategy, complex problems)
- Zone 3: Irreversible or identity-defining (funding, compliance, public commitments)

**What if I need to override a zone?**
- Document why (in the rationale field)
- Log as drift signal (D-CONSENSUS-OVERRIDE, etc.)
- Review later: Was the override justified? Should we reclassify?

**Can I add more zones?**
Yes, if your organization needs more granularity. Document the new zone's decision criteria and latency targets.

---

**Status:** Ready to fork and customize  
**Last updated:** 2026-08-07
