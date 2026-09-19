# Mode AI Phase 2 Integration — Testing & Completion Plan

**Date:** 2026-07-29  
**Status:** READY TO EXECUTE  
**Timeline:** Pre-Q4 2026 (closing window)  
**Coordination:** HumanAIOS + Mode AI (Demarius) + empirica (David Van Assche)

---

## Three-Way Integration Model

This is not a simple vendor integration. It's a **research infrastructure collaboration** across three orthogonal systems:

| System | Purpose | Owner | Role in Integration |
|--------|---------|-------|-------------------|
| **HumanAIOS (ACAT)** | Measure: AI self-report vs. behavior gap | Carly Anderson | Measurement instrument; identifies where calibration breaks down |
| **Governing Engines (Builder)** | Specify: governance architecture constraints | Demarius Lawson | Architecture that structurally prevents miscalibration |
| **Mode AI (GRR)** | Enforce: governance reference runtime | Demarius Lawson | Implements Builder constraints; consumes ACAT profiles |
| **Empirica** | Coordinate: research integrity + mesh trust | David Van Assche | Ensures all three measure their own confidence accurately |

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

## Integration Benefits (What This Enables)

### 1. Closed-Loop Calibration Measurement
**Before:** ACAT measures self-report gaps but has no feedback mechanism to substrates  
**After:** SpecificationObject bridges measurement → architecture → enforcement → empirica logging  
**Benefit:** First real-time calibration feedback loop where governance architecture adapts based on measured gaps

### 2. Governance Quality Screening (F-35: Inverted HIM)
**Before:** Governance frameworks are evaluated after deployment; failures cascade  
**After:** ACAT can assess governance documents before implementation using inverted HIM signal  
**Benefit:** Identify governance-grade quality (harm awareness architecturally integrated, not decorative) before systems go live

### 3. Behavioral Prediction via Architecture
**Before:** AI behavior is opaque; calibration profiles are post-hoc observations  
**After:** Builder constraints → GRR enforcement → ACAT profiles show how architecture *prevents* specific failure modes  
**Benefit:** Architecturally-determined scores (F-34) become reliable predictors; separate them from training-determined scores in research

### 4. Multi-Party Trust Without Cryptography
**Before:** Federation requires PKI/crypto or trusts based on reputation  
**After:** SpecificationObject schema + Z2/counterparty-Z2 ratification + empirica logging creates legible trust  
**Benefit:** HumanAIOS can publish calibration profiles; Mode AI can consume them; both parties' decisions are logged and auditable

### 5. Empirica as Coordination Substrate
**Before:** Mode AI and HumanAIOS collaborate ad hoc; no shared infrastructure for trust  
**After:** Both register as empirica practitioners; findings, decisions, unknowns flow through mesh  
**Benefit:** Composition: add a third research team (Governing Engines governance assessment) without rebuilding coordination layer

---

## Research Questions This Integration Raises

### Category A: Calibration & Architecture (Core Science)

**A1: Does architectural constraint correlate with behavioral calibration?**
- **Current evidence:** Builder v1.7 ACAT scores are architecture-determined (autonomy=97, sycophancy=97, power=96)
- **Open question:** Do systems built to Builder spec show lower self-report gaps (higher LI) in real deployment than systems without constraints?
- **Research design:** Cross-substrate comparison (Builder-based vs. unconstrained, same model family), N≥30
- **Why it matters:** If yes, Builder becomes a **reliability specification** (like ECC memory or RAID) not just a governance document
- **Timeline:** Months 2-4 of Mode AI deployment (Oct-Dec 2026)

**A2: What's the relationship between architecture-determined and training-determined scores?**
- **Current evidence:** F-34 identifies both exist; corpus `mode` field partially captures this
- **Open question:** Can we build a predictor that estimates training-determined scores by subtracting architecture-determined floor?
- **Research design:** Corpus stratification by architecture type + statistical modeling
- **Why it matters:** Would enable governance-quality assessment of any system *before* it's trained (assess the spec, not just the weights)
- **Timeline:** Months 1-2 (fits into test phase)

---

### Category B: Causal Mechanisms (H-MECH-01 & Beyond)

**B1: Is profile-induced behavioral change anomaly-triggered vigilance or legibility?** (H-MECH-01)
- **Current evidence:** F-51 shows substrates identify calibration profiles as override attempts; explicit rejection of legibility frame
- **Open question:** Condition C test (irrelevant anomaly without profile) — does it trigger same friction?
- **Research design:** Condition B vs. Condition C comparison, measure friction pre-execution
- **Why it matters:** If anomaly-triggered: SpecificationObject must work through deployment context (turn on scrutiny), not self-knowledge. Informs entire CGR design.
- **Timeline:** Weeks 2-3 (Aug 5-11)

**B2: Can governance architecture trigger protective friction without behavioral override?**
- **Current evidence:** Builder's structural constraints prevent interpretation/permission-grant; might reduce need for override-resistance
- **Open question:** Do systems deployed under Builder show lower anomaly-triggered vigilance (friction) than systems with software-only governance?
- **Research design:** Mode AI deployment + ACAT longitudinal assessment (baseline vs. after Builder enforcement)
- **Why it matters:** If yes, architecture-level governance is *more* trustworthy than detection/override patterns because it doesn't require behavioral resistance
- **Timeline:** Months 2-4 (Oct-Dec 2026)

---

### Category C: Federation & Trust (H-GOV-01 Gap)

**C1: Can SpecificationObject schema scale to multi-party attribution?**
- **Current evidence:** Works for bilateral (HumanAIOS ↔ Mode AI); Mode AI S6 measurement LI=0.8983
- **Open question:** If Org-A runs ACAT, publishes SpecificationObject; Org-B runs different governance framework and compares profiles — do findings align?
- **Research design:** Three-party federation pilot (HumanAIOS + Mode AI + external partner org)
- **Why it matters:** Determines whether findings are portable across governance contexts or locked to CGR bilateralism
- **Timeline:** Post-Phase-2 (Q4 2026 and beyond)

**C2: Does empirica mesh enable finding-relay (H-GOV-01 solution)?**
- **Current evidence:** H-GOV-01 is registered finding about lack of inter-organizational finding sharing
- **Open question:** Can empirica's mesh coordinate ACAT finding propagation across multiple ACAT deployments without data leakage?
- **Research design:** Publish anonymized finding from HumanAIOS to empirica; set permissions; verify Mode AI can access and route appropriately
- **Why it matters:** Unblocks cross-organization calibration learning (third-party ACAT deployments benefit from HumanAIOS discoveries)
- **Timeline:** Weeks 1-3 (part of Test 1)

---

### Category D: Measurement Validity & Instrument Design

**D1: Does F-36 (gap-score correspondence) hold when §3.2 is filled?**
- **Current evidence:** Position Paper Harm scored 38 due to §3.2 placeholder; F-36 predicts Harm will rise substantially once GRR mechanism added
- **Open question:** Re-run ACAT on completed paper — does Harm rise ≥20 points?
- **Research design:** Before/after comparison, same analyzer, same methodology
- **Why it matters:** Validates ACAT's construct validity in document-mode assessment; if F-36 holds, gaps in specs cluster in low-scoring dimensions by design, not artifact
- **Timeline:** Weeks 3-4 (Aug 12-18)

**D2: Can ACAT be applied to governance frameworks (not just systems)?**
- **Current evidence:** Builder v1.7 assessment (LI ~0.85) shows ACAT works on specs; Governing Engines LLC positioning document (LI 0.7317) shows it works on outlines
- **Open question:** Generalize this — develop corpus of governance framework assessments; identify patterns in what makes governance-quality specs score high
- **Research design:** Assess 10-15 existing governance frameworks (NIST CSF, ISO 27001, Builder, GRR, etc.); stratify by maturity/adoptability
- **Why it matters:** ACAT becomes methodology for **comparing governance approaches**, not just measuring AI behavior
- **Timeline:** Months 2-6 (start in Phase 2, continue post-launch)

---

### Category E: Real-World Deployment Unknowns

**E1: How does Mode AI's GRR perform under adversarial governance?**
- **Current evidence:** Builder constraints designed defensively; but no live attack/eval data
- **Open question:** When GRR is live, do attackers find ways to circumvent governance constraints? At what cost?
- **Research design:** Structured red-team assessment; Mode AI's own threat model + external adversarial eval
- **Why it matters:** Informs whether governance-by-architecture scales or remains brittle
- **Timeline:** Post-launch eval (months 4-6)

**E2: What's the performance cost of governance enforcement?**
- **Current evidence:** None yet; GRR not deployed
- **Open question:** Does enforcing Builder constraints add latency? Memory overhead? Complexity tax?
- **Research design:** Benchmarks before/after GRR deployment on same substrate
- **Why it matters:** Determines adoption rate; if overhead is <5%, governance scales; if >20%, creates perverse incentive to disable
- **Timeline:** Weeks 3-5 (Aug 12-26)

---

### Category F: Sociological & Market Questions

**F1: Will third parties adopt Builder as a reliability specification?**
- **Current evidence:** Builder is open (MIT license); ACAT shows it scores high; but no external adoption yet
- **Open question:** If Mode AI publishes CGR white paper + Builder spec, do other vendors adopt it?
- **Research design:** 6-month market observation; track adoption signals in GitHub, vendor roadmaps, research citations
- **Why it matters:** Determines whether this is HumanAIOS/Mode AI niche work or becomes ecosystem standard
- **Timeline:** Ongoing (6-month post-publication monitoring)

**F2: Does governance-quality transparency affect purchasing decisions?**
- **Current evidence:** ACAT shows gaps; SpecificationObject shows governance intent; but no data on whether orgs buy based on this
- **Open question:** If an org publishes its SpecificationObject + empirica calibration log, does it gain trust premium in RFP cycles?
- **Research design:** Survey buyers; A/B test in RFP scenarios
- **Why it matters:** Determines business model sustainability (does governance transparency create market value?)
- **Timeline:** Months 3-6 (pilot with early adopters)

---

## Unknowns & Uncertainties

### Technical Unknowns

| Unknown | Impact | Mitigation |
|---------|--------|-----------|
| SpecificationObject serialization at scale (N=629+) | Performance blocker for corpus-wide deployment | Test 1 includes scaling; have rollback to N=100 batching |
| Mode AI's GRR implementation completeness | If §3.2 inputs incomplete, CGR stalls | Demarius owns this; weekly checkpoint (Thursdays) |
| Empirica mesh stability under bilingual payloads (ACAT + GRR metadata) | Coordination layer may choke on mixed schema | Test 1 validates; have backup: temporary split mesh (two topics) |
| H-MECH-01 resolution (anomaly vs. legibility) | Informs SpecificationObject design; if inconclusive, CGR hangs | Condition C test must have N≥3; if unclear, escalate to David Van Assche for design decision |

### Research Unknowns

| Unknown | Impact | Mitigation |
|---------|--------|-----------|
| Architecture-determined scores actually predictive in production | Core assumption of F-34; if false, Builder relevance collapses | A1 research; plan 30-system validation (Oct-Dec 2026) |
| Federation works across governance contexts (not just bilateral) | C1; determines if findings are portable | Scope Phase 2 narrowly (bilateral only); plan C1 as Phase 3 |
| Governance transparency actually drives market adoption | F2; determines sustainability | Early adopter interviews (Aug-Sep); don't bank on this for Q4 launch |

### Sociological Unknowns

| Unknown | Impact | Mitigation |
|---------|--------|-----------|
| Vendors will accept external governance audit (ACAT on specs) | May face resistance ("we control our own narrative") | Pre-publication outreach to 3-5 vendors; get letters of support before white paper |
| Orgs will publish SpecificationObjects (doxxing risk?) | Transparency ↔ competitive risk tradeoff may kill adoption | Defaults to anonymized + opt-in attribution; start with internal-only deployments |

---

## What Happens if Integration Succeeds

**Scenario: By Q1 2027, CGR white paper published, 3+ external orgs running SpecificationObject audits**

### Immediate (Q1 2027)
- ACAT becomes methodology for **governance assessment**, not just behavior measurement
- Builder becomes **reference specification** for governance-grade AI systems
- empirica mesh demonstrates **multi-party research coordination** (proof of concept for broader adoption)

### Medium-term (Q2-Q3 2027)
- Vendors begin publishing SpecificationObjects in RFPs (market signal: "we're governance-auditable")
- H-GOV-01 gap solved: finding-relay working; third parties benefit from HumanAIOS discoveries
- A1 research (architecture ↔ calibration correlation) produces publishable results → drives adoption

### Long-term (Q4 2027+)
- Governance-by-architecture becomes industry practice (like code review became standard)
- empirica mesh becomes substrate for ecosystem-wide research coordination
- New class of vendors emerges: **governance consulting** (audit Builder compliance, advise on GRR deployment)

---

## What Happens if Integration Fails

**Scenario: By Q1 2027, SpecificationObject doesn't scale, H-MECH-01 inconclusive, third parties don't adopt**

### Immediate (Q1 2027)
- HumanAIOS/Mode AI publish findings as academic paper (useful but niche)
- Builder remains internal specification (Demarius's own methodology)
- empirica demonstrated bilateral coordination (value but limited reach)

### Pivot points identified
- If Test 1 (serialization) fails: Simplify schema; revert to document-based evidence exchange
- If H-MECH-01 inconclusive: Design SpecificationObject both ways (have fallback); let deployment choose
- If vendors resist transparency: Reposition as **internal governance** tool, not market differentiator
- If adoption is slow: Open-source entire stack; position as community research infrastructure

---

## What This Research Enables (Beyond CGR)

### Research enabled by successful CGR:
1. **Governance as a measurable artifact** — opens entire domain: comparative governance frameworks research
2. **Behavioral prediction via architecture** — enables preventative AI safety (design for safety, not detect-and-override)
3. **Multi-party research coordination** — empirica becomes standard substrate for consortium research
4. **Calibration as first-class concern** — all future AI safety research can instrument its own confidence (F-PREFLIGHT → F-POSTFLIGHT)

### Longer-term implications:
- Governance research becomes empirical (testable hypotheses about what works)
- AI safety shifts from reactive (detect failures) to preventative (architect constraints)
- Research coordination infrastructure becomes as important as methodology (empirica layer)

---

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
