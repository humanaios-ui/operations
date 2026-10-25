```yaml
candidate_id: "Q-H-WITNESS-UX-LESSONS-01"
title: "Scope H2: W1 (game Witness) UX properties as a design reference for the real Witness Ledger"

description: |
  Issue #1020 (Game vNext charter) specifies W1, a read-only per-player Witness:
  evidence-cited, non-advisory, scope-bounded to the owning player's own data.
  These are UX properties, written in game-design prose, not code.

  This candidate proposes extracting 3 concrete UX lessons from W1's spec and
  checking each against the real, ratified Witness Ledger's current human-facing
  views (Q-INTENT-OS-WITNESS-LEDGER-01, Phase 1):
    1. Cite, don't assert — show the evidence pointer beside every claim.
    2. Scope boundary should be visible, not just enforced in code.
    3. Non-advisory framing — mark a record as "record, not recommendation."

  Motivation: this costs no implementation and risks nothing (read-only review
  of existing specs), and either confirms the real ledger already does this
  (no action) or surfaces a concrete, small UI fix.

author: "Z1 (Claude)"
proposed_at: "2026-10-25T00:00:00Z"

scope:
  - "operations"
  - "issue #1020 (read only)"
  - "Witness Ledger Phase 1 UI (read only, this candidate)"

resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 3
    Z3-hr: 0
    CI-min: 0
  dependencies:
    - "issue #1020 (W1 spec)"
    - "Q-INTENT-OS-WITNESS-LEDGER-01 (ratified 2026-09-19)"
  blocking_on: []

impact_prediction:
  resource_impact: 2
  areas_affected:
    - "Witness Ledger human-facing views (UX only)"
  positive_outcomes:
    - "Either confirms existing ledger UX already meets these 3 properties (no action, cheap close)"
    - "Or produces 1-3 small, concrete UI change requests, each independently reviewable"
  risk_factors:
    - "Game-to-real analogy could be over-read as more than UX inspiration; this candidate explicitly disclaims shared code/data to guard against that"

falsifier: |
  This hypothesis is FALSE if a 10-minute read-through of the real Witness
  Ledger's current (Phase 1) UI shows all 3 properties (cite-don't-assert,
  visible scope boundary, non-advisory framing) already present, OR if none
  of the 3 produce an actionable, concrete UI change. Either outcome closes
  this candidate without code change — it is not stretched to find a finding
  that isn't there.

evidence:
  - "issue #1020, section 'Game design: authoritative layers', item 4 (W1 spec)"
  - "CLAUDE.md, Appended Events, Q-INTENT-OS-WITNESS-LEDGER-01 ratification line (2026-09-19)"
  - "issue #1020, 'Z1 Candidate: Dual-Use Mapping' section, H2"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-H-SOUND-CALLOUT-ADAPTER-01"]
external_constraint: null
links:
  - name: "Source issue"
    url: "https://github.com/humanaios-ui/operations/issues/1020"
```
