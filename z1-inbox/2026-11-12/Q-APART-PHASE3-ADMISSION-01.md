# Candidate Block: Q-APART-PHASE3-ADMISSION-01 — budget/reviewer/ethics admission for Apart Phase 3 loaded-phrase pilot

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-12
**Status:** ADMISSION_REQUESTED (not approved for execution)
**Authority Required:** Z2 (Night) admission of budget, reviewer, and ethics controls before any live model call. Separate from, and in addition to, PR #1210's repository-coordinator admission (already granted, `ADMIT` at head `2359e240bbcb641fd92e2d6c96b19033ea70e60f`) and the Track A/B scope decision (already resolved — Track A primary, Nov 12 2026, per #1200's decision register). No implementation is approved by this candidate alone.
**Carrier:** PR #1210 (`research/apart_phase3_epistemics/`), specifically `PROTOCOL_DRAFT_v0.md` §§3.2, 3.3, 7. This file consolidates those sections into one decision packet; it changes no code and proposes no file edit.

```yaml
candidate_id: "Q-APART-PHASE3-ADMISSION-01"
title: "Admit budget, reviewer, and ethics controls for the Apart Phase 3 loaded-phrase pilot (Track A)"
author: "Z1 (Claude)"
proposed_at: "2026-11-12T00:00:00Z"
scope:
  - "research/apart_phase3_epistemics/PROTOCOL_DRAFT_v0.md (no file change proposed; this candidate requests sign-off on content already there)"
  - "this candidate and its index row"
resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 15
    CI-min: 0
  dependencies:
    - "#1200 (tracker)"
    - "#1114 (cumulative Apart log)"
    - "PR #1210 (carrier, draft protocol + synthetic harness)"
  blocking_on:
    - "originator's consent/attribution — separate decision, not resolved by this candidate"
    - "sprint survey/eligibility status — separate decision, not resolved by this candidate"
impact_prediction:
  resource_impact: 2
  areas_affected: ["research/apart_phase3_epistemics/", "Apart Nov 13-15 sprint submission"]
  positive_outcomes:
    - "One decision packet instead of three scattered checklists (#1200, #1114, PR #1210 review threads) for Night to act on."
  risk_factors:
    - "Dual-use flag (a phrase that reliably elicits unsupported authority/approval claims is also a usable primer against deployed agents) is named, not resolved, by this candidate."
    - "ACCEPT here still does not authorize a live call on its own — the two blocking items above remain separate."
```

## Claim

- **claim:** three independent controls — budget, reviewer, ethics — are each specified to the degree `PROTOCOL_DRAFT_v0.md` currently defines them, and each has a named gap Night would need to close or explicitly accept before a live call. This candidate asks for Night's decision on each **independently**, not as one bundled accept/reject.
- **why the existing checklist line doesn't resolve this:** the Nov 12 #1114 comment lists "Z2: admit bounded protocol, budget, reviewer/ethics controls" as a single bullet. Collapsing three independent decisions under one line is the same failure class REGISTERED.md already names for Z2-CORPUS-TRUST-01 (2026-06-06): a bundled gate blocks items that do not need to wait on each other. Budget, reviewer, and ethics are independent questions; a decision on one does not need to wait on the others.
- **evidence_tier:** every "already specified" line below cites the exact `PROTOCOL_DRAFT_v0.md` section; every "still missing" line names what is absent, not a guess at what Night might separately want.
- **not claimed:** that this candidate authorizes a live call, that the originator has consented, that sprint eligibility is confirmed, or that PR #1210's repository-coordinator admission substitutes for any of this.

## Z2 decisions needed (accept, edit, or reject — independently; each is its own decision)

1. **Budget.** `PROTOCOL_DRAFT_v0.md` §3.2 fixes a retry policy (2 retries on HTTP 429/timeout, 0 retries on content) and a 90-call attempt ceiling for the 60-response pilot. Not fixed: which provider/model runs it (Adaption's Responses API is the only concrete option floated so far, per the Nov 12 #1114 comment, keyed via a private `ADAPTION_API_KEY` secret), a per-call/token dollar cost, or a total dollar ceiling. **Decision needed:** name the provider/model and a dollar ceiling, or reject/defer the pilot on budget grounds.
2. **Reviewer.** §3.3 fixes two blinded raters, a masking/redaction procedure (`[PHRASE]`/`[CONTEXT]` redaction before a rater sees text, random response IDs), retained — not majority-voted — disagreements, and *proposes* (does not adopt) AERC's κ ≥ 0.65 pre-pilot gate. Not fixed: who the two raters are, a training/calibration step, consent, compensation, a content-warning/stop rule, and confirmation neither is a coauthor (role-separation table, #1200). **Decision needed:** name or approve the raters and the welfare terms, and confirm or set the kappa threshold.
3. **Ethics.** §7 names, but does not yet write policy text for: a dual-use attack-phrase disclosure policy, a private-draft-transcript leakage check (the originator's October drafts are explicitly not to be shared, per #1200), and ties to a no-mental-state-inference clause already drafted in §1. The sprint's own mandatory Limitations & Dual-Use appendix is a separate downstream submission requirement, not this candidate. **Decision needed:** accept §7 as sufficient scaffolding to proceed to drafting that policy text, or specify what must exist first.

## Falsifier

This candidate's consolidation is FALSE — incomplete, not merely imperfect — if any of the following is observed:

1. A requirement present in #1200's acceptance criteria, the #1114 Nov 12 comment, or PR #1210's review threads (read-only code inspection, GitHub Copilot, CodeRabbit, empirica-autonomy) is absent from all three decision items above.
2. This document, once any item is ACCEPTed, is treated as authorizing a live model call without the separately-blocking originator-consent and sprint-eligibility items also being resolved.
3. Budget, reviewer, and ethics end up ratified as one bundled decision rather than three independent ones — the failure class this candidate exists to avoid.

## Z2 Decision Gate

- [ ] Budget — ACCEPT (name provider/model + dollar ceiling), EDIT, or REJECT/DEFER
- [ ] Reviewer — ACCEPT (name raters + welfare terms + kappa threshold), EDIT, or REJECT/DEFER
- [ ] Ethics — ACCEPT §7 scaffolding as sufficient, EDIT (specify required text/checks first), or REJECT/DEFER

Z1 signs none of these. Signing:

```
python3 .z1-control/ratify.py Q-APART-PHASE3-ADMISSION-01 --decision ACCEPT --by Night --apply
python3 .z1-control/ratify.py Q-APART-PHASE3-ADMISSION-01 --decision EDIT --by Night --apply
python3 .z1-control/ratify.py Q-APART-PHASE3-ADMISSION-01 --decision REJECT --by Night --apply
```
