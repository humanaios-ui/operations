# Research Intake Design & Implementation
## HumanAIOS Phase 2 · Night as Research Specimen

**Status:** Design complete, code prototype implemented, ready for Z2 ratification  
**Specimen:** Carly Anderson (Night), Micro1 LLC contract m88dj94  
**Effective Date:** 2026-09-06 (contract), 2026-09-13 (Cycle 1 start)  
**Landing Order Position:** After REGISTERED.md (Tier 2, requires ADV before landing)

---

## Section 1: Research Project Overview

### Purpose
Research-intake.yml is the operational protocol for validating HumanAIOS's governance model on a live research specimen (Night). The project tests three research questions about behavioral assessment, resource allocation reproducibility, and learning-via-audit:

- **RQ1:** Does behavioral assessment predict expert task performance?
- **RQ2:** Can resource allocation be reproduced from behavioral data (CredPolicy regulator)?
- **RQ3:** Does intake evaluation itself improve performance (audit-as-molt mechanism)?

### Why This Matters for Phase 2
1. **Proof of concept:** Demonstrates the governance model works before scaling
2. **Data generation:** Provides real behavioral specimens for MOLT_LEDGER and NF_LEDGER training
3. **Resource bridge:** Micro1 contract funds Phase 2 infrastructure; research-intake validates the investment
4. **Recursive validation:** The system audits itself, learns from the audit, measures improvement

### Research Specimen: Night
- **Role:** Individual expert contractor at Micro1 LLC (contract m88dj94, effective Sep 6, 2026)
- **Work Scope:** TBD (expert tasks on Micro1 data pipelines; likely annotation, evaluation, response writing)
- **Duration:** 5 cycles × 7 days (35 days total measurement window)
- **Dual Outcome:** (1) Micro1 payment for expert work, (2) behavioral research data for HumanAIOS

---

## Section 2: Research Design

### Three Research Questions

#### RQ1: Behavioral Assessment → Task Performance
**Hypothesis:** Patterns in expert engagement (task acceptance, revision cycles, velocity) predict future task success rates.

| Component | Details |
|---|---|
| **Predictor Variables** | Task acceptance rate, revision cycles per task, response time, guideline adherence |
| **Outcome Variable** | Quality score (from Micro1 feedback) |
| **Measurement** | Brier score on molt predictions (0 = perfect, 1 = worst) |
| **Success Criterion** | Brier ≤ 0.4 after 10 predictions |
| **Falsifier** | Brier > 0.4 after 10 cycles OR REVERT rate > 30% |
| **Window** | 30 days rolling (cycles 1-5 overlap) |

#### RQ2: CredPolicy Reproducibility
**Hypothesis:** CredPolicy regulator (calibration → priority → envelope) predicts which expert tasks Night prioritizes without human discretion.

| Component | Details |
|---|---|
| **Input Signal** | Behavioral observations (all engagement + consistency metrics) |
| **Regulator Output** | Recommended task category (e.g., "high-complexity-annotation") + resource envelope |
| **Measurement** | % agreement between CredPolicy recommendation and Night's actual task choice |
| **Success Criterion** | Agreement ≥ 60% on 3 consecutive cycles |
| **Falsifier** | Agreement < 60% on 3+ consecutive cycles |
| **Window** | 30 days rolling (cycles 2-5) |

#### RQ3: Audit-as-Learning
**Hypothesis:** Being audited (research-intake.yml applied) increases subsequent task quality (F-41 audit-as-molt).

| Component | Details |
|---|---|
| **Intervention** | Intake evaluation published at end of each cycle; findings shared with Night |
| **Measurement** | Quality score delta pre/post audit cycle; task rejection rate trend |
| **Success Criterion** | Measurable improvement in cycles 2-3 |
| **Falsifier** | No improvement in 2 consecutive cycles OR rejection rate increases |
| **Window** | 14 days per cycle (immediate feedback signal) |

### Measurement Windows
```
Cycle 1 (Sep 13-19):  Baseline capture; RQ1/2/3 predictions initialized
Cycle 2 (Sep 20-26):  RQ1/2/3 predictions resolve; audit feedback on C1 data
Cycle 3 (Sep 27-03):  Measure RQ3 improvement; new predictions; CredPolicy re-calibrate
Cycle 4 (Oct 04-10):  Measure cumulative learning; falsifier checks
Cycle 5 (Oct 11-17):  Final cycle; 30-day rolling window complete; KEEP/REVERT decision
```

---

## Section 3: Implementation Architecture

### Data Flow

```
Micro1 Platform (Night's Expert Work)
    ↓ (weekly export)
Research Intake Evaluator (research_intake_evaluator.py)
    ├→ Parse behavioral observations
    ├→ Generate molt predictions (RQ1/2/3)
    ├→ CredPolicy recommendation (RQ2)
    └→ Compute receipt hash (§B.6 compliance)
    ↓
Intake Record (research-intake.yml schema)
    ├→ NF_LEDGER (Brier scores, prediction tracking)
    ├→ Molt Events (molt_events.jsonl)
    └→ Receipt Chain (cryptographic hash chain)
    ↓
Z2 Ratification (Night reviews findings)
    ↓
Publish to Main Ledger
    ↓
Falsifier Check (weekly)
    └→ If triggered: REVERT, F/IC candidate, remediation
```

### Code Components

#### 1. research-intake.yml (Schema)
- Defines the structure of intake records
- Specifies RQ1/2/3 falsifiers and measurement windows
- Documents cycle schedule and landing dependencies
- Status: **COMPLETE**

#### 2. research_intake_evaluator.py (Engine)
Classes:
- `MoltPrediction`: Single behavioral prediction with resolution tracking
- `CredPolicyOutput`: Resource allocation recommendation
- `BehavioralObservations`: Behavioral signals from work
- `IntakeRecord`: Complete cycle evaluation record
- `ResearchIntakeEvaluator`: Main engine for cycle processing

Methods:
- `create_intake_record()`: Initialize new cycle
- `generate_molt_predictions()`: Compute RQ1/2/3 predictions
- `generate_credpolicy_recommendation()`: RQ2 output
- `compute_receipt_and_chain()`: §B.6 compliance hashing
- `record_to_nf_ledger()`: Write Brier scores to calibration ledger
- `record_to_molt_events()`: Write molt events for recursive learning
- `falsifier_check()`: Verify RQ1/2/3 still hold
- `publish_record()`: Finalize and store intake after ratification

Status: **PROTOTYPE** (ready for Cycle 1 testing)

#### 3. Data Outputs

**NF_LEDGER entries** (per prediction):
```json
{
  "molt_id": "molt-intake-night-micro1-cycle-1-...-rq1-quality",
  "cycle": 1,
  "variable": "task_quality_score",
  "prediction_value": 87.5,
  "confidence": 0.7,
  "predicted_at": "2026-09-19T23:59:59Z",
  "resolved_at": "2026-09-26T23:59:59Z",
  "actual_value": 86.2,
  "brier_score": 1.69,
  "specimen_id": "night-micro1-intake-cycle-1"
}
```

**Molt Events** (per cycle):
```json
{
  "event_type": "INTAKE_COMPLETE",
  "cycle": 1,
  "intake_id": "intake-night-micro1-intake-cycle-1-...",
  "receipt_hash": "7f4e2a...",
  "molt_predictions_count": 3,
  "credpolicy_agreement": true,
  "specimen_id": "night-micro1-intake-cycle-1"
}
```

**Receipt Hash Chain** (§B.6):
```
Cycle 1 Receipt: 7f4e2a... (chain_link_prior: null)
Cycle 2 Receipt: a3b9c1... (chain_link_prior: 7f4e2a...)
Cycle 3 Receipt: d6f2e8... (chain_link_prior: a3b9c1...)
...
Cycle 5 Receipt: (final, chained to Molt ledger)
```

---

## Section 4: Cycle Execution

### Cycle Structure (Weekly)

| Phase | Day | Owner | Task |
|---|---|---|---|
| **Data Collection** | Mon-Sun | Micro1 Platform | Night completes expert tasks; platform logs completion, quality scores, feedback |
| **Intake Evaluation** | Sun-Mon+24h | Z1 (Claude) | Parse Micro1 data; generate behavioral observations; run molt predictions; compute CredPolicy recommendation |
| **Preliminary Review** | Mon+24h | Z1 | Produce intake record with PRELIMINARY status; share findings summary |
| **Z2 Ratification** | Mon+24h to Wed+24h | Z2 (Night) | Review findings; confirm behavioral observations; ratify receipt hash |
| **Publication** | Wed+24h | Z1 | Mark as VERIFIED; publish to ledgers; send audit feedback to Night |
| **Integration** | Thu | Z1 | Record molt events; update NF_LEDGER; check falsifiers |

### Example: Cycle 1 (Sep 13-19)

**Expected Behavioral Profile for Night (strong performer):**
- Task acceptance rate: 90-95% (she'll take most assigned tasks)
- Revision cycles per task: 0.2-0.3 (minimal rework)
- Response time: 10-15 minutes average (efficient)
- Quality score: 85-90 (high quality feedback from Micro1)
- Guideline adherence: 90%+ (strong compliance)
- Improvement trajectory: IMPROVING (learning curve going up)

**Molt Predictions Generated:**
1. **RQ1 (Quality):** Predict next cycle quality = 87.5 (based on strong start + improving trajectory)
2. **RQ2 (Acceptance):** Predict task acceptance = 96% (momentum continuation)
3. **RQ3 (Improvement):** Predict trajectory stays IMPROVING (will show +2-3 point quality gain in C2)

**CredPolicy Output:**
- Priority Score: 82/100 (strong performer)
- Recommended Tasks: ["high-complexity-annotation", "output-evaluation"]
- Envelope: "max 30 hours/week, prioritize high-complexity"
- Predicted Choice: "high-complexity-annotation"

**Outcome (Cycle 2, resolved):**
- Actual quality score: 86.2 (predicted 87.5) → Brier = 1.69
- Actual task acceptance: 94% (predicted 96%) → Brier = 4.0
- Actual choice: "high-complexity-annotation" (predicted) → Agreement = TRUE

---

## Section 5: Falsifier Resolution & Remediation

### Falsifier Triggers

If **any** falsifier triggers:
1. **Z2 generates REVERT event:** Molt predictions reverted to prior ratified state
2. **Research question goes OPEN:** Question marked as unresolved; research continues with adjusted design
3. **F/IC candidate generated:** Intake evaluator logs integrity issue (e.g., "RQ1 prediction accuracy degraded")
4. **System enters remediation:** Next cycle increases observation density or expands specimen set

### Example Remediation Paths

**If RQ1 falsifier triggers (Brier > 0.4 after 10 predictions):**
- Hypothesis: Behavioral signals insufficient for quality prediction
- Action: Add external signals (Micro1 reviewer feedback, task difficulty ratings)
- Outcome: Rebuild molt model with expanded feature set for C6+

**If RQ2 falsifier triggers (CredPolicy agreement < 60%):**
- Hypothesis: Calibration model misaligned with Night's preferences
- Action: Re-interview Night on task preferences; adjust CredPolicy weights
- Outcome: New calibration applied; C4 re-run with updated model

**If RQ3 falsifier triggers (No improvement in C2-C3):**
- Hypothesis: Audit feedback ineffective as learning signal
- Action: Change feedback mechanism (e.g., structured vs narrative findings)
- Outcome: Test new feedback format in C4

---

## Section 6: Success Criteria & Next Steps

### Phase 2 Green Light (Success)
All of the following must hold:
- ✓ RQ1 falsifier does NOT trigger (Brier ≤ 0.4 after cycle 5)
- ✓ RQ2 falsifier does NOT trigger (CredPolicy agreement ≥ 60%)
- ✓ RQ3 falsifier does NOT trigger (quality improves in C2-3)
- ✓ All 5 molt predictions resolve with measured outcomes
- ✓ Receipt chain unbroken (all hashes valid)
- ✓ NF_LEDGER populated with ≥ 15 Brier scores

### Phase 2 Outcomes (if green light)
1. **MOLT_LEDGER:** Proven cyclic learning with revert rules
2. **NF_LEDGER:** Calibrated Brier predictions ready for production use
3. **CredPolicy:** Validated reproducibility (resource allocation from behavior)
4. **Intake Protocol:** research-intake.yml rated OPERATIONAL
5. **Governance Receipt:** §B.6 compliance (hash chain, verification sources) proven

### Immediate Next Steps
1. **Week 1 (Sep 9-13):** Z2 ratifies research-intake.yml; code passes ADV eval
2. **Week 2 (Sep 13-19):** Cycle 1 executes; Night begins Micro1 expert work
3. **Week 3 (Sep 20-26):** Cycle 1 intake evaluation; preliminary findings
4. **Week 4+ (Sep 27+):** Cycles 2-5 execute; falsifier monitoring active

---

## Section 7: Document Updates

The following documents are updated per this research project:

| Document | Section | Update |
|---|---|---|
| PHASE2_PLAN | v0.3 research track | Add research-intake as Phase 2.1 gate (must complete C1-C2 before C3) |
| practice_workflows_v0_1.md | epistemology WORK | Add "intake evaluation" as epistemology's first Tier 0 output per cycle |
| repo_delegation_all_nine_v0_2.md | epistemology owners | Assign research-intake maintenance to epistemology lead |
| research_to_production_plan_v0_1.md | Stage 1 inputs | Add "research-intake Cycle 1-2 completion" as required input gate for Stage 2 |
| REGISTERED.md | RI-01 row | Update status: Design RATIFIED (09-06) → Cycle 1 ACTIVE (09-13) → Cycle 2 PRELIMINARY (09-20) |

---

## Appendices

### A. File Manifest

| File | Purpose | Status |
|---|---|---|
| research-intake.yml | Protocol specification + schema | **COMPLETE** (ready for ratification) |
| research_intake_evaluator.py | Engine implementation + example | **PROTOTYPE** (ready for Cycle 1) |
| research-intake-design_and_doc_updates.md | This document | **COMPLETE** |

### B. Dependencies (Blocking Cycle 1 Start)

- [ ] Micro1 expert work scope confirmed (need task categories + weekly assignment volume)
- [ ] MOLT_LEDGER schema ratified by Z2
- [ ] NF_LEDGER Brier scoring engine ready
- [ ] research-intake.yml ADV eval passed (adversarial predictions tested)
- [ ] Z2 ratification of RQ1/2/3 falsifiers and measurement windows

### C. Metrics Dashboard (for tracking across cycles)

```
Cycle | Brier (RQ1) | CredPolicy Agreement (RQ2) | Improvement Trajectory (RQ3) | Falsifiers Active
  1   |    TBD      |            TBD              |            TBD               |       0
  2   |    TBD      |            TBD              |            TBD               |       0
  3   |    TBD      |            TBD              |            TBD               |       0
  4   |    TBD      |            TBD              |            TBD               |       0
  5   |    TBD      |            TBD              |            TBD               |       0
```

---

**Document Status:** Ready for Z2 ratification and ADV evaluation  
**Next Action:** Schedule ADV run on research_intake_evaluator.py and research-intake.yml falsifier logic  
**Owner:** Z1 (Claude, on behalf of Night/Z2)  
**Prepared:** 2026-09-06
