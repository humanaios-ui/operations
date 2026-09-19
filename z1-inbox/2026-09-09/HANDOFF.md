# HANDOFF.md

- **Pinned start SHA:** `5c7e6d4317d8c06c2158e2e668bdbe213a06e6bc`
- **Current work SHA:** `1f953da`
- **Position:** F-HUB-01 staged as a non-canonical registry-ready markdown artifact at `/home/runner/work/operations/operations/registry-candidates/blocks/F-HUB-01_hubinger-coxon-extinction-risk-statements.md`.
- **Destination:** Zone-2/3 append path once merge assigns the entry hash; no direct edit to `REGISTERED.md`.
- **Probability:** High.

## Session-open findings carried forward

- **DRIFT / IC-CAND:** current `REGISTERED.md` blob at session open was `cdbc0afbb8454f994da79cec905e4d886177cd82`, which differs from the 2026-09-06 manifest pin `c0899b9b4f8825d154274b176bb880f233c45995`.
- **RECEIPT-GAP:** `/home/runner/work/operations/operations/z1-inbox/2026-09-06/MANIFEST.md` lists multiple files that are absent from this checkout, including `ic030_live_read_090626.md` and `registry_block_and_manifest_090626_v2.md`; manifest integrity could not be fully re-established from the working tree.

## Work completed

1. Added a single staged finding file for F-HUB-01 with ratification metadata, five sub-claims, falsifiers, measurement plan, and submission metadata.
2. Verified doc integrity with `python3 .doc-control/validate.py` and repo health with `python3 tools/repo_health.py --strict`.
3. Ran secret scanning on the changed staged finding file; no secrets detected.

## Falsifier-first note

This handoff would be proven wrong if the missing 2026-09-06 inbox files are present in another fetched tree location or if a later commit shows the recorded `REGISTERED.md` blob comparison was taken against the wrong ref rather than `HEAD`.
