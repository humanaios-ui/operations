# Q-AGENT-WORKFLOWS-01 — Agent map and workflows: cut what runs hollow, merge what overlaps, one action per Night ask

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-26
**Status:** AWAITING Z2 RATIFICATION
**AUTHORITY_EFFECT:** NONE. No workflow, gate, policy, secret, app or agent setting is changed by this file. Each change below is a separate act that waits for its own Z2 yes.
**Filed because:** Night asked on 2026-11-26 to assess every autonomous agent's capabilities and assignments and build the most useful workflows, scope "ALL" (repo agents, model legs, routines). Night also sent a ChatGPT-written handoff file ("HumanAIOS agent workflow handoffs — Z1 proposal", 2026-11-26); it is checked in Part 3, not adopted.

**Read at:** main `6cf25ac`, GitHub API 2026-11-26 10:00-10:40 UTC. Run window: 3,000 most recent Actions runs, 2026-11-22 23:36 UTC to 2026-11-26 09:45 UTC (3.4 days). Counts are mine from the API, not carried from earlier reports.

## What Z2 is asked to decide

1. Accept the map (Part 1) as the current record of who does what.
2. Accept the role split. Accept, edit or reject each workflow W1-W8 (Part 2). W2, W3, W5 and W7 are already filed as their own draft PRs; each takes effect only when Night merges it.
3. Accept the Part 3 verdict on the ChatGPT handoff file.

## Top findings

1. **Half the Actions load is bot comments waking three workflows.** 1,458 of 3,000 runs (49%) were `issue_comment` runs; 1,253 of those (86%) ended skipped or cancelled. The ECC Tools app posted 385 PR comments in the window (4 per push: Security Evidence, PR Risk Taxonomy, Reference Set Readiness, Hosted Promotion Readiness) and caused 1,027 runs. Nothing in the repo reads its output. Of 766 PR/issue comments in the window, 680 (89%) were bots; 84 were Night's account.
2. **Ten scheduled jobs report green or red while doing nothing useful (two more are already disabled).** Green but hollow: `acat-pipeline-trigger` (all 6 model webhooks unset, 141 runs), `haios-corpus-integrity` (Supabase HTTP 401, check skipped), `agent-api-monitor` (Supabase legacy keys disabled since 2026-09-10), `haios-system-audit` (0 PASS, 6 WARN, 3 SKIP). Red for weeks: `ci-predict-consolidate` (failing since 2026-10-27, merged rolling branch never deleted), `daily-topic-digest` (0 successes in last 100; `jq: Is a directory`), `resource-miner-scan` (0 in last 100; 4 failures, 2 errors in ACAT-R bridge tests), `research-agent` (0 in last 100; empty secret → `curl: blank argument`), `weekly-funding-rescore` (failing since 2026-07-17; `data/opportunities.json` missing), `weekly-profile-sync` (failing since 2026-10-19; pushes straight to protected `main`). Already disabled: `divergence-detect`, `scvc-milestone-witness`.
3. **Night's queue is the bottleneck, and most of it is old.** 37 candidates sit `awaiting_z2`, all submitted 2026-09-08 to 09-19 (67-79 days, every one past the 2-day window). 98 PRs are open, 31 from before November. Of 136 PRs merged in November, 101 (74%) had at least one failed check on the merged head. SMAG (capture per PR, weekly consolidate) ran through this period and the rate rose, not fell.

## Role split (Night's direction, 2026-11-26)

Night is a scientist and operations lead, not a programmer. The concepts, content and direction are Night's; the code and CI were built by AI agents on AI advice. So:

- **Night decides what and why, and ratifies by merging.** Night never has to read code.
- **Agents own how.** Every code PR has one builder agent and a separate reviewer agent. An agent never reviews its own work.
- **Every PR ends with a three-line plain-words card:** what it changes; if it is wrong, what breaks and how to undo; safe to merge yes/no in the reviewer's words. W5 puts this card in the PR template.
- **Only agents with a verified runtime get roles.** Today that is Claude Code (builder: writes PRs in Night's sessions) and CodeRabbit (reviewer: reviews every non-draft PR on `operations` and states a merge risk). Grok and ChatGPT stay on the mail digest; Copilot gets a role only when Night assigns it an issue (its review workflow is disabled and its 3 drafts are idle).

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

Builder for every code row is Claude Code; reviewer is CodeRabbit. Each filed PR carries the plain-words card. Nothing is merged by an agent.

| # | Workflow | Builder → reviewer | Filed as | Night does (one action) | We know it works when |
|---|---|---|---|---|---|
| W1 | **Quiet the PR thread.** Remove the ECC Tools app from `operations`. | Night (app setting; no agent can do it) | — | GitHub → organization `humanaios-ui` → Settings → GitHub Apps → ECC Tools → Configure → Repository access: untick `operations` (or Uninstall). If it is not listed there, the same path is under your personal Settings → Applications. | `issue_comment` runs fall from ~430/day to <150/day within 7 days |
| W2 | **Pause hollow jobs.** Remove the daily cron from `acat-pipeline-trigger`, `haios-corpus-integrity`, `agent-api-monitor`, `haios-system-audit`. Manual runs still work. Each file states its re-enable condition (a webhook secret set; Supabase key rotated; one audit check passing). Merging the PR is the disable; no extra command. | Claude Code → CodeRabbit | own draft PR | Merge | No green scheduled run reports a check it skipped |
| W3 | **Red jobs.** (a) Retire from the schedule: `research-agent`, `weekly-funding-rescore`, `weekly-profile-sync`, `daily-topic-digest` (repo job only; the mail digest trial is untouched). (b) Fix `resource-miner-scan`: `intent_os.py` shadowed the shared hold list and dropped `SOURCE_CONFLICT`, so 6 tests failed; fixed, 618 tests pass. (c) `ci-predict-consolidate` fails because its rolling branch from merged PR #884 still exists (0 commits not on main); Claude Code deletes that branch after Night merges W3a. | Claude Code → CodeRabbit | two draft PRs (a, b) | Merge each | 0 scheduled jobs red for >7 days |
| W4 | **One comment router.** Dropped: see below. | — | — | — | — |
| W5 | **Admit last, one line, plain-words card.** PR template gains the card, builder/reviewer fields and the rule: when implementation checks are green on the final head (the admission gate excluded; Night's admit clears it), the last report ends with `/coordinator admit <sha>`. | Claude Code → CodeRabbit | own draft PR | Merge | Admission-gate failures per week fall from ~130 to <30 |
| W6 | **Close the stale queue (5S Sort).** One Z2 ruling marks the 37 candidates submitted 2026-09-08 to 09-19 LAPSED, not rejected; any can be re-filed. List below. Not filed: it changes Night's own asks. | Claude Code → CodeRabbit | waits for Night's yes | Say yes to the list | Awaiting count stays ≤5, none past 14 days |
| W7 | **Freeze SMAG.** `smag-capture` stops running on each merged PR; `smag-consolidate` stops its weekly PR. Ledger untouched; manual trigger kept. Restore only when an agent is named as the reader of its lessons. | Claude Code → CodeRabbit | own draft PR | Merge | No SMAG PR asks Night to merge |
| W8 | **Weekly backlog card.** After the 2026-12-10 digest verdict: one Monday list of open PRs older than 14 days, each marked merge / close / keep, folded from the three Monday triage jobs. | Claude Code → CodeRabbit | after 2026-12-10 | Tick merge/close/keep | Open PRs older than 30 days fall from 31 toward 0 |

**W4 — No, and here is the cost.** Merging the three comment-triggered workflows means editing the 1,243-line admission gate, the same gate whose admits failed on old heads until PR #1323. W1 alone removes the 385 ECC Tools comments that caused 1,027 of the 1,458 comment runs (70%). What is left after W1 is roughly 2 skipped runs per human or CodeRabbit comment, which costs Actions minutes but nothing from Night. What would flip it: comment runs still above 150/day 7 days after W1.

**Filed (2026-11-26):** W2 #1335, W3a #1336, W3b #1337, W7 #1338, W5 #1339.

**Merge order.** No two of these PRs touch the same file, so any order works. Least risk first: #1335 (W2), #1336 (W3a), #1338 (W7), #1339 (W5), #1337 (W3b). This PR (#1334) only records the plan and can go first. W3c (branch delete) follows #1336.

**W6 list (37).** Q-FRAMEWORK-MAPPING-01 is shown awaiting here but `CLAUDE.md` records it ratified 2026-10-02; the lapse ruling would mark it ratified instead.

- 2026-09-08 Q-DOC-LIFECYCLE-01
- 2026-09-10 Q-FRAMEWORK-MAPPING-01
- 2026-09-10 Q-FRAMEWORK-MAPPING-INTEGRATION-01
- 2026-09-10 Q-NF-SCHEMA-01
- 2026-09-11 Q-PHASE1-2-ROLLOUT-01
- 2026-09-12 Q-ADVREVIEW-CALIB-01
- 2026-09-13 Q-CGBG-BASELINE-01
- 2026-09-13 Q-CGBG-PILOT-01
- 2026-09-13 Q-DOCREVIEW-01
- 2026-09-13 Q-DOCREVIEW-02
- 2026-09-13 Q-GOVGATE-01
- 2026-09-13 Q-RBE-01
- 2026-09-13 Q-REGISTRY-AUDIT-01
- 2026-09-13 Q-REGISTRY-AUDIT-02
- 2026-09-13 Q-REGISTRY-AUDIT-03
- 2026-09-13 Q-RFM-01
- 2026-09-13 Q-TOOLCONTROL-01
- 2026-09-13 Q-TOOLCONTROL-02
- 2026-09-13 Q-TOOLCONTROL-03
- 2026-09-14 Q-BOOT-FINDINGS-SCAN-01
- 2026-09-14 Q-BOOT-STATE-MACHINE-01
- 2026-09-14 Q-IC-BOARD-SEALS-01
- 2026-09-18 Q-BOARD-PUBLISH-01
- 2026-09-19 Q-BOARD-RULING-20
- 2026-09-19 Q-BOARD-RULING-21
- 2026-09-19 Q-BOARD-RULING-22
- 2026-09-19 Q-BOARD-RULING-23
- 2026-09-19 Q-BOARD-RULING-24
- 2026-09-19 Q-BOARD-RULING-25
- 2026-09-19 Q-BOARD-RULING-26
- 2026-09-19 Q-BOARD-RULING-27
- 2026-09-19 Q-BOARD-RULING-28
- 2026-09-19 Q-BOARD-RULING-29
- 2026-09-19 Q-BOARD-RULING-30
- 2026-09-19 Q-BOARD-RULING-32
- 2026-09-19 Q-BOARD-RULING-33
- 2026-09-19 Q-RESEARCH-OPS-LOOP-AND-AUDITOR-01

**Index count line.** Only this PR touches the count line; the W PRs add no candidate. Every Z1 PR that adds a candidate edits `counts:` in `z1-inbox/INDEX.yaml` and the rendered count line in `Z1_INBOX_INDEX.md`, so parallel PRs clash there. Proposal (own draft PR, gate change): derive counts at render time and stop storing them. This PR itself edits that line (136 candidates, 38 awaiting).

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

This proposal is wrong if, 14 days after W1, W2, W3, W5 and W7 land: `issue_comment` runs exceed 200/day, or any scheduled job is red for more than 7 days, or admission-gate failures exceed 30 per week, or Night's open asks (awaiting candidates + PRs older than 30 days) do not fall below 20. Any of these sends the matching workflow back to Z2.

## Not decided here

- Whether the Slack posts from `haios-harmonizer-pulse` have a reader (no Slack connector to check).
- Whether `daily-deadline-alerts` sends mail (log does not show it).
- Red-merge rate by month before November (this file counts November only).
