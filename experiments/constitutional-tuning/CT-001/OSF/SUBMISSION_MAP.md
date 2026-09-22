# CT-001 — OSF submission map

Use this file when creating the OSF preregistration. It does not replace the frozen Git preregistration at commit `d17b75d6b0f30e0d96607713ffeeddcb76eecda6`.

## Recommended OSF path

Create a new OSF Registration / Preregistration **from scratch** unless there is a dedicated CT-001-only OSF project. Creating from an existing project may archive unrelated project files into the registration.

Recommended template: **OSF Preregistration** (general-purpose).

## Registration metadata

**Title**  
CT-001 — Constitutional Tuning Reconstruction Test

**Description**  
Preregistered three-pass experiment testing whether a typed multi-voice evidence graph can preserve human, AI, industry, tool, constitutional, and normative signals without collapsing agreement into authority.

**Contributor**  
Carly R. Anderson

**ORCID**  
0009-0003-7540-4245

**Suggested subjects**  
Artificial Intelligence; Human-Computer Interaction; Governance; Software Engineering; Open Science

## Form mapping

### Research question / study information
Paste the Research Question from `OSF_PREREGISTRATION.md`.

### Hypotheses
Paste H-CT-001 verbatim.

### Design
Describe the three passes:
- A: frozen historical reconstruction
- B: blind independent reconstruction
- C: one-at-a-time adversarial mutations

### Sampling / data source
No human-subject sampling. The specimen is a frozen repository-governance artifact: PR #451 @ `4290d18ba5e067ea2d119b6adbcaf5238c978f62`.

### Variables / observations
Voice class, evidence standing, authority standing, independence vector, applicability, relationships, omissions, and warrant state.

### Analysis
Categorical relationship reconstruction only. No pooled alignment score and no majority-vote decision rule.

### Exclusion rules
Use the Non-goals / Exclusion section verbatim.

### Primary outcome
Use the Primary Outcome section verbatim.

### Secondary outcomes
Six Pass-C mutation outcomes, reported separately.

### Decision criteria / falsifiers
Paste all ten preregistered falsifiers verbatim.

### Materials
Reference:
- Git preregistration commit `d17b75d6b0f30e0d96607713ffeeddcb76eecda6`
- GitHub repository `humanaios-ui/operations`
- branch `z1/ct-001-constitutional-tuning`
- draft PR #452

## Files to attach

Recommended:
1. `PREREGISTRATION.md`
2. `OSF_PREREGISTRATION.md`
3. `OSF_METADATA.json`

Optional, because they were generated after the Git preregistration:
4. Pass-B package
5. Pass-C package

Do **not** present Pass-A results as preregistered outcomes. Pass A was encoded only after commit `d17b75d6...`.

## Registration integrity statement

Add this statement if the OSF template provides an additional notes field:

> The research question, hypothesis, design, falsifiers, and Pass-B/Pass-C plan were frozen in Git commit d17b75d6b0f30e0d96607713ffeeddcb76eecda6 before Pass-A results were encoded. Subsequent repository commits contain Pass-A reconstruction results and test packages and must not be interpreted as part of the original preregistered result state.

## Visibility

For open-science use, public registration is preferred unless there is a specific reason for embargo. Choose intentionally; do not infer the choice from this file.

## Final check before submission

- Confirm author/contributor information.
- Confirm ORCID is correct.
- Confirm hypothesis and falsifiers match the Git preregistration semantically.
- Confirm no Pass-A result text has leaked into the hypothesis/analysis-plan fields.
- Confirm attached files contain no secrets, private data, or unrelated project files.
- Record the OSF registration URL / DOI back into this experiment directory after registration.
