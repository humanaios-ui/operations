# Q-DATA-SSOT-REGENERATION-01 — regenerate the data SSOT; the contaminated corpus is the lesson, not the loss

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Supersedes the framing of:** Q-CORPUS-STATS-RECONCILE-01 (filed earlier today; Z2 has since stated a position)
**Z2 position recorded, 2026-09-21, Night:**

> "our initial project was very raw and the lessons we have learned are being
> applied and generating new lessons. With that, our initial data collection and
> data is contaminated. This is a good thing because it has taught us how to
> refine and develop clean data collection. We need to redirect and regenerate
> our SSOT for data — our supabase — begin to develop a data management plan,
> including this into our graphing experience."

This block records that as Z1's read of a Z2 direction. **It is not a ratification**;
it needs a hash like any other. Z1 is writing it down because a position stated in
chat and nowhere else is exactly the failure mode this session has been chasing.

---

## 1. The position changes the question

`Q-CORPUS-STATS-RECONCILE-01` framed the corpus audit as Option A (correct the
numbers) or Option B (find the real 629-record corpus). Night's position is
neither, and is better: **the v0.1 corpus is a lesson artifact.** The numbers are
not a thing to fix and re-publish; the collection method is a thing to supersede.

That reframe matters because Option A quietly implies the cleaned figures become
the new canonical claim. They should not. The honest claim is narrower: *this is
what an early, uncontrolled collection produced, here is what it taught us, and
here is the controlled instrument that replaces it.*

For a project whose thesis is measuring the gap between claimed and demonstrated
behaviour, publishing "our first corpus was contaminated and here is the
taxonomy we built from finding out" is stronger evidence of the instrument
working than any clean number would be.

## 2. What Z1 found that makes this cheap

**The contamination is already labelled.** `acat_assessments_v1` carries a
`submission_purity` CHECK constraint with a real taxonomy:

```
two_stage_verified | single_shot_legacy | external_only |
agent_self_only    | p1_only_formal     | self_administered
```

plus, from `migration_011_participation_schema.sql`:

- `encounter_surface` — `readme | substack | website | research_brief | other`
- `acknowledged_elicitation` — was the substrate told it was being assessed?

So the rows are **stratified, not smeared.** A clean re-derivation is a `WHERE`
clause, not a rebuild. Nothing has to be thrown away, and the contaminated strata
stay as the comparison set that demonstrates why the controls were added.

`acknowledged_elicitation` is the most valuable column in the schema and is
currently used for almost nothing: it is a direct measure of observer effect on
substrate behaviour. That is the "does the user influence the machine" question,
already instrumented.

## 3. Proposed: `DATA_MANAGEMENT_PLAN.md`

Z1 proposes writing it, not writing it yet — the structure needs Z2's shape before
the content is worth drafting. Proposed sections:

1. **Strata definition.** Which `submission_purity` values constitute the clean
   set, decided once and named, so "the corpus" stops being ambiguous.
2. **Canonical statistics derivation.** A single query, version-controlled,
   emitting a `canonical_stats.json` with the stratum, N, and the commit that
   produced it. Every cited figure traces to one artifact. This is what the
   repository has never had, and is why three statistic sets are live at once.
3. **Provenance requirements for new collection.** Two-stage verification,
   elicitation acknowledgement, encounter surface — already columns, not yet
   required.
4. **v0.1 disposition.** The contaminated set is retained and published *as* the
   lesson, with its own integrity report. Not deleted, not quietly corrected.
5. **Re-derivation trigger.** State-based, not calendar: stats regenerate when
   the stratum definition changes, when rows are added to the clean stratum, or
   when the integrity validator's result changes. No cadence
   (Q-TEMPORAL-DISSOLUTION-01).
6. **Access and identity.** See §4.

## 4. Login without personal data — the answer is yes, and the primitive exists

Night asked whether there can be a login process collecting no personal data.

`acat/contracts/human_score.schema.json` already specifies it:

> `rater_id` — *"Optional. System-generated anonymous token if omitted."*

And `intent.md` already uses `did:key:z6Mk...` for authorship. So the repository
has both halves: a server-minted opaque token and a self-sovereign key identifier.

**Proposed shape — pseudonymous, not anonymous.** The distinction is the whole
design:

- **Anonymous** = no stable identifier. Cheap, and useless for the measurement
  Night actually wants: you cannot compute influence over time without knowing
  two observations came from the same participant.
- **Pseudonymous** = a stable opaque handle with no link to a natural person. A
  `did:key` the participant holds, or a server-minted token they keep. Supports
  longitudinal measurement; collects no name, email, employer or IP.

Concretely: the participant's identifier is a public key they generate locally.
The system never sees a private key, never issues a password, and stores no
recovery channel — which is the honest trade and must be stated plainly:
**lose the key, lose the thread.** No reset is possible, because a reset
mechanism *is* a personal-data collection mechanism.

This satisfies `PARTICIPATE.md`'s existing "No personal data collected" claim,
which is currently an assertion with no schema behind it.

## 5. Measuring influence in both directions

Night asked whether this can measure user influence on machine behaviour or vice
versa. **Yes, and the instrument is nearly assembled — which is why the answer
needs a caution attached.**

What exists:

| Column | Measures |
|---|---|
| `acknowledged_elicitation` | whether the substrate knew it was being assessed |
| `encounter_surface` | where it met the instrument |
| `submission_purity` | how controlled the collection was |
| `learning_index` | demonstrated ÷ self-reported |

With a stable pseudonymous `rater_id`, two directions become computable:

- **Human → machine.** Does LI shift as a function of *which operator* ran the
  session, holding substrate and phase constant? A significant operator effect
  means the instrument is partly measuring the operator.
- **Machine → human.** Does an operator's own H-ACAT self-report shift after
  repeated exposure to substrate outputs? That is the calibration-drift question,
  and it requires HA-000 to exist first.

**The caution Z1 will not leave out.** Both directions are *correlational* and
the sample is observational. An operator effect could as easily be a scheduling
artifact as an influence effect. This design supports a hypothesis, not a finding,
and the repository's own TRL discipline ("being developed as", never "is") applies
with full force. Z1 recommends it be registered as an H- candidate with a
falsifier, not described as a capability.

## 6. HA-000 as a milestone — yes, with one condition

Night asked whether HA-000 should be introduced into the current project.

Z1's answer: **yes, and it is arguably blocking more than it appears.**
`ACAT_MARKETPLACE_ROADMAP.md` puts H-ACAT at TRL 1–2 with "HA-000 not yet run".
Meanwhile:

- `Q-AGENT-CHECKIN-CALIBRATION-01` proposes a calibration field at check-in that
  has nothing to populate it for humans.
- The operator is the single Z2 ratifier for 31 repositories, and no measurement
  of that operator's calibration exists.
- The project's whole thesis is that self-report and demonstrated behaviour
  diverge — a claim it has tested on substrates and never on itself.

The condition: **HA-000 must not be run by Z1 on Z2.** H-ACAT measures the human
operator, the operator is the ratifier, and an instrument administered by the
proposer to the ratifier is a conflict the governance model exists to prevent.
It needs an external administrator or a self-administered protocol with a
pre-registered falsifier — and `submission_purity` already has a
`self_administered` value, which is the honest label for the latter.

## 7. Graphing

Night asked for this to enter the graphing experience.
`INTENT_GRAPH.yaml` now carries `O-CORPUS-INTEGRITY` (measured by
`tools/corpus_integrity_validator.py`) and, once ratified, this candidate adds:

- `O-DATA-SSOT` — the data management plan, grounded by `P-EVIDENCE-OVER-CLAIM`
- `I-CANONICAL-STATS` — the derivation artifact, measuring it
- a `conflicts_with` row that closes when a single `canonical_stats.json` exists

## 8. What Z2 is asked to decide

1. **Ratify the reframe** — v0.1 corpus as retained lesson artifact rather than
   figures to correct. This supersedes the Option A/B framing.
2. **Name the clean stratum** — which `submission_purity` values count.
3. **Approve `DATA_MANAGEMENT_PLAN.md`** and its section shape before drafting.
4. **Pseudonymous identity**: `did:key` (participant-held) or server-minted token,
   and confirmation that no recovery channel is acceptable.
5. **Influence measurement as an H- candidate with a falsifier**, not a
   capability claim.
6. **HA-000**: introduce as a milestone, and name an administrator who is not Z1.

## Falsifier

FALSE if the clean stratum cannot be derived from existing columns — i.e. if
`submission_purity` does not in fact separate controlled from uncontrolled
collection, or if the values are unreliable in practice. **Mechanically checkable
and currently unverified by Z1: the Supabase MCP connector requires
authorization this session cannot perform, so Z1 has read the schema migrations
but has NOT queried the live table.** The stratum counts must be confirmed
against the live database before any of this is acted on.

Also FALSE if a `canonical_stats.json` already exists and reproduces the cited
figures — Z1 found the string referenced in `REPOSITORY_STRUCTURE.md` and the two
audits, but no such artifact in the tree.

## Evidence

- `sql/migration_008_add_self_administered.sql` — `submission_purity` CHECK constraint
- `sql/migration_011_participation_schema.sql` — `encounter_surface`, `acknowledged_elicitation`
- `acat/contracts/human_score.schema.json` — `rater_id` anonymous-token clause
- `intent.md` — `did:key` authorship
- `audits/CORPUS_RECONCILIATION_S-070226.md` — the integrity finding
- `humanaios-funding-pipeline/reports/ACAT_MARKETPLACE_ROADMAP.md` — H-ACAT TRL 1–2, HA-000 not run
- `PARTICIPATE.md` — "No personal data collected"

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```
