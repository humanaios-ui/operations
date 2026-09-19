---
addendum_to: "humanaios-triage-finding SKILL.md"
status: Z1 DRAFT — not ratified, not wired in
proposed: continuation of S-071126-01
pattern_source: "timing_audit_v1_0.py + lessons_learned_ledger.json — same
  recursive design, applied to the 7-question triage gate instead of the
  4-question timing audit"
---

# Addendum: Triage Lessons Ledger (recursive hardening)

## Why

`timing_audit_v1_0.py` already proved the pattern this session: an audit
that consults a ledger before recommending, then writes new lessons back,
so the next run inherits what the last one learned. `humanaios-triage-
finding` has no such memory — Q1 through Q7 are re-derived from scratch
on every candidate, even when this exact failure shape has already been
seen and named.

This session alone produced at least three lessons the gate should have
been able to consult rather than re-discover:

```json
{
  "ledger_version": "1.0",
  "purpose": "Accumulated triage-gate lessons. Each humanaios-triage-finding
    run MUST consult this ledger at Q1 (corpus quality) and Q5 (duplicate
    check), and MUST append any new lesson it discovers.",
  "lessons": [
    {
      "id": "T1",
      "discovered_in": "S-071126-01, Grok document assessment",
      "constraint": "vocabulary_fluency_is_not_evidential_tier",
      "rule": "Correct, fluent use of this project's own F-/H-/D- vocabulary
        by an external or relayed source is not itself evidence the
        reasoning underneath is sound. Check for the specific failure
        shape F-51/F-57 already named (fabricated statistics, false
        VERIFIED tags) as a targeted test, not a general vibe check.",
      "applies_to_gate": "Q1 (corpus quality), Q5 (duplicate check)"
    },
    {
      "id": "T2",
      "discovered_in": "S-071126-01, Grok document assessment",
      "constraint": "relayed_reasoning_on_verified_sources_stays_reported_tier",
      "rule": "A document citing real, independently-verifiable papers is
        not thereby promoted to VERIFIED tier itself. The citation chain
        being real does not make the relayed reasoning built on top of it
        real. Only the cited source is VERIFIED; the relaying document's
        own claims remain REPORTED/JUDGMENT until independently checked.",
      "applies_to_gate": "Q1 (corpus quality)"
    },
    {
      "id": "T3",
      "discovered_in": "S-071126-01, self-generated-hypothesis-extraction idea",
      "constraint": "self_administered_scrutiny_applies_regardless_of_framing",
      "rule": "H-SELF-01's inflation finding applies to any self-generated
        output from a tested substrate, not only to self-scored numeric
        values. Reframing self-generated output as a 'suggested hypothesis'
        rather than a 'self-score' does not exempt it from the same
        scrutiny — the mechanism (substrate authoring claims about itself
        under low-friction conditions) is unchanged by the framing.",
      "applies_to_gate": "Q1 (corpus quality), Q2 (scope)"
    }
  ]
}
```

## Mechanism (mirrors timing_audit exactly)

1. Before running Q1–Q7 on a new candidate, grep the ledger for lessons
   tagged to the relevant question(s).
2. Apply matched lessons as a first-pass filter before doing fresh
   analysis — the same "recursive part" `timing_audit` already
   implements: question 4's mechanism recommendation there is looked up,
   not re-derived; this does the same for triage.
3. If the candidate surfaces a new failure shape not in the ledger,
   append it at the end of triage, same write-back discipline as
   `append_new_lesson()` in `timing_audit_v1_0.py`.

## What this does NOT do

- Does not change the 7 questions themselves or their STOP conditions.
- Does not let a ledger match substitute for actually running Q1–Q7 —
  same caution as the pre-flight addendum: a pattern-class match is a
  prompt to check, not a substitute for checking.
- Does not self-register — this ledger is consulted by Zone 1, written
  to by Zone 1, and the ledger file itself would need Zone 2 sign-off to
  go live, same as `lessons_learned_ledger.json`'s own status this
  session.

## Ratification gate (for Z2)

- Confirm T1–T3 are correctly scoped and worth seeding the ledger with.
- Decide whether this is a new file (`triage_lessons_ledger.json`,
  parallel structure to the existing timing-audit ledger) or a section
  appended to the existing one — they serve different gates, so a
  separate file with the same schema seems cleaner, but that's a Z2 call.
