# CI triage, November 2026

Status: read-only findings for Z2 review. No workflow was changed. Source: the last 1,000 workflow runs (2026-11-25 23:34 to 2026-11-26 10:24 UTC), plus `.github/workflows/`.

## Headline

CI is noisy, not broken. The repo has 107 workflow files. Half of recent runs (501 of 1,000) come from comment triggers, and most of those were skipped or cancelled rather than failed.

Run volume by trigger (1,000 runs): `issue_comment` 501, `pull_request` 359, `pull_request_target` 68, `push` 37, everything else under 30.

## Findings

### 1. Three workflows fire on every issue or PR comment (about 500 runs in 11 hours)

| Workflow | Runs | Outcome | Problem |
|---|---|---|---|
| `coordinator-issue-route` | 173 | 52 success, 121 cancelled | Legacy workflow whose only step prints a notice that it is disabled. It still starts a runner for every comment. |
| `pr-challenge-dialogue` | 173 | 171 skipped, 2 cancelled | Job is gated on `issue.number == 630`, so it skips on every other comment. |
| `repository-admission-gate` | 155 (comment event) | 149 skipped, 3 success, 3 failure | Needed for admission, but most comment events are skipped. |

Suggested fixes (each touches coordinator or governance paths, so Z2 should decide):
- Remove `coordinator-issue-route.yml`, or switch it to `workflow_dispatch` only. It does nothing today.
- Remove the `issue_comment` trigger from `pr-challenge-dialogue.yml` once pilot PR 630 closes, or move the PR check from the job to the workflow trigger if GitHub allows it.
- Leave `repository-admission-gate` as is until the two above are done, then re-measure.

### 2. About 10 gates run on every PR

`on-track-reflex-observe`, `repository-admission-gate`, `No-op PR guard`, `semgrep-review`, `repository-coordinator`, `molt-tier-check`, `security-gates`, `ci-predict-pin`, `SonarCloud Baseline Auto-Capture`, `temporal-dissolution-gate`, `document-control`, `quality-baseline` each run roughly 25 to 40 times in this window.
- Failure rate for each is low (2 to 4 per about 30), and the failures mostly line up across all of them. That points to a shared cause, such as a bad PR or base state, not ten separate bugs. Worth checking which PRs failed.
- `copilot-base-guard` skipped all 31 runs. Confirm its condition can ever be true.

### 3. Concurrency and timeouts

87 of 107 workflow files have no `concurrency:` block. Adding `cancel-in-progress: true` to PR-triggered workflows would stop stale runs from piling up.

### 4. Existing docs are stale

`.github/WORKFLOWS.md` is the inventory, but it describes a consolidation from an earlier phase. Refresh its counts and tables after any removals above.

## Suggested order

1. Remove or narrow `coordinator-issue-route` (highest noise, zero function).
2. Gate `pr-challenge-dialogue` after PR 630.
3. Add `concurrency` to PR workflows in batches.
4. Investigate the shared PR failures from item 2.
5. Update `.github/WORKFLOWS.md`.

## Method

`gh run list --limit 1000 --json name,conclusion,event,createdAt,workflowName`, grouped by workflow and event. One 11-hour window is a snapshot; re-run it over a longer period before removing anything scheduled.
