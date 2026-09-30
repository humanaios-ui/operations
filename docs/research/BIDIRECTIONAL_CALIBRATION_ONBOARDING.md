# Bidirectional Calibration Onboarding

Status: PROVISIONAL SESSION EVIDENCE
Date: 2026-09-30

## Purpose

HumanAIOS onboarding includes an observer-first human/AI calibration protocol. It does not classify a person into a fixed learning style. It gathers provisional behavioral evidence about how information is represented, traced, corrected, retained, disrupted, and recovered, then adapts the interaction contract while keeping every adaptation challengeable.

## Canonical two-thread loop

```text
EXPERIMENT THREAD
PREFLIGHT / H0
 -> STIMULUS
 -> HUMAN TRACE (uninterrupted)
 -> TRACE FREEZE
 -> MACHINE TRACE
 -> COMPARE
 -> CONVERGENCE | DIVERGENCE | UNRESOLVED | DELAYED | INTERFERENCE

SYSTEM THREAD (only after trace freeze)
 -> DESIGN-DELTA CHECK
 -> DELTA RECEIPT: what changed | what did not | evidence | status
 -> RETEST
 -> PROVISIONAL | REPLICATED | WARRANTED | WITHDRAWN
```

The System Thread must never leak expected answers into an open Human Trace. Calibration remains distinct from warrant, authorization, and enforcement.

## Requirements

- REQ-BO-001 OBSERVER_FIRST: do not reveal the expected/correct result before the participant completes and freezes their trace.
- REQ-BO-002 PARALLEL_MODALITY: preserve concurrent reported modalities; do not force a single modality label.
- REQ-BO-003 IN_LOOP_CORRECTION: retain the initial trace and the correction.
- REQ-BO-004 VERSIONED_STATE: when overwrite produces interference, test explicit state versions and preserve history.
- REQ-BO-005 RESOLUTION_NE_OUTPUT: distinguish internally resolved value from explicit program output.
- REQ-BO-006 INTERFERENCE_AS_EVIDENCE: capture distraction, blur, memory loss, and environmental noise without backfilling.
- REQ-BO-007 HALT_RESET: preserve last valid state and reset when clarity degrades.
- REQ-BO-008 PROVENANCE_TRACE: separately store stimulus, human trace, machine trace, comparison, correction, and design delta.
- REQ-BO-009 DISCOVERY_NE_TRAINING: teaching follows trace freeze in discovery mode.
- REQ-BO-010 LIVE_DESIGN_SHADOW: behavioral observations may immediately create provisional design deltas; retest before warranting.
- REQ-BO-011 UNRESOLVED_IS_VALID: never force a value when the participant reports no resolution.
- REQ-BO-012 DELAYED_RESOLUTION: retain later resolutions separately with latency/order and participant confidence; never overwrite the initial unresolved trace.
- REQ-BO-013 ACTIVE_FOCUS: represent currently salient/“hero” state separately from preserved state.
- REQ-BO-014 REALTIME_DELTA_LEDGER: after each frozen comparison, run a system-delta check and emit a compact receipt without contaminating the next human trace.
- REQ-BO-015 SUBJECTIVE_OBJECTIVE_BOUNDARY: introspective reports are subjective observations. Machine semantics, protocol events, and controlled manipulations can provide objective comparators; neither converts a single subjective trace into an objective cognitive claim.
- REQ-BO-016 COGNITIVE_CLUE_NE_CLAIM: a repeatable task-bound pattern may become a cognitive clue/hypothesis; it is not a stable cognitive claim without independent validation.

## Gateway-style state discipline

Use a repeatable operational entry/reset sequence: establish H0, capture environmental interference and internal clarity, introduce one bounded stimulus, freeze the trace, compare, then explicitly close or halt the trial. This borrows the operational value of staged awareness-training protocols without asserting metaphysical mechanisms or treating introspective reports as independently verified facts.

## Warrant rule

A successful single trial may create a provisional design delta. It does not establish a permanent cognitive trait. Adaptations move through PROVISIONAL -> REPLICATED -> WARRANTED, or are WITHDRAWN when falsified.

## Ratified runtime rule

The experiment and software-design work now execute in parallel. The experiment produces evidence; the design shadow consumes only frozen evidence. System updates are indicated at the point they arise rather than reconstructed retrospectively.
