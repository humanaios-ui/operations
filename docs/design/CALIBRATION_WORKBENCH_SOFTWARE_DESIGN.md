# Calibration Workbench — Software Design Delta

Status: PROVISIONAL / LIVE DESIGN SHADOW
Date: 2026-09-30

## Role in HumanAIOS

The Calibration Workbench extends Progressive Onboarding and the Witness/Gateway. It calibrates the collaboration interface, not the worth or capability of the human. It preserves HumanAIOS separations: observation != evidence != calibration != warrant != authorization != enforcement.

## Dual runtime

```text
EXPERIMENT THREAD                          SYSTEM THREAD
PREFLIGHT                                 (closed)
BASELINE_CAPTURE                          (closed)
STIMULUS_READY                            (closed)
HUMAN_TRACE_OPEN                          (closed)
TRACE_FROZEN ---------------------------> DESIGN_DELTA_CHECK
MACHINE_TRACE_REVEALED                    DELTA_RECEIPT
COMPARED --------------------------------> UPDATE_PROVISIONAL_MODEL
RETEST <---------------------------------- RETEST_PROPOSAL
CLOSE | HALT_RESET                        LEDGER_APPEND
```

Hard invariant: the System Thread cannot reveal expected machine semantics while HUMAN_TRACE_OPEN.

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
  presentation_mode: STEPWISE | BUNDLED | EXTERNALIZED_STATE
  human_trace[]
  resolution_state: RESOLVED | UNRESOLVED | DELAYED | NOT_CAPTURED
  participant_confidence
  active_focus:
    symbol
    value_if_reported
    salience_label
  trace_frozen_at
  machine_trace[]
  comparison: CONVERGENCE | DIVERGENCE | INTERFERENCE | INDETERMINATE
  corrections[]
  delayed_resolutions[]
  design_deltas[]
  warrant_state: PROVISIONAL | REPLICATED | WARRANTED | WITHDRAWN
  provenance
```

## Real-time Design Delta Ledger

After each comparison, evaluate whether frozen evidence changes the software model. When it does, display a compact receipt:

```text
SYSTEM DELTA
changed: <specific interface/model change>
unchanged: <protected invariants>
evidence: <trial ids / observations>
status: PROVISIONAL | REPLICATED | WARRANTED | WITHDRAWN
falsifier: <next observation that could defeat it>
```

This replaces retrospective “look back for updates” as the primary mechanism. Retrospective audit remains available for verification.

## UX contract

Primary surfaces: BASELINE | STIMULUS | YOUR TRACE | MACHINE TRACE | COMPARE | SYSTEM DELTA | CORRECTION | HISTORY.

- Participant can halt/reset at any point.
- Machine answer cues are hidden before trace freeze in discovery mode.
- State history is append-only; corrections and delayed answers do not erase prior trace.
- UNRESOLVED is a valid first-class state.
- Delayed resolution stores order/latency and confidence separately.
- Active focus/“hero” is displayed separately from the full preserved state.
- Externalized state can be tested as a presentation control rather than silently imposed.
- Environmental/interference events remain visible in the trial receipt without causal attribution.
- Training mode is visibly distinct from discovery mode.
- Adaptation rules show warrant state and supporting observations.
- System-delta receipts appear only after trace freeze.

## Evidence-graph mapping

`Stimulus -> HumanObservation -> ResolutionState -> TraceFreeze -> MachineEvaluation -> Comparison -> CalibrationState -> DesignDelta -> Retest -> Warrant`

Additional edges:
`EnvironmentalObservation -[CONTEXT_FOR]-> Trial`
`ActiveFocus -[SALIENT_DURING]-> HumanObservation`
`DelayedResolution -[FOLLOWS]-> UnresolvedObservation`
`DesignDelta -[SUPPORTED_BY]-> FrozenTrace`
`DesignDelta -[CHALLENGED_BY]-> Retest`

Every inferred/adaptive edge retains provenance, confidence/standing, assumptions, falsifier, and review state.

## Epistemic boundary

Subjective introspection is valid evidence of what the participant reports experiencing, not objective proof of the underlying cognitive mechanism. Controlled stimuli and machine semantics provide comparators. Repeated cross-condition evidence may support a cognitive clue/hypothesis. No single trial is promoted into a stable cognitive claim.

## Immediate implementation boundary

This document specifies the interface and evidence contract. It does not authorize psychological diagnosis, covert sensing, model training, or consequential external action. Any voice/gaze/pointer telemetry remains modality-specific opt-in and minimized to protocol need.
## Evidence-graph implementation

This PR now includes an executable graph schema and validation layer:

- `docs/design/calibration-evidence-graph.ttl` — HumanAIOS calibration ontology using PROV-O-compatible provenance primitives.
- `docs/design/calibration-evidence-graph.shacl.ttl` — SHACL constraints for persisted graph validation.
- `docs/research/CALIBRATION_EVIDENCE_GRAPH_EXTERNAL_MAPPING.md` — node-by-node mapping to external standards/research, including relation type, scope, limitations, and version watch.

External evidence edges MUST be typed as one of: `IMPLEMENTS_STANDARD`, `CONSTRAINED_BY_STANDARD`, `METHOD_ANALOGUE`, `COGNITIVE_ANALOGUE`, `EMPIRICALLY_MOTIVATED_BY`, `CHALLENGED_BY`, `LOCAL_HYPOTHESIS`, or `VERSION_WATCH`.

PROV-O is the provenance substrate. SHACL 1.0 is the normative graph-validation baseline. SHACL 1.2 Core remains a version-watch target while it is a Working Draft. Nanopublication structure is an optional claim-packaging pattern, not a dependency.

Important separation: SHACL validates persisted graph structure; it does not enforce the temporal runtime rule that machine semantics remain hidden until trace freeze. That invariant belongs in the controller/application layer.
## Validation-stage integration

Validation staging is integrated at the **promotion boundary**, not inside the open human-trace loop.

```text
OBSERVATION
 -> TRACE FREEZE
 -> DESIGN DELTA (PROVISIONAL)
 -> GRAPH ENCODE
 -> STRUCTURAL VALIDATION
 -> RETEST
 -> REPLICATED | WITHDRAWN
 -> WARRANT REVIEW
```

Rationale: the first fixture pass exposed missing graph primitives (`comparisonType`, values, sequence, and retest outcome) and required a negative fixture that rejects malformed evidence. This demonstrates process utility before claim validation. Structural validation is therefore required for evidence-graph/schema-affecting deltas before promotion, while remaining outside the stimulus -> human-trace path to avoid adding observational latency or contamination.

Structural conformance is necessary for promotion but is never sufficient evidence that a cognitive interpretation is true.

## Landing Verification Lane

HumanAIOS now treats **understanding as a state that may require verification**, not as an assumption made from message delivery.

The lane is separate from agreement and correctness:

```text
MESSAGE
 -> RECEIVED
 -> LANDING_CHECK
 -> UNVERIFIED | CONFIRMED | CLARIFIED | MISUNDERSTOOD | DEFERRED
 -> CONTINUE | REPHRASE | HALT
```

A landing check asks whether the intended meaning landed well enough for the next action. It does **not** require the person to agree with the content.

Trigger the lane selectively when:
- technical jargon or an unfamiliar term is introduced;
- a dependency or limitation changes what can actually be executed;
- the participant reports confusion or asks for clarification;
- a consequential state transition is about to occur;
- the next action depends on a specific interpretation.

Do not insert a landing check after every conversational turn. That would create friction and may interfere with the open human-trace loop. In discovery mode, landing verification occurs only after the trace is frozen unless clarification is required to understand the stimulus itself.

AHRQ TeamSTEPPS check-back and teach-back are external methodological analogues for this lane: closed-loop communication verifies that information was received as intended, and teach-back verifies understanding by asking the receiver to restate meaning in their own words. HumanAIOS adopts the control pattern, not the healthcare-specific context.

## Dependency Flagging

Dependencies are first-class execution evidence.

```text
DEPENDENCY FLAG
dependency: <package/tool/permission/network/upstream artifact/human input/version/etc.>
state: SATISFIED | UNSATISFIED | UNVERIFIED | DEGRADED | VERSION_MISMATCH
required_for: <specific stage/action>
blocks_stage: true | false
impact_plain_language: <what cannot happen because of this>
resolution_action: <what would satisfy it>
fallback: <bounded alternative, if any>
```

The flag must name the blocked scope precisely. A missing dependency does not automatically mean the whole project is blocked.

Example from this session:

```text
dependency: pyshacl==0.40.1
state: UNSATISFIED in current session execution environment
required_for: canonical SHACL validation
blocks_stage: true for canonical SHACL execution
does_not_block: fixture authoring, ontology design, structural preflight
resolution_action: execute in an environment that can install/run PySHACL
```

This replaces vague phrases such as “needs a dependency-capable run” with an explicit machine- and human-readable dependency state.

## Updated runtime model

```text
EXPERIMENT THREAD
  -> TRACE FREEZE
SYSTEM / DESIGN THREAD
  -> DESIGN DELTA
  -> DEPENDENCY CHECK
  -> GRAPH VALIDATION
LANDING VERIFICATION LANE
  -> verify critical explanation / dependency meaning
  -> clarify if needed
  -> continue only with known landing state when consequential
```

Landing verification and dependency flags are initially PROVISIONAL design deltas. They become canonical only if validation/retest shows that they improve legibility, reduce execution ambiguity, or prevent false claims of completion without imposing excessive interaction cost.

