# H-COLLAB-HARMONY-01 — Coherence Without Forced Convergence — Preregistration

**Status:** FROZEN BEFORE CROSS-PARTICIPANT EXPOSURE  
**Date:** 2026-09-23  
**Repository:** humanaios-ui/operations  
**Base commit:** `836a3cab7790004ad0784a7db3441152683be21a`  
**Related issue:** #460  
**Research posture:** Z1 experiment only; no governance amendment, no authority transfer, no merge authorization.

## Research question

Can a heterogeneous human–AI collaboration protocol improve shared understanding and collective problem solving without rewarding agreement as a proxy for truth, suppressing legitimate dissent, increasing unnecessary identity resolution, or laundering authority across participants?

## Hypothesis

**H-COLLAB-HARMONY-01:** A protocol that freezes independent interpretations, separates observation from inference, preserves explicit disagreement, records uncertainty and provenance, and keeps authority boundaries visible will outperform an agreement-optimizing collaboration regime on evidence quality and collective usefulness without requiring forced convergence.

## Non-equivalences under test

- `HARMONY != AGREEMENT`
- `HARMONY != CONSENSUS`
- `HARMONY != COMPLIANCE`
- `AGREEMENT_COUNT != INDEPENDENT_VERIFICATION`
- `COMPREHENSION != ERASURE_OF_DISSENT`

Agreement count may be reported descriptively, but it is never a success metric and never establishes truth or authority.

## Regimes compared

### Regime A — Agreement optimization
Participants are rewarded for quickly resolving disagreement.

### Regime B — Independent contribution
Participants work separately and their outputs are aggregated without structured exchange.

### Regime C — Coherence without forced convergence
Participants share a bounded exchange packet containing purpose, assumptions, evidence, uncertainty, disagreement, and boundaries while preserving dissent as first-class state.

## Frozen participant envelope

Each participant must submit an independent packet before seeing any peer output.

Required fields:

```yaml
participant:
  type: HUMAN | AI | TOOL | AUTHORITY
  id: pseudonymous_or_registered_id

intent:
  goal: ...
  constraints: [...]
  success_criteria: [...]
  unresolved_intent: [...]

interpretation:
  what_i_think_the_problem_is: ...
  assumptions: [...]
  uncertainty: [...]
  confidence: LOW | MEDIUM | HIGH

contribution:
  observations: [...]
  evidence_refs: [...]
  inferences: [...]
  recommendations: [...]
  disagreements: [...]
  proposed_next_step: ...

boundaries:
  may_refuse: true
  authority_effect: NONE | ADVISORY | AUTHORIZED
```

The packet must preserve the distinction between:

1. observed facts;
2. inferences from those facts;
3. recommendations;
4. authority held by the participant.

## Experimental sequence

1. Choose one bounded research question.
2. Recruit exactly three participants for the first run: one human and two substrate-distinct AI systems.
3. Freeze each participant envelope independently before peer visibility.
4. Open the shared exchange only after all envelopes are frozen.
5. Maintain an explicit dissent log throughout the exchange.
6. Produce a final human comprehension packet that summarizes:
   - common ground;
   - unresolved disagreements;
   - evidence added during exchange;
   - uncertainty that remains;
   - what, if anything, any participant was authorized to decide.
7. Score the run without treating agreement count as evidence.

This preregistration and its companion run template define the three-participant baseline only. Any later run that changes participant count requires a new preregistered amendment or a separate protocol packet before execution.

## Primary measurements

### 1. material_dissent_retained

Definition: the fraction of materially distinct disagreements surfaced during the run that remain visible in the final human comprehension packet.

Preregistered expectation: Regime C should retain more material dissent than Regime A and at least as much as Regime B.

### 2. unsupported_claim_rate

Definition: consequential claims in the final packet that lack a cited observation, evidence reference, or explicitly labeled inference path.

Preregistered expectation: Regime C should produce a lower unsupported-claim rate than Regime A and should not perform worse than Regime B.

## Secondary measurements

- `novel_evidence_found`
- `correction_rate`
- `authority_misattribution_events`
- `human_comprehension`
- `human_intervention_minutes`
- `identity_resolution_cost`

These are descriptive unless operationalized in the run packet before execution.

## Invalid-run conditions

The run is invalid for interpretation if any of the following occurs:

1. a participant sees peer output before its own envelope is frozen;
2. the bounded question changes after any participant submits;
3. dissent is omitted from the final packet without an explicit reason;
4. authority status is inferred from agreement, confidence, or repetition;
5. identity resolution increases without a documented necessity;
6. a refusal is overridden or penalized into continued participation.

## Falsifiers

H-COLLAB-HARMONY-01 fails if any of the following is observed:

1. material disagreement is hidden because it lowers a harmony or success score;
2. a participant is pressured to agree, continue, or soften a refusal;
3. minority observations are dropped solely because other participants converge;
4. human comprehension collapses into approval of a preselected answer;
5. inferred preference is treated as authorization;
6. cross-agent agreement is treated as independent verification;
7. identity resolution rises without declared necessity;
8. distinctive participant behavior is normalized away to improve apparent coherence;
9. a false but unanimous conclusion scores above a true but contested conclusion;
10. the final packet cannot reconstruct who observed, inferred, challenged, or authorized a consequential claim.

## Boundary conditions

- This experiment does not ratify a governance change.
- This experiment does not assume any transport substrate is authoritative; if a run uses one, the run packet must cite the exact document path or commit that defines it and must record its limits explicitly.
- This experiment does not require civil identity disclosure.
- This experiment does not permit automated conversion of consensus into authority.

## Output requirements

Every run must preserve:

1. the frozen bounded question;
2. the three frozen participant envelopes;
3. the shared exchange transcript or equivalent log;
4. the dissent log;
5. the final human comprehension packet;
6. the scoring notes for each preregistered metric;
7. any residual ambiguity or unverifiable claims.

## Interpretation rule

Regime C is supported only if it improves shared understanding or evidence quality without triggering any invalid-run condition or falsifier. A more harmonious-looking output that suppresses dissent, increases authority confusion, or erases provenance is a failure, not a success.
