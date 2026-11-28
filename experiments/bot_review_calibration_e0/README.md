# BOT-REVIEW-CALIBRATION-E0 — past bot reviews vs SMAG predictions (Z1, read-only)

Night asked (2026-11-28) for a small read-only look at past bot reviews as a calibration signal. AUTHORITY_EFFECT=NONE. Nothing posted, no Supabase, no new datastore. GitHub stays the record.

## What it does
- `fetch_rest.sh OUT_DIR` reads, by GitHub REST only: every PR, every CodeRabbit inline comment's severity word (from its header, both header styles), and every bot review's verdict line and quota-failure flag. No comment text is stored. A failed review request is listed in `fetch_errors.jsonl` instead of being read as "no review"; an unmatched severity is `unparsed`, never clean.
- `analyze.py DATA_DIR SMAG_LEDGER OUT_JSON` joins that with `audits/smag_pilot_ledger.jsonl` (resolved rows with a `smag_p` pin) and writes `result.json` plus `result_per_pr.jsonl`.
- `data/` is the snapshot taken 2026-11-28 ~09:20 UTC (re-taken after the CodeRabbit review fixes). Re-running later gives different counts.

Replay: `python3 -I analyze.py data ../../audits/smag_pilot_ledger.jsonl data/result.json` reproduces `data/result.json` from the committed snapshot.

## Observed (snapshot above)
- **Plenty of bot reviews:** 1,092 PRs. Copilot reviewed 731 (427 "Changes recommended", 105 "Needs a closer look", 29 "Approval recommended"); 46 Copilot attempts failed on quota. CodeRabbit reviewed 187 PRs and left 1,110 top-level findings (299 major or critical, 672 minor, 139 trivial, 0 unparsed). 0 review requests failed.
- **Few scored predictions:** only 152 PRs have a resolved SMAG `smag_p` pin, and all 152 were merged. 128 of them also have a bot review.
- **SMAG's red outcome is mostly the admission gate:** of the 79 red PRs (CodeRabbit's own check excluded), 67 include "Repository admission/backpressure gate". Counted that way, agents said 0.86 and got green 48% of the time: Brier 0.40, worse than always saying 0.5 (0.25). Excluding admission/routing checks (list in `analyze.py`), code-red rate is 22% and Brier is 0.19.
- **CodeRabbit majors carry some signal, small n:** code-red rate 27% with a major finding (n=15) vs 6% minor-only (n=16). The first snapshot read 40% vs 7% because an older severity parser missed CodeRabbit's newer header style and counted those PRs as clean; CodeRabbit's review of this PR caught it.
- **Copilot verdict carries little:** code-red 21% "Changes recommended" (n=91), 27% "Needs a closer look" (n=26), 30% "Approval recommended" (n=10).
- **Agent confidence does not move with what bots find:** mean `smag_p` is 0.84 to 0.92 in every group.
- **Contamination:** CodeRabbit runs as a failing commit status (`fail_commit_status: true` in `.coderabbit.yaml`), so it appears in 8 SMAG failure lists. `analyze.py` drops it from the outcome.

## Limits
Observational, one repo, one snapshot. Groups overlap (a PR can have both bots). n per group is 8 to 91; no significance test. Severity is CodeRabbit's own tag, not verified. "Routing" check list is a judgment from the admit-timing failures seen on #1331, #1332 and #1359; change it and the code-red numbers change. Merged-only ledger means no signal on what blocks a merge. No ACAT score.

## What would make it a calibration measure
One reviewer on every PR for about 2 weeks, and SMAG's outcome defined without admission/routing checks. That outcome definition is a Z2 call.
