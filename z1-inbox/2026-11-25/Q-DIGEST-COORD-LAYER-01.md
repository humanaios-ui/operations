# Q-DIGEST-COORD-LAYER-01 — HAIOS-MM-ACAT-003 daily digest as the multi-model coordination layer: layout, measures, two-week trial

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-25
**Status:** AWAITING Z2 RATIFICATION
**AUTHORITY_EFFECT:** NONE until ratified. Tier 0: no constants, no gates, no workflow, no automation added by this file.

Filed on the owner's instruction of 2026-11-25 to make the HAIOS-MM-ACAT-003 digest format the operational coordination layer for the multi-model (Grok, ChatGPT, Claude) ACAT research and to measure whether it reduces operator workload while preserving evidence integrity. The owner chose Grok as the daily opener the same day. The trial routines (Grok opener, Claude-side read-only scorer) are run outside this repository; this file records the design and the test, not the routines.

## What Z2 is asked to decide

1. **Layout.** Adopt the six-item layout and the three added rules below as the digest format for the trial window.
2. **Measures and verdict.** Adopt W1-W5, I1-I7 and the paired verdict rule as how the trial is judged, before any trial data is read.
3. **Claude-leg gap.** Accept that during the trial the Claude leg's owner items stay in its own task surface and are scored separately, or rule another route.

## Question

Does the layer cut the operator's reading and finding load without losing evidence? A workload gain that costs integrity counts as a failure.

## Baseline (2026-11-18 to 2026-11-25, 8 digest threads, 39 messages)

- 81 asks to the operator. 4 (5%) carry a direct link. 71 (88%) first appear past word 200.
- Median words before the first ask: 213. Median thread length: 4,656 words.
- 38 packets; 3 (8%) carry all 7 header fields.
- 28 ID errors (3.5 a day, at least 2 every day).
- 46 status counts; 0 state when they were read.
- 207 tagged vs 263 untagged factual item lines (44% tagged, hand count).
- 94 carried items; 74 (79%) with no re-check stated.

Per-day counts: `q-digest-coord-layer-01/baseline_metrics.json` (counts only, no message text). Word and position counts: `q-digest-coord-layer-01/score_digest.py`. Digests: `manifest.json` in the same folder.

## Layout (one thread per day)

1. NEEDS YOU TODAY first: `[ACTION] #id | status | one-line ask | link`, owner items only.
2. STATUS line: open PRs, conflicted, idle >14 days, unstable/blocked, merged and closed since last digest. Live at send time with read time, else `UNREAD`. Never a carried number.
3. One line per item with its own link; a leg links only items it opened that day.
4. Stable prefixes `[ACTION] [STATUS] [GROK] [CHATGPT] [CLAUDE]`. No mail labels or filters without owner approval.
5. One opener: Grok, 07:30-07:45 America/Chicago, from 2026-11-26 (owner choice, 2026-11-25). Other legs reply only. No thread by 09:00 CT: a leg may open one tagged `OPENED_LATE`.
6. Audit packets as replies below the summary, headers and claim tags intact.

Added rules:
- Every packet says HAIOS-MM-ACAT-003; PARENT_ID equals the thread's own id.
- Every item line ends `VERIFIED_TODAY` or `CARRIED (leg, date)`.
- A packet goes in the thread of the day it was sent; late packets say `LATE_FOR <date>`.

Open gap: the Claude leg cannot send email from a scheduled run. During the trial its owner items stay in its own task surface and are reported separately; block recall (I1) is scored on the thread alone. A shared list read by a mail-capable leg is a possible later fix and needs a Z2 ruling.

## Measures

| ID | Measure | Baseline | Pass |
| --- | --- | --- | --- |
| W1 | Words before first ask | median 213 | median <= 80 |
| W2 | Asks with direct link | 5% | >= 90% |
| W3 | Asks past word 200 | 88% | <= 10% |
| W4 | Words above first audit packet | n/a (median thread 4,656) | median <= 300 |
| W5 | Days an ask repeats before leaving the block | scored at trial end | lower than baseline |
| I1 | Block recall (thread asks also in NEEDS YOU TODAY) | n/a | >= 95% |
| I2 | Packets with all 7 header fields | 8% | >= 90% |
| I3 | ID errors per day | 3.5 | <= 1, zero PARENT_ID/node mismatches |
| I4 | Status counts with read time or UNREAD | 0% | 100% |
| I5 | Item lines marked VERIFIED_TODAY / CARRIED | 0% | 100% |
| I6 | Claim-tag coverage | 44% (approx.) | not below 44%, aim >= 80% |
| I7 | Leg packets kept below summary | 38 / 8 days | none missing |

Verdict: PASS if >= 3 of W1-W4 pass and every I-measure passes. FAIL if any I-measure ends below baseline, or fewer than 2 of W1-W4 pass. INCONCLUSIVE if fewer than 10 scored days, or integrity holds with only 2 workload passes.

## Trial

- Window: 2026-11-26 to 2026-12-09 (14 digest days); verdict 2026-12-10.
- Day 1: check the opener against its claims (timing, single recipient, PARENT_ID match, no duplicate, prefixes, live/UNREAD counts).
- Daily: score the prior day's thread after the 10:00 CT Grok reply, same script and rubric.
- Second reader: ChatGPT leg scores rubric items blind on 3 random days; < 80% agreement on asks means fix the rubric first.
- Stop rule: any I-measure failing 3 days running pauses the trial.
- Not measurable: operator minutes and attention, decision quality, asks that reached no leg. Proxies: a weekly one-line self-report at the Friday review (minutes a day, asks found outside the block) and first-action lag from GitHub timestamps.
- Confounds: 2026-11-26 holiday; 2026-11-22 outlier day; 2026-11-25 partial; scorer is a participating leg; hand-counted tags.

No CLI, automation, credentials, schema change or authority change is added.

## Falsifier

The layer is falsified, and should not be kept as the coordination format, if at the 2026-12-10 verdict any of these holds over the scored trial days (2026-11-26 to 2026-12-09):

- any integrity measure I1-I7 ends below its baseline value above;
- fewer than 2 of W1-W4 meet their pass value;
- block recall (I1) is below 95%, meaning the shorter summary is hiding asks.

Fewer than 10 scored days makes the result INCONCLUSIVE, not a pass.
