---
name: humanaios-omission-log
status: Z1 DRAFT — not ratified, not canonical, not wired into any skill directory
proposed: S-071126-01 (chat session, mobile)
requires: Zone 2 ratification per P21 before merge into /mnt/skills/user/
motivating_request: Night — “omission log… catch mistakes and fix it… omission tracking”
external_grounding: see Section 0 — required reading before Z2 disposition
---

# Omission Log — Z1 Candidate Skill

## Section 0 — External grounding (required before Z2 review)

This skill’s entire design is downstream of one constraint established by
outside research, not by this project: **a model’s self-report about its
own internal error-catching process is not a reliable evidential source,
and the model’s own self-evaluation is not statistically positioned to
validate itself.**

- Anthropic, *Emergent Introspective Awareness in Large Language Models*
  (arXiv:2602.20031) — functional introspection in current Claude models
  is real but “highly unreliable and context-dependent”; authors’ own
  stated open problem is developing methods to detect when a model’s
  self-report is confabulated rather than grounded. No such method is
  assumed to exist here.
- Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*
  — without external feedback, self-correction attempts often fail or
  degrade the output, empirically.
- *Self-Correction Bench* (arXiv:2507.02778) — names “hallucination
  snowballing”: once an error occurs, subsequent generation tends to
  align with it rather than catch it. A missed self-correction is not a
  neutral gap; it actively reinforces the error downstream.
- *Limits of Self-Correction in LLMs* (theoretical) — when generator and
  self-evaluator share the same blind spots, self-evaluation is
  statistically non-identifying, and correlated self-critique can
  *amplify* confidence in a wrong answer rather than fix it.
- *SELF-[IN]CORRECT* (arXiv:2404.04298) — LLMs are measurably worse at
  discriminating their own outputs as correct/incorrect than at
  generating them.

**Design consequence:** this skill never logs an event on the basis of
the model’s own claim to have silently caught and fixed something before
output. That category is permanently out of scope (see Section 2). This
is not a conservative choice made out of caution — it is the only
defensible scope given what the cited research actually shows.

## Section 1 — What this skill is

A session-scoped log of self-correction events that are **externally
checkable in the visible transcript** — not a log of internal process.
Distinct from IC-class registry entries (which capture errors caught
*after* a session, typically by the operator) — this captures errors
caught *within* a live session, before the operator had to.

## Section 2 — Scope boundary (hard, non-negotiable per Section 0)

**In scope — an event may be logged only if it is one of:**

1. A claim I made is later contradicted by a tool’s real return value
   (code execution, file read, live fetch) within the same or a later
   turn, and I state the correction explicitly.
1. A claim I made is contradicted by information the operator supplies
   (a document, a correction, a live data pull), and I state the
   correction explicitly.
1. I explicitly flag uncertainty *in the visible transcript* before
   resolving it myself via a verifiable action (a tool call, a fetch) —
   the flag and the resolution must both be visible; the flag cannot be
   reconstructed after the fact.

**Permanently out of scope — never logged, under any framing:**

- Any claim of the form “I almost said X but caught it” where X was
  never visible in the transcript.
- Any claim of the form “I noticed internally and silently corrected
  before this message” with no external trigger.
- Reconstructing a plausible internal process narrative to fill in gaps
  in the visible record. Per Section 0, this is confabulation risk, not
  a lower-confidence version of real data.

If an event does not clearly fall into one of the three in-scope
categories, it is not logged. Ambiguous cases are dropped, not
soft-included.

## Section 3 — Required schema field: `detection_mechanism`

Every logged entry must carry this field, with no default value:

|Value                      |Meaning                                                                                                         |
|---------------------------|----------------------------------------------------------------------------------------------------------------|
|`external_data`            |Contradicted by operator-supplied information                                                                   |
|`tool_verified`            |Contradicted by a real tool/execution return value                                                              |
|`self_initiated_and_stated`|I flagged uncertainty in-transcript, then resolved it via a verifiable action — flag and resolution both visible|

No other values are valid. A missing or invented `detection_mechanism`
value is a hard-reject condition (same enforcement pattern as
`tools/registry_issue_compiler_v1_0.py`’s `zone2_ratification` hard gate — the field is required at
the write path, not documented as a convention above it).

## Section 4 — Trigger pattern set (for scanning a transcript)

Two trigger classes, ranked by reliability:

**Class 1 (stronger) — tool-return contradiction.** A tool call’s actual
output does not match what a prior claim asserted. This is checkable
mechanically: diff the claim against the return value. Does not depend
on matching my own language at all.

**Class 2 (weaker, advisory only) — stated-correction phrases.** Regex/
keyword scan for explicit correction language: “I was wrong,” “actually,”
“correction:,” “let me recheck,” “that’s not accurate.” Per the Timing Audit L2
lesson (heuristic pattern checks must be advisory, never hard-blocking), Class 2
matches are candidates for
review, not automatic log entries — a Class 2 match must still resolve
to Section 2’s three in-scope categories before it’s written.

## Section 5 — Human verification requirement (non-optional)

Per Section 0’s own citations, this cannot be a self-administered
metric. Undercounting (missed corrections) and overcounting (Class-2
false positives, or borderline events wrongly classified as in-scope)
are both expected failure modes, and I am not positioned to grade my own
output against this specific rubric — that would be exactly the
correlated-blind-spot problem the cited theoretical paper describes.

Required: periodic operator spot-check against the raw transcript,
sampling logged entries for false positives and — harder to catch —
sampling *unlogged* stretches of a session for missed Class 1 events.
Frequency and sample size are a Z2 decision, not proposed here.

## Section 6 — Output format

```
OMISSION_LOG_ENTRY
  session_id: [S-XXXXXX-NN]
  turn_range: [where the original claim and correction both appear]
  original_claim: [one line]
  correction_trigger: [what contradicted it]
  detection_mechanism: [external_data | tool_verified | self_initiated_and_stated]
  correction_as_stated: [quote or close paraphrase of the actual correction]
  verification_status: [unconfirmed | operator_confirmed]
```

**`verification_status` (added — closes the paper-4 gap):** every entry is
written as `unconfirmed` at creation, with no other default permitted.
This exists because the log itself is written by the same model whose
outputs it is logging — per *Limits of Self-Correction in LLMs*
(generator and self-evaluator sharing blind spots renders self-evaluation
statistically non-identifying), an entry I write and immediately treat as
settled fact would be a same-mechanism recurrence of the exact failure
this skill exists to catch, just one layer up. `operator_confirmed` is
the only value that may replace `unconfirmed`, and only Night’s spot-check
against the raw transcript (Section 5) may set it. No entry may be cited
elsewhere — in a WGS post, a triage input, a registry candidate — while
still `unconfirmed`, and any downstream use must carry the status forward,
not silently drop it.

## Section 7 — Relationship to existing registry classes

- **Not IC-class.** IC entries are typically post-session, operator- or
  cross-session-detected. This skill’s log is same-session, and every
  entry it produces is a *candidate* input to a future IC-cand if a
  pattern recurs across sessions — it does not replace triage.
- **Feeds `humanaios-findings-scan`** the same way `tools/timing_audit_V1.0.md`
  feeds pattern classification: an omission log with a recurring
  `detection_mechanism: tool_verified` cluster around one tool or claim
  type is itself a triage-worthy signal, routed through the existing
  Q1–Q7 gate, not self-registered here.

## Section 8 — What this addendum does NOT do

- Does NOT claim any access to internal generation process.
- Does NOT log anything on the strength of self-report alone.
- Does NOT run as a hard gate on every message — it is a passive,
  transcript-scoped log, reviewed at session close or on request.
- Does NOT self-register its own output as IC/F/H class.

## Ratification gate (for Z2)

- Confirm Section 2’s scope boundary is the right line — not
  over-broad (admitting self-report) or under-broad (excluding real
  Class 1 events by requiring too strict a match).
- Decide spot-check cadence and sample size (Section 5).
- Decide whether this ships as a standalone skill or as a mode inside
  `humanaios-findings-scan`, parallel to the pre-flight addendum
  already Z1-drafted this project.
- Confirm the external-grounding citations in Section 0 are read and
  accepted as the operating constraint before any wider rollout.