# HIAE-001 — Z1 proposal: neutral assignment, receipt schema, synthetic transaction

**Parent:** humanaios-ui/operations#780
**Status:** Z1 proposal. **Not ratified.** No governance file (REGISTERED.md, PRIORITY_QUEUE.md, constants) is changed.
**Authority needed:** Z2 signature before any external claim, pilot, or merge to `main` that relies on this code.

## What was built

| Artifact | Purpose |
|---|---|
| `tools/hiae_assurance.py` | Stdlib-only core: rotation assignment with conflict exclusion, assignment verifier, versioned receipt issue/verify, observer-signed evidence, overclaim filter, synthetic transaction, negative suite |
| `tests/test_hiae_assurance.py` | 25 unittest cases: neutrality, conflicts, receipt tamper, forged evidence, unauthorized reviewer, overclaim |
| `docs/HIAE_EXTERNAL_CLAIMS_VERIFICATION.md` | Claim-by-claim status; primary sources blocked from this session |

Run: `python3 tools/hiae_assurance.py --smoke-test` and `python3 -m unittest tests.test_hiae_assurance`.

## Design choices (proposed, for Z2 review)

1. **No customer influence.** Requests carrying any reviewer-selection field are refused. Assignment is least-loaded rotation over eligible reviewers, tie-broken by `sha256(seed | request_id)`. Given the same inputs, anyone reproduces the choice.
2. **Conflicts are excluded, not scored.** Excluded: inactive or uncredentialed reviewers, unqualified for the risk class, same org as customer, declared conflict with customer, prior involvement with the same subject.
3. **Assignment is re-checkable.** `check_assignment()` recomputes the choice from the recorded seed and flags any substituted or conflicted reviewer.
4. **Receipts pin versions.** Protocol id and version, ACAT version, model id and version, commit SHA. Each receipt lists what was measured and what was not.
5. **Overclaiming is refused at issue time and at verify time.** Whole-word match on certified, certification, safe, compliant, accredited, accreditation. Not a complete semantic check; it blocks the obvious cases only.

## Known limits (stated, not hidden)

- **Signatures are HMAC-SHA256 with shared keys.** This stands in for an asymmetric scheme (Ed25519 or a W3C VC proof). The verifier must hold issuer keys, so receipts are not publicly verifiable. Replacing this is a Z2 decision.
- **Demo keys are in the source.** `DEMO_KEYS` is for the synthetic run and tests only.
- **Hash chaining is not used for authorship.** Authorship rests on observer and issuer signatures.
- **Fee/escrow and reviewer-key-per-change are not implemented.** They are design items for later review.
- **Principle 10 and credentialing** are in the humanaios child issue, not here.
- **Overclaim filter is lexical.** It will miss paraphrases and will flag some correct uses.

## Checklist status against #780

- [x] Neutral assignment + conflict-of-interest check (code and tests; unratified)
- [x] HIAE-001 synthetic transaction + negative tests (in-process, demo keys; unratified)
- [ ] Assessment receipt schema extending #751 (schema drafted; not yet reconciled with #751)
- [ ] Evidence authentication (observer signatures drafted; asymmetric keys not done)
- [ ] Ingestion of external evaluation results as untrusted claims
- [ ] Risk-class routing table (lane 1 SOP)
- [ ] Fee/escrow design review
- [ ] Host gate enforcement (#730): **blocked** on repository-admin access

## Z2 decisions requested

1. Accept the least-loaded rotation rule, or specify a different one (e.g. round-robin by reviewer id).
2. Accept HMAC as a temporary signature scheme, or require asymmetric signatures before any receipt leaves the repo.
3. Confirm the overclaim vocabulary.
4. Approve the non-claims language in #780 before any external use.
