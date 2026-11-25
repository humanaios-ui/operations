# INTENT-OS Form Assistance E0

This bounded prototype implements a **read-only application packet** from the user's October 23 captured BlueDot Rapid Grants form. It is not a live website scraper and does not submit or prefill an external website.

## Evidence and policy
- User-provided form capture is the sole field source; live form and AI-use terms are not verified.
- The packet only proposes values from explicitly `USER_VERIFIED` or `SOURCE_VERIFIED` inputs.
- `UNKNOWN` policy is the default; drafting is disabled until a separately reviewed policy permits it.
- Human-choice and consent fields always require direct human action.
- Budget amount and items require verified values; no invented costs.
- No personal profile, credentials, browser, network requests, database, or account access.
- Do not log or publish packets containing personal values. Integrate with the user's private Witness only after a separate privacy review.
- No automatic submission, Coordinator bypass, or admission self-approval.

## Test
From `humanaios-funding-pipeline/resource-miner` run:
`python -m unittest discover -s tests -p 'test_form_assistance.py'`

## Next integration (not included)
Add a user-controlled private profile mapping, budget-evidence links, provider-specific policy verification, review UI, and permission-gated browser prefill. Keep Coordinator/Z2 admission and explicit human submission approval. Compare manual vs assisted time and count unsupported claims, missing fields, and unapproved actions.
