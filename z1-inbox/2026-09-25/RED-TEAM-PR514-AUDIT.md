# Red-team audit — PR #514 (REPOSITORY-COORDINATOR-02: admission and backpressure control)

**Date:** 2026-09-25
**Target:** https://github.com/humanaios-ui/operations/pull/514 at head `4e8028d`
**Auditor:** Z1 (Claude), adversarial posture: "how does an autonomous agent or any contributor get past admission?"
**Standing:** Z1 findings + fixes, awaiting Z2 review. Nothing here ratifies or merges anything.

## Verdict

The v0.2 candidate gate was **bypassable by construction and simultaneously
rejected legitimate work**. Every bypass below was reproduced locally against
the gate script extracted from the PR's workflow. All are fixed on
`claude/red-team-audit-fixes-y3vnd3`, with regression tests.

## Findings

| # | Severity | Finding | Reproduced | Fix |
|---|---|---|---|---|
| 1 | CRITICAL | **Control-plane exemption is a universal bypass.** Any PR touching one of seven control-plane paths (e.g. a whitespace edit to `.github/CODEOWNERS`) was lane `CONTROL_PLANE` and passed admission regardless of the rest of its diff. | Yes: synthetic PR touching `copilot-instructions.md` → `PASS` | `CONTROL_PLANE` now requires **every** changed file to be a control-plane path. Mixed PRs need admission. |
| 2 | CRITICAL | **Policy read from the PR checkout.** The gate ran on `pull_request` and read `REPOSITORY_COORDINATOR_POLICY.json` from the merge ref, so a PR could admit itself by editing the policy it was judged against (and doing so also made it `CONTROL_PLANE`, see #1). | By inspection | Gate moved to `repository-admission-gate.yml` on `pull_request_target`: workflow, policy, tool and `PRIORITY_QUEUE.md` all come from the default branch; PR state is read through the API; no PR code is checked out or executed. |
| 3 | HIGH | **Issue-reference regex never matched.** The heredoc script used `r"(?<![\\w])#(\\d{1,6})\\b"`, which in a Python raw string is a literal backslash pattern. `refs` was always empty, so issue-based admission could never succeed; every ready, non-draft, non-maintenance PR that did not touch a control path failed, including work linked to admitted issue #378. | Yes: synthetic PR with body `Fixes #378` → `FAIL` | Gate now delegates to the tested tool (`--gate N`). Regex lives in one tested place. |
| 4 | HIGH | **Capacity was never enforced.** The gate compared the *size of the policy's admission lists* against the limit (`1 > 4`), not live admitted ready PRs. `CAPACITY_CONTENTION → fail` in the PR description was not implemented. | By inspection | Gate evaluates the real open-PR set via `analyze()`; contention and duplicate objectives fail closed. |
| 5 | HIGH | **Self-asserted admission.** Any mention of `#378` anywhere in a body ("unrelated to #378") counted as admission evidence; no ownership or linkage semantics. | Yes (tool path) | Admission evidence must be a closing-keyword link (`Fixes/Closes/Resolves #N`, GitHub linking semantics) to an admitted issue, or an explicit `pull_request_numbers` entry. |
| 6 | HIGH | **No objective dedup** (Copilot finding, still open at head). Two ready PRs both linking #378 both became `ACTIVE`, violating `ONE_OBJECTIVE_SHOULD_NOT_CREATE_MULTIPLE_ACTIVE_IMPLEMENTATIONS`. Combined with #5, N contributors could each occupy a slot on one objective, or push legitimate work into contention (denial of service on admitted work). | Yes (test) | `DUPLICATE_ACTIVE_IMPLEMENTATION`: all ready PRs sharing an admitted objective are held (gate `FAIL`, action `COMPARE_CONSOLIDATE`). Coordinator still never picks a winner. |
| 7 | MEDIUM | **Label-based maintenance standing.** `labels: ["dependencies"]` granted `MAINTENANCE` (gate `PASS`, no capacity cost). Labels are self-assignable by anyone with triage access. | Yes (test) | Maintenance standing comes from the automated author identity only; labels refine cohorts. |
| 8 | MEDIUM | **Zero-diff PRs consumed capacity** (Copilot finding, still open at head). | Yes (test) | Excluded from `admitted_ready_count`. |
| 9 | MEDIUM | **Operator-queue numerator disagreed with the contention decision** (Copilot finding, still open at head): markdown showed `ACTIVE + CONTROL_PLANE` over the limit while `analyze()` counted only `ACTIVE`. The live comment on #514 read `2/4` with one admitted PR. | Yes (live comment) | Markdown shows `admitted_ready_count/limit` and control-plane count separately. |
| 10 | MEDIUM | **Bot-comment content injection.** The index job runs PR-head Python and the write-capable comment job posts its output verbatim, so a PR can make `github-actions[bot]` assert `ACTIVE / ADVANCE` about itself. The index also applied the PR-checkout policy to the whole repository projection. | By inspection | Index now applies the default-branch policy (fetched via API). The comment carries an explicit provenance footer naming the PR head SHA and pointing to the separate enforcement check. Residual: report text is still PR-head-generated; it is advisory and labelled as such. |
| 11 | LOW | `edited` / `converted_to_draft` were not triggers, so a body edit or draft conversion did not re-evaluate the gate. | By inspection | Both added to the gate's trigger types. |

## Not fixed here (Z2 decisions or repo settings)

- **Required-check configuration.** Nothing in the diff makes `Repository admission/backpressure gate` a required status check. Until branch protection / a ruleset requires it, the gate is informational. Z2 action.
- **A PR that edits the gate workflow itself** still runs the PR's version under the *index* workflow (`pull_request`), but the enforcement workflow is `pull_request_target` and always uses the default-branch definition. CODEOWNERS review on `.github/workflows/` remains the control for the workflow file itself.
- **De-admission is not retroactive.** A policy change merged to `main` does not re-run checks on already-passing open PRs until they receive an event. Recommend a follow-up that re-dispatches the gate for open PRs on policy change.
- **Dependabot bounds.** `open-pull-requests-limit: 3` across six ecosystems still permits 18 concurrent maintenance PRs (observed burst was 12). Grouping is only applied to the GitHub Actions ecosystem. Policy question, not a defect.
- **Copilot instructions are advisory.** They now describe the mechanical behaviour accurately, but the enforcement is the gate, not the prose.

## Verification performed

- Extracted the original gate script from the PR workflow and ran it against synthetic events (bypass and false-hold both reproduced).
- Ran the rewritten `--gate` CLI against eight scenarios plus a duplicate-objective case; all resolve as intended.
- `pytest tools/tests/test_repository_coordinator_v0_1.py`: 32 passed (22 original + 10 red-team regressions).
- `--smoke-test`: PASS.
- Strict YAML parse (duplicate-key rejecting loader, as `workflow-lint.yml` does) on both workflows.
- `tests.test_temporal_dissolution_gate` with `TEMPORAL_SCAN_ENFORCE=1`: OK.
- `scripts/verify_pr_readiness.sh`: 5 passed, manifest regenerated for tool version 0.2.1.

## Falsifier

If, after this lands and the check is required, any ready non-maintenance PR
passes the gate without a closing-keyword link to an admitted issue or an
explicit `pull_request_numbers` entry, or two ready PRs linking one admitted
issue both pass, this audit's fixes are falsified and the gate must be
re-opened.
