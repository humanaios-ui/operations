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

  Motivation: callouts are currently text-only; a human scanning many of them
  (e.g. in a dashboard or CI summary) may benefit from a fast visual/verbal
  cue of urgency class, same reasoning the game applies to players.

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
    - "Faster urgency triage for a human scanning multiple open callouts"
    - "Reusable, tested-in-miniature pattern if the game's own sound_intent later ships"
  risk_factors:
    - "Glyph/word choices are bikeshed-prone; this draft explicitly marks them as the most revisable part"
    - "If adopted anywhere, must not be audio-only (accessibility) — carried over from the game's own constraint"

falsifier: |
  This hypothesis is FALSE if a person unfamiliar with the taxonomy, shown
  only the glyph + word-cue (no callout name), cannot distinguish a
  decide-now callout (AMBIGUITY, DISPUTED, REVERT) from a can-wait callout
  (STALE, GAP, DRIFT) at better than chance in a quick read-through. If
  falsified, the taxonomy's own text stays authoritative; no presentation
  layer is adopted.

evidence:
  - "CLAUDE.md § Callout Mandatory Triggers (table of 10 callouts)"
  - "issue #1020, Sound-first interface section (sound_intent catalog)"
  - "issue #1020, 'Z1 Candidate: Dual-Use Mapping' section, H4"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-H-WITNESS-UX-LESSONS-01"]
external_constraint: null
links:
  - name: "Source issue"
    url: "https://github.com/humanaios-ui/operations/issues/1020"
```
