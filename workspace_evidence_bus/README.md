# HumanAIOS Workspace Evidence Bus

Implementation scaffold for operations issue #681.

## Boundary

This subsystem connects Google Workspace evidence custody to GitHub validation without making Gmail, Drive, Apps Script, the knowledge graph, or GitHub a universal source of truth.

Core invariants:

- `EMAIL != STATE`
- `EMAIL_REPLY != AUTHORITY`
- `DELIVERY != VERIFICATION`
- `DRIVE_FILE != CANONICAL_CLAIM`
- `COMPUTED != COMMITTED`
- `WRITE != VERIFIED_WRITE`
- `GRAPH != AUTHORITY`
- `HISTORICAL_SNAPSHOT != CURRENT_STATE`
- `CURRENT_STATE = deterministic_projection(immutable_receipts)`
- private contact data and Gmail bodies do not enter the public repository
- HMBM remains PAPER ONLY

## Components

- `schemas/workspace_event.schema.json` — common cross-plane event envelope.
- `tools/workspace_event.py` — deterministic canonical JSON/hash + envelope validation.
- `tools/workspace_lifecycle.py` — fail-closed lifecycle projector from immutable receipts.
- `tests/test_workspace_event.py` — tamper, authority and hash checks.
- `tests/test_workspace_lifecycle.py` — current-state, replay, receipt-completeness and authority-expansion checks.
- `state/current_state.json` — generated projection; never hand-edited as an authority record.
- `apps_script/Code.gs` — Google-native persistence/read-back relay and reference-draft creator.
- `apps_script/appsscript.json` — Apps Script manifest for the scaffold.
- `hmbm/HMBM_CYCLE_003_PROTOCOL.md` — clean continuation protocol; Cycle 002 remains historical.

## Lifecycle state

Current projected state: `ROUNDTRIP_VERIFIED`.

This state is not asserted from prose or from the old Drive deployment snapshot. It is derived from
`receipts/roundtrip_gate_receipt.json`, which records PASS for Apps Script POST, Drive write/read-back
hash verification, idempotent replay and secret-presence checks while preserving
`authority_effect=NONE`.

The earlier Drive artifact `DEPLOYMENT_STATE.json` recorded `CODE_ONLY_NOT_DEPLOYED` at
2026-10-02T20:52:00Z. It remains valid historical evidence, but it is
`SUPERSEDED_AS_CURRENT_STATE`; history is preserved rather than overwritten.

Reproduce the projection:

```bash
python3 workspace_evidence_bus/tools/workspace_lifecycle.py \
  --receipt workspace_evidence_bus/receipts/roundtrip_gate_receipt.json \
  --historical-drive-file-id 11EgHtelUYGFGA5uYHZPzn6wIf1q717tg \
  --historical-recorded-at 2026-10-02T20:52:00Z \
  --out workspace_evidence_bus/state/current_state.json
```

The next lifecycle gate is `BIND_PRIVATE_REFERENCES`. A receipt can advance this projection only when
the projector recognizes the event and every required invariant passes; Drive storage alone cannot
promote authority.

The Apps Script relay originally required explicit operator configuration of:

- `EVIDENCE_FOLDER_ID` in Script Properties;
- `RELAY_TOKEN` in Script Properties;
- a deployed Apps Script web app endpoint if GitHub-to-Workspace round-trip testing is authorized.

No GitHub credential is required inside Apps Script for the initial design.

## Bounded lifecycle

Completed:
1. Apps Script deployment/configuration sufficient for the synthetic test.
2. Synthetic `ROUNDTRIP_TEST` POST.
3. Drive event write + read-back hash verification.
4. Idempotent replay verification.
5. Receipt committed with `authority_effect=NONE`.

Next:
1. bind private reference verification;
2. preserve private contact/PII boundaries;
3. require an independently inspectable receipt before any later lifecycle transition;
4. keep HMBM prediction authority false unless separately authorized by its own gate.

No Workspace Evidence Bus lifecycle transition grants merge, deployment, prediction, or Z2 authority.
