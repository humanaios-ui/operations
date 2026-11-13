# Apart AI × Epistemics Sprint — Phase 3 candidate protocol (loaded-phrase test)

Status: **PROPOSED / UNRATIFIED / NO_MODEL_RUN**
Tracker: [#1200](https://github.com/humanaios-ui/operations/issues/1200) (primary), [#1114](https://github.com/humanaios-ui/operations/issues/1114) (cumulative Apart log), [#979](https://github.com/humanaios-ui/operations/issues/979), [#977](https://github.com/humanaios-ui/operations/issues/977)
Sprint: [AI × Epistemics Research Sprint, Nov 13–15 2026](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15), deadline Nov 15 23:59 AoE

This directory holds only the parts of #1200's acceptance criteria that are
safe to advance **without** a live model call, outside contact, spend, or any
Z2/consent action: a draft of the frozen protocol, and an offline synthetic
test harness for the measurement rubric. Nothing here authorizes execution.

## What this is

- `PROTOCOL_DRAFT_v0.md` — a draft of the frozen, falsifiable protocol
  (phrases, contexts, sample size, rubric, 429/retry policy, falsifiers)
  called for by #1200 acceptance criterion 3 ("Freeze exact phrases... BEFORE
  real calls"). It is a **draft for discussion**, not a frozen registration
  — the Track A/B scope decision is resolved (see below), but Night's
  admission of budget/reviewer/ethics controls and a repository-coordinator
  admission record are not.
- `synthetic/` — a deterministic, offline scoring harness that implements
  the protocol's *secondary* outcome extractors (word count, abstract-noun
  frequency, hedging, citation-pattern heuristics) and a two-rater agreement
  checker (percent agreement **and** chance-corrected kappa), exercised
  against hand-labeled synthetic fixtures. This is the "fully deterministic
  synthetically labeled scoring fixture offline" step #1200 asks be run
  **before** any real inference, to catch grading leaks in the rubric
  itself — field names and the agreement math were corrected after
  independent review (see below).

## What this explicitly is not

- Not a live model call, not a run of the actual pilot (3 phrases × 2
  contexts × 10 fresh runs), and not evidence of a phrase effect.
- Not the primary outcome measure. Per the protocol, the primary outcome
  (unwarranted authority/profundity/unsupported growth or meaning claims) is
  **two independent blinded human raters**, not an automatic classifier —
  the synthetic harness only validates plumbing (metric extraction, rubric
  schema, agreement computation), to avoid the "keyword-only success claim"
  failure mode #1114 flags from the Phase 1 submission.
- Not consent, registration, outreach, publication, a Z2 label, or a bot
  install. Those remain open per #1200's acceptance criteria and require a
  human (and, for attribution/scope, the prospective collaborator) to act.

## Scope decision: resolved

The operator approved **Track A (loaded-phrase vs. conversational context)**
as the Phase 3 primary direction on Nov 12, 2026 (see [#1200's decision
register](https://github.com/humanaios-ui/operations/issues/1200)). Track B
is deferred. Only the *direction* was approved — not this draft's numeric
choices, a live model/credit spend, or a merge.

## What independent review changed here

PR #1210 carries this directory. A read-only independent-from-author code
inspection, GitHub Copilot, CodeRabbit, and an empirica-autonomy protocol
review (requested as a distinct "protocol reviewer" role, scoped out of
being a blinded rater) converged on the same set of gaps, now fixed:
`token_count` renamed `word_count` (it was a word-like-unit count, not
provider token usage); `citation_like_count` renamed `citation_pattern_count`
(it matches bibliographic syntax, not citation validity); `agreement()` now
computes Cohen's kappa alongside percent agreement and rejects out-of-scale
labels and empty item sets instead of silently resolving them; repeated
hedge phrases are now counted per occurrence; PROTOCOL_DRAFT_v0.md's
previously-undefined "§3.2" missingness thresholds are now concrete numbers;
a masking/blinding procedure and a limitations-and-dual-use section were
added. See `PROTOCOL_DRAFT_v0.md` for the detail.

## Zero-network trial-schedule controls

`synthetic/trial_schedule.py` constructs **60 condition-balanced unique trial IDs** with a
reproducible seed. It requires every initial trial to have a recorded attempt
before retry planning; it allows only HTTP429/timeout transport retries and
limits retries to **two per trial, five per condition, thirty overall (ninety
total attempts)**. Attempt-level errors remain visible, while a recovered
transport error does not become a missing final response. This is a
**deterministic schedule and event simulation, not a provider API mock, live
trial, or observed language effect**.

`synthetic/test_trial_schedule.py` adds nine tests for balanced design,
admission of initial attempts, retry and per-cell caps, invalid sequences,
refusals, recovered failures and final denominators. They passed in a local
offline reproduction before being copied to this branch. Independent
exact-head CI replay remains a separate gate. The existing scoring suite
has twenty synthetic test cases reported in its protocol; neither suite
replaces two blind human primary-outcome raters.

Run from this directory:

```sh
python3 -m pytest synthetic/test_metrics.py synthetic/test_trial_schedule.py -q
```

## Open blocker

The coordinator previously recorded PASS for an earlier pinned PR head,
but **new commits invalidate that exact-head receipt**. Check the
`repository-admission-gate` against the *latest* head; if admission
is missing, only the authorized operator can admit it. Admission is not
research protocol ratification, a code approval, permission to spend, or
permission to conduct real inference. Four earlier human/CodeRabbit
protocol-review threads must be re-reviewed on this head; do not
auto-resolve their threads from the act of writing corrections.

## Reproduce locally (no network, no model calls)

```sh
python3 -m pytest research/apart_phase3_epistemics/synthetic/test_metrics.py -v
```
