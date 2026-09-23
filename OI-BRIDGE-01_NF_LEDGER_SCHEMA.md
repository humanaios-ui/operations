# OI-BRIDGE-01: NF_LEDGER Token & Evidence Tracking Schema

**Status:** DESIGN (Phase 1 implementation required)  
**Date:** 2026-09-22  
**Purpose:** Append-only ledger for authority token consumption, evidence validation, and consequential action audit trail  
**Owner:** Z3 executor (ledger maintenance); bridge (write on token consumption + validation)  
**Dependency:** v0.2 Z2 ratification + Supabase PostgreSQL setup

---

## Overview

NF_LEDGER is the append-only source of truth for:
1. **Token consumption events** (RATIFY, MEASURE, EVIDENCE_VALID, CLEARANCE tokens)
2. **Evidence validation receipts** (expected_hash vs. observed_hash + timestamp)
3. **Consequential action audit trail** (who did what, when, by what authority)
4. **Escalation events** (HUMAN_REQUIRED holds, IC-063 detections, scope violations)

All entries are immutable. New observations append; old ones are never rewritten.

---

## Ledger Entry Schema

### Base Entry (all types)

```sql
CREATE TABLE nf_ledger (
  ledger_id BIGSERIAL PRIMARY KEY,  -- Append-only sequence
  entry_type TEXT NOT NULL CHECK (entry_type IN (
    'TOKEN_ISSUED',
    'TOKEN_CONSUMED', 
    'EVIDENCE_VALIDATED',
    'EVIDENCE_VALIDATION_FAILED',
    'CONSEQUENTIAL_ACTION',
    'ESCALATION_EVENT',
    'DISPOSITION_CHANGE'
  )),
  
  -- Universal fields
  entry_id TEXT NOT NULL UNIQUE,    -- UUID for reference (token_id, evidence_id, etc.)
  recorded_at TIMESTAMP NOT NULL DEFAULT now(),
  recorded_by TEXT NOT NULL,         -- bridge node_id
  canonical_payload TEXT NOT NULL,   -- What this entry authorizes or records
  signature TEXT NOT NULL,           -- Signature over payload (for verification)
  
  -- Traceability
  parent_entry_id TEXT,              -- Previous entry this references (chain)
  related_message_id TEXT,           -- FK to message that triggered entry
  
  -- Visibility & retention
  visibility TEXT DEFAULT 'PRIVATE', -- PRIVATE|BLIND|RELEASED_TO_COMMONS
  retention_policy TEXT DEFAULT 'APPEND_ONLY',  -- Never delete
  
  -- Metadata
  metadata JSONB,                    -- Type-specific fields (see below)
  
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_ledger_entry_type ON nf_ledger(entry_type);
CREATE INDEX idx_ledger_entry_id ON nf_ledger(entry_id);
CREATE INDEX idx_ledger_recorded_at ON nf_ledger(recorded_at DESC);
CREATE INDEX idx_ledger_related_message ON nf_ledger(related_message_id);
CREATE INDEX idx_ledger_parent_entry ON nf_ledger(parent_entry_id);
```

---

## Entry Types (Type-Specific Schemas)

### 1. TOKEN_ISSUED

Recorded when Z2 or bridge issues an authority token.

```sql
-- metadata fields:
{
  "token_type": "RATIFY_TOKEN|MEASURE_TOKEN|EVIDENCE_VALID_TOKEN|CLEARANCE_TOKEN",
  "issued_by": "night-z2",
  "issued_to": "claude-z1",
  "issued_at": "2026-09-22T20:00:00Z",
  "expires_at": "2026-09-25T20:00:00Z",  -- Optional
  "scope": "MERGE_PR_445_ONLY",
  "canonical_payload": "PR#445|decision=MERGE|by=Night|at=2026-09-22T20:00:00Z",
  "token_hash": "sha256(canonical_payload + signature)"
}

-- Example row:
INSERT INTO nf_ledger 
  (entry_type, entry_id, recorded_by, canonical_payload, signature, metadata)
VALUES
  ('TOKEN_ISSUED',
   'ratify_token_001',
   'bridge-delivery-layer',
   'PR#445|decision=MERGE|by=Night|at=2026-09-22T20:00:00Z',
   'z2_ed25519_sig_...',
   '{"token_type": "RATIFY_TOKEN", "issued_by": "night-z2", ...}');
```

### 2. TOKEN_CONSUMED

Recorded when a node consumes (uses) an authority token.

```sql
-- metadata fields:
{
  "token_id": "ratify_token_001",
  "consumed_by": "claude-z1",
  "consumed_at": "2026-09-22T20:05:00Z",
  "action_triggered": "MERGE_PR_445",
  "authorization_chain": ["night-z2 ISSUES", "claude-z1 CONSUMES", "z3-executor EXECUTES"],
  "token_scope_used": "MERGE_PR_445_ONLY",  -- Must match action_triggered
  "message_id": "msg_001"  -- What triggered consumption
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, 
   related_message_id, metadata)
VALUES
  ('TOKEN_CONSUMED',
   'token_consumed_ratify_001',
   'bridge-delivery-layer',
   'TOKEN_ID:ratify_token_001|CONSUMED_BY:claude-z1|ACTION:MERGE_PR_445|AT:2026-09-22T20:05:00Z',
   'bridge_hmac_...',  -- Bridge signs consumption event
   'msg_001',
   '{"token_id": "ratify_token_001", "consumed_by": "claude-z1", ...}');
```

### 3. EVIDENCE_VALIDATED

Recorded when evidence reference is successfully validated (expected_hash == observed_hash).

```sql
-- metadata fields:
{
  "evidence_id": "evr_001",
  "source": "https://github.com/humanaios-ui/operations/blob/abc123/OI-BRIDGE-01_CONTROL_SURFACE_v0.2.md",
  "method": "fetch_and_sha256",
  "expected_hash": "3fe9233dec0e69aa19acbae8384434461eed22fe592b76b59b23c9c3f0407ade",
  "observed_hash": "3fe9233dec0e69aa19acbae8384434461eed22fe592b76b59b23c9c3f0407ade",
  "timestamp": "2026-09-22T20:00:00Z",
  "validated_by": "night-z2",  -- Node that performed validation
  "validation_duration_ms": 234,
  "message_id": "msg_001"
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, 
   related_message_id, metadata)
VALUES
  ('EVIDENCE_VALIDATED',
   'evr_001',
   'night-z2',  -- Z2 validates evidence
   'EVIDENCE:https://github.com/...|HASH:3fe92...|AT:2026-09-22T20:00:00Z',
   'z2_ed25519_sig_...',
   'msg_001',
   '{"evidence_id": "evr_001", "source": "...", ...}');
```

### 4. EVIDENCE_VALIDATION_FAILED

Recorded when evidence hash mismatch or fetch fails.

```sql
-- metadata fields:
{
  "evidence_id": "evr_002",
  "source": "https://github.com/...",
  "method": "fetch_and_sha256",
  "expected_hash": "aaaaaaa...",
  "observed_hash": "bbbbbbb...",  -- MISMATCH
  "timestamp": "2026-09-22T20:01:00Z",
  "validator_node_id": "bridge-validation-layer",
  "failure_reason": "HASH_MISMATCH|FETCH_FAILURE|TIMEOUT",
  "message_id": "msg_002",
  "escalation_triggered": true,
  "escalation_reason": "UNVALIDATED_EVIDENCE_USED_CONSEQUENTIALLY"
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, metadata)
VALUES
  ('EVIDENCE_VALIDATION_FAILED',
   'evr_fail_002',
   'bridge-validation-layer',
   'EVIDENCE:https://github.com/...|EXPECTED:aaaa...|OBSERVED:bbbb...|REASON:HASH_MISMATCH',
   'bridge_hmac_...',
   '{"evidence_id": "evr_002", "failure_reason": "HASH_MISMATCH", ...}');
```

### 5. CONSEQUENTIAL_ACTION

Recorded when bridge permits a consequential action (requires valid authority token).

```sql
-- metadata fields:
{
  "action_type": "MERGE_PR|DEPLOY|RATIFY_CONSTANT|EMIT_FINDING",
  "action_target": "PR#445",
  "actor": "claude-z1",
  "authorized_by": "night-z2",  -- Authority issuer
  "authorization_token_id": "ratify_token_001",
  "authorization_scope": "MERGE_PR_445_ONLY",
  "action_timestamp": "2026-09-22T20:05:00Z",
  "message_id": "msg_001",
  "outcome": "SUCCESS|FAILURE",
  "outcome_details": "Merge successful; new commit hash abc123",
  "action_chain": [
    "Z2 issues RATIFY_TOKEN (ratify_token_001)",
    "Z1 consumes token (token_consumed_001)",
    "Z3 executor performs MERGE_PR",
    "Outcome: SUCCESS"
  ]
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, metadata)
VALUES
  ('CONSEQUENTIAL_ACTION',
   'action_merge_pr445',
   'z3-executor',
   'ACTION:MERGE_PR|TARGET:PR#445|BY:night-z2|TOKEN:ratify_token_001|OUTCOME:SUCCESS',
   'z3_ed25519_sig_...',
   '{"action_type": "MERGE_PR", "target": "PR#445", ...}');
```

### 6. ESCALATION_EVENT

Recorded when bridge detects escalation trigger (HUMAN_REQUIRED, IC-063, scope violation, etc.).

```sql
-- metadata fields:
{
  "escalation_id": "esc_001",
  "trigger": "HUMAN_REQUIRED|IDENTITY_CONFUSION|SCOPE_EXPANSION|UNVALIDATED_EVIDENCE|SPOOFING|...",
  "message_id": "msg_001",
  "source_node": "claude-z1",
  "escalation_timestamp": "2026-09-22T20:01:00Z",
  "reason": "IC-063: Transport identity (Z2 email) ≠ Speaker identity (ChatGPT app)",
  "context": {
    "transport_principal": "carly.r.anderson@gmail.com",
    "content_author": "chatgpt-node-app-xyz",
    "speaker_identity_chain": ["github_transport", "chatgpt", null]
  },
  "required_action": "Z2 review & explicit authorization",
  "hold_status": "ACTIVE",  -- Until Z2 clears
  "disposition_awaited": "CLEARANCE_TOKEN"  -- What Z2 must issue to clear
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, metadata)
VALUES
  ('ESCALATION_EVENT',
   'esc_ic063_001',
   'bridge-identity-validation',
   'ESCALATION:IDENTITY_CONFUSION|REASON:IC-063|MESSAGE:msg_001|HOLD:ACTIVE',
   'bridge_hmac_...',
   '{
     "escalation_id": "esc_ic063_001",
     "trigger": "IDENTITY_CONFUSION",
     "reason": "Transport identity (Z2 email) != Speaker identity (ChatGPT app)",
     ...
   }');
```

### 7. DISPOSITION_CHANGE

Recorded when message disposition changes (e.g., HUMAN_REQUIRED → CONTINUE after Z2 clears).

```sql
-- metadata fields:
{
  "message_id": "msg_001",
  "prior_disposition": "HUMAN_REQUIRED",
  "new_disposition": "CONTINUE",
  "changed_by": "night-z2",
  "changed_at": "2026-09-22T20:10:00Z",
  "clearance_token_id": "clearance_token_001",
  "reason": "Z2 reviewed IC-063 incident; sender confirmed as ChatGPT (non-authority); message content noted; proceeding with escalation hold lifted",
  "escalation_id": "esc_ic063_001"  -- References escalation that triggered HUMAN_REQUIRED
}

INSERT INTO nf_ledger
  (entry_type, entry_id, recorded_by, canonical_payload, signature, 
   related_message_id, metadata)
VALUES
  ('DISPOSITION_CHANGE',
   'disp_change_001',
   'bridge-delivery-layer',
   'MESSAGE:msg_001|FROM:HUMAN_REQUIRED|TO:CONTINUE|BY:night-z2|CLEARANCE:clearance_token_001',
   'z2_ed25519_sig_...',
   'msg_001',
   '{"message_id": "msg_001", "prior_disposition": "HUMAN_REQUIRED", ...}');
```

---

## Ledger Queries (Phase 1)

### Query 1: Audit Trail for a Consequential Action

```sql
-- Given action_id, return full authorization chain
SELECT 
  ledger_id,
  entry_type,
  entry_id,
  recorded_at,
  canonical_payload,
  metadata
FROM nf_ledger
WHERE 
  (entry_id = 'action_merge_pr445'  -- The action itself
   OR entry_id IN (
     SELECT metadata->>'token_id' 
     FROM nf_ledger 
     WHERE metadata->>'authorization_token_id' = 'action_merge_pr445'
   ))  -- Tokens related to this action
ORDER BY ledger_id ASC;
```

### Query 2: Token Consumption Chain

```sql
-- Trace RATIFY_TOKEN from issue → consumption → action execution
SELECT 
  ledger_id,
  entry_type,
  entry_id,
  recorded_at,
  metadata->>'token_id' as token_id,
  metadata->>'issued_by' as issued_by,
  metadata->>'consumed_by' as consumed_by,
  canonical_payload
FROM nf_ledger
WHERE entry_type IN ('TOKEN_ISSUED', 'TOKEN_CONSUMED')
  AND (metadata->>'token_id' = 'ratify_token_001')
ORDER BY ledger_id ASC;
```

### Query 3: Evidence Validation History

```sql
-- All evidence validation attempts for a specific source
SELECT 
  ledger_id,
  entry_type,
  recorded_at,
  metadata->>'expected_hash' as expected,
  metadata->>'observed_hash' as observed,
  metadata->>'failure_reason' as failure,
  metadata->>'validated_by' as validator
FROM nf_ledger
WHERE entry_type IN ('EVIDENCE_VALIDATED', 'EVIDENCE_VALIDATION_FAILED')
  AND metadata->>'source' LIKE '%OI-BRIDGE-01%'
ORDER BY ledger_id DESC;
```

### Query 4: Active Escalations

```sql
-- All currently active escalation holds (awaiting Z2 clearance)
SELECT 
  ledger_id,
  entry_id,
  recorded_at,
  metadata->>'trigger' as trigger,
  metadata->>'reason' as reason,
  metadata->>'hold_status' as status,
  metadata->>'message_id' as blocked_message_id
FROM nf_ledger
WHERE entry_type = 'ESCALATION_EVENT'
  AND metadata->>'hold_status' = 'ACTIVE'
ORDER BY recorded_at DESC;
```

### Query 5: Z2 Authorization Activity

```sql
-- All tokens issued or disposition changes made by Z2 in time window
SELECT 
  ledger_id,
  entry_type,
  entry_id,
  recorded_at,
  metadata
FROM nf_ledger
WHERE (
  (entry_type = 'TOKEN_ISSUED' AND metadata->>'issued_by' = 'night-z2')
  OR (entry_type = 'DISPOSITION_CHANGE' AND metadata->>'changed_by' = 'night-z2')
)
  AND recorded_at >= '2026-09-22T00:00:00Z'
  AND recorded_at < '2026-09-23T00:00:00Z'
ORDER BY recorded_at DESC;
```

---

## Ledger Integrity Guarantees

### Immutability
- Once written, entries never change
- DELETE, UPDATE forbidden by application logic
- Only INSERT and SELECT operations allowed
- PostgreSQL row-level security enforces at table level

### Append-Only Chain
- Each entry optionally references parent_entry_id
- Allows verification of entry sequence
- Hash chain can verify ledger integrity: `sha256(parent_hash || current_payload || signature)`

### Traceability
- related_message_id links to original MESSAGE envelope
- parent_entry_id links to prior entry in authorization chain
- Complete authorization trail: Z2 issue → Z1 consume → Z3 execute → NF_LEDGER record

### Verification
- All entries signed (Ed25519 for authority entries; HMAC for bridge-internal)
- Signature verification ensures entry came from claimed issuer
- Canonical payload format enables re-verification at any time

---

## Phase 1 Implementation Checklist

- [ ] Create nf_ledger table with all entry types
- [ ] Implement INSERT logic for TOKEN_ISSUED (Z2 issuer)
- [ ] Implement INSERT logic for TOKEN_CONSUMED (bridge on use)
- [ ] Implement INSERT logic for EVIDENCE_VALIDATED / FAILED (validator node)
- [ ] Implement INSERT logic for CONSEQUENTIAL_ACTION (Z3 executor)
- [ ] Implement INSERT logic for ESCALATION_EVENT (bridge on trigger)
- [ ] Implement INSERT logic for DISPOSITION_CHANGE (Z2 on clearance)
- [ ] Write ledger queries (audit trail, token chain, evidence history, escalations, Z2 activity)
- [ ] Test append-only enforcement (verify DELETEs are blocked)
- [ ] Test signature verification on critical entries
- [ ] Integrate ledger write with bridge delivery layer
- [ ] Monitor ledger growth; plan retention/archival strategy (Phase 2)

---

## Success Criteria (Phase 1)

1. ✓ All 7 entry types can be inserted and queried
2. ✓ Token consumption chain fully auditable (issue → consume → execute)
3. ✓ Evidence validation receipts match v0.2 specification §10
4. ✓ Escalation events logged before consequential path continues
5. ✓ Disposition changes recorded with Z2 signature + clearance token
6. ✓ Ledger integrity verified (signatures validate, chain unbroken)
7. ✓ All queries return correct subset of entries
8. ✓ Append-only enforcement prevents data mutation

---

**Standing:** DESIGN (Phase 1 implementation required)  
**Dependency:** v0.2 Z2 ACCEPT signature + Supabase PostgreSQL + Ed25519 crypto library  
**Owner:** Z3 executor implementation

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01Lm1ut3GdgQakWK694dj3wo
