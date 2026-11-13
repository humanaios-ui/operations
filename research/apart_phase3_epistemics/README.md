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
  real calls"). It is a **draft for discussion**, not a frozen registration —
  freezing requires the scope decision (Track A vs Track B primary) that
  #1200 explicitly reserves for the originator and Night (Z2).
- `synthetic/` — a deterministic, offline scoring harness that implements
  the protocol's *secondary* outcome extractors (length, abstract-noun
  frequency, hedging, invented-citation heuristics) and an inter-rater
  agreement checker, exercised against hand-labeled synthetic fixtures. This
  is the "fully deterministic synthetically labeled scoring fixture offline"
  step #1200 asks be run **before** any real inference, to catch grading
  leaks in the rubric itself.

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

## Open decision this cannot resolve

#1200 and the Nov 12 review on #1114 both leave **Track A vs Track B as
primary** open, explicitly reserved for the originator's input. This
directory drafts Track A (the originator's phrase hypothesis) as primary,
matching the existing "Primary recommendation to discuss with
originator/Z2" in the #1114 Nov 12 comment — but that draft choice is not a
ratification, and the files here do not freeze anything until that
conversation happens.

## Reproduce locally (no network, no model calls)

```sh
python3 -m pytest research/apart_phase3_epistemics/synthetic/test_metrics.py -v
```
