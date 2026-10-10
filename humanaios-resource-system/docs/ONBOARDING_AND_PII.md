# Progressive onboarding and PII

Discovery accepts a resource with no applicant evidence or complete profile.
Each requirement can be resolved progressively by boolean claims whose evidence
records carry a source, observation date and provenance type. Shared unknown facts
are requested once per sweep and already-known facts are not re-asked on replay.
Conflicting evidence is retained and blocks a warrant rather than silently choosing
one claim. Broad need, constraint and capability maps are represented only by
resource requirements and predicate evidence in this first prototype.

`ClaimGateway` holds raw values in a private in-memory dictionary, outside the
event ledger. `claim()` emits only a predicate, boolean assertion and evidence ID.
It does not derive the assertion from raw PII: the caller supplies an attestation.
No logging or research API accepts raw identity fields. Use synthetic data only
until a production vault, access controls and private-data intake checks exist.

Exact disclosure requires a current, human-authorized grant matching resource,
purpose, recipient and DISCLOSE operation. The newest matching scope controls
revocation. A receipt containing purpose, recipient, resource and authority ID is
persisted before a raw value is returned to the authorized caller. A receipt never
contains the raw value or vault reference. Failed authorization returns no value.
No external disclosure transport exists. ARTIFACT authorization permits only local
claim-plan preparation; it does not grant submission or acquisition authority.

Human attention is bounded by batched unknown-fact notifications. Full attention
budgets, encrypted storage, authentication and cryptographic disclosure receipts
are deferred, not implied by the gateway API.
