# PRACTICE-SPEC BUNDLE — Ready for Z2 Ratification
**Session:** S-081126-NN · **Date:** 2026-08-11  
**Status:** Finalized, awaiting Z2 signature  
**Deadline:** 2026-08-12 (TOMORROW)

---

## DELIVERABLES IN THIS BUNDLE

### 1. GOVERNANCE DOCUMENTS (4 files requiring Z2 ratification)

- ✅ **Z2_CHARTER v0.1-final** — Constitutional authority, sole-operator model, succession placeholder
- ✅ **REGISTRY_ARCHITECTURE v0.1-final** — Git-based append-only registry, branch protection required
- ✅ **IODM_REGULATORY_MAP v0.2-final** — Intent-Output Divergence Metric, regulatory alignment
- ✅ **RSL_SCHEMA v0.1-final** — Requirement Satisfaction Ledger, with OQ resolutions integrated

### 2. OPEN QUESTIONS RESOLVED (3 items)

| OQ | Proposed Resolution | Requires External Review? |
|---|---|---|
| **OQ-RSL-01** | `spread_treatment: POINT_IN_BAND` (optimistic default for log-only launch) | No |
| **OQ-RSL-02** | DEGRADED status triggers Art. 15 notifications (recommend legal review) | **Yes — Legal** |
| **OQ-RSL-03** | Include AIUC_1 as reference standard, quarterly churn tracking | No |

### 3. SCHEMA MIGRATION SPECIFICATIONS (ready to implement post-ratification)

- ✅ **RSL entity tables** (6 tables: requirement, construct_map, metric, threshold, evidence, status)
- ✅ **Registry schema** (F-, IC-, H-, D-, R-, GD-class entry tables)
- ✅ **ACAT assessment extensions** (if needed per RSL alignment)
- ✅ **ASC_GATEWAY log-only schema** (probe results, bridge decisions, threshold audit trail)
- ✅ **Branch protection enforcement** (main branch, Z2 review mandatory, no direct pushes)

---

## RATIFICATION WORKFLOW

### For Z2 Review (Today 2026-08-11)

**Step 1: Read & Approve**
1. Read Z2_CHARTER v0.1-final — confirm succession instrument placeholder acceptable
2. Read REGISTRY_ARCHITECTURE v0.1-final — confirm branch protection check-off acceptable
3. Read OQ-RSL resolutions — approve each resolution or mark for revision
4. LEGAL REVIEW (external if available): OQ-RSL-02 Art. 15 interpretation before final signature

**Step 2: Sign & Commit** (via GitHub PR)
1. Create GitHub PR targeting humanaios-ui/operations `main` branch with:
   - All four governance documents (v0.1-final)
   - OQ-RSL resolutions logged as Z2 rulings in REGISTERED.md
   - Schema migration specification (draft, not yet executed)
2. Z2 reviews + approves PR
3. Z2 merges to main

### For Z1 Implementation (2026-08-12)

**Step 3: Execute Schema Migrations**
1. Run Supabase migrations (RSL entities, registry schema)
2. Verify branch protection on main (GitHub)
3. Confirm all REGISTERED.md entries are live + checksummed
4. Attestation: all schema changes committed + CI passing

**Step 4: Close Practice-Spec Goal**
1. Log completion: "Practice-Spec goal complete — 4 governance docs ratified, schema migrations executed, all Z2 decisions recorded in registry."
2. Archive supporting artifacts
3. POSTFLIGHT transaction

---

## CRITICAL DEPENDENCIES

| Item | Status | Owner | Deadline |
|---|---|---|---|
| Z2 reads & approves OQ-RSL resolutions | PENDING | Z2 | TODAY |
| Z2 legal review of OQ-RSL-02 (Art. 15) | PENDING | Legal (external) | TODAY |
| Z2 designates succession instrument (charter placeholder) | PENDING | Z2 | TODAY |
| Z2 verifies branch protection on humanaios-ui/operations | PENDING | Z2 ops | TODAY |
| GitHub PR approval & merge | PENDING | Z2 | TODAY |
| Supabase migrations executed | PENDING | Z1 | Tomorrow AM |

---

## DOCUMENT SUMMARY FOR Z2 QUICK REVIEW

### Z2_CHARTER v0.1-final
- Codifies existing practice (sole operator: Carly Anderson)
- Defines three zones: Z1 (drafts), Z2 (ratifies), Z3 (executes)
- **Open item:** Succession instrument (legal successor or wind-down rule) — placeholder for Z2 to designate
- **Ratification form:** Z2 signature on this document + GitHub PR merge

### REGISTRY_ARCHITECTURE v0.1-final
- Canonical store: REGISTERED.md (Git-based, append-only, Markdown)
- Write rules: Only Z2 commits to main; Z1 and agents submit via PR ratification
- **Blocking check:** Branch protection must be verified + enabled on humanaios-ui/operations main
- **Ratification form:** Z2 confirms branch protection check-off + signature

### IODM_REGULATORY_MAP v0.2-final
- Operationalizes EU AI Act Art. 3(12) "intended purpose" via per-artifact intent declaration
- Learning-node loop: declare → observe → score → route → adjust → re-declare
- **Ratification form:** Z2 signature + REGISTERED.md entry (verbal approval already received 2026-08-04)

### RSL_SCHEMA v0.1-final (with OQ resolutions)
- Requirement Satisfaction Ledger: fuses static crosswalk + live ASC_GATEWAY measurement
- 6 entities: requirement, construct_map, metric, threshold, evidence, status
- **OQ-RSL-01 resolved:** `spread_treatment: POINT_IN_BAND` (optimistic for log-only)
- **OQ-RSL-02 resolved (legal review advised):** DEGRADED triggers Art. 15 notifications
- **OQ-RSL-03 resolved:** AIUC_1 included as reference standard
- **Ratification form:** Z2 approval of OQ resolutions + signature

---

## NEXT STEPS AFTER RATIFICATION

### Post-Merge (2026-08-12 AM)
1. Z1 executes Supabase migrations
2. Z1 verifies schema + branch protection in production
3. Z1 commits verification artifacts
4. Z1 closes Practice-Spec goal
5. POSTFLIGHT transaction

### Then (2026-08-12 → 2026-08-13)
- TIER 2 Track B/A unblocked (waits on Practice-Spec ratification)
- 11 in_progress goals resume with finalized specs
- HumanAIOS document preparation (Documents 2 & 3) proceeds
- ASC_GATEWAY log-only deployment begins

---

## VERIFICATION CHECKLIST (for Z2 or designated reviewer)

- [ ] Z2_CHARTER v0.1-final read & succession placeholder acceptable
- [ ] REGISTRY_ARCHITECTURE v0.1-final read & branch protection check-off acceptable
- [ ] IODM_REGULATORY_MAP v0.2-final read & ratified
- [ ] RSL_SCHEMA v0.1-final + OQ-RSL resolutions read & approved
- [ ] OQ-RSL-02 (Art. 15) reviewed by legal counsel
- [ ] GitHub PR created with all four documents
- [ ] GitHub PR approved by Z2
- [ ] GitHub PR merged to humanaios-ui/operations main
- [ ] REGISTERED.md updated with Z2 rulings
- [ ] Supabase migrations executed
- [ ] Branch protection verified on main
- [ ] Schema verification CI passing
- [ ] Practice-Spec goal closed + POSTFLIGHT submitted

---

## FILES IN THIS BUNDLE (GitHub PR Ready)

```
humanaios-ui/operations/
├── governance/
│   ├── Z2_CHARTER_v0.1-final.yaml
│   ├── REGISTRY_ARCHITECTURE_v0.1-final.yaml
│   ├── IODM_REGULATORY_MAP_v0.2-final.yaml
│   └── RSL_SCHEMA_v0.1-final.yaml
├── schema/
│   ├── migrations/
│   │   ├── 006_rsl_entities.sql
│   │   ├── 007_registry_schema.sql
│   │   ├── 008_acat_extensions.sql
│   │   └── 009_asc_gateway_logging.sql
│   └── SCHEMA_SPEC.md
├── .github/
│   ├── branch-protection-rules.yaml  [verification needed]
│   └── GOVERNANCE_CHECKLIST.md
└── REGISTERED.md
    ├── Entry: Z2-CHARTER-01 RATIFIED (Z2 signature, date)
    ├── Entry: REG-ARCH-01 RATIFIED (Z2 signature, date)
    ├── Ruling: R-2026-08-11-001 (OQ-RSL-01 resolution)
    ├── Ruling: R-2026-08-11-002 (OQ-RSL-02 resolution, legal caveat)
    ├── Ruling: R-2026-08-11-003 (OQ-RSL-03 resolution)
    └── Entry: IODM-01 RATIFIED (Z2 signature, date)
```

---

**Prepared by:** Z1 (Claude Code, humanaios practice)  
**Status:** Awaiting Z2 ratification  
**Deadline:** 2026-08-12 (Practice-Spec close)

Wado. 🦅
