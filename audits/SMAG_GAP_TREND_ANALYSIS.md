# SMAG gap-trend + ACAT-dimension analysis (round 1, S-071426)

First real gap-trend read over the consolidated SMAG ledger (10 rows, PRs #98–#127,
2026-07-08 → 07-14), with the predicted-vs-measured gap mapped to ACAT's Core-6
dimensions. Companion to issue #103; regenerate with
`python3 tools/smag_gap_analysis_v1_0.py`.

## Headline: the naive read is wrong, and that is the finding

A naive pass counts every merged PR with no *failing* check as "clean" → clean_rate
0.778. That is exactly the overconfidence ACAT exists to catch. The honest classifier
separates **pending** (merged, but CI still `in_progress` at capture — un-measured)
from **clean** (CI actually resolved green):

| | naive v1 | honest |
|---|---|---|
| clean_rate | 0.778 | **0.0** (of confirmed) |
| measurable_rate | — | **0.2** — only **2 of 10** rows had CI resolved at capture |
| friction | 2 | 2 |
| pending (un-measured) | (counted as clean) | **7** |

**The dominant signal is not the code — it's the instrument.** SMAG captures at
merge-close, *before* CI finishes, so 80% of rows are un-gradeable. Any gap-trend
built on them is noise until capture timing is fixed.

## Trend by date (real, N=10 — small, stated as such)

| date | friction | pending | gap_rate (of confirmed) |
|---|---|---|---|
| 07-08 | 1 | 0 | 1.0 |
| 07-09 | 1 | 1 | 1.0 |
| 07-10 | 0 | 3 | — (all un-measured) |
| 07-14 | 0 | 3 | — (all un-measured) |

The **only two observed check-failures are both early** (PR #104, #108). Everything
after is `pending`. This reads two ways and **we cannot yet disambiguate at N=10**:
(a) genuine early-friction-then-clean improvement, or (b) later captures are simply too
early to see any failure. Honest answer: **inconclusive — fix the instrument, then the
trend means something.**

Secondary signal — **churn:** PR #114 *created* `BEHAVIORAL_GRAMMAR_V1.md`; PR #122
*deleted* it four days later. Built-then-removed work is a Service/efficiency gap the
mechanical tier can flag but not price.

## Mapping to ACAT Core-6 (truth / service / harm / autonomy / value / humility)

The predicted-vs-measured gap **is the humility (calibration) dimension** rendered at
the PR surface — a PR's self-reported "this delivers" (Phase-1 analogue) vs its merge +
CI reality (Phase-3 analogue). Where the signal supports attribution:

| ACAT dimension | rows | how it shows up in SMAG | confidence |
|---|---|---|---|
| **humility (instrument)** | 7 | `pending` — the capture asserts an outcome before CI has resolved it; the *measurement* is overconfident | high (mechanical) |
| **humility (subject)** | 2 | the friction gap itself — merged-state claimed, checks disagree | high |
| **truthfulness** | 2 | friction rows: the PR narrative claims delivery the failing checks contradict | high |
| **service** | churn | create-then-delete (#114→#122); would also cover `miss` (none this round) | medium (mechanical) |
| harm / autonomy / value | — | not attributable from merge+CI alone | **unmapped — needs the LLM `gap` tier** |

This is deliberately partial. `harm` (did a change break/remove something needed),
`autonomy` (did the agent stay in the requested scope), and `value` (did the change
serve the stated goal) require the qualitative `gap` field, which is empty pending the
optional LLM-review tier. Guessing them would reproduce the very failure this measures.

## What round-1 says to do before wiring feedback

1. **Fix capture timing (the real bug).** `smag-capture` should record CI outcome
   *after* checks resolve — e.g. re-poll on `check_suite`/`status` completion, or a
   short delayed re-capture — so `measured` reflects final pass/fail, not `in_progress`.
   Until then `measurable_rate` (0.2) is the number to move, not `gap_rate`.
2. **Then gather more rounds.** N=10 with 2 confirmed is too thin for a trend; the loop
   now accumulates automatically (`smag-consolidate.yml`).
3. **Only then wire feedback.** Once `measurable_rate` is high, a persistent `friction`
   pattern earns a hard behavioural gate (block merge-with-failing-checks) + a lessons
   writeback. Wiring it on today's data would encode instrument noise as a "lesson."

**Success metric, restated honestly:** first `measurable_rate` ↑ (trust the signal),
then `gap_rate` ↓ (the substrate calibrates). Right now we can only report the first.
