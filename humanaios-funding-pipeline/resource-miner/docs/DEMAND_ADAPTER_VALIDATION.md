# Demand Adapter Validation — Five Opportunity Classes

Issue #713 validates whether radically different demand sources can compile into one Resource Miner demand contract without losing the distinctions that determine whether an opportunity can actually be pursued.

## Shared contract

```text
BOP-* Opportunity
  ↓
DMD-* Demand Profile
  ↓
DMR-* semantic demand requirements
  ↓
BRQ-* brokerable capability requirements
  ↓
Resource / Suitability / Authorization / Outcome
```

DMD records preserve:

- source identity and provenance;
- objective;
- deadline when established;
- requirements;
- constraints;
- eligibility predicates;
- prohibitions;
- deliverables;
- evaluation criteria;
- value/reward signals;
- submission surface;
- source-specific metadata;
- `authority_effect=NONE`.

Requirement modes:

```text
REQUIRED
OPTIONAL
PREFERRED
PROHIBITED
CONDITIONAL
SCORED
```

Semantic classes:

```text
CAPABILITY
ELIGIBILITY
CONSTRAINT
PROHIBITION
DELIVERABLE
EVALUATION
COMPLIANCE_CONTROL
```

## 1. GitHub Issue Demand Adapter

Preserves:

- repository + issue number;
- issue state;
- labels;
- milestone;
- unchecked acceptance-criteria checklist items;
- closing-keyword issue references.

Acceptance criteria become required deliverables.

```text
ISSUE_EXISTS != WORK_AUTHORIZED
ACCEPTANCE_CRITERIA != IMPLEMENTATION_AUTHORITY
```

The adapter records `work_authorized=false`.

## 2. Grants.gov Demand Adapter

Current official REST surface:

```text
https://api.grants.gov/v1/api/search2
https://api.grants.gov/v1/api/fetchOpportunity
```

As of this validation, Grants.gov documents both `search2` and `fetchOpportunity` as not requiring authentication/authorization.

The pure adapter accepts a fetched opportunity record and preserves:

- opportunity number/title;
- agency;
- synopsis/objective;
- response/deadline information;
- applicant types;
- funding instruments;
- funding activity categories;
- cost sharing;
- award floor/ceiling;
- deliverables when available.

Applicant types remain `ELIGIBILITY` requirements and are non-brokerable.

```text
CAPABILITY_FIT != APPLICANT_ELIGIBILITY
ALLOWABLE_ACTIVITY != RESOURCE_AVAILABILITY
```

## 3. SAM.gov Procurement Demand Adapter

Current public opportunity surface:

```text
https://api.sam.gov/opportunities/v2/search
```

SAM.gov documents the public opportunities API as requiring a user API key. This validation implements the pure record adapter only; no credentials or live calls are embedded.

Preserves:

- notice/solicitation identity;
- notice type;
- agency;
- description/SOW;
- mandatory requirements;
- deliverables;
- NAICS;
- set-aside;
- place of performance;
- response deadline;
- prohibitions;
- submission surface.

Set-asides remain eligibility requirements rather than capability requirements.

```text
MANDATORY_REQUIREMENT != WEIGHTED_PREFERENCE
SET_ASIDE != CAPABILITY
```

The adapter records that mandatory requirements are not averageable away.

## 4. Federal Challenge/Prize Demand Adapter

Challenge.gov was sunset on 2026-03-30.

Current public discovery is modeled as:

```text
USA.gov challenge listings
+
agency-hosted rules / participation surface
```

The adapter therefore does not claim a live Challenge.gov transport.

Preserves:

- challenge identity;
- sponsor;
- objective;
- eligibility;
- required submissions/deliverables;
- rules;
- prohibitions;
- IP terms;
- evaluation/judging criteria;
- numeric score weights when stated;
- prize/value signals;
- deadline;
- submission URL.

Scored evaluation criteria remain `SCORED / EVALUATION`; they are not brokered as capabilities merely because they influence judging.

## 5. Compliance Demand Adapter

This validates demand that has no economic opportunity at all.

Normative operators compile as:

```text
MUST / SHALL           -> REQUIRED
MUST NOT / SHALL NOT   -> PROHIBITED
SHOULD                 -> PREFERRED
MAY                    -> OPTIONAL
IF / WHEN              -> CONDITIONAL
explicit numeric weight -> SCORED
```

Brokerable positive controls compile into capability/resource requirements.

Prohibitions never compile into resource demand.

```text
COMPLIANCE_REQUIREMENT != EXECUTION_AUTHORITY
CONTROL_MATCH != COMPLIANCE_VERIFIED
PROHIBITED_REQUIREMENT != RESOURCE_DEMAND
```

## Cross-adapter anti-laundering rules

```text
ELIGIBILITY_PREDICATE != CAPABILITY_REQUIREMENT
PROHIBITED_REQUIREMENT != RESOURCE_DEMAND
EVALUATION_CRITERION != AUTOMATIC_CAPABILITY_REQUIREMENT
DMD != AUTHORIZATION
SOURCE_RECORD != AUTHORITY
```

`compile_broker_requirements()` emits only requirements explicitly marked brokerable and rejects eligibility/prohibited semantics.

## Validation result

The five adapters share the same `humanaios.demand-profile.v1` schema while preserving source-specific semantics.

The regression suite also retains the existing Resource Miner path:

```text
Mine
→ Opportunity
→ Proposition
→ Adjudication
→ Verification work
→ RQY
→ OAG
→ QRC
```

and the evidence-bearing broker:

```text
Opportunity
→ Requirement
→ Resource
→ Suitability
→ Authorization
→ Outcome
```

No applications, bids, challenge submissions, security testing, purchases, or other external mutations are performed by these adapters.
