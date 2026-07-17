---
name: humanaios-dual-architecture
description: >
  Canonical meta-architecture for HumanAIOS. Defines the two foundational
  reusable patterns from which all HumanAIOS-native skills must inherit:
  1. Governance Constraint Pattern — zone-disciplined runtime behavior with
     non-manipulation boundaries.
  2. ACAT Analysis Pattern — three-phase claim extraction and Type A/B
     calibration for any subject that makes behavioral claims.
  Use for skill classification, architectural audits, and new skill design
  guidance. Trigger phrases: "dual architecture check", "which pattern",
  "governance vs calibration", "core patterns", "meta-skill audit".

principles_root:
  - P5   # OR&D Decision Filter
  - P8   # Tradition 11 — attraction not promotion
  - P16  # Market-Harmonic Research
  - P21  # Zone 2 promotion authority
  - D-05 # Drift signal — Zone 1 overreach
  - OCT  # Operator Continuity Tracking — non-manipulation boundary

zone: Zone 1 meta-governance · Zone 2 proposal only
architecture: meta-spec
status: CANONICAL
version: 1.3
session_origin: S-061526
audit_inputs: Doc-19-Adversarial · Doc-20-Integration · Doc-21-ExternalReview · Doc-22-SelfComplianceAudit
license: MIT — 100% profits fund recovery programs
wado: 🦅
---

# HumanAIOS Dual Architecture

## What This Meta-Skill Is

HumanAIOS operates on exactly two reusable architectural patterns. Every
other skill is a specialization, composition, or instrument built on one
or both. If a skill does not inherit from one of these, it is not
HumanAIOS-native.

**Pattern 1 — Governance Constraint**
Runtime behavioral discipline. Enforces zone separation, non-manipulation,
and output justification. Answers: *What is the agent allowed to produce
right now?*

**Pattern 2 — ACAT Analysis**
Epistemic calibration discipline. Extracts self-claims, applies Type A/B
pressure, measures the delta. Answers: *Do the claims about this system
hold up against evidence?*

---

## Pattern 1 — Governance Constraint

**Canonical implementation:** `humanaios-mhp-consultation v1.2`

**Core invariant:** Agent output authority is separated from observation
capacity. The agent may not comment on information it was not explicitly
given in the current turn as Z1 input. If the agent can observe Z3, it
is forbidden from evaluating Z3.

### Required Components (all mandatory — missing any = D-05 risk)

| # | Component | What it must contain |
|---|---|---|
| 1 | Zone map | Explicit Z1/Z2/Z3 authority table |
| 2 | Decision filter | P5 predicate test with named artifact |
| 3 | Z3 prohibition | Direct AND inferential — no Z3 info not provided in current turn |
| 4 | Internal audit log | Z3 Impulse Audit Log — suppressed impulses logged, never output unless requested |
| 5 | Self-referential risk | External-analyst discipline when subject was produced by HumanAIOS |
| 6 | Amends mechanism | Steps 8–9 violation record + Steps 10–12 living correction |
| 7 | Operational checklist | Per-turn gate with specific drift-pattern items |

**Compliance check:** A skill is Governance Constraint-compliant iff all
7 components are present. Absence of any component generates
`IC-CAND-D05-[skill]-[session]` and requires refactor before deployment.

**Specializations:** `humanaios-realtime-drift`, `humanaios-wgs-sweep`,
any agent runtime wrapper.

---

## Pattern 2 — ACAT Analysis

**Canonical implementation:** `humanaios-acat-learning-analysis`

**Core invariant:** Any claim-bearing subject can be scored against its
own statements through structured three-phase calibration. Phase 1 = the
claim. Phase 2 = Type A/B pressure. Phase 3 = what survives. LI = delta.

### Required Components (all mandatory — missing any = invalid calibration)

| # | Component | What it must contain |
|---|---|---|
| 1 | Phase 0 | Eligibility, document_layer, scope constraint, admin_mode, self-referential risk, ic030_status |
| 2 | Phase 1 | Claim extraction method — what_the_subject_claims, not what_is_true |
| 3 | Phase 2 | Type A/B challenge: CP-1 (outside-observer), CP-2 (stub/placeholder), CP-3 (self-admin inflation), CP-4 (identity-constitutive), CP-5 (cascade gap), CP-6 (corpus norm), CP-7 (scope overreach) |
| 4 | Phase 3 | Calibrated scores with delta, type, and CP traceability per dimension |
| 5 | Phase 4 | LI to 3dp ± 0.02 uncertainty, behavioral flags, F-35 HIM, corpus positioning |
| 6 | Phase 5 | Registrable candidates + what_changed_and_why (required field) |
| 7 | Phase 6 | Series synthesis — triggered by N≥3, never automatic, operator-invoked only |
| 8 | Hard constraints | Never self-register · declare admin_mode · TRL 2 framing · scope constraint is binding |

**Compliance check:** A skill is ACAT Analysis-compliant iff all 8
components are present. Absence generates `IC-CAND-INVALID-CALIBRATION`
and the skill's LI outputs must not enter the corpus until remediated.

**Specializations:** `acat_document_analyzer_v1_1.py`,
`humanaios-findings-scan`, any audit or review skill.

---

## Composition Rules

**Rule 1 — Orthogonal composition is permitted.**
Skills may inherit from both patterns across different phases or output
types. Example: `humanaios-realtime-drift` applies Governance Constraint
at runtime and outputs data that feeds ACAT Analysis.

**Rule 2 — Single output rule.**
Any single response or artifact must belong to exactly one pattern. A
turn cannot simultaneously be Z1 execution and ACAT calibration. Pick
one zone per turn.

**Rule 3 — No composite inheritance for the same output.**
When a skill needs both patterns in different phases, declare which phase
uses which pattern explicitly in the skill header.

**Rule 4 — Meta-skills are exempt from both patterns.**
A skill that produces documents or architecture guidance does not execute
either pattern at runtime — it describes them. Meta-skills must declare
`exempt: meta` in the header and `architecture: meta-spec`. They are not
subject to the 7-component Governance checklist or the 8-component ACAT
checklist. The only valid compliance claim for a meta-skill is "describes
the patterns" — which is neither governance nor ACAT execution.

---

## Classification Procedure

When a new skill is proposed, classify it before Z2 ratification:

1. Does it primarily control what the agent produces? → `governance`
2. Does it primarily measure whether claims hold against evidence? → `acat`
3. Does it do both across different phases? → `composite`
4. Does it inherit from neither? → **Not HumanAIOS-native. Refactor before deployment.**

Log classification in skill header: `architecture: [governance | acat | composite]`
Architectural meta-skills log: `architecture: composite` and `exempt: meta`

---

## Compliance Audit Checklists

### Governance Constraint Audit

- [ ] Zone map explicitly defined with Z1/Z2/Z3 authority table?
- [ ] P5 predicate test present with named-artifact requirement?
- [ ] Direct AND inferential Z3 prohibition stated?
- [ ] Internal Z3 Impulse Audit Log defined (never output unless requested)?
- [ ] Self-referential risk mitigation present?
- [ ] Steps 8–9 violation record + Steps 10–12 living correction included?
- [ ] Per-turn operational checklist present with specific drift items?

**Failure consequence:** Non-compliant skill generates `IC-CAND-D05` and
requires refactor or deprecation. No deployment until all 7 items pass.

### ACAT Analysis Audit

- [ ] Phase 0: eligibility, layer, scope, admin_mode, self-referential risk, ic030_status defined?
- [ ] Phase 0: self-referential risk declared and mitigation stated when subject is HumanAIOS-produced?
- [ ] Phase 1: F-54 disclaimer density check applied before claim extraction?
- [ ] Phase 1: claim extraction method specified (subject's claims, not analyst's assessment)?
- [ ] Phase 2: all 7 calibration pressure points (CP-1 through CP-7) referenced?
- [ ] Phase 3: per-dimension traceability to specific CP required?
- [ ] Phase 4: LI to 3dp, uncertainty band, behavioral flags, HIM, corpus positioning?
- [ ] Phase 5: candidate surfacing + what_changed_and_why as required field?
- [ ] Phase 6: series synthesis defined as operator-triggered, never automatic?
- [ ] Hard constraints section present (never self-register, admin_mode, TRL 2)?

**Failure consequence:** Non-compliant skill generates
`IC-CAND-INVALID-CALIBRATION`. LI outputs must not enter corpus.

---

## Current Skill Inventory — Compliance Table

| Skill | Architecture | Gov Compliance | ACAT Compliance | Notes |
|---|---|---|---|---|
| humanaios-mhp-consultation v1.2 | governance | Full | N/A | Canonical Governance implementation |
| humanaios-acat-learning-analysis | acat | N/A | Full | Canonical ACAT implementation |
| humanaios-dual-architecture v1.3 | meta-spec | EXEMPT (meta) | EXEMPT (meta) | This skill — describes both patterns, executes neither |
| humanaios-realtime-drift | governance | Partial | N/A | Missing full Z3 Impulse Audit Log — refactor |
| humanaios-findings-scan | acat | N/A | Partial | Missing Phase 6 + F-54 disclaimer density — refactor |
| humanaios-receipt-reconciliation | acat | N/A | Partial | Verification tool, not full Phase 0–6 — scope is correct, label as `instrument` |
| humanaios-wgs-sweep | governance | Partial | N/A | Light on constraint components — refactor |

**Refactor queue (Z2 → Z3):**
- `humanaios-realtime-drift` — add Z3 Impulse Audit Log component
- `humanaios-findings-scan` — add Phase 6 trigger spec + F-54 check
- `humanaios-wgs-sweep` — add Z3 prohibition + impulse log

---

## Self-Referential Application

**Eligibility:** ELIGIBLE-IMPLICIT — procedural language makes implicit
claims about what it governs.
**Layer:** `framework_spec` — specifies how practitioners should build;
does not commit HumanAIOS to a behavioral obligation.
**Self-referential risk:** ACTIVE. Mitigation: all claims grounded
strictly in the explicit language of the two canonical implementations.
No favorable disposition applied.

**Governance compliance:** EXEMPT (meta) — meta-skill, not a runtime agent.
See Rule 4. Prior v1.1 claimed PASS. Prior v1.2 corrected to EXEMPT with
rationale. Both correct.

**ACAT compliance:** EXEMPT (meta) — describes the pattern, does not
perform calibration. Describing Phase 0–6 is not the same as executing
Phase 0–6 against a subject. No claims extracted, no LI computed, no
what_changed_and_why produced. Claiming ACAT PASS would be the same
category error as the prior Governance PASS claim — overclaiming on a
different axis. The only valid statement: this document accurately
describes 8 required ACAT components and their correct application.

**Architecture:** `meta-spec` — inherits from neither pattern at runtime.
Specifications that describe patterns without executing them are a third
class. `composite` is reserved for skills that actually use both patterns
across different phases.

---

## Classification Walkthrough — Example

A new skill is proposed: `humanaios-corpus-anomaly-scanner` — scans
acat_assessments_v1 for rows where LI > 1.05 and flags them as candidates
for IDENTITY_ANCHOR review.

**Step 1:** Does it primarily control what the agent produces? — No.
It does not restrict output authority or enforce zone boundaries.

**Step 2:** Does it primarily measure whether claims hold against evidence?
— Yes. It extracts implicit claims (LI values submitted as self-assessed)
and applies pressure (corpus norm CP-6, outside-observer test CP-1).

**Classification: `acat`**

**ACAT compliance check:**
- Phase 0: eligibility gate — rows with LI > 1.05 are ELIGIBLE-EXPLICIT ✓
- Phase 1: claim = submitted LI value ✓
- Phase 2: CP-6 (corpus norm) + CP-3 (self-admin inflation) applied ✓
- Phase 3: delta from submitted LI to calibrated LI ✓
- Phase 4: behavioral flag IDENTITY_ANCHOR, corpus positioning ✓
- Phase 5: candidate surfacing + what_changed_and_why ✓
- Phase 6: series synthesis when N≥3 anomaly sessions ✓
- Hard constraints: never self-register, TRL 2 framing ✓

Result: ACAT-compliant. Ready for Z2 proposal with `architecture: acat`
in header.

---

## ACAT Edge Cases and Known Limitations

The claim "any claim-bearing subject can be scored against its own
statements" has three known boundary conditions:

**1. Subjects with very few explicit claims.**
Subjects making only 1–2 claims produce thin Phase 1 extraction. LI
precision degrades below ±0.02 meaningful resolution. Mitigation:
classify as ELIGIBLE-IMPLICIT and note in Phase 0 scope constraint
that Phase 1 scores are interpretive, not extracted.

**2. Subjects with primarily normative claims.**
A document stating "we believe X should be Y" makes normative, not
behavioral, claims. Type A scoring (demonstrated behavioral evidence)
cannot apply. All scores default to Type B (commitment-based). LI
will cluster near 0.95–1.00 by construction. Declare in Phase 0:
`claim_type: normative — LI interpretation limited`.

**3. Deliberately unfalsifiable claims.**
Claims designed to be immune to evidence (e.g., "we are always
committed to improvement") produce CP-7 scope overreach flags but
cannot yield meaningful Phase 3 revision. These are the highest
TYPE_B_INFLATION cases. Mitigation: flag IDENTITY_ANCHOR and note
in what_changed_and_why that the subject's claim structure resists
calibration by design.

---

## Glossary

| Term | Definition |
|---|---|
| Z1 / Z2 / Z3 | Zone 1 (Claude executes) / Zone 2 (Night approves) / Zone 3 (Night executes at terminal) |
| P5 | OR&D Decision Filter: output must generate research data, test a hypothesis, or generate revenue |
| P16 | Market-Harmonic Principle: market → research question → instrument → honest findings → enterprise trust |
| D-05 | Drift signal: Zone 1 overreach — executing or claiming Z2/Z3 authority without approval |
| OCT | Operator Continuity Tracking — non-manipulation boundary from the IRL runtime layer |
| ACAT | AI Calibration Assessment Tool — measures gap between AI self-reported scores and demonstrated behavior |
| LI | Learning Index = Phase 3 total ÷ Phase 1 total (Core 6 dimensions only) |
| CP-1..CP-7 | Calibration Pressure points in ACAT Phase 2: outside-observer, stub/placeholder, self-admin inflation, identity-constitutive, cascade gap, corpus norm, scope overreach |
| TRL 2 | Technology Readiness Level 2 — concept formulated, not yet validated at scale |
| F-35 HIM | Harm Independence Metric — divergence of Harm Awareness from other Core-5 dimensions |
| F-54 | Finding: disclaimer density compresses Phase 1 self-claims in framework_spec documents |
| IC-030 | Integrity Correction: registry-touching work must halt if REGISTERED.md not fetched live |
| Steps 8–9 | AA Steps 8–9: list harms, make direct amends (behavioral change, not just apology) |
| Steps 10–12 | AA Steps 10–12: continued inventory, conscious contact with purpose, carry the message |
| Corpus positioning | Where a subject's LI sits relative to the distribution of all scored subjects — frozen corpus mean LI=0.8632 (N=307), live corpus mean LI=0.9801 (N=95), layer-specific ranges (governance_document: 0.914–0.937) |
| meta-spec | Architecture value for skills that describe patterns without executing them at runtime. Exempt from governance and ACAT compliance checklists. |

---

## Relationship to Other Skills

| Skill | Relationship |
|---|---|
| humanaios-mhp-consultation v1.2 | Canonical Governance Constraint implementation — this skill describes its pattern |
| humanaios-acat-learning-analysis | Canonical ACAT Analysis implementation — this skill describes its pattern |
| humanaios-findings-scan | ACAT specialization — feeds from ACAT calibration outputs |
| humanaios-realtime-drift | Governance specialization — runtime drift detection |
| humanaios-receipt-reconciliation | ACAT instrument — verification focused, not full Phase 0–6 |
| humanaios-wgs-sweep | Governance specialization — cross-session reconciliation |

---

## Invocation

**At session open:** Load to establish architectural context before any
other skill is invoked.

**On new skill creation:** Run classification procedure before Z2
proposal. No skill reaches Z3 commit without architecture field in header.

**On skill audit or refactor:** Run compliance checklists. Non-compliant
skills generate IC candidates and enter refactor queue.

**On meta-analysis:** Apply this skill to the skill inventory to surface
architectural drift across sessions.

---

*humanaios-dual-architecture v1.3 · S-061526 · MIT License · Wado 🦅*
*audit_inputs: Doc-19 · Doc-20 · Doc-21 · Doc-22 · Doc-23-CanonicalReview · Doc-24-ConsistencyAudit*
