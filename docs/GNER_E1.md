# GNER-E1 — Authenticated GitHub run reconciliation

Stacked on GNER-E0 PR #767. This increment adds an explicit opt-in **read-only GitHub Actions run metadata verifier**, not an automated Gmail agent.

## Local execution

From repository root, use a fine-grained GitHub token with read-only Actions metadata access, never paste it into email, logs or repo:

```bash
export GITHUB_TOKEN='<token loaded securely from your local secrets manager>'
python3 tools/gner_verify_e1.py --subject '[humanaios-ui/operations] PR run failed: quality-baseline - E1 (2fca23f)' --run-id 37992199793
python3 -m unittest discover -s tests -p 'test_gner_verify_e1.py' -v
```

Only the **explicit CLI** makes one GitHub HTTPS GET request to an internally constructed repository-specific `api.github.com` endpoint. It does not follow links extracted from emails, make writes, or access Gmail.

Output states: `CANONICAL_VERIFIED` (run metadata agrees with GitHub), `CONFLICT` (contradiction), `ABSTAIN` (unresolved). The pure `reconcile` function takes a mapping for isolated tests; its result is trustworthy **only when the mapping was independently retrieved over authenticated GitHub HTTPS**, as in `verify_lead`. Never use fixture data as evidence that a live run was verified.

This phase verifies **run metadata only**. It does not validate review comments, job log root causes, SHA signatures, CI policy, HMBM/DHP custody, admission, or emails' actual senders. In GitHub workflows the PR association array may be absent, resulting in deliberate abstention. Do not commit private tokens or notification links containing `email_token`.

Future increments require independently scoped review-comment validation, failure-signature extraction, authenticated inbox ingestion, privacy review, and explicit coordinator admission. Do not promote email to governance authority.
