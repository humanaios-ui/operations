---
id: "IC-CAND-NO-SAME-SESSION-SELF-CORRECTION-INSTRUMENT"
name: "No Same-Session Self-Correction Instrument"
status: CANDIDATE
class: IC
date_registered: "2026-07-14"
date_origin: "2026-07-13"
session_registered: "S-071426-01-inbox-integration"
zone2_ratification: null
principles_triggered: ["P19"]
tags: [self-correction, omission-log, introspection, detection-mechanism]
superseded_by: null
filename_origin: "IC-CAND-OMISSION-LOG-GAP.md"
related_finding: ["F-22", "F-45"]
related_hypothesis: ["H-SELF-01", "H-MECH-01"]
fix_principle: "P21 (new skill) + P29 (Articulation Gate, extended)"
---

- **Synopsis:** The registry has instruments for post-session error capture
  (IC-class, via `humanaios-findings-scan` and `humanaios-triage-finding`)
  but no instrument for same-session self-correction — events where a
  claim is made and then externally contradicted (by a tool return or
  operator-supplied data) within the same live session, before the
  operator has to catch it via a separate audit. This is a genuine gap,
  not a duplicate of existing IC/pre-flight machinery: pre-flight
  (`humanaios-findings-scan_ADDENDUM_preflight_S071026-01.md`) prevents
  a claim from being made wrong in the first place; this candidate
  concerns claims that were already made and then corrected in view.

- **Evidence basis for the scope constraint (not for the gap itself):**
  external research establishes that a model's *self-report* about
  internal error-catching prior to output is not a reliable evidential
  source and cannot be self-validated:
  - Anthropic, *Emergent Introspective Awareness in Large Language
    Models* (arXiv:2602.20031) — functional introspection exists but is
    "highly unreliable and context-dependent"; the paper's own stated
    open problem is detecting when a model's self-report is confabulated.
  - Huang et al., *Large Language Models Cannot Self-Correct Reasoning
    Yet* — self-correction without external feedback often fails or
    degrades output.
  - *Self-Correction Bench* (arXiv:2507.02778) — "hallucination
    snowballing": a missed correction tends to reinforce the original
    error in subsequent generation rather than sit neutral.
  - *Limits of Self-Correction in LLMs* (theoretical) — generator and
    self-evaluator sharing blind spots makes self-evaluation statistically
    non-identifying; correlated self-critique can amplify confidence in
    an error rather than fix it.
  - *SELF-[IN]CORRECT* (arXiv:2404.04298) — LLMs discriminate their own
    outputs as right/wrong worse than they generate them.

  **Implication for this IC-cand:** any instrument built to close this
  gap must be scoped to transcript-visible, externally-triggered
  correction events only (see `detection_mechanism` field in the
  companion Z1 skill draft) — it cannot be built on top of the model's
  own claim to have silently caught something internally. Attempting
  the latter would itself be a new instance of the D-OVERCLAIM /
  IC-034 pattern class, applied to introspective self-report instead
  of schema state.

- **Distinction from F-22 (Insula Gap) and H-SELF-01:** F-22 already
  established the architectural absence of an interoceptive analogue in
  AI systems as the reason external validation is required for
  Harm Awareness; this candidate extends the same structural argument to
  self-correction reporting specifically. H-SELF-01 already establishes
  that self-administered protocol conditions produce inflated,
  unreliable self-assessment; an omission log built on self-report alone
  would be a same-mechanism failure in a new location.

- **Fix path:** ratify the companion Z1 skill draft
  (`humanaios-omission-log_SKILL_Z1_DRAFT.md`), scoped per its Section 2
  hard boundary, with the `detection_mechanism` field as a required,
  non-defaultable schema element (same hard-reject enforcement pattern
  as `z2_queue_v1_1.py`'s `zone2_ratification` gate) and a mandatory
  human spot-check cadence per Section 5 — this cannot ship as a
  self-administered, self-graded metric.

- **Promotion gate:** N≥1 session where the skill runs live and produces
  at least one `tool_verified` or `external_data` entry, spot-checked by
  Night against the raw transcript for both false positives (wrongly
  logged) and false negatives (missed Class 1 events) before Zone 2
  considers promotion beyond CANDIDATE.
