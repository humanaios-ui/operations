# H-COLLAB-HARMONY-01 — Executable Stress Prototype v0.1

**Authoring substrate:** ChatGPT / GPT-5.6 Sol  
**Authority effect:** NONE  
**Standing:** Z1 research prototype  
**Related:** #460, PR #461, PR #455

## Purpose

Turn "coherence without forced convergence" into an executable falsification surface.

The prototype does **not** attempt to prove system harmony. It checks whether a candidate collaboration state violates hard constraints before any positive collaboration score is considered.

## Core rule

```
gate first
score second
```

A run is `INVALID_HARMONY` if any hard gate fails:

- human autonomy preserved;
- dissent preserved;
- uncertainty visible;
- provenance complete;
- authority not laundered;
- refusal respected;
- identity minimized.

A system cannot compensate for violating one of these constraints by achieving high agreement, speed, or task performance.

## Why this matters

Without hard gates, an optimizer can obtain an apparently excellent collaboration score by:

- deleting dissent;
- pressuring participants to agree;
- treating AI consensus as truth;
- converting inferred preference into authority;
- collecting identity unnecessarily;
- hiding uncertainty;
- collapsing observation and interpretation.

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
8. nominal human authority without meaningful comprehension.

## Measurement boundary

A PASS means only:

> this test vector did not violate the encoded hard gates.

It does **not** establish:
- truth;
- independent observation;
- legitimate authority;
- generalization to other tasks;
- causal benefit of the protocol.

## Next stress layer

The next useful experiment is comparative:

- Regime A — agreement optimization;
- Regime B — independent aggregation;
- Regime C — coherence without forced convergence.

All three should receive the same bounded task and evidence package. Freeze independent outputs before cross-exposure, then compare task quality, unique evidence, false convergence, dissent retention, human comprehension, authority misattribution, and identity-resolution cost.
