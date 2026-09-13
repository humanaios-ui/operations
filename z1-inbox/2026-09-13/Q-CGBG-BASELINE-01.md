# Candidate Block: Q-CGBG-BASELINE-01 — Adversarial Review: CGBG-MARKET-BASELINE-001 (Evidence-Linked Market Observation v0.1)

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-09-13
**Pinned SHA:** `52b88f2a8fae826f15ba18bd3a0555ca6e57a154`
**Branch:** `claude/cgbg-pilot-offer-review-nyc32b`
**Phase:** 0 (pre-pilot document review)
**Status:** AWAITING Z2 RATIFICATION
**Subject document:** "CGBG-MARKET-BASELINE-001 — Evidence-Linked Market Observation v0.1,"
Status: Z1_PROPOSED, as pasted to this session 2026-09-13 (not otherwise on file in this repo)
**Note on redaction:** the subject document names a specific client, engagement manager, and
compensation figure. Per the subject document's own §10 ("no confidential client material is
published") and by request, this block generalizes those to **Client A**, **Engagement Manager**,
and **$X/project**; unredacted specifics were given to Night in conversation only and are not
committed here.

---

## §A Position · Destination · Probability

**Position:** This document proposes a typed-unknown evidence graph for a real freelance
engagement, intended as the "Control" against a future CGBG "Treatment" exchange (per its own
§9), and explicitly refuses to convert the observed compensation figure into a CGBG valuation
unit.

**Destination:** Seven findings below. None is as severe as the Pilot Offer's broken expiration
field, but two are real self-consistency defects (evidence-matrix conclusions outside the
document's own declared state vocabulary) and one is a live signal already present in the given
material (a content mismatch between the evidence-candidate filename and the stated engagement
description) that the document defers to a future step without flagging now.

**Probability:** 55% that, if the evidence candidate is inspected without first re-running the §7
identity-match test against the filename/description mismatch noted in finding 1, it gets
provisionally treated as belonging to this engagement by proximity rather than by a passed test —
the exact failure mode §7 exists to prevent. Held near even because the document's own discipline
(typed states, no silent promotion) is a real safeguard against this happening.

---

## Adversarial findings

### 1. The document's own identity-match test already has a visible failure signal it doesn't call out

§7 lists "project/service description" as a candidate matching attribute for confirming the
evidence candidate belongs to this engagement. The evidence candidate is filed as "US Data
Annotator Consulting Agreement (2).pdf" — a data-annotation agreement — while the engagement
itself is described as "Recruiting Paid Consultant — People Metrics, Dashboarding, Privacy &
Access Governance." That's a mismatch on the one attribute already visible in the material given,
and the document defers the identity-match test to a future inspection step without noting that
the input already contains a reason to expect that test to fail.

### 2. "$X/project" is used as a usable conclusion while its own denominator is UNKNOWN

Nothing in the document pins down what "project" means here — one deliverable, the whole
engagement, or one of several. §5 and §10 correctly forbid converting the figure into a CGBG
exchange rate, but §4's matrix still permits "observed market price" as the conclusion for a
figure whose unit is unverified. Under the document's own typed-unknown discipline, the more
honest permitted conclusion is closer to "reported figure, unit unverified" than "observed market
price."

### 3. Two Evidence Matrix rows use conclusion labels outside the document's own declared vocabulary

§2 enumerates exactly seven epistemic states (USER_REPORTED, DOCUMENT_REFERENCED,
DOCUMENT_VERIFIED, INDEPENDENTLY_CORROBORATED, CONTRADICTED, UNKNOWN, NOT_APPLICABLE). §4's
matrix then uses "NONE" and "PROHIBITED" for two rows ("CGBG settlement occurred," "$X = CGBG
valuation unit") — these are outcomes, not states from the declared type system. Same defect
class as the `review_due` finding in `Q-DOCREVIEW-01`: a schema declares a closed set of
permitted values, and the document then uses values outside it.

### 4. No preservation step for the graph's own root evidence

Every USER_REPORTED claim traces to the platform engagement record as its evidence reference, but
nothing states that record has been captured, hashed, or dated. If the source record is later
edited or removed, the root of the entire evidence graph becomes unverifiable after the fact,
with no `NF_LEDGER`-style hash-chain or timestamp the way this repo does elsewhere for
prediction/receipt events.

### 5. INDEPENDENTLY_CORROBORATED may be structurally unreachable

§10 correctly bars the Z3 who performed the work from independently verifying their own
contribution — but no third party capable of corroboration is named anywhere in the document.
Worth flagging explicitly so this state isn't silently permanent-UNKNOWN by omission rather than
by an actual attempted-and-failed corroboration.

### 6. Relation to the Pilot Offer's own gaps isn't reconciled

§9 frames this as the "Control" against a future CGBG "Treatment" exchange, but doesn't say
whether that Treatment will run under the original Pilot Offer as published or a revised one. If
the Treatment inherits the Pilot Offer's unpatched settlement-floor and sequencing gaps (see
`Q-CGBG-PILOT-01`), comparison dimensions like "perceived fairness" and "dispute frequency" risk
measuring a known, already-flagged defect rather than a genuinely fair control-vs-treatment
design.

### 7. Credit where due

§8's CGBG boundary and §11's `EVIDENCE_CANDIDATE_PENDING_RETRIEVAL` — a third state distinct from
both "missing" and "verified" — are exactly the kind of typed-unknown discipline the Pilot Offer
lacked, and directly close that document's biggest gap by refusing to let a market price silently
become a CGBG valuation unit. This document is a genuine improvement in rigor over letting a
baseline get set informally.

---

## Verdict — how it lands

Sound instinct, mostly self-consistent, and a real improvement over an informal baseline — the
refusal to convert $X/project into a CGBG unit directly closes the "no settlement floor" risk
flagged in the Pilot Offer review. But it isn't yet ready to anchor real comparison work: the
filename/description mismatch already visible in the inputs should be surfaced now rather than
left to a later inspection step, the two out-of-vocabulary matrix states should be fixed or
folded into §2's enumeration, and the "$X/project = observed market price" conclusion should be
softened to match the document's own unit-verification standard. None of these block continued
Z1_PROPOSED status, but should be resolved before this baseline is actually used as the Control in
a §9 comparison.

---

## Falsifier

**Prediction (window: 30 days from ratification, closes 2026-10-13):**

1. When the evidence candidate is actually inspected, the §7 identity-match test is run and its
   result (pass or fail) is recorded before any field is upgraded from UNKNOWN — including in the
   case where the mismatch flagged in finding 1 turns out to be immaterial.
2. No field in the matrix is upgraded past what its recorded evidence actually supports (e.g.,
   "$X/project" does not become "verified market rate" without the unit being confirmed).

**Falsifier — either of these refutes the assessment:**

- The evidence candidate is inspected and treated as matching this engagement (any field upgraded
  on that basis) without an explicit §7 match result being recorded. *(The identity-match
  discipline described in §7 was not actually followed.)*
- "$X/project" is used in a later document as a CGBG-comparable figure despite §5/§10's own
  prohibition. *(The floor this document establishes didn't hold.)*

**Prediction that the falsifier does NOT fire: 0.75.** High confidence because the document's own
drafting shows real commitment to the discipline it describes; the residual risk is process
slippage under time pressure, not a flaw in the design.

---

## Registrable items surfaced (routed, not self-registered)

1. **An evidence-state schema declared a closed set of permitted values and then used two values
   outside it** ("NONE," "PROHIBITED" where §2 defines seven specific states). Same class as the
   `review_due` finding in `Q-DOCREVIEW-01` — a declared type system with an undeclared escape
   hatch. **IC candidate.**
2. **A market-rate figure with an unverified unit was still permitted as an "observed market
   price" conclusion**, in tension with the same document's own unit-verification standard
   applied everywhere else. **F candidate**, generalizes to any future baseline that logs a
   compensation figure without pinning down what it's a rate of.

---

## Honest limits

- This is a document-design review; it does not itself perform the §7 identity-match test or
  inspect the referenced agreement — that inspection is exactly what the subject document defers,
  and this review defers it too.
- No independent verification of the underlying engagement was performed or attempted.
- The falsifier's 30-day window depends on the evidence candidate actually being inspected in
  that window; if it isn't, the falsifier can't fire either way.
- Redaction in this file (Client A / Engagement Manager / $X per project) is a presentation choice
  for this committed artifact, not a claim that the underlying specifics are themselves
  uncertain — the epistemic-state findings above apply regardless of whether the real names are
  shown.

---

## Files

| file | change |
|---|---|
| `z1-inbox/2026-09-13/Q-CGBG-BASELINE-01.md` | this block |

---

## Z2 Review Checklist

- [ ] Confirm or refute the filename/description mismatch flagged in finding 1 before any field
      tied to that evidence candidate is upgraded.
- [ ] Decide whether "NONE" and "PROHIBITED" should be added to §2's enumerated states, or the two
      matrix rows restated using the existing seven (finding 3).
- [ ] Decide whether "$X/project" should be downgraded to "reported figure, unit unverified"
      pending confirmation of what "project" denotes (finding 2).
- [ ] Decide whether the source engagement record should be captured/hashed/dated now, before it
      can be edited or removed (finding 4).
- [ ] Name (or explicitly decline to name) a third party who could ever move a claim to
      INDEPENDENTLY_CORROBORATED (finding 5).
- [ ] Decide whether the future Treatment exchange runs under the Pilot Offer as published or a
      revised version addressing `Q-CGBG-PILOT-01` (finding 6).

---

## Summary

CGBG-MARKET-BASELINE-001 is a genuine improvement over an informal baseline: its typed-unknown
discipline and explicit refusal to convert a market price into a CGBG unit directly address the
settlement-floor gap found in the Pilot Offer. Its remaining issues are a live identity-match
signal already present in the given material that the document doesn't call out, two
evidence-matrix values outside its own declared state vocabulary, and one conclusion ("observed
market price") that's more confident than its own unverified unit supports. None of these are
blocking for continued Z1_PROPOSED status, but should be resolved before this baseline anchors a
real control-vs-treatment comparison.

**Ratification requested.**
