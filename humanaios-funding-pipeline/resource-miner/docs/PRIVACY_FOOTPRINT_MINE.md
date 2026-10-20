# Privacy Footprint Mine v0.1

Status: **read-only Z1 research candidate**. It is not a production privacy
service and has no action authority.

## Purpose

The user-facing idea is **My AI Footprint**. The Resource Miner component is the
**Privacy Footprint Mine**. It inspects only text the user explicitly supplies
for one bounded audit and projects possible privacy-resource needs.

```text
INTENT-OS objective
  -> OAG consent grant
  -> RQY in-memory audit
  -> privacy-minimized observation or linkage candidate
  -> conditional Resource Requirement
  -> separate human review
  -> QRC receipt
```

The mine is registered as `USER_CONTROLLED_DATASET` and `EVIDENCE_SOURCE` only.
It is not an `OPPORTUNITY_SOURCE`, so the persistent Mine resolver cannot scan
it automatically or turn private source text into a public opportunity.

## Implemented now

- One explicit OAG-style grant bound to one exact RQY query ID.
- Trusted execution-time checks for issuance, expiry, and revocation.
- User-supplied AI chat exports, public-profile snapshots, or activity logs.
- In-memory detection of email addresses, phone numbers, and IPv4 addresses.
- Exact normalized-identifier recurrence across supplied sources.
- HMAC-SHA-256 value and source commitments using a caller-held key.
- Evidence locations without raw values or snippets.
- Conditional privacy-tool requirements for Resource Miner.
- User review that separates factual confirmation from `SEEK_REPAIR`.
- QRC-style receipt with `authority_effect: NONE` and `execution: DISABLED`.
- Explicit `NOT_CALIBRATED` confidence state; no invented probability score.

## Not implemented

- OAuth, provider APIs, web crawling, or public-profile fetching.
- Chat export parsers or archive decompression.
- Health, relationship, occupation, location, or other attribute inference.
- A global uniqueness or re-identification probability.
- Storage, accounts, dashboards, deletion, provider setting changes, or export.
- Claims about what an AI provider, adversary, or other person actually knows.

Later attribute inference needs its own versioned method contract, sensitive
class consent, calibration evidence, user correction path, and false-positive
measurement. It must not silently enter this explicit-pattern detector.

## Governing semantics

```text
OBSERVED != PROVIDER_KNOWLEDGE
LINKAGE_CANDIDATE != COMMON_IDENTITY
FINDING != PRIVACY_DEFICIT
USER_CONFIRMED != SEEK_REPAIR
RESOURCE_REQUIREMENT != AUTHORIZATION
QRC_RECEIPT != INDEPENDENT_ATTESTATION
PATTERN_MATCH != CALIBRATED_CONFIDENCE
ZERO_MATCHES_OBSERVED != NO_EXPOSURE
```

An unreviewed finding creates only a `CONDITIONAL` requirement. The requirement
becomes `CONFIRMED` only when the user confirms the finding and separately
chooses `SEEK_REPAIR`. Even then, it remains a discovery input. It cannot change
an account, delete data, contact a provider, or authorize another agent.

## Data boundary

Raw content stays in the caller-owned `PrivacySource` object. The object hides
content from its default representation. The result carries only:

- opaque source IDs;
- keyed content commitments;
- keyed value commitments;
- line, column, and span length;
- bounded claim language;
- conditional resource requirements.

The caller must provide a private pseudonymization key of at least 32 bytes.
The key is never placed in the result. Different keys break cross-run token
linkability. A durable local client may reuse one protected key when the user
explicitly wants longitudinal comparison.

The current grant carries a caller-supplied human-authorization receipt
reference, but this slice does not verify a cryptographic signature or maintain
a spent-grant ledger. Binding the OAG to one exact RQY prevents substitution;
authenticated consent-origin and replay enforcement remain later controls.
Both the request timestamp and the trusted host execution instant must be inside
the grant window, and neither may be at or after revocation. The Python API has
an injectable clock for deterministic tests; the CLI always uses its host clock
and accepts no request-supplied execution-time override.

A normalized `privacy_tool` type does not by itself establish every privacy
capability. Specific affordances such as `redaction` or `local_processing` are
attached only when the candidate's evidence text supports them.

## Synthetic test

```bash
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_privacy_footprint.py' -v
python3 -m resource_miner.privacy_footprint_cli \
  --input fixtures/privacy_footprint_synthetic.json --pretty
```

The command also accepts the request on stdin. It creates an ephemeral in-memory
HMAC key, so commitments from separate CLI runs are intentionally not linkable.
Longitudinal comparison belongs in a local client that calls the Python API with
a protected caller-owned key.

The committed fixture uses reserved example data only: `example.test`, a 555
number, and the documentation address block `192.0.2.0/24`. Its synthetic grant
has a deliberately long test-only expiry so the command remains reproducible;
real clients should issue short-lived grants.
