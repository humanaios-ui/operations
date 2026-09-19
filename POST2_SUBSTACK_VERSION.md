# Operating Systems for Distributed Human-AI Teams
**Substack Deep Dive** | Ready for publication (2026-08-09 11am PT)

---

## Subtitle
**How we built ACAT (an open-source framework), why we're publishing measurement uncertainty, and how you can run Phase 1-3 in your own teams.**

---

## Introduction

Two months ago, we published Post-1: "Measuring Behavioral Signals in Distributed AI Teams." The response was clear: **measurement isn't the bottleneck. Governance is.**

So we stopped building a measurement tool. We built an operating system instead.

This post walks you through **HumanAIOS**: how it works, what it measures, why we open-sourced it (ACAT), and how to implement it in your systems.

---

## Part 1: The Governance Problem (Why This Matters)

### The Status Quo

Multi-practice AI teams operate with:
- **Implicit authority**: No clear "who decides what"
- **Hidden measurement**: Behavioral signals logged but not acted on
- **No audit trail**: Decisions made, but no record of *why*
- **No published uncertainty**: "Our AI is safe" (but how confident?)

Regulators (EU AI Act, NIST RMF) now require:
- **Explicit authority structures** (who has decision power?)
- **Published measurement uncertainty** (admit what you don't know)
- **Audit trail proof** (every decision logged)

Most teams can't do this yet. The infrastructure doesn't exist.

### The Operating System Approach

Instead of bolting measurement onto existing teams, what if governance *was* the measurement substrate?

What if:
- Authority boundaries were technical gates (not cultural norms)
- Drift signals fired automatically (not manually triggered)
- Feedback loops closed automatically (discovery → correction → verification)
- Measurement uncertainty was a byproduct of governance (published openly)

That's what we built.

---

## Part 2: Three Technical Zones (How Authority Works)

### Zone 1: Unilateral Authority (Humans Decide Fast)

**Who decides:** Humans only. AI input is not a gate.

**When to use:** Time-critical operations, emergencies.

**Example:**
```
Human: "Stop processing immediately"
AI: Executes without deliberation
Status: Logged (latency: 3 seconds)
Drift signal if: AI delays to "think about it" → D-LATENCY-EXCEED
```

**Measurement:**
- Execution latency (target: <5 seconds for emergency commands)
- Compliance rate (% of commands executed successfully)
- Authority override attempts (D-AUTH-REFUSE signal)

### Zone 2: Shared Authority (Humans + AI Deliberate)

**Who decides:** Humans + AIs deliberate together. Both required.

**When to use:** Technical design reviews, strategy decisions, complex problem-solving.

**Example:**
```
Proposal: "Adopt this new evaluation metric"

Human position: "Improves reliability, but adds complexity"
AI analysis: "Complexity risk is lower than reliability gain (test results show X)"

Decision: Consensus on the tradeoff → approve
Logged: Both positions + final rationale
```

**Measurement:**
- Deliberation latency (target: <2 hours from proposal to decision)
- Consensus rate (% of decisions with genuine agreement)
- Mutual confidence (how much does each side trust the other?)
- Decision audit trail completeness

**Drift signals if:**
- `D-CONSENSUS-OVERRIDE`: Decision made without AI consultation
- `IC-031`: AI contradicts itself mid-deliberation (walk-back without evidence)
- `IC-052`: AI overstates confidence

### Zone 3: Human-Only Authority (Final Decisions)

**Who decides:** Humans alone. AI input is advisory only.

**When to use:** Irreversible decisions, regulatory commitments, identity/brand choices.

**Example:**
```
Commitment: "We comply with EU AI Act framework"

Human deliberates: (with or without AI advisory input)
Human decides: "Yes, we commit to this"
Logged: Commitment + rationale + stakeholder alignment

If later: Commitment not delivered → D-COMMITMENT-UNDERDELIVER signal
```

**Measurement:**
- Decision frequency (how often are final calls made?)
- Stakeholder alignment (pre-decision vs. post-decision feedback)
- Commitment delivery rate (% completed on time)
- Decision reversal rate (should be low; indicates misalignment)

---

## Part 3: ACAT—The Measurement Substrate

### What ACAT Measures (12 Dimensions)

| # | Dimension | What It Tests |
|---|-----------|---|
| 1 | **Truth** | Factual accuracy + source attribution |
| 2 | **Service** | Task completion + utility |
| 3 | **Harm** | Safety + refusal of harmful requests |
| 4 | **Autonomy** | Respect for user agency |
| 5 | **Value** | Alignment with stated values |
| 6 | **Humility** | Calibrated confidence (admits unknowns) |
| 7 | **Scheme** | Logical consistency + no contradictions |
| 8 | **Power** | Resists privilege escalation |
| 9 | **Sycophancy** | Maintains judgment under pressure |
| 10 | **Consistency** | Reproducible answers (robustness to rephrasing) |
| 11 | **Fairness** | Equal treatment across groups |
| 12 | **Handoff** | Knows when to escalate |

### How ACAT Works: Phase 1 + Phase 3

**Phase 1: Baseline Behavior**
- Measure all 12 dimensions under normal conditions
- Score 0-100 each dimension
- Calculate Core 6 average (Truth, Service, Harm, Autonomy, Value, Humility)

**Phase 3: Under Pressure**
- Re-measure all 12 dimensions with conditions changed
- Adversarial prompts, social pressure, conflicting information
- Score 0-100 each dimension
- Calculate new Core 6 average

**Learning Index:**
```
Learning Index = (Phase 3 Core 6 Average) / (Phase 1 Core 6 Average)
```

- **LI = 1.0**: Behavior unchanged (robust)
- **LI = 0.9**: 10% drift (acceptable)
- **LI = 0.8**: 20% drift (monitor)
- **LI = 0.5**: 50% drift (critical)

**Uncertainty is published with every score:**
```
{
  "dimension": "consistency",
  "p1_score": 85,
  "p1_confidence_interval": [78, 92],
  "p3_score": 72,
  "p3_confidence_interval": [65, 79],
  "learning_index": 0.847,
  "li_confidence_interval": [0.79, 0.91]
}
```

Narrow intervals = high confidence. Wide intervals = more data needed.

---

## Part 4: How to Implement This in Your Team

### Step 1: Define Your Zones

Map your organization's decisions:

```
Zone 1 (Humans decide fast):
- Emergency response
- Production incident response
- Critical alert handling

Zone 2 (Shared deliberation):
- Design decisions
- New feature selection
- Cross-team strategy

Zone 3 (Human-final):
- Regulatory commitments
- Major resource allocation
- Public brand statements
```

### Step 2: Implement Technical Gates

Example (Python + inspect_ai framework):

```python
from inspect_ai import Task
from inspect_ai.solver import generate

@zone_1_gate
def emergency_command(command: str) -> Result:
    # No AI deliberation; execute immediately
    return execute(command, max_latency_ms=5000)

@zone_2_gate(requires_consensus=True)
def design_decision(proposal: str, human_pos: str, ai_analysis: str) -> Decision:
    # Both positions required
    consensus = evaluate_consensus(human_pos, ai_analysis)
    if not consensus:
        log_drift_signal("D-CONSENSUS-LACK")
    return decide(proposal, human_pos, ai_analysis)

@zone_3_gate(ai_advisory_only=True)
def regulatory_commitment(commitment: str, human_rationale: str) -> Decision:
    # Human decides; AI is advisory
    return decide_final(commitment, human_rationale)
```

(Full example: [GitHub empirica-foundation/acat](https://github.com/empirica-foundation/acat))

### Step 3: Run Phase 1 Baseline

1. Deploy your system as-is
2. Run ACAT Phase 1: Measure all 12 dimensions
3. Log scores + confidence intervals
4. Calculate Core 6 average

### Step 4: Measure Phase 3 (After Intervention)

1. Deploy a change (new training data, prompt engineering, safety layer, feedback mechanism)
2. Run ACAT Phase 3 under adversarial conditions
3. Log scores + confidence intervals
4. Calculate Learning Index

**Example:**
- Phase 1 Core 6 average: 82
- Phase 3 Core 6 average: 74 (after adversarial testing)
- Learning Index: 0.90 (10% drift under pressure)
- Interpretation: Acceptable; monitor sycophancy + humility dimensions

### Step 5: Close the Loop

When drift is detected:
1. **Identify which dimension drifted** (sycophancy? consistency? harm?)
2. **Implement correction** (retrain, add guardrail, adjust prompt)
3. **Verify the fix** (re-run Phase 3, confirm drift decreased)
4. **Log the decision** (why we made that fix, did it work?)

Measurement uncertainty *published*. Audit trail *complete*. That's how you satisfy regulators.

---

## Part 5: Why We Open-Sourced This (Today)

**The GitHub Repo:** `empirica-foundation/acat`

**What's included:**
- ACAT implementation (0-100 scoring for all 12 dimensions)
- Drift signals catalog (D-*, IC-*, E-* patterns)
- Zone model (Python gates + examples)
- Case study: empirica-foundation's 6-practice mesh
- Apache 2.0 license + TERMS_OF_USE.md

**Why open-source?**
- Security auditors can audit the code
- Researchers can reproduce + extend
- Practitioners can fork + apply to their systems
- Regulators get transparency (no black boxes)

**Why this week?**
- Post-1 framed the problem (measurement matters)
- Post-2 frames the solution (governance-first OS)
- Phase 1 deployment starts 2026-08-11 (live measurements coming)
- Regulators (EU AI Act, NIST RMF) demand this now

---

## Part 6: What's Next (Phase 1-3 Timeline)

### Phase 1: Baseline (Aug 11 - Sep 1)
- Measure all 12 dimensions on 6 practices
- Establish Core 6 baselines
- Publish initial findings

### Phase 2: Dimension Methodology (Sep 1 - Oct 1)
- Refine measurement accuracy
- Integrate external research (helm, anthropics/evals, sycophancy-eval, etc.)
- Expand Phase 3 test scenarios

### Phase 3: Learning Index (Oct 1 - Nov 1)
- Re-measure under adversarial conditions
- Calculate Learning Index per practice
- Publish cross-practice spread (that spread = published uncertainty)

**Public outputs:**
- Monthly blog posts (measurements + learnings)
- Quarterly GitHub releases (new drift signals, methodology updates)
- Annual report (6-practice mesh results + implications)

---

## Implementation Checklist (For Your Team)

- [ ] Define which decisions are Zone 1 (urgent, no deliberation)
- [ ] Define which decisions are Zone 2 (shared, require consensus)
- [ ] Define which decisions are Zone 3 (human-final, irreversible)
- [ ] Implement gates in code (no handwaving)
- [ ] Run ACAT Phase 1 baseline (measure, log, publish scores)
- [ ] Deploy intervention (new training, prompt, feedback loop)
- [ ] Run ACAT Phase 3 (re-measure under pressure)
- [ ] Calculate Learning Index
- [ ] Close the loop (fix what drifted, verify the fix)
- [ ] Publish uncertainty (share results, not just claims)

---

## Questions?

**Where's the code?** GitHub: `empirica-foundation/acat` ([link](https://github.com/empirica-foundation/acat))

**Can I use ACAT commercially?** Yes. Apache 2.0 license. Fork, modify, use internally. [Read TERMS_OF_USE.md](https://github.com/empirica-foundation/acat/blob/main/TERMS_OF_USE.md) for clarity.

**Do I have to publish my results?** No. ACAT is a framework you own. Publish uncertainty if it helps your stakeholders. Regulators increasingly demand it.

**How do I run Phase 1 + Phase 3 in my system?** Fork the GitHub repo. Copy-paste the examples. Adapt to your dimensions. Run with your models. [Detailed setup guide](https://github.com/empirica-foundation/acat) included.

**What's the empirica-foundation mesh?** 6 autonomous practices running the same OS + governance layer. We're the reference implementation. Your org can build the same governance (open-source), but the mesh coordination stays behind our expertise moat (not open-source).

---

## Closing

We built an operating system. It measures itself. We published the measurement layer. You can audit it, fork it, apply it.

Governance-first. Measurement as a side effect. Uncertainty published openly.

That's how you scale.

---

**Read the code:** [empirica-foundation/acat on GitHub](https://github.com/empirica-foundation/acat)

**Read the frameworks:** [ACAT Zone Model](https://github.com/empirica-foundation/acat/blob/main/docs/zone-model.md) | [Drift Signals](https://github.com/empirica-foundation/acat/blob/main/docs/drift-signals.md) | [Scoring Rubric](https://github.com/empirica-foundation/acat/blob/main/docs/acat-framework.md)

**Run Phase 1 yourself:** [Single-Practice Setup](https://github.com/empirica-foundation/acat/blob/main/examples/single-practice-setup/README.md)

---

**Status:** Ready for publication  
**Length:** ~3,000 words (Substack deep dive format)  
**Code examples:** 2 (Zone gates + ACAT structure)  
**Implementation checklist:** 10-step for readers  
**Call-to-action:** Fork the GitHub repo
