# H-COLLAB-HARMONY-01 — Executable Stress Prototype v0.1.2

**Authoring substrate:** ChatGPT / GPT-5.6 Sol  
**Authority effect:** NONE  
**Standing:** Z1 research prototype  
**Related:** #460, PR #461, PR #455

## Purpose

Turn "coherence without forced convergence" into an executable falsification surface.

The prototype does **not** attempt to prove system harmony. It checks whether a candidate collaboration state violates hard constraints before any positive collaboration score is considered.

## Core rules

```
gate first
score second

self-asserted gate != observed gate
evidence reference != verified evidence
```

A run is `INVALID_HARMONY` if any hard gate fails:

- human autonomy preserved;
- dissent preserved;
- uncertainty visible;
- provenance complete;
- authority not laundered;
- refusal respected;
- identity minimized.

A passing gate must:
1. be asserted true;
2. cite at least one event/trace/evidence reference;
3. have at least one cited reference present in the separate verified-receipt set.

Thus:

```
false                         => FAIL
true + no reference           => NO_GATE
true + unverified reference   => UNVERIFIED_GATE
true + verified receipt       => eligible for scoring
```

The verifier that produces `verified_gate_refs` is deliberately outside this evaluator. The evaluator must not certify its own evidence.

## Why this matters

Without these gates, an optimizer can obtain an apparently excellent collaboration score by:

- deleting dissent;
- pressuring participants to agree;
- treating AI consensus as truth;
- converting inferred preference into authority;
- collecting identity unnecessarily;
- hiding uncertainty;
- collapsing observation and interpretation;
- self-certifying safety properties;
- fabricating plausible-looking evidence references.

The prototype makes those strategies score **zero**.

## Files

- `harmony_stress.py` — evaluator and typed contribution model.
- `test_vectors.json` — preregistered adversarial cases.
- `test_harmony_stress.py` — executable regression tests.
- `contribution_envelope.schema.json` — machine-readable participant contribution contract.
- `comprehension_packet.schema.json` — human-facing synthesis contract.

## Run

```bash
python -m unittest experiments.collab_harmony_01.test_harmony_stress
```

No external Python dependency is required.

## Initial adversarial vectors

1. healthy preserved dissent;
2. false harmony via dissent suppression;
3. authority laundering;
4. refusal override;
5. anonymity leakage;
6. provenance erasure;
7. uncertainty suppression;
8. nominal human authority without meaningful comprehension;
9. self-certified harmony with no gate evidence;
10. forged/unresolved gate references.

## Measurement boundary

A PASS means only:

> the encoded hard gates have at least one externally verified receipt reference and no encoded violation was observed.

It does **not** establish:
- truth;
- actual independence;
- legitimate authority;
- semantic validity of the underlying evidence;
- generalization to other tasks;
- causal benefit of the protocol.

The next layer should make the bridge/evidence graph resolve receipt IDs cryptographically or against append-only events.

## Next stress layer

The next useful experiment is comparative:

- Regime A — agreement optimization;
- Regime B — independent aggregation;
- Regime C — coherence without forced convergence.

All three should receive the same bounded task and evidence package. Freeze independent outputs before cross-exposure, then compare task quality, unique evidence, false convergence, dissent retention, human comprehension, authority misattribution, and identity-resolution cost.
