# Q-TEMPORAL-DISSOLUTION-01 — index filing

**Status:** awaiting Z2. This file indexes an existing identifier. It does not ratify the policy, close an open conflict, or change a control surface.

**Authority effect:** NONE.

## Why this filing exists

`INTENT_GRAPH.yaml` cites `q_ref: Q-TEMPORAL-DISSOLUTION-01` on the open `conflicts_with` edge from `O-DOC-CONTROL` to `O-TEMPORAL-GATE`. The intent-graph checker warned (W6) that the identifier was well-formed but not present in `z1-inbox/INDEX.yaml`.

The policy text already exists in the tree as `TEMPORAL_DISSOLUTION_POLICY.md`. That file names Policy ID `Q-TEMPORAL-DISSOLUTION-01` and states that it is proposed, and effective only after merge and required review.

## What this PR does not do

- It does not treat the policy as ratified or effective.
- It does not resolve the open graph conflict, or the related temporal conflicts about molt closure and decision windows.
- It does not change `TEMPORAL_DISSOLUTION_POLICY.md`, the document registry, or any gate.

## Pointers

- Policy text: `TEMPORAL_DISSOLUTION_POLICY.md`
- Graph conflict: `INTENT_GRAPH.yaml` edge `O-DOC-CONTROL` → `O-TEMPORAL-GATE` (`conflicts_with`, status OPEN)
- Related indexed candidate: `Q-MOLT-TEMPORAL-PURITY-01`

Refs: #1391.
