# HumanAIOS Schemas

This directory contains canonical machine-readable contracts used across HumanAIOS repositories.

## System Stance v1

`system_stance_v1.schema.json` defines an **advisory** assessment record.

The authority boundary is absolute:

```text
system stance != authorization
overall_stance = ACT != permission to execute
VERIFIED != permission to execute

advisory_only = true
can_authorize = false
authority_effect = NONE
```

A valid stance record may recommend, abstain, escalate, request evidence, reduce scope, make work reversible, sandbox, or roll back. None of those values grant authority to perform a consequential action.

Authorization remains with the applicable human or governance process outside this schema.

## Subject pinning

Every record must identify the exact repository state being assessed:

```json
{
  "subject": {
    "repository": "humanaios-ui/operations",
    "ref": "<lowercase hexadecimal commit SHA>",
    "scope": "<bounded assessment scope>"
  }
}
```

Branch names, tags, prose labels, or other mutable references are not valid substitutes for the commit-pinned `subject.ref`.

## Evidence

Evidence must state both what was observed and where it can be inspected.

Supported relations:

- `SUPPORTS`
- `CONTRADICTS`

Supported kinds:

- `source`
- `data`
- `test`
- `workflow`
- `decision`
- `other`

The locator must identify a specific inspectable location such as:

```text
path/to/file.ext:123
https://example.org/document#section
```

An evidence locator does not make the evidence true. It makes the basis inspectable.

## Pre-action requirements

Statuses are:

- `OPEN`
- `VERIFIED`
- `BLOCKED`

`VERIFIED` and `BLOCKED` require evidence.

If `overall_stance = ACT`, every pre-action requirement must be `VERIFIED`.

This is still advisory:

```text
all requirements VERIFIED
+ overall_stance ACT
!= authorization to execute
```

## Opportunity scan invariant

A scan with:

```text
status = NOT_STARTED
```

cannot contain discovered opportunities.

This prevents unperformed discovery from being represented as completed observation.

## Golden fixtures

Canonical downstream fixtures live in:

```text
fixtures/system_stance_v1/
```

Current corpus:

- `valid_acquire_evidence.json`
- `invalid_act_with_open.json`
- `invalid_not_started_with_opportunity.json`
- `invalid_verified_without_evidence.json`
- `invalid_non_hex_subject_ref.json`

Downstream implementations should validate against these records in addition to validating against the JSON Schema itself.

The invalid fixtures intentionally isolate the contract invariants that must fail closed.

## Versioning

Changes that alter field meaning, authority semantics, or validation behavior require explicit review and should not be inferred from downstream implementation convenience.

Potential v1.1 additions identified during review include numeric certainty and replay metadata. They are not part of v1 unless separately admitted and implemented.
