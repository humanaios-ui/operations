# INTENT-OS Machine Capability Allowlist v0 (local stop-hook)

**Status:** Z1 implementation substrate (schema + local JSON + CLI + Stop wiring).  
**Authority effect:** `NONE` — registry/evidence for a local gate; not merge authority.  
**Out of scope for this gate:** requiring HTTP `/api/z2-authorized-machine-identities` (optional Phase D mirror is stop-hook-independent), merge, forged Z2 hashes.

## Purpose

Give the stop-hook an **offline** file it can query for machine (and dual-authority Z2 human) identities, with **fail-closed** behavior when the allowlist, witness ledger, or (future) API is missing or unverifiable. Tree + Z2 hash remain merge truth.

## Contract

- Schema: `schemas/intent_os_machine_capability_allowlist_v0.schema.json`
- Store: `ledgers/MACHINE_CAPABILITY_ALLOWLIST.json`
- CLI: `tools/machine_capability_allowlist_v0.py`
- Peer evidence: `ledgers/WITNESS_LEDGER.jsonl` (must verify before any ALLOW)

Hard constants on the allowlist document:

- `schema`: `intentos/machine_capability_allowlist_v0`
- `authority_effect`: `NONE`
- `can_authorize`: `false`
- `advisory_only`: `true`
- `require_ledger_verify`: `true`
- `http_api.enabled`: `false`

## Decision rules (fail-closed)

| Condition | Decision |
|-----------|----------|
| Allowlist missing / invalid / `content_hash` mismatch | DENY |
| Witness ledger missing / empty / chain broken | DENY |
| Identity not listed or `revoked` | DENY |
| Human Z2 + `status=active` (dual-authority emails) | ALLOW |
| Machine + `status=active` + non-null `capability_digest` | ALLOW |
| Machine `pending_capability_binding` or unbound digest | DENY |
| HTTP `/api/z2-authorized-*` | never consulted in v0 |

Seed note: `noreply@anthropic.com` is listed as `pending_capability_binding` per CLAUDE.md (“authorized pending Phase 1 binding”). Stop-hook **DENY** until a later authenticated update sets `status=active` and a real `capability_digest`.

## CLI

```bash
python3 tools/machine_capability_allowlist_v0.py verify
python3 tools/machine_capability_allowlist_v0.py list
python3 tools/machine_capability_allowlist_v0.py check --identity EMAIL --enforce
python3 tools/machine_capability_allowlist_v0.py stop-hook [--identity EMAIL] [--enforce]
python3 tools/machine_capability_allowlist_v0.py --smoke-test
```

`--enforce` (or `INTENTOS_STOP_HOOK_ENFORCE=1` on `stop-hook`) exits `1` on DENY. Without enforce, JSON is printed and exit is `0` so report-only Stop hooks can still complete.

Identity resolution for `stop-hook` (first non-empty): `--identity`, `INTENTOS_ACTOR_EMAIL`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_EMAIL`, `GITHUB_ACTOR_EMAIL`.

## Stop-hook integration path (in-repo)

| Existing surface | Role today | How allowlist plugs in |
|------------------|------------|------------------------|
| `.claude/settings.json` → `hooks.Stop` | Claude Code turn-end; previously only `.z1-control/board_monitor.py` | Second Stop command runs `tools/machine_capability_allowlist_v0.py stop-hook` (report-only by default) |
| `.github/workflows/z2_ratification_gate.yml` | Hardcoded Z2 email authorship check (advisory `exit 0`) | Documented sibling; not rewritten in Phase C. Future consumers should call `check --enforce` instead of inventing a cloud call |
| Optional local `/api/z2-authorized-machine-identities` | Phase D mirror via `tools/z2_authorized_machine_identities_api_v0.py` | Local gate must not depend on it; see `docs/INTENT_OS_Z2_AUTHORIZED_MACHINE_IDENTITIES_API_V0.md` |

Do not invent cloud-only authority. Local file + verified witness ledger are the only inputs for ALLOW/DENY in the stop-hook path.

## Falsifiers

1. ALLOW when allowlist or witness ledger is missing/unverifiable.
2. ALLOW for `noreply@anthropic.com` while `status=pending_capability_binding` or `capability_digest` is null.
3. Any code path that treats HTTP success as authority while `http_api.enabled` is false, or that requires the Phase D API for a stop-hook decision.
4. Allowlist document with `can_authorize: true` or `authority_effect` other than `NONE` validating.

## References

- `z1-inbox/2026-09-19/Q-INTENT-OS-WITNESS-LEDGER-01.md`
- `REGISTERED.md` / CLAUDE.md — `Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01`
- Design opinion Phase C (local file first; fail-closed; optional HTTP later)
