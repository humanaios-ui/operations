# ECO-Ratify Ledger — the B1 ↔ B2 interface contract

**Status:** B1 (`ratify_eco.py`) produces this ledger. B2 (REGISTERED.md projection
generator) **consumes** it. This file is the contract between them so the projection
renders ratifications from one source of truth instead of re-deriving them.

## What the ledger is

`.z1-control/eco_ratify_ledger.jsonl` — an append-only, hash-chained record of every
Z2 ECO-acceptance of an Empirica proposal. One JSON object per line. Written only by
`ratify_eco.py` (never hand-edited). It is the signed-RATIFY store that closes
Substrate-Map binding **D2**; the projection (B2) is a read-only view over it.

## Row schema (`eco-ratify/v1`)

| field | type | meaning |
|---|---|---|
| `schema` | str | `"eco-ratify/v1"` |
| `seq` | int | 0-based position; MUST equal line order |
| `at` | str | ISO-8601 UTC timestamp of the Z2 act |
| `by` | str | ratifier identity; always ∈ `KNOWN_RATIFIERS` (`{"Night"}`) |
| `decision` | str | `ACCEPT` \| `EDIT` \| `REJECT` |
| `decision_status` | str | `ratified` \| `edit_requested` \| `rejected` (= `DECISIONS[decision]`) |
| `candidate_id` | str | the proposal/decision id being ratified (join key) |
| `candidate_path` | str\|null | repo-relative path of the signed artifact, or null if signed from stdin |
| `payload_sha256` | str | sha256 of `artifact_payload()` — content pin, independent of signer fields |
| `signature` | str | the Z2 mark: `sha256(candidate \| by= \| at= \| decision=)` (ratify.py's signer) |
| `prev_hash` | str | `record_hash` of the previous row, or `"genesis"` for `seq=0` |
| `record_hash` | str | sha256 of the row with `record_hash` excluded — the chain link |

## Rules B2 must honour

1. **Do not parse the ledger for truth without verifying it.** Call
   `python3 .z1-control/ratify_eco.py --verify` (or import and reuse its `cmd_verify`)
   before rendering. A row whose chain or signature fails is **not** a ratification —
   render it as `TAMPERED`, never as `ratified`.
2. **A candidate is RATIFIED in the projection iff** a *verifying* row exists for its
   `candidate_id` with `decision == ACCEPT`. `EDIT`/`REJECT` rows render as their own
   states. The latest row for a `candidate_id` wins (a later decision supersedes).
3. **Render the mark, not a re-derivation.** Show `candidate_id`, `decision`, `by`,
   `at`, and the first 16 hex of `signature`. Do not recompute a different hash or
   invent a second RATIFY format — that is the parallel-engine failure this contract exists to prevent.
4. **The ledger is append-only.** The projection is regenerated from it; it never
   writes back. REGISTERED.md becomes output, never input (Substrate Map §4).

## Reuse, don't reimplement

The signer and verifier already exist and are CI-enforced:

```python
import sys; sys.path.insert(0, ".z1-control")
from ratify import artifact_signature, artifact_payload   # the canonical signer
import ratify_eco                                          # read_ledger(), cmd_verify()
rows = ratify_eco.read_ledger()                            # list[dict], chain-ordered
ok   = ratify_eco.cmd_verify() == 0                        # gate before rendering
```

## First real row (expected)

Once B1's PR merges, the first genuine ledger row should be the Z2 ratification of
`D-SUBSTRATE-01` (the D1–D4 rulings) — B1 signing the decision that authorised B1.
