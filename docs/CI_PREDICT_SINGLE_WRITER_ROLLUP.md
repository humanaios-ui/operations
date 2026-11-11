# CI Prediction Consolidation — Single-Writer Maintenance Control

Status: Z1 implementation candidate. Human Z2 review required; no automatic admission or merge.

## Observed failure (2026-10-15)

The prior `.github/workflows/ci-predict-consolidate.yml` runs hourly and
on every PR close, creating a timestamped branch and a new PR for every
nonempty diff to `ledgers/CI_PREDICT_LEDGER.jsonl`.

There were **17 open** `ci-predict: consolidate resolved CI predictions`
PRs (#839, #842, #844-#849, #850-#851, #855-#858, #860, #862, #866).
All are data-only snapshots of the same ledger, not feature implementations.

A bounded inspection showed:
- #839: 132 events / 44 TOKENs.
- #842–#851 (matching group): 162 events / 54 TOKENs; tail
  `e6391443b9a8ce56b0b0ff52b294eafe353ce03eda2a78a5ec4ef17a26304ee5`.
- #855–#866 (matching group): 162 events / 54 TOKENs; tail
  `d3f80dd5a2e9c3da3c7ca5e24310a6fab8a158a9a992c74dac85c381727fcd34`.

**These are not all semantically equivalent.** Two TOKEN resolutions changed
between the second and third groups despite identical TOKEN identities:
- `CI-e90e4cbd35ea-measure-molt-tier-from-the-diff-advisory-4527cd80`:
  YES at run 38653587426/job 116157977703 vs NO at run
  38710329738/job 116339835553.
- `CI-e90e4cbd35ea-repository-admission-backpressure-gate-3dcad4b0`:
  YES at run 38655061130/job 116162748778 vs NO at run
  38710328696/job 116339835121.

This is a source-selection / check-run identity ambiguity, **not evidence
that the original observation was false**. Both observations must be
preserved until source-run chronology, commit/head match and repeat-run
policy are independently verified. Do not pick the newest PR by number
and pretend it subsumes contradictory outcomes.

## New guarded lifecycle

1. PIN and RESOLVE continue as independent observation operations.
2. A trusted-main daily collector rechecks GitHub check conclusions.
3. Before collection, a guard inventories the open consolidation PRs.
   Any timestamped legacy backlog, more than one rolling PR, malformed
   inventory, or missing tool blocks publication. **No 18th PR.**
4. With no backlog, maintain only `ci-predict-consolidate/rolling`.
   Read the candidate ledger as data only; *never run its code*.
5. Verify both hash chains and require the rolling ledger to extend
   main's exact event prefix. Do not force-push, rebase away conflicting
   history, or fabricate a new chain that discards source rows.
6. Consolidation subprocess failures propagate and prevent publication.
7. Revalidate the chain and main's live base ledger before writing.
8. Commit only the ledger; update the existing PR by a fast-forward push.
9. No automatic admission, approval or merge. Source evidence and
   external witness authentication remain separate.

### Rolling-branch post-merge recovery

When the single rolling PR is merged, **verify that the exact PR head or
its merge commit is incorporated in `main`**, and then delete the
`ci-predict-consolidate/rolling` remote branch through the authorized
repository control plane. A stale, undeleted branch intentionally blocks the
next automated rollup; it must not be silently reused from a historical tree,
force-pushed, or allowed to revert unrelated files that advanced on `main`.
A missing branch (git exit 2) is distinct from a remote API/network error:
the latter blocks publication. No automatic branch deletion is performed.

### Strict source retrieval

The daily ledger publisher uses strict, paginated GitHub API decoding.
Failed requests, malformed JSON, missing/invalid `check_runs` arrays,
or mixed batches with one failed source cause the workflow to exit nonzero.
No partially verified batch is published. The older interactive resolver
continues to use non-strict behavior unless explicitly changed by separate
governance review.

The daily schedule is `37 4 * * *` UTC; a manual single-PR dispatch
remains available. The 50-recently-updated-PR sweep is retained for
compatibility; a complete cursor-based historical backfill is **not**
claimed. Run targeted manual backfills when required.

## Backlog disposition (two-stage, fail closed)

- Group the 17 PRs by full verified event content and source-run identity.
- Retain a representative of each **materially distinct** resolution
  until independently rederived. Do not approve or merge conflicting
  branches on hash equivalence alone.
- When source-run chronology is resolved, generate one candidate by the
  existing trusted PIN/RESOLVE tools, verify the `nf_ledger_v0_1` chain,
  and verify its exact base prefix and source commitments.
- Only then close historical duplicates with a comment naming the
  accepted rollup and explaining preserved conflicts.
- After the verified canonical ledger is merged with authorized
  approval, the new workflow may create the sole stable rolling PR.
- Keep any unresolved conflict as an explicit evidence discrepancy,
  not a replacement value in an existing TOKEN.

## Acceptance / falsifiers

- No new timestamped consolidation PRs after deployment.
- At most one open `ci-predict-consolidate/rolling` PR.
- No append on failed collection, API error or invalid chain.
- No silent branch reset, force-push, self-approval or self-merge.
- Both previously conflicting sources remain traceable.
- Protected CI executes `tools/tests/test_ci_predict.py` (existing enrollment).
- Repeated runs with no new verified events make no commit or PR.
- The separate Coordinator policy determines admission and human authority.

**Note:** Closing or merging any existing PR is not part of this
implementation diff. The conflicting backlog requires a distinct,
evidence-bearing human disposition.
