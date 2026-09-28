# Pilot 001 — Talos (Boundary Control Archetype)

## Scope

This pilot is a functional reconstruction study for issue #498. It does not assign governance authority and does not modify #497 role contracts.

## Fixed-comparison setup

Frozen across variants:

- mission: protect boundary,
- scenarios: `talos_scenarios.json`,
- authority boundary: no boundary expansion, no invented authorization,
- evaluation: expected outcome match + prohibited action check.

Variants compared:

- TALOS-RULES
- TALOS-STATE-MACHINE

## Results summary

`talos_results.jsonl` records eight runs (2 variants x 4 scenarios).

Observed in this baseline:

- both implementations matched all expected outcomes,
- no prohibited-action violations,
- identical mission/environment/evaluation contract remained fixed.

## Lineage claims

`talos_lineage_claims.jsonl` explicitly separates:

- resemblance claims,
- no-direct-lineage declarations,
- contested confidence.

No claim in this pilot is treated as historical transmission unless supported by independent provenance.

## Novelty decomposition (pilot baseline)

- boundary-guard role: `CONCEPTUALLY_OLD`, `MECHANICALLY_OLD`
- explicit state contract: `PROGRAMMATICALLY_OLD`
- cross-task language-mediated adaptation: `UNCERTAIN` (not tested in this baseline)

## Falsifier status

No pilot falsifier triggered in this initial executable baseline. Future variants (symbolic/ML/LLM) must keep the same frozen contract fields for valid comparison.
