# Application Replay — 2026-10-02

**Replay ID:** APP-REPLAY-CAREER-EVIDENCE-20261002  
**Inputs:** promoted Project Evidence Records + final 49-resource Resource Miner snapshot + current primary-source opportunity pages.  
**Boundary:** evidence coverage is not applicant eligibility and does not predict a hiring/funding decision.

## Resource Miner result

A rerun was required because the canonical source set had grown from 45 to 49 resources and the new resources were absent from the durable snapshot.

Final corrected states:

| Resource | Route | Durable state |
|---|---|---|
| Mercor Analytical Chemist | VERIFY_NOW | ACTIVE |
| DataAnnotation Chemist | VERIFY_NOW | ACTIVE |
| GovAI Entrepreneur-in-Residence | VERIFY_NOW | ACTIVE |
| BlueDot Career Transition Grants | VERIFY_NOW | ACTIVE |
| GovAI Fellowship | WATCH | NOT_CURRENTLY_OPEN |
| Microsoft for Startups | WATCH | ALREADY_ACQUIRED / MANAGE |

The replay also exposed and repaired a typing defect:

```
CANONICAL SOURCE CATEGORY = RESOURCE MECHANISM
DESCRIPTIVE TEXT != RESOURCE MECHANISM
```

Therefore:
- BlueDot Career Transition Grant = **fellowship**, not generic project grant.
- DataAnnotation Chemist = **paid_work**, not a training resource simply because the work trains AI.
- GovAI EIR = **paid_work** with explicit bundled affordances `project_funding` and `research_access`.

Durable reconciliation now re-ranks after state changes so WATCH/ARCHIVE resources do not remain ahead of actionable resources.

## Mercor Analytical Chemist

**Current source:** https://work.mercor.com/jobs/list_AAABoKHdST6cTipsJcxHCZ-r/analytical-chemist  
**Human authorization:** AUTHORIZED_TO_APPLY  
**Evidence coverage:** PARTIAL_SUPPORTED

Strong source-supported evidence:
- analytical method validation and mass-spectrometry QC — PER-LABCORP-QUALITY-001
- HPLC analytical laboratory buildout and LC/MS proteomics — PER-STJOES-HPLC-001
- QA/CAP/SOP/documentation systems — PER-STJOES-HPLC-001 + PER-LABCORP-QUALITY-001
- AI evaluation/calibration/quality methods — PER-HUMANAIOS-ACAT-001

Boundary:
- Mercor specifically emphasizes hazardous-compound and trace-level detection expertise.
- No current source-supported PER establishes that specialization.
- Application may proceed, but the resume/interview must not silently relabel general analytical chemistry as hazardous-compound expertise.

## DataAnnotation Chemist

**Current source:** https://www.dataannotation.tech/job-board/chemist  
**Human authorization:** AUTHORIZED_TO_APPLY  
**Evidence coverage:** SUPPORTED_WITH_ROLE_ASSESSMENT_PENDING

Strong source-supported evidence:
- B.S. Chemistry + extensive laboratory experience
- HPLC, LC/MS/mass spectrometry, analytical interpretation and quality systems
- method validation / QC
- AI evaluation, calibration, corrections-ledger and technical-writing experience

Boundary:
- platform qualification remains external;
- do not overstate synthetic/process chemistry where direct evidence is limited.

## GovAI Entrepreneur-in-Residence

**Current source:** https://www.governance.ai/post/eir  
**Currentness:** rolling  
**Evidence coverage:** SUPPORTED

GovAI's essential criteria map to the PER graph:
- getting things done / entrepreneurial shipping -> HumanAIOS/ACAT, HumanAIOSBot, St. Joseph's HPLC build
- AI governance/safety context -> HumanAIOS Control Graph + Witness assurance work
- judgment under uncertainty -> healthcare quality/risk and safety programs
- impact evaluation / intellectual rigor -> validation, corrections-ledger, audit and falsification methods
- communication/collaboration -> cross-functional healthcare, research, regulator and operational work

**Project boundary:** HumanAIOS Control Graph + Witness Assurance Layer.

Next operation: submit expression of interest + max-2-page pitch when external form execution is available. Reference identities remain in the private reference-resource process.

## BlueDot Career Transition Grant

**Current source:** https://bluedot.org/grants/career-transition  
**Currentness:** active  
**Evidence coverage:** SUPPORTED_WITH_BUDGET_INPUT_PENDING

Strong evidence:
- recent HumanAIOS/ACAT work and accessible public samples
- recent AI forecasting/technical experimentation
- extensive analogous evidence for disciplined validation, operational judgment and adaptation

Current budget state:
- duration: 12 months
- living runway: $6,000/month
- base request: $72,000
- unresolved: whether the additional $2,400 health-insurance/tax-reserve/required-cost amount is **monthly** or **total/annual**

The grant remains a personal full-time transition resource. It should not be treated as a generic project-funding mechanism.

## Replay conclusion

```
PER PROMOTION
-> MASTER RESUME REGENERATION
-> RESOURCE MINER RERUN
-> DURABLE RECONCILIATION
-> MECHANISM/AFFORDANCE CORRECTION
-> APPLICATION REPLAY
```

No further broad career interrogation is required for these four applications.
