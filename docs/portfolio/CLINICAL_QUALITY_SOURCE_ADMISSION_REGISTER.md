# Clinical and quality experience — source admission register

**Record:** HAIOS-PORTFOLIO-SOURCE-REGISTER-20261026  
**State:** REVIEW CANDIDATES / not ratified as private master-profile facts.  
**Destination:** Owner-controlled master profile via the private bridge in PR #1029, after human review.  
**Privacy / authority:** No patient data, private human profile, or automatic portfolio update in this public registry.

## Documents in this research batch

| Record | Repository path | Status | Scope |
| --- | --- | --- | --- |
| HAIOS-PORTFOLIO-CLINICAL-2004-01 | `clinical-infrastructure/archive/2004-amino-acid-neuroproteomics.md` | HISTORICAL RECONSTRUCTION | 2004–2011 user-reported clinical HPLC; independently indexed 2009 MALDI-HDX paper |
| HAIOS-PORTFOLIO-QMS-2017-01 | `compliance/labcorp-quality-compliance.md` | PRACTICE MODEL | 2017–2020 user-reported Labcorp quality experience; independently documented CLIA requirements |
| HAIOS-QMS-ANALOGY-20261026 | `playbooks/integrated-qms-playbook.md` | DESIGN HYPOTHESIS | Translates quality-method controls into HumanAIOS evidence handling, non-authoritatively |

## Three different evidence types must not collapse

1. **Publication:** PMID 19940340 authenticates a *2009 MALDI-HDX study* and author list, including Carly R. Anderson and Richard S. Burns. It does not authenticate a July 2004 clinical launch, director titles, a first-certified claim, or a Parkinson's/MS clinical program.
2. **Career statement:** the owner-supplied resume supplies a claimed 2004–2011 HPLC/lab development role and 2017–2020 Labcorp quality role. Until employer/supervisor or protected historical records are reviewed, mark `SUPPORTED_BY_USER_SOURCE`.
3. **Rules:** CLIA/CAP sources support *what a laboratory should have done* in a specified period and context, not proof that a specific employer actually did it. No software security gate acquires clinical licensing authority from this mapping.

## Applicant profile projection proposal (human review required)

| Candidate resume claim | Source | Evidence state | Decision |
| --- | --- | --- | --- |
| Collaborated on published 2009 calmodulin/S100B MALDI-HDX methods study | PMID 19940340 | **OBSERVED** | Suitable for publication record; verify display details |
| Built and validated a clinical biochemical-genetics HPLC workflow | Owner-supplied resume | **SUPPORTED** (user-supplied) | Review historical work artifacts |
| Authored SOP / LIS integration / QA / competency systems | Owner-supplied resume | **SUPPORTED** (user-supplied) | Review historical work artifacts |
| Worked on Labcorp regional quality audits and analytical method validation | Owner-supplied resume | **SUPPORTED** (user-supplied) | Reconcile title and date with private master |
| “First certified clinical amino acid facility” in July 2004 | Narrative only | **UNVERIFIED** | Keep out of applications until proof |
| Named clinical director or direct report chain at 2004 hospital | Narrative only | **UNVERIFIED** | Do not add to master |
| Parkinson's disease/MS proteomics cohort studies | Narrative only | **UNVERIFIED** | Do not add without study record |
| Automated Labcorp CAPA software engine was deployed | Narrative only | **UNVERIFIED** | Do not add as executed accomplishment |
| Universal 24–48-hour governmental reporting requirement | Historical draft | **UNVERIFIED** | Replace with event-specific rule |
| Four-hour rule applied to all HPLC and MALDI specimens in 2004 | Historical draft | **CONTRADICTED AS UNIVERSAL** | Keep test-specific handling and time |

## Intake and disposition contract

The private master is **canonical for the individual's reviewed career evidence**. These public docs are merely attributed research candidates.

Proposed record fields for future private `project_evidence[]` import: `id`, `title`, `date_range`, `mandate`, `evidence_bullets`, `evidence_ref`, `evidence_state`, `review_status`, `approved_by`, `approved_at`. The existing draft PR #1029 can read approved `project_evidence`; no automatic import occurs here. The published paper belongs in the `publications` section with its verified DOI and PMID.

**Required decision:** the owner reviews role claims and historical dates; the source recorder marks approval at claim level. A reviewer may accept the publication while rejecting speculative facility claims. Retain all prior drafts and discrepancies rather than overwriting them.

**Test for success:** source-linked claims render correctly in one private application; rejected claims never appear; source SHA and user approval remain tied to the produced draft; no raw personal or patient data leaves the private boundary. Any missing proof results in `INVESTIGATE` or `NOT_ESTABLISHED`, never inferred entitlement.

**Related:** Operations PR #1029 (private master / application portfolio); prior user-supplied project-management resume; `SEED.md` (business identity anchor).  
**Admission:** draft only. No merge or production deployment authorized.
