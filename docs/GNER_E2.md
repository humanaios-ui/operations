# GNER-E2 — Failure Signature Correlation

This is a **stacked draft** on GNER-E1 #770 (which depends on E0 #767). The module groups *candidate recurring diagnostics*, not proven shared root causes. It has no network, Gmail intake, GitHub write, or action execution.

## Contract

An upstream authenticated GitHub fetcher must retrieve run details and job/test diagnostic evidence, identify a bounded failure code and exact failing test, and retain evidence links privately. E2 accepts a list of normalized records with `CANONICAL_VERIFIED` state, failed run metadata, commit SHA, workflow, and an explicit `{code,test_path,test_name}` diagnostic.

**Trust limitation:** These are caller-supplied dictionaries; E2 does not cryptographically authenticate them or fetch job logs. Consequently, even if a caller sets `CANONICAL_VERIFIED`, E2 output remains `SHARED_FAILURE_SIGNATURE_CANDIDATE`; `root_cause_verified=false`. No admission, approval, issue creation, or repair may be triggered from the output.

Two distinct (run ID, head SHA) pairs with an identical diagnostic triplet form a group. Repeated emails for one run are not counted as distinct occurrences. Matching workflow names alone are insufficient.

## Run

`python3 -m unittest discover -s tests -p test_gner_failure_signatures_e2.py -v`

## First case

For PR #765, the quality-baseline failure was independently inspected and showed `test_every_tools_test_file_is_enumerated` as the named failing test. Other failure emails in Gmail are **unverified leads**, not proof of the same defect. E2 deliberately does not assert they share a root cause until their GitHub job diagnostics are fetched and reviewed.

## Next gate

Independently fetch and pin job annotations/log snippets over authenticated GitHub; convert to the bounded failure schema with traceable run/job/commit receipts; test cross-run attribution and negative controls. Keep email_token and other private notification URLs out of public receipts. Approve under Repository Coordinator before deploying any automated polling.
