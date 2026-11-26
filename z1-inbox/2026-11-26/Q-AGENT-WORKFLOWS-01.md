# Q-AGENT-WORKFLOWS-01 — Agent map and workflows: cut what runs hollow, merge what overlaps, one action per Night ask

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-26
**Status:** AWAITING Z2 RATIFICATION
**AUTHORITY_EFFECT:** NONE. No workflow, gate, policy, secret, app or agent setting is changed by this file. Each change below is a separate act that waits for its own Z2 yes.
**Filed because:** Night asked on 2026-11-26 to assess every autonomous agent's capabilities and assignments and build the most useful workflows, scope "ALL" (repo agents, model legs, routines). Night also sent a ChatGPT-written handoff file ("HumanAIOS agent workflow handoffs — Z1 proposal", 2026-11-26); it is checked in Part 3, not adopted.

**Read at:** main `6cf25ac`, GitHub API 2026-11-26 10:00-10:40 UTC. Run window: 3,000 most recent Actions runs, 2026-11-22 23:36 UTC to 2026-11-26 09:45 UTC (3.4 days). Counts are mine from the API, not carried from earlier reports.

## What Z2 is asked to decide

1. Accept the map (Part 1) as the current record of who does what.
2. Accept, edit or reject each workflow W1-W8 (Part 2). A yes here authorizes only the follow-up draft PR or setting change named in that row; each follow-up still needs Night's merge.
3. Accept the Part 3 verdict on the ChatGPT handoff file.

## Top findings

1. **Half the Actions load is bot comments waking three workflows.** 1,458 of 3,000 runs (49%) were `issue_comment` runs; 1,253 of those (86%) ended skipped or cancelled. The ECC Tools app posted 385 PR comments in the window (4 per push: Security Evidence, PR Risk Taxonomy, Reference Set Readiness, Hosted Promotion Readiness) and caused 1,027 runs. Nothing in the repo reads its output. Of 766 PR/issue comments in the window, 680 (89%) were bots; 84 were Night's account.
2. **Ten scheduled jobs report green or red while doing nothing useful (two more are already disabled).** Green but hollow: `acat-pipeline-trigger` (all 6 model webhooks unset, 141 runs), `haios-corpus-integrity` (Supabase HTTP 401, check skipped), `agent-api-monitor` (Supabase legacy keys disabled since 2026-09-10), `haios-system-audit` (0 PASS, 6 WARN, 3 SKIP). Red for weeks: `ci-predict-consolidate` (failing since 2026-10-27, merged rolling branch never deleted), `daily-topic-digest` (0 successes in last 100; `jq: Is a directory`), `resource-miner-scan` (0 in last 100; 4 failures, 2 errors in ACAT-R bridge tests), `research-agent` (0 in last 100; empty secret → `curl: blank argument`), `weekly-funding-rescore` (failing since 2026-07-17; `data/opportunities.json` missing), `weekly-profile-sync` (failing since 2026-10-19; pushes straight to protected `main`). Already disabled: `divergence-detect`, `scvc-milestone-witness`.
3. **Night's queue is the bottleneck, and most of it is old.** 37 candidates sit `awaiting_z2`, all submitted 2026-09-08 to 09-19 (67-79 days, every one past the 2-day window). 98 PRs are open, 31 from before November. Of 136 PRs merged in November, 101 (74%) had at least one failed check on the merged head. SMAG (capture per PR, weekly consolidate) ran through this period and the rate rose, not fell.

## Part 1 — Agent map

Status: LIVE = runs and its output is read or acted on; HOLLOW = runs, output does nothing; RED = fails every run; NO RUNTIME = no verified place it runs.

### Repository agents (`.github/workflows`, 107 files; 132 active per API)

| Agent | Trigger | Does | Hands to | Needs from Night | Status |
|---|---|---|---|---|---|
| Repository coordinator (`repository-coordinator`, `coordinator-admission-sweep` every 6 h, `coordinator-issue-route`) | PR, push, comment, cron | Admission state, decision receipts (96 comments in window), `/coordinator` commands | Admission gate | `/coordinator admit <exact head>` per PR | LIVE, noisy |
| Admission gate (`repository-admission-gate`, 1,243 lines) | `pull_request_target`, review, every comment | Blocks merge until admit on exact head | Night | Admit after last push (PR #1323) | LIVE; 65 failures, 419 skips in window |
| Ratify signer (`.z1-control/ratify.py`, `validate.py`, `render.py`, `z2_ratification_gate`) | Manual + PR | Validates INDEX.yaml, renders `Z1_INBOX_INDEX.md` | INTENT-OS reconcile | Merge = ratify (ruling 2026-09-18, PR #1319) | LIVE |
| INTENT-OS reconcile/refresh | push | Opens bot PRs that record ratifications (e.g. #1324, merged 2026-11-26 07:02 UTC by Night) | Night | Merge | LIVE |
| SMAG (`smag-capture`, `smag-consolidate`, `meta-smag-regression`) | each PR, Mondays | Predicted-vs-measured row per PR, weekly lessons PR (#1309) | Nobody reads the lessons | Merge its PRs | HOLLOW (output unused) |
| CI prediction (`ci-predict-pin`, `-resolve`, `-consolidate`) | PR, check_suite, daily | Status comment per PR (76 in window); daily roll-up | — | — | Roll-up RED since 2026-10-27 |
| Molt tier check | PR | Tier comment per PR (25 in window) | — | — | LIVE |
| PR challenge router | every comment | Routes `/challenge` | — | — | 504 skips in window |
| Audits: standing, system, corpus integrity, harmonizer pulse (3×/day to Slack), agent-api monitor, ACAT pipeline trigger | daily cron | Health checks and Slack posts | Slack (reader unverified) | — | 4 HOLLOW (finding 2); pulse reader unverified |
| Monday triage: `governance-triage`, `priority-queue-triage`, `scheduled-audit`, `industry-telemetry` | Mondays | Update bot issues #328, #329, #331, #574 | Issues | — | Run; #328 and #329 have 0 comments since 2026-09-14, #574 has 7 bot comments and 0 human |
| Resource Miner (`scan`, `PR`, `funding-rescore`, `profile-sync`) | daily/weekly | Funding opportunities | Issues #1037, #1143 | — | RED (finding 2) |
| Other Monday/daily jobs (drift, mesh, intake, scorecard, URA HMBM, molt window, graph freshness) | cron | Checks | Step summary/artifacts | — | Green; no consumer named |
| ~60 path-scoped PR tests | PR paths | Tests | Merge gate | — | Keep; not agents |

### Third-party bots on `operations`

| Bot | Does | Evidence | Status |
|---|---|---|---|
| ECC Tools app | 4 audit comments per push | 385 comments, 1,027 runs woken in 3.4 days; `.claude/ecc-tools.json` generated 2026-06-27, not read by any workflow | HOLLOW, costly |
| CodeRabbit | Review comments | 35 in window | LIVE (review) |
| Dependabot | Dependency PRs | 10 open | Backlog |
| GitHub Copilot | Draft PRs | 3 open drafts (#1117 2026-11-03, #1144 2026-11-05, #1192 2026-11-12), none newer; `auto-request-copilot-review` disabled | IDLE |

### Model legs and routines (outside the repo)

| Leg | Assigned | Trigger | Output | Status |
|---|---|---|---|---|
| Grok | Digest opener 07:30-07:45 CT, briefing 10:00 CT, counterevidence | Night's Grok routines | Mail thread "HumanAIOS Daily Repository Cleanup…" | LIVE; on 2026-11-25 Grok opened the thread at 10:04 CT as a placeholder because none existed by 10:00 |
| ChatGPT | 08:00 CT audit, 15:00 CT gap closure (per its own file) | ChatGPT tasks | Reply in digest thread | LIVE (posted 2026-11-25 11:53 CT) |
| Claude (Duet) | Morning brief, check-ins every 3 h 9-22 CT, ACAT-003 scorer 11:04 CT (read only), helper threads | Duet routines | Brief; `digest-trial/` files | LIVE; Claude leg items stay in the brief during the trial |
| Claude Code (Z1) | Engineering PRs, candidates | Night's sessions | PRs | LIVE; author of most of the 82 open `humanaios-ui` PRs |

## Part 2 — Workflows

Rule used: cut or merge before adding. No new agent is proposed; the map shows no gap that an existing agent cannot fill. Nothing here touches the ACAT-003 digest trial (2026-11-26 to 2026-12-09); W8's digest items are scheduled after the 2026-12-10 verdict.

| # | Workflow | Owner agent | Trigger | Input → Output | Handoff | Night does (one action) | We know it works when |
|---|---|---|---|---|---|---|---|
| W1 | **Quiet the PR thread.** Remove ECC Tools from `operations`; make coordinator receipts edit one sticky comment instead of posting new ones. | Night (app), then Claude Code (receipt change, own draft PR) | This ruling | Bot comment flood → ≤1 comment per bot per PR | Coordinator | Uninstall or scope ECC Tools off `operations` in GitHub app settings | `issue_comment` runs fall from ~430/day to <60/day; bot share of PR comments <50% in the next 7 days |
| W2 | **Pause hollow jobs.** Disable the 4 green-but-hollow jobs until a secret or a reader exists. | Claude Code (one draft PR listing `gh workflow disable` targets, reversible) | This ruling | 4 jobs → disabled, listed with re-enable condition | — | Merge that PR | No green run reports a check it skipped |
| W3 | **Fix or retire red jobs.** `ci-predict-consolidate`: delete the merged rolling branch (one act). `resource-miner-scan`: one repair PR for the 6 failing bridge tests. Retire `research-agent`, `weekly-funding-rescore`, `weekly-profile-sync`, `daily-topic-digest` (overlaps the model-leg digest; repo job only, the mail trial is untouched). | Claude Code | This ruling | 6 red jobs → 2 fixed, 4 disabled | — | Merge one PR | 0 scheduled jobs red for >7 days |
| W4 | **One comment router.** Merge `coordinator-issue-route`, `pr-challenge-dialogue` and the comment path of the admission gate into one job that exits at once unless the comment starts with `/coordinator` or `/challenge` from a human account. | Claude Code (own draft PR; gate change) | After W1 | 3 wake-ups per comment → 1 | Admission gate | Merge that PR | Admission-gate skips drop to near 0; no admit missed in 14 days |
| W5 | **Admit last, one line.** A Z1 PR ends its last report with `READY: /coordinator admit <sha>` only when checks are green on that head. | Claude Code, Claude Duet helpers | Last push green | PR → one copy-paste line | Admission gate | Paste the line | Admission-gate failures per week fall from ~130 (65 in 3.4 days) |
| W6 | **Close the stale queue (5S Sort).** One Z2 ruling marks the 37 Sep 8-19 candidates LAPSED, not rejected; any can be re-filed. | Claude Code (one draft PR: INDEX status + ruling record) | This ruling | 37 awaiting → 0 | INTENT-OS reconcile | Merge that PR | Awaiting count stays ≤5 and none past 14 days |
| W7 | **Freeze SMAG.** Disable `smag-capture`, `smag-consolidate`, `meta-smag-regression`; keep the ledger read-only. Re-open only if an agent is named as the reader of its lessons. | Claude Code | This ruling | SMAG PRs stop | — | Merge that PR | No SMAG PR asks Night to merge; red-merge rate is measured without it |
| W8 | **Weekly backlog card (after 2026-12-10).** One list of open PRs older than 14 days, each marked merge / close / keep, read at Friday 16:00 CT review. Use the existing `priority-queue-triage` issue, folded with `governance-triage` and `scheduled-audit` into one Monday issue. | Existing triage job | Monday cron | 3 triage outputs → 1 issue | Night's Friday review | Tick merge/close/keep per row | Open PRs older than 30 days fall from 31 toward 0 |

**Index count line.** Every Z1 PR that adds a candidate edits `counts:` in `z1-inbox/INDEX.yaml` and the rendered count line in `Z1_INBOX_INDEX.md`, so parallel PRs clash there. Proposal (own draft PR, gate change): derive counts at render time and stop storing them. This PR itself edits that line (136 candidates, 38 awaiting).

## Part 3 — Check of the ChatGPT handoff file (2026-11-26)

Read as quoted material. Claims checked against the API on 2026-11-26.

| Claim or assignment | Check | Verdict |
|---|---|---|
| #1317, #1323, #1324 merged | All three merged by Night's account (1324 at 07:02 UTC) | Holds |
| #1116, #986, #1230, #1304, #750, #1068, #1037, #1143, #1329 open; #1332, #1333, #1196 draft; #1292 open | All match | Holds |
| ChatGPT: coordinator + research producer | Runs; posts in digest | Keep, but "coordinator" overlaps Grok's opener; ChatGPT replies, does not coordinate |
| Grok: source discovery, counterevidence | Runs | Keep |
| Claude Code: engineering + separate evaluator | Runs | Keep; scoring stays with the Duet scorer routine already set |
| GitHub Copilot: narrow repair | 3 idle drafts, review workflow disabled | Hold until Night assigns one issue |
| Cursor: adversarial replay | No runtime in repo; named only as an editor surface in `SUBSTRATE_CAPABILITY_REGISTRY.md` | Cut |
| OpenScience: scientific worker | 0 files reference it | Cut |
| Odin: inventory first | Only a PR-path test (`odin-opportunity-e1`) | Cut as an agent; the file itself says hold |
| Witness, AEO/GEO | Work items under #1329 (#1330-#1333), not agents; under audit in another thread | Fold into #1329; not roles |
| Resource Miner: human benefit path | All 4 jobs red (finding 2) | Fix first (W3) |
| 20-field YAML return contract | Baseline: 3 of 38 packets (8%) carried the 7-field header | **No.** Cost: 20 fields per return per leg, read by Night; adds load the trial is measuring. The 7-field header already in Q-DIGEST-COORD-LAYER-01 covers it. Revisit after 2026-12-10 only if the trial shows a field is missing. What would flip it: the verdict shows a needed field absent. |

## Falsifier

This proposal is wrong if, 14 days after W1-W5 land: `issue_comment` runs exceed 200/day, or any scheduled job is red for more than 7 days, or admission-gate failures exceed 30 per week, or Night's open asks (awaiting candidates + PRs older than 30 days) do not fall below 20. Any of these sends the matching workflow back to Z2.

## Not decided here

- Whether the Slack posts from `haios-harmonizer-pulse` have a reader (no Slack connector to check).
- Whether `daily-deadline-alerts` sends mail (log does not show it).
- Red-merge rate by month before November (this file counts November only).
