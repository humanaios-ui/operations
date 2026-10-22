# Automata Lineage Lab Protocol v1.0

**Status:** DRAFT — requires Zone-2 ratification before any comparative claim is registered as a finding.  
**Related issues:** #498 (this lab), #497 (governance architecture), #499 (market validation).  
**Authority firewall:** `ARCHETYPE/NAME ≠ ROLE CONTRACT ≠ PROGRAM ≠ AUTHORIZATION ≠ TELEMETRY/RECEIPTS`

## 1) Scope boundary

This protocol governs historical/function lineage research only.

- #498 may inform language, controls, and baselines.
- #498 does **not** grant governance authority.
- #498 does **not** modify RoleContracts or constitutional state.
- #498 does **not** establish product-market demand (tracked in #499).

## 2) Pre-registered reconstruction protocol (required)

Before mapping any historical/mythical entity to modern systems:

1. At least two independent formalizers create reconstructions using one fixed template.
2. Reconstructions are published append-only before comparative mapping.
3. Inter-rater agreement is reported (target: Cohen's kappa >= 0.70 for binary attributes).
4. Comparative claims must cite the preregistered reconstruction IDs and decision rules.

### Required reconstruction template

- Entity and primary sources
- Claimed functions
- Inputs/observations
- Outputs/actions
- Internal state (if any)
- Control/feedback loop
- Authority boundary
- Failure modes
- Explicit non-claims

**Constraint:** No modern-AI capability terms are introduced during reconstruction.

## 3) Relation vocabulary

Every lineage edge must use one declared relation type:

- `FORESHADOWS`
- `RESEMBLES`
- `MECHANICALLY_IMPLEMENTED_BY`
- `FORMALIZED_BY`
- `DIRECTLY_INFLUENCED`
- `INDEPENDENTLY_REINVENTED`
- `TECHNOLOGICALLY_DESCENDED_FROM`
- `DISPUTED_LINEAGE`
- `NO_DIRECT_LINEAGE_ESTABLISHED`

Resemblance is not transmission; mythic precedent is not technical prior art.

## 4) Provenance requirements per edge

Each edge must include:

- `source`
- `period`
- `relation_type`
- `evidence_refs`
- `confidence`
- `contested`
- `direct_lineage_claim`

## 5) Pilot 001 (Talos) control rules

Pilot 001 compares implementation variants while freezing:

- mission contract,
- scenario set,
- environment assumptions,
- authority boundaries,
- success/failure scoring rubric.

Allowed progression labels:

- `TALOS-RULES`
- `TALOS-STATE-MACHINE`
- `TALOS-SYMBOLIC`
- `TALOS-ML`
- `TALOS-LLM`
- `TALOS-LLM+HUMANAIOS`

Comparative output must identify whether observed differences are mechanism differences, scale/speed differences, or confounds.

## 6) Novelty decomposition classes

Use dimensioned classification, not one novelty score:

- `CONCEPTUALLY_OLD`
- `MECHANICALLY_OLD`
- `PROGRAMMATICALLY_OLD`
- `ADAPTIVELY_NEW`
- `COMBINATION_NOVELTY`
- `SCALE_NOVELTY`
- `SPEED_NOVELTY`
- `ACCESS_NOVELTY`
- `GENERALITY_NOVELTY`
- `UNCERTAIN`

## 7) Falsifiers

Escalate as unsuccessful / requires molt if any hold:

1. Lineage repeatedly collapses into vague analogy.
2. Functional similarity cannot be separated from transmission claim.
3. Executable reconstructions provide no incremental insight over ordinary historical analysis.
4. Archetype vocabulary increases anthropomorphic/authority confusion.
5. Fixed-contract cross-implementation comparison cannot be reproduced.
6. Novelty classifications cannot be supported by explicit decision rules.

## 8) Required outputs (human + machine)

- Human-readable: protocol + pilot report.
- Machine-readable: lineage schema, scenario data, claims records, run results.

No output in this protocol is an authorization artifact.
