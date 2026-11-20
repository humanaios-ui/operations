# Q-INTENT-OS-WITNESS-LEDGER-01 — INDEX / REGISTERED AMBIGUITY reconcile (step A)

**Status:** Z1 consistency edit. `authority_effect: NONE`. Does **not** create, claim, or re-issue a Z2 ratification. Does **not** start Phase 1 ledger implementation (step B).

**Pinned main:** `2b5882a0e3fd1d5945c365a4b22d2d7b048b7fea` (pre-edit HEAD).

## Conflict (before)

| Surface | Stated state |
|---------|--------------|
| `z1-inbox/INDEX.yaml` | `status: awaiting_z2` (note admitted CLAUDE approval “pending formal INDEX entry”) |
| `REGISTERED.md` candidate header | `status: CANDIDATE`, `zone2_ratification: null` |
| `REGISTERED.md` Z2 Ratification block | `Decision: ACCEPT`, `2026-09-19T19:00:00Z`, formula hash present |
| `CLAUDE.md` appended events | “Z2 (Night) ratified Q-INTENT-OS-WITNESS-LEDGER-01” at 2026-09-19 19:00 UTC |
| `AUTHORIZATION_EVIDENCE_MAPPING.md` | Still said “not yet ratified” |
| Follow-up `Q-WITNESS-LEDGER-TIER0-EXTENSION-01` INDEX note | Already called the parent “already-ratified” |

## Reconciliation chosen

**Align INDEX and stale prose headers to the existing REGISTERED ACCEPT + CLAUDE append.** Stronger evidence is the ACCEPT block and CLAUDE append (same pattern as sibling `Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01`, whose REGISTERED header already reads `ACCEPTED`). Do **not** invent a new `ratify.py` hex digest.

## Cited signature (existing; not newly issued)

**z2_hash (verbatim from REGISTERED.md ACCEPT block):**  
`sha256(Q-INTENT-OS-WITNESS-LEDGER-01 | carly.r.anderson@gmail.com | 2026-09-19T19:00:00Z | ACCEPT | witness-ledger-architecture)`

Primary evidence locations (unchanged by this reconcile beyond REGISTERED candidate YAML header alignment):
- `REGISTERED.md` — section `## Z2 Ratification — 2026-09-19` for this Q-ID
- `CLAUDE.md` — appended events line dated 2026-09-19 19:00 UTC

## Changes in this PR

1. `z1-inbox/INDEX.yaml` → `status: ratified`; cite existing REGISTERED formula as `z2_hash` string (not a new signature).
2. `REGISTERED.md` candidate YAML header → `status: ACCEPTED`, `zone2_ratification: "2026-09-19T19:00:00Z"` (matches sibling dual-authority header shape; ACCEPT block unchanged).
3. `AUTHORIZATION_EVIDENCE_MAPPING.md` → replace “not yet ratified” with architecture-ratified / Phase-1-pending.
4. Inbox candidate status line updated to match.
5. `Z1_INBOX_INDEX.md` re-rendered from INDEX.

## Falsifier (this reconcile)

If after merge, `INDEX.yaml` status for this Q-ID again disagrees with the REGISTERED ACCEPT block **and** the CLAUDE.md append for the same Q-ID, this reconcile is falsified and must be re-opened as AMBIGUITY.

## Explicitly out of scope (steps B+)

- Witness ledger schema file, `jsonl` store, CLI (`tools/witness_ledger_*`)
- `/api/z2-authorized-*` endpoint
- Stop-hook consumer wiring
- Any new Z2 hash from `ratify.py`
- Merge of this PR (Z2/human)

## Residual Z2 human decision (optional, not blocking this reconcile)

Night may still (a) confirm the 2026-09-19 ACCEPT was intentional, and/or (b) later re-pin with a modern `ratify.py` hex. Until then, the formula string already in REGISTERED remains the cited evidence; this PR does not substitute for that optional re-pin.
