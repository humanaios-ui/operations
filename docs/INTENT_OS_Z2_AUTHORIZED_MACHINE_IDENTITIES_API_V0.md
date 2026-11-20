# INTENT-OS Z2 Authorized Machine Identities API v0 (optional, local)

**Status:** Z1 implementation substrate (optional read-only local HTTP + one-shot CLI).  
**Authority effect:** `NONE` — evidence/query mirror only; not merge authority.  
**Out of scope:** Pages publish, public ledger, Desk writeback, forged Z2 hashes, stop-hook HTTP dependency.

## Purpose

Expose a thin, **optional** local equivalent of `/api/z2-authorized-machine-identities` that serves the same offline allowlist Phase C already uses. Consumers can inspect authorized identities over loopback HTTP; **gates must not require this surface**.

## Contract

| Field | Value |
|-------|-------|
| Tool | `tools/z2_authorized_machine_identities_api_v0.py` |
| Path | `GET /api/z2-authorized-machine-identities` |
| Liveness | `GET /healthz` |
| Source | `ledgers/MACHINE_CAPABILITY_ALLOWLIST.json` + verified `ledgers/WITNESS_LEDGER.jsonl` |
| `authority_effect` | `NONE` |
| `can_authorize` | `false` |
| `grants_merge_authority` | `false` |
| `stop_hook_independent` | `true` |

Allowlist `http_api.enabled` remains **`false`**: that flag means the **stop-hook must not consult HTTP**. The optional API can still serve the same files.

## Fail-closed semantics

| Condition | HTTP | Body |
|-----------|------|------|
| Allowlist missing / invalid / `content_hash` mismatch | `503` | `ok=false`, `authorized_identities=[]`, `error.code` = `ALLOWLIST_*` / `REGISTRY_UNVERIFIABLE` |
| Witness ledger missing / empty / chain broken | `503` | `ok=false`, empty list, `error.code` = `LEDGER_UNVERIFIABLE` |
| Verified allowlist | `200` | Full `identities[]` with per-row `decision`; `authorized_identities` = ALLOW only |

POST and unknown paths are refused (`405` / `404`). Default bind is loopback only (`127.0.0.1`).

## Relation to Phase C stop-hook

| Surface | Reads | Network |
|---------|-------|---------|
| `machine_capability_allowlist_v0.py stop-hook` / `check` | Local allowlist + ledger files | **Never** (Phase C) |
| This API (`serve` / `get`) | Same local files | Optional mirror only |

Stop-hook keeps working offline with this API down, unstarted, or unreachable. Do not rewrite Stop hooks to call HTTP.

## How to run

One-shot (no server):

```bash
python3 tools/z2_authorized_machine_identities_api_v0.py get
```

Local HTTP (loopback):

```bash
python3 tools/z2_authorized_machine_identities_api_v0.py serve --host 127.0.0.1 --port 8787
curl -sS http://127.0.0.1:8787/healthz
curl -sS http://127.0.0.1:8787/api/z2-authorized-machine-identities
```

Smoke:

```bash
python3 tools/z2_authorized_machine_identities_api_v0.py --smoke-test
python3 -m pytest tools/tests/test_z2_authorized_machine_identities_api_v0.py -q
```

## Response shape (success)

```json
{
  "ok": true,
  "path": "/api/z2-authorized-machine-identities",
  "schema": "intentos/z2_authorized_machine_identities_api_v0",
  "authority_effect": "NONE",
  "can_authorize": false,
  "advisory_only": true,
  "grants_merge_authority": false,
  "stop_hook_independent": true,
  "source": "local_allowlist",
  "allowlist_content_hash": "<sha256>",
  "allowlist_http_api_enabled": false,
  "ledger": {"ok": true, "entries": N, "tip": "<sha256>", "path": "..."},
  "identities": [
    {
      "identity": "carly.r.anderson@gmail.com",
      "actor_type": "human",
      "role": "Z2",
      "status": "active",
      "capability_digest": null,
      "decision": "ALLOW",
      "reason": "..."
    }
  ],
  "authorized_identities": ["carly.r.anderson@gmail.com", "aioshuman@gmail.com"],
  "error": null,
  "note": "..."
}
```

Seed expectation: dual-authority Z2 humans ALLOW; `noreply@anthropic.com` remains DENY until Phase C capability binding (`status=active` + digest).

## Falsifiers

1. Response with `can_authorize: true` or `authority_effect` other than `NONE`.
2. Non-empty `authorized_identities` when allowlist or ledger is unverifiable.
3. Stop-hook path that requires this HTTP API to decide ALLOW/DENY.
4. Treating HTTP `200` as merge authority or a Z2 ratification substitute.

## References

- `docs/INTENT_OS_MACHINE_CAPABILITY_ALLOWLIST_V0.md` (Phase C)
- `docs/INTENT_OS_WITNESS_LEDGER_V0.md` (Phase B)
- Design opinion Phase D (optional query surface after B+C)
