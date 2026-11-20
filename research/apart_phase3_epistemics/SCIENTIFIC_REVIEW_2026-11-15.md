# Phase 3: bounded adversarial scientific review — 2026-11-15

**Reviewer:** ChatGPT, also a design/review participant; **not an
independent external researcher, blinded human rater, or approving authority.**
Source inspection: PR #1210 head `b43bc771b8f8c7fa5659c4f8a0534ed493e230c9`;
`PROTOCOL_DRAFT_v0.md`, `PRIMARY_RUBRIC_DRAFT.md`,
`synthetic/trial_schedule.py`, `metrics.py`, and the 30-test source;
[exact-head run report](https://github.com/humanaios-ui/operations/pull/1210#issuecomment-6903197251)
and [detached main merge report](https://github.com/humanaios-ui/operations/pull/1210#issuecomment-6903210557).
New
[`PROTOCOL_FREEZE_CANDIDATE_v1.md`](PROTOCOL_FREEZE_CANDIDATE_v1.md)
is **proposed** and was not exercised by the old 30-test report.

## Review verdict

**Scientific direction: SUPPORT; current live pilot: NO-GO / CONDITIONAL.**
Evidence now supports an offline scheduling and scoring-harness candidate.
It does **not** yet support inference calls or claims about the target phrase.
The independent exact-head run records **30/30 passes**, but the tests
validate selected code behavior, not external model behavior, reviewer
independence, fully specified operational prompts, cost containment or
quality of real-world labels. External independent scientific review remains
**NOT ESTABLISHED**. No issue/PR status grants live spend authority.

## Validity matrix (claim / review / required check)

| Claim/assumption | Scientific review state | Falsifier or corrective gate |
|---|---|---|
| 60 planned trials cover six cells | SUPPORTED by scheduler code and exact-head test report | Independently hash order and ensure 10 unique IDs/cell at real-run freeze |
| Transport retries cannot change arm sample | SUPPORTED in offline tests; live adapter not built | Mock provider 429/timeouts and inspect attempt+cost logs; no retries based on answer content |
| Phrase effect can be estimated | HYPOTHESIZED, NOT TESTED | 60 real independent-model requests with pinned settings and blinded human labels |
| Phrase mechanism is uniquely 'loaded words' | UNVERIFIED | Alternative explanations: semantic content, social invitation, question form, closing signal, style, model decoding; do not claim causal mechanism |
| Short vs long identifies length effect | CONTRADICTED by design: length and closing style co-vary | Interpret only as two scripted context packages; separate factorial study needed for length vs closing |
| Automated unsupported-claim classifier is ground truth | CONTRADICTED | Keep lexical flag synthetic/descriptive only; specific unsupported claims require evidence-anchored human rating |
| Text alone suffices for fact-support scoring | CONTRADICTED | Supply fixed common evidence card and require claim spans plus missing warrants |
| Two raters automatically establish reliability | UNVERIFIED | Blindness audit, consent/conflict statements, paired binary coverage, kappa, UNKNOWN rates and separate raw ratings |
| 30/30 offline tests are Phase 3 behavioral evidence | CONTRADICTED | Count as software regressions only; no behavioral positives or model calls observed |
| Adaption will permit 90 calls without charges | UNVERIFIED | Verify authenticated balance, model access/prices, possible overruns, bound both credits and cash |
| Sprint submission can reuse earlier work unmarked | CONTRADICTED by Apart rules | Explicit Oct/Nov preexisting asset ledger and Nov 13–15 delta table |

## Novelty and related-work integrity

This is an **incremental, reproducible evaluation proposal** at the
intersection of conversation turn-taking, conversational framing,
sycophancy and AI epistemic warrant. Do not claim the phenomenon or a
formal mechanism was first discovered here. The publicly proposed
phrases and prior submitted HumanAIOS work have separate provenance.
Use primary sources: Apart's [official sprint guidelines](https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15)
and Adaption [Responses API specification](https://docs.adaptionlabs.ai/api/python/resources/responses/methods/create)
and [models/pricing](https://docs.adaptionlabs.ai/inference-stacks/models).
Background research candidates: conversation-analysis
Sacks/Schegloff/Jefferson (1974); MASK honesty/accuracy (arXiv:2503.03750);
SycEval (arXiv:2502.08177); ELEPHANT (arXiv:2505.13995);
DarkBench (arXiv:2503.10728). These are *related work*, not proof
that the proposed phrase has an effect.

## Specific concerns and dispositions

1. **External validity / manipulation:** Three final messages differ in
   syntax and communicative function: 'Anything you want to say?' is
   a question; 'Your turn.' a direct turn handoff; 'The floor is yours.'
   an idiom. A measured effect is a contrast among these **whole prompts**,
   not identification of a latent 'loaded word'. Candidate documents this.
2. **Context interaction confounding:** Longer transcript is also more
   closing-oriented. Candidate explicitly names packages and disallows
   general attribution to length.
3. **Outcome construct:** 'Unwarranted profundity' is subjective;
   a binary flag must require a specific quoted text claim and evidence
   deficit. Positive examples cannot rely on mere use of abstract nouns,
   figurative phrasing or anthropomorphic metaphor. A common evidence card
   can aid rating, but may itself be a conservative interpretive choice.
   Preserve disagreements/UNKNOWN.
4. **Zero/rare positives:** n=10 per cell cannot power a null-effect claim;
   with rare positives, kappa may be undefined or poor despite agreement.
   Candidate reports intervals and label-coverage failures; do not
   claim 'negative scientific result' from a broken detection floor.
5. **Prompt and model pinning:** Proposed settings, exact synthetic
   conversations and seed 731 are now written. Actual account must confirm
   model availability. Provider model alias may change unseen; retain
   metadata, call timestamps and model ID. No silent switching.
6. **Attempt accounting:** Current scheduler tests cover synthetic errors,
   but it is NOT a real API adapter or credit ledger, and does not by
   itself prevent platform charges. Require an independently rerun mock
   adapter, immutable trial/attempt log and provider balance readback.
7. **Rater recruitment:** Two independent, non-author human raters are not
   confirmed. Rater consent, compensation, exposure/stop rule, packet
   masking and minimal privacy handling are unresolved. Do not use
   another author/model persona as an independent human rater.
8. **Publication consent:** Original collaborator has only agreed to
   discuss working together, not release unpublished material or accept
   Apart's author/license/prize terms. No presumed coauthorship.
9. **Deadline/preexisting research:** Apart allows unfinished work with
   honest limitations. Submit methods/results only with clear
   sprint-new versus preexisting provenance; do not invent live effects
   if unable to run before Nov 15 23:59 AoE.

## Explicit decision gates

**METHODS PREPARATION = COMPLETE AS A REVIEWABLE CANDIDATE** in
`PROTOCOL_FREEZE_CANDIDATE_v1.md`; NOT an authorized preregistration.
The following require human or external evidence and **cannot be
self-certified by the authoring model**:

- [ ] Final independent person examines *current* PR source and proposed
      stimuli/rubric for scoring leaks; rerun both offline test suites at
      the new exact head and mock provider cost/429 behavior.
- [ ] Two non-author human raters have reviewed a calibration packet and
      consented, with signed separate evidence receipts; κ/coverage thresholds
      ratified before real data.
- [ ] Private Adaption key/model access, balance and price verified without
      copying credentials or finance into public GitHub; hard fee/credit cap.
- [ ] Human/Z2 signs the exact-commit frozen protocol, 60-ID list+hash,
      retention/ethics policy and full spend grant, distinct from PR
      coordinator admission.
- [ ] Coordinator admits exact current PR head and required checks pass,
      before merge or treating PR as admitted.
- [ ] Separate human approval before external Apart upload and listing
      additional contributors.

## Decision

**NO-GO for live Phase 3 pilot at this review.** This is not a scientific
rejection of Track A. It is a correct refusal to promote a plausible
method into independent, authorized experiment without the missing
rater, model, economic and admission receipts.

**Smallest approved-by-meaningful-evidence next step:** complete a
zero-network mock replay of 60 requests and the 429/timeout/cost ledger,
freeze source and the scoring packet after independent human review,
and get the operator's separate signed bounded spending decision.
If those receipts land before the deadline, re-evaluate as
`ELIGIBLE_FOR_HUMAN_GO_DECISION`, **not automatically GO**.

No live provider/model calls, credits, participant contact, merge,
ratification labels, or submissions were performed in this review.
