# WITNESS_LEDGER v0 — local INTENT-OS attribution store

**Authority:** evidence/registry substrate only. `authority_effect: NONE`. `can_authorize: false`.  
**Not:** merge authority, stop-hook allowlist (Phase C), or HTTP API (Phase D).

| Path | Role |
|------|------|
| `ledgers/WITNESS_LEDGER.jsonl` | Append-only hash-chained entries |
| `schemas/intent_os_witness_ledger_entry_v0.schema.json` | Entry contract |
| `tools/witness_ledger_v0.py` | `init` / `append` / `verify` / `list` / `--smoke-test` |
| `docs/INTENT_OS_WITNESS_LEDGER_V0.md` | Operator notes |

## Integrity

Each line is one JSON object. `hash = sha256(canonical_json(row without hash))` with `prev_hash` linking to the prior row's `hash` (genesis uses 64 zero hex digits). Any edit breaks `verify`.

## Standing check

```bash
python3 tools/witness_ledger_v0.py --smoke-test
python3 tools/witness_ledger_v0.py verify
python3 tools/builder_compliance_scanner_v1.0.py --path tools/witness_ledger_v0.py
```

Do not forge Z2 ratification hashes into this file. Seed only with honest attribution rows after Z2-scoped landing.
