# GitHub Actions workflow inventory

**Last regenerated:** 2026-11-11
**Source of the file count:** `python3 tools/render_workflow_inventory.py --write`

The previous revision of this document was dated 2026-09-21 and said the repository had 52 workflows, with a shell example that still said 42. Both numbers were hand-maintained and wrong. The table below is generated from `.github/workflows/*.yml` and `*.yaml`. Re-run the script after adding or removing a workflow; `python3 tools/render_workflow_inventory.py --check` exits 1 when the marked region is stale.

## What actually gates a merge

The active repository ruleset **Basic** (ruleset id 18594514, target `~ALL`, enforcement active) was read from `GET /repos/humanaios-ui/operations/rules/branches/main` on 2026-11-11. It contains three rules:

| Rule | Effect |
| --- | --- |
| `deletion` | The branch cannot be deleted |
| `non_fast_forward` | Force-push is rejected |
| `copilot_code_review` | Copilot reviews open, non-draft pull requests. `review_on_push` and `review_draft_pull_requests` are both false |

That ruleset does **not** require a status check, an approving review, a review from someone other than the author, or dismissal of stale approvals. `GET /repos/humanaios-ui/operations/branches/main/protection` returned HTTP 403 for the token used to inspect, so a classic branch-protection rule that this token cannot see is not ruled out. Merges of pull requests whose admission gate was red have previously landed with `mergeable_state` `unstable` rather than `blocked`, which is what GitHub reports when the failing checks are not required.

A red check on a pull request is therefore a signal, not a merge block, until the owner adds it to the ruleset. Checks whose workflow text says they are advisory must not be added as required checks: a required advisory check that is designed never to fail does not gate anything, and one that warns on pre-existing defects fails every pull request. A strict YAML load of all 105 workflow files on 2026-11-11 found no duplicate keys. `workflow-lint.yml` still describes itself as advisory because that was the promotion condition while files on `main` did not parse; the file has not been promoted.

### Checks that are written to fail the job

These are the checks worth requiring. The check name GitHub shows is the job's `name:` when set, otherwise the job id. Three workflows use the job id `validate` and do not set `name:`, so their check runs are all called `validate`. Give each a distinct `name:` before requiring them, or a single required context named `validate` does not mean what it looks like.

| Workflow | Check name | What a failure means |
| --- | --- | --- |
| `repository-admission-gate.yml` | `Repository admission/backpressure gate` | The coordinator decision for this pull request is FAIL (no admission, scope drift, capacity, or duplicate objective). A missing receipt comment, a rate-limit 403 while listing every open pull request, a review event on an already-closed pull request, and a full mutation queue are not decision failures. See the companion gate fix. |
| `no-op-pr-guard.yml` | `guard` | The pull request changes zero files |
| `quality-baseline.yml` | `quality` | The pytest baseline failed. The SMAG calibration step in that workflow is advisory |
| `security-gates.yml` | `Python dependency vulnerability scan` | `pip-audit` failed on a changed requirements file. The gitleaks step is `continue-on-error: true`, so `Secret scanning (gitleaks)` does not fail the job |
| `temporal-dissolution-gate.yml` | `Reject unauthorized internal deadline semantics` | Unauthorized internal deadline language |
| `builder-lint.yml` | `Builder v1.7 compliance` | Builder lint failed |
| `tool-manifest.yml` | `Tool manifest integrity` | Manifest drift. Some manifest warnings are still advisory inside the tool |
| `z2_ratification_gate.yml` | `Verify Z2 Ratification Requirements` | Ratification requirements failed. A sibling job in that file is not part of this name |
| `findings-registry.yml` | `validate` (collides) | REGISTERED.md hard failures |
| `governance-files.yml` | `validate` (collides) | Governance file list drift |
| `document-control.yml` | `validate` (collides) | Document registry / frontmatter failed. Markdown lint and link check in this file are advisory (`continue-on-error`) |
| `pr-hygiene.yml` | `Title matches draft state` | Title says draft/WIP but the pull request is ready, or the reverse. The auto-merge and dirty-SLA jobs in that file are mutators, not merge gates |

### Checks that are advisory on purpose

Do not require these. `molt-tier-check.yml` says it never fails the build. `workflow-lint.yml` is named ADVISORY because defective workflows already on `main` would fail every pull request. `graph-capture-lint.yml` says it is not a required check until a Z2 decision adds it. `repository-coordinator.yml` publishes an advisory index.

### Settings the owner has to change by hand

Branch protection and rulesets are not editable from a workflow file.

1. On ruleset Basic (or a new active ruleset targeting `main`), add `required_status_checks` for the fail-closed check names in the table above, after the three `validate` jobs have distinct names. Start with `Repository admission/backpressure gate`, `guard`, `quality`, `Reject unauthorized internal deadline semantics`, and `Builder v1.7 compliance`.
2. Add a `pull_request` rule: `required_approving_review_count` 1, `dismiss_stale_reviews_on_push` true, `require_last_push_approval` true. The last of those is what requires a non-author approval of the latest push.
3. Add the repository secret `SMAG_CONSOLIDATE_TOKEN` described under the SMAG job below. Nothing in git can create that secret.

## Process workflows for the open-PR backlog

These land as separate pull requests. Until they merge, the generated table below only lists files on this branch. Re-run the renderer after they merge.

| File | Behavior |
| --- | --- |
| `repository-admission-gate.yml` | Existing gate. The companion fix stops the check going red before a decision: it no longer lists files and reviews for every open pull request (that fan-out returned HTTP 403 `API rate limit exceeded for installation` on #798, #817, and #827 on 2026-10-21), it does not fail a PASS decision when the receipt comment returns 403 `Resource not accessible by integration` (the failure described on #809), it does not fail a review event for a pull request that is already closed (run 42992433004, PR #1158), and the gate job no longer waits on the `repository-coordinator-state-mutation` queue (run 43098236021 cancelled with `Unable to acquire concurrency group`). A real FAIL decision still fails the check. |
| `smag-consolidate.yml` | Existing weekly job. It now force-with-lease updates `smag-consolidate/rolling` and edits that pull request instead of opening `smag-consolidate/<timestamp>` every Monday. Older open pull requests with the exact title `SMAG: consolidate ledger + refresh gap report` are closed as superseded. Pushes use `secrets.SMAG_CONSOLIDATE_TOKEN` when set, else `GITHUB_TOKEN`. |
| `pr-hygiene.yml` | New. Fails the check when the title and the draft flag disagree. On pull_request and a daily schedule, disables auto-merge when REST `mergeable_state` is not `clean` or a required check-run is not `success` (Checks API, not the combined status). On Mondays, converts an agent or owner pull request back to draft when it has been `DIRTY` with no updates for more than 7 days. Exempts #597, the `do not merge` label, and experiment titles/labels. |
| `auto-label.yml` | New. Labels from existing definitions: `dependencies` (Dependabot), `Z1` and `experiment` from title prefixes, `do not merge` from that phrase, `governance` and `z2-queue` from title prefixes, `substrate:copilot` / `substrate:claude-code` from `copilot/` and `claude/` branches, `smag` on the consolidate bot, `conflict` while `mergeable_state` is `dirty`. Creates only `smag` and `experiment`. `conflict` and `stale` already exist. There is no lowercase `z1` label and no bare `substrate` label. |
| `pr-sweep.yml` | New weekly job, equivalent to actions/stale for the label and the ping. `stale` after 14 days without updates, an author comment at 21 days, a weekly issue `Weekly PR conflict and behind report` listing `DIRTY` and `BEHIND` pull requests. Closes only superseded bot pull requests that share an author and title. Never closes human or owner pull requests. Exempts `do not merge`, live experiments, and #597. |

### Secret the owner must add

`SMAG_CONSOLIDATE_TOKEN`: a fine-grained personal access token or a GitHub App installation token for `humanaios-ui/operations` with contents read/write, pull requests read/write, and issues read. The token's user or app must be allowed to trigger workflows. A `GITHUB_TOKEN` push does not start other workflows, which is why the consolidation pull requests were opening with almost no Actions runs. Until the secret exists the job still updates the rolling pull request, and it prints a warning that Actions will not start.

## Inventory

<!-- workflow-inventory:start -->
Generated by `python3 tools/render_workflow_inventory.py --write`. The date is not embedded here, so `--check` stays green until a workflow file changes.
Workflow files: **105**. Files with a duplicate top-level key or no `on:` trigger: **0**.

Trigger counts are file counts, not mutually exclusive.

| Trigger | Files |
| --- | ---: |
| `workflow_dispatch` | 87 |
| `pull_request` | 66 |
| `push` | 38 |
| `schedule` | 28 |
| `issue_comment` | 3 |
| `pull_request_target` | 3 |
| `branch_protection_rule` | 1 |
| `check_suite` | 1 |
| `issues` | 1 |
| `pull_request_review` | 1 |
| `workflow_run` | 1 |

| File | Name | Triggers | Schedule |
| --- | --- | --- | --- |
| `acat-pipeline-trigger.yml` | ACAT Research Pipeline | `schedule`, `workflow_dispatch` | `0 8 * * *` |
| `acat-r-noninjected.yml` | ACAT-R Existing Non-Injected Runtime Reference Pilot | `pull_request`, `workflow_dispatch` | — |
| `acat-r-second-runtime-comparison.yml` | ACAT-R Second Runtime Fair Comparison | `pull_request`, `workflow_dispatch` | — |
| `acat-r-v01.yml` | ACAT-R v0.1 Offline Contract Tests | `pull_request`, `workflow_dispatch` | — |
| `agent-api-monitor.yml` | agent-api-monitor | `schedule`, `workflow_dispatch` | `0 9 * * *` |
| `agent-coordination-reflex-pilot.yml` | Agent coordination reflex pilot | `pull_request`, `push` | — |
| `agent-principle-compliance-check.yml` | agent-principle-compliance-check | `push`, `pull_request` | — |
| `audit-protocol-v3-1-regression.yml` | Audit Protocol v3.1 Synthetic Gates | `pull_request`, `workflow_dispatch` | — |
| `auto-request-copilot-review.yml` | Legacy Copilot review request (disabled) | `workflow_dispatch` | — |
| `azure-budget-tests.yml` | Azure budget template tests | `pull_request`, `push` | — |
| `azure-readiness-tests.yml` | Azure readiness report tests | `pull_request`, `push` | — |
| `b4-migration-admission.yml` | b4-migration-admission | `pull_request`, `workflow_dispatch` | — |
| `behavioral-compliance.yml` | behavioral-compliance | `pull_request`, `push`, `workflow_dispatch` | — |
| `builder-lint.yml` | builder-lint | `pull_request`, `push`, `workflow_dispatch` | — |
| `cflite_pr.yml` | ClusterFuzzLite PR fuzzing | `pull_request`, `workflow_dispatch` | — |
| `ci-predict-consolidate.yml` | ci-predict-consolidate | `schedule`, `workflow_dispatch` | `37 4 * * *` |
| `ci-predict-pin.yml` | ci-predict-pin | `pull_request` | — |
| `ci-predict-resolve.yml` | ci-predict-resolve | `check_suite`, `workflow_dispatch` | — |
| `claim-intersection-e0.yml` | claim-intersection-e0 | `pull_request`, `workflow_dispatch` | — |
| `codebase-atlas.yml` | codebase-atlas | `pull_request`, `push`, `workflow_dispatch` | — |
| `coordinator-admission-sweep.yml` | coordinator-admission-sweep | `schedule`, `workflow_dispatch` | `17 */6 * * *` |
| `coordinator-issue-route.yml` | coordinator-issue-route | `issue_comment` | — |
| `copilot-base-guard.yml` | copilot-base-guard | `pull_request_target` | — |
| `daily-deadline-alerts.yml` | Daily Deadline Alerts | `schedule`, `workflow_dispatch` | `0 8 * * *` |
| `daily-topic-digest.yml` | Daily Topic-to-Mitigation Digest | `schedule`, `workflow_dispatch` | `0 9 * * *` |
| `deploy-acat-api-azure.yml` | Deploy ACAT API to Azure Container Apps | `pull_request`, `push`, `workflow_dispatch` | — |
| `divergence-detect.yml` | divergence-detect | `schedule`, `workflow_dispatch` | `0 0 * * *` |
| `document-control.yml` | document-control | `pull_request`, `push`, `workflow_dispatch` | — |
| `drift-monitor.yml` | drift-monitor | `schedule`, `workflow_dispatch` | `0 2 * * 1` |
| `external-contribution-admission-witness.yml` | external-contribution-admission-witness | `pull_request_target`, `workflow_dispatch` | — |
| `feedback-replay-1002.yml` | INTENT-OS E1 pinned source-feedback replay | `pull_request`, `workflow_dispatch` | — |
| `findings-registry.yml` | findings-registry | `pull_request`, `push`, `workflow_dispatch` | — |
| `forecasting-tools-031-smoke.yml` | forecasting-tools-0.3.1-compat-smoke | `push` | — |
| `governance-files.yml` | governance-files | `pull_request`, `push`, `workflow_dispatch` | — |
| `governance-invariant-evaluator.yml` | governance-invariant-evaluator | `pull_request`, `workflow_dispatch` | — |
| `governance-triage.yml` | governance-triage | `schedule`, `workflow_dispatch` | `0 7 * * 1` |
| `gpcs-contract.yml` | GPCS contract tests | `pull_request`, `workflow_dispatch` | — |
| `graph-capture-lint.yml` | graph-capture-lint | `pull_request`, `push`, `workflow_dispatch` | — |
| `haios-corpus-integrity.yml` | HAIOS Corpus Integrity | `schedule`, `workflow_dispatch` | `0 2 * * *` |
| `haios-harmonizer-pulse.yml` | HAIOS Harmonizer Pulse | `schedule`, `workflow_dispatch` | `0 0,8,16 * * *` |
| `haios-standing-audit.yml` | HumanAIOS Standing Audit | `push`, `schedule`, `workflow_dispatch` | `0 9 * * *` |
| `haios-system-audit.yml` | HAIOS System Audit | `schedule`, `workflow_dispatch` | `0 6 * * *` |
| `iew-001-admission-negative-controls.yml` | iew-001-admission-negative-controls | `pull_request`, `push`, `workflow_dispatch` | — |
| `industry-telemetry.yml` | industry-telemetry | `schedule`, `workflow_dispatch`, `pull_request` | `30 9 * * 1` |
| `intake-pipeline.yml` | intake-pipeline | `schedule`, `workflow_dispatch`, `push` | `0 3 * * 1` |
| `intent-form-browser.yml` | intent-form-browser | `pull_request`, `workflow_dispatch` | — |
| `intent-os-collaboration.yml` | INTENT-OS collaboration boundary | `pull_request`, `push` | — |
| `intent-os-opportunity-journey-e0.yml` | INTENT-OS Opportunity Journey E0 | `pull_request`, `workflow_dispatch` | — |
| `intent-os-reconcile.yml` | intent-os-reconcile | `push`, `workflow_dispatch` | — |
| `intent-os-refresh.yml` | intent-os-refresh | `push`, `workflow_dispatch` | — |
| `manifest-sync-gate.yml` | manifest-sync-gate | `pull_request`, `workflow_dispatch` | — |
| `mesh-standard-files.yml` | mesh-standard-files | `schedule`, `workflow_dispatch` | `0 6 * * 1` |
| `mesh-sync-batch.yml` | mesh-sync-batch | `pull_request` | — |
| `meta-smag-regression.yml` | Meta SMAG Accuracy Regression | `pull_request`, `workflow_dispatch` | — |
| `metaculus-e0-offline.yml` | Metaculus E0 offline safety | `pull_request`, `workflow_dispatch` | — |
| `mode-haios-interop-e0.yml` | MODE-HumanAIOS E0 synthetic interoperability | `pull_request`, `workflow_dispatch` | — |
| `mode-publisher-influence-e0.yml` | MODE publisher influence source test | `pull_request`, `workflow_dispatch` | — |
| `molt-notification-hook.yml` | MOLT State Tracking & Falsifier Notifications | `push`, `pull_request`, `workflow_dispatch` | — |
| `molt-tier-check.yml` | molt-tier-check | `pull_request` | — |
| `molt-window-close-trigger.yml` | MOLT Window Close Measurement Trigger | `schedule`, `workflow_dispatch` | `0 0 * * *` |
| `no-op-pr-guard.yml` | No-op PR guard | `pull_request` | — |
| `odin-opportunity-e1.yml` | ODIN E1 Opportunity Task Projection | `pull_request`, `workflow_dispatch` | — |
| `on-track-reflex-execution.yml` | on-track-reflex-execution | `pull_request`, `workflow_dispatch` | — |
| `on-track-reflex-observe.yml` | on-track-reflex-observe | `workflow_dispatch`, `issues`, `pull_request` | — |
| `oracle-replay-regression.yml` | Oracle Replay Regression | `pull_request`, `workflow_dispatch` | — |
| `orcid-reconcile-tests.yml` | ORCID reconcile tests | `pull_request`, `push` | — |
| `pages.yml` | Deploy GitHub Pages | `push`, `workflow_dispatch` | — |
| `pr-challenge-dialogue.yml` | PR challenge dialogue router | `issue_comment` | — |
| `priority-queue-triage.yml` | priority-queue-triage | `schedule`, `workflow_dispatch` | `0 12 * * 1` |
| `quality-baseline.yml` | quality-baseline | `pull_request`, `push`, `workflow_dispatch` | — |
| `receipt-reconciliation-post-merge.yml` | Post-Merge Receipt Reconciliation | `push`, `workflow_dispatch` | — |
| `repository-admission-gate.yml` | repository-admission-gate | `pull_request_target`, `pull_request_review`, `issue_comment`, `workflow_dispatch` | — |
| `repository-coordinator.yml` | repository-coordinator | `pull_request`, `push`, `workflow_dispatch` | — |
| `research-agent.yml` | HAIOS Research Agent | `schedule`, `workflow_dispatch` | `0 6 * * 1` |
| `research-validation.yml` | Research Validation | `workflow_dispatch`, `pull_request` | — |
| `resource-miner-azure-readiness.yml` | Resource Miner Azure Container Readiness | `pull_request`, `push` | — |
| `resource-miner-pr.yml` | Resource Miner PR | `pull_request` | — |
| `resource-miner-scan.yml` | Resource Miner Scan | `schedule`, `workflow_dispatch` | `15 6 * * *` |
| `resource-miner-three-source-observation.yml` | Resource Miner Three Source Observation | `pull_request`, `workflow_dispatch` | — |
| `rmo-verification-cross-contract.yml` | RMO URA Cross Contract | `pull_request`, `workflow_dispatch` | — |
| `rmo-verification-opportunities.yml` | RMO Verification Opportunity Offline Tests | `pull_request`, `workflow_dispatch` | — |
| `rnola-governance-validation.yml` | rnola-governance-validation | `pull_request`, `push`, `workflow_dispatch` | — |
| `scheduled-audit.yml` | scheduled-audit | `schedule`, `workflow_dispatch` | `0 9 * * 1` |
| `scorecard.yml` | scorecard-security | `branch_protection_rule`, `schedule`, `push`, `workflow_dispatch` | `0 8 * * 1` |
| `scvc-milestone-witness.yml` | scvc-milestone-witness | `workflow_run`, `schedule`, `workflow_dispatch`, `push` | `17 9 * * *` |
| `security-gates.yml` | security-gates | `pull_request`, `push`, `workflow_dispatch` | — |
| `seed-satellite-ci.yml` | Seed Satellite CI | `workflow_dispatch` | — |
| `semgrep-review.yml` | semgrep-review | `pull_request`, `workflow_dispatch` | — |
| `smag-capture.yml` | smag-capture | `pull_request` | — |
| `smag-consolidate.yml` | smag-consolidate | `schedule`, `workflow_dispatch` | `17 6 * * 1` |
| `sonarcloud-baseline-auto.yml` | SonarCloud Baseline Auto-Capture | `pull_request`, `push`, `workflow_dispatch` | — |
| `system-graph-freshness.yml` | system-graph-freshness | `pull_request`, `push`, `schedule`, `workflow_dispatch` | `17 6 * * 1` |
| `temporal-dissolution-gate.yml` | temporal-dissolution-gate | `pull_request` | — |
| `tool-manifest.yml` | tool-manifest | `pull_request`, `push`, `workflow_dispatch` | — |
| `ura-hmbm-daily-regression.yml` | URA HMBM State-Triggered Regression (read-only) | `schedule`, `workflow_dispatch`, `pull_request` | `17 13 * * *` |
| `verified-receipts-tests.yml` | verified-receipts-tests | `pull_request`, `workflow_dispatch` | — |
| `wardens-council-prototype.yml` | Wardens Council Prototype Tests | `pull_request`, `push`, `workflow_dispatch` | — |
| `wardens-lineage-prototype.yml` | Wardens persistent lineage + Discord prototype tests | `pull_request`, `workflow_dispatch` | — |
| `weekly-funding-rescore.yml` | Weekly Funding Rescore | `schedule`, `workflow_dispatch` | `30 9 * * 1` |
| `weekly-profile-sync.yml` | Weekly Profile Sync | `schedule`, `workflow_dispatch` | `0 9 * * 1` |
| `workflow-lint.yml` | workflow-lint | `pull_request`, `push`, `workflow_dispatch` | — |
| `workflow-path-validation.yml` | workflow-path-validation | `pull_request`, `push`, `workflow_dispatch` | — |
| `workspace-evidence-bus-roundtrip.yml` | Workspace Evidence Bus Roundtrip | `workflow_dispatch`, `pull_request` | — |
| `z2-ratification-z3-kickoff.yml` | Z2 Ratification → Z3 Executor Kickoff | `push`, `workflow_dispatch` | — |
| `z2_ratification_gate.yml` | Z2 Ratification Gate | `pull_request`, `push`, `workflow_dispatch` | — |
<!-- workflow-inventory:end -->

## How to regenerate

```bash
python3 tools/render_workflow_inventory.py --write
python3 tools/render_workflow_inventory.py --check
```

The script is stdlib-only. It records workflow `name:`, the keys under top-level `on:`, cron strings, and duplicate top-level keys. A duplicate top-level key is the defect that makes GitHub create a zero-job run that looks like a failed gate (`workflow-lint.yml` describes that failure mode). The script does not decide which checks are required; that is the ruleset, described above.

**Governance:** this file is a Z1 inventory of what is in the tree and what the rules API returned. Changing a workflow that is a gate is still a Tier 2 edit. Adding a required check or a review rule is a repository setting and is not done by merging this document.
