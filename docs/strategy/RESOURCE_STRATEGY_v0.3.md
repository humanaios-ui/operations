# RESOURCE_STRATEGY_v0_3

Status: BUILT (Z1) per Z2 scope ratification of 2026-08-29 → awaiting Z2 hash → Z3 lands
Supersedes v0_2 (2f3134b8…). Red-team disposition applied: 13 accept, 1 contest (§6 ERAP evidence grade), 1 accept-with-modification (§8).

## Objective (restated)
Maximize measurable institutional capacity acquired at zero or near-zero cash cost, per founder-hour, subject to mission, governance, legal, security, and entity-separation constraints. Resources are a byproduct of research engagements, not the purpose of the program.

## Resource classes
A labor · B compute · C data · D expertise · E infrastructure · F institutional validation · G distribution · H capital-equivalent credits

## Pipeline stages (ledger field `stage`)
DISCOVERED → ELIGIBILITY_CHECKED → TERMS_CHECKED → ENTITY_CHECKED → MISSION_CHECKED → SCORED → APPLIED → AWARDED | REJECTED → REALIZED → RENEWED | TERMINATED. BLOCKED is a parking state with `blocked_on`.

## Ledger
`resource_ledger_v0_1.jsonl`, one row per opportunity. Required fields: entity · beneficiary · resource_class · nominal_value_usd · realizable_value_usd · founder_hours · expiry_months · billing_exposure · obligations · artifact_output · stage · prior_P · calibration_status · unblocks · evidence_grade · last_read.
Rules: `realizable_value_usd` stays null until REALIZED; `prior_P` is never written as `P`; `calibration_status` flips to CALIBRATED only when an outcome resolves in NF_LEDGER.

## Gate (code: resource_gate.py v0.1)
Ten conditions, all must pass for APPLY: eligibility plausible · identifiable use · founder_hours ≤ 40 · entity in the three · obligations declared · expiry ≤ 24 mo or none · entity == beneficiary (no benefit transfer) · expiry declared · billing exposure declared · artifact measurable.
Score = (nominal_value × prior_P + Σ nominal×prior of what it unblocks) ÷ founder_hours. Code emits the verdict.

## Re-run result (resource_gate.py on ledger sha 51725724…)
| rank | id | move | verdict | score /founder-hr |
|---|---|---|---|---|
| 1 | R-003 | Cloudflare entry tier (GRBS) | APPLY | 7000 |
| 2 | R-004 | AWS Activate Founders (GRBS) | APPLY | 1400 |
| 3 | R-001 | capstone/clinic letters (HumanAIOS) | APPLY | 448 |
| 4 | R-002 | Anthropic ERAP (HumanAIOS) | APPLY | 83 |
| — | R-005 | nonprofit pool (RecoveryPlatform) | DO_NOT_APPLY | 0 (blocked: entity) |

Finding: the founder-hour denominator reorders the first day. Self-serve credits (≈1.5 h total) go first; letters second; ERAP fourth on value-per-hour but keeps its window (≤ 2026-09-04). Order of *unblocking* is unchanged — R-001 still feeds R-002. The re-ranking is reported as the function's output, not adopted by judgment.

## Falsifier (strategy-level, DERIVED)
Trips on 2026-12-31 unless all three hold: ≥1 external institutional relationship AND ≥1 measurable resource transfer (any class A–H) AND ≥1 independently generated artifact. Trip → mechanical REVERT, F/IC candidate.

## Operating hypothesis (H-candidate, needs falsifier_lint before registry)
H: a small research program can convert underutilized institutional capacity into independently verifiable research capacity without cash. Falsifier: if after two semester cycles no institution has produced an artifact that survives an external read, H is false.

## Callouts
- VOID: class F (institutional validation) has no price in the score. R-001's $15K nominal is a labor proxy only; the validation value is unmeasured and the score understates it.
- VOID: R-003/R-004 terms (tier sizes, expiry, payment method) are REPORTED via red-team, not fetched. Verify before APPLIED.
- GAP: location unknown to Z1; regional clinics unmatched.
- IC candidate: v0_2 prose said "priors," ledger block wrote `P = 0.70`. Discipline stated, not enforced. Same class as F-45. Mitigated in v0_3 by the `prior_P` field name and gate check.
- Open: nonprofit formation as queue item; retired-model baseline for substrate_canary. Neither in this hash.

## Out of scope for this hash
Letter drafts, application text, queue_items.json entries.
