# Integrated quality management playbook — clinical-method discipline to evidence-governed software

**Record:** HAIOS-QMS-ANALOGY-20261026 | **Version:** 1.1.0 (review draft)  
**State:** PROPOSED HUMANAIOS ENGINEERING PLAYBOOK; **not** a historical hospital/Labcorp deployment, accredited QMS, patient SOP, or active production enforcement engine.  
**Authority effect:** NONE. All changes to regulated clinical workflows require their own qualified personnel and controls.

## 1. Why these two historical domains belong together

The user's project-management resume describes two classes of work:

- **Specialized measurement development (St. Joseph's / Barrow, 2004–2011):** HPLC quantitative amino-acid workflows, method records and quality-system development are user-reported; a **2009 peer-reviewed MALDI-TOF HDX publication independently verifies** participation by Carly R. Anderson and Richard S. Burns in a specific protein-conformation methods study [C1].
- **Regional quality management (Labcorp, 2017–2020):** user-reported audit, regulatory and analytical QA experience. CLIA/CAP **rules** are independently checkable; whether a specific automation was deployed in that role is not.

The original playbook drew a direct historical “2004 micro system -> Labcorp enterprise automation” pipeline. **Correction:** this is a *cross-career method analogy*, not a shared institution, common production platform, documented data transfer, or retroactive automated CAPA deployment.

## 2. Two-tier model with explicit control boundary

```text
                         USER-ATTESTED HISTORICAL EXPERIENCE
                    ┌────────────────────────────────────────┐
Tier A              │ Method / specimen / instrument controls│
MEASUREMENT         │ HPLC / clinical diagnostics             │
                    │ MALDI-HDX structural research (distinct)│
                    │ Accuracy, precision, SOP, QC, provenance│
                    └─────────────────────┬──────────────────┘
                                          │ DESIGN PRINCIPLES ONLY
                                          ▼
                    ┌────────────────────────────────────────┐
Tier B              │ Quality / governance / corrective loops │
ORGANIZATION        │ Risk triage, PT isolation, access roles  │
                    │ Audit, CAPA, competence, review outcomes│
                    └─────────────────────┬──────────────────┘
                                          │ RESEARCH ANALOGY ONLY
                                          ▼
                    ┌────────────────────────────────────────┐
HumanAIOS           │ INTENT-OS + Resource Miner + Witness    │
APPLICATION         │ Observe -> challenge -> propose -> test  │
                    │ -> human approval -> result receipt     │
                    └────────────────────────────────────────┘
```

Every arrow is a conceptual translation. It grants no equivalence between clinical accreditation and AI governance.

## 3. Tier A: measurement-system integrity

**Clinical background:** Specimen identity, matrix/temperature and timed processing, chain of custody, calibration, instrument controls, operator competency, numerical uncertainty, and result-release gates all affect clinical measurement quality.

**Method separation:** Plasma amino-acid testing and MALDI-TOF protein HDX use distinct analytes, sample-preparation schemes, data interpretations and approvals. The Mayo plasma amino-acid instructions specifying wet ice and up-to-four-hour refrigerated separation are a *current test-specific example*, not a universal 2004 clinical/research rule [C2]. GeneReviews substantiates MSUD analyte significance [C3]; PubMed substantiates MALDI-HDX controls [C1].

**CLIA reference:** Verification or establishment depends on method type under 42 CFR 493.1253 [C4]. Do not infer a historical instrument model, universal number of runs, or method acceptance criterion without an archived SOP.

**Software transfer proposal:** For any Resource Miner source observation, record URL, observed time, method, revision where available, content trust level, contradiction and reproducible readback. If source says “found” but verified evidence says “role missing,” status becomes **CONFLICT_REVIEW**, not an auto-award or hidden suppression without human review.

## 4. Tier B: quality governance and escalation

**Clinical controls:** A documented nonconformance may trigger authorized containment; investigators separate symptom and cause, make a controlled correction and verify effectiveness. Applicable proficiency-testing rules bar inter-laboratory PT-result communication until the reporting deadline, regardless of internal sign-off, and restrict PT referral [C5]. Competency checks are specific to roles/methods [C6].

**Software translation — proposed finite state model:**

```text
OBSERVED
  ├── confirmed supporting source -> SUPPORTED
  ├── evidence conflicts -> CHALLENGED (no external action)
  └── source missing -> UNVERIFIED
CHALLENGED -> PROPOSED_CORRECTION -> INDEPENDENT_REVIEW
INDEPENDENT_REVIEW
  ├── fails -> REJECTED / record falsifier
  └── passes -> HUMAN_APPROVAL_REQUIRED
HUMAN_APPROVAL -> ADMITTED_CHANGE -> REPLAY -> VERIFIED_OUTCOME
```

A code merge is **not** clinical sign-off, resource entitlement or proof of real-world benefit. Do not use clinical words “validated,” “CAP-certified,” or “regulatory-compliant” to describe a software process merely because this pattern was adapted.

### 4.1 Product-specific application

| Surface | Minimum control | Observable receipt | Human boundary |
| --- | --- | --- | --- |
| Private Master Profile | Source-linked claim, review state, source revision | Which facts changed, which remain disputed | Owner controls disclosure and edits |
| Application Portfolio | Exact evidence IDs, target role, generated document fingerprint | Trace each sentence to private master | Human reviews and submits |
| Business profile / SEED | Canonical revision and staged governance | Exact-head review evidence | Zone 2 only changes authority |
| Resource Miner | Two-way source verification, conflict state | Observed URL + source timestamp and state | Candidate ≠ eligibility |
| Witness / P1–P2–P3 | Independent challenge, frozen P1, amended P3 | Two distinct recorded perspectives | No self-approval |
| Opportunity results | Status replay after correction | Closed role stays excluded from ordinary active display | Reversible human disposition |
| Resource outcomes | Acquisition and downstream benefit proof | Receipt of real acquired resource/use | Research is not authorization |

## 5. Master profile is a resource, not an unrestricted data mine

The profile-maintainer proposal in operations PR #1029 uses:

- Private anchor: `humanaios-internal/src/data/master_profile.yaml`
- Business anchor: `operations/SEED.md`
- Template: the user-supplied `HumanAIOS_Master_Project_Management_Resume.docx`
- Data roles: `EVIDENCE_SOURCE` and `CONTROLLED_RESOURCE_SOURCE`, **not** `OPPORTUNITY_SOURCE`

The historical QMS archive may inform applicant *skills* (analytical validation, laboratory QA, CAP/CLIA literacy, process control, audits). It is **not** a new live license, company certification, guaranteed skill level, employment verification, or reason to expose old patient/employer data.

**Proposed evidence admission fields** (private only until reviewed):

```yaml
project_evidence:
  - id: project-clinical-hplc-2004-2011
    title: "Biochemical genetics HPLC & research infrastructure"
    review_status: "USER_SUPPLIED_NEEDS_HUMAN_REVIEW"
    evidence_state: "SUPPORTED"
    source_ref: "user-provided-resume"
    external_publication_ref: "PMID:19940340"
    publication_scope: "MALDI-HDX paper authorship only"
    claims_needing_proof:
      - "July 2004 deployment"
      - "first certified clinical facility"
      - "laboratory manager appointment"
```

**Design rule:** A publication citation supports exactly the paper's reported work. It does not automatically validate every item in an employment narrative.

## 6. Controlled experiment — can QMS reasoning improve Resource Miner?

**Hypothesis (H1):** A challenge-and-effectiveness loop reduces contradictory active opportunity displays without raising false suppression compared with the existing baseline.

**Protocol:**
1. Freeze 20 synthetic results, including positive URLs, genuinely closed roles, ambiguous source failures and stale titles.
2. P1: capture initial statuses and confidence *before* reviewer evidence.
3. P2: independent verifier checks the source and challenge, recording exact observations.
4. Apply proposed conflict-classification logic in a test-only branch.
5. P3: record changes, disagreements and reasons without deleting P1/P2.
6. Replay input and compare baseline vs patched active results.
7. Human reviewer decides whether admission criteria were met.

**Primary metrics:** confirmed false-active count (lower is better); false-dismissal count (must not increase); status persistence after replay; exact-source attribution completeness; reviewer time. **Failure mode:** evidence from one webpage is treated as independent verification of itself, a closed source gets presented as open, or a disagreement is erased. On failure, preserve failed experiment and do not auto-admit.

## 7. Quality and evidence controls

- **OBSERVED:** 2009 paper coauthorship; current published CLIA rules.
- **SUPPORTED:** user-supplied career/project claims, clearly attributed.
- **INFERRED:** transfer of quality-control design patterns from measurement to software.
- **HYPOTHESIZED:** new challenge loop improves source reliability.
- **UNVERIFIED:** exact 2004 launch date, first-certified claim, past automated containment engine, role-specific organizational appointments.
- **CONTRADICTED:** claim that a staff signature can override PT communication embargo; claim that one universal four-hour processing rule covers all clinical and proteomics specimens.

**Publication gate:** do not list any historical hospital or employer record as an approved policy without evidence and accountable authorization. Do not copy employee records, reagent credentials, protected health information or original patient datasets into a public repository.

## 8. Sources and related records

- **[C1]** NLM PubMed, 2009 MALDI-HDX calmodulin/S100B article, PMID 19940340: https://pubmed.ncbi.nlm.nih.gov/19940340/
- **[C2]** Mayo Clinic Laboratories, quantitative plasma amino acids specimen rules: https://www.mayocliniclabs.com/test-catalog/Overview/9265
- **[C3]** GeneReviews, MSUD diagnosis/quantitative analytes: https://www.ncbi.nlm.nih.gov/books/NBK1319/
- **[C4]** 42 CFR 493.1253, analytical performance: https://www.law.cornell.edu/cfr/text/42/493.1253
- **[C5]** 42 CFR 493.801, PT testing / communication / referrals: https://www.law.cornell.edu/cfr/text/42/493.801
- **[C6]** 42 CFR 493.1451, personnel competency: https://www.law.cornell.edu/cfr/text/42/493.1451
- **[U1]** 2026-10-26 user-supplied historical archive draft and QMS playbook, plus project/program resume.
- **Internal companion:** `clinical-infrastructure/archive/2004-amino-acid-neuroproteomics.md`, `compliance/labcorp-quality-compliance.md`.

**Review sign-off:** PENDING HUMAN REVIEW. There is no “Global Quality and Regulatory Vigilance Team” approval demonstrated for these materials; the original signature field is a proposal, not evidence of consent or institutional authorization.
