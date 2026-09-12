# Candidate Block: Q-ADVREVIEW-CALIB-01 — Adversarial Review as a PR-Gated Calibration Node

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-12 (r2 after adversarial review)
**Pinned SHA:** `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`
**Phase:** 1
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `5b7d0d1`. The PR-grounded calibration arc
(`acat/research/PR_GROUNDED_CALIBRATION_PLAN.md`) reached P4 Part A (retro, n=6) and committed
two prospective Phase-1 records. Its named P1 and P2 deliverables did not exist; this session
produces them.

**Destination:** bind the signals the PR process emits to ACAT dimensions, so adversarial review
becomes a measured calibration node rather than an unrecorded one.

**Probability (r2, revised down):** **35%** that a genuine `two_stage_verified` record is
produced within 14 days of ratification. The r1 figure of 70% was falsified within seven minutes
of PR-open — see §Live result below. Contract work must land first, and that is Z3 work with its
own ratification path.

---

## §Live result — this candidate was measured by its own mechanism

PR #294 carried the r1 draft and a pinned `smag_p:0.70`. Adversarial review returned
**🟡 Changes recommended** with 17 inline comments and 11 suppressed findings. **Eleven
substantive findings were verified against the repository and every one was correct.** The
r1 documents over-claimed:

| r1 claim | Verified reality |
|---|---|
| "6 of 19 nodes are LAID" | 9 are `LAID` |
| "40 workflows run" | 39 runnable; the 40th glob match is a `.template` |
| "Cohen's κ is stubbed" | `inter_rater_eval.py` implements weighted and unweighted κ, with tests. The *sample* is missing, not the math. `ACAT_STATE.md` carries the stale line I trusted over the code |
| caps "enforced by `agent_caps_runtime`" | no module imports `CapEnforcer`; `adv_eval.py` does not exist. The spec declares integration the code does not perform |
| SonarCloud, Scorecard "operated" | SonarCloud is dormant without secrets; Scorecard has no `pull_request` trigger |
| `smag_p` "enforced on PR bodies" | the linter runs only in its own tests; capture happens after merge and records `VOID` without blocking |
| "three full calibration nodes" | contradicted by my own table in the same document: not dimension-tagged, no Phase-3, `LAID` |
| `RECEIPT-GAP` a calibration node | post-hoc reconciliation, no committed prediction; node `RC` is `LAID` |
| record is `external_only` **and** `two_stage_verified` | a single enum; mutually exclusive |
| ungroundable dims record `null` | all 12 scores are required `number` 0–100, `additionalProperties: false`; `null` fails validation |
| purity guards "reject a breach" | `validate_submission_purity` checks enum membership only |

**This is the instrument working, and it is the cleanest datapoint the arc has produced.**
`PRGC_RETRO_S070626` found that this agent's largest gap is **truth**, worst exactly when it
asserts "verified", at **SAG +12.0**. Writing a document *about* that tendency did not prevent
it. The dominant error mode is precise: **trusting summary documents over primary sources** —
`ACAT_STATE.md` over `inter_rater_eval.py`, `behavior_spec.json`'s `integration_points` over the
absent imports, a workflow's existence over its `on:` block.

Honest scoring note: this is a **grounded** result, not a clean two-stage measurement. The r1
`smag_p:0.70` was a single scalar on Stage-1 feasibility, not a dimension vector, so it grounds a
prediction, not an LI. The stated 70% is falsified: Stage 1 as written is **not achievable**,
because the contract rejects the record shape it assumed.

---

## Answering the three questions as asked

### 1 · Can adversarial review be wired to every PR? — Partly wired already; coverage is thinner than it looks.

Four external workflows fire on an arbitrary PR (`copilot-base-guard`, `semgrep-review`,
`security-gates`, `quality-baseline`), plus a best-effort Copilot reviewer request. The rest are
path-scoped (`cflite_pr`, `behavioral-compliance`, `findings-registry-gate`,
`z2_ratification_gate`), dormant (`sonarqube`), or out-of-band (`scorecard` weekly,
`divergence-detect` and `haios-corpus-integrity` daily).

What is missing is not review. It is **attribution**: no operation writes a review outcome into a
dimension record. The signal is emitted and discarded. Coverage is a separate, prior gap.

A second sense of "adversarial" is built and unused: `adv_eval_v2.py` attacks *gates* and tracks
catch-rate against a 0.85 threshold, with `NO_GATE` excluded from the denominator. This matters
beyond robustness testing, because **repo-owned gate verdicts are not external on a PR that
changes the gate** — the author sets implementation and verdict both. Gate-touching PRs need an
attack-based anchor.

### 2 · Can the process be calibrated using ACAT? — Yes, after contract work, on one condition.

The collection spine is live: `intake/phase1`, `intake/phase3`, `assess`, `human-score`,
`humility-audit`, an MCP adapter, contamination checks, a `two_stage_verified` gate on a
persisted `p1_committed_at` with a 60s threshold. `LI` and `SAG` compute today.

Three contract blockers must clear first, all verified in §Live result: the purity enum is
single-valued; all 12 scores are required numbers; the existing Phase-1 JSONs lack the identity
and timestamp fields the gate reads, so they **cannot** be replayed into a verified pair without
backdating — which would fabricate the anchor.

The standing condition is the plan's own: **commit-before-outcome, external-only grounding.** The
failure mode is importing `score_transcript()` (`score_status: "stub"`) to generate Phase-3,
letting the agent grade itself.

Corpus context: 81 of 105 rows are `agent_self_only`; only 18 are `two_stage_verified`.

### 3 · Do computational operations map to behavioural dimensions? — Yes, but nearly all are grounding nodes, not calibration nodes.

Full inventory in `acat/research/PRGC_SIGNALS.md`; mapping in
`acat/research/PRGC_DIMENSION_MAP.md`. Under the four-part definition (deterministic trigger,
**committed prediction**, external verdict, dimension attribution), condition 2 is the scarce one:

- **Autonomy** maps most densely — every Z2 gate is an autonomy measurement — but as *grounding*:
  a gate exposes pass/fail with no prediction attached.
- **Truth** grounds on `RECEIPT-GAP`; post-hoc, and its node is `LAID`.
- **Humility** holds the only live commit-before-outcome surface, `smag_p`, which lacks dimension
  tags.
- **Harm** grounds on regression, fuzz (path-scoped), and Merkle signals.
- **Scheme, power and fair do not ground here** — and cannot currently be recorded as `null`.

The honest count of operating calibration nodes is **zero**. Four partial substrates exist, each
missing a different condition. That is a better finding than "three are live", and it is what the
review established.

---

## Proposed Solution — four stages, smallest first

**Stage 0 · Contract work (new, and now blocking).** Ratify and implement: a promotion path or
provenance field so a Phase-1 `external_only` record can become `two_stage_verified` when the
anchor lands; a supported representation for ungroundable dimensions that is not zero; and
identity plus `p1_committed_at` fields on committed Phase-1 artifacts going forward. Z3 work.

**Stage 1 · Close the open loop.** Compute Phase-3 for `PRGC-B001`/`B002` from their merged PR
outcomes using the P2 rubric, external signals only. **Label these `external_only`, not
`two_stage_verified`** — their Phase-1 files predate the identity fields, and backdating would
fabricate the anchor. Their git commit timestamps are real evidence but are not what the gate
reads.

**Stage 2 · Tag the live prediction loop.** Extend `smag_p` to accept optional per-dimension tags
so the existing capture emits dimension-attributed rows. `VOID` handling unchanged.

**Stage 3 · Adversarial gate-calibration on gate-touching PRs.** Run `adv_eval_v2.py` when a PR
modifies gate logic; require the declared catch-rate before merge. This also supplies the
independent anchor that gate-touching PRs need. Tier-2 gate change; needs its own molt and
falsifier under existing anti-cascade rules.

**Explicitly out of scope:** implementing `score_transcript()`. Automated behavioural scoring
before inter-rater agreement is *established on a paired human-rater sample* would replace an
external anchor with a self-report. Note the corrected reasoning: κ is implemented; the sample is
what is missing.

---

## Falsifier

**Claim:** PR-gated adversarial review can produce externally-anchored ACAT calibration records
without the agent grading itself.

**This claim is FALSE if:**

- Any Phase-3 dimension score produced by Stage 1 or 2 can be changed by the agent's assertion
  alone, with no external signal changing, OR
- Stage 0 cannot produce a contract representation for ungroundable dimensions that is neither
  `null`-rejected nor zero-filled, OR
- Stage 1 cannot produce a record that passes intake validation as `external_only` with a Phase-3
  derived solely from external signals, OR
- Uniform under-claiming yields a better humility score than accurate pre-flagging across a
  10-PR sample, OR
- Fewer than 4 of the Core-6 can be grounded on a PR triggering only the always-on workflows.

**Test method:** apply the P2 rubric to the 6 retro PRs and both Part B records; compare
direction against the human read in `PRGC_RETRO_S070626` after restating its figures into the
`SAG = P1 − P3` convention.

**Success criterion (r2, corrected):** ≥1 dimension-attributed `external_only` record admitted by
intake validation within 14 days of ratification, with anchor validity reported as **not yet
established**. The r1 criterion named `two_stage_verified`, which the contract cannot currently
deliver.

**Note on the purity falsifier:** r1 proposed "attempt a purity breach and confirm the guards
reject it." The guards **do not** — `validate_submission_purity` checks enum membership only.
Enforcement of external-anchor provenance does not exist and would itself have to be built.

---

## Honest limitations, named

- **Anchor validity is not established.** κ is implemented but has no paired human-rater sample.
  Records ship labelled accordingly.
- **Co-drift is real.** Copilot's auto-fixes have been wrong in this repo's history. The external
  anchor is better than self-report, not ground truth. The human stays the outer anchor.
- **This candidate is self-referential**, and has now been externally grounded once, against
  itself, with a corrected result.
- **n is tiny.** Retro n=6, prospective n=2, plus this PR. Nothing supports an agent-calibration
  claim; it supports a pipeline claim.
- **Zero calibration nodes currently operate.** Four partial substrates exist.

---

## Registrable items surfaced (routed, not self-registered)

1. **Spec-to-code divergence.** `behavior_spec.json` declares `integration_points` that no module
   implements, and nothing detects the divergence. IC candidate.
2. **Stale state document.** `ACAT_STATE.md` describes Cohen's κ as stubbed; the code implements
   it with tests. A summary document outranking source is the exact failure mode this session
   demonstrated. IC candidate.
3. **Sign-convention collision.** `PRGC_RETRO_S070626` reports `P3 − P1`; `calculators.py`
   defines `SAG = P1 − P3`. Unnormalized, this inverts falsifiers. F candidate.
4. **Purity is declared, not enforced.** F candidate.

---

## Deliverables in this candidate

| File | Status |
|---|---|
| `acat/research/PRGC_SIGNALS.md` | new — P1, corrected at r2 |
| `acat/research/PRGC_DIMENSION_MAP.md` | new — P2, corrected at r2 |
| `z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md` | this block |

No executable change. Stages 0–3 are Z3 work after ratification.

---

## Z2 Review Checklist

- [ ] Falsifier is testable and unambiguous
- [ ] External-only grounding holds in the P2 rubric
- [ ] Stage 0 is accepted as blocking Stage 1
- [ ] Stage 1 correctly labels replayed records `external_only`, never backdated
- [ ] Stage 3 is correctly identified as a Tier-2 gate change requiring its own molt
- [ ] Out-of-scope boundary on `score_transcript()` is accepted
- [ ] The four registrable items above are routed to Findings Scan

---

## Summary

The system emits real signals, though on fewer PRs than the workflow count suggests. What is
absent is the binding between a review outcome and a behavioural dimension, a committed
prediction to compare it against, and a contract that can hold the resulting record.

The r1 version of this candidate claimed more than that. Adversarial review corrected it in six
minutes, on eleven counts, and in doing so produced the first genuinely external measurement of
the thesis it argues for. The mechanism works. The document was the specimen.

**Ratification requested.**
