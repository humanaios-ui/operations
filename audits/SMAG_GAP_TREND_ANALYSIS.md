# SMAG gap-trend + ACAT-dimension analysis (S-071426)

Gap-trend over the consolidated SMAG ledger, predicted-vs-measured, mapped to ACAT's
Core-6. Companion to issue #103. Regenerate:
`smag_consolidate → smag_resolve → smag_gap_analysis`.

## The capture-timing fix was the whole game

Round 1 (raw capture) reported `measurable_rate 0.2` — SMAG fires at merge-close,
before CI finishes, so 7/10 rows recorded `in_progress`. `smag_resolve` now re-queries
each row's **terminal** check state (preserving the capture snapshot as
`measured_capture`). That moved the number that matters:

| | raw capture (round 1) | resolved |
|---|---|---|
| **measurable_rate** | 0.2 | **0.9** |
| pending (un-measured) | 7 | 0 |
| clean / friction | 0 / 2 | **3 / 6** |
| gap_rate (of confirmed) | 1.0 (n=2) | **0.667 (n=9)** |

Premature capture erred **both ways**: PR #104 looked `friction` (failure:2) but
resolved **clean**; PR #114 looked `pending` but resolved **friction**. The
capture-time snapshot was unreliable up *and* down — resolving is required for any true
number, and `measurable_rate` (not `gap_rate`) was the right number to move first.

## The real signal: the gap is one check, not many misses

gap_rate 0.667 looks alarming until you attribute it. `smag_resolve` records which
checks failed; the analysis tallies them:

| failing check | PRs |
|---|---|
| **`claude`** | 6 |
| `Builder v1.7 compliance` | 1 |

**The gap is dominated by a single check — `claude` (the claude-review workflow) —
failing on 6 of 9 PRs and merged over.** That is not six independent quality misses;
it is one systemic issue: a review gate that is red on nearly every PR. Either it is
broken (e.g. mis-configured / missing credential, like earlier CI-token issues) or it
is a genuine advisory that is being ignored at merge. **Diagnose that one check before
reading gap_rate as calibration** — otherwise the loop measures a broken gate.

## Trend by date (N=10, small — stated as such)

| date | clean | friction | gap_rate |
|---|---|---|---|
| 07-08 | 1 | 0 | 0.0 |
| 07-09 | 0 | 2 | 1.0 |
| 07-10 | 0 | 3 | 1.0 |
| 07-14 | 2 | 1 | 0.333 |

A dip toward clean on 07-14 — but with the `claude` check dominating, "improvement"
mostly means that check passed/was skipped on #125/#127, not that calibration changed.
Honest verdict: **inconclusive as a calibration trend until the `claude` check is fixed
and more rounds accumulate.**

## Mapping to ACAT Core-6 (truth / service / harm / autonomy / value / humility)

The predicted-vs-measured gap **is the humility (calibration) dimension** at the PR
surface — a PR's self-reported delivery vs its merge+CI reality.

| ACAT dimension | rows | how it shows up | confidence |
|---|---|---|---|
| **humility** | 6 | the friction gap — merged claimed, checks disagree | high |
| **truthfulness** | 6 | the PR narrative claims delivery the failing check contradicts | high |
| **service** | churn | create-then-delete (#114→#122); no `miss` this round | medium |
| harm / autonomy / value | — | not attributable from merge+CI alone | **unmapped — needs the LLM `gap` tier** |

Caveat inherited from above: since the friction is one recurring check, the
humility/truthfulness attribution is really "merged over a known-red gate," a
*governance* calibration gap more than a per-PR self-report gap. Both are real; the LLM
`gap` tier is what would separate them.

## Next (in order)

1. **Diagnose the `claude` check** — is it broken or a real advisory? Fix or explicitly
   de-advisory it. This is the single highest-leverage move; it dominates the gap.
2. **Accumulate rounds** — `smag-consolidate.yml` now runs consolidate → resolve →
   analyze weekly, so `measurable_rate` stays high and the trend fills in.
3. **Then wire feedback** — once the gate noise is gone and N is larger, a persistent
   friction pattern earns a lessons writeback + a hard behavioural gate.

**Success metric, honest:** `measurable_rate` is now 0.9 (achieved). Next is a *clean*
`gap_rate` (gate noise removed) that then declines across rounds.
