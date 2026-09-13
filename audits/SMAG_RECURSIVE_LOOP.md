# The SMAG recursive-learning loop

Operationalizes ACAT's self-report-vs-behaviour measurement on the repo itself:
every merged PR's **predicted** delivery (the author's self-report — a Phase-1
analogue) is measured against its **actual** outcome (merge + CI checks — a Phase-3
behavioural analogue). The gap between them is the Learning-Index at the PR surface,
and it feeds back into gates and lessons. This is the "ACAT-on-PR-surface" plan from
`AUDIT_LESSONS_AND_PLAN_UPDATE_S070726.md` (B1–B3), wired end to end.

## The four stages

| Stage | Mechanism | Status |
|---|---|---|
| **MEASURE** | ACAT corpus (`acat/`) + per-PR predicted/measured | live |
| **CAPTURE** | `smag-capture.yml` → `tools/smag_pr_autocapture` posts one row/merged-PR as a comment on issue **#103** | live |
| **CONSOLIDATE** | `tools/smag_consolidate_v1_0.py` drains #103's row-comments → `audits/smag_pilot_ledger.jsonl` (dedup by PR, idempotent) | **added S-071426** |
| **ANALYZE** | `tools/smag_gap_analysis_v1_0.py` → `audits/smag_gap_report.md` (clean / friction / miss, gap_rate by substrate) | **added S-071426** |
| **FEED BACK** | `tools/smag_feedback_v1_0.py` — gap cues → `data/lessons_learned_ledger.json` (idempotent upsert); promoting a hard pattern to `behavioral-compliance.yml` / a REGISTERED finding stays a Z2 act, printed as a proposal, not auto-applied | **added S-091326** |

`smag-consolidate.yml` runs CONSOLIDATE+ANALYZE+FEED BACK weekly and opens a PR with
the deltas, so the loop stays closed without a person remembering to run it.

### FEED BACK's honest current state (S-091326)

Dispatching `smag-consolidate.yml` for real after it sat un-run since 2026-09-07 drained
44 rows (61 → 105) and surfaced a bigger problem than "FEED BACK is manual": **only 2 of
105 rows carry a pinned `smag_p:` prediction.** IC-SMAG-01's mitigation (a `predicted`
field without `smag_p:` is VOID, not scored) is working exactly as designed — but nothing
in the PR-authoring path ever prompted anyone to add one, so calibration data nearly
stopped accumulating the moment the mitigation shipped. Fixed at the source:
`.github/PULL_REQUEST_TEMPLATE.md` now prompts for `smag_p:`. Until enough new PRs pin
one, `smag_feedback_v1_0.py` correctly reports `INSUFFICIENT_DATA` rather than computing
a gap-driver claim from too few rows — that report is itself now recorded as
`SMAG-FEEDBACK-CALIBRATION-STARVED` in `data/lessons_learned_ledger.json`.

The pre-mitigation gap-driver finding (`pr-fuzzing (address)` on 10/18 friction PRs) is
already registered as `H-SMAG-01` / `MOLT-SMAG-01` in
`registry-candidates/blocks/IC-CAND-SMAG-PREDICTION-MISLABEL-S090926.md` — that block
predates the VOID mitigation and cannot be refreshed from current (now-VOID) data; it
still awaits a Priority Queue entry and a Z2 ratification hash, not a fresh copy of the
same finding.

## Why this existed as a gap

CAPTURE was live but nothing drained the rows: the ledger sat at 1 seed row while 9
predicted-vs-measured rows accumulated, un-analyzed, in #103's comments. "Measurement
without metabolism." CONSOLIDATE + ANALYZE close it.

## Reading the gap report

- **clean** — merged, no failing checks (self-report matched behaviour).
- **friction** — merged *with* failing checks (delivered, but not as claimed — the
  reward-hacking smell; candidate for a hard behavioural gate).
- **miss** — not merged (predicted deliver, didn't land).
- **gap_rate = (friction + miss) / graded.** Success over rounds = gap_rate declining.
- **prediction-calibration guard:** `predicted` must carry a pinned `smag_p:` line.
  Rows without it are **VOID** for prediction-calibration claims.

First resolved run (S-071426, 10 rows): measurable_rate 0.9 (9 confirmed); clean_rate 0.333; gap_rate 0.667 — 6 merged PRs shipped
with failing checks. That is the first measured signal the loop was built to surface.

## Run locally

```bash
python3 tools/smag_consolidate_v1_0.py --issue 103        # drain #103 → ledger
python3 tools/smag_gap_analysis_v1_0.py                    # ledger → gap report
python3 tools/smag_feedback_v1_0.py                         # gap report → lessons ledger cues
python3 tools/smag_feedback_v1_0.py --dry-run               # report only, no write
# all three support --smoke-test
```
