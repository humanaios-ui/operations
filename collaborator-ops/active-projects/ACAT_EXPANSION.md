# Active Project: ACAT Expansion & Benchmark Development

**Lead:** Carly R. Anderson  
**Status:** In Progress (foundational work; full ramp pending Longview decision)  
**Timeline:** Months 1-6 (within Longview 18-month program, OR continue independently)  
**Collaborators:** Demarius Labs (evaluation), Mode AI (in-kind support)

---

## Project Overview

Expand ACAT (AI Calibrated Assessment Tool) beyond current model families to multimodal, reasoning-optimized, and novel architectures. Develop benchmark suite for community adoption.

---

## Scope & Deliverables

### Phase 1: New Model Families (Months 1-3)
- **Multimodal models:** [CARLY TO LIST: which models? Vision-language? Audio?]
- **Reasoning-optimized:** [Which architectures? o1? DeepSeek?]
- **Novel architectures:** [Any emerging models to assess?]
- **Evaluation partner:** Demarius Labs conducts robustness assessment

**Deliverable:** ACAT evaluation results for ≥5 new model families

### Phase 2: Task Set Development (Months 3-5)
- **Sentience-focused tasks:** [CARLY TO DESIGN: which hypothesis-testing tasks?]
- **Welfare-assessment tasks:** [Which behavioral indicators?]
- **Calibration robustness tasks:** [Pressure/ambiguity stress tests]

**Deliverable:** 3+ validated task sets with scoring rubrics

### Phase 3: Benchmark Suite & Public Release (Month 6)
- **Code:** Cleaned, documented ACAT implementation
- **Data:** All evaluation results (35+ existing + new models)
- **Documentation:** User guide, methodology, reproduction instructions
- **Benchmark page:** Leaderboard + submission process for external teams

**Deliverable:** Public-facing benchmark suite (GitHub + HuggingFace)

---

## Success Criteria

- [ ] ≥5 new model architectures evaluated successfully
- [ ] Benchmark adopted by ≥2 external research teams within 6 months of release
- [ ] Zero methodological issues flagged in peer review
- [ ] Community engagement (≥10 external submissions to benchmark within first quarter)

---

## Collaborators & Roles

| Name | Role | Org | Contribution | Sync Cadence |
|------|------|-----|--------------|--------------|
| Carly R. Anderson | Lead Researcher | HumanAIOS | ACAT design, task development, writing | — |
| Demarius J. Lawson | Evaluation Partner | Demarius Labs | Robustness assessment, architecture feedback | Monthly |
| Mode AI | In-kind Support | Mode AI | Compute resources?, early model access? | As-needed |
| Junior Researcher | Implementation Support | HumanAIOS | [CARLY TO FILL: code, data processing] | [TBD] |

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **New model API access blocked** | Evaluation impossible | Backup: evaluate only open-weight models |
| **Reasoning models too expensive** | Budget overrun | Cap evaluation cost; prioritize highest-impact models |
| **Task design complexity** | Timeline slip | Start task design Month 2 (parallel with Phase 1) |
| **External adoption slow** | Impact reduced | Marketing push: papers, talks, community outreach |

---

## Budget Allocation (Pending Longview Award)

**Compute & Infrastructure (Longview allocation: $40K/year for all initiatives)**
- Model API costs: [CARLY TO ESTIMATE: $X/month for new evals]
- Benchmark infrastructure: Supabase, GitHub Pages, HuggingFace hosting (est. $X/month)

**Personnel:**
- Carly: [X% of 0.6 FTE]
- Junior researcher: [X% of 0.5 FTE]

---

## Timeline & Milestones

| Month | Task | Owner | Deliverable | Status |
|-------|------|-------|-------------|--------|
| 1 | Model family selection + access | Carly | List of 5-7 target models | Planned |
| 1-2 | ACAT infrastructure setup | Junior | Scalable eval pipeline | Planned |
| 2-3 | Initial evaluations (Demarius review) | Carly + Demarius | Robustness report | Planned |
| 3 | Task set design review | Carly + Demarius | Draft task sets | Planned |
| 3-5 | Full evaluation suite | Carly + Junior | Complete results for all models | Planned |
| 5-6 | Benchmark packaging + docs | Junior + Carly | Public release package | Planned |
| 6 | Launch + community outreach | Carly | Benchmark live + paper ready | Planned |
| 7 | Paper 1 submitted | Carly | "ACAT Benchmark Expansion" | Planned |

---

## Communication & Governance

**Lead Authority:** Carly (day-to-day decisions)

**Consultation Points:**
- Demarius (Months 2-3) on robustness assessment methodology
- Demarius (Month 3-4) on task set validation
- Mode AI (as-needed) on compute/model access

**Decision Log:** Logged in parent Longview project file

---

## Current Status

**[CARLY TO FILL: What's been done pre-Longview?]**
- Existing ACAT: 35+ models evaluated ✓
- Existing dataset: Public on HuggingFace ✓
- Next: Expand to new architectures (pending Longview funding)

---

## Notes

- This project can proceed independently of Longview funding (at reduced scope)
- Strong collaboration with Demarius Labs de-risks methodology
- Benchmark adoption is key for impact (not just publication)
