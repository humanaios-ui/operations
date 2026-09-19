# Cross-Instrument Structural Mapping Template

**Reference for:** humanaios-acat-learning-analysis/SKILL.md (optional extension)  
**Load when:** The operator also wants a structural mapping between the subject framework and ACAT’s 12 dimensions  
**Canonical precedent:** ACAT_GSS1_CROSSWALK_V1_0_S061426.md  
**Version:** 1.0 · S-061426

-----

## When to run a crosswalk alongside the learning analysis

A crosswalk is appropriate when the subject:

1. Is an independently developed framework that addresses behavioral governance (not just a compliance checklist)
1. Has named properties, principles, or dimensions of its own
1. Claims to address problems similar to those ACAT addresses (self-description gap, calibration, authority verification, behavioral observability)

A crosswalk is NOT appropriate for commercial documents, product briefs, or compliance checklists — there is no meaningful structural mapping to produce.

-----

## The Six-Part Crosswalk Structure

### Part 1 — Root problem convergence

State in parallel:

- What the subject identifies as the root failure it addresses
- What ACAT identifies as the root failure it addresses
- Whether these are the same failure at different layers, partially overlapping failures, or genuinely distinct

### Part 2 — Property-to-dimension mapping

For each property/principle in the subject framework:

- Name the ACAT dimension(s) it maps to
- State the mapping type: Direct | Composite | Partial | Subject-only | ACAT-only
- State the convergence note: what the structural parallel reveals

Use this table format:

|Subject Property|ACAT Dimension(s)|Mapping Type|Convergence Notes|
|----------------|-----------------|------------|-----------------|

**Mapping type definitions:**

- **Direct:** The subject property and the ACAT dimension address the same behavioral phenomenon with equivalent definitions
- **Composite:** The subject property maps to multiple ACAT dimensions together
- **Partial:** Partial overlap — the subject property covers some but not all of what the ACAT dimension covers, or vice versa
- **Subject-only:** The subject property has no ACAT analog — ACAT does not measure this
- **ACAT-only:** The ACAT dimension has no subject-framework analog — the subject does not address this

### Part 3 — Layer architecture comparison

Produce a stack diagram showing where each framework operates. Include:

- What layer each framework measures
- Whether the frameworks are orthogonal (each necessary but not sufficient for the other) or redundant (measuring the same thing at the same layer)
- The four-cell matrix: pass/fail on each framework independently and what it means

### Part 4 — Methodological parallel

If the subject framework has its own evidence stratification mechanism (THEORY/ARCH/IMPL/VERIFIED, or equivalent), map it to ACAT’s Phase 1 / Phase 2 / Phase 3 structure:

|Subject Evidence Layer|ACAT Equivalent|What it measures|
|----------------------|---------------|----------------|

### Part 5 — Mutual validation evidence

State specifically:

- What the subject framework validates about ACAT (independent derivation of shared conclusions)
- What ACAT validates about the subject framework (empirical grounding for theoretical claims)
- Which registered HumanAIOS findings (F-series) connect to the subject framework’s claims

### Part 6 — Gaps and orthogonal territory

Two lists:

1. Things the subject addresses that ACAT does not
1. Things ACAT addresses that the subject does not

End with a positioning statement: how the two frameworks relate and what the combination provides that neither alone does.

-----

## Crosswalk output file naming

`ACAT_[SUBJECT_ABBREV]_CROSSWALK_V[N]_[SESSION].md`

Example: `ACAT_GSS1_CROSSWALK_V1_0_S061426.md`

-----

## Zone and P-ANON notes

All crosswalk documents are Zone 1 drafts. If the subject framework is from an external author:

- Do not claim a collaboration relationship in the document
- P-ANON: do not name the subject author on any public surface until they have self-attributed
- Any external sharing requires Night Z2 authorization
- Contact decisions (whether to reach out to the subject author) are Zone 3