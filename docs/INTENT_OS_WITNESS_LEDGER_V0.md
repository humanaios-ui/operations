# INTENT-OS Witness Ledger v0 (local)

**Status:** Z1 implementation substrate (schema + CLI + append-only jsonl).  
**Authority effect:** `NONE` — evidence/attribution only; not merge authority.  
**Out of scope for this file:** HTTP `/api/z2-authorized-*` (Phase D). Phase C local stop-hook allowlist lives in `docs/INTENT_OS_MACHINE_CAPABILITY_ALLOWLIST_V0.md`.

## Purpose

Capture human↔machine decision attribution in a machine-readable, tamper-evident local store so later consumers (stop-hook, capability registry) can read a verified chain. Tree + Z2 hash remain merge truth.

## Contract

- Schema: `schemas/intent_os_witness_ledger_entry_v0.schema.json`
- Store: `ledgers/WITNESS_LEDGER.jsonl`
- CLI: `tools/witness_ledger_v0.py`

Hard constants on every entry:

- `schema`: `intentos/witness_ledger_entry_v0`
- `authority_effect`: `NONE`
- `can_authorize`: `false`
- `advisory_only`: `true`

## CLI

```bash
# Create genesis row (once)
python3 tools/witness_ledger_v0.py init

# Append an attribution row
python3 tools/witness_ledger_v0.py append \
  --decision-id Q-EXAMPLE-01 \
  --actor-type human \
  --actor-email carly.r.anderson@gmail.com \
  --actor-role Z2 \
  --decision-class ratify \
  --title "Example attribution" \
  --context "Local ledger demo; not a forged Z2 hash" \
  --authority-level Z2 \
  --rationale "Demonstrate append path" \
  --falsifier "verify fails if this row is edited"

# Verify hash chain
python3 tools/witness_ledger_v0.py verify

# List recent rows
python3 tools/witness_ledger_v0.py list --limit 20

# Self-test (temp ledger; does not touch the repo file)
python3 tools/witness_ledger_v0.py --smoke-test
```

Optional `--artifact key=value` may be repeated on `append`. Default ledger path is `ledgers/WITNESS_LEDGER.jsonl` (override with `--ledger`).

## Falsifiers (from Q-INTENT-OS-WITNESS-LEDGER-01, local subset)

1. Retroactive edit of a prior jsonl line without a detectable `verify` break.
2. An entry with `can_authorize: true` or `authority_effect` other than `NONE` validating against the schema.
3. Claiming this ledger alone authorizes a merge or stop-hook allowlist change.

## References

- `z1-inbox/2026-09-19/Q-INTENT-OS-WITNESS-LEDGER-01.md`
- Design opinion Phase B (local first; no network API required)
