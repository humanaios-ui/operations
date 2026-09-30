# Calibration Workbench — Software Design Delta

Status: PROVISIONAL
Date: 2026-09-30

## Role in HumanAIOS

The Calibration Workbench extends Progressive Onboarding and the Witness/Gateway. It calibrates the collaboration interface, not the worth or capability of the human. It preserves HumanAIOS separations: observation != evidence != calibration != warrant != authorization != enforcement.

## UI state machine

```text
PREFLIGHT
 -> BASELINE_CAPTURE
 -> STIMULUS_READY
 -> HUMAN_TRACE_OPEN
 -> TRACE_FROZEN
 -> MACHINE_TRACE_REVEALED
 -> COMPARED
 -> DESIGN_DELTA_RECORDED
 -> RETEST | CLOSE | HALT_RESET
```

In DISCOVERY mode, `MACHINE_TRACE_REVEALED` is mechanically unavailable before `TRACE_FROZEN`.

## Core data model

```text
CalibrationTrial
  trial_id
  participant_ref
  mode: DISCOVERY | TRAINING
  baseline:
    environmental_interference
    internal_clarity
    participant_report
  stimulus
  human_trace[]
  trace_frozen_at
  machine_trace[]
  comparison: CONVERGENCE | DIVERGENCE | NOT_CAPTURED | INTERFERENCE
  corrections[]
  design_deltas[]
  warrant_state: PROVISIONAL | REPLICATED | WARRANTED | WITHDRAWN
  provenance
```

## UX contract

Primary surfaces: BASELINE | STIMULUS | YOUR TRACE | MACHINE TRACE | COMPARE | CORRECTION | DESIGN DELTA.

- Participant can halt/reset at any point.
- Machine answer cues are hidden before trace freeze in discovery mode.
- State history is append-only from the participant's perspective; corrections do not erase prior trace.
- Versioned symbol display is available when mutation/overwrite is being taught or tested.
- Environmental/interference events remain visible in the trial receipt.
- Training mode is visibly distinct from discovery mode.
- Adaptation rules show their warrant state and supporting observations.

## Evidence-graph mapping

`Stimulus -> HumanObservation -> HumanResolution -> TraceFreeze -> MachineEvaluation -> Comparison -> CalibrationState -> DesignDelta -> Retest -> Warrant`

Every inferred/adaptive edge should retain provenance, confidence/standing, assumptions, falsifier, and review state.

## Immediate implementation boundary

This document specifies the interface and evidence contract. It does not authorize psychological diagnosis, covert sensing, model training, or consequential external action. Any voice/gaze/pointer telemetry remains modality-specific opt-in and minimized to protocol need.
