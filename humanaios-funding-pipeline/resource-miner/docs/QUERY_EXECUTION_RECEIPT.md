# One-Shot Query Execution Receipt

Issue #706 adds `QRC-*`, the first post-authorization evidence object in the queryable-registry path.

## Canonical progression

```text
RQY-* Subject-Scoped Registry Query Plan
  ↓
OAG-* Observation Authorization
  ↓
PRIVATE RUNTIME
  |- resolves SUBJ-* to private query values
  |- performs the authorized read-only observation
  ↓
QRC-* Query Execution Receipt
  ↓
RMO-* Registry Match Observations [0..N]   # later layer
```

This implementation does **not** perform the registry query.

## Purpose

QRC answers a narrow question:

> Was one exact OAG authorization consumed once for one bounded observation, within the authorized query/origin/consequence scope?

QRC does not establish entitlement, ownership, eligibility, or claim authority.

## Required lineage

Each receipt binds:

- `OAG-*` authorization ID/token;
- canonical OAG SHA-256;
- `RQY-*` query ID/token;
- RQY plan SHA-256;
- OAG policy receipt SHA-256;
- registry Mine;
- pathway OPP;
- opaque `SUBJ-*`;
- private subject-binding attestation `PSB-*`;
- executed semantic fields;
- observed origin;
- opaque execution nonce `EXE-*`;
- start/end timestamps;
- bounded result state/count;
- deterministic authorization consumption key;
- QRC integrity hash.

Minting requires **both** the exact RQY and the OAG. The same `authorization_covers_query()` guard used by the authorization layer must still pass.

## Private subject binding

The public receipt carries only:

```text
subject_ref = SUBJ-*
private_subject_binding_attestation_id = PSB-*
private_subject_binding_attested = true
```

The `PSB-*` is an opaque private-ledger reference. It must not be derived by unsalted hashing of a claimant name, DOB, SSN, address, email, phone, or other low-entropy identity value.

QRC does not accept or persist:

- claimant/search values;
- raw query parameters;
- raw request body;
- raw response;
- cookies;
- auth/session tokens;
- private claim IDs;
- hashes directly derived from low-entropy claimant values.

## One-shot consumption

Historical OAG objects remain immutable.

One-shot consumption is evidenced by the QRC ledger:

```text
OAG:
  decision = ALLOW_OBSERVATION
  consumption_state = UNUSED
  max_executions = 1

QRC ledger:
  no prior receipt for authorization
  ↓
  first QRC accepted

QRC ledger:
  prior receipt has same authorization_id or consumption_key
  ↓
  second QRC rejected
```

The deterministic consumption key is derived from the authorization ID.

The runtime append path uses an exclusive file lock around read/check/append and fsyncs the receipt before releasing the lock. This prevents a local check-then-append race from consuming the same OAG twice.

The default local ledger is:

```text
data/query-execution-receipts.jsonl
```

and is git-ignored.

## Execution scope

Before minting, QRC requires:

- OAG schema/policy identity is supported;
- OAG ID/token recompute correctly;
- OAG policy receipt hash is intact;
- decision = `ALLOW_OBSERVATION`;
- authority effect = `OBSERVATION_ONLY`;
- operation = `OBSERVE_REGISTRY_QUERY_RESULTS`;
- execution state = `NOT_EXECUTED`;
- consumption state = `UNUSED`;
- one-shot / max executions = 1;
- consequence ceiling = `EVIDENCE_ONLY`;
- no external state change;
- no consequential action permission;
- no claim-submission permission;
- private subject binding required;
- exact supplied RQY is covered by the OAG;
- executed semantic fields exactly equal the RQY field set;
- observed origin is within the OAG target origins.

The receipt itself records:

```text
external_state_change = false
consequential_actions_permitted = false
claim_submission_permitted = false
prohibited_action_executed = false

authorization_consumed = true
authorization_consumption_ordinal = 1

evidence_effect = OBSERVATION_RECEIPT_ONLY
authority_effect = NONE
```

Authority returns to `NONE`: QRC is evidence that bounded authority was consumed, not a new authority token.

## Result states

Initial result states:

### ZERO_MATCHES_OBSERVED

Requires:

```text
observed_record_count = 0
```

Semantics:

```text
ZERO_MATCHES_OBSERVED != NO_ENTITLEMENT
```

### MATCHES_OBSERVED

Requires:

```text
observed_record_count > 0
```

Semantics:

```text
MATCHES_OBSERVED != OWNERSHIP
MATCHES_OBSERVED != ELIGIBILITY
MATCHES_OBSERVED != CLAIM_AUTHORIZED
MATCHES_OBSERVED != FUNDS_RECOVERED
```

### OBSERVATION_FAILED

Requires:

```text
observed_record_count = null
```

An observation failure is not a zero-result observation.

## Receipt integrity

The receipt ID is derived from:

```text
authorization_id + execution_nonce
```

The final `receipt_sha256` covers the canonical public QRC payload.

Deserialization rejects a receipt whose payload no longer matches its integrity hash.

This is an integrity mechanism, not a cryptographic identity signature. A later runtime-hardening increment may bind receipts to a signing key or hardware-backed attestor.

## CLI

The receipt-only CLI records an observation already completed by a private runtime:

```bash
python3 -m resource_miner.cli record-registry-query-execution \
  --query-plan /private-safe/rqy.json \
  --authorization /private-safe/oag.json \
  --private-subject-binding-attestation-id PSB-BBBBBBBBBBBBBBBB \
  --query-field owner_name \
  --query-field last_known_location \
  --observed-origin-key unclaimedproperty.colorado.gov \
  --execution-nonce EXE-CCCCCCCCCCCCCCCC \
  --started-at 2026-10-04T09:00:00Z \
  --finished-at 2026-10-04T09:00:01Z \
  --result-state ZERO_MATCHES_OBSERVED \
  --observed-record-count 0
```

The command does not contain a registry transport and cannot perform the observation itself.

## Next layer

QRC establishes that an observation happened within the authorized envelope.

It does not model the returned records.

The next semantic layer is:

```text
RMO-* Registry Match Observation [0..N]
```

which should project privacy-minimized candidate registry records into evidence without promoting them to ownership, eligibility, or claim authority.

Session graph: issue #706.
