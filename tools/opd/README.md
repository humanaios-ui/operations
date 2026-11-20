# OPD v0.1 — offline operational policy distillation

This is a **Z1, observational-only** experiment. It cannot authorize, admit,
revoke, dispatch, execute, merge, or write to GitHub. It does not change
the Coordinator or the admission gate. Input is JSONL containing full
proposal/correction/outcome traces; output is advisory rule candidates only.

## Trust model
The trace contract preserves original proposals, corrections, exact PR head,
verified outcomes, and evidence pointers. An evidence URL is an **unverified
claim**, not an authenticated witness. Do not interpret this tool's acceptance
as CI evidence verification or admission. Before any future live integration,
independently fetch the GitHub run, verify repository, workflow identity,
conclusion, commit, provenance and authorizations. Never trust a comment as
approval. Do not put private information, credentials, or commands in traces.

A candidate requires two distinct heads. A disjoint holdout is required.
The implementation fails closed on unknown action kinds. No output is
executable policy; human and protected-CI review remain upstream of any
separate deployment decision.

## Use
`python -m unittest discover -s tests -p test_opd_offline.py -v`

`python tools/opd/offline_distiller.py --train train.jsonl --holdout holdout.jsonl --out opd-report.json`

Use only pre-reviewed sanitized data. Do not manufacture observations to
claim real efficiency. The report provides offline coverage and a
**potential** number of review calls avoided, assuming each correct match
could replace one low-risk repeated review. Real AI-call cost, engineer
minutes, CI run time, and incident metrics require prospective measurement
against a baseline; until then production savings are null.

### Pilot evaluation
- Train on independently verified historic low-risk Coordinator diagnostic
  corrections, with exact heads and run evidence verified externally.
- Hold out distinct later cases by incident and PR, not merely trace ID.
- Compare matched and unmatched diagnoses in shadow mode.
- Record false suggestions, manual review calls, tokens, duration and cost.
- Require zero authority bypasses; independently test malformed evidence,
  comment-only approvals, forged receipts and changed PR heads.
- Do not graduate into runtime without separate Z2 approval and protected CI.

Related: research graph #799, Coordinator security issue #897, audit #893.
