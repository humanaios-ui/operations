# NF_LEDGER Schema (Phase 1)

**File:** `.claude/skills/pr-manager/nf_ledger.jsonl`  
**Format:** JSONL (one JSON entry per line, append-only)  
**Purpose:** Immutable audit trail for all authority events

## Hash Chain

Each entry commits SHA256(prior_entry_hash | this_entry_json) to provide tamper evidence.

```
Entry 1: hash = sha256("" | entry_1_json)
Entry 2: hash = sha256(entry_1_hash | entry_2_json)
Entry 3: hash = sha256(entry_2_hash | entry_3_json)
...
```

## Entry Types

### SIGNATURE_VALIDATION
Logged when a message signature is validated.

```json
{
  "event_type": "SIGNATURE_VALIDATION",
  "message_id": "msg_t1_001",
  "sender": "claude-z1",
  "result": "PASS",
  "key_id": "z1_pub_key_2026_09_22",
  "timestamp": "2026-09-22T20:00:00Z",
  "hash": "sha256(...)"
}
```

### MESSAGE_DELIVERY
Logged when a message successfully parses and enters DELIVERY state.

```json
{
  "event_type": "MESSAGE_DELIVERY",
  "message_id": "msg_001",
  "recipient": "bridge",
  "visibility": "PRIVATE",
  "epistemic": "CLAIMED",
  "timestamp": "2026-09-22T20:00:00Z",
  "hash": "sha256(...)"
}
```

### TOKEN_ISSUED
Logged when Z2 issues authority token.

```json
{
  "event_type": "TOKEN_ISSUED",
  "token_id": "ratify_token_v0.3_oi_bridge_01",
  "issued_by": "night-z2",
  "issued_to": "claude-z1",
  "scope": "RATIFY_CANDIDATE_G-OI-BRIDGE-01-v0.3",
  "expires_at": "2026-12-22T22:45:06Z",
  "timestamp": "2026-09-22T20:00:00Z",
  "hash": "sha256(...)"
}
```

### TOKEN_CONSUMED
Logged when token is consumed for an action.

```json
{
  "event_type": "TOKEN_CONSUMED",
  "token_id": "ratify_token_v0.3_oi_bridge_01",
  "consumed_by": "z3_executor",
  "action": "RATIFY_CANDIDATE_G-OI-BRIDGE-01-v0.3",
  "timestamp": "2026-09-22T20:05:00Z",
  "hash": "sha256(...)"
}
```

### CONSEQUENTIAL_ACTION
Logged when Z3 executor performs authority-backed action.

```json
{
  "event_type": "CONSEQUENTIAL_ACTION",
  "message_id": "msg_001",
  "action": "MERGE_PR_445",
  "actor": "z3_executor",
  "token_consumed": "ratify_token_...",
  "result": "SUCCESS",
  "timestamp": "2026-09-22T20:05:00Z",
  "hash": "sha256(...)"
}
```

### ESCALATION
Logged when bridge escalates to HUMAN_REQUIRED.

```json
{
  "event_type": "ESCALATION",
  "message_id": "msg_001",
  "reason": "SIGNATURE_INVALID",
  "disposition": "HUMAN_REQUIRED",
  "timestamp": "2026-09-22T20:00:00Z",
  "hash": "sha256(...)"
}
```

### DISPOSITION
Logged when Z2 makes a disposition decision.

```json
{
  "event_type": "DISPOSITION",
  "message_id": "msg_001",
  "decision": "CONTINUE_WITH_TOKEN",
  "decided_by": "night-z2",
  "timestamp": "2026-09-22T20:00:00Z",
  "hash": "sha256(...)"
}
```

## Validation & Audit

```python
# Read and validate ledger
ledger = read_ledger("nf_ledger.jsonl")

# Validate hash chain
for i, entry in enumerate(ledger):
    if i == 0:
        expected_hash = sha256("" | json(entry))
    else:
        expected_hash = sha256(ledger[i-1].hash | json(entry))
    
    if entry.hash != expected_hash:
        raise Exception(f"TAMPER DETECTED at entry {i}")

# Queries
tokens_for_message("msg_001")  # All tokens associated with message
escalations_to_human_required()  # All escalations needing Z2 decision
message_history("msg_001")  # All events for a message
```

## Phase 1 Goals

- [x] Schema definition
- [ ] Ledger writer (append entry, compute hash)
- [ ] Ledger reader (validate hash chain)
- [ ] Audit queries (by message, by token, by escalation)
- [ ] Integration with bridge state machine
- [ ] NF_LEDGER initial entry (schema validation)
