# What is running — one list

Status: Z1 inventory for Z2 (Night) review. Read-only snapshot. Nothing was stopped, paused or changed to make it.
Checked: 2026-11-26, about 11 AM CT, by Claude (thread "Make everything running traceable in one list").
Why it exists: Night, 2026-11-26: "Moving forward, anything running anywhere (Azure, Metaculus, etc) should be traceable."

Times are Central (CT). "Until stopped" means no stop date is set anywhere.
GitHub workflow details (every file, not just timers) live in [`.github/WORKFLOWS.md`](../.github/WORKFLOWS.md); PR #1183 regenerates that list. This page only says **what runs on its own** and points there.

## Rule: keep this list true

1. Any PR or agent that **starts, stops, moves or re-times** something that runs on its own (a server, a timer, a routine, a cloud machine, a bot) changes this file **in the same PR**.
2. A thing not on this list should not be running. If you find one, add it with "owner: unknown" and tell Night.
3. Each row says: where, what, who or what started it, why, cost a month, stop date.

## 1. Costs money or has no owner (look here first)

| What | Where | Started by / why | Cost a month | Stops |
|---|---|---|---|---|
| 15 timers that copy the `operations` timers (harmonizer pulse 3x a day, system audit, standing audit, deadline alerts, research pipeline, agent API monitor, plus 9 weekly) | GitHub `empirica-outreach` (private repo) | Copied from `operations`; today's timer shut-off (PRs 1335-1339) only touched `operations`. Owner not named. | Private repo: uses the org's Actions minutes (bill not visible here). `agent-api-monitor` calls the Anthropic API daily: paid, amount unknown. | Until stopped |
| 4 live web services: `operations` (serves api.humanaios.ai), `resource-miner`, `intent-os-relay`, `entitlement-navigator` | Railway project `sweet-perfection` | Auto-deploy from `operations` main on every merge (last: today 9:22 AM CT). Who created each service: not recorded. | Usage-billed; bill not visible to agents | Until stopped |
| ACAT-002 Claude leg: reads the digest thread, sends one Gmail reply a day | Claude routine, 8:43 AM daily | Set up Nov 6 for HAIOS-MM-ACAT-002. Overlaps the ACAT-003 trial now running. | Inside Night's Claude plan | Until stopped |
| HumanAIOS Weekly Checker: checks the digest, replies by Gmail | Claude routine, Mondays 8:20 AM | Set up Oct 24 | Inside Night's Claude plan | Until stopped |
| 2 Workers: `haios-personal-ops`, `humanaios` | Cloudflare | Made Apr-May 2026. Whether they have timers: not visible. | Plan not visible | Until stopped |

## 2. GitHub timers in `operations` (public repo: Actions minutes are free)

About 2,500 workflow runs in the last 7 days (all triggers). 17 timers on, 2 switched off in GitHub (`divergence-detect`, `scvc-milestone-witness`).

| Timer | When (CT) | Note |
|---|---|---|
| coordinator-admission-sweep | every 6 hours | |
| haios-harmonizer-pulse | 10 AM, 6 PM, 2 AM | |
| molt-window-close-trigger | 6 PM daily | |
| resource-miner-scan | 12:15 AM daily | failed all 6 runs this week |
| daily-deadline-alerts | 2 AM daily | |
| haios-standing-audit | 3 AM daily | |
| ura-hmbm-daily-regression | 7:17 AM daily | |
| ci-predict-consolidate | 10:37 PM daily | failed all 6 runs this week |
| drift-monitor | Sun 8 PM | |
| intake-pipeline | Sun 9 PM | |
| mesh-standard-files | Mon 12 AM | |
| system-graph-freshness | Mon 12:17 AM | |
| governance-triage | Mon 1 AM | |
| scorecard | Mon 2 AM | |
| scheduled-audit | Mon 3 AM | |
| industry-telemetry | Mon 3:30 AM | failed this week |
| priority-queue-triage | Mon 6 AM | |

Started by: merged PRs over time. Why: see each file and `.github/WORKFLOWS.md`.

## 3. Claude routines (inside Night's Claude plan, no extra bill)

| Routine | When (CT) | Why | Stops |
|---|---|---|---|
| Morning brief | 8:46 AM daily | Night's daily brief | Until stopped |
| Check-ins | every 3 hours, 9 AM-10 PM | Night's check-ins | Until stopped |
| ACAT-003 digest trial scorer | 11:04 AM daily | Trial Nov 26-Dec 9 | Stops itself Dec 10 |
| Code learning log rows | 7:23 PM daily | One merge, one lesson | Stops itself after 14 quiet days or when task closes |
| ACAT-002 leg, Weekly Checker | see section 1 | | Until stopped |

Off (kept, not running): Foundation Audit Aggregator, Monitor Collab Responses, m2r3-hourly-sync.

## 4. Stopped or idle (listed so nobody wonders)

| What | Where | State |
|---|---|---|
| Metaculus forecasting bot (`scintillating-playfulness`) | Railway, `tools/Metaculus` | Not running. Restart set to never; auto-deploy paused Nov 24 until live posting is approved. Holds keys for 5 paid AI APIs, but spends nothing while stopped. |
| Railway project `elegant-commitment` | Railway | Empty, no services |
| Supabase `HumanAIOS` | Supabase, free plan | Live database, $0. 5 edge functions run only when called. |
| Supabase `FTLA` | Supabase, free plan | Paused |
| Azure | Microsoft for Startups credit ($5,000, ends Jan 2) | Nothing running (Night, Nov 26). Any machine started later goes on this list first. |
| Corpus integrity check | GitHub `empirica-outreach` | Paused by PR 28 (Nov 26) |

## 5. Could not see (blind spots)

- GitHub repos `humanaios` and `lasting-light-ai`: their files have timers (`mesh-sync-batch`, `state-validate`, `acat_pipeline_trigger`, `framework-audit`); whether they run was not visible from here.
- GitHub repos `opportunity-aggregator`, `empirica-foundation-evaluator`: not readable from here.
- Bills: Railway, GitHub Actions minutes, Cloudflare plan, Anthropic and other AI API spend, Azure.
- Work run from other AI accounts: the ChatGPT and Grok digest legs (7:00 and 7:30 AM).
- Anything on Night's own computer (local scripts, schedulers).

Checked with no timers found: `research`, `acat-x`, `oracle-agent`, `acat-inspect` (timer in file, no runs this week), `empirica-autonomy`, `empirica-mesh-support`, `practices-snapshot`, `operations-audit-sandbox`, `heritage-miner`, `ACAT-Observatory`, `arena`, `neuromorphic-whitebox-agent`, `empirica-practice-mesh`.
