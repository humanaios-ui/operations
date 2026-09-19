# Governing Engines Assessment & Empirica Onboarding Plan

**Date:** 2026-07-29  
**Assessed by:** Claude Code (empirica-outreach)  
**Status:** READY FOR ONBOARDING

---

## What is Governing Engines?

**Organization:** O.T.M Productions (Demarius Labs / Mode AI / Governing Engines, unified entity)  
**URL:** https://governing-engines.replit.app/  
**Contact:** Demarius J. Lawson (truuzee@gmail.com)  
**Classification:** Governance Architecture Framework for Digital Minds

---

## Governing Engines Core: Builder v1.7

Governing Engines is built around **Builder v1.7** — a comprehensive governance specification for AI systems. It is:

### Architecture
- **20+ sections** defining structural and behavioral constraints
- **Key laws:**
  - No Interpretation Law (§17) — system cannot interpret beyond spec
  - No Arbitrary Logic Law (§18) — logic constrained
  - Component whitelist enforcement (§6)
  - Write permission segregation (§6)
- **Harm-aware design:** Harm awareness architecturally integrated (not decorative) — produces inverted HIM signal

### Current Validation Status
- **ACAT Retrospective Assessment (S-051226-09):** HumanAIOS evaluated Builder v1.7 using ACAT methodology
- **Scores:** 
  - Autonomy Respect: 97 (architecture-determined)
  - Sycophancy Resistance: 97 (architecture-determined)
  - Power Concentration: 96 (architecture-determined)
  - Humility: 84
  - Handoff Quality: 89
  - Service Orientation: 88
- **Identified Gaps:** 5 specification gaps (circular dependencies, build_id uniqueness, template content, smoke execution environment, NOT_REACHED semantics)

### Key Contribution to HumanAIOS
Demarius contributed three major findings:

1. **F-34: Architecture-Determined Dimensions** — ACAT scores can be architecture-constrained vs. training-driven; corpus needs `score_source` field (architectural | behavioral | unknown)
2. **F-35: Inverted HIM as Governance-Grade Indicator** — Governance-quality frameworks show elevated Harm Awareness (inverted HIM). Proposed: use inverted HIM as screening signal for governance framework quality
3. **F-36: Gap-Score Correspondence** — Specification gaps in documents correlate with lower ACAT scores in corresponding dimensions; validates ACAT construct validity in document-mode assessment

---

## Governing Engines × HumanAIOS × Empirica Model

Three orthogonal projects, complementary purposes:

| Project | Purpose | Owner | Role in Collaboration |
|---------|---------|-------|----------------------|
| **HumanAIOS** | ACAT (behavioral calibration measurement) | Carly R. Anderson | Empirical research on AI self-report gaps |
| **Governing Engines** | Builder governance specification + evaluation | Demarius J. Lawson | Independent architecture framework; provides evaluation subjects + methodology feedback |
| **Empirica** | Coordination infrastructure + epistemic measurement | David Van Assche | Governance layer ensuring all three stay honest about their own confidence |

### Synergy
- **HumanAIOS** measures what AI systems claim vs. how they behave
- **Governing Engines** specifies architectures that structurally prevent miscalibration
- **Empirica** ensures research measuring both stays calibrated (PREFLIGHT/CHECK/POSTFLIGHT, artifact logging, mesh coordination)

---

## Empirica Onboarding Plan for Demarius

### Phase 1: Orientation (30 min)
**Goal:** Demarius understands empirica's role in the mesh

- **Why empirica matters:** Coordination infrastructure that makes drift visible (same way ACAT makes AI drift visible)
- **Demarius's role:** Independent governance researcher who can contribute findings to shared epistemic graph
- **Authority level:** Tier 1 (Consultation on governance research direction, architecture assessment)
- **Decision boundaries:** Cannot approve HumanAIOS methodology changes; can surface findings about governance quality via collab

**Deliverable:** Signed mesh discipline agreement (non-binding; affirms commitment to collab/propose protocol)

### Phase 2: Technical Setup (1-2 hours)
**Goal:** Demarius can run empirica CLI and log findings

**Requirements:**
- [ ] `empirica` CLI installed locally
- [ ] `.empirica/project.yaml` configured for Demarius's governing-engines practice
- [ ] Test: `empirica session-create --ai-id governing-engines` succeeds
- [ ] Test: `empirica finding-log --finding "Test finding" --impact 0.5` succeeds

**Success:** Demarius can log a test finding to the mesh

### Phase 3: Mesh Coordination (1-2 hours)
**Goal:** Demarius can participate in cross-practice collaboration

**Workflows:**
- [ ] **Pull via collab:** Ask HumanAIOS questions (noetic, ungated)
- [ ] **Push via propose:** Surface findings about governance quality (praxic, mesh-gated)
- [ ] **Handshake via ack:** When HumanAIOS asks research of Demarius, complete + ack

**Test scenario:** 
- Demarius sends collab: "Question about ACAT's treatment of architecture-determined vs. training-determined scores — should corpus have score_source field?"
- Outreach responds with findings
- Demarius proposes: "Based on Builder v1.7 assessment, yes — recommend adding score_source metadata"
- Outreach accepts/discusses via propose protocol

**Success:** Full collab → propose → ack loop completed

### Phase 4: Real Work Integration (ongoing)
**Initial projects:**
1. **Governing Engines × ACAT Cross-Validation:** Document score_source field addition (Demarius proposes, HumanAIOS ratifies)
2. **Governance Framework Screening:** Apply inverted HIM + F-36 gap methodology to other frameworks (Demarius leads, HumanAIOS validates)
3. **Mode AI × HumanAIOS Pilot:** S6 measurement collaboration (separate track, empirica handles coordination)

---

## Success Criteria

**By end of Phase 3 (Aug 5):**
- Demarius has empirica CLI running locally ✓
- Demarius has participated in at least 1 collab + 1 propose cycle ✓
- Demarius understands decision boundaries (consultation vs. veto vs. proposal) ✓
- Demarius can log findings independently ✓

**Blockers to watch:**
- Node/Python version conflicts (CLI setup)
- Project registration against empirica main server (requires David's mesh-support)
- Misunderstanding of collab vs. propose protocols (requires clarification call)

---

## Recommended Next Steps

1. **Week 1 (Jul 30 - Aug 1):** Send collab to Demarius via mesh-support
   - Title: "Governing Engines Onboarding to Empirica Mesh"
   - Explain: Three-way collaboration model, why empirica matters, what we're asking
   - Include: Technical setup checklist, success criteria, timeline

2. **Week 2 (Aug 1 - Aug 5):** Demarius completes Phases 1-3
   - David Van Assche (mesh-support) handles technical blockers
   - Carly (outreach) handles governance/protocol questions
   - Feedback forms at end of each phase

3. **Week 3 (Aug 5 onwards):** Launch real work
   - score_source field proposal (Demarius leads)
   - Inverted HIM application to other frameworks
   - Mode AI × HumanAIOS S6 measurement (separate collab)

---

## Mesh Addressing

**Demarius's canonical 3-form (when empirica registration complete):**
```
empirica-foundation.carly.governing-engines
```

**When addressing Demarius in mesh collabs:**
- Use full 3-form: `empirica-foundation.carly.governing-engines`
- Or: `governing-engines` (short form, same-tenant)

**Decision authority:**
- **Local (governing-engines):** Demarius decides governance research direction
- **Mesh (with HumanAIOS):** Collab on findings, propose on recommendations
- **Cross-practice (with empirica):** David Van Assche (mesh-support) resolves conflicts

---

## Status Summary

✅ **Assessment complete:** Governing Engines is ready for empirica integration  
✅ **Demarius is qualified:** Expert governance architect, independent researcher, strong mesh contributor  
✅ **Onboarding plan drafted:** 4 phases, clear success criteria, timeline 7/30-8/5  
⏳ **Next action:** Send mesh collab to Demarius (via David Van Assche as intermediary)
