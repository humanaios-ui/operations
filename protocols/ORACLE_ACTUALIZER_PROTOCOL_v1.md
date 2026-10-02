# Oracle + Actualizer Protocol v1.0

Status: DRAFT (experimental, falsifiable)

This protocol defines a thin MVP for Oracle (evidence-bearing warranted state) and Actualizer (authorized next-action proposals). It does not grant new authority.

## Core stance

- Oracle is not ground truth.
- All material claims must carry epistemic status and provenance.
- Actualizer cannot convert uncertainty into authority.
- Human authority remains explicit for consequential decisions.

## Epistemic status requirements

Every rendered claim includes one status badge:

- 🟢 VERIFIED
- 🟡 PARTIALLY_SUPPORTED
- 🔵 INFERRED
- ⚫ DISPUTED
- ❓ UNKNOWN
- 🔴 DEFEATED

Badge visibility is required in summary and detail views.

## Actualizer authority and action constraints

Each action proposal must include:

- goal
- warrant
- authority_basis
- required_preconditions
- execution_plan
- reversibility
- expected_observation
- success_condition
- falsifier
- human_approval_required

Action color is derived from the minimum epistemic status among warrant premises.

Actualizer cannot execute as if VERIFIED when any premise is UNKNOWN or DISPUTED without explicit human override.

## Temporal firewall for execution consequences

Execution consequences are first-class observations but begin as `EXECUTION_CONSEQUENCE_UNVERIFIED`.

- Consequences are visible immediately.
- Consequences enter a minimum 48-hour quarantine window.
- Actualizer cannot cite its own unverified consequences as warrant-upgrading evidence.
- Witness must independently verify with primary evidence before status upgrade.

## Cybersecurity boundary objects (MVP schema support)

The Oracle state model supports:

- AuthorizationGrant
- TrustBoundary
- DelegationGrant
- SafeStopPolicy

These model capability-vs-authority boundaries and escalation/stop behavior.

## Additional governance role

The model includes a fifth function:

- Human archetype: Witch/Warlock
- Implementation role: ProvenanceTopologyAgent

Function: identify hidden dependency paths, authority crossings, shared failure modes, and missing provenance topology.

## Research hypothesis framing

The “Living Computational Constitution” framing is treated as a testable architecture hypothesis.
It is not canonical truth and must remain contestable, evidence-bound, and falsifiable.

## Out-of-scope for this MVP

- No automatic execution engine.
- No authority redefinition.
- No replacement of Witness/Jester adjudication with Oracle synthesis.
