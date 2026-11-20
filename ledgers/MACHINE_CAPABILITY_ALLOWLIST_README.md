# MACHINE_CAPABILITY_ALLOWLIST v0 — local stop-hook registry

**Authority:** evidence/registry substrate only. `authority_effect: NONE`. `can_authorize: false`.  
**Not:** merge authority, forged Z2 hashes, or HTTP `/api/z2-authorized-machine-identities` (Phase D).

| Path | Role |
|------|------|
| `ledgers/MACHINE_CAPABILITY_ALLOWLIST.json` | Offline identity + capability digest registry |
| `schemas/intent_os_machine_capability_allowlist_v0.schema.json` | Allowlist contract |
| `tools/machine_capability_allowlist_v0.py` | `verify` / `list` / `check` / `stop-hook` / `--smoke-test` |
| `ledgers/WITNESS_LEDGER.jsonl` | Required verify peer (hash chain) |
| `docs/INTENT_OS_MACHINE_CAPABILITY_ALLOWLIST_V0.md` | Operator notes |

## Fail-closed

DENY when any of these hold:

1. Allowlist file missing, invalid JSON, shape breach, or `content_hash` mismatch
2. Witness ledger missing, empty, unreadable, or chain broken
3. Identity absent / revoked / machine unbound (`pending_capability_binding` or null digest)
4. HTTP API consulted (v0 never does; Phase D only)

## Standing check

```bash
python3 tools/machine_capability_allowlist_v0.py --smoke-test
python3 tools/machine_capability_allowlist_v0.py verify
python3 tools/machine_capability_allowlist_v0.py check --identity carly.r.anderson@gmail.com --enforce

Optional Phase D local mirror (does not grant authority; stop-hook does not call it):

```bash
python3 tools/z2_authorized_machine_identities_api_v0.py get
python3 tools/z2_authorized_machine_identities_api_v0.py serve --port 8787
```

See `docs/INTENT_OS_Z2_AUTHORIZED_MACHINE_IDENTITIES_API_V0.md`.
```
