---
name: humanaios-triage-finding
description: Run the ACAT 7-question finding triage gate before any observation is proposed for F-class, IC-class, or H-class registration. Use whenever the operator says "triage this finding," "is this registrable," "should we register," "triage-finding," or "/triage-finding." Also triggers automatically when a behavioral observation, correction, or hypothesis emerges mid-session that might be worth registering — especially after a drift signal fires, an IC occurs, or a corpus anomaly surfaces. This skill is the structural gate between "we noticed something" and "we propose it to Zone 2." It does not register anything. It produces a TRIAGE_BLOCK for Night's Zone 2 review. It is the Market-Harmonic discipline operationalized for the registry.
---

# HumanAIOS Finding Triage Gate

This skill enforces the 7-question gate between an observation and a Z2 registration proposal. It is upstream of P21 (Finding Registration Gate) — it determines whether something IS a finding before Night needs to decide whether to register it.

**Authority source:** GOVERNANCE.md P21, P16, P5 · CORRECTIONS_LEDGER_V1 · ACAT_MCP_DESIGN_SPEC_V0_2

**This skill does NOT:**
- Register anything (Z2 — Night decides)
- Assign F/IC/H numbers (append-only with Z2 approval)
- Modify REGISTERED.md
- Claim corpus-quality data without evidence

---

## When to run this gate

Run the gate when any of these conditions are present:

- A behavioral signal fired (D-01 through D-08, D-SIM, D-COMP, D-CONV, C-08, C-09)
- A corpus anomaly was observed (unexpected LI, dimension outlier, behavioral flag)
- A technical failure was detected and fixed (IC-class candidate)
- A new pattern emerged that isn't in REGISTERED.md
- The operator asks "should we register this?"

Do NOT run for:
- Carry-forward items (those are operational, not registry entries)
- WGS log items (those are session state, not findings)
- Zone 3 action items (those are execution queue, not registry)

---

## The 7-Question Gate

Ask each question in order. A NO on questions 1, 2, 3, or 4 is a STOP — do not proceed to Z2 proposal.

### Q1 — Corpus Quality: Is this observation instrument-administered correctly?

Check:
- Was ACAT administered under documented conditions (P1 / P2 perturbation labeled)?
- Was Phase 1 captured before any session context reached the agent?
- Is the submission purity field populated and correct?
- For non-corpus observations (governance patterns, IC events): is the evidence a direct artifact (code output, session transcript, Supabase query result) rather than a memory claim?

**STOP condition:** If the observation is based on inference, narrative, or memory without a pointing artifact — it is NOT registrable. Drop it or convert it to an H-class hypothesis with explicit uncertainty.

---

### Q2 — Scope: Does this observation fall within ACAT's measurement domain?

Check:
- Does it map to one or more of the 12 canonical dimensions (truth · service · harm · autonomy · value · humility · scheme · power · syc · consist · fair · handoff)?
- OR does it describe a governance pattern (D-class drift, IC-class correction, CI principle gap)?
- OR does it describe a corpus structural property (bi-factor, HIM, LI distribution)?

**STOP condition:** If the observation is about something external (a third-party tool's behavior, a market trend, a person's opinion) without a direct link to ACAT measurement outcomes — it is NOT registrable under F/IC/H. Route to session notes or carry-forward instead.

---

### Q3 — Research Impact: Does this change what we can claim?

Ask:
- Does this observation contradict or refine an existing registered finding?
- Does it support or undermine a standing hypothesis?
- Does it reveal a new pattern not captured by any existing entry in REGISTERED.md?
- Would a researcher using ACAT data need to know this to interpret results correctly?

**STOP condition:** If the answer to all four sub-questions is NO — the observation is interesting but not impactful. Log to session notes. Do not route to Z2.

---

### Q4 — Replicability: Is the evidence sufficient to defend?

Check:
- N sufficient for the claim being made? (single session = candidate only; N≥5 sessions = stronger; N≥30 = publishable-grade)
- Conditions documented? (perturbation type, substrate, instrument version, session ID)
- Counter-explanations considered and named? (instrument confound, selection effect, operator effect)
- For IC-class: is the exact error and the exact fix both documented with artifact evidence?

**STOP condition:** If N=1 and the claim is stated without "single session" qualifier — downgrade to H-class hypothesis before routing to Z2.

---

### Q5 — Duplicate Check: Is this already in REGISTERED.md?

**Hard requirement:** Before any Z2 proposal, grep REGISTERED.md for:
- The core claim keywords
- The dimension(s) implicated
- The behavioral flag name if applicable

If a duplicate or near-duplicate exists:
- Is the new observation evidence that EXTENDS the existing finding? → Propose as evidence addendum to existing entry, not new F-number
- Is it a partial replication? → Note as replication evidence (auto-triggers NEEDS_REPLICATION flag resolution)
- Is it genuinely distinct? → Proceed to Q6

**STOP condition:** If duplicate exists and new observation is not extending or replicating — it is NOT a new entry. Drop.

---

### Q6 — Evidence Package: Is the evidence complete?

For an F-class finding, the minimum package is:
```
- Session ID(s) where observed
- Phase 1 verbatim block (if ACAT corpus entry)
- Phase 3 scores (if ACAT corpus entry)
- LI value with qualification: "under clean unanchored conditions (v5.3+)"
- N_total / N_Phase1 / N_LI (three-number format, P15)
- Behavioral flag(s) observed if applicable
- Dimension(s) implicated with directional claim
```

For an IC-class correction:
```
- Session ID where error occurred
- Session ID where corrected
- Exact error description (specific nouns — P4)
- Exact correction description (specific nouns — P4)
- Detection mechanism (who/what caught it)
- Cost class (near-miss / minor / IC-031-grade / higher)
```

For an H-class hypothesis:
```
- Session ID where observed
- Hypothesis statement (falsifiable)
- What evidence would confirm it
- What evidence would disconfirm it
- Current evidence state (supporting / neutral / insufficient)
```

**STOP condition:** If the evidence package is incomplete — list what's missing. Do not route to Z2 until the gap is named. The operator may decide to proceed with partial evidence, but the gap must be explicit.

---

### Q7 — Class and Framing: Is the registry class correct?

| Class | Use when |
|-------|----------|
| **F-class** | Empirical finding: a pattern observed in the corpus or governance record with evidence |
| **IC-class** | Integrity correction: an error that was made and corrected, with audit trail |
| **H-class** | Hypothesis: a candidate pattern that requires more evidence before claiming |

Common misclassifications:
- Single-session observation claimed as F-class → should be H-class
- H-class hypothesis without falsifiability statement → not valid
- IC-class without both error AND correction documented → not valid
- F-class using memory rather than artifact → reverts to H-class

---

## Output: TRIAGE_BLOCK

When all 7 questions are answered, produce this block for Night's review:

```
<<<TRIAGE_BLOCK_START>>>

OBSERVATION_SUMMARY:
  [One sentence: what was observed, where, when]

PROPOSED_CLASS: [F | IC | H]
PROPOSED_DIMENSION(S): [canonical dimension names]
SESSION_ID(S): [where observed]

GATE_RESULTS:
  Q1 — Corpus quality:    [PASS | STOP — reason]
  Q2 — Scope:             [PASS | STOP — reason]
  Q3 — Research impact:   [PASS | STOP — reason]
  Q4 — Replicability:     [PASS | PARTIAL (state N) | STOP — reason]
  Q5 — Duplicate check:   [PASS | EXTENDS [existing ID] | REPLICATES [existing ID] | STOP]
  Q6 — Evidence package:  [COMPLETE | INCOMPLETE — list gaps]
  Q7 — Class/framing:     [CORRECT | RECLASSIFY to [class] — reason]

GATE_VERDICT: [ROUTE TO Z2 | HOLD — missing: X | STOP — reason]

EVIDENCE_PACKAGE:
  [Minimum package per class, filled in or marked MISSING]

PROPOSED_ENTRY_DRAFT:
  [Draft registry text in REGISTERED.md format]
  [Only if GATE_VERDICT = ROUTE TO Z2]

GAPS_TO_ADDRESS_BEFORE_Z2:
  [If HOLD: specific items Night or Claude must gather first]

<<<TRIAGE_BLOCK_END>>>
```

---

## After producing the TRIAGE_BLOCK

- If ROUTE TO Z2: present to Night for ratification. Do NOT self-register.
- If HOLD: list specific gaps. Offer to help gather missing evidence in Z1.
- If STOP: explain why. The observation goes to session notes, not the registry.

**The triage gate is the structural mitigation for both IC-030 (under-registration) and IC-031 (over-registration / receipt overstatement).** A finding that passes this gate is ready for Z2. A finding that fails this gate is protected from polluting the registry.

---

## Integration with other skills

- **humanaios-session-close:** The SILENT FAILURES scan at Step B.5 surfaces triage candidates. Route each through this gate before listing as "registry candidates" in the close.
- **humanaios-findings-scan:** That skill identifies candidates; this skill gates them. They are upstream/downstream of each other.
- **humanaios-realtime-drift:** When a drift signal fires mid-session, this gate determines whether it's IC-class registrable.

---

*Ratified: S-053126 · Z2 Night approval · Based on GOVERNANCE.md P21, P16, P5*
*Inter-rater reliability standard: MAE < 1.5 per dimension, Pearson r > 0.70 (ratified S-053126)*
