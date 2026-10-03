# Opportunity Claim v1

## Purpose

An **Opportunity Claim** is the evidence-bearing assertion that a bounded Resource Opportunity exists under some represented state and terms.

It sits between discovery and consequential action:

```text
Resource Mine
  -> observation
  -> Resource Opportunity token
  -> Opportunity Claim
  -> verification / falsification
  -> warrant
  -> authority
  -> authorization
  -> action
  -> outcome
```

The claim is deliberately not the opportunity itself. The opportunity has stable identity; the claim is a revisable epistemic object about that opportunity.

## Core invariants

```text
OPPORTUNITY_IDENTITY != OPPORTUNITY_CLAIM
CLAIM_VALIDITY != APPLICANT_ELIGIBILITY
ELIGIBILITY != ATTAINABILITY
ATTAINABILITY != WARRANT
WARRANT != AUTHORIZATION
FALSIFIER != RESOURCE
FALSIFIER_OBSERVED != DELETE_HISTORY
OBSERVATION_FAILURE != FALSIFICATION
```

Resource Miner may create the claim, attach evidence, pre-register falsifiers, and route verification. It may not self-promote eligibility, warrant, authorization, or actionability.

## Identity

A Resource Opportunity has an `OPP-*` identifier and HumanAIOS resource-opportunity URN. Its Opportunity Claim has a separate stable `CLM-*` identifier and opportunity-claim URN derived from that opportunity ID.

Changing a title, value, description, or evidence does not mint a new claim when the same bounded opportunity is still being asserted. A materially different opportunity identity produces a different `OPP-*` and therefore a different `CLM-*`.

## Facets

A claim is not one Boolean. v1 has five independently evaluated facets:

| Facet | Question |
| --- | --- |
| `EXISTENCE` | Does this bounded opportunity actually exist? |
| `CURRENTNESS` | Is it currently open/offered/available? |
| `TERMS` | Are represented value, scope, deadlines and restrictions materially correct? |
| `ELIGIBILITY` | Does a particular applicant satisfy authoritative predicates? |
| `ATTAINABILITY` | Can the evaluated actor complete the acquisition path under current capabilities and constraints? |

Facet states are `UNKNOWN | UNASSESSED | SUPPORTED | CONTRADICTED | FALSIFIED | NOT_APPLICABLE`.

The default Resource Miner boundary is:

```text
EXISTENCE      = SUPPORTED or UNKNOWN
CURRENTNESS    = SUPPORTED or UNKNOWN
TERMS          = SUPPORTED or UNKNOWN
ELIGIBILITY    = UNASSESSED
ATTAINABILITY  = UNASSESSED
WARRANT        = NOT_EVALUATED
AUTHORIZATION  = NOT_REQUESTED
ACTIONABILITY  = NOT_ACTIONABLE
AUTHORITY      = NONE
```

## Falsifiers

Every standard facet receives a pre-registered falsifier. A falsifier is a condition that, if observed with provenance-bearing evidence, invalidates its target facet.

Examples:

```text
EXISTENCE
  authoritative correction shows the represented opportunity never existed

CURRENTNESS
  authoritative source says closed / withdrawn / paused / expired

TERMS
  authoritative source materially contradicts value / scope / deadline

ELIGIBILITY
  an authoritative required predicate fails for the evaluated applicant

ATTAINABILITY
  a required acquisition path is unavailable under verified constraints
```

A falsifier evaluation is `UNTESTED | NOT_OBSERVED | OBSERVED | INCONCLUSIVE`. A boolean alone is insufficient; every evaluation requires provenance-bearing evidence.

## Local falsification semantics

Falsification is facet-local unless the existential facet is falsified.

```text
CURRENTNESS falsified
-> overall claim = RETIRED
-> EXISTENCE may remain SUPPORTED
-> historical opportunity identity is preserved

TERMS falsified
-> overall claim = CONTESTED
-> opportunity identity remains intact

EXISTENCE falsified
-> overall claim = FALSIFIED
```

This prevents one failed property from being treated as proof that every proposition about the node was false.

## Overall claim state

v1 derives `UNVERIFIED | OBSERVED | SUPPORTED | CONTESTED | RETIRED | FALSIFIED`. The overall state is descriptive epistemic state only. It never grants action authority.

## Microsoft specimen

```text
Mine: Microsoft for Startups
Opportunity: entry startup-credit path
OPP-*
  -> CLM-*
     EXISTENCE: SUPPORTED
     CURRENTNESS: SUPPORTED when endpoint observation succeeds
     TERMS: SUPPORTED/UNKNOWN depending on material evidence
     ELIGIBILITY: UNASSESSED
     ATTAINABILITY: UNASSESSED
```

If an authoritative endpoint later states the path is closed, the currentness falsifier becomes OBSERVED, `CURRENTNESS=FALSIFIED`, and the claim becomes `RETIRED`; the historical OPP/CLM identity remains.

## HackerOne specimen

The intended opportunity unit is `HackerOne Mine -> Program -> bounty-eligible ScopeAsset -> OPP -> CLM`. If a later authenticated scope observation removes bounty eligibility or the scope asset, currentness or terms can be falsified without asserting that the program never existed. No scope observation grants target-testing authority.

## Repository specimen

A repository issue labeled `bounty` may become an OPP only when the repository is explicitly registered as an `OPPORTUNITY_SOURCE`. A normal issue in an evidence-only HumanAIOS repository never becomes an Opportunity Claim.

## Downstream handoff

Entitlement Navigator may receive the Opportunity Claim alongside the candidate. The handoff preserves its unresolved eligibility facet and rejects claims that already assert upstream eligibility or authorization.

```text
Opportunity Claim
  ELIGIBILITY = UNASSESSED
      -> Entitlement / rule resolver
      -> applicant predicates evaluated
      -> new evidence returned to claim graph
```

## Machine surfaces

- Schema: `schemas/opportunity-claim.v1.schema.json`
- Implementation: `resource_miner/opportunity_claim.py`
- Regression tests: `tests/test_opportunity_claim.py`
