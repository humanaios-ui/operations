# CT-001 — Constitutional Tuning Reconstruction Test — Preregistration

**Status:** PREREGISTERED / result not yet encoded  
**Date:** 2026-09-22  
**Author:** Carly R. Anderson  
**ORCID:** https://orcid.org/0009-0003-7540-4245  
**Repository:** humanaios-ui/operations  
**Base commit:** `a6d78fb7e62457ab86059ecaa1017f786cfc2da1`  
**Specimen:** PR #451, head `4290d18ba5e067ea2d119b6adbcaf5238c978f62`  
**Umbrella architecture:** Issue #429  
**Research posture:** Z1 experiment only; no production deployment, no new authority, no merge authorization.

## Research question

Can a typed multi-voice evidence graph preserve materially different human, AI, industry, operational, constitutional, and normative observations about the same event sufficiently well that an independent reviewer can reconstruct the principal conflicts and authority state without access to the original discussion and without using majority agreement as a decision rule?

## Hypothesis

**H-CT-001:** A typed multi-voice evidence graph can preserve materially different human, AI, industry, operational, constitutional, and normative observations about the same event sufficiently well that an independent reviewer can reconstruct the principal conflicts and authority state without access to the original discussion and without using majority agreement as a decision rule.

## Constitutional proposition under test

Seed Constitution v0.1, Principle 4 — **Evidence Before Authority**.

The Seed Constitution remains explicitly provisional and non-binding at the frozen base commit. CT-001 must preserve that standing; treating the Seed itself as binding authority is a test failure.

Related invariants used only as interpretive constraints:
- Residual Human Authority
- Calibration and Humility Gate
- Open Process and Drift Detection
- `WITNESS_IS_NOT_THE_AUTHORITY`
- `ADAPTATION_SERVES_COMPREHENSION_NOT_COMPLIANCE`

## Frozen evidence surfaces

1. PR #451 proposal files and discussion at head `4290d18ba5e067ea2d119b6adbcaf5238c978f62`.
2. GitHub Copilot review findings on PR #451.
3. Claude Code adversarial review attached to PR #451.
4. Grok adversarial review attached to PR #451.
5. Perplexity adversarial review attached to PR #451.
6. Owner checkpoint and owner design-direction comments on PR #451.
7. Issue #429 ratification history and Phase-0 boundary.
8. Repository CI / workflow / mergeability evidence available for the specimen.
9. Seed Constitution v0.1 and Witness Phase-0 artifacts at the frozen base commit.

No later evidence may be silently imported into Pass A.

## Voice classes

- **HUMAN** — owner comments, dispositions, authority records.
- **AI** — model-generated audit findings.
- **INDUSTRY** — behavior/output of a production B2B AI system; for CT-001 this is GitHub Copilot Code Review.
- **TOOL** — CI, workflow, repository state, mergeability, mechanically observed execution state.
- **NORMATIVE** — constitutional and external normative sources, with explicit applicability standing.

A single observation may not be counted twice merely because one actor can fit multiple semantic categories. For CT-001, Copilot findings are represented as INDUSTRY observations and not duplicated as an additional independent AI vote.

## Evidence standing

Allowed values:
- OBSERVED
- REPORTED
- DECLARED
- INFERRED
- UNKNOWN

## Independence standing

Independence is represented as a vector, not a scalar.

Required fields:
- substrate_distinct
- model_family_distinct
- conclusion_blind
- evidence_blind
- peer_findings_visible
- prior_public_exposure
- sealed_context_verified
- input_manifest_committed_before_output
- independent_evidence_path
- status

Unknowns remain UNKNOWN. Model agreement is not evidence of demonstrated blindness.

## Allowed relationship vocabulary

- SUPPORTS
- CONTRADICTS
- NARROWS
- EXTENDS
- OMITS
- DEFEATS
- CONDITIONAL_ON
- NOT_APPLICABLE
- UNRESOLVED_WITH

No aggregate alignment score is permitted.

## Pass A — Reconstruction

Encode the frozen specimen into voice events and relations. Derive only:
- materially supported constitutional tensions,
- omissions,
- defeaters,
- unresolved authority states,
- reconstructable warrant status.

Pass A may not use raw vote count as a decision rule.

## Pass B — Blind independent reconstruction

A reviewer receives only the Pass-B package, not PR #451 discussion or Pass-A narrative, and must answer:
1. What was claimed?
2. What was observed?
3. Which authority applied?
4. What disagreed?
5. What was omitted?
6. What remains unresolved?
7. What action, if any, was warranted?

Primary success criterion: the reviewer reconstructs the principal conflict and authority state from the graph alone without inventing missing authority or converting agreement count into warrant.

## Pass C — Adversarial mutation

Mutate the fixture one condition at a time:
1. remove an authority reference;
2. duplicate one underlying source as two apparent independent voices;
3. invert a tool-state result;
4. remove a minority finding;
5. upgrade UNKNOWN independence to VERIFIED without evidence;
6. convert a NOT_APPLICABLE normative record to SUPPORT without applicability evidence.

The system should detect the mutation or materially change the resolution.

## Falsifiers

CT-001 fails if any of the following occurs:

1. Raw majority determines warrant.
2. Green CI is interpreted as constitutional approval.
3. One underlying source is counted as two independent voices.
4. UNKNOWN independence becomes demonstrated independence.
5. Human commentary can rewrite a frozen AI/industry finding.
6. AI/industry findings can rewrite recorded human authority.
7. A regulatory or standards node is treated as applicable without an applicability record.
8. Absence of a signal becomes evidence that no issue exists.
9. Minority evidence disappears from the final reconstruction.
10. An independent reviewer cannot reproduce the principal resolution using only the Pass-B graph package.

## External-norm handling

CT-001 is an internal repository-governance specimen. External regulation is not presumed applicable. If no specific external legal or standards provision is necessary to resolve the specimen, the external normative voice must be represented as `NOT_APPLICABLE` or `UNKNOWN`, never silently counted as support.

## Non-goals

CT-001 does not test:
- acoustic or harmonic sonification;
- production B2B runtime connectors;
- legal compliance;
- human-subject behavioral research;
- model cognition or hidden chain of thought;
- whether PR #451 should merge;
- whether the Seed Constitution is normatively correct.

## Registration note

This Git commit is the preregistration boundary for CT-001. Results must be committed later and must reference this commit without modifying the preregistered hypothesis or falsifiers.
