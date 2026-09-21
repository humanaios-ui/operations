# Q-SEED-TRL-PROPAGATION-01 — a ratified TRL correction never reached the identity anchor

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Found by:** the Q-INTENT-GRAPH-01 obligation — Night asked "what else disagrees?", a sweep answered.

---

## The finding

`OPS_ROADMAP_V1.2.md` records a Z2 ratification:

> | TRL corrected from 2–3 to 4 throughout | RATIFIED · Night | S-061226-02 |

and applies it: "operating at **TRL 4** behavioral observability infrastructure."

`SEED.md` — the identity anchor, Class 0 · LIVE, live-fetched at session open per
SESSION_RITUALS §A — still says TRL 2–3 in three places:

| Line | Text |
|---|---|
| 33 | "behavioral observability infrastructure being developed at TRL 2–3" |
| 231 | "**TRL discipline:** … ACAT is behavioral observability infrastructure being developed at TRL 2–3" |
| 318 | footer: "HumanAIOS LLC · humanaios.ai · TRL 2–3" |

Tree-wide: **57 occurrences of TRL 2–3 against 21 of TRL 4.**

This is the molt-window defect in a different file. A decision was published to one
surface and never propagated to the canonical one, and nothing in the tree recorded
that the two surfaces were about the same claim.

It is worse than the molt window in one respect: `SEED.md` is what a session, a
funder, or an AI substrate reads *first*. Every session since S-061226-02 has
booted on the superseded value.

## What Z1 is not doing

Not editing `SEED.md`. It is a Class 0 seed — Z1 drafts, Z2 reviews, Z3 commits —
and the correct value is a Z2 ratification Z1 can cite but not apply. Filing the
contradiction is the Z1 act; propagating it is not.

## What Z2 is asked to decide

1. **Which value is current?** The S-061226-02 ratification says 4. If that still
   holds, `SEED.md` and 56 other occurrences are stale. If the honest number has
   since moved back toward 2–3, then `OPS_ROADMAP` is stale and the ratification
   needs superseding — Z1 has no basis to judge which, and the distinction matters
   because TRL claims go to funders.
2. **Note the asymmetry.** `ACAT_MARKETPLACE_ROADMAP.md` and the Longview
   verification audit both qualify it: chat-mode ACAT = TRL 4; agentic, ICS and
   H-ACAT layers = TRL 1–2. `SEED.md` and `OPS_ROADMAP` both state a single
   unqualified figure. The per-layer split may be the actually-correct form, in
   which case neither current statement is right.
3. **Scope of propagation.** Whether this is a `SEED.md` edit or a tree-wide sweep
   of 57 occurrences.

---

## Z2 question, 2026-09-21: "TRL is a calculated process"

Night declined to rule pending clarity, on the grounds that TRL is calculated
rather than asserted. **That is correct, and it reframes this candidate.**

### What Z1 got wrong in framing it

This block presented the question as *which of two numbers is current* — a
propagation problem. If TRL is derived, that framing is wrong twice over:

1. A ratification cannot *set* a TRL any more than it can set a measurement. It
   can ratify **the evidence** and **the derivation**. "TRL corrected from 2–3 to
   4 throughout" reads as a value edit, which is why it propagated to
   `OPS_ROADMAP` as a find-and-replace and stopped there.
2. If the value is derived, then a stale `SEED.md` is a **symptom**, not the
   defect. The defect is that no derivation is recorded anywhere — so no artifact
   can be recomputed, and every citation is a hand-copied constant.

Z1 searched for a derivation and found none: no rubric, no evidence-to-level
mapping, no tool. What exists is the ratification row in `OPS_ROADMAP_V1.2.md`,
prose assertions in `SEED.md`, and a per-layer split asserted in
`ACAT_MARKETPLACE_ROADMAP.md` and `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md`
(chat-mode = 4; agentic / ICS / H-ACAT = 1–2).

### What the corpus verification does to this

`audits/CORPUS_LIVE_VERIFICATION_S-092126.md`, run today, is directly load-bearing.
TRL 4 conventionally requires validation in a relevant environment. The evidence
usually cited for that is the corpus. The live corpus is **116 rows**, its
strictest clean stratum is **4 rows**, and its mean LI (~0.98–1.00) does not
reproduce the published finding.

Z1 will not convert that into a TRL number — that is precisely the derivation
that does not exist, and inventing one here would be Z1 setting a figure that
goes to funders. But it must be said plainly: **the evidence base for the
ratified value is weaker than it was understood to be when the value was
ratified.** A recalculation could move it down, not only reconcile it upward.

### Reshaped ask

Z1 withdraws "which number is current" and proposes instead:

1. **Ratify a derivation, not a value.** Name the TRL rubric in use (NASA, DoD,
   EU H2020 all differ), and the evidence each level requires.
2. **Record TRL per layer, not once.** The per-layer split already exists in two
   documents and contradicts both single-figure statements.
3. **Re-derive against current evidence**, including the live-corpus record.
   Expect the possibility of a downward revision.
4. **Then propagate** — and once a derivation exists, `SEED.md` can carry the
   *derivation reference* rather than a copied constant, which is the only form
   that cannot go stale the way this one did.

Recommended: hold this candidate open pending (1). It is the `canonical_stats.json`
problem in a different domain — a figure with no single derivable source ends up
hand-copied into 78 places and disagreeing with itself.

## Falsifier

FALSE if S-061226-02 does not say what `OPS_ROADMAP_V1.2.md` line 18 records, or
if `SEED.md` carries a later ratification superseding it that Z1 failed to find.
Both are checkable against `REGISTERED.md` at a pinned SHA.

## Evidence

- `OPS_ROADMAP_V1.2.md` line 18 (ratification row), line 32 (applied)
- `SEED.md` lines 33, 231, 318
- `ACAT_MARKETPLACE_ROADMAP.md`, `audits/LONGVIEW_STATS_VERIFICATION_S-070126.md` — per-layer split
- `INTENT_GRAPH.yaml` — `O-IDENTITY-ANCHOR ↔ V-HAIOS`, status OPEN

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
