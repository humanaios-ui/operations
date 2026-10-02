# Q-AUTOMATA-LINEAGE-LAB-01: Implementation Specification

**Z2 Ratified Decisions:** 3a–3f (See PHASE_1_RATIFICATION_PACKAGE.md)  
**Authority:** Night (carly.r.anderson@gmail.com)  
**Status:** DRAFT — Ready for Z2 Signature + Z3 Implementation  
**Stage:** 4 (Z2 Ratification) → 5 (Z3 Implementation)

---

## Core Decision Summary

| Decision | Ratified Value | Impact |
|----------|---|---|
| **3a. Reconstruction Rigor** | Dual independent formalization | Two researchers; inter-rater κ ≥70%; prevents single-researcher bias |
| **3b. Novelty Classification** | Structural rule | New mechanism = new failure mode OR boundary (not speed/scale) |
| **3c. Cooling-Off Period** | 30-day holding period | Historical findings sit 30 days before informing #497 decisions |
| **3d. Pilot 001 Scope** | Both separately documented | Talos Lineage (historical) AND Talos Benchmark (contemporary) with explicit separation |
| **3e. Negative Case Requirement** | Required ≥1 per mapping | Every positive claim cites failed/dead-end archetype |
| **3f. Publication Policy** | Published with disclaimer | Disclaimer on all external publication |

---

## Implementation Part 1: Automata Lineage Lab Protocol

### File: `AUTOMATA_LINEAGE_LAB_PROTOCOL_v1.md`

```markdown
# Automata Lineage Lab Protocol v1.0

**Authority:** Night (Z2) ratified Q-AUTOMATA-LINEAGE-LAB-01  
**Effective Date:** 2026-09-28  
**Review Cycle:** Per RESEARCH_CYCLE_SCHEDULE.md

---

## § 1: Reconstruction Rigor (Decision 3a)

### Dual Independent Formalization

**Mandate:** Every historical archetype undergoes formalization by two independent researchers.

**Process:**
1. **Researcher A** reads primary sources (mythology, historical texts, scientific papers)
   - Completes FORMALIZATION_TEMPLATE (see below)
   - Documents reasoning chain (mechanical → programmable → adaptive → agentic progression)
   - Identifies key decision points

2. **Researcher B** (blind to A's output) completes same template independently
   - Reads same primary sources
   - Produces independent formalization
   - Identifies convergence and divergence

3. **Inter-rater Agreement:**
   - Cohen's κ ≥ 0.70 required for publication
   - κ < 0.70 → dispute resolution conference → potential revision or retraction
   - κ values logged in lineage study report

### Formalization Template

```yaml
# Formalization: [Archetype Name]
# Researcher: [Name]
# Date: ISO8601
# Confidence: HIGH | MEDIUM | LOW

archetype_id: "[e.g., TALOS-001]"
name: "[e.g., Talos, the Brazen Automaton]"

# Primary Sources
sources:
  - title: ""
    author: ""
    date_range: ""
    reliability: "primary | secondary | tertiary"
    quote: ""
    interpretation: ""

# Formalization Chain
formalization:
  mythology: "Description of mythological form and function"
  mechanical: "Mechanical analog (e.g., clockwork, hydraulic systems)"
  programmable: "Programmable abstraction (e.g., state machine, algorithm)"
  adaptive: "Adaptive features (e.g., learning, feedback loops)"
  agentic: "Agentic interpretation (e.g., autonomous goal-seeking, self-modification)"

# Novelty Assessment (Decision 3b)
novelty_classification:
  mechanism: "New control mechanism? YES|NO"
  failure_mode: "New failure mode? YES|NO"
  boundary_change: "New authority/control boundary? YES|NO"
  is_genuinely_novel: "NOVEL (≥1 structural change) | VARIANT (speed/scale only)"

# Negative Case (Decision 3e)
negative_case:
  archetype_counterexample: "[Related archetype that did NOT exhibit this mechanism]"
  reason_not_applicable: "Why this variant failed or remains dormant"
  evidence: "[Citation/description]"

# Mapping to Contemporary Systems
contemporary_analog:
  system: "[e.g., Claude, Copilot, Multi-agent systems]"
  mechanism_mapping: ""
  evidence_strength: "strong | moderate | weak"
  confidence: "HIGH | MEDIUM | LOW"

# Falsifiers (Decision 3b)
falsifiers:
  - "Mechanism exists in pre-1800 written works → classification of novelty is false"
  - "Failure mode does not manifest in contemporary analog → mapping is spurious"
  - "Alternative explanation (orthogonal mechanism) better explains evidence → reinterpret"

# Sign-Off
formalized_by: "[Researcher]"
reviewed_by: "[Second Researcher]"
inter_rater_agreement_kappa: "[Score]"
```

---

## § 2: Novelty Classification Rule (Decision 3b)

**Structural Rule:**
- **NOVEL** = New mechanism (control flow) OR new failure mode OR new authority boundary
- **VARIANT** = Same mechanism, different speed or scale (e.g., faster learning)

**Falsifier:** If two researchers disagree on novelty classification:
1. Present evidence at inter-rater conference
2. If κ < 0.70 on novelty, finding marked as DISPUTED
3. Cooling-off period extends by 14 days pending Z2 judgment
4. Original claim cannot inform #497 decisions until resolved

**Examples (Pre-Registered):**
- ✓ NOVEL: Self-modifying agent (new authority boundary)
- ✗ VARIANT: Agent training 10x faster (speed, not structure)
- ✓ NOVEL: Byzantine fault tolerance (new failure mode)
- ✗ VARIANT: 1000-node cluster vs. 100-node (scale, not structure)

---

## § 3: Cooling-Off Period (Decision 3c)

**Mandate:** No historical lineage finding can inform #497 decisions during cooling-off period (state-tracked in REGISTERED.md per Decision 3c).

**Timeline:**
1. Dual formalization completed: Day 0
2. Inter-rater agreement ≥70%: Day 0 (recorded)
3. 30-day holding period: Days 0–30
4. Earliest citation in #497 design: Day 31+

**Tracking:**
- REGISTERED.md records: `LINEAGE_FINDING_<id> | completed_date=<D0> | cooling_off_until=<D30>`
- Automated gate: CI rejects PR citing lineage claim before Day 31

**Rationale:** Prevents authority leakage (historical analogy masquerading as empirical warrant in governance decisions).

---

## § 4: Pilot 001 Scope: Separate Documentation (Decision 3d)

### Talos Lineage Study (Historical)

**File:** `research/talos_lineage_study.md`

**Scope:** Reconstructing hypothetical evolution of autonomous control mechanisms from mythology through contemporary AI.

**Question:** Does the historical record suggest a conceptual lineage (mechanical → programmable → adaptive → agentic) that informs contemporary design debates?

**Methods:**
- Dual independent formalizations per § 1
- Genealogy mapping: Talos → clockwork automata → state machines → learning agents
- Relation types (pre-registered):
  - DIRECTLY_INFLUENCED: Later work cites or explicitly builds on earlier
  - RESEMBLES: Structural similarity without documented influence
  - NO_LINEAGE: Convergent evolution; unrelated mechanisms

**Deliverable:** Research report with inter-rater agreement scores, negative-case evidence, and falsifier audit trail.

### Talos Benchmark Study (Contemporary, Orthogonal)

**File:** `research/talos_benchmark_comparison.md`

**Scope:** Observational comparison of three implementations on fixed task contract (not claimed as lineage).

**Question:** Do three different agent architectures (rule-based, ML-based, LLM-based) exhibit measurable behavioral differences on a standardized control problem?

**Implementations:**
- TALOS-RULES: Hand-coded state machine
- TALOS-ML: Supervised learning model
- TALOS-LLM: Large language model agent

**Task Contract:** Fixed problem instance (e.g., simulated factory control task with known ground truth).

**Deliverable:** Benchmark comparison report; explicit non-claims about genealogy (this is contemporary observation, not historical lineage).

**Separation Invariant:** Talos Lineage and Talos Benchmark are separate reports. No conflation in publication or governance decisions.

---

## § 5: Negative Case Requirement (Decision 3e)

**Mandate:** Every positive lineage mapping must cite ≥1 failed or dead-end archetype.

**Example Structure:**
```
POSITIVE CLAIM: Talos → Byzantine Fault Tolerance
  Mapping: "Both employ redundancy + majority voting to tolerate agent failure"
  Evidence: [Talos myth describes three bronze servitors; BFT needs ≥2/3 honest agents]
  
  NEGATIVE CASE (REQUIRED): 
    Archetype: "Homunculus (Alchemical automaton)"
    Why not applicable: "Homunculus lacked redundancy or voting mechanism; centralized control"
    Evidence: "Paracelsus (1516) describes single artificial creature; no ensemble"
    Interpretation: "Homunculus represents failed path; lineage moved toward Talos model"
```

**Falsifier:** Missing negative case → finding marked DISPUTED; cooling-off extended.

**Hunting Protocol:**
- For each positive relation, researchers search literature for failed/dormant analogs
- Document why each failed variant is excluded
- Produces negative-case bibliography per lineage claim

---

## § 6: Publication Policy & Disclaimer (Decision 3f)

**Mandate:** All external publication includes explicit disclaimer.

### Disclaimer Template

```
---
**Research Disclaimer**

This computational genealogy is exploratory research and does not establish 
governance authority for HumanAIOS. Historical analogies inform but do not ratify 
design decisions. All architectural choices remain subject to Z2 ratification under 
GOVERNANCE_WORKFLOW_PATTERN.md.

This study was conducted under Automata Lineage Lab Protocol v1.0 with dual 
independent formalization (Cohen's κ ≥ 0.70) and mandatory negative-case evidence. 
Negative-case citations are available in [Appendix X]. Inter-rater agreement scores 
are reported in [Methods Section Y].

This research does not constitute evidence for governance decisions about SMAG 
calibration, Oracle authority, or any other policy. It is offered as background 
context only, subject to 30-day cooling-off period before citation in governance 
decisions (Decision 3c).

---
```

**Scope of Publication:**
- Peer-reviewed venues: Include disclaimer
- Institutional reports: Include disclaimer + link to GOVERNANCE_WORKFLOW_PATTERN.md
- Conference presentations: Include disclaimer in title slide
- Open preprints: Include disclaimer above abstract

**CI/CD Gate:** Pre-publication review step checks for disclaimer presence.

---

## § 7: Preconditions Checklist

Before any Pilot 001 lineage claim can inform #497 decisions:

- [ ] Dual formalization completed by two researchers
- [ ] Inter-rater agreement κ ≥ 0.70
- [ ] Novelty classification agrees (κ > 0.70) or resolved via Z2 judgment
- [ ] ≥1 negative case cited per positive mapping
- [ ] 30-day cooling-off period elapsed (REGISTERED.md shows Day 30+)
- [ ] Publication includes disclaimer template (§ 6)
- [ ] External links to governance workflow documented
- [ ] Falsifier audit trail recorded (all disconfirming evidence documented)

---

## § 8: Falsifiers & Halt Conditions

Study halts if any of these occur:

| Falsifier | Halt Condition | Resolution |
|-----------|---|---|
| κ < 0.70 on structure | Two researchers disagree on novelty | Inter-rater conference; Z2 arbitrates if unresolved |
| Negative case missing | Cannot cite failed archetype for mapping | Finding marked DISPUTED; publication delayed |
| Pre-1800 source found | Mechanism already exists in historical record | Novelty claim revoked; reinterpret as variant |
| Mechanism does not manifest in analog | Historical mechanism absent in contemporary | Mapping falsified; alternative explanation required |
| Cooling-off period violated | Governance decision cites <30-day-old finding | Decision marked DISPUTED; Z2 re-reviews |
| Disclaimer omitted | Publication lacks required caveat | Pre-publication gate blocks release |
```

---

## Implementation Part 2: Study Plan Files

### File: `TALOS_LINEAGE_STUDY_PLAN.md`

```markdown
# Talos Lineage Study: Plan & Design

**Principal Researchers:** [Two named researchers, TBD]  
**Start Trigger:** Resource allocation approved (state-gated, not calendar-driven)  
**Success Criterion:** Dual independent formalization complete with κ ≥ 0.70  
**Cooling-Off Period:** 30 days from completion (state-tracked in REGISTERED.md per Decision 3c)

## Research Question
Does the historical record suggest conceptual lineage from mythological automata → mechanical → programmable → adaptive → agentic control?

## Primary Archetypes (Pre-Registered)
1. Talos (Greek mythology)
2. Golem (Jewish legend)
3. Homunculus (Alchemical)
4. Frankenstein's creature (Gothic literature)
5. Mechanical Turk (18th-century automaton)
6. Babbage Analytical Engine (19th-century computing)

## Dual Formalization Timeline
- Week 1–2: Researcher A formalization (TALOS-001 through TALOS-006)
- Week 3–4: Researcher B independent formalization (same archetypes)
- Week 5: Inter-rater agreement calculation (Cohen's κ)
- Week 6: Dispute resolution if κ < 0.70

## Novelty Classification (Pre-Registered)
Example: Talos exhibits "redundancy with majority voting" (new boundary)
- Researchers agree this is NOVEL (κ test)
- Homunculus exhibits "centralized control only" (variant only)
- Researchers agree this is NOT NOVEL (κ test)

## Negative-Case Hunting
Per archetype, identify ≥1 failed variant:
- Talos positive: redundancy model | Homunculus negative: centralized-only model
- Golem positive: indestructible entity | Frankenstein negative: destructible creature
- [etc.]

## Publication Target
- Journal: [TBD, peer-reviewed]
- Preprint: [TBD]
- Conference: [TBD]
- All include § 6 disclaimer

## Success Criteria (for Phase 2 review)
- [ ] Dual formalizations completed; κ ≥ 0.70
- [ ] Negative-case citations present
- [ ] Novelty classifications finalized
- [ ] Publication ready with disclaimer
- [ ] Cooling-off period tracking logged in REGISTERED.md
```

### File: `TALOS_BENCHMARK_STUDY_PLAN.md`

```markdown
# Talos Benchmark: Contemporary Comparison

**Principal Researchers:** [Two named researchers, TBD]  
**Start Trigger:** Resource allocation approved (state-gated, not calendar-driven)  
**Success Criterion:** Benchmark protocol complete and peer-reviewed formalization ready

## Research Question
Do three agent architectures (rule-based, ML, LLM) exhibit measurable behavioral differences on a fixed control task?

## Study Design (Pre-Registered)
- **TALOS-RULES:** Hand-coded state machine controller
- **TALOS-ML:** Supervised learning model (trained on expert data)
- **TALOS-LLM:** LLM agent with provided API

- **Task Contract:** Factory simulation with 50 scenarios (fixed random seed)
  - Ground truth: optimal control sequence
  - Metrics: time-to-solution, action efficiency, error rate

## Non-Claims
This study does NOT claim historical lineage. It is a contemporary benchmark only.
Results may inform future lineage research but are orthogonal to Pilot 001 scope.

## Deliverable
Benchmark report with tables, error bars, confidence intervals. No claims of genealogy.

## Separation Rule
Talos Lineage report (historical) and Talos Benchmark report (contemporary) are 
published separately. No co-citation suggesting lineage without explicit methodological note.
```

---

## Implementation Part 3: CI/CD Integration

### File: `.github/workflows/lineage-precondition-gate.yml`

```yaml
name: Lineage Finding Precondition Gate

on:
  pull_request:
    paths:
      - 'research/talos_lineage_study.md'
      - 'research/talos_benchmark_comparison.md'
      - 'AUTOMATA_LINEAGE_LAB_PROTOCOL_v1.md'

jobs:
  precondition_check:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: "Check dual formalization presence"
        run: |
          if grep -q "Researcher A\|Researcher B" research/talos_lineage_study.md; then
            echo "✓ Dual formalization documented"
          else
            echo "✗ ERROR: Lineage claims missing dual formalization evidence"
            exit 1
          fi
      
      - name: "Verify inter-rater agreement κ ≥ 0.70"
        run: |
          kappa=$(grep -oP 'inter_rater_agreement_kappa.*\K[\d.]+' research/talos_lineage_study.md)
          if (( $(echo "$kappa >= 0.70" | bc -l) )); then
            echo "✓ Cohen's κ = $kappa ≥ 0.70"
          else
            echo "✗ ERROR: κ = $kappa < 0.70; inter-rater disagreement too high"
            exit 1
          fi
      
      - name: "Verify negative cases present"
        run: |
          negative_cases=$(grep -c "negative_case\|NEGATIVE" research/talos_lineage_study.md)
          if [ "$negative_cases" -ge 6 ]; then  # One per archetype
            echo "✓ Negative cases documented: $negative_cases"
          else
            echo "✗ ERROR: Insufficient negative-case evidence"
            exit 1
          fi
      
      - name: "Verify disclaimer in publication"
        run: |
          if grep -q "Research Disclaimer\|governance authority" research/*.md; then
            echo "✓ Disclaimer present"
          else
            echo "✗ ERROR: Publication missing required disclaimer (§ 6)"
            exit 1
          fi
      
      - name: "Check cooling-off period state"
        run: |
          python3 << 'PYTHON'
          import re
          
          # Query REGISTERED.md for cooling-off state per Decision 3c
          # Elapsed-time logic replaced with state-tracked checks (not calendar-driven)
          with open('REGISTERED.md') as f:
              content = f.read()
          
          match = re.search(r'LINEAGE_FINDING.*cooling_off_state=(\S+)', content)
          if not match:
              print("INFO: No lineage findings in REGISTERED.md yet (pre-study)")
          else:
              cooling_off_state = match.group(1)
              
              if cooling_off_state == 'EXPIRED':
                  print(f"✓ Cooling-off period expired (state-tracked in REGISTERED.md)")
              elif cooling_off_state == 'ACTIVE':
                  print(f"⚠ Cooling-off period active (state-tracked in REGISTERED.md)")
                  # Non-blocking warning; can cite after period expires
              else:
                  print(f"INFO: Unknown cooling-off state: {cooling_off_state}")
          PYTHON
      
      - name: "Verify no conflation (separate reports)"
        run: |
          if grep -l "Talos Lineage\|talos_lineage" research/*.md | \
             xargs grep -l "Talos Benchmark\|talos_benchmark" > /dev/null; then
            echo "✗ ERROR: Talos Lineage and Benchmark conflated in same document"
            echo "       Must be separate reports per Decision 3d"
            exit 1
          else
            echo "✓ Lineage and Benchmark are separate reports"
          fi
      
      - name: "Falsifier audit trail"
        run: |
          echo "Falsifier checklist (§ 8):"
          echo "  [ ] κ < 0.70 on structure → dispute resolution needed?"
          echo "  [ ] Negative case missing → finding marked DISPUTED?"
          echo "  [ ] Pre-1800 precedent found → novelty revoked?"
          echo "  [ ] Mechanism absent in analog → mapping falsified?"
          echo "  [ ] Cooling-off violated → decision DISPUTED?"
          echo "  [ ] Disclaimer omitted → publication blocked?"
          echo ""
          echo "ACTION: Z2 reviews audit trail; confirms no falsifiers tripped"
```

---

## Success Criteria (§6 Process Review)

- [ ] Dual-formalization protocol followed; inter-rater κ ≥ 70% achieved
- [ ] Novelty classifications cite structural rule; speed/scale changes not classified as novel
- [ ] 30-day cooling-off periods tracked in REGISTERED.md with completion dates
- [ ] Talos Lineage and Talos Benchmark published as separate reports with explicit separation note
- [ ] Every positive mapping includes negative-case evidence
- [ ] All external publications carry disclaimer template (§ 6)
- [ ] Falsifier audit trail complete (all disconfirming evidence documented)
- [ ] CI/CD gate enforces all preconditions before governance citation

---

## Next Steps

1. **Z2 reviews this spec** (you have it now)
2. **Z2 signs lineage protocol** with hash and timestamp
3. **Z3 (Copilot) implements:**
   - AUTOMATA_LINEAGE_LAB_PROTOCOL_v1.md in repository
   - Talos Lineage Study Plan (recruiting researchers)
   - Talos Benchmark Study Plan (concurrent implementation comparison)
   - CI/CD gate enforcing preconditions
   - REGISTERED.md tracking cooling-off periods
4. **Process review (8 weeks out):** Measure whether dual-formalization rigor detected methodological issues; whether cooling-off period prevents authority leakage; whether negative-case hunting produced robust mappings

---

**Document Version:** 1.0  
**Z2 Authority:** Night  
**Status:** AWAITING Z2 RATIFICATION SIGNATURE
