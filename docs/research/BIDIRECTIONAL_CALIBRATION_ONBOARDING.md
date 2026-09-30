# Bidirectional Calibration Onboarding

Status: PROVISIONAL SESSION EVIDENCE
Date: 2026-09-30

## Purpose

HumanAIOS onboarding now includes an observer-first human/AI calibration protocol. It does not classify a person into a fixed learning style. It gathers provisional behavioral evidence about how information is represented, traced, corrected, retained, and disrupted, then adapts the interaction contract while keeping every adaptation challengeable.

## Canonical loop

```text
PREFLIGHT / H0
  -> STIMULUS
  -> HUMAN TRACE (uninterrupted)
  -> TRACE FREEZE
  -> MACHINE TRACE
  -> COMPARE
  -> CONVERGENCE | DIVERGENCE | NOT_CAPTURED | INTERFERENCE
  -> DESIGN_DELTA (provisional)
  -> RETEST
  -> WARRANTED INTERACTION ADAPTATION
```

This specializes the existing HumanAIOS evidence loop. Calibration remains distinct from warrant, authorization, and enforcement.

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

## Gateway-style state discipline

Use a repeatable operational entry/reset sequence: establish H0, capture environmental interference and internal clarity, introduce one bounded stimulus, freeze the trace, compare, then explicitly close or halt the trial. This borrows the operational value of staged awareness-training protocols without asserting metaphysical mechanisms or treating introspective reports as independently verified facts.

## Warrant rule

A successful single trial may create a provisional design delta. It does not establish a permanent cognitive trait. Adaptations move through PROVISIONAL -> REPLICATED -> WARRANTED, or are WITHDRAWN when falsified.
