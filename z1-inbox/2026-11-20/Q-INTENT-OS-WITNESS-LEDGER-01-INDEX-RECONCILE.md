# Q-INTENT-OS-WITNESS-LEDGER-01 — INDEX / REGISTERED AMBIGUITY reconcile (step A)

**Status:** Z1 consistency edit **pending Night Z2 confirmation**. `authority_effect: NONE`. Does **not** create, claim, or re-issue a Z2 ratification. Does **not** start Phase 1 ledger implementation (step B). Leaves the Z2 decision box for Night.

**Pinned main:** `2b5882a0e3fd1d5945c365a4b22d2d7b048b7fea` (pre-edit HEAD).

## Conflict (before)

| Surface | Stated state |
|---------|--------------|
| `z1-inbox/INDEX.yaml` | `status: awaiting_z2` (note admitted CLAUDE approval “pending formal INDEX entry”) |
| `REGISTERED.md` candidate header | `status: CANDIDATE`, `zone2_ratification: null` |
| `REGISTERED.md` Z2 Ratification block | `Decision: ACCEPT`, `2026-09-19T19:00:00Z`, **formula string** (not a 64-hex digest) |
| `CLAUDE.md` appended events | “Z2 (Night) ratified Q-INTENT-OS-WITNESS-LEDGER-01” at 2026-09-19 19:00 UTC |
| `AUTHORIZATION_EVIDENCE_MAPPING.md` | Still said “not yet ratified” |
| Follow-up `Q-WITNESS-LEDGER-TIER0-EXTENSION-01` INDEX note | Already called the parent “already-ratified” |

## Reconciliation chosen (Z1 proposal; pending Night)

**Align INDEX toward the existing REGISTERED ACCEPT prose + CLAUDE append**, while marking that **no verbatim sha256 hex from Night exists in this repo**. Do **not** invent or compute a digest Night did not produce.

This PR’s INDEX `status: ratified` line is a **Z1 reconcile pending Night’s Z2 confirmation** — not an independent ratification act.

## Cited evidence (formula-only; not a Night hex)

REGISTERED.md ACCEPT block records this formula string (unchanged; not a hex digest):

`sha256(Q-INTENT-OS-WITNESS-LEDGER-01 | carly.r.anderson@gmail.com | 2026-09-19T19:00:00Z | ACCEPT | witness-ledger-architecture)`

**INDEX `z2_hash` (this reconcile):** `PENDING_NIGHT_REPIN`

Primary evidence locations:
- `REGISTERED.md` — section `## Z2 Ratification — 2026-09-19` for this Q-ID (formula-only)
- `CLAUDE.md` — appended events line dated 2026-09-19 19:00 UTC

Night may confirm the ACCEPT and supply a real hex, or reject/edit this INDEX alignment. Until then the marker stays `PENDING_NIGHT_REPIN`.

## Changes in this PR

1. `z1-inbox/INDEX.yaml` → `status: ratified` as Z1 reconcile; `z2_ruling` → this file; `z2_hash` = `PENDING_NIGHT_REPIN` (not a forged/computed hex).
2. `REGISTERED.md` — **append-only**: original candidate header left as `CANDIDATE` / `zone2_ratification: null`; append entry frames Z1 reconcile pending Night confirmation.
3. `AUTHORIZATION_EVIDENCE_MAPPING.md` → note ACCEPT prose present / INDEX pending Night re-pin; Phase 1 still open.
4. Inbox candidate status line updated to match.
5. `Z1_INBOX_INDEX.md` re-rendered from INDEX.

## Falsifier (this reconcile)

If after merge, `INDEX.yaml` status for this Q-ID again disagrees with the REGISTERED ACCEPT prose **and** the CLAUDE.md append for the same Q-ID (without an intervening Night confirm/reject), this reconcile is falsified and must be re-opened as AMBIGUITY.

## Explicitly out of scope (steps B+)

- Witness ledger schema file, `jsonl` store, CLI (`tools/witness_ledger_*`)
- `/api/z2-authorized-*` endpoint
- Stop-hook consumer wiring
- Any new Z2 hash from `ratify.py` (Night only)
- Merge of this PR / marking ready / Z2 ratification (Night / human)

## Residual Z2 decision (Night)

Night owns: (a) confirm or reject that the 2026-09-19 ACCEPT was intentional, and (b) optionally replace `PENDING_NIGHT_REPIN` with a verbatim Night-issued sha256 hex. This PR does not substitute for that confirmation.
