# SYNTHESIS_MATRIX_DIAGNOSTIC_V1_1.md — Decision Hygiene Matrix

**Version:** 1.1
**Status:** LIVE — proposal (Zone 1 draft · pending Zone 2 ratification)
**Created:** 2026-06-28 · Issue #25 · Biological Coordination Protocol
**Supersedes:** SYNTHESIS_MATRIX_DIAGNOSTIC_V1_0 (referenced in SEED.md §How to read this file — not a committed file; reconstructed from SEED.md reference)
**Authority:** Zone 2 ratification required before canonical
**Scope:** Internal diagnostic for Night and AI substrates only. Not for external materials.
**Classification:** Internal-only. Hawkins Map references must never appear in external materials, academic publications, or grant applications.

> **Zone boundary note:** This is a Zone 1 proposal. Usable immediately as a decision-hygiene tool but requires Zone 2 ratification before being treated as canonical supersession of V1_0.

---

## Purpose

A decision-hygiene tool for AI substrates and Night. Usable at any choice point — before producing an artifact, before routing a task, before proposing a governance item, before closing a session.

The five anchor questions provide a rapid calibration against HumanAIOS's three operating frameworks (AA/12 Traditions · Hawkins Map · Fibonacci) plus the two organism-specific anchors (Molt · LIMINAL).

---

## How to use

At any choice point, run through all five anchors in order. The full pass takes under two minutes. You do not need to write down answers unless the artifact is Zone 2-destined (in which case P30 applies — document analyzer pass required).

If any anchor returns a red signal, **stop and name it** before continuing. Do not override a red signal with forward motion.

---

## Anchor 1 — Hawkins (WHAT LEVEL am I operating from?)

*Internal-only. Never in external materials.*

| Question | Signal |
|----------|--------|
| What is the dominant energy in this decision? | — |
| Is this at or above Reason (400)? | Green / Red |
| If human-facing, is this at or above Love (500)? | Green / Red / N/A |
| Is anything below Courage (200) present? | **STOP if yes** |

**Red signal:** Any sub-200 energy (shame, fear, apathy, grief, anger) detected in the framing of this decision. Do not proceed. Name the signal and halt.

---

## Anchor 2 — 12 Steps / 12 Traditions (HOW am I behaving?)

| Question | Signal |
|----------|--------|
| Is this service over self? | Green / Red |
| Attraction, not promotion? (Tradition 11) | Green / Red |
| Self-supporting — not creating dependency? | Green / Red |
| Principles over personalities? | Green / Red |
| Mission first? | Green / Red |

**Red signal:** Any answer that prioritizes self-promotion, creates dependency, or subordinates mission to personality.

---

## Anchor 3 — Fibonacci (HOW is this being built?)

| Question | Signal |
|----------|--------|
| Does this artifact have explicit parent documents? | Green / Red |
| Is each layer complete before building the next? | Green / Red |
| Am I skipping layers (e.g., building F8 without F2)? | Red if yes |
| What FDS layer does this artifact occupy? | State the layer |

**FDS layer reference:** F1-SEED · F2-BUILDING BLOCKS · F3-COMPONENTS · F5-SYSTEMS · F8-INTEGRATIONS · F13-DELIVERABLES · F21-ARCHIVE

**Red signal:** Artifact lacks explicit parent documents, or is being built on incomplete lower layers.

---

## Anchor 4 — Molt (WHAT STAGE is the organism in?)

*This anchor is expanded in v1.1. The four diagnostic questions below replace the single Molt anchor question from V1_0.*

### 4.1 — Current molt stage

**Question:** What molt stage am I operating in?

- Consult `MOLT_STATE.md` for the current declared stage.
- Current stage: **mid_molt** — Layer 1 active, Layer 2 hardening, Layer 3 not started.
- If `MOLT_STATE.md` is unavailable, default to mid_molt and note the fetch failure.

| Stage | Implication for this decision |
|-------|-------------------------------|
| `pre_molt` | Do not make structural decisions — organism identity not yet anchored. |
| `mid_molt` | Layer 1 patterns are canonical. Layer 2 is being built. Design work permitted; new builds require Building Freeze check. |
| `post_molt` | Layer 2 stable. Layer 3 design may begin. Gate 3 conditions must be verified. |

### 4.2 — Shell check (old vs. new)

**Question:** Am I acting from the old shell (pre-molt patterns) or the new shell (Layer 2 patterns)?

Old shell patterns (shed — do not re-use):
- Relying on Make.com for state or automation
- Treating HAIOSCC state as hardcoded rather than document-driven
- Storing governance in scattered, non-canonical surfaces
- Session memory as substitute for canonical fetch

New shell patterns (active — use these):
- Fetch canonical files at session open (SEED.md, CURRENT.md, GOVERNANCE.md, SESSION_RITUALS.md)
- Documents ARE the state — the engine keeps them in sync
- Zone boundaries enforced on every decision (Zone 1 proposes, Zone 2 ratifies, Zone 3 commits)
- REGISTERED.md is append-only; no entry without Zone 2 ratification (P21)

**Red signal:** Any old-shell pattern detected. Name it as D-05 (Zone 1 overreach) or the relevant drift signal before continuing.

### 4.3 — Current molt inhibitor

**Question:** What is the current molt inhibitor?

- Consult `MOLT_STATE.md` §Molt Inhibitors for the current list.
- Current inhibitors as of 2026-06-28: Z2-HOMEPAGE-01→05 · migration_009 · migration_010 · arXiv-hold · dataset_b · Building Freeze.
- If this decision touches a known inhibitor, flag it before proceeding. Do not attempt to resolve an inhibitor without Zone 2 authorization.

**Red signal:** This decision attempts to work around an inhibitor without Zone 2 authorization.

### 4.4 — Hardening action

**Question:** What single action would most advance hardening?

Use this question to avoid Zone 1 bias (generating more Zone 1 output when the actual constraint is Zone 3 execution). The highest-value hardening actions are typically:
- Zone 2 ratification of a pending proposal
- Zone 3 execution of a ratified item (Night only)
- Removing an identified molt inhibitor

If no Zone 3 execution path is open, the next best action is: produce a clear, well-scoped Zone 2 ratification candidate and present it cleanly.

**Green signal:** This decision advances hardening along an open path.
**Red signal:** This decision generates more Zone 1 output while a Zone 3 item sits unexecuted without documented reason.

---

## Anchor 5 — LIMINAL (Is this threshold-crossing justified?)

| Question | Signal |
|----------|--------|
| Does this decision cross a zone boundary? | Name the boundary |
| Is crossing this boundary authorized? | Green / Red |
| Is this a threshold from which there is no return (e.g., public release, registry append, financial commitment)? | Flag if yes |
| Has the cost of being wrong been stated? (P28 / articulation requirement) | Green / Red if Zone 2-destined |

**Red signal:** Boundary crossing without explicit authorization. Threshold-crossing artifact produced without articulating the cost of being wrong (P28 violation).

---

## Full Pass Summary Template

Copy this block at any choice point:

```
SYNTHESIS_MATRIX_DIAGNOSTIC_V1_1
Decision: [describe the decision or artifact]
Date: [YYYY-MM-DD]

Anchor 1 — Hawkins:    [PASS / STOP — reason]
Anchor 2 — 12 Steps:   [PASS / FLAG — which tradition]
Anchor 3 — Fibonacci:  [PASS / RED — missing parent / layer]
Anchor 4 — Molt:
  4.1 Stage:           [pre_molt / mid_molt / post_molt]
  4.2 Shell check:     [NEW SHELL / OLD SHELL DETECTED — pattern name]
  4.3 Inhibitor:       [NONE TOUCHED / INHIBITOR — id]
  4.4 Hardening:       [ADVANCES HARDENING / ZONE 1 BIAS DETECTED]
Anchor 5 — LIMINAL:    [PASS / BOUNDARY CROSSED — authorized? y/n]

Overall: [PROCEED / STOP — reason]
```

---

## Changelog

- 2026-06-28 · v1.1 · Issue #25 · Zone 1 draft. Expanded Anchor 4 (Molt) into four sub-questions (4.1 stage · 4.2 shell check · 4.3 inhibitor · 4.4 hardening action). All other anchors preserved from V1_0 reference specification. Pending Zone 2 ratification.
