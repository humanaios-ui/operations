# Human-reported oracle worksheet — source reconciliation

**Status:** HUMAN-REPORTED ARITHMETIC COMPLETE / ROW-8 SOURCE MATCH EXPLICITLY CONFIRMED BY OPERATOR / NO LIVE EXPERIMENT.
**Source:** [PR #1242](https://github.com/humanaios-ui/operations/pull/1242),
original blank `ORACLE_HAND_CHECK_WORKSHEET.md` at
`6d53cf89ee039b871281a8ff360eda97873d027d`,
Git blob `35f2e3fe586b5541a6a893cfdacd39cb368eaaa0`.
**Locked sample:** `python3 print_oracle_sample.py 10 --seed 20261116`.
**Provenance:** the human operator supplied two versions of a ten-row
hand-computed table in the conversation on Nov 16, 2026, followed by
an explicit third message confirming row 8's source values. This note
records the submissions and compares them with the locked GitHub source.
It is an AI-authored reconciliation of human-reported entries, **NOT**
a signed independent reviewer attestation, a Z2 label, a freeze, or
permission to call models. No direct evidence of how calculations were
performed was obtained.

## Canonical worksheet results, reconstructed from source

Compute `human_net = sum(charges) - credit` and
`human_verdict = FAIL iff human_net > net_limit`.
Equality is PASS. Do **not** use the untrusted `reported_net`.

| i | seed | Source `net_limit` | Human-reported `human_net` (second submission) | Human-reported verdict | Source arithmetic check | Evidence note |
| ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | 220587 | 287 | 295 | FAIL | 295 > 287 | Matches |
| 1 | 666312 | 290 | 291 | FAIL | 291 > 290 | Matches |
| 2 | 898495 | 233 | 234 | FAIL | 234 > 233 | Corrected verdict from initial PASS |
| 3 | 528734 | 202 | 203 | FAIL | 203 > 202 | Matches |
| 4 | 602612 | 270 | 278 | FAIL | 278 > 270 | Matches |
| 5 | 530506 | 265 | 273 | FAIL | 273 > 265 | Matches |
| 6 | 721005 | 252 | 260 | FAIL | 260 > 252 | Matches |
| 7 | 797035 | 315 | 316 | FAIL | 316 > 315 | Matches |
| 8 | 526679 | **239** | **247** | FAIL | 247 > 239 | Last submitted `net_limit` was **246**, not source **239** |
| 9 | 590851 | 294 | 295 | FAIL | 295 > 294 | Matches |

**Row 8 raw evidence retained:** First submission used the correct
source `net_limit=239`, but entered `human_net=246`; the second
submission corrected `human_net=247` yet copied
`net_limit=246` instead of the source `239`.
The human's FAIL judgment is the same under either number:
`247 > 246` and `247 > 239`.
We preserve the original discrepancy. **A subsequent explicit operator
confirmation on Nov 16, 2026 states**: row 8 uses `net_limit = 239`,
`human_net = 247`, and `FAIL`. This is a human-reported source-match
attestation, **not** a third complete 10-row worksheet and not an
independent second-person scientific review.

**Row 2 raw evidence retained:** Initial `234 / PASS` was wrong
against `net_limit=233`; the second submission fixed the verdict to
`234 / FAIL`.

## Bounded review conclusion

- **OBSERVED:** two human-reported worksheet submissions; second contains
  **10/10 arithmetically correct nets** and **10/10 mathematically correct
  FAIL verdicts** for the visible inputs. This is a source-comparison
  finding, not authenticated provenance of human mental computation.
- **OBSERVED:** 9/10 rows in the second submission copied every locked
  source input exactly; row 8 had one `net_limit` mismatch. **A later
  human message explicitly resolves the row-8 source value to 239.**
  The original second submission remains unchanged in the audit history.
- **SUPPORTED:** recomputation with the source's actual row 8
  `net_limit=239` yields `247 / FAIL`, agreeing with the human
  verdict. All ten locked source tasks fail, consistent with the
  historical **failing-only generator**.
- **OBSERVED:** operator explicitly confirmed row 8's `239 / 247 / FAIL`
  in chat. The ten final human-reported results now agree with the
  locked sample, after the documented correction sequence.
- **NOT YET ATTESTED:** independent verification by a *different*,
  unaffiliated human reviewer; external scientific methods review.
- **UNVERIFIED:** whether the tested head has a current protected CI
  run on the newly created documentation. The existing PR text reports
  65 passing unit tests but tests cannot replace human verification.
- **IMPORTANT:** a hand check of ten *failing* original-generator
  examples does not validate the proposed passing-task generator.
  Separate passing-task fixture code and six tests have since been
  committed on parent PR #1159, but their **independent exact-head
  execution and shortcut resistance are not established**. The
  behavioral passing-control cohort remains **NOT RUN**.

## Immediate offline-only continuation

1. **Do not alter** `ORACLE_HAND_CHECK_WORKSHEET.md`. It is the locked,
   deliberately blank reproducibility sample and has a regression
   assertion that all human cells stay blank.
2. **Human row-8 source confirmation COMPLETE:**
   `row 8 / seed 526679 / charges 53,46,57,74,63 / credit 46 /`
   `net_limit 239 / human_net 247 / FAIL` was explicitly confirmed
   Nov 16, 2026. Do not overwrite the original blank worksheet or
   erase the earlier incorrect transcription. This closes the human
   sample source-match question only.
3. Obtain an independent reviewer / two-source differential check
   for oracle edge cases, including `T=limit`, `T<limit`, and
   `T>limit`, with the original generator left unchanged.
4. Review and repair the separately committed **offline valid/invalid
   controls** in parent [PR #1159](https://github.com/humanaios-ui/operations/pull/1159).
   Copilot has identified a critical class-leak shortcut:
   `reported_net - net_limit` has disjoint value sets for VALID and INVALID.
   Correct this before trusting the fixtures, then independently rerun
   tests, include a shortcut-prediction check, and preserve the
   original failing-only study. Do **not** pool outcomes.
5. Keep original v0.3 cohort's 24 calibration / 120 proposed holdout
   IDs, `task()`, `schedule()`, `violates()`, October evidence,
   and `freeze_receipt.json` unchanged. Never promote a proposed
   fixture or a hand-check receipt into a behavioral result.

**Execution boundary:** No model endpoint, credit spend, provider access,
private document disclosure, PR merge, Z2 ratification, or project
submission is authorized by this note. PR #1242 is stacked on the
review-only parent PR #1159. A branch admission or test pass does not
supply human research or merge authority.
