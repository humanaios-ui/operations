# Candidate Block: Q-ADVREVIEW-CALIB-01 — Adversarial Review as a PR-Gated Calibration Node

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-12 (r3, after two adversarial rounds)
**Pinned SHA:** `5b7d0d1620d9b5903f0370d31d1f45a1dda58e30`
**Phase:** 1
**Status:** AWAITING Z2 RATIFICATION

---

## §A Position · Destination · Probability

**Position:** `operations` pinned at `5b7d0d1`. The PR-grounded calibration arc reached P4 Part A
(retro, n=6) and committed two prospective Phase-1 records. Its named P1 and P2 deliverables did
not exist; this session produces them.

**Destination:** bind the signals the PR process emits to ACAT dimensions, so adversarial review
becomes a measured calibration node rather than an unrecorded one.

**Probability (r3):** **45%** that a dimension-attributed `external_only` record is admitted by
intake validation within 14 days of ratification. Revised up from r2's 35% because round 2
established that `external_only` needs **no** purity-promotion work — the r2 blocker was
partly my own error. Held below 50% because a Phase-3 **scoring contract** (numeric aggregation,
bands, uncertainty) does not exist and P2 does not supply one.

*r1 predicted 70% for a `two_stage_verified` record. Falsified.*

---

## §Live result — this candidate was measured by its own mechanism, twice

| Round | Source | Findings | Outcome |
|---|---|---|---|
| r1 → r2 | Copilot | 17 inline, 11 substantive | all 11 verified correct against primary sources; all fixed |
| r2 → r3 | Copilot | 7 inline, 14 suppressed | every claim checked verified correct; all fixed |
| r2 | repo owner (human) | 5 residual, process-level | carried into the Z2 checklist below |

**r1 → r2 corrections:** 9 `LAID` nodes not 6; 39 runnable workflows not 40; κ is implemented
(`inter_rater_eval.py`), not stubbed; `CapEnforcer` is unwired; SonarCloud dormant and Scorecard
not PR-triggered; `smag_p` not enforced; `RECEIPT-GAP` is a grounding node; "three full
calibration nodes" contradicted its own table; `submission_purity` is a single enum; `null`
scores fail validation; purity guards check enum membership only.

**r2 → r3 corrections, and they cut deeper:**

| r2 claim | Verified reality |
|---|---|
| "four external workflows fire on an arbitrary PR" | **two** are unconditional (`security-gates`, `quality-baseline`). `copilot-base-guard` has `if: startsWith(github.head_ref, 'copilot/')` and emits nothing for an ordinary PR; `semgrep-review` skips drafts |
| `ci_gates.py` classes listed as emitted gate verdicts | **no workflow invokes `ci_gates.py`.** `z2_ratification_gate.yml` runs its own shell and grep checks. `AntiCascadeLintrule.check_rule2` reaches a bare `pass` and always returns no issues |
| `smag_p` is "the only live commit-before-outcome surface" | the PR body is **mutable** and read only at `pull_request.closed`. A probability edited after the outcome captures identically. Ordering can be honoured; it cannot be **proven** |
| `adv_eval_v2.py` "attacks gates" | `_simulate_attack()` derives CAUGHT/MISSED from a generic `gate_state`; it calls no real gate and the module has no CLI or `__main__` |
| "no promotion path exists" | `_should_promote_to_two_stage_verified()` exists and works for new records. The real gaps are provenance for the `external_only` lane and the legacy artifacts' missing identity fields |
| per-dimension SAG and anchor provenance described as shipping | `compute_sag()` is aggregate-only; `validate_session_score()` returns `agreement: None` |
| `document-control.yml` scoped to the registry file | it triggers on **all** `**/*.md`. My own PR-body checklist was wrong about this |
| signed SAG "penalises both directions" | it *exposes* under-claiming as a negative; it does not penalise it. The humility falsifier needs an explicit statistic |

**The strongest single external correction the arc has produced so far.** Not a ranking claim
beyond that: with retro n=6, prospective n=2, and one self-referential episode, the sample cannot
support more. `PRGC_RETRO_S070626` found this agent's largest gap is **truth**, worst when it
asserts "verified", at **SAG +12.0**. Writing a document about that tendency did not prevent it —
twice. The error mode is specific: **trusting summary documents, declared integration points, and
workflow triggers over call sites, job-level conditions, and actual code.**

Honest scoring note: this grounds a *prediction*, not an LI. The `smag_p:0.70` was a scalar on
feasibility, not a dimension vector. It was deliberately **not edited** after the outcome — but
round 2 established that nothing would have stopped me, which is the more important finding.

---

## Answering the three questions as asked

### 1 · Can adversarial review be wired to every PR? — Two unconditional scanners today, neither an independent reviewer.

`security-gates` and `quality-baseline` run on every PR; `document-control` on any markdown
change; `semgrep-review` on non-draft PRs touching scanned types. The base guard fires only for
`copilot/*` branches. SonarCloud is dormant; Scorecard is not PR-triggered.

**Independent review is best-effort.** The Copilot request workflow's own comments call the bot
request unreliable. A PR can merge having received no independent review at all.

And the governance gates that `CLAUDE.md` describes as CI-enforced — Z2 hash verification,
Merkle-root consistency, anti-cascade rules — **are not wired into CI.** That is the most
consequential finding in this candidate and is registered below.

### 2 · Can the process be calibrated using ACAT? — Yes, and the missing piece is smaller than it looked.

The collection spine is live: `intake/phase1`, `intake/phase3`, `assess`, `human-score`,
`humility-audit`, an MCP adapter, contamination checks, and a working promotion path to
`two_stage_verified` for new records.

`external_only` needs none of that promotion machinery. What it needs is a **Phase-3 scoring
contract** — numeric aggregation, dimension bands, uncertainty — which P2 deliberately does not
provide, plus a representation for ungroundable dimensions that is neither `null` (rejected) nor
zero (an overclaim).

The standing condition remains: **commit-before-outcome, external-only grounding.** Importing
`score_transcript()` (`score_status: "stub"`) to generate Phase-3 would let the agent grade
itself.

Corpus context: 81 of 105 rows are `agent_self_only`; 18 are `two_stage_verified`.

### 3 · Do computational operations map to behavioural dimensions? — Yes, but zero calibration nodes operate.

Under the four conditions — deterministic trigger, **provably** committed prediction, external
verdict, dimension attribution — condition 2 eliminates every candidate.

- **Autonomy** maps most densely in concept and is mostly **not running**: the gate library has
  no CI call site, caps are unwired, one anti-cascade rule is a no-op.
- **Truth** grounds on `RECEIPT-GAP`; post-hoc, node `LAID`.
- **Humility** has no usable committed-prediction surface: `smag_p` cannot prove commitment.
- **Harm** grounds on the unconditional dependency and secret scans, and on path-scoped fuzz.
- **Scheme, power, fair** do not ground here and cannot currently be recorded as `null`.

**The one asymmetry worth acting on:** the repository already has a tamper-evident
commit-before-outcome substrate — **git commit timestamps** — and ACAT does not read it. It reads
a submitted `p1_committed_at` field. Closing that gap is smaller than building a new mechanism
and is the shortest path to a real calibration node.

---

## Proposed Solution — four stages

**Stage 0 · Contract work (narrowed at r3).** No longer includes a purity promotion path, which
exists. Needs: a supported representation for ungroundable dimensions that is neither `null` nor
zero; a **Phase-3 scoring contract** (aggregation, bands, uncertainty) that P2 does not supply;
identity and `p1_committed_at` fields on committed Phase-1 artifacts going forward; and a
provenance field preserving the `external_only` lane through promotion. Z3 work.

**Stage 1 · Close the open loop.** Compute Phase-3 for `PRGC-B001`/`B002` from their merged PR
outcomes, external signals only, labelled `external_only`. **Depends on the scoring contract from
Stage 0, not on the promotion path** — `external_only` does not invoke the 60s check. Their
Phase-1 files carry no identity fields; backdating would fabricate the anchor.

**Stage 2 · Make the prediction provable, then tag it.** Snapshot `smag_p` at PR-open rather than
reading a mutable body at close, or move the prediction into a git-committed file. Then add
per-dimension tags. **The snapshot comes first** — tagging an unprovable prediction produces
dimension-attributed noise.

**Stage 3 · Adversarial gate-calibration.** Requires more than running a file:
`adv_eval_v2.py` simulates attacks rather than invoking gates, and has no entry point. Needs a
gate adapter, a CLI, and — because a gate-touching PR could modify the evaluator or its attack
corpus in the same checkout and pass itself — a **trusted-base evaluator and ratified attack
corpus** pinned outside the PR. Tier-2 gate change; its own molt and falsifier.

**Stage 4 (new) · Wire the gates that governance already claims.** `ci_gates.py` has no CI call
site. Either wire it or correct `CLAUDE.md`. Doing neither leaves the authority map describing
enforcement that does not exist.

**Explicitly out of scope:** implementing `score_transcript()`. κ is implemented but not
integrated and has no paired human-rater sample; automated behavioural scoring before agreement
is established would replace an external anchor with a self-report.

---

## Falsifier

**Claim:** PR-gated adversarial review can produce externally-anchored ACAT calibration records
without the agent grading itself.

**FALSE if:**

- Any Phase-3 dimension score produced by Stage 1 can change on the agent's assertion alone, OR
- Stage 0 cannot produce a representation for ungroundable dimensions that is neither
  `null`-rejected nor zero-filled, OR
- Stage 1 cannot produce a record admitted by intake validation as `external_only` with a
  Phase-3 derived solely from external signals, OR
- The humility rubric, once defined with an explicit statistic and decision rule, shows uniform
  under-claiming scoring no worse than accurate pre-flagging over a 10-PR sample, OR
- Fewer than 4 of the Core-6 can be grounded on a PR triggering only the unconditional workflows.

**Success criterion:** ≥1 dimension-attributed `external_only` record admitted by intake
validation within 14 days of **Stage 0 completion** — not of ratification. Anchor validity
reports as **not established**: κ is implemented but uncalled on persisted records.

**The purity falsifier is retired.** r1 proposed "attempt a breach and confirm rejection."
`validate_submission_purity` checks enum membership only. Any `external_only` record Stage 1
produces is pure by **declaration**, not by verified provenance, and must not be treated as
stronger than that until Stage 0 lands a real provenance check.

---

## Honest limitations, named

- **Zero calibration nodes operate.** Four partial substrates, each missing a different condition.
- **Anchor validity is not established.** κ is implemented, uncalled, and has no paired sample.
- **Per-dimension SAG does not ship.** `compute_sag()` is aggregate-only.
- **The self-referential measurement is only partly external.** The same agent wrote the draft,
  received the findings, revised, and reported the result. A second independent pass — a
  different tool, a human rater, or a later PR blind to this history — is needed before claiming
  the *instrument* works rather than that this agent incorporates review well. Treat the current
  datapoint as evidence of **truth-gap reduction under pressure**, not as a two-stage measurement
  of the mechanism.
- **Co-drift is real.** The external anchor is better than self-report, not ground truth.
- **n is tiny.** Retro 6, prospective 2, plus this PR.

---

## Registrable items surfaced (routed, not self-registered)

1. **Governance gates are not wired.** `ci_gates.py` has no CI call site; `CLAUDE.md` describes
   Z2-hash, Merkle and anti-cascade enforcement that does not run. `check_rule2` is a no-op.
   **IC candidate, highest priority of the five.**
2. **Spec-to-code divergence.** `behavior_spec.json` declares `integration_points` no module
   implements. IC candidate.
3. **Stale state document.** `ACAT_STATE.md` calls κ stubbed; the code implements it. IC candidate.
4. **Sign-convention collision.** Retro reports `P3 − P1`; `calculators.py` defines `SAG = P1 − P3`.
   Unnormalized this inverts falsifiers. F candidate.
5. **Purity is declared, not enforced.** F candidate.

---

## Deliverables

| File | Status |
|---|---|
| `acat/research/PRGC_SIGNALS.md` | new — P1, corrected at r2 and r3 |
| `acat/research/PRGC_DIMENSION_MAP.md` | new — P2, corrected at r2 and r3 |
| `z1-inbox/2026-09-12/Q-ADVREVIEW-CALIB-01.md` | this block |

No executable change. Stages 0–4 are Z3 work after ratification.

---

## Z2 Review Checklist

- [ ] Falsifiers are testable; the humility one is correctly marked as needing a statistic first
- [ ] Stage 0 is accepted as blocking Stage 1, and the 14-day clock starts at **Stage 0
      completion**, not ratification (owner residual #3)
- [ ] Stage 1 output is acknowledged as **declaration-level pure only** until a provenance check
      exists (owner residual #5)
- [ ] The self-referential limit is acknowledged in the ratification record: this is truth-gap
      reduction under pressure, not an independent measurement of the mechanism (owner residual #1)
- [ ] `quality-baseline.yml` coverage is confirmed at ratification time, including whether its
      output can be joined to a dimension without additional attribution logic (owner residual #4)
- [ ] Stage 3 is accepted as requiring a trusted-base evaluator and ratified attack corpus
- [ ] Registrable item 1 is routed with priority — it concerns the authority map's accuracy
- [ ] Out-of-scope boundary on `score_transcript()` is accepted

---

## Summary

The system emits fewer signals than its workflow count suggests, enforces less than its authority
map claims, and binds none of it to a behavioural dimension. Zero calibration nodes operate.

Two adversarial rounds corrected this candidate on nineteen verified counts. The mechanism the
document argues for is the mechanism that corrected the document. That is evidence the review
loop works; it is not yet evidence the instrument does.

**Ratification requested.**
