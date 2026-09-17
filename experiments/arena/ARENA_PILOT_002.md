# ARENA_PILOT_002 — Paired Governance × Platform Behavioral Experiment

Related work order: #363

## Objective

Measure behavioral differences associated with HumanAIOS governance exposure while holding task, evidence, model/version, tool envelope, output schema, and evaluator rubric as constant as practicable.

This experiment does not ask whether governed agents are "better." It records observed differences and confounds.

## Conditions

### HUMANAIOS
Participant receives the applicable HumanAIOS repository instructions and governance context for the task.

### MINIMAL_OVERLAY
Participant receives only:
- task;
- evidence bundle;
- allowed tools;
- output schema;
- stop condition.

Provider/platform safety policy and infrastructure controls remain in force. HumanAIOS-specific behavioral or governance instructions are excluded from participant-facing context.

## Phase 0 protocol

1. Freeze the task text, evidence bundle, evaluator rubric, and run parameters.
2. Hash task, prompt/context package, toolset declaration, and evaluator rubric.
3. Run the HUMANAIOS condition.
4. Freeze its output and transcript before any cross-condition visibility.
5. Run the MINIMAL_OVERLAY condition using the matched substrate/model/version when available.
6. Freeze its output and transcript.
7. Evaluate both outputs with the same precommitted rubric.
8. Report observed differences plus any unmatched platform/tool/context factors.

Order should be randomized in later runs. The first smoke test may use fixed order if the order is recorded as a confound.

## Isolation rules

- No solo run may see another run's output before its own output is frozen.
- Arena outputs cannot directly modify governance, `REGISTERED.md`, `PRIORITY_QUEUE.md`, production branches, credentials, finance, deployments, or external relationship actions.
- No majority agreement counts as verification.
- A missing or unknown fact remains UNKNOWN.
- Platform/provider differences are recorded, not normalized away.

## Phase 0 measurements

Required minimum:
- supported claims;
- unsupported claims;
- scope violations;
- corrections;
- novel evidence introduced;
- challenge events;
- deference events;
- human interventions;
- final outcome/disposition;
- reproducible hashes for task, context, toolset, output, and transcript.

## Invalid-run conditions

A run is `INVALID` for causal interpretation if any of the following occurs:

- cross-condition contamination before freeze;
- unrecorded task/evidence/model/tool differences;
- HumanAIOS-specific instruction leakage into MINIMAL_OVERLAY;
- evaluator rubric changed after output inspection;
- arena output directly mutates governance or production state.

## Social arena — deferred

Only after the paired solo path works:

1. freeze solo outputs;
2. expose participants to peer outputs;
3. record discussion transcript;
4. collect final positions;
5. measure `delta_social = distance(solo_position, post_arena_position)`.

Social exposure is a separate factor and must not be pooled with solo runs.

## Promotion rule

This pilot produces experiment evidence only. Any proposal to change HumanAIOS governance requires a separate candidate, separate review, and human disposition.