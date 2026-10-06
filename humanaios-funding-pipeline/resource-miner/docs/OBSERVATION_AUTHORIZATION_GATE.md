# Observation Authorization Gate

Issue #700 adds an explicit authorization decision between a subject-scoped registry query plan and any later observation execution.

## Canonical progression

```text
REGISTRY MINE
  ↓
PATHWAY OPP
  ↓
RQY-* Subject-Scoped Registry Query Plan
  ↓
OAG-* Observation Authorization Decision
  ↓
QRC-* Query Execution Receipt        # not implemented here
  ↓
RMO-* Registry Match Observation     # not implemented here
```

The OAG layer does **not** execute the query.

## Exact-query binding

The gate authorizes one exact public RQY object.

It computes:

```text
query_plan_sha256 =
  SHA256(canonical JSON of RQY-*)
```

The `OAG-*` identity is derived from:

```text
query_plan_sha256
+ requested_operation
+ policy_id
+ policy_version
```

Any change to the Mine, pathway OPP, subject reference, subject kind, semantic query fields, purpose, response semantics, or other public RQY field changes the digest and invalidates the prior authorization.

The helper `authorization_covers_query()` must return false for a mutated RQY.

## Independent RQY revalidation

OAG does not trust the RQY token by appearance.

Before allowing observation it independently checks:

- schema = `humanaios.registry-query-plan.v1`;
- canonical `RQY-*` ID recomputes from the query content;
- query token matches the recomputed query ID;
- `SUBJ-*` is a privacy-safe subject token;
- evaluated Mine ID matches the RQY Mine;
- target Mine is enabled and kind `REGISTRY`;
- pathway OPP is registered under the evaluated Mine;
- Mine declares `queryable=true`;
- query class matches the Mine contract;
- requested semantic fields are inside the Mine contract;
- query values remain `PRIVATE_RUNTIME_ONLY`;
- both RQY and Mine contract declare `external_state_change=false`;
- input RQY is still planning-only and carries no authority.

## Allowed operation

The initial policy has exactly one allowed operation:

```text
OBSERVE_REGISTRY_QUERY_RESULTS
```

A valid decision is:

```text
decision = ALLOW_OBSERVATION
authority_effect = OBSERVATION_ONLY
execution_state = NOT_EXECUTED
consumption_state = UNUSED

one_shot = true
max_executions = 1

consequence_ceiling = EVIDENCE_ONLY
external_state_change = false
consequential_actions_permitted = false
claim_submission_permitted = false
private_subject_binding_required = true
```

This is deliberately narrower than general external-action authority.

## Private runtime boundary

OAG never receives or stores raw registry search values.

The public chain contains:

```text
SUBJ-*
semantic query-field names
RQY digest
OAG policy receipt
```

The private runtime may later resolve the `SUBJ-*` to actual query values, but those values remain:

```text
PRIVATE_RUNTIME_ONLY
```

Any future `QRC-*` execution receipt must attest that private values were resolved under the authorized subject binding without exposing those values in the public artifact.

## Hard-denied actions

The initial policy hard-denies every operation other than `OBSERVE_REGISTRY_QUERY_RESULTS`.

Explicit prohibited actions include:

- `CREATE_CLAIM`
- `SUBMIT_CLAIM`
- `UPDATE_CLAIM`
- `UPLOAD_DOCUMENT`
- `LOOKUP_PRIVATE_CLAIM_STATUS`
- `CREATE_ACCOUNT`
- `MUTATE_CREDENTIALS`
- `SEND_MESSAGE`
- `MAKE_PAYMENT`
- `PURCHASE`
- `TRANSFER_FUNDS`

Therefore:

```text
OBSERVATION_AUTHORIZATION != CLAIM_AUTHORIZATION
OBSERVATION_AUTHORIZATION != SUBMISSION_AUTHORIZATION
OBSERVATION_AUTHORIZATION != DOCUMENT_AUTHORIZATION
OBSERVATION_AUTHORIZATION != PAYMENT_AUTHORIZATION
```

A denied decision has:

```text
authority_effect = NONE
consumption_state = NOT_APPLICABLE
execution_state = NOT_EXECUTED
```

## Policy receipt

Every decision carries a deterministic `policy_receipt_sha256` over:

- authorization ID;
- RQY digest;
- requested operation;
- decision;
- decision reasons;
- policy ID/version;
- target origins;
- allowed query fields;
- consequence ceiling;
- max executions.

This receipt is evidence of the policy decision, not evidence that execution occurred.

## CLI

Given a public RQY JSON file:

```bash
python3 -m resource_miner.cli authorize-registry-observation \
  --query-plan /tmp/rqy.json
```

The command emits an OAG decision and performs no registry request.

A prohibited operation can be tested explicitly:

```bash
python3 -m resource_miner.cli authorize-registry-observation \
  --query-plan /tmp/rqy.json \
  --requested-operation SUBMIT_CLAIM
```

The expected decision is `DENY`.

## Execution boundary

This implementation stops at authorization.

It does not implement:

- private subject resolution;
- HTTP/browser query execution;
- one-shot consumption;
- query execution receipts;
- registry result parsing;
- claim creation/submission;
- document upload;
- private claim-status access.

Those later surfaces must consume the exact OAG decision rather than infer authority from capability or from the RQY itself.

Session graph: issue #700.
