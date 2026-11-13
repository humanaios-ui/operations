# Proposed experiment: evidence accuracy, human decision burden, correction rate (v0.1)

**Status: PROPOSED. NOT FROZEN. NOT RUN.** Authority effect NONE. Freezing means hashing this file, the code and the analysis script **before** any data are collected; until a human signs off, nothing here is a preregistration. A local freeze is not external preregistration.

## Why
The token-attractor pilot ([negative result](TOKEN_ATTRACTOR_NEGATIVE_RESULT.md)) asked whether a smarter *search* helps. It did not, and its rating was model-only and tiny. The open question that matters to a person deciding is different: **when an AI hands a human a lead, is the evidence on it accurate, how much work does the decision cost, and how often does the human have to correct it?**

## Question
Does a lead presented with a verified provenance card (claim, source link, evidence state, requirement flags, explicit unknowns) produce more accurate human decisions, at lower decision burden and with fewer later corrections, than the same lead presented as a plain title-and-snippet list from the existing matcher?

## Arms (randomized by lead, not by person)
- **C (control):** existing plain-word matcher output as it is today: title, snippet, source link.
- **P (provenance):** the same lead plus a card: each claim tied to a quoted source span and a state (DOCUMENTED / USER_ATTESTED / IN_PROGRESS / UNKNOWN), requirement flags, and the questions still open. No concept expansion, no transfer hypotheses.

## Units and sample
- Unit: one lead. Draw at least 60 leads from a **fresh** corpus slice not used in the pilot, fixed by a seeded draw recorded before any card is built. 30 per arm after seeded randomization; add 8 planted false leads (4 per arm) with known defects.
- Decision-maker: the owner for personal leads; for generality, two additional reviewers on a shared subset of 20 leads to estimate agreement. Reviewers are blind to arm only as far as the interface allows; state this limit in the report.

## Measures (all defined before data)
1. **Evidence accuracy (primary).** For every claim shown, a verifier who did not build the card checks it against the primary source: CONFIRMED / WRONG / NOT_CHECKABLE. Primary statistic: share of claims CONFIRMED among checkable claims, per arm. Also report planted-defect detection rate.
2. **Human decision burden.** Time to a decision (timer started on open, stopped on decision), number of primary-source opens, and share of leads deferred ("need more information"). Report medians and interquartile ranges.
3. **Correction rate.** Share of first decisions the same person reverses or amends after a fixed re-review pass, plus share of card fields a human edits. Re-review happens after a fixed number of other decisions, not after a calendar interval.

## Analysis plan (fixed before data)
- Per-lead comparison between arms: difference in proportions with an exact or bootstrap 95% interval for accuracy and correction rate; Mann-Whitney for time. No p-value thresholds are used to declare success.
- Smallest effect worth acting on, stated in advance: a 10 percentage-point gain in claim accuracy, or a 25% cut in median decision time, with correction rate not worse. Anything smaller is reported as "not shown".
- Planted false leads are excluded from accuracy and burden statistics and used only as a detection check.
- All outcomes are reported, including nulls and reversals. No post hoc subgroup, threshold or rubric change after unblinding; any such change is a new experiment.

## Independence and controls
- Verifier and card builder are different agents; at least one verifier is human. If a model is used as an additional rater it must be from a different family than the builder, and its ratings are labelled model ratings.
- A hold-out: the card builder and rubric are frozen (hash recorded) before the fresh slice is drawn.
- Test-retest: 10% of leads are shown twice; disagreement is reported.

## Falsifiers (any one ends the claim)
- Claim accuracy in P is not above C by the stated margin.
- Median decision time in P exceeds C by more than 10%.
- Correction rate in P is higher than in C.
- A planted false lead is accepted as supported in P more often than in C.
- Verifier agreement on CONFIRMED/WRONG is below 0.7 (kappa), which would void the primary measure.

## Resource accounting
Report labor in people-hours and model usage in tokens per arm; do not schedule by calendar. A larger burden that buys fewer corrections is a trade-off to be stated, not hidden.

## Out of scope
Search quality, concept expansion, transfer hypotheses, eligibility determination, and any external contact or submission.

## Human decisions needed before freezing
Who the verifiers are; the fresh corpus slice; whether the owner is an acceptable single decision-maker for the primary comparison; the effect sizes above.
