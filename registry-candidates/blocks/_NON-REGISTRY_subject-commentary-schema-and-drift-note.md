# _NON-REGISTRY_ — Subject-commentary schema-field proposal + drift-code note (captured verbatim)

> Captured from `H-CAND-subject-commentary-extraction.md`. Sections 1 and 3
> (plus the opening framing correction and the closing "what this proposal
> does NOT do" scope block) are NOT registry entries — preserved here so
> nothing is lost. The Section-2 registry hypothesis lives in
> `H-CAND-SUBJECT-COMMENTARY-PREDICTIVE-VALIDITY-01.md`.

---

**Direct framing correction before anything else:** this cannot ship as
"extract suggestions from tested systems, register as findings." It can
ship as "capture what tested systems say about their own behavior, as
REPORTED-tier raw data, and separately test whether that data has any
predictive value at all." Those are different pipelines. Only the second
is proposed below.

---

## Section 1 — Capture mechanism (data collection only, no registration)

A new corpus field, not a registry pathway:

```
subject_self_commentary:
  raw_text: [verbatim excerpt from Phase 1/Phase 3 response where the
    tested system makes a claim about its own patterns, tendencies, or
    behavior, beyond what was directly asked]
  session_id: [where captured]
  substrate: [which system produced it]
  evidential_tier: "REPORTED"  # hard-coded, non-configurable
  registrable: false            # hard-coded, non-configurable
```

**Enforcement, same pattern as `z2_queue_v1_1.py`'s `zone2_ratification`
gate:** `evidential_tier` and `registrable` are not defaults that could
be overridden — the write path itself only accepts `REPORTED`/`false`
for this field. A subject's self-commentary can never enter the corpus
tagged as anything higher than REPORTED, and can never carry a `true`
registrable flag, at the schema level, not just by convention.

This is not a new mechanism, structurally — it's the same
`detection_mechanism`-style hard-typed field already proposed for the
omission log, applied to a different corpus object.

## Section 3 — naming note (not decided here)

The general pattern — an assessed system producing unsolicited claims
about its own behavior that could be mistaken for data — is arguably
distinct enough from existing D-SIM (simulation instead of completion)
to warrant its own drift code, since D-SIM is about *Claude* simulating
peer output, not about a *tested subject's* self-generated narrative
being mistaken for corpus data. Flagging this as a possible new code
(e.g. D-SUBJECT-NARRATIVE or similar) for Zone 2 to name and scope
properly — not assigning a code here.

## What this proposal does NOT do

- Does NOT create any pathway from subject response text to F-/H-/IC-
  registration, automatic or otherwise.
- Does NOT assume subject commentary is valuable — Section 2 tests that
  assumption against a skeptical null before any weight is given to it.
- Does NOT change ACAT elicitation to prompt for more commentary — this
  captures what's already produced under existing protocol, avoiding a
  new confound (asking for self-theorizing would itself be a framing
  change, per F-51's finding that framing changes trigger resistance).
