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
- private contact data and Gmail bodies do not enter the public repository
- HMBM remains PAPER ONLY

## Components

- `schemas/workspace_event.schema.json` — common cross-plane event envelope.
- `tools/workspace_event.py` — deterministic canonical JSON/hash + envelope validation.
- `tests/test_workspace_event.py` — tamper, authority and hash checks.
- `apps_script/Code.gs` — Google-native persistence/read-back relay and reference-draft creator.
- `apps_script/appsscript.json` — Apps Script manifest for the scaffold.
- `hmbm/HMBM_CYCLE_003_PROTOCOL.md` — clean continuation protocol; Cycle 002 remains historical.

## Deployment state

`CODE_ONLY / NOT_DEPLOYED`.

The Apps Script relay requires explicit operator configuration of:

- `EVIDENCE_FOLDER_ID` in Script Properties;
- `RELAY_TOKEN` in Script Properties;
- a deployed Apps Script web app endpoint if GitHub-to-Workspace round-trip testing is authorized.

No GitHub credential is required inside Apps Script for the initial design.

## First bounded test

1. deploy the Apps Script code manually under the HumanAIOS Google account;
2. set the Drive evidence folder ID + relay token;
3. POST one synthetic `ROUNDTRIP_TEST` envelope;
4. verify event write, read-back hash and idempotent replay;
5. only then bind reference verification;
6. only after that run HMBM-CYCLE-003 H0 initialization.
