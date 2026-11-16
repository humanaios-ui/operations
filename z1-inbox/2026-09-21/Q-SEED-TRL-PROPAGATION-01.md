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

---

## Z2 Ruling

**Decision:** ACCEPT, on the reshaped ask only — stated by Night (Z2/Admiral) in
session, 2026-09-21: *"ratify trl derivation."*
**Recorded by:** Claude (Z1), as transcription. Z1 did not make this call.
**Signature:** none on this file, and the merge does not create one.

### What was accepted, precisely

Night's earlier response was *"I need more clarity to help with that decision
because my understanding is that TRL is a calculated process."* That observation
is what reshaped this candidate, and the ACCEPT lands on the reshaped form:

**Accepted** — item 1 of the reshaped ask. A derivation is to be ratified, not a
value. Name the rubric in use, and the evidence each level requires.

**Not decided here** — items 2, 3 and 4 remain open, and deliberately:

- **Per-layer recording** follows from the derivation rather than preceding it. A
  rubric that yields one figure and a rubric that yields a figure per layer are
  different rubrics, so item 2 is answered by item 1's choice, not alongside it.
- **Re-derivation against current evidence** cannot run before the rubric exists.
  `audits/CORPUS_LIVE_VERIFICATION_S-092126.md` measured the live corpus at 116
  rows, strictest clean stratum 4, `acknowledged_elicitation = true` in zero rows
  in every stratum. A recalculation may move the figure **down**. That was stated
  before the ACCEPT and is restated here so the ratification cannot later be read
  as endorsing the existing value.
- **Propagation** is last by construction. Once a derivation exists, `SEED.md`
  carries a *derivation reference* rather than a copied constant — which is the
  only form that cannot go stale the way 57 occurrences of "TRL 2–3" did.

### Why this ruling changes the shape of the finding

The original candidate reported a propagation failure: a ratified value reached
`OPS_ROADMAP_V1.2.md` and never reached `SEED.md`. Night's observation reclassifies
it. If TRL is calculated, then a ratification cannot set it any more than it can
set a measurement, and "TRL corrected from 2–3 to 4 throughout" was a value edit
standing in for a derivation that was never recorded. The stale `SEED.md` is a
symptom. **The defect is that no artifact can recompute the number**, which is why
every citation of it is hand-copied — the `canonical_stats.json` problem in a
different domain.

Accepting a derivation rather than a value is therefore not a narrower ruling
than the one originally asked for. It is the only one that closes the class.

### What Z1 does next, and does not

Does not: select a rubric, compute a TRL, edit `SEED.md`, or touch any of the 57
occurrences. A TRL figure goes to funders, and Z1 choosing the rubric that
produces it would be Z1 setting the figure by the back door — the same objection
that kept Z1 from selecting Option A in `Q-CORPUS-STATS-RECONCILE-01`.

Does: on Z2 naming the rubric, build the derivation as a tool with the evidence
mapping as data, so the figure is recomputable and `SEED.md` can reference it.

### Mechanism

```
python3 .z1-control/ratify.py Q-SEED-TRL-PROPAGATION-01 --decision ACCEPT --by Night --apply
```

computes `sha256(candidate | by | at | decision)` over the file's bytes, writes
the dated ruling file, and updates `z1-inbox/INDEX.yaml` to a terminal status —
the three things `.z1-control/validate.py` requires and that a merge does not
supply. Run it **after this PR merges**, so the hash covers the final bytes
including this section.

Z1 does not run it: the tool's own docstring says "Run by Z2, not by Z1", because
Z1 writing the ruling file, computing the hash and setting the status in one pass
would satisfy every check while proving nothing.

Single-member override applies: with one board member, Night reviews, approves
and merges her own ruling PR, recorded as an override per that ruling's `review`
row.

---

## Options

- `ratify 1`
- `edit`
- `reject`
- `later`

The number is item 1 of the reshaped ask ("Ratify a derivation, not a value"). Items 2, 3 and 4 of the reshaped ask are not offered as separate choices, because this block says they follow from item 1: per-layer recording is answered by the rubric chosen, re-derivation cannot run before a rubric exists, and propagation comes last.

## What each sets in motion

- `ratify 1`: the direction is ratified. TRL is treated as derived, not set. A derivation, meaning a named rubric and the evidence each level requires, is to be ratified before any TRL value is propagated again. It does **not** name the rubric; that stays Night's. It does **not** confirm or revoke the existing "TRL 4 throughout" row or the per-layer split. It changes no file except this one: `SEED.md` still says TRL 2-3 and `OPS_ROADMAP_V1.2.md` still says TRL 4, and the many other occurrences are untouched. Z1 builds nothing until a rubric is named; on that naming, Z1 builds the derivation as a tool with the evidence mapping as data. Assigning a registry entry in `REGISTERED.md` is a Z2 act; Z1 does not write that file.
- Not asked here, and left open: what `SEED.md` and funder-facing text say in the meantime, and whether the existing "TRL 4 throughout" row stays in force until a derivation exists. Each would need its own block.
- `edit`: Z1 revises the block and files it again.
- `reject`: the block closes with its bytes signed and the reason Night records. Nothing is entered in `REGISTERED.md`.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Checked on 2026-11-16 (not carried from the block above)

- **Unchanged since the block:** `OPS_ROADMAP_V1.2.md` line 18 still reads "TRL corrected from 2-3 to 4 throughout | RATIFIED · Night | S-061226-02", and `SEED.md` lines 33, 231 and 318 still say TRL 2-3. Those are the only three TRL statements in `SEED.md`, and none refers to a later ratification.
- **The ratification the block cites is not in `REGISTERED.md`.** The block's falsifier says to check `S-061226-02` against `REGISTERED.md`. That id does not appear there at all. The row is restated in `OPS_ROADMAP_V1.2.md`, `MARKET_HARMONIC_RESEARCH_PRINCIPLE_SEED.md` and `INTENT_GRAPH.yaml` (which quotes the roadmap). Z1 did not look outside the tree, such as session logs, so this does not show the ratification did not happen. It shows the tree cannot confirm it.
- **Two sessions are cited, with ids a day apart.** The per-layer split (chat-mode ACAT TRL 4; agentic, ICS and H-ACAT TRL 1-2) is cited to `S-061126-02` ("canvas") in `ACAT_MARKETPLACE_ROADMAP.md` and in the Longview verification audit. The single figure ("TRL 4 throughout") is cited to `S-061226-02`. `S-061126-02` appears once in `REGISTERED.md`, in an unrelated note about a "4 days to Charter close" error. From the tree alone, Z1 cannot tell whether the later row was meant to replace the earlier split.
- **Occurrence counts are not comparable to the block's.** The block says 57 occurrences of TRL 2-3 against 21 of TRL 4 and does not state how it counted. Z1's count today is 114 matching lines for "TRL 2-3" against 32 for "TRL 4" (outside `z1-inbox/` and `audits/`: 100 lines in 54 files against 25 lines). Z1 cannot say whether the gap moved.
- **No reproducible derivation exists.** There is no tool, no named rubric, and no evidence threshold per level in the tree. The only tracked file whose name mentions TRL is this block. A partial, prose mapping does exist: `humanaios-funding-pipeline/reports/ACAT_MARKETPLACE_ROADMAP.md` section 2.1 pairs nine assets with an evidence base and a TRL level each (for example chat-mode ACAT, N=604 published plus N=95 live, TRL 4; human operator calibration, "HA-000 not yet executed", TRL 1-2). That table is not a derivation. Its "N=95 live" is not the 116 rows the 2026-09-21 audit measured, and Z1 did not work out why. A derivation should assess it, not overlook it.
- **Not re-checked:** the live-corpus figures (116 rows, 4 in the strictest clean stratum) are from 2026-09-21; Z1 did not query the database today.

## Note on the "Z2 Ruling" section above

That section transcribes what Night said in session on 2026-09-21 ("ratify trl derivation"). It carries no signature, and `INDEX.yaml` still reads `awaiting_z2`, so the `.z1-control/ratify.py` step was not completed for this block. It also says the merge ratifies nothing, because the file then had no `## Ruling` section. This file now has one, in the shape `tools/decision_relay.py` writes. Under the 2026-09-18 ruling, the merge of the pull request that fills it is the ratification, and the `ratify.py` command in that section is not needed. Z1 left the earlier text unchanged. It does not count as a ruling, and nothing here treats it as one.

## Ruling

choice: ratify 1
by: Z1-prepared (not an identity claim)
at: 2026-11-16T14:51:09Z
status: DECIDED
block_hash: eb8385cb456f2df0486701201fdf19f1b1210bde09ef96cadbfdfd359efea656
body_hash: fd9272863bf30326453e1fd564b62f5be51a25f9fbefbd2a01052a87042ff250

```
RULING z1-seedtrl-01
  by: Z1-prepared (not an identity claim) (tagline)
  project: humanaios
  question: Ratify item 1 of the reshaped ask of Q-SEED-TRL-PROPAGATION-01: treat TRL as derived, and ratify a derivation (a named rubric and per-level evidence) before any TRL value is propagated again; the rubric is not named here and no existing TRL value is confirmed or revoked?
  choice: ratify 1
  note: 
  at: 2026-11-16T14:51:09Z
  status: DECIDED
```

