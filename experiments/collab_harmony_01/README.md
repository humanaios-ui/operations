# H-COLLAB-HARMONY-01 — Executable Stress Prototype v0.2

**Authoring substrate:** ChatGPT / GPT-5.6 Sol  
**Authority effect:** NONE  
**Standing:** Z1 research prototype  
**Related:** #460, PR #461, PR #455

## Purpose

Turn "coherence without forced convergence" into an executable falsification surface.

## Receipt integration

The evaluator no longer trusts a list called `verified_gate_refs`.

Each hard gate now cites one or more **typed receipt IDs**. The Bridge / Evidence Graph supplies an append-only receipt event stream plus a separately pinned chain-head hash.

A gate is eligible for scoring only when at least one receipt:

1. exists in the receipt stream;
2. is inside an intact append-only hash chain;
3. terminates at the separately supplied pinned head;
4. has `verification_status=VERIFIED`;
5. does not use `STUB`, `SIMULATED`, `FORMAT_ONLY`, or other disallowed methods;
6. has sufficient verification strength;
7. matches the exact gate subject;
8. matches action `ASSERT_GATE`;
9. matches the exact run scope;
10. has not been revoked.

Thus:

```
false gate                         => FAIL
true + no receipt ID               => NO_GATE
true + no receipt feed             => UNVERIFIED_GATE
tampered chain                     => UNVERIFIED_GATE
wrong subject/action/scope         => UNVERIFIED_GATE
simulated/stub receipt             => UNVERIFIED_GATE
valid pinned receipt               => eligible for scoring
```

## Trust boundary

The evaluator verifies receipt-chain integrity and requirement matching. It does **not** decide that an underlying real-world claim is true.

The pinned head must come from a channel independent of the event payload. An attacker-controlled ledger plus attacker-controlled head is not a trust anchor.

## Core rule

```
gate first
score second
receipt proof before gate credit
```

A run remains `INVALID_HARMONY` if any hard gate fails or cannot be established.

## Run

```bash
python -m unittest experiments.collab_harmony_01.test_harmony_stress
```

## Stress coverage

The test suite now includes:
- false harmony;
- authority laundering;
- refusal override;
- anonymity leakage;
- provenance erasure;
- uncertainty suppression;
- nominal human authority without comprehension;
- self-certification;
- raw "verified" reference lists;
- forged/unresolved receipt references;
- tampered receipt chains;
- wrong-scope receipts;
- simulated verification methods.

## Measurement boundary

A passing harmony gate means only that the encoded requirement has a matching receipt in an integrity-checked, pinned receipt stream. It does not independently establish truth, authority, causal benefit, or substrate independence.
