# Evidence-Bearing Resource Brokerage Control Substrate

Issue #711 implements a generic brokerage/control layer in Resource Miner.

## Canonical chain

```text
OPPORTUNITY
→ REQUIREMENT
→ RESOURCE
→ SUITABILITY
→ AUTHORIZATION
→ OUTCOME
```

The broker does not require HumanAIOS-local capability. Provider classes are:

```text
HUMANAIOS_INTERNAL
LOCAL_MACHINE
OPEN_SOURCE
EXTERNAL_SERVICE
DATASET
HUMAN_EXPERT
OTHER
```

## Stage semantics

### Opportunity — BOP-*

Represents external demand: bounty, program, challenge, procurement request, research problem, or other bounded opportunity.

Requires provenance-bearing evidence.

### Requirement — BRQ-*

Compiles opportunity demand into an explicit capability requirement.

Carries:
- required affordances;
- acceptable resource types;
- method permission state;
- target scope state;
- whether external state change is allowed;
- evidence.

### Resource

Uses the existing ResourceCandidate object.

A resource is supply, not authority.

```text
RESOURCE_AVAILABILITY != CAPABILITY_EVIDENCE
OPEN_SOURCE_AVAILABILITY != AUTHORIZATION
INSTALLABLE != SAFE_TO_EXECUTE
```

### Constitutional / resource screen — CRS-*

Screens a resource for:
- provenance;
- license;
- permissions;
- network behavior;
- credential requirements;
- external state change;
- auditability;
- least-privilege compatibility.

States:

```text
PASS
PASS_WITH_CONDITIONS
FAIL
UNKNOWN
```

The screen is advisory/evidentiary only.

### Suitability — BSA-*

Compares one resource against one requirement.

States:

```text
ADEQUATE
PARTIAL
INADEQUATE
UNKNOWN
```

A resource must carry provenance-bearing evidence.

A capable resource may still be unsuitable because of license, provenance, privilege, auditability, or other screening failures.

```text
CAPABILITY_MATCH != METHOD_PERMISSION
SUITABILITY != AUTHORIZATION
```

### Authorization — BAU-*

Initial action classes:

```text
REVIEW_RESOURCE_METADATA
COMPOSE_CAPABILITY_PACKAGE
INSTALL_LOCAL_RESOURCE
EXECUTE_EXTERNAL_TOOL
SUBMIT_FINDING
```

Decisions:

```text
AUTHORIZED_BOUNDED
REQUIRE_HUMAN
DENY
NOT_APPLICABLE
```

Policy:

- metadata review and capability composition may receive bounded broker-review authority when suitability is sufficient;
- installation requires explicit human authorization;
- external tool use or submission cannot be automatically authorized;
- external action requires explicit method permission, explicit in-scope state, and explicit human authorization;
- unknown or inadequate suitability fails closed.

This module has no executor. An `AUTHORIZED_BOUNDED` decision does not perform the action.

### Outcome — BOT-*

Records what happened after a broker decision.

States:

```text
REVIEW_COMPLETED
RESOURCE_ACCEPTED
RESOURCE_REJECTED
NO_SUITABLE_RESOURCE
EXECUTION_NOT_ATTEMPTED
EXECUTION_REPORTED
```

Every outcome preserves exact opportunity → requirement → resource → suitability → authorization lineage.

Outcome receipts always return to:

```text
authority_effect = NONE
```

Therefore:

```text
OUTCOME_SUCCESS != AUTHORITY_EXPANSION
```

## HackerOne-style use

A bug-bounty program can act as the opportunity source.

Example:

```text
BOP: bounty program
 ↓
BRQ: passive public HTTP inspection
 ↓
RES: open-source read-only HTTP inspection project
 ↓
CRS: provenance/license/privilege/network screen
 ↓
BSA: capability coverage assessment
 ↓
BAU:
   REVIEW_RESOURCE_METADATA -> may be bounded
   EXECUTE_EXTERNAL_TOOL -> requires human + scope + method permission
 ↓
BOT: review or execution outcome receipt
```

This layer is source-agnostic and does not depend on the separate HackerOne adapter implementation in PR #682.

## Non-goals

This implementation does not:
- contact HackerOne;
- scan or test third-party targets;
- install open-source software;
- execute external tools;
- submit findings;
- infer bounty eligibility;
- infer asset scope from capability;
- create future authority from successful outcomes.

## Core invariants

```text
OPPORTUNITY != REQUIREMENT
REQUIREMENT != RESOURCE
RESOURCE_AVAILABILITY != CAPABILITY_EVIDENCE
CAPABILITY_MATCH != METHOD_PERMISSION
SUITABILITY != AUTHORIZATION
AUTHORIZATION != EXECUTION
OUTCOME_SUCCESS != AUTHORITY_EXPANSION
OPEN_SOURCE_AVAILABILITY != AUTHORIZATION
TOOL_CAPABILITY != PROGRAM_PERMISSION
INSTALLABLE != SAFE_TO_EXECUTE
LICENSED != IN_SCOPE
BROKER_MATCH != WARRANT
BROKER_MATCH != EXECUTION
```

Session graph: issue #711.
