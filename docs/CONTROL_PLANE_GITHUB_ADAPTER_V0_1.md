# Control-Plane GitHub Adapter — v0.1

Issue: #622  
Depends on: #620 / PR #621  
Standing: Z1 observation adapter  
Authority effect: **NONE**

## Purpose

Transform exported GitHub event/API payloads into the raw observation shape consumed by the custody observer.

```
GitHub evidence
→ control_plane_github_adapter
→ raw observation
→ control_plane_custody_observer
→ custody receipt
```

Collection and classification remain separate.

## Conservative defaults

Unless positive evidence is supplied:

```
actor origin      = SHARED_ACCOUNT_ORIGIN_UNKNOWN
decision custody  = UNKNOWN
information       = UNKNOWN
authority evidence= UNKNOWN
boundary          = UNKNOWN
```

The adapter never treats a normal GitHub user account as proof of a human actor.

## Positive origin evidence

v0.1 recognizes:

- GitHub bot/app login;
- explicit `humanaios-origin: ai-agent; agent=...` watermark;
- Claude Code watermark/session markers;
- Copilot watermark/login.

Absence of those markers does not establish human origin.

## Supported source types

- `commit`
- `workflow_run`
- `check_run`
- `pr_comment`
- `pull_request`
- `ref_error`

`ref_error` exists because rejected control-plane mutations may have no durable repository object. The error payload must be supplied explicitly; the adapter does not fabricate one.

## Boundary handling

The adapter only emits a non-UNKNOWN boundary when the evidence bundle supplies it.

Example:

```json
{
  "boundary": {
    "state": "MECHANICAL",
    "mechanism": "repository ruleset",
    "evidence_refs": ["api-error:422"]
  }
}
```

## Authority

The adapter has no authority resolver. Authority evidence defaults to `UNKNOWN`.

If a separately verified authority receipt is supplied, it may be carried as evidence, but the resulting custody receipt still has:

```
authority_effect = NONE
```

## CPC-002

CPC-002 replays exported PR #593 evidence and compares stable IDs/SHAs/provenance with CPC-001.

The adapter is expected to know less than the manually reconstructed specimen in some places. That is acceptable and preferred to guessing.

## CLI

```bash
python3 tools/control_plane_github_adapter_v0_1.py \
  --input experiments/control-plane-custody/CPC-002/pr-593-github-evidence.json
```
