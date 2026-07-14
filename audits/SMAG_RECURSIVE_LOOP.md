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
| **FEED BACK** | gap cues → `lessons_learned_ledger.json` + promote hard patterns to `behavioral-compliance.yml` / a REGISTERED finding | manual (v1) |

`smag-consolidate.yml` runs CONSOLIDATE+ANALYZE weekly and opens a PR with the deltas,
so the loop stays closed without a person remembering to run it.

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

First run (S-071426, 10 rows): clean_rate 0.778, gap_rate 0.222 — 2 merged PRs shipped
with failing checks. That is the first measured signal the loop was built to surface.

## Run locally

```bash
python3 tools/smag_consolidate_v1_0.py --issue 103        # drain #103 → ledger
python3 tools/smag_gap_analysis_v1_0.py                    # ledger → gap report
# both support --smoke-test
```
