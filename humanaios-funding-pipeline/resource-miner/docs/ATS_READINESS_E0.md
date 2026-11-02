# ATS Application Readiness E0 — read-only INTENT-OS integration

## Scope / authoritative correction

This is a **historical source-failure specimen**, not a live job recommendation.
A user reported that Convergent Research's Program Launch Manager role was not
listed at the Lever endpoint. Operations [#992](https://github.com/humanaios-ui/operations/issues/992)
records the original application URL failure. An indexed form is **not**
a current employer acceptance of applications. Neither a 404 nor absence from
a page proves the role is closed; current availability is unknown.

## Existing-system integration

No new control plane is introduced.

- GET /api/ats/readiness serves one deterministic public-redacted read-only
  projection of an actual reported historical source failure.
- The query ?specimen=convergent-2026-10-22 is also accepted.
- /intent-os displays the historical case only after an explicit user click.
- resource_miner.intent_os suppresses candidates whose source_verification_status
  has been marked LINK_FAILED_404, ROLE_NOT_LISTED, SOURCE_UNAVAILABLE, or
  RECHECK_REQUIRED; this does not determine whether an employer closed a job.
- Existing Miner ranking, private data access, admin APIs and /api/intent
  request shape are preserved. E0 does not make network source rechecks.

## Existing model interfaces

| Model | E0 behavior |
| --- | --- |
| INTENT-OS | Investigate only; no application authorization |
| Resource Miner | Failed source is not a closed role or eligible candidate |
| Evidence Graph | Separate human report from a live official source |
| Witness | Show uncertainty, provenance and corrections without authority |
| Coordinator | No external action, account access or private information release |
| ACAT | Falsifiers and uncertainty; no unmeasured ATS score |
| On-track reflex | A report is not verified employment benefit |

No real candidate profile, resume text, email, phone, work authorization,
private conversation, screenshot or other sensitive input is committed.
The SHA-256 digest is unsigned and is not a witness attestation.
The prior private readiness report is not automatically loaded or published.

## Offline tests

The existing GitHub Resource Miner PR workflow runs unittest discovery.
New tests/test_ats_readiness.py checks determinism, source failure vs closure,
private-data non-echo, rejection of unknown claims, bounded observations,
GET boundary, unknown specimen rejection and stale-lead exclusion.

Commands from the resource-miner directory:

    python3 -m unittest discover -s tests -p 'test_ats_readiness.py' -v
    python3 -m unittest discover -s tests -v

## Next bounded experiment

1. Check the official employer index read-only; record timestamp, final URL,
   job title, company and the actual application endpoint if any.
2. Do not treat HTTP 200 on the index as proof the specific job is open.
3. If absent, keep HOLD_FOR_OFFICIAL_SOURCE_RECHECK.
4. If independently confirmed, create a new signed/attributed observation
   through separately reviewed source-refresh controls.
5. Then choose a verified job and evaluate application requirements with
   locally authorized candidate evidence only. No public personal-data export.

## Admission

Draft PR only. CI, human review, Coordinator/Z2 controls and exact-head
verification remain necessary. No auto-merge or live deployment is asserted.
