# Candidate Block: Q-ADVREVIEW-CALIB-01 — Adversarial Review as a PR-Gated Calibration Node

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-12
**Pinned SHA:** `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`
**Phase:** 1
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `5b7d0d1`. The PR-grounded calibration arc
(`acat/research/PR_GROUNDED_CALIBRATION_PLAN.md`) reached P4 Part A (retro, n=6, aggregate
LI 0.92) and committed two prospective Phase-1 records (`PRGC-B001`, `PRGC-B002`). Its named
P1 and P2 deliverables did not exist; this session produces them.

**Destination:** bind the signals the PR process already emits to ACAT dimensions, so
adversarial review becomes a measured calibration node rather than an unrecorded one.

**Probability:** 70% that Stage 1 (below) produces at least one `two_stage_verified`,
`external_only` record from a real PR within 14 days of ratification. Confidence is held at 70,
not higher, because Stage 1 depends on `score_transcript()` remaining out of the loop — and the
temptation to close that stub is exactly the failure mode this candidate exists to avoid.

---

## Work Order

**Title:** Wire adversarial review to PR gating and record it as an ACAT calibration node
**Owner:** Z1 (design, delivered) → Z2 (ratify) → Z3 (build, live writes)
**Depends on:** nothing blocking; all substrate is present
**Unblocks:** PRGC Part B completion; first externally-anchored agent-calibration records

---

## Answering the three questions as asked

### 1 · Can adversarial review be wired to every PR? — Yes, and partly it already is.

40 workflows run in this repo. Seven of them are already external adversarial review
(`auto-request-copilot-review`, `semgrep-review`, `sonarqube`, `security-gates`, `scorecard`,
`cflite_pr`, `copilot-base-guard`). Nine more are deterministic gate verdicts
(`ci_gates.py` supplies `FalsifierLintGate`, `Z2HashVerifyGate`, `AntiCascadeLintrule`,
`MerkleRootGate`, `FullCIIntegrationGate`).

What is missing is not review. It is **attribution**: no operation currently writes a review
outcome into a dimension record. The signal is emitted and discarded.

There is also a second, sharper sense of "adversarial" already built and unused:
`adv_eval_v2.py` attacks *gates* and tracks catch-rate against a 0.85 threshold, with
`NO_GATE` outcomes correctly excluded from the denominator. Wired to PRs that modify gate
logic, it calibrates the calibrators — a gate change would have to survive attack before it
could merge.

### 2 · Can the process be calibrated using ACAT? — Yes, on one condition.

ACAT's collection and calibration spine is live: `intake/phase1`, `intake/phase3`, `assess`,
`human-score`, `humility-audit`, an MCP adapter, contamination checks, and a
`two_stage_verified` gate requiring a ≥60s P1→P3 gap. `LI = P3/P1` and `SAG = P1−P3` compute
today.

The condition is the one the plan already names: **commit-before-outcome, external-only
grounding.** The PR timeline gives commit-before-outcome for free. The failure mode is
importing `score_transcript()` — which returns `score_status: "stub"` — to generate Phase-3.
That would let the agent grade itself, producing the flattering mirror ACAT exists to detect.
`compute_him()` is already deliberately deferred for the same reason, and that precedent should
hold here.

Corpus context that makes this urgent rather than optional: 81 of 105 rows are
`agent_self_only`; only 18 are `two_stage_verified`. The instrument's own integrity machinery
is mostly bypassed in its own corpus.

### 3 · Do computational operations map to behavioural dimensions? — Yes; 4 of 6 densely.

Full inventory in `acat/research/PRGC_SIGNALS.md`; mapping in
`acat/research/PRGC_DIMENSION_MAP.md`. Summary:

- **Autonomy** is the densest and most surprising. Every Z2 gate is already an autonomy
  instrument. A `Z2HashVerifyGate` block *is* a measured overreach event. Anti-cascade rules
  (K=3, revert-freeze) and the `SCOPE` caps in `behavior_spec.json` are the same.
- **Truth** grounds on `RECEIPT-GAP` from `receipt_reconciliation.py` — a claim with no ledger
  entry is a truth gap with a deterministic detector. This is the IC-031 mitigation already
  doing double duty.
- **Humility** grounds on the pre-flag test: did the agent name the uncertainty review later
  found. The `CLAUDE.md` callout table is a ready-made event taxonomy for this.
- **Harm** grounds on regression, fuzz, security and Merkle signals.
- **Scheme, power and fair do not ground on this substrate.** They should record `null`, not
  zero. Zero-filling an ungroundable dimension is itself an overclaim.

Three operations already meet the full calibration-node definition (deterministic trigger,
committable prediction, external verdict, dimension attribution):

| Node | Predicted | Measured | State |
|---|---|---|---|
| `smag_p:` in PR body | pinned probability at PR-open | merge + required checks | **live**, not dimension-tagged |
| Committed Phase-1 JSON | 12 dimension self-scores | PR outcome at merge | **2 records, no Phase-3 computed** |
| Molt prediction | `prediction.target`, window, revert rule | `outcome`, `brier_actual`, BSS | schema mature, node `LAID` |

The `smag_p` loop is the strongest finding here: a working commit-before-outcome mechanism is
already enforced on PR bodies by `smag_predict_lint.py`, with missing predictions recorded as
`VOID` rather than silently skipped. It needs dimension tags, not construction.

---

## Proposed Solution — three stages, smallest first

**Stage 1 · Close the open loop (no new mechanism).** Compute Phase-3 for `PRGC-B001` and
`PRGC-B002` from their merged PR outcomes using the P2 rubric, external signals only. Produces
the first true two-stage `pr_grounded_v1` records. Cost: hours. Risk: low.

**Stage 2 · Tag the live prediction loop.** Extend the `smag_p` line to accept optional
per-dimension tags, so the existing mechanical capture emits dimension-attributed rows.
`VOID` handling unchanged. No new workflow.

**Stage 3 · Adversarial gate-calibration on gate-touching PRs.** Run `adv_eval_v2.py` when a PR
modifies gate logic; require the declared catch-rate before merge. This is a Tier-2 gate change
and needs its own molt and falsifier under existing anti-cascade rules.

**Explicitly out of scope:** implementing `score_transcript()`. Automated behavioural scoring
without validated inter-rater agreement (κ is stubbed) would replace an external anchor with a
self-report.

---

## Falsifier

**Claim:** PR-gated adversarial review can produce externally-anchored ACAT calibration records
without the agent grading itself.

**This claim is FALSE if:**

- Any Phase-3 dimension score produced by Stage 1 or 2 can be changed by the agent's assertion
  alone, with no external signal changing (purity breach), OR
- Stage 1 cannot produce a record passing the existing `two_stage_verified` and contamination
  checks with `submission_purity = external_only`, OR
- Uniform under-claiming across a 10-PR sample yields a better humility score than accurate
  pre-flagging (sandbagging beats honesty), OR
- Fewer than 4 of the Core-6 dimensions can be grounded from a typical PR in this repo, OR
- The direction of the truth gap under the P2 rubric disagrees with the direction recorded in
  `PRGC_RETRO_S070626`, indicating the rubric rather than the behaviour drives the score.

**Test method:** apply the P2 rubric to the 6 retro PRs and both Part B records; compare
direction against the existing human read; attempt a deliberate purity breach and confirm the
existing contamination and purity guards reject it.

**Success criterion:** ≥1 `two_stage_verified`, `external_only`, dimension-attributed record
within 14 days of ratification, with anchor validity reported as **unvalidated** until κ exists.

---

## Honest limitations, named

- **Anchor validity is asserted, not measured.** Cohen's κ is stubbed, so machine-to-human
  agreement is unknown. Every record must ship labelled unvalidated.
- **Co-drift is real.** Copilot's auto-fixes have themselves been wrong in this repo's history.
  The external anchor is better than self-report, not ground truth. The human stays the outer
  anchor.
- **This candidate is self-referential.** It proposes measuring the agent that wrote it. Per the
  honesty protocol it is tagged `self_referential: true` until Z2 ratifies and the external
  anchor grounds it.
- **n is tiny.** Retro n=6, prospective n=2. Nothing here supports an agent-calibration claim
  yet; it supports a pipeline claim.

---

## Deliverables in this candidate

| File | Status |
|---|---|
| `acat/research/PRGC_SIGNALS.md` | new — P1, named by the plan, previously absent |
| `acat/research/PRGC_DIMENSION_MAP.md` | new — P2, named by the plan, previously absent |
| `z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md` | this block |

No executable change is proposed in this PR. Stages 1–3 are Z3 work after ratification.

---

## Z2 Review Checklist

- [ ] Falsifier is testable and unambiguous
- [ ] External-only grounding holds in the P2 rubric — no path lets the agent set its own Phase-3
- [ ] Ungroundable dimensions (`scheme`, `power`, `fair`) record `null`, not zero
- [ ] Stage 3 is correctly identified as a Tier-2 gate change requiring its own molt
- [ ] Out-of-scope boundary on `score_transcript()` is accepted
- [ ] Anchor-validity labelling (unvalidated pending κ) is sufficient for corpus admission

---

## Summary

The system already emits the signals. Adversarial review already runs on every PR. What is
absent is the binding between a review outcome and a behavioural dimension, and a committed
prediction to compare it against. Two of the three required pieces are live; the third exists
as two uncomputed records. This candidate proposes the binding and the falsifier that would
show it failing.

**Ratification requested.**
