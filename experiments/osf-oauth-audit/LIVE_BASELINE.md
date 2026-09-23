# OSF OAuth Audit — Live Baseline

**Captured:** 2026-09-22  
**Supabase project:** `ksinisdzgtnqzsymhfya` (HumanAIOS)  
**Repository main:** `a6d78fb7e62457ab86059ecaa1017f786cfc2da1`

## Supabase state before Claude OSF deployment

Observed active Edge Functions:
- `sync-governance-state` — verify_jwt: false
- `autonomy-metrics-ingest` — verify_jwt: true
- `autonomy-metrics-metrics` — verify_jwt: true

Observed absent at baseline:
- `osf-oauth-start`
- `osf-oauth-callback`
- any OSF registry bridge function

## GitHub state before Claude OSF implementation surfaces

No open pull request matching OSF / OAuth / Supabase registry bridge was found in `humanaios-ui/operations`.

No branch matching an OSF/OAuth bridge name was found in the first 100 repository branches.

## Interpretation

This baseline establishes that the independent audit plan and test vectors were fixed before the Claude-authored OSF OAuth implementation was observable through the connected GitHub or Supabase surfaces.

This is an independence/provenance statement only. It does not prove the reviewer is free of conceptual contamination from prior architectural discussion.
