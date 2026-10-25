```yaml
candidate_id: "Q-H-SOUND-CALLOUT-ADAPTER-01"
title: "Scope H4: bounded sound_intent-style vocabulary as a presentation layer over the callout taxonomy"

description: |
  Issue #1020 specifies a bounded `sound_intent` catalog for the game's sound-born
  faction: a small fixed set of signals (ping, warn, invite, offer_passage, refuse,
  mourn, resonate), each required to have a non-audio fallback (shape/color/text).

  This candidate proposes drafting the same shape — small fixed vocabulary,
  >=2 non-exclusive channels, never audio-only — as an optional presentation
  layer over CLAUDE.md's existing callout taxonomy (GAP, STALE, RECEIPT-GAP,
  GAUGE, AMBIGUITY, VOID, DRIFT, DISPUTED, MOLT, REVERT). It changes no
  trigger, route, or Z2 response in that table — glyph/word cues only.

  Correction (per review on this PR): the original draft tested recognition
  of an invented "decide-now vs can-wait" urgency split. CLAUDE.md's taxonomy
  defines triggers, routes and Z2 responses, not a severity field — e.g. a
  GAP can represent an expired urgent decision window, so "GAP = can wait"
  is not a safe assumption. This version drops the urgency framing entirely:
  the glyph/word cue is scoped to help a reader recognize *which callout
  applies* (its documented trigger meaning), nothing about how urgent it is.

  Motivation: callouts are currently text-only; a human scanning many of them
  (e.g. in a dashboard or CI summary) may benefit from a fast visual/verbal
  cue of *which* callout this is, without re-reading the full word each time
  — same reasoning the game applies to players learning sound_intent.

author: "Z1 (Claude)"
proposed_at: "2026-10-25T00:00:00Z"

scope:
  - "operations"
  - "CLAUDE.md § Callout Mandatory Triggers (read only, this candidate)"
  - "issue #1020 (read only)"

resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 4
    Z3-hr: 0
    CI-min: 0
  dependencies:
    - "CLAUDE.md callout taxonomy table (unchanged by this candidate)"
    - "issue #1020 (sound_intent spec)"
  blocking_on: []

impact_prediction:
  resource_impact: 2
  areas_affected:
    - "Callout presentation only (dashboards, CI summaries, future UI)"
  positive_outcomes:
    - "Faster callout-identity recognition for a human scanning multiple open callouts"
    - "Reusable, tested-in-miniature pattern if the game's own sound_intent later ships"
  risk_factors:
    - "Glyph/word choices are bikeshed-prone; this draft explicitly marks them as the most revisable part"
    - "If adopted anywhere, must not be audio-only (accessibility) — carried over from the game's own constraint"
    - "Must not imply urgency/severity the taxonomy doesn't define — see corrected falsifier"

falsifier: |
  This hypothesis is FALSE if a person unfamiliar with the taxonomy, shown
  only the glyph + word-cue (no callout name), cannot match it back to the
  correct callout's documented trigger (e.g. distinguishing a GAP's "blocked
  row without an unblock action" from a DRIFT's "dial moved from its ratified
  baseline") at better than chance in a quick read-through. If falsified, the
  taxonomy's own text stays authoritative; no presentation layer is adopted.

  This candidate makes no urgency or severity claim and tests none: CLAUDE.md's
  taxonomy defines triggers, routes and Z2 responses only, and a callout's
  urgency (e.g. a GAP sitting on an expired decision window) is not determined
  by its type alone. Any future urgency cue would need separately authorized
  per-event priority information — out of scope here.

evidence:
  - "CLAUDE.md § Callout Mandatory Triggers (table of 10 callouts: trigger/route/response)"
  - "issue #1020, Sound-first interface section (sound_intent catalog)"
  - "issue #1020, 'Z1 Candidate: Dual-Use Mapping' section, H4"
  - "PR #1023 review comment (Copilot, discussion_r4371374116): flagged the original urgency-binary framing as unsupported by the taxonomy"

z2_decision:
  status: "ratified"
  ratified_at: "2026-10-25"
  ratification_hash: null
  z2_notes: "Approved by Night via direct chat instruction, this session ('ratify H2/H4 approved'). Offered a choice of three paths, Night chose to skip .z1-control/ratify.py and record this as a plain note instead -- no cryptographic Z2 signature exists for this decision. See z1-inbox/2026-10-25/Z2_RULINGS_2026-10-25.md for the full ruling."

related_candidates: ["Q-H-WITNESS-UX-LESSONS-01"]
external_constraint: null
links:
  - name: "Source issue"
    url: "https://github.com/humanaios-ui/operations/issues/1020"
  - name: "Review comment addressed"
    url: "https://github.com/humanaios-ui/operations/pull/1023#discussion_r4371374116"
```
