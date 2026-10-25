```yaml
candidate_id: "Q-H-WITNESS-UX-LESSONS-01"
title: "Scope H2: W1 (game Witness) UX properties as a design reference for the Witness Ledger's eventual human-facing view"

description: |
  Issue #1020 (Game vNext charter) specifies W1, a read-only per-player Witness:
  evidence-cited, non-advisory, scope-bounded to the owning player's own data.
  These are UX properties, written in game-design prose, not code.

  Correction (per review on this PR): Q-INTENT-OS-WITNESS-LEDGER-01's own
  Implementation Path puts the human-facing view ("INTENT-OS board shows
  decision timeline + actors") in Phase 3, not Phase 1 — and per CLAUDE.md,
  Phase 1 itself is still "in progress." There is no live Witness Ledger UI
  to read through yet. This candidate now compares against the *documented
  design intent* for that eventual view, not a live walkthrough.

  This candidate proposes extracting 3 concrete UX lessons from W1's spec and
  checking each against what Q-INTENT-OS-WITNESS-LEDGER-01 documents the
  eventual human-facing view should do:
    1. Cite, don't assert — show the evidence pointer beside every claim.
    2. Scope boundary should be visible, not just enforced in code.
    3. Non-advisory framing — mark a record as "record, not recommendation."

  Motivation: this costs no implementation and risks nothing (read-only
  comparison of two specs), and either confirms the documented design already
  implies these 3 properties (no action) or surfaces a concrete addition to
  make to that design before Phase 3 is built.

author: "Z1 (Claude)"
proposed_at: "2026-10-25T00:00:00Z"

scope:
  - "operations"
  - "issue #1020 (read only)"
  - "Q-INTENT-OS-WITNESS-LEDGER-01 design text (read only, this candidate)"

resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 3
    Z3-hr: 0
    CI-min: 0
  dependencies:
    - "issue #1020 (W1 spec)"
    - "Q-INTENT-OS-WITNESS-LEDGER-01 (ratified 2026-09-19; Phase 3 covers the human-facing view and is not yet built)"
  blocking_on: []

impact_prediction:
  resource_impact: 2
  areas_affected:
    - "Witness Ledger Phase 3 design (documented intent, not live UI)"
  positive_outcomes:
    - "Either confirms the documented design already implies these 3 properties (no action, cheap close)"
    - "Or produces 1-3 small, concrete additions to the Phase 3 design doc, each independently reviewable, before any UI is built"
  risk_factors:
    - "Game-to-real analogy could be over-read as more than UX inspiration; this candidate explicitly disclaims shared code/data to guard against that"
    - "No live UI exists yet to verify against; a live-UI check stays blocked/unverified until Phase 3 ships, and is not evidence against this hypothesis in the meantime"

falsifier: |
  This hypothesis is FALSE if a 10-minute read-through of Q-INTENT-OS-WITNESS-LEDGER-01's
  documented design (and any Phase 3 design text that supersedes it) shows all 3
  properties (cite-don't-assert, visible scope boundary, non-advisory framing)
  already specified, OR if none of the 3 produce an actionable addition to that
  design. Until Phase 3 has a built, inspectable view, "the live UI doesn't do
  this yet" is BLOCKED/UNVERIFIED, not a falsifying result — this candidate is
  only evaluated against the documented design until an inspectable view exists.

evidence:
  - "issue #1020, section 'Game design: authoritative layers', item 4 (W1 spec)"
  - "z1-inbox/2026-09-19/Q-INTENT-OS-WITNESS-LEDGER-01.md, 'Implementation Path' (Phase 1 Tier 2 Foundation vs Phase 3 Scale — board/timeline is Phase 3)"
  - "CLAUDE.md, Appended Events, Q-INTENT-OS-WITNESS-LEDGER-01 ratification line (2026-09-19) and machine Z3 authority note ('Phase 1 integration in progress')"
  - "issue #1020, 'Z1 Candidate: Dual-Use Mapping' section, H2"
  - "PR #1023 review comment (Copilot, discussion_r4371374171): flagged the original Phase-1-UI framing as unsupported"

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
  - name: "Review comment addressed"
    url: "https://github.com/humanaios-ui/operations/pull/1023#discussion_r4371374171"
```
