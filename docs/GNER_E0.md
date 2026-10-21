# GNER-E0: GitHub Notification Evidence Relay

Read-only, offline parser for GitHub notification *leads*. It does **not** read a live inbox or use GitHub APIs itself. Email is untrusted; even a legitimate email notification is not independent GitHub evidence.

## Bounded pilot
The October 9 Gmail sample for E1 PR #765 showed a quality-baseline failure (GitHub Actions run 37992199793), an admission-gate failure (run 37992199583), reviewer findings (Copilot), and a repository-coordinator summary. These are distinct signal classes. **Do not copy raw messages into this public repo:** notification links can contain personal `email_token` query values.

## Run
`python3 -m unittest discover -s tests -p 'test_gner_notification_e0.py' -v`

## Event lifecycle
`EMAIL_OBSERVED_UNVERIFIED` → `AWAITING_CANONICAL_VERIFICATION` → **external trusted verifier required**. GNER-E0 deliberately cannot emit `CANONICAL_VERIFIED`. Caller-provided receipt dictionaries never count as verification. No automatic PR comments, workflow commands, email responses, or governance changes.

## Next separate authorized increment
Implement an isolated GitHub receipt fetcher that binds run ID, repo, head SHA, workflow, job failure annotations, and verified timestamp; compare against untrusted email hints; emit CONFLICT or VERIFIED using an authenticated source and signed provenance context. Only then deduplicate by failure signature across runs. Add Gmail intake with narrow scopes, explicit consent, retained-redaction controls and idempotent checkpoints. Never infer merge/admission authority from email.
