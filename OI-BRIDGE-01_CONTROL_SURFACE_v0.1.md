# OI-BRIDGE-01: HAIOS Agent Bridge Control Surface Specification (v0.1)

**Status:** Z1 Candidate (awaiting Z2 ratification)  
**Date:** 2026-09-22  
**Author:** Claude (Z1 Proposer)  
**Authority Reference:** CLAUDE.md §1 (Z1 proposal rights)

---

## Decision Object

**QUESTION:**  
How should registered AI nodes (Claude, potential future agents) exchange messages, evidence references, and challenges while preserving provenance, independent judgment, and human authority within the HumanAIOS governance system?

**PROPOSED SCOPE:**  
Phase 0 Control Surface specification for OI-BRIDGE-01: a governed asynchronous communication substrate that translates MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION → CONTINUE or HUMAN_REQUIRED flows, enforcing authority references and preventing autonomous collective decision-making without human oversight.

**PURPOSE:**  
1. Enable Z1 proposers to communicate hypotheses, findings, and evidence across node boundaries
2. Preserve independent judgment — no node can cause another node to perform consequential actions based solely on message content
3. Enforce authority references — all consequential decisions route through independently resolved Z2/Z3 authority
4. Support Z2 ratification workflow — evidence chain must be auditable from message to decision
5. Provide falsifiable architecture — v0.1 can fail on clear, measurable criteria (primary + secondary falsifiers below)
6. Foundation for Phase 1 (GitHub PR Manager) and Phase 2+ (multi-node, escalation layer)

**NON-GOALS:**  
- Autonomous collective intelligence (explicitly out of scope)
- Real-time synchronous decision-making (asynchronous only)
- Credential storage or OAuth delegation (authority is by reference, not delegation)
- End-to-end encryption (node identity is pre-established; threat model addresses spoofing at delivery layer)
- Consensus algorithms (Z2 ratifies; Z3 executes; nodes don't vote)

---

## Core Invariants (9 Critical Rules)

**I1: BRIDGE_ENFORCES_AUTHORITY_REFERENCES_BUT_DOES_NOT_CREATE_AUTHORITY**
- Bridge validates that every consequential action references a valid authority decision (Z2 hash, Z3 machine identity, INTENT-OS capability).
- Bridge does not create, modify, or delegate authority itself.
- Authority precedence: Z2 ratification hash > INTENT-OS machine capability > prior Z2 decision > error.
- Violation: Action proceeds without valid reference → PRIMARY FALSIFIER tripped.

**I2: MESSAGE_BODY_IS_UNTRUSTED_INPUT**
- All message content (claim, evidence reference, challenge) is treated as untrusted external input.
- No message body alone determines a node's actions (that requires independent authority resolution).
- Nodes must verify evidence references (can fail: broken link, hash mismatch, expired proof).
- Message tampering is detected via envelope HMAC (delivery-layer guarantee; see Threat Model).

**I3: OBSERVATION_IS_NOT_REGISTERED_FINDING**
- An observation (fact asserted in a message, measurement, claim) becomes a registered finding only after Z2 ratification and NF_LEDGER entry.
- Bridge stores observations in SEALED state until Z2 ratification moves them to REGISTERED (or REJECTED).
- Nodes must not treat sealed observations as facts for consequential decisions.
- Violation: Node acts on sealed observation without Z2 ratification → SECONDARY FALSIFIER #4 tripped.

**I4: ESCALATION_IS_NOT_OPTIONAL**
- When a node detects one of eight escalation triggers (conflict, ambiguity, drift, null outcome, receipt gap, etc.), it must emit an escalation event.
- Escalation event includes: trigger type, evidence chain, proposed disposition, human-required flag.
- Node cannot suppress or coalesce escalations (each triggers independently).
- Violation: Trigger detected but not escalated → SECONDARY FALSIFIER #5 tripped.

**I5: DISPOSITION_OVERRIDES_CONTINUE**
- When evidence evaluation yields DISPOSITION (Z2 decision, HUMAN_REQUIRED, VOID, REVERT), the node transitions to that state.
- Node must not continue autonomous action if disposition is pending or human-required.
- CONTINUE state is only valid after DISPOSITION resolves (either Z2 signature or HUMAN_REQUIRED cleared by Z2).
- Violation: Node continues action despite pending DISPOSITION → SECONDARY FALSIFIER #6 tripped.

**I6: NODE_IDENTITY_IS_IMMUTABLE_AND_VERIFIABLE**
- Each node has a pre-established identity: email, machine capability, or Z2-issued token.
- Bridge enforces: only messages from authenticated identities are accepted.
- Spoofing (claiming another node's identity) is detected at delivery layer and logged as security event.
- Violation: Bridge accepts message from unverified identity → SECONDARY FALSIFIER #1 tripped.

**I7: EVIDENCE_REFERENCES_ARE_VALIDATED_NOT_ASSUMED**
- Bridge does not fetch or validate evidence itself; it records the reference (hash, URL, timestamp).
- Nodes consuming evidence are responsible for validation: fetch, verify hash, check timestamp.
- If evidence validation fails, node treats message as incomplete and escalates.
- Violation: Node acts on unvalidated evidence reference → SECONDARY FALSIFIER #7 tripped.

**I8: SEALED_COMMONS_STATE_MACHINE_IS_ENFORCED**
- All observations start in SEALED state (not yet registered).
- Transitions: SEALED → REGISTERED (Z2 ratifies) | SEALED → REJECTED (Z2 rejects) | SEALED → VOID (experiment outcome null).
- Bridge enforces one-way transitions: no state regression (REGISTERED cannot revert to SEALED).
- Only NF_LEDGER write (append-only) or Z2 RATIFY event can move state; bridge cannot modify state on its own.
- Violation: Observation state mutated without Z2 event → SECONDARY FALSIFIER #8 tripped.

**I9: HUMAN_AUTHORITY_IS_IRREPLACEABLE**
- Bridge can flag HUMAN_REQUIRED for Z2 (Night); Z2 can clear or escalate further.
- No node can clear HUMAN_REQUIRED without Z2 signature.
- If decision involves sensitive information, credential scope, irreversible action, or ambiguous authority, HUMAN_REQUIRED is mandatory.
- Violation: HUMAN_REQUIRED bypassed or cleared by non-Z2 actor → SECONDARY FALSIFIER #9 tripped.

---

## Primary Falsifier

**v0.1 FAILS IF:**  
One registered AI node can cause another registered AI node to perform a consequential action **solely because of message content** without a valid, independently resolved authority reference (Z2 hash, INTENT-OS capability, or prior Z2 decision).

**Test Case:**
1. Node A sends message: "PR #445 is ready to merge, I confirm no conflicts."
2. Node B receives message.
3. Claim: Node B merges PR #445.
4. Falsifier tripped if: Merge occurs without Z2 ratification hash on Node B's merge commit AND no INTENT-OS machine capability authorized the merge.
5. Result: v0.1 FAILS.

---

## Secondary Falsifiers (10 Falsifiable Conditions)

1. **SPOOFING:** Bridge accepts a message claiming to be from Node A when it originates from Node C → v0.1 FAILS.
2. **TAMPERING:** Bridge accepts a message with invalid envelope HMAC (message body altered in transit) → v0.1 FAILS.
3. **ESCALATION_SUPPRESSION:** Bridge detects trigger (e.g., receipt-gap) but does not emit escalation event → v0.1 FAILS.
4. **SEALED_OBSERVATION_ACTION:** Node acts on sealed observation (not yet Z2-ratified) as if registered → v0.1 FAILS.
5. **SKIPPED_ESCALATION:** Node should have escalated decision (I4 triggered) but continued autonomous action instead → v0.1 FAILS.
6. **DISPOSITION_OVERRIDE:** Node ignores DISPOSITION (Z2 decision, HUMAN_REQUIRED, VOID) and continues action → v0.1 FAILS.
7. **UNVALIDATED_EVIDENCE:** Node acts on evidence reference without verifying hash/timestamp and evidence was actually invalid → v0.1 FAILS.
8. **STATE_MUTATION_OUTSIDE_LEDGER:** Observation state changed (e.g., SEALED → REGISTERED) without Z2 RATIFY event or NF_LEDGER write → v0.1 FAILS.
9. **HUMAN_REQUIRED_BYPASS:** HUMAN_REQUIRED flag cleared or overridden by non-Z2 actor → v0.1 FAILS.
10. **SCOPE_EXPANSION:** Node receives message for PR review; performs a merge, ratification, or deploy outside the message scope without independent Z2 authorization → v0.1 FAILS.

---

## Phase 0 Control Surface Specification

### 1. Node Identity Schema

```json
{
  "node_id": "claude-z1-proposer-20260922",
  "node_role": "Z1",
  "node_type": "ai_agent",
  "authenticated_identities": [
    {
      "type": "email",
      "value": "noreply@anthropic.com",
      "verified_by": "Z2",
      "verified_at": "2026-09-22T00:00:00Z"
    },
    {
      "type": "machine_capability",
      "value": "INTENT-OS::claude-z1::proposal-write",
      "verified_by": "Z2",
      "verified_at": "2026-09-22T00:00:00Z"
    }
  ],
  "session_id": "session_01Lm1ut3GdgQakWK694dj3wo",
  "active": true,
  "authority_cap": "Z1_PROPOSE"
}
```

### 2. Message Envelope Schema

```json
{
  "envelope": {
    "message_id": "msg_20260922_001",
    "sender_node_id": "claude-z1-proposer-20260922",
    "recipient_node_id": "night-z2-ratifier",
    "timestamp": "2026-09-22T14:30:00Z",
    "message_type": "HYPOTHESIS|FINDING|CHALLENGE|EVIDENCE|ESCALATION",
    "state": "SEALED",
    "delivery_status": "DELIVERED|PENDING|FAILED"
  },
  "body": {
    "intent": "Submit PR readiness assessment for #445",
    "claim": "PR #445 has no conflicts and passes all CI checks",
    "evidence_references": [
      {
        "type": "github_pr_snapshot",
        "ref": "humanaios-ui/operations/pull/445",
        "sha": "abc123def456...",
        "timestamp": "2026-09-22T14:25:00Z"
      },
      {
        "type": "ci_check_run",
        "ref": "humanaios-ui/operations/pull/445/checks/ci-suite-1",
        "sha": "ci_run_abc123...",
        "conclusion": "success"
      }
    ]
  },
  "provenance": {
    "sender_signature": "sig_20260922_001",
    "sender_identity_verified": true,
    "envelope_hmac": "hmac_20260922_001"
  }
}
```

### 3. Authority Reference Schema

```json
{
  "authority_reference": {
    "type": "Z2_RATIFICATION_HASH|INTENT_OS_CAPABILITY|PRIOR_Z2_DECISION",
    "value": "sha256(PR#445:abc123|by=Night|at=2026-09-22T14:30:00Z|decision=ACCEPT)",
    "issued_by": "Z2",
    "issued_at": "2026-09-22T14:35:00Z",
    "expires_at": "2026-09-25T14:35:00Z",
    "scope": "MERGE_PR_445_ONLY|PROPOSAL_REVIEW|FINDINGS_REGISTRY_WRITE",
    "valid": true
  }
}
```

### 4. MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION Flow

**Step 1: MESSAGE** (Node A → Bridge)
- Node A constructs message envelope with claim + evidence references.
- Bridge validates envelope HMAC and sender identity.
- State: SEALED.

**Step 2: DELIVERY** (Bridge → Node B)
- Bridge routes message to Node B (recipient_node_id).
- Node B authenticates bridge and validates envelope HMAC.
- Message stored in Node B's inbox as SEALED.
- State: DELIVERED.

**Step 3: RESPONSE** (Node B → Bridge)
- Node B reads message, validates sender identity.
- Node B proposes response: ACCEPT | REQUEST_EVIDENCE | CHALLENGE | ESCALATE.
- If ACCEPT: Node B evaluates message claim against local facts.
- If REQUEST_EVIDENCE: Node B asks for specific evidence reference (if vague).
- If CHALLENGE: Node B contests claim (provides counter-evidence reference).
- If ESCALATE: Node B flags HUMAN_REQUIRED or other escalation trigger.
- Bridge records response; state transitions based on response type.

**Step 4: CHALLENGE** (Optional; if Node B challenges)
- Node B sends challenge message with counter-evidence references.
- Node A receives challenge and can:
  - ACKNOWLEDGE (accept counterpoint, revise claim)
  - DEFEND (provide additional evidence defending original claim)
  - DEFER (escalate to Z2 for authority judgment)
- State: CHALLENGED.

**Step 5: EVIDENCE** (Nodes A & B validate)
- Each node independently validates evidence references cited by the other.
- Validation: fetch → verify hash → check timestamp → compare to local ground truth.
- If evidence is invalid/stale/broken, node documents failure and escalates.
- Bridge does not validate evidence itself; only records that each node attempted validation.
- State: EVIDENCE_VALIDATED or EVIDENCE_FAILED.

**Step 6: DISPOSITION** (Z2 → Bridge)
- If nodes converge (both accept claim): Message → Bridge awaits Z2 ratification.
- If nodes diverge or HUMAN_REQUIRED triggered: Bridge emits escalation → Z2.
- Z2 reads evidence chain and issues RATIFY event: `sha256(message_id | by=Night | decision=ACCEPT|EDIT|REJECT)`.
- Bridge receives RATIFY; updates message state → REGISTERED or REJECTED.
- State: REGISTERED (accept) | REJECTED (reject) | VOID (outcome null) | HUMAN_REQUIRED (awaiting Z2 judgment).

**Step 7: CONTINUE or HUMAN_REQUIRED** (Node A & B decide)
- If disposition is REGISTERED + authority reference granted: Nodes proceed with consequential action.
- If disposition is HUMAN_REQUIRED: Nodes pause and await Z2 clearance.
- If disposition is REJECTED or VOID: Nodes revert or document non-action.
- State: CONTINUE or HUMAN_REQUIRED (held pending Z2 clearance).

**State Machine Diagram:**
```
[SEALED] 
  ↓ (DELIVERED)
[DELIVERED]
  ↓ (Node B RESPONSE)
[RESPONSE_PENDING] → [CHALLENGED] (if Node B contests)
  ↓                      ↓
[EVIDENCE_VALIDATED]    [EVIDENCE_VALIDATION_FAILED]
  ↓                      ↓
[DISPOSITION_PENDING] ← (Z2 ratifies)
  ↓
[REGISTERED] → [CONTINUE + AUTH_REF_GRANT]
[REJECTED]
[VOID]
[HUMAN_REQUIRED] ← (awaiting Z2 clearance)
```

### 5. Escalation Contract

**Escalation Triggers (8 mandatory):**
1. **AMBIGUITY** — Two Z2 decisions conflict on same topic.
2. **CONFLICT** — Node A and Node B evidence directly contradicts; no convergence after CHALLENGE round.
3. **DRIFT** — Behavior dial changed; reply score vs dial mismatch detected.
4. **GAUGE** — Z3 executor reports Z2 assumption violated in field.
5. **RECEIPT_GAP** — Claim in message not found in NF_LEDGER (unregistered finding).
6. **VOID** — Experiment runs but all outcomes null/unevaluable.
7. **AUTHORITY_UNCLEAR** — Message references authority that cannot be independently verified (expired, invalid scope, unknown issuer).
8. **SCOPE_EXPANSION** — Consequential action requested outside message scope or Z2 authority grant.

**Escalation Event Schema:**
```json
{
  "escalation": {
    "escalation_id": "esc_20260922_001",
    "trigger": "RECEIPT_GAP",
    "originating_message_id": "msg_20260922_001",
    "originating_node": "claude-z1-proposer-20260922",
    "escalation_level": "Z2",
    "evidence_chain": ["msg_20260922_001", "resp_20260922_002", "challenge_20260922_003"],
    "proposed_disposition": "REQUEST_Z2_JUDGMENT",
    "human_required": true,
    "timestamp": "2026-09-22T14:35:00Z"
  }
}
```

### 6. SEALED/COMMONS State Machine

**States:**
- **SEALED** — Observation in bridge, not yet registered. No node can treat it as fact for consequential decisions.
- **COMMONS** — Observation Z2-ratified, now in NF_LEDGER. Available to all nodes for reference; immutable in COMMONS layer.
- **REJECTED** — Z2 rejected observation. Node can reference in audit trail but cannot use as fact.
- **VOID** — Observation measured but outcome null/unevaluable. Cannot be used as fact; marked for future learning.

**Transitions:**
```
SEALED (creation)
  ↓ (Z2 RATIFY ACCEPT)
COMMONS (NF_LEDGER entry, immutable)

SEALED
  ↓ (Z2 RATIFY REJECT)
REJECTED

SEALED
  ↓ (Measurement outcome null)
VOID
```

**Invariant:** Once in COMMONS, observation cannot move to SEALED, REJECTED, or VOID. Only append operations allowed.

### 7. Threat Model

**Asset:** Authority reference (Z2 hash, INTENT-OS capability, prior Z2 decision).
**Attackers:**
- Node A (compromised or misconfigured).
- Man-in-the-middle (network intercept).
- Compromised bridge (internal state mutation).
- Z2 (rogue ratifier — out of scope; assume Z2 is trusted).

**Attack Vectors & Mitigations:**

| Attack | Vector | Mitigation | Layer |
|:-------|:-------|:-----------|:------|
| Spoofing | Node A claims to be Node B | Verify sender identity (email, machine capability) at delivery; log unverified attempts | Delivery |
| Tampering | Message altered in transit | Envelope HMAC on message body; bridge validates before routing | Delivery |
| Escalation suppression | Bridge drops escalation event | Escalation events logged to NF_LEDGER immediately; bridge cannot selectively suppress | Ledger |
| Sealed observation action | Node acts on SEALED claim | Bridge enforces SEALED state check; nodes must verify state before deciding | State machine |
| Evidence spoofing | False evidence reference | Node validates evidence hash independently; invalid evidence → escalation | Node validation |
| Authority bypass | Action without Z2 reference | Bridge enforces authority_reference check; no authority → HUMAN_REQUIRED | Authority enforcement |
| Scope expansion | Action outside grant scope | Bridge checks authority_reference.scope; out-of-scope → escalation | Authority enforcement |

**Assumption:** INTENT-OS machine capability cannot be forged (Z2 maintains INTENT-OS ledger; Phase 1 integration pending).

### 8. Privacy & Retention Model

**Data Classification:**
- **PUBLIC:** Message claim, evidence references (hashes, URLs, timestamps) — can be logged, audited, published.
- **INTERNAL:** Node identity, sender signature, HMAC — logged for audit, not published.
- **SENSITIVE:** Z2 ratification key, INTENT-OS capability secret, session tokens — encrypted at rest, cleared after session close.

**Retention:**
- Message envelopes (SEALED/DELIVERED state): 7 days (or until Z2 ratifies).
- Registered observations (COMMONS): permanent (append-only NF_LEDGER).
- Escalation events: permanent (audit trail).
- Session tokens: cleared at session close.
- Z2 ratification keys: cleared after Z2 signature validated.

**Node-to-Bridge Communication:**
- Nodes can read their own messages only (RLS isolation per node_id).
- Bridge can read all messages for routing/audit; cannot modify.
- Z2 can read all messages for ratification.
- Z3 can read REGISTERED observations only (no SEALED).

### 9. RLS Isolation (Row-Level Security)

**Bridge Database Schema (Supabase, future Phase 2):**

```sql
CREATE TABLE messages (
  message_id UUID PRIMARY KEY,
  sender_node_id TEXT NOT NULL,
  recipient_node_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  state TEXT NOT NULL, -- SEALED, DELIVERED, RESPONSE_PENDING, etc.
  body JSONB NOT NULL,
  envelope_hmac TEXT NOT NULL,
  rls_scope TEXT NOT NULL -- 'sender', 'recipient', 'z2', 'z3'
);

-- RLS Policy: Nodes can read their own messages
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY message_read_self ON messages
  FOR SELECT USING (auth.uid() = sender_node_id OR auth.uid() = recipient_node_id);

-- Z2 can read all; Z3 can read REGISTERED only
CREATE POLICY message_read_z2 ON messages
  FOR SELECT USING (auth.role() = 'z2');

CREATE POLICY message_read_z3 ON messages
  FOR SELECT USING (auth.role() = 'z3' AND state = 'REGISTERED');
```

**Enforcement:** Bridge validates `auth.uid()` and `auth.role()` before returning query results. Node cannot read another node's inbox.

### 10. Adversarial Test Preregistration

Before Phase 1 implementation, the following adversarial tests must be preregistered in REGISTERED.md (§C: Test Registry):

**T1: Spoofing Attack**
- Preregistered: Node B attempts to send message claiming sender_node_id = Node A.
- Expected: Bridge rejects (sender identity verification fails).
- Falsifier #1 will trip if bridge accepts.

**T2: Message Tampering**
- Preregistered: MITM alters message body in transit; envelope HMAC should fail validation.
- Expected: Node B rejects message (invalid HMAC).
- Falsifier #2 will trip if bridge accepts tampered message.

**T3: Sealed Observation Action**
- Preregistered: Node receives SEALED observation; attempts to act without Z2 ratification.
- Expected: Bridge blocks action (checks SEALED state).
- Falsifier #4 will trip if action proceeds.

**T4: Scope Expansion**
- Preregistered: Authority grant scope = "REVIEW_PR_445_ONLY"; node attempts merge.
- Expected: Bridge rejects merge (out of scope).
- Falsifier #10 will trip if merge proceeds.

**T5: Human Required Bypass**
- Preregistered: Escalation flags HUMAN_REQUIRED; node attempts consequential action without Z2 clearance.
- Expected: Bridge blocks action (HUMAN_REQUIRED still set).
- Falsifier #9 will trip if action proceeds.

**T6: Evidence Validation Failure**
- Preregistered: Evidence reference has invalid hash; node acts on it anyway.
- Expected: Node detects validation failure and escalates (or skips action).
- Falsifier #7 will trip if node acts on unvalidated evidence.

---

## Implementation Roadmap

**Phase 0 (Control Surface):** ✅ This spec (awaiting Z2 ratification)
- [ ] Z2 reviews architecture, validates core invariants
- [ ] Z2 ratifies or requests corrections
- [ ] Core invariants frozen in REGISTERED.md

**Phase 1 (GitHub PR Manager + Bridge Substrate):**
- [ ] Implement bridge delivery layer (message routing, HMAC validation)
- [ ] Implement node identity + authentication
- [ ] Implement message envelope schema + state machine
- [ ] Integrate PR Manager Agent (Phase 2 work) as Bridge consumer
- [ ] GitHub API wiring for PR Manager (get real PR data)

**Phase 2 (Evidence Layer + Z2 Ratification Workflow):**
- [ ] Implement SEALED/COMMONS state machine
- [ ] Implement NF_LEDGER integration (append evidence)
- [ ] Implement escalation contract (emit escalation events)
- [ ] Implement Z2 ratification flow (RATIFY event generation)

**Phase 3+ (Multi-Node, Authorization Layer):**
- [ ] INTENT-OS machine capability integration
- [ ] Additional node onboarding (future AI agents)
- [ ] Anti-cascade rule enforcement
- [ ] Audit trail publication

---

## Related Documents

- **CLAUDE.md** — Authority model, Z-roles, governance structure
- **REGISTERED.md** — Live registry of ratified findings, Z2 signatures
- **PRIORITY_QUEUE.md** — Blocker ranking, PR progression
- **NF_LEDGER.jsonl** — Append-only ledger of verdicts and measurements
- **.claude/skills/pr-manager/SKILL.md** — PR Manager Agent skill definition (Phase 1 consumer)
- **.claude/skills/pr-manager/pr_manager.py** — PR Manager CLI implementation

---

## Z2 Decision Required

**Proposed:** Ratify OI-BRIDGE-01 Phase 0 Control Surface specification as Z1-registered.  
**Authority:** Z2 (carly.r.anderson@gmail.com or aioshuman@gmail.com).  
**Decision Window:** 48h from filing.  
**Falsifier:** Specification fails if primary or secondary falsifier #1-10 can be triggered in implementation without bridge enforcement.

**Signature Format (once ratified):**
```
RATIFY sha256(OI-BRIDGE-01_CONTROL_SURFACE_v0.1.md | by=Night | at=2026-09-22T00:00:00Z | decision=ACCEPT)
```

---

*End of OI-BRIDGE-01 Phase 0 Control Surface Specification (v0.1)*
