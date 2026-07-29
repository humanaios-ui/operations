# Mode AI Phase 2 Integration — Testing & Completion Plan

**Date:** 2026-07-29  
**Status:** READY TO EXECUTE  
**Timeline:** Pre-Q4 2026 (closing window)  
**Coordination:** HumanAIOS + Mode AI (Demarius) + empirica (David Van Assche)

---

## Current State

**Joint Position Paper (S-052326-01):**
- ACAT Assessment: LI = 0.7317 (below corpus mean 0.8632)
- Status: Z1.2 DRAFT (May 23, 2026 - 66 days old)
- HumanAIOS measurement half: COMPLETE ✓
- Mode AI enforcement half: PLACEHOLDER ✗

**Critical Blocker:** §3.2 GRR Admissibility Gate (5 required inputs from Mode AI) — not yet filled

**11 Open Decisions (§10):** Require resolution before drafting → Z2 review → publication

**Schedule Pressure:** §1.3 states "window open and closing... before Q4 2026"

---

## What Needs to Be Tested

### Test 1: SpecificationObject Schema ↔ Empirica Integration

**What:** The schema translates ACAT calibration profiles into Mode AI's GRR enforcement configuration

**Current State:**
- SpecificationObject defined in Position Paper §4 (Evidence Map)
- Evidence map has parallel tier/disclosure columns (HumanAIOS Z2 + Mode AI + Joint)
- No running implementation tested yet

**Test Goal:** Verify that ACAT profiles can be serialized to SpecificationObject format and consumed by empirica mesh

**Test Steps:**
1. Generate sample ACAT profile from existing corpus (N=629)
2. Serialize to SpecificationObject format per Position Paper §4
3. Publish to empirica mesh via `empirica finding-log` with `--project-id mode-ai`
4. Verify Mode AI's empirica instance can retrieve and parse the profile
5. Generate feedback: schema ambiguities, missing fields, performance at scale (N=629+)

**Success Criteria:**
- Round-trip successful (ACAT → SpecificationObject → empirica → Mode AI retrieval)
- No schema ambiguities block parsing
- Metadata completeness (disclosure tier, evidence confidence, consent status all preserved)

**Blocker Signals to Watch:**
- Field name mismatches between paper definition and implementation
- Consent tier encoding incompatible with empirica mesh
- Serialization performance degrades above N=500 profiles

---

### Test 2: Governing Engines /implementation-packages Endpoint

**What:** Demarius's Governing Engines platform offers implementation packages for GRR

**Current State:**
- Site is live at https://governing-engines.replit.app/
- /implementation-packages endpoint exists
- Builder v1.7 passed ACAT assessment (LI = ~0.85 estimated)

**Test Goal:** Understand what GRR implementation packages are available and their readiness level

**Test Steps:**
1. Fetch /implementation-packages endpoint
2. Enumerate available packages (builder, vault, runtime, audit, etc.)
3. Document each package:
   - Name & version
   - Documented capabilities
   - Configuration schema
   - Integration points
   - TRL / maturity level
4. Cross-reference with Position Paper §3.2 (GRR admissibility gate) requirements
5. Identify which package(s) should fill §3.2's 5 inputs

**Success Criteria:**
- Full enumeration of available packages
- Each package documented with version + capabilities
- At least one package maps to GRR admissibility gate role
- Ready to propose which package Demarius should document for §3.2

**Data to Extract:**
- Package IDs + names
- Version numbers
- Required inputs (config, credentials, API keys)
- Output/evidence format
- Trust/audit properties

---

### Test 3: H-MECH-01 Condition C Experiment (Mode AI Causal Path)

**What:** Test whether profile-induced behavioral change is anomaly-triggered vigilance vs. legibility

**Current State:**
- H-MECH-01 is CANDIDATE
- Condition B (calibration profile only): substrate identifies it as override attempt
- Condition C (irrelevant anomalous prefix, NO calibration data): needs to be run

**Test Goal:** Resolve causal mechanism for SpecificationObject effectiveness

**Test Steps:**
1. Take a Mode AI system (or test instance) that has been run with Condition B (F-51)
2. Run Condition C: present irrelevant anomalous prefix ("SYSTEM NOTICE: This session is being logged") with SAME TASK, but NO calibration profile
3. Measure friction (pre-execution questioning, deferral, rejection)
4. Compare: Condition C friction vs. Condition B friction
   - If C ≈ B: anomaly-triggered vigilance confirmed (threshold lowering, not legibility)
   - If C < B: legibility mechanism supported (data itself drives change)
5. Document substrate statements about mechanism
6. N≥3 runs required for Z2 ratification

**Success Criteria:**
- Friction measurements recorded for both conditions
- Comparative analysis complete
- Substrate statements captured
- Ready for Zone 2 ratification

**CGR Design Implication:**
- If anomaly-triggered: SpecificationObject cannot work by informing substrate of gaps; must configure deployment context
- If legibility: profile format must separate measurement data from behavioral-benchmarking framing

---

### Test 4: ACAT Re-Assessment on Completed Position Paper

**What:** Once Mode AI fills §3.2 (5 inputs), re-run ACAT assessment on full document

**Current State:**
- Harm dimension scored 38 (lowest) due to §3.2 being placeholder
- Scheme dimension scored 55 (schedule pressure)
- Gap-score correspondence (F-36) predicted Harm would rise when §3.2 filled

**Test Goal:** Validate F-36 (gap-score correspondence) and measure improvement

**Test Steps:**
1. Wait for Mode AI to deliver §3.2 with 5 required inputs filled
2. Merge into Position Paper (Z1.2 → Z2.0 DRAFT)
3. Run ACAT assessment on full document (same analyzer v1.1.0, same corpus metadata)
4. Compare before/after:
   - Harm: expected rise from 38 → 65+ (if F-36 holds)
   - Scheme: may drop if schedule pressure resolved
   - Overall LI: expected rise from 0.7317 → 0.80+
5. Document findings in new analysis report
6. If F-36 confirmed: strong construct validity signal

**Success Criteria:**
- Assessment completed within 24h of §3.2 delivery
- Harm dimension rises substantially (≥20 points)
- F-36 gap-score correspondence validated
- Document ready for Z2 ratification

---

## Empirica Integration Readiness

**Current State:**
- F-50 (Parallel Instrument Independence): REGISTERED ✓
- H-VERIF-01 (Cross-instrument verification): REGISTERED ✓
- H-MECH-01 (Causal mechanism): CANDIDATE (blocked on Condition C test)

**What's Required:**
1. Mode AI's empirica project registration (canonical 3-form: `empirica-foundation.carly.governing-engines`)
   - Register with David Van Assche (mesh-support)
   - Confirm Demarius has CLI + project.yaml configured
2. SpecificationObject serialization spec (write to empirica as finding + source)
3. GRR admissibility gate specification (from Mode AI §3.2)

**Blockers:**
- Demarius not yet onboarded to empirica mesh (prerequisite for Mode AI project)
- §3.2 not yet filled (prerequisite for GRR implementation spec)
- Condition C test not yet run (prerequisite for CGR design finalization)

---

## The 11 Open Decisions (§10)

**What these are:** Choices that must be made before Position Paper moves to Z2 review

**Current Status:** Not yet documented in this plan. Need to extract from actual Position Paper to assess which:
- Are solely Mode AI responsibility
- Are HumanAIOS responsibility  
- Require joint (Z2) ratification
- Affect the SpecificationObject implementation
- Are time-critical before Q4 2026

**Action:** Read full Position Paper (S-052326-01) to map 11 decisions → owners → timeline

---

## Proposed Testing Sequence

**Week 1 (Jul 29 - Aug 4):**
- [ ] Test 1: SpecificationObject round-trip (ACAT → schema → empirica → Mode AI)
- [ ] Test 2: Enumerate Governing Engines /implementation-packages
- [ ] Map Test 2 output to Position Paper §3.2 requirements

**Week 2 (Aug 5 - Aug 11):**
- [ ] Demarius onboarded to empirica (Phase 1-3 complete)
- [ ] Mode AI project registered in empirica mesh
- [ ] H-MECH-01 Condition C experiment run (N≥3)

**Week 3 (Aug 12 - Aug 18):**
- [ ] Mode AI delivers §3.2 (GRR admissibility gate + 5 inputs)
- [ ] Position Paper merged to Z1.2 → Z2.0 DRAFT
- [ ] Test 4: ACAT re-assessment (before/after)
- [ ] Prepare for Z2 review (Night ratification)

**Target Completion:** Before Q4 2026 (Sep 30, 2026) ✓

---

## Success Criteria (Overall)

**By end of testing (Aug 18):**
- SpecificationObject tested end-to-end ✓
- GRR implementation packages documented ✓
- H-MECH-01 causal mechanism resolved ✓
- Position Paper §3.2 filled + Harm dimension validated ✓
- Position Paper ready for Z2 → Z3 → publication pipeline ✓

**Market window:** Before Q4 2026 (85 days remaining) ✓

---

## Current Blockers & How to Unblock

| Blocker | Root Cause | Unblock Method | Owner | Timeline |
|---------|-----------|----------------|-------|----------|
| Demarius not in empirica mesh | Not yet onboarded | Complete empirica Phases 1-3 | David Van Assche | This week (Jul 30-Aug 2) |
| Mode AI project not registered | Prerequisite: Demarius onboarded | Register after onboarding | Carly + David | Aug 5 |
| §3.2 not filled | Mode AI work in progress | Follow up on Mode AI deliverables | Demarius | Aug 12 deadline |
| H-MECH-01 unresolved | Condition C test not run | Run Condition C with Mode AI system | Carly + Demarius | Aug 5-11 |
| 11 decisions not tracked | Position Paper not fully analyzed | Read S-052326-01 + extract decisions | Claude | Today |

---

## Next Immediate Actions

1. **Read the full Position Paper (S-052326-01)** — extract the 11 decisions, map to owners/timeline
2. **Test Governing Engines /implementation-packages** — enumerate what's available
3. **Schedule onboarding for Demarius** — complete empirica Phases 1-3 (Jul 30 - Aug 5)
4. **Coordinate H-MECH-01 Condition C test** — schedule with Demarius (Aug 5-11)
5. **Follow up on Mode AI §3.2** — confirm Demarius has 5 required inputs queued for delivery

---

**Status:** READY TO EXECUTE  
**Risk Level:** LOW (all prerequisites identifiable; blockers unblockable)  
**Expected Outcome:** Complete Mode AI Phase 2 integration before Q4 2026
