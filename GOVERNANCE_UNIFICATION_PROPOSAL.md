# Governance Unification Proposal — Foundation-Wide PR Ratification

**Date:** 2026-07-30  
**Authority:** empirica-foundation Admiral (Carly R. Anderson)  
**Decision Status:** Z2 RATIFIED  
**Scope:** All 10 foundation practices  
**Timeline:** Phase 1-3, go-live 2026-08-15

---

## Executive Summary

This proposal unifies governance across 10 foundation practices by making **GitHub PRs the canonical ratification mechanism** for all governance documents. Every governance change flows through:

1. **Discovery & Drafting** (Z1)
2. **Zone 2 Ratification Review** (authority approval via 5 gate questions)
3. **Merge & Registry** (decision recorded in GOVERNANCE_RATIFICATIONS_REGISTRY.yaml)
4. **Automated Deployment** (synced to all practices via mesh-sync-batch)
5. **Daily Audit** (divergence-detect verifies all practices applied changes)

---

## Participating Practices (10 total)

1. website
2. collaborator-ops
3. empirica-autonomy
4. empirica-mesh-support
5. empirica-outreach
6. flta-app-empirica
7. grok-crossref
8. humanaios
9. humanaios-internal
10. opportunity-aggregator

**Observer:** empirica-foundation-evaluator (objective, outside ratification)

---

## Design: Three-Document Specification

1. **GOVERNANCE_PR_TEMPLATE.md** — PR structure + 5 Z2 gate questions
2. **GOVERNANCE_PR_WORKFLOW_SPEC.md** — 5-stage workflow + authority matrix
3. **GOVERNANCE_CHANGE_PROCEDURES.md** — 4 procedures (new/minor/breaking/operational)

---

## Implementation Timeline

### Phase 1: Preparation (2026-08-01 to 08-07)
- Circulate proposal to 10 practices
- Collect feedback + designate Z2 authorities
- Finalize design

### Phase 2: Setup (2026-08-08 to 08-14)
- Deploy PR templates to all 10 repos
- Set up branch protection rules
- Deploy mesh-sync-batch + divergence-detect workflows
- Train practice leads

### Phase 3: Go Live (2026-08-15)
- Merge decision to operations repo
- Dispatch to all 10 practices simultaneously
- Verify 100% consistency

---

## Admiral Z2 Ratification

**Q1: Is this unification necessary & sufficient?** ✅ YES

**Q2: Does this align with existing authority model?** ✅ YES

**Q3: What's the rollout sequence?** Phased prep, all 10 synchronized go-live

**Q4: Are there edge cases?** Address when encountered, quarantine for assessment

**Q5: When should this take effect?** Immediate (effective 2026-07-30), Phase 3 go-live 2026-08-15

**Overall Decision:** ✅ Z2-RATIFIED
