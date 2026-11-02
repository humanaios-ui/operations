# HumanAIOS Attractor Observatory — E1 evidence bridge

**Status:** Z1 draft, stacked on PR #1040, read-only, non-authorizing. No resource catalog write, outcome promotion, account action, application, or beneficiary disclosure.

## The two connections

**Internal convergence, observed from GitHub:** `tools/attractor_evidence_bridge_e1.py` uses narrowly scoped GitHub REST GET calls to read explicitly selected PRs. Each PR's current head is pinned to a fetched, matching commit SHA. Associated checks are accepted only when `check_run.head_sha` equals that SHA. Reviews are counted only when their `commit_id` equals the same SHA. The report records PR state, merge date, check results, human-review events and repeated *check names across sampled PRs*. Repeated CI surface visits are **not** evidence that an AI agent executed a feedback loop or that a code change created external value.

**External conversion, independent-review interface:** The bridge reads comments on one explicitly chosen GitHub issue. A claim must be a small, exact fenced JSON packet. A separate human GitHub account can append a review packet linking its source commit, exact claim ID and canonical SHA256, and independent public evidence reference/digest. The program checks the distinct account identity and matching references using GitHub's authenticated comment authorship. A `SUPPORTS` verdict produces `SEPARATE_REVIEW_ATTESTED`, **not** `VERIFIED_RESOURCE_ACQUIRED` or independently authenticated benefits. A contesting `REJECTS` or `INDETERMINATE` verdict creates `DISPUTED`; self-review, unknown commits and hash drift cannot qualify.

These are distinct signals. A merged PR is not a real-world resource. A resource candidate is not an acquisition. Existing owned Azure credits, a prepared job application, a click, or a source failure do not establish new acquisition or service benefit.

## Existing sources

- PR #835 — Codebase Atlas, repository graph evidence; merged October 14.
- PR #841 — Temporal Graph, commit-based history; merged October 15.
- Issue #588 — Resource System and already-owned Azure credit documentation. It is an **observation source, not a confirmation or independent review**.
- E0 PR #1040 — structural graph measurement; retains `NOT_MEASURED` when no operational event input.
- Issue #821 — minimal-versus-full human-value falsifier.
- Issue #1002 — source correction, independent review and replay.
- `docs/graph_integration/observation_projection_v0.schema.json` — existing evidence graph projection.
  
No change to these source systems. E1 is additive and does not infer resource eligibility, alter a Resource Miner row, or update a governance register.

## Run

From `operations` checkout, with Python 3.11 (stdlib only):

```bash
python3 -m unittest discover -s tests -p 'test_attractor_evidence_bridge_e1.py' -v
python3 tools/attractor_evidence_bridge_e1.py --smoke-test
GH_TOKEN=... python3 tools/attractor_evidence_bridge_e1.py \
  --live --repo humanaios-ui/operations --prs 835,841 \
  --outcome-issue 588 \
  --output /tmp/attractor-e1.json \
  --html /tmp/attractor-e1.html
```

In GitHub Actions, `GH_TOKEN` uses only the runner's read-scoped GitHub token. Never write a token into a command line, issue, file or artifact. Public GitHub GET routes are strictly allowlisted to three repositories and specific PR, commit, check-run, issue and comment paths. Redirects are refused; response sizes are bounded; partial check pagination fails closed. If rate-limited or unavailable, the live job fails without inventing evidence. The separate offline test job still demonstrates the contract.

For offline testing, `--snapshot /private/reviewed-github-shape.json` is permitted, but all resulting observations are explicitly `OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED`. No automatic conversion of a hand-authored snapshot into live or authenticated source data is possible.

## Exact comment contract

**These are only protocol samples with fake IDs and digests. Do not post them as real findings.**

A claimant with a normal GitHub account posts a comment on the reviewed issue consisting of **only**:

```humanaios-outcome-claim-v1
{"schema":"humanaios.outcome.claim.v1","objective_id":"OBJ-EXAMPLE","process_id":"resource_miner","event_type":"RESOURCE_ACQUIRED","source_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evidence_ref":"https://github.com/humanaios-ui/operations/issues/588","evidence_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","resource_id":"RES-EXAMPLE"}
```

A different human GitHub account independently inspects the source and posts its own comment:

```humanaios-outcome-review-v1
{"schema":"humanaios.outcome.review.v1","claim_comment_id":123456,"claim_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","verdict":"SUPPORTS","source_commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","independent_evidence_ref":"https://github.com/humanaios-ui/operations/pull/835","independent_evidence_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"}
```

The `claim_sha256` must be SHA256 of the claim's **canonical JSON** using `json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')`. The claim `source_commit` must be one of the exact heads audited in the same run. An evidence reference is restricted to public GitHub URLs inside the same named repository; E1 never fetches external official sources or handles private receipts. Resource benefit records also require a pseudonymous `benefit_id` and `beneficiary_alias`. No PII, medical/recovery story, bank or AWS/Azure account information, keys, personal resumes or contact details should be posted as GitHub comments.

Distinct GitHub account names and a positive review *do not demonstrate source authenticity*. No independent evidence signature validation exists in E1. A peer's review may be wrong; absence of valid review does not prove absence of acquisition.

## Metrics and acceptance

| Instrument | Value measured | Must never imply |
|---|---|---|
| Source-pinned PR head | GitHub head+fetched commit agree | Z2 ratification or deployment |
| Exact-head checks | Reported CI check runs bound to SHA | Global safety or system benefit |
| Human review events | GitHub review accounts, state, exact SHA | Code quality unless review accepted |
| Repeated check surface | Check name recurs across selected PRs | Agent runtime loop or attractor outcome |
| Claim packet | Declared outcome referencing source commit | Ownership or acquisition |
| Independent review packet | Different GitHub account and pinned claim SHA | First-party receipt authenticated |
| Verified human benefit | `NOT_ESTABLISHED` in E1 | A measured zero or completed recovery benefit |

**Falsifiers:** commit mismatch, unbounded/paginated GitHub data, bot/self review, same-account review, different claim hash, unmatched source commit, external/credentialed URL, corrupted JSON, role injection, unsafe HTML, disputed review, and absent observations.

## Measured E1 boundary

E1 can now connect **real repository activity** to a read-only report and expose independent-review attestations if structured evidence is supplied. The current Issue #588 text documents an existing Azure credit, but the fetched material has not established a separately reviewed, authenticated source proof of ownership or realized value. **Do not report any independently verified acquisition or recovery outcome based on it.**

## E2 work not claimed here

Before `VERIFIED_RESOURCE_ACQUIRED`, `OBJECTIVE_COMPLETED` or `RECOVERY_BENEFIT_DELIVERED` can appear, implement an independently authenticated reviewer with direct first-party evidence retrieval, bounded consent, source attestation and verified provenance. Review state and source evidence must stay separable; private recovery benefit records must live in a protected store and be released only as aggregate, disclosure-approved facts. Use Resource Manager #588 to represent restrictions, usable value, and allocation without mistaking non-cash Azure credit for revenue.
