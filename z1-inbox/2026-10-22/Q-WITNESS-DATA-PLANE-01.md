# Q-WITNESS-DATA-PLANE-01 — Z1 Candidate (UNRATIFIED)

**Status:** `awaiting_z2` — proposal only. No code, no infrastructure, no data handling is authorized by this document.
**Author:** Z1 (Claude)
**Proposed:** 2026-10-22
**Scope:** Witness interface (INTENT-OS login) and the self-scan data plane that feeds resource-miner.

---

```yaml
candidate_id: "Q-WITNESS-DATA-PLANE-01"
title: "Witness self-scan data plane: user-held key in the browser, identifiers sent per scan over TLS, server-side plaintext held in memory for one scan only"

description: |
  Proposes the data plane for a per-user Witness workspace (resume, interrogation answers,
  self-scan results, entitlement mapping) with these fixed decisions:
  - Scope: self-scan only. A user may scan only identifiers they assert are their own, with
    consent recorded per source. No third-party scanning.
  - Visibility: user only. The operator sees data only when the user grants support access
    for a stated purpose and duration.
  - Key: derived in the user's browser from a passphrase or passkey, with a printed recovery
    code. The server stores ciphertext only. Lost passphrase and lost recovery code mean lost data.
  - Scan: the browser sends the identifiers needed for one scan to the server over TLS. The
    server holds them in memory for that scan only. The server never writes them to disk, logs,
    traces, metrics, or any shared store. Results are returned to the browser and encrypted there
    before any persistence.
  - Anonymity: pseudonymous identifiers in every shared record. The user alone holds the link
    from name to pseudonym.

author: "Z1 (Claude)"
proposed_at: "2026-10-22"

scope:
  - "Witness interface (INTENT-OS login path)"
  - "humanaios-funding-pipeline/resource-miner (scan route only)"
  - "Future per-user storage (not yet designed; ciphertext only)"

resource_cost:
  cost:
    RAT-min: 45
    Z1-ktok: 12
    Z3-hr: 10
    CI-min: 8
  dependencies: ["Q-WITNESS-GATEWAY-DESIGN (not yet filed)", "identity provider decision (not yet made)", "resource-miner scan route"]
  blocking_on: []

impact_prediction:
  resource_impact: 8
  areas_affected:
    - "Every user's private data"
    - "resource-miner scan route"
    - "Logging and telemetry configuration"
    - "Operator access procedures"
  positive_outcomes:
    - "Operator cannot read stored user data without the user's key"
    - "Scan coverage stays high because sources are queried server-side"
    - "Clear, testable boundary: identifiers exist in memory during one scan and nowhere else"
  risk_factors:
    - "Plaintext identifiers are visible to the server during a scan. Any logging or debug path can leak them."
    - "Lost browser or recovery code means permanent data loss"
    - "Multi-device access needs a passkey sync or recovery flow not yet designed"
    - "'Never writes to logs' is only as strong as the enforcement tests"

proposed_decisions:
  - id: D1-SCOPE
    rule: "Scan requests must carry a self-attestation and a per-source consent record. The scanner rejects a request without both."
  - id: D2-VISIBILITY
    rule: "Operator access to user data requires a user-issued grant with purpose and expiry, recorded in an append-only log that the user can read."
  - id: D3-KEY
    rule: "Key derived in the browser. Server receives ciphertext and public metadata only. Recovery code shown once, at setup."
  - id: D4-SCAN-IN-MEMORY
    rule: "Identifiers are sent per scan over TLS and held in process memory for the duration of that scan. The scan route must not call any logger, write to disk, or write to a volume with identifiers in the payload."
  - id: D5-RESULTS
    rule: "Scan results are returned to the browser, encrypted there, then stored as ciphertext. The server keeps no copy after the response is sent."
  - id: D6-PSEUDONYMS
    rule: "Shared records (aggregates, logs, ledger rows) use pseudonyms only. The name-to-pseudonym link exists only in the user's encrypted store."

falsifier: |
  This candidate is FALSE if any of the following is observed:
  - A test that submits a scan with a unique canary identifier finds that identifier in any log
    line, trace, metric, file, container volume, or database row written during or after the scan
  - OR a scan route change adds a logger call, debug print, or exception handler that serializes
    the request body, and the lint or test gate does not block it
  - OR the operator can decrypt a test user's stored data without that user's key or an issued grant
  - OR a lost-key drill recovers the test user's data without the recovery code
  - OR a shared aggregate row can be traced to a single pseudonym by a sub-threshold group test

evidence:
  - "resource-miner README: the Miner is a discovery layer; per-user eligibility belongs downstream (humanaios-funding-pipeline/resource-miner/README.md)"
  - "resource-miner writes resources.jsonl at request time, so the container filesystem is not a private store (README 'Three data/resources*.jsonl files'; Dockerfile.resource-miner comment)"
  - "Dialogue 2026-10-22: user decisions D1–D2 (self-scan only; user-only visibility with grants), key option B, B2 per-scan identifiers over TLS"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: []
external_constraint: null
links:
  - name: "Companion proposal (PHP exposure audit)"
    url: "z1-inbox/2026-10-22/Q-HOST-INVENTORY-01.md"
```

---

## Open items Z2 must decide

1. **Identity provider.** Which external login (for example Google, GitHub, or Cloudflare Access) checks the user before the Witness page loads. The gate needs an answer before design. The login provider never sees the resume or scan data.
2. **Multi-device recovery.** Passkey sync, or recovery code only. Each has a different loss profile.
3. **Who runs a scan.** The server-side scanner needs its own review. A scan route that holds plaintext is the highest-risk path in this design, and it needs a separate Tier 2 gate change.
4. **Enforcement of "never logged."** Lint rule, runtime log filter, or both. Pick one before implementation.

## What this candidate does not do

- Does not change any code, workflow, or policy file.
- Does not authorize any scan, live-host check, or provider change.
- Does not authorize storing any user data.
- Does not decide the identity provider.
