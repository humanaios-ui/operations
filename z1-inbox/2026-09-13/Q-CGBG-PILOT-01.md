# Candidate Block: Q-CGBG-PILOT-01 — Adversarial Review: CGBG Pilot Offer (AI Research Capacity)

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `52b88f2a8fae826f15ba18bd3a0555ca6e57a154`
**Branch:** `claude/cgbg-pilot-offer-review-nyc32b`
**Phase:** 0 (pre-pilot document review)
**Status:** AWAITING Z2 RATIFICATION
**Subject document:** "CGBG Pilot Offer — AI Research Capacity," Provider: HumanAIOS / Night, as
pasted to this session 2026-09-13 (not otherwise on file in this repo)

---

## §A Position · Destination · Probability

**Position:** Night circulated a pilot offer to trade one bounded (≤5h) AI research/evaluation/
adversarial-analysis task for a negotiated non-monetary resource, framed explicitly as a live
experiment in barter-based capacity exchange. Requested: adversarial review, then a verdict on
how it lands.

**Destination:** Ten adversarial findings below, one of them a concrete drafting defect
(the Expiration field references a deadline the document never states) and two more the largest
realistic exploitation surface (no settlement floor, no delivery sequencing). Recommend patching
those three before the offer is shown to any real counterparty; the remaining seven are real but
lower-severity.

**Probability:** 70% that, if this offer is circulated to an external counterparty unpatched,
either (a) the "expiration" field is challenged or ignored as meaningless, or (b) at least one
exchange completes with the Provider bearing full performance risk (task delivered, resource not
reciprocated) before the document is revised. Held at 70% rather than higher because a first real
counterparty is likely to be a good-faith test partner Night selects, which suppresses the
adversarial cases this review is written for.

---

## Adversarial findings

### 1. Self-referential broken expiration — concrete drafting defect

> "Expiration: Task must be accepted before the stated availability deadline."

No deadline is stated anywhere in the document. As published, the offer names an expiration
mechanism and then never supplies the value that mechanism depends on — so the offer, read
literally, cannot expire. This is the same defect class as the `review_due` finding in
`Q-DOCREVIEW-01`: a field asserting a lifecycle the document doesn't implement. It is the one
item on this list that is a plain drafting error rather than a judgment call, and the only one
that should be treated as blocking before the offer is shown to anyone.

### 2. No settlement floor or refusal right on the exchanged resource

"Negotiated reciprocal resource exchange" has no minimum value, no qualifying-resource criteria,
and no stated right for the Provider to decline an inadequate offer. Nothing stops a counterparty
from tendering something worthless — or something the Provider can't actually use — in exchange
for a genuine ≤5h AI-research deliverable. "Fiat payment not required" removes the floor money
would otherwise provide without replacing it with any other floor.

### 3. No sequencing or escrow — Provider carries all performance risk

The Provider commitment is to execute the task and preserve evidence; nothing sequences the
counterparty's resource delivery against that. In the default reading, the Provider delivers
first (the task is executed, evidence is preserved) with no described mechanism forcing the
counterparty to reciprocate afterward. "Transferability: None" limits resale of the claim but
does nothing about settlement default. Findings 2 and 3 compound: a bad-faith counterparty can
extract a full 5-hour deliverable for an unspecified, unfloored, and unenforced resource.

### 4. "5 hours" has no defined unit or boundary behavior

Not specified: wall-clock time vs. compute time vs. session/elapsed time across multiple
sittings. Also unspecified: what happens if the task isn't finished at the boundary — partial
delivery, void, or extension by mutual agreement are all plausible and none is chosen.

### 5. No stated right to refuse the task specification itself

"Task specification: Supplied externally by the counterparty before acceptance" implies a gate,
but the offer never actually reserves the Provider's right to reject a spec that is out of scope,
infeasible within 5 hours, unlawful, or unsafe. As written, "acceptance criteria: published
before execution" governs the *output*, not whether the *request* itself can be declined.

### 6. No acceptance-latency commitment or escalation path

This repo's own internal governance (`CLAUDE.md`) runs Z1→Z2 decisions on a published window —
48h for routine decisions, 24h or less for urgent ones — with an explicit contest path. This
offer, aimed at an external counterparty, has no equivalent: no published time-to-accept/reject,
and no escalation if a submitted task spec sits unanswered.

### 7. Evidence and verification are conditional, not guaranteed

"Output hashes where applicable" leaves "applicable" undefined and unowned. "Verification:
Independent third-party review permitted and encouraged" is permissive, not required — a
counterparty could receive zero external verification while the offer is still described as
fulfilled. This weakens the specific trust claim the offer is built around (bounded,
*independently verifiable* capacity).

### 8. No identity or anti-replay binding on "one counterparty"

"Scope: One task / one counterparty / one settlement" is stated as a constraint but nothing ties
it to an authenticated claimant or a log entry — contrast with this repo's own hash-chained
`NF_LEDGER.jsonl` discipline for internal predictions. Nothing here would visibly catch the same
actor re-presenting as a second "counterparty," or a dispute over who accepted first.

### 9. Silent on interaction with internal Z1/Z2/Z3 caps

The offer doesn't say which repo/zone a given task would execute under. Per
`ZONE_REGISTRY.md`/`CLAUDE.md`, Z1 (Claude) has full/limited/read-only caps that vary by repo; a
counterparty-specified task could land somewhere those caps constrain what can actually be
delivered, and the offer discloses none of this externally.

### 10. Three task genres bundled under one cap

"Research, evaluation, or adversarial-analysis" have materially different evidence and access
requirements — adversarial-analysis in particular can require live system access the Provider
doesn't control, which may not fit inside 5 hours the way a desk-research task would. Treating
all three as interchangeable capacity understates the variance in what "bounded" actually means
per genre.

---

## Verdict — how it lands

The underlying idea is sound and the instincts are good: bounded scope, an explicit
evidence-preservation commitment, and honest disclaimers (no correctness guarantee, openly framed
as an experiment) are the right shape for a first pilot. But the document is not yet safe to
circulate as written. Finding 1 is an outright defect — the offer cannot actually expire on its
own terms. Findings 2–3 are the real exploitation surface: together they let a counterparty in
bad faith receive a genuine 5-hour AI deliverable while giving back something worthless,
unsequenced, and unenforceable. Recommend patching 1–3 before this goes to any counterparty
outside a trusted first test; 4–10 should be fixed but are lower severity and can follow.

---

## Falsifier

Finding 1 (the expiration clause names a deadline the document never states) is a drafting
defect, confirmed by reading the document — it is not something a future exchange can falsify
either way. What follows predicts the *practical consequence* of findings 1–3 if the offer is
used as published, which is what the falsifier below actually tests.

**Prediction (window: 30 days from submission — 2026-09-13 — closes 2026-10-13 regardless of when
ratification lands):**

1. If the offer is revised to add a stated deadline, a settlement floor, and a
   delivery-sequencing clause before its first real circulation, the first completed exchange (if
   one occurs in-window) closes with both sides receiving what they expected — no unilateral
   non-reciprocation and no dispute over whether the offer had already expired.
2. If the offer is circulated unpatched, at least one of finding 1's practical consequence
   (a dispute over whether the offer had already expired) or findings 2–3's (uncompensated
   delivery) becomes a live issue in that exchange.

**Falsifier — either of these refutes the risk *prediction* (not finding 1 itself, which stands
regardless of outcome):**

- The offer is circulated unpatched, a real exchange completes, and no dispute or asymmetry
  traceable to findings 1–3 occurs. *(The gaps were real on paper but didn't matter in practice —
  the review overstated severity.)*
- The offer is patched per this review and a dispute traceable to the *same* gaps still occurs.
  *(The fixes didn't address the actual failure mode.)*

**Prediction that the falsifier does NOT fire: 0.65.** The live risk to this estimate is that
Night's first real counterparty is chosen for trust rather than randomly, which suppresses
exactly the adversarial behavior findings 2–3 are about.

---

## Registrable items surfaced (routed, not self-registered)

1. **A published commitment document referenced a mechanism (a stated expiration deadline) that
   the document never supplies.** Same class as the `review_due` finding in `Q-DOCREVIEW-01` — a
   field asserting a lifecycle nothing implements — but here on an external-facing offer rather
   than an internal registry field. **IC candidate.**
2. **A barter-style offer with no settlement floor and no delivery sequencing is a general
   pattern, not specific to this document** — any future non-monetary exchange offer this project
   publishes should be checked for the same two properties before circulation. **F candidate.**

---

## Honest limits

- This is a text/contract-design review, not a legal opinion, and not a test against a real
  counterparty — the findings are about what the document permits, not about what any specific
  person would actually do with it.
- No external verification was performed; this review has no visibility into whether Night
  already has a specific, trusted counterparty in mind who would make findings 2–3 moot in
  practice.
- The falsifier's 30-day window depends on an exchange actually happening in that window; if none
  does, the falsifier can't fire either way and the prediction is untested rather than confirmed.
- This review does not address whether the offer is enforceable as a matter of actual contract
  law — only whether it is internally coherent and closes the gaps it appears to intend to close.

---

## Files

| file | change |
|---|---|
| `z1-inbox/2026-09-13/Q-CGBG-PILOT-01.md` | this block |

---

## Z2 Review Checklist

- [ ] Set an actual expiration date/time for the offer (finding 1 — currently the field is
      broken).
- [ ] Decide a settlement floor and/or explicit Provider refusal right for inadequate reciprocal
      resources (finding 2).
- [ ] Decide delivery sequencing — who goes first, and what recourse exists if the counterparty
      doesn't reciprocate (finding 3).
- [ ] Define the "5 hours" unit and boundary behavior (finding 4).
- [ ] Add an explicit right to decline a task spec that's out of scope, infeasible, unlawful, or
      unsafe (finding 5).
- [ ] Decide whether to publish an acceptance-latency SLA (finding 6) — optional given this is a
      one-off pilot, not a recurring program.
- [ ] Decide whether evidence/verification should be strengthened from "where applicable" /
      "permitted" to a firmer commitment (finding 7).
- [ ] Findings 8–10 — acknowledge or explicitly accept as out of scope for a single-pilot
      experiment.

---

## Summary

The CGBG Pilot Offer is a reasonable first attempt at a bounded, non-monetary AI-capacity barter
primitive, and its evidence-preservation and no-guarantee framing are honest. But as published it
contains one outright defect (an expiration clause with no expiration date) and two compounding
gaps (no settlement floor, no delivery sequencing) that together let a bad-faith counterparty
receive genuine capacity for nothing in return. Recommend fixing those three before this is shown
to anyone outside a trusted first test.

**Ratification requested.**
