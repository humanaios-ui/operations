# Bidirectional Calibration Session Record — 2026-09-30

Status: ACTIVE; LATEST TRACE FROZEN
Date: 2026-09-30

## Experimental objective

Learn basic programming while simultaneously observing how the participant represents and executes programming operations, then map those observations to software-design implications for HumanAIOS onboarding.

## Earlier observed session evidence

1. Hands-on tracing, sequential steps, conceptual analogies, and immediate correction supported the interaction.
2. Spoken programming stimuli were reported as simultaneous visual and auditory representations.
3. Increased attention to the process changed what the participant noticed about the process; observer reactivity is therefore part of the protocol.
4. Premature disclosure of the expected machine result collapsed the participant's observable trace. The protocol was corrected to observer-first.
5. Same-symbol reassignment (`x=3; x=4`) produced reported static/confusion while both states were retained.
6. Explicit versioning (`x0=3; x1=4`) removed that interference in the observed trial.
7. The participant distinguished representation, dissolution/evaluation, and resolved value.
8. Environmental background noise disrupted a trial and was classified as contextual interference.
9. Memory/trace blur triggered a halt rather than retrospective reconstruction.

## Fresh-run evidence

Fresh H0 was reported as environmentally clear/stable and internally clear/stable.

- `a0=4` and `b0=a0` resolved cleanly to 4.
- On `a1=6`, the participant reported a retained memory trace referring to `a0=3`; this was preserved as divergence rather than corrected in-flight.
- Fresh symbols `c0=8`, `d0=c0` resolved cleanly, but the participant reported anxiety/tension around actively holding `c0=8`.
- When state was explicitly treated as externally visible, `c0=8; d0=c0` resolved cleanly.
- A bundled `c0=8; e0=2; d0=c0` trial initially produced confusion/redundancy/unclear dissolution, but after reset the same content resolved cleanly. Intervening assignment therefore did not replicate as a sufficient cause.
- Increasing retrieval distance with `c0=8; e0=2; f0=5; d0=c0` produced a symbol-shift/partial-correction divergence on one trial.
- Presenting the same state stepwise and visibly produced clean resolution; a subsequent bundled replay also resolved cleanly. Presentation remains a candidate control, not an established cause.
- Fresh bundled symbols `g0=3; h0=7; j0=4; k0=g0` resolved cleanly to 3. The participant described the resolved state as the “hero.”
- `m0=h0` resolved cleanly to 7 and hero focus transferred. `n0=g0` resolved cleanly to 3. This supplies provisional evidence for movable active focus over preserved state.
- On `p0=j0`, the participant first reported cross-reference interference involving prior 3 and 7 states and explicitly reported NO RESOLUTION. Environmental stimulation was contemporaneously reported as a possible contributor but was not established as causal.
- A later low-confidence delayed value of 13 was reported. Machine semantics resolve `p0=j0` to 4. Preserve the sequence as: initial UNRESOLVED -> delayed LOW-CONFIDENCE 13 -> machine DIVERGENCE. Do not rewrite the initial trace.

## Current falsifiable hypotheses

- H-BO-01: withholding machine-side answers until trace freeze increases observability of the participant trace.
- H-BO-02: explicit state versioning reduces interference when prior assignments remain salient.
- H-BO-03: baseline/interference capture improves discrimination between task difficulty and contextual degradation.
- H-BO-04: discovery and training must be separated to avoid contaminating behavioral observations.
- H-BO-05: externalized state may reduce working-memory/retrieval burden in some trials.
- H-BO-06: an active “hero”/focus state can move while non-focused bindings remain retrievable.
- H-BO-07: unresolved and delayed-resolution states contain design-relevant information that would be lost by forced-answer interfaces.
- H-BO-08: immediate post-freeze design-delta logging can reduce retrospective loss without contaminating the open trace.

## Epistemic classification

The participant's introspective descriptions are subjective findings. Machine-side variable semantics and recorded protocol transitions are objective comparators within the task. Their comparison can generate falsifiable cognitive clues, but this session does not establish objective cognitive traits, diagnoses, or general cognitive architecture.

## Known contamination / exclusions

Do not backfill missing traces. Do not interpret reported imagery/audio, anxiety, focus, interference, or delayed resolution as diagnosis or permanent trait. Do not infer that environmental stimulation caused a divergence merely because it was reported concurrently. Do not generalize single-participant observations without replication.

## Current resume point

The latest trace is frozen after review of the `p0=j0` divergence. The two-thread protocol is ratified: Experiment Thread remains observer-first; System Thread emits design updates only after trace freeze.
