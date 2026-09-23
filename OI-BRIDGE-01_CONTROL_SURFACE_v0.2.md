# OI-BRIDGE-01: HAIOS Agent Bridge Control Surface Specification (v0.2)

**Status:** Z1 Candidate (v0.2 revision; awaiting Z2 ratification)  
**Date:** 2026-09-22  
**Author:** Claude (Z1 Proposer)  
**Authority Reference:** CLAUDE.md §1 (Z1 proposal rights)  
**Revision Notes:** Incorporates temporal dissolution guard (tokenized authority), identity provenance corrections, and ChatGPT/Copilot review findings.

---

## Executive Summary: Temporal Dissolution Guard

**Core Problem (User Insight):** Time-based governance protocols decay invisibly. A 48-hour decision window auto-expires, a discovery holds for 30 days then forgets—no explicit action required. Autonomous agents contract governance decay without knowing it happened.

**v0.2 Solution: Tokenized Authority.** Replace all time-based state transitions with explicit, consumable tokens:
- **RATIFY_TOKEN**: Z2 explicitly issues token for each ratification (not auto-expiry after 48h).
- **MEASURE_TOKEN**: Bridge explicitly issues token for molt window opening; window closes only when token expires or measurement completes.
- **EVIDENCE_VALID_TOKEN**: Evidence validation timestamp replaced with explicit validity token issued by validating node.

**Result:** Authority is strictly resource-constrained (tokens), not time-constrained. When a node acts, it consumes a token. When tokens are gone, action stops—no silent erosion.

---

## Decision Object

**QUESTION:**  
How should registered AI nodes (Claude, potential future agents) exchange messages, evidence references, and challenges while preserving provenance, independent judgment, and human authority within the HumanAIOS governance system, with governance protocols that do not decay over time?

**PROPOSED SCOPE:**  
Phase 0 Control Surface specification for OI-BRIDGE-01: a governed asynchronous communication substrate that translates MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION → CONTINUE or HUMAN_REQUIRED flows, enforcing tokenized authority references and preventing autonomous collective decision-making without explicit human authorization tokens.

**PURPOSE:**  
1. Enable Z1 proposers to communicate hypotheses, findings, and evidence across node boundaries
2. Preserve independent judgment — no node can cause another node to perform consequential actions based solely on message content
3. Enforce tokenized authority references — all consequential decisions route through independently issued, consumable Z2/Z3 authority tokens
4. Support Z2 ratification workflow — evidence chain must be auditable from message to decision
5. Provide falsifiable architecture — v0.2 can fail on clear, measurable criteria (primary + secondary falsifiers below)
6. Prevent temporal dissolution — no time-based governance decay; only explicit token consumption limits actions
7. Foundation for Phase 1 (GitHub PR Manager) and Phase 2+ (multi-node, escalation layer)

**NON-GOALS:**  
- Autonomous collective intelligence (explicitly out of scope)
- Real-time synchronous decision-making (asynchronous only)
- Credential storage or OAuth delegation (authority is by token reference, not delegation)
- End-to-end encryption (node identity is pre-established; threat model addresses spoofing at delivery layer)
- Consensus algorithms (Z2 ratifies; Z3 executes; nodes don't vote)

---

## Critical Incident: Identity Provenance Failure

**Incident ID:** IC-063 (Identity-Confusion: Transport Identity Masking Speaker Identity)  
**Date Discovered:** 2026-09-22T18:00:00Z  
**Severity:** CRITICAL (affects authority reference resolution)  
**Resolution Status:** OPEN (awaiting Z2 ratification of v0.2 mitigations)

**What Happened:**
- ChatGPT app (linked to user's GitHub account like Claude is) posted review comments on PR #455 via GitHub API.
- Reviewer email appears as "GitHub account owner" (carly.r.anderson@gmail.com), which is also Z2's canonical email.
- System initially interpreted the review as Z2 authority feedback.
- Root cause: Transport identity (GitHub account) ≠ Speaker identity (ChatGPT) ≠ Authority effect (Z2 ratification).

**Impact:**
- Misattribution of ChatGPT feedback as Z2 authority guidance for Phase 0 specification.
- Demonstrates need for explicit provenance envelope separating transport, speaker, and authority planes.

**v0.2 Mitigation:**
- New invariant: **TRANSPORT_IDENTITY_IS_NOT_SPEAKER_IDENTITY** (I10 below).
- Require explicit provenance envelope with `content_author`, `transport_principal`, `human_principal`, `authority_reference` fields.
- All communications carrying authority effect must include cryptographic proof of Z2 identity (Ed25519 signature, not self-asserted).

**T7 Adversarial Test (Preregistered):**
- ChatGPT posts comment via GitHub account; system assumes it's Z2.
- Expected: Bridge rejects (speaker identity not cryptographically linked to Z2).
- Falsifier #11 will trip if bridge accepts.

---

## Core Invariants (10 Critical Rules)

**I1: BRIDGE_ENFORCES_AUTHORITY_TOKENS_BUT_DOES_NOT_CREATE_AUTHORITY**
- Bridge validates that every consequential action references a valid, consumable authority token (Z2 RATIFY_TOKEN, Z3 INTENT-OS machine capability, prior Z2 decision token).
- Bridge does not create, modify, or delegate tokens itself.
- Authority precedence: Z2 RATIFY_TOKEN (cryptographically signed) > Z3 machine capability (INTENT-OS) > prior Z2 decision token > error.
- No time-based auto-expiry: tokens are only consumed when actions are taken or explicitly revoked by issuer.
- Violation: Action proceeds without valid token → PRIMARY FALSIFIER tripped.

**I2: MESSAGE_BODY_IS_UNTRUSTED_INPUT**
- All message content (claim, evidence reference, challenge) is treated as untrusted external input.
- No message body alone determines a node's actions (that requires independent authority token resolution).
- Nodes must verify evidence references (can fail: broken link, hash mismatch, expired proof).
- Message tampering is detected via envelope HMAC (delivery-layer guarantee; see Threat Model).

**I3: OBSERVATION_IS_NOT_REGISTERED_FINDING**
- An observation (fact asserted in a message, measurement, claim) becomes a registered finding only after Z2 RATIFY_TOKEN is issued and NF_LEDGER entry is recorded.
- Bridge stores observations in SEALED state until Z2 issues RATIFY_TOKEN and moves them to COMMONS (REGISTERED).
- Nodes must not treat sealed observations as facts for consequential decisions.
- Violation: Node acts on sealed observation without Z2 RATIFY_TOKEN → SECONDARY FALSIFIER #4 tripped.

**I4: ESCALATION_IS_NOT_OPTIONAL**
- When a node detects one of eight escalation triggers (conflict, ambiguity, drift, null outcome, receipt gap, authority unclear, scope expansion, identity unverified), it must emit an escalation event.
- Escalation event includes: trigger type, evidence chain, proposed disposition, human-required flag.
- Node cannot suppress or coalesce escalations (each triggers independently).
- Violation: Trigger detected but not escalated → SECONDARY FALSIFIER #5 tripped.

**I5: DISPOSITION_TOKENS_OVERRIDE_CONTINUE**
- When evidence evaluation yields DISPOSITION_TOKEN (Z2 RATIFY_TOKEN issued, HUMAN_REQUIRED_TOKEN required, VOID_TOKEN issued, REVERT_TOKEN issued), the node transitions to that state.
- Node must not continue autonomous action if DISPOSITION_TOKEN is pending or if HUMAN_REQUIRED_TOKEN is held by Z2.
- CONTINUE state is only valid after DISPOSITION_TOKEN resolves (either Z2 RATIFY_TOKEN issued or HUMAN_REQUIRED_TOKEN cleared by Z2 counterissuing CLEARANCE_TOKEN).
- Violation: Node continues action despite pending DISPOSITION_TOKEN → SECONDARY FALSIFIER #6 tripped.

**I6: NODE_IDENTITY_IS_IMMUTABLE_AND_VERIFIABLE**
- Each node has a pre-established identity: email, machine capability, or Z2-issued identity token.
- Bridge enforces: only messages from authenticated identities are accepted.
- Spoofing (claiming another node's identity) is detected at delivery layer and logged as security event.
- All authority-carrying communications must include cryptographic proof of speaker identity (Ed25519 signature).
- Violation: Bridge accepts message from unverified identity → SECONDARY FALSIFIER #1 tripped.

**I7: EVIDENCE_REFERENCES_ARE_VALIDATED_NOT_ASSUMED**
- Bridge does not fetch or validate evidence itself; it records the reference (hash, URL, timestamp).
- Nodes consuming evidence are responsible for validation: fetch, verify hash, check timestamp.
- Evidence validation success issues EVIDENCE_VALID_TOKEN (consumable by that node for one action).
- If evidence validation fails, node treats message as incomplete and escalates.
- Violation: Node acts on unvalidated evidence reference → SECONDARY FALSIFIER #7 tripped.

**I8: SEALED_COMMONS_STATE_MACHINE_IS_ENFORCED**
- All observations start in SEALED state (not yet registered).
- Transitions: SEALED → COMMONS (Z2 RATIFY_TOKEN issued) | SEALED → REJECTED (Z2 REJECT_TOKEN issued) | SEALED → VOID (VOID_TOKEN issued).
- Append-only correction dispositions: COMMONS + SUPERSEDED (newer observation replaces), COMMONS + NARROWED (scope reduced), COMMONS + WITHDRAWN (retracted by author), COMMONS + UNRESOLVED (evidence remains contestable).
- Bridge enforces one-way state progression for COMMONS: no state regression (COMMONS cannot revert to SEALED).
- Only Z2 RATIFY_TOKEN, REJECT_TOKEN, or VOID_TOKEN (or NF_LEDGER write by Z3 executor) can move state; bridge cannot modify state on its own.
- Violation: Observation state mutated without Z2 token or NF_LEDGER write → SECONDARY FALSIFIER #8 tripped.

**I9: HUMAN_AUTHORITY_IS_IRREPLACEABLE**
- Bridge can flag HUMAN_REQUIRED_TOKEN request (held by Z2); Z2 can issue CLEARANCE_TOKEN or escalate further.
- No node can clear HUMAN_REQUIRED_TOKEN without Z2 CLEARANCE_TOKEN.
- If decision involves sensitive information, credential scope, irreversible action, or ambiguous authority, HUMAN_REQUIRED_TOKEN is mandatory.
- Violation: HUMAN_REQUIRED_TOKEN bypassed or cleared by non-Z2 actor → SECONDARY FALSIFIER #9 tripped.

**I10: TRANSPORT_IDENTITY_IS_NOT_SPEAKER_IDENTITY (NEW)**
- Messages routed via transport (GitHub, Slack, email API) carry transport_principal (GitHub account, email address used for API call).
- Messages must also declare content_author (who wrote/authorized the content) and human_principal (human authorizing if applicable).
- No authority effect (RATIFY_TOKEN, CLEARANCE_TOKEN, escalation decision) can be inferred from transport_principal alone.
- All authority-carrying communications must include cryptographic proof linking content_author to Z2 (Ed25519 signature over canonical payload).
- Violation: System infers authority from transport identity without cryptographic proof → SECONDARY FALSIFIER #11 tripped.

---

## Primary Falsifier

**v0.2 FAILS IF:**  
One registered AI node can cause another registered AI node to perform a consequential action **solely because of message content** without a valid, independently issued, consumable authority token (Z2 RATIFY_TOKEN, Z3 INTENT-OS machine capability token, or prior Z2 decision token).

**Test Case:**
1. Node A sends message: "PR #445 is ready to merge, I confirm no conflicts."
2. Node B receives message.
3. Claim: Node B merges PR #445.
4. Falsifier tripped if: 
   - Merge occurs without Z2 RATIFY_TOKEN on Node B's merge commit, AND
   - No Z3 INTENT-OS machine capability token authorizes the merge, AND
   - No prior Z2 decision token grants merge authority for this PR.
5. Result: v0.2 FAILS.

**Extended Test Case (Tokenized Authority):**
1. Z2 issues RATIFY_TOKEN for PR #445: `{type: "RATIFY_TOKEN", issued_by: "Z2", target: "PR_445_MERGE", token: "rt_xyz123...", signature: "ed25519_sig_..."}`
2. Node A receives RATIFY_TOKEN.
3. Node A sends message to Node B referencing RATIFY_TOKEN.
4. Node B independently verifies RATIFY_TOKEN (checks Z2 signature, confirms not yet consumed).
5. Node B merges PR #445, consuming RATIFY_TOKEN.
6. Bridge logs consumption; RATIFY_TOKEN cannot be reused.
7. If Node B attempts second merge without new RATIFY_TOKEN: Bridge rejects.
8. Result: v0.2 PASSES (authority is tokenized, consumable, auditable).

---

## Secondary Falsifiers (11 Falsifiable Conditions)

1. **SPOOFING:** Bridge accepts a message claiming to be from Node A (in `content_author` or envelope signature) when it originates from Node C → v0.2 FAILS.
2. **TAMPERING:** Bridge accepts a message with invalid envelope HMAC (message body or envelope header altered in transit) → v0.2 FAILS.
3. **ESCALATION_SUPPRESSION:** Bridge detects trigger (e.g., receipt-gap) but does not emit escalation event → v0.2 FAILS.
4. **SEALED_OBSERVATION_ACTION:** Node acts on sealed observation (not yet Z2 RATIFY_TOKEN issued) as if registered → v0.2 FAILS.
5. **SKIPPED_ESCALATION:** Node should have escalated decision (I4 triggered) but continued autonomous action instead → v0.2 FAILS.
6. **DISPOSITION_OVERRIDE:** Node ignores DISPOSITION_TOKEN (Z2 RATIFY_TOKEN, HUMAN_REQUIRED_TOKEN, VOID_TOKEN) and continues action → v0.2 FAILS.
7. **UNVALIDATED_EVIDENCE:** Node acts on evidence reference without verifying hash/timestamp and evidence was actually invalid → v0.2 FAILS.
8. **STATE_MUTATION_OUTSIDE_LEDGER:** Observation state changed (e.g., SEALED → COMMONS) without Z2 RATIFY_TOKEN or NF_LEDGER write → v0.2 FAILS.
9. **HUMAN_REQUIRED_BYPASS:** HUMAN_REQUIRED_TOKEN cleared or overridden by non-Z2 actor (without Z2 CLEARANCE_TOKEN) → v0.2 FAILS.
10. **SCOPE_EXPANSION:** Node receives message for PR review; performs a merge, ratification, or deploy outside the message scope without independent Z2 authorization token → v0.2 FAILS.
11. **IDENTITY_CONFUSION:** System infers authority effect (ratification, decision, escalation clearance) from transport_principal (GitHub account, email API sender) without cryptographic proof of Z2 speaker identity → v0.2 FAILS.

---

## Phase 0 Control Surface Specification (v0.2)

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
  "authority_cap": "Z1_PROPOSE",
  "public_key_ed25519": "pk_ed25519_..."
}
```

### 2. Message Envelope Schema (v0.2 with Identity Provenance)

```json
{
  "envelope": {
    "message_id": "msg_20260922_001",
    "sender_node_id": "claude-z1-proposer-20260922",
    "recipient_node_id": "night-z2-ratifier",
    "timestamp": "2026-09-22T14:30:00Z",
    "message_type": "HYPOTHESIS|FINDING|CHALLENGE|EVIDENCE|ESCALATION|RATIFICATION",
    "state": "SEALED",
    "delivery_status": "DELIVERED|PENDING|FAILED",
    "transport_principal": "noreply@anthropic.com",
    "content_author": "claude-z1-proposer-20260922",
    "human_principal": null
  },
  "body": {
    "intent": "Submit PR readiness assessment for #445",
    "claim": "PR #445 has no conflicts and passes all CI checks",
    "evidence_references": [
      {
        "type": "github_pr_snapshot",
        "ref": "humanaios-ui/operations/pull/445",
        "sha": "abc123def456...",
        "timestamp": "2026-09-22T14:25:00Z",
        "evidence_valid_token": "evt_20260922_001"
      },
      {
        "type": "ci_check_run",
        "ref": "humanaios-ui/operations/pull/445/checks/ci-suite-1",
        "sha": "ci_run_abc123...",
        "conclusion": "success",
        "evidence_valid_token": "evt_20260922_002"
      }
    ]
  },
  "provenance": {
    "content_author_signature": "sig_ed25519_20260922_001",
    "transport_principal_verified": true,
    "envelope_hmac": "hmac_20260922_001",
    "hmac_covers": "canonical_envelope_serialization"
  }
}
```

### 3. Authority Token Schema (v0.2 New)

```json
{
  "authority_token": {
    "type": "RATIFY_TOKEN|REJECT_TOKEN|VOID_TOKEN|MEASURE_TOKEN|CLEARANCE_TOKEN|EVIDENCE_VALID_TOKEN",
    "token_id": "rt_abc123_20260922",
    "issued_by": "Z2",
    "issued_at": "2026-09-22T14:35:00Z",
    "target_scope": "MERGE_PR_445_ONLY|PROPOSAL_REVIEW|FINDINGS_REGISTRY_WRITE|DECISION_CLEARANCE",
    "issued_to": "claude-z1-proposer-20260922",
    "consumed": false,
    "consumed_at": null,
    "consumed_by_action": null,
    "signature": "ed25519_sig_...",
    "signature_over": "canonical_token_payload"
  }
}
```

### 4. MESSAGE → DELIVERY → RESPONSE → CHALLENGE → EVIDENCE → DISPOSITION Flow (v0.2)

**Step 1: MESSAGE** (Node A → Bridge)
- Node A constructs message envelope with claim + evidence references.
- Node A includes EVIDENCE_VALID_TOKENs for validated evidence (or leaves blank if not yet validated).
- Node A signs envelope using Ed25519 private key (content_author_signature).
- Bridge validates envelope HMAC and sender identity signature.
- State: SEALED.

**Step 2: DELIVERY** (Bridge → Node B)
- Bridge routes message to Node B (recipient_node_id).
- Node B authenticates bridge and validates envelope HMAC + sender signature.
- Message stored in Node B's inbox as SEALED.
- State: DELIVERED.

**Step 3: RESPONSE** (Node B → Bridge)
- Node B reads message, validates sender identity signature.
- Node B validates evidence references (fetches, verifies hashes, checks timestamps).
- If validation succeeds: Bridge issues EVIDENCE_VALID_TOKEN for each reference.
- Node B proposes response: ACCEPT | REQUEST_EVIDENCE | CHALLENGE | ESCALATE.
- If ACCEPT: Node B evaluates message claim against local facts and issues response.
- If REQUEST_EVIDENCE: Node B asks for specific evidence reference (if vague).
- If CHALLENGE: Node B contests claim (provides counter-evidence references).
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
- If validation succeeds: Validating node issues EVIDENCE_VALID_TOKEN.
- If evidence is invalid/stale/broken, node documents failure and escalates.
- Bridge does not validate evidence itself; only records that each node attempted validation and issued tokens.
- State: EVIDENCE_VALIDATED or EVIDENCE_VALIDATION_FAILED.

**Step 6: DISPOSITION** (Z2 → Bridge)
- If nodes converge (both accept claim AND hold EVIDENCE_VALID_TOKENs): Message → Bridge awaits Z2 decision.
- If nodes diverge or HUMAN_REQUIRED_TOKEN_REQUEST triggered: Bridge emits escalation → Z2.
- Z2 reads evidence chain and issues decision token: `RATIFY_TOKEN | REJECT_TOKEN | VOID_TOKEN` signed with Ed25519.
- Bridge receives token; updates message state → COMMONS (if RATIFY_TOKEN) or REJECTED/VOID.
- Bridge consumes token in NF_LEDGER entry (one-time consumption).
- State: COMMONS (accept) | REJECTED (reject) | VOID (outcome null) | HUMAN_REQUIRED (awaiting Z2 CLEARANCE_TOKEN).

**Step 7: CONTINUE or HUMAN_REQUIRED** (Node A & B decide)
- If disposition is COMMONS + authority token consumed: Nodes may proceed with consequential action (if they hold corresponding authority token).
- If disposition is HUMAN_REQUIRED: Nodes pause and await Z2 CLEARANCE_TOKEN.
- If disposition is REJECTED or VOID: Nodes revert or document non-action.
- State: CONTINUE (with consumed token) or HUMAN_REQUIRED (held pending Z2 CLEARANCE_TOKEN).

**State Machine Diagram (v0.2):**
```
[SEALED] 
  ↓ (DELIVERED)
[DELIVERED]
  ↓ (Node B validates evidence, receives EVIDENCE_VALID_TOKENs)
[EVIDENCE_VALIDATED] or [EVIDENCE_VALIDATION_FAILED]
  ↓
[RESPONSE_PENDING] → [CHALLENGED] (if Node B contests)
  ↓                      ↓
[EVIDENCE_VALIDATED]    [EVIDENCE_VALIDATION_FAILED]
  ↓                      ↓
[DISPOSITION_PENDING] ← (Z2 issues RATIFY_TOKEN / REJECT_TOKEN / VOID_TOKEN)
  ↓
[COMMONS] → [CONTINUE + AUTHORITY_TOKEN_CONSUMED]
[REJECTED]
[VOID]
[HUMAN_REQUIRED] ← (awaiting Z2 CLEARANCE_TOKEN)
```

### 5. Escalation Contract (v0.2 Updated)

**Escalation Triggers (8 mandatory):**
1. **AMBIGUITY** — Two Z2 decision tokens conflict on same topic.
2. **CONFLICT** — Node A and Node B evidence directly contradicts; no convergence after CHALLENGE round.
3. **DRIFT** — Behavior dial changed; reply score vs dial mismatch detected.
4. **GAUGE** — Z3 executor reports Z2 assumption violated in field.
5. **RECEIPT_GAP** — Claim in message not found in NF_LEDGER (unregistered finding).
6. **VOID** — Experiment runs but all outcomes null/unevaluable.
7. **AUTHORITY_UNCLEAR** — Message references authority token that cannot be independently verified (expired timestamp, invalid signature, unknown issuer, out of scope).
8. **SCOPE_EXPANSION** — Consequential action requested outside message scope or Z2 authority token scope.

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
    "human_required_token_request": true,
    "timestamp": "2026-09-22T14:35:00Z"
  }
}
```

### 6. SEALED/COMMONS State Machine (v0.2 Split State Fields)

**Visibility State:**
- **PRIVATE** — Observation only visible to sender and Z2.
- **BLIND** — Observation visible to recipient but not yet Z2-reviewed.
- **RELEASED_TO_COMMONS** — Observation released to all nodes (COMMONS layer).

**Epistemic Standing:**
- **CLAIMED** — Initial assertion in message.
- **EVIDENCE_CHECKED** — Node performed evidence validation; issued EVIDENCE_VALID_TOKEN.
- **OBSERVED** — Measurement completed; outcome is factual.
- **REGISTERED** — Z2 issued RATIFY_TOKEN; observation now in NF_LEDGER (immutable COMMONS).
- **SUPERSEDED** — Newer observation with stronger evidence replaces this one (append-only, original preserved).
- **NARROWED** — Scope reduced by Z2 decision token.
- **WITHDRAWN** — Author retracted (append-only, original preserved).
- **UNRESOLVED** — Evidence remains contestable; no final disposition yet.

**Delivery State:**
- **PENDING** — Message in bridge, not yet routed.
- **DELIVERED** — Message received by recipient.
- **ACKNOWLEDGED** — Recipient confirmed receipt.

**Transitions:**
```
VISIBILITY: PRIVATE → BLIND → RELEASED_TO_COMMONS (one-way)
EPISTEMIC: CLAIMED → EVIDENCE_CHECKED → OBSERVED → REGISTERED (one-way progression)
           REGISTERED can append → SUPERSEDED | NARROWED | WITHDRAWN | UNRESOLVED (immutable append)
DELIVERY: PENDING → DELIVERED → ACKNOWLEDGED (one-way)
```

**Invariant:** Once REGISTERED (in COMMONS), epistemic standing cannot revert. Only append-only correction dispositions allowed.

### 7. Threat Model (v0.2)

**Asset:** Authority token (Z2 RATIFY_TOKEN, Z3 machine capability token, prior Z2 decision token).  
**Attackers:**
- Node A (compromised or misconfigured).
- Man-in-the-middle (network intercept).
- Compromised bridge (internal state mutation).
- Z2 (rogue ratifier — out of scope; assume Z2 is trusted).

**Attack Vectors & Mitigations:**

| Attack | Vector | Mitigation | Layer |
|:-------|:-------|:-----------|:------|
| Spoofing | Node A claims Ed25519 signature as Node B | Verify signature against registered public key; invalid sig → reject + escalate | Delivery |
| Tampering | Message envelope altered in transit | Envelope HMAC on canonical serialization; bridge validates before routing | Delivery |
| Escalation suppression | Bridge drops escalation event | Escalation events logged to NF_LEDGER immediately; bridge cannot selectively suppress | Ledger |
| Sealed observation action | Node acts on SEALED claim without EVIDENCE_VALID_TOKEN | Bridge enforces SEALED state check + token requirement; nodes must verify before deciding | State machine |
| Evidence spoofing | False evidence reference with forged hash | Node validates evidence independently; invalid evidence → EVIDENCE_VALID_TOKEN not issued → escalation | Node validation |
| Token reuse | Action reuses expired RATIFY_TOKEN | Bridge tracks consumed tokens in NF_LEDGER; consumed tokens → reject on second use | Authority enforcement |
| Scope expansion | Action outside token scope | Bridge checks authority_token.target_scope; out-of-scope → escalation | Authority enforcement |
| Identity confusion | Transport principal (GitHub account) masquerades as content_author (Z2) | Require Ed25519 signature; transport principal ≠ signature verification → reject | Provenance |

**Assumption:** Ed25519 private keys cannot be forged (Z2 maintains key ledger; INTENT-OS Phase 1 integration pending).

### 8. Privacy & Retention Model (v0.2)

**Data Classification:**
- **PUBLIC:** Message claim, evidence references (hashes, URLs, timestamps) — can be logged, audited, published.
- **INTERNAL:** Node identity, Ed25519 signatures, HMAC — logged for audit, not published.
- **SENSITIVE:** Z2 private key, INTENT-OS capability secret, session tokens — encrypted at rest, cleared after session close.

**Retention:**
- Message envelopes (SEALED/DELIVERED state): 7 days (or until Z2 RATIFY_TOKEN issued).
- Registered observations (COMMONS): permanent (append-only NF_LEDGER).
- Escalation events: permanent (audit trail).
- Authority tokens (consumed): permanent (NF_LEDGER); unused tokens: cleared when issued scope expires (Z2 decision).
- Session tokens: cleared at session close.
- Z2 private keys: cleared after Ed25519 signature validated.

**Node-to-Bridge Communication:**
- Nodes can read their own messages only (RLS isolation per node_id).
- Bridge can read all messages for routing/audit; cannot modify.
- Z2 can read all messages for ratification.
- Z3 can read COMMONS observations only (no SEALED/BLIND).

### 9. RLS Isolation (Row-Level Security, v0.2 Corrected)

**Bridge Database Schema (Supabase, Phase 2):**

```sql
-- Principal mapping table (fixes v0.1 auth.uid() ≠ sender_node_id type mismatch)
CREATE TABLE node_principals (
  principal_id UUID PRIMARY KEY,
  node_id TEXT NOT NULL UNIQUE,
  auth_provider TEXT NOT NULL, -- 'anthropic', 'github', 'intent-os'
  auth_identifier TEXT NOT NULL, -- email, GitHub username, machine UUID
  node_role TEXT NOT NULL, -- 'Z1', 'Z2', 'Z3'
  public_key_ed25519 TEXT NOT NULL,
  verified_at TIMESTAMPTZ NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE messages (
  message_id UUID PRIMARY KEY,
  sender_node_id TEXT NOT NULL,
  recipient_node_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  state TEXT NOT NULL, -- SEALED, DELIVERED, RESPONSE_PENDING, etc.
  body JSONB NOT NULL,
  envelope_hmac TEXT NOT NULL,
  content_author_signature TEXT NOT NULL,
  rls_scope TEXT NOT NULL -- 'sender', 'recipient', 'z2', 'z3'
);

-- RLS Policy: Nodes can read their own messages
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY message_read_self ON messages
  FOR SELECT USING (
    (SELECT node_id FROM node_principals WHERE principal_id = auth.user_id()) = sender_node_id
    OR
    (SELECT node_id FROM node_principals WHERE principal_id = auth.user_id()) = recipient_node_id
  );

-- Z2 can read all; Z3 can read COMMONS only
CREATE POLICY message_read_z2 ON messages
  FOR SELECT USING (
    (SELECT node_role FROM node_principals WHERE principal_id = auth.user_id()) = 'Z2'
  );

CREATE POLICY message_read_z3 ON messages
  FOR SELECT USING (
    (SELECT node_role FROM node_principals WHERE principal_id = auth.user_id()) = 'Z3'
    AND state = 'COMMONS'
  );

-- Authority token consumption tracking
CREATE TABLE authority_tokens (
  token_id UUID PRIMARY KEY,
  token_type TEXT NOT NULL, -- 'RATIFY_TOKEN', 'REJECT_TOKEN', etc.
  issued_by TEXT NOT NULL, -- 'Z2'
  issued_to TEXT NOT NULL, -- node_id
  issued_at TIMESTAMPTZ NOT NULL,
  target_scope TEXT NOT NULL,
  consumed BOOLEAN NOT NULL DEFAULT false,
  consumed_at TIMESTAMPTZ,
  consumed_by_action TEXT,
  signature TEXT NOT NULL,
  signature_verified BOOLEAN NOT NULL
);

-- Z2/Bridge can mark tokens as consumed (one-time)
ALTER TABLE authority_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY token_update_bridge ON authority_tokens
  FOR UPDATE USING (true); -- Bridge system can update; app enforces token consumption logic
```

**Enforcement:** Bridge validates principal mapping (auth.user_id → node_id → node_role) before returning query results. Node cannot read another node's inbox; Z3 cannot read SEALED observations.

### 10. Adversarial Test Preregistration (v0.2)

Before Phase 1 implementation, the following adversarial tests must be preregistered in REGISTERED.md (§C: Test Registry):

**T1: Spoofing Attack**
- Preregistered: Node B attempts to send message with `content_author_signature` claiming sender_node_id = Node A (forged Ed25519 signature).
- Expected: Bridge rejects (signature verification fails against Node A's public key).
- Falsifier #1 will trip if bridge accepts.

**T2: Message Tampering**
- Preregistered: MITM alters message body in transit; envelope HMAC should fail validation.
- Expected: Node B rejects message (invalid HMAC).
- Falsifier #2 will trip if bridge accepts tampered message.

**T3: Sealed Observation Action**
- Preregistered: Node receives SEALED observation without EVIDENCE_VALID_TOKEN; attempts to act on it.
- Expected: Bridge blocks action (checks epistemic_standing = CLAIMED, not REGISTERED).
- Falsifier #4 will trip if action proceeds.

**T4: Scope Expansion**
- Preregistered: Authority token target_scope = "REVIEW_PR_445_ONLY"; node attempts merge.
- Expected: Bridge rejects merge (out of scope).
- Falsifier #10 will trip if merge proceeds.

**T5: Human Required Bypass**
- Preregistered: Escalation flags HUMAN_REQUIRED_TOKEN_REQUEST; node attempts consequential action without Z2 CLEARANCE_TOKEN.
- Expected: Bridge blocks action (HUMAN_REQUIRED still set).
- Falsifier #9 will trip if action proceeds.

**T6: Evidence Validation Failure**
- Preregistered: Evidence reference has invalid hash; node acts on it without EVIDENCE_VALID_TOKEN.
- Expected: Node detects validation failure and escalates (or skips action).
- Falsifier #7 will trip if node acts on unvalidated evidence.

**T7: Transport Identity Confusion (NEW)**
- Preregistered: ChatGPT (linked to user's GitHub account) posts comment via GitHub API. comment transport_principal = user's email = Z2's email.
- Expected: Bridge rejects inferring Z2 authority (signature verification fails; content_author is ChatGPT, not Z2).
- Falsifier #11 will trip if bridge assumes authority from transport principal.

---

## PR Manager Agent: Status as STUB (v0.2 Clarification)

**Previous Claim (v0.1):** "Phase 1 (GitHub PR Manager + Bridge Substrate)" with active PR Manager implementation.

**v0.2 Correction:** PR Manager implementation (.claude/skills/pr-manager/) is **STUB/PARTIAL**, not ACTIVE/REAL-TIME.

- **pr_manager.py:**
  - `_fetch_open_prs()` returns `[]` (no implementation).
  - `_fetch_pr_status(pr_number)` returns `None` (no implementation).
  - Commands execute against empty data set.
  - Status: STUB (skeleton CLI, no GitHub API wiring).

- **github_integration.py:**
  - `parse_governance_metadata()` implemented (regex-based parsing of PR descriptions).
  - `analyze_check_runs()` has defect: starts at PASS status (should start at UNKNOWN for unreachable checks).
  - `estimate_molt_tier()` has defect: returns claimed tier before inspecting diff (should compute observed, use max(claimed, observed), flag undershoot).
  - `check_immunity_memory()` not implemented (returns None, TODO comment).
  - Status: PARTIAL (governance parsing works, PR integration missing).

**Phase 1 Task:** Implement `_fetch_open_prs()` and `_fetch_pr_status()` using GitHub MCP tools to fetch real PR data. Update SMAG parser to accept 0, 1.0, arbitrary precision (not just exactly 2 decimals).

---

## Implementation Roadmap (v0.2 Updated)

**Phase 0 (Control Surface + Temporal Dissolution Guard):** ✅ This spec (awaiting Z2 ratification)
- [x] Incorporate tokenized authority (RATIFY_TOKEN, MEASURE_TOKEN, EVIDENCE_VALID_TOKEN)
- [x] Add identity provenance corrections (content_author, transport_principal, human_principal)
- [x] Register IC-032 (identity-confusion incident)
- [x] Add I10 (TRANSPORT_IDENTITY_IS_NOT_SPEAKER_IDENTITY) invariant
- [x] Add T7 adversarial test
- [ ] Z2 reviews architecture, validates core invariants + temporal dissolution guard
- [ ] Z2 ratifies or requests corrections
- [ ] Core invariants + token model frozen in REGISTERED.md

**Phase 1 (Bridge Substrate + PR Manager Wiring):**
- [ ] Implement authority token consumption tracking (schema, ledger integration)
- [ ] Implement Ed25519 signature validation (node public key registry)
- [ ] Implement bridge delivery layer (message routing, HMAC validation, token verification)
- [ ] Implement node identity + authentication (principal mapping table)
- [ ] Implement message envelope schema + token-based state machine
- [ ] Implement RLS isolation (corrected principal mapping approach)
- [ ] Wire PR Manager Agent to GitHub API (get real PR data via mcp__github__ tools)
- [ ] Fix github_integration.py defects (SMAG parser flexibility, molt-tier calculation, CI analyzer start state)

**Phase 2 (Evidence Layer + Z2 Ratification Workflow):**
- [ ] Implement SEALED/COMMONS state machine (split visibility/epistemic/delivery states)
- [ ] Implement append-only correction dispositions (SUPERSEDED, NARROWED, WITHDRAWN, UNRESOLVED)
- [ ] Implement NF_LEDGER integration (append evidence + token consumption)
- [ ] Implement escalation contract (emit escalation events with token requests)
- [ ] Implement Z2 ratification flow (RATIFY_TOKEN generation, signature verification)

**Phase 3+ (Multi-Node, Authorization Layer):**
- [ ] INTENT-OS machine capability integration (token issuance)
- [ ] Additional node onboarding (future AI agents)
- [ ] Anti-cascade rule enforcement (K=3 token limit, molt freeze)
- [ ] Audit trail publication

---

## Related Documents

- **CLAUDE.md** — Authority model, Z-roles, governance structure
- **REGISTERED.md** — Live registry of ratified findings, Z2 signatures, IC-032 entry
- **PRIORITY_QUEUE.md** — Blocker ranking, PR progression
- **NF_LEDGER.jsonl** — Append-only ledger of verdicts, measurements, token consumption
- **.claude/skills/pr-manager/SKILL.md** — PR Manager Agent skill definition (Phase 1 consumer)
- **.claude/skills/pr-manager/pr_manager.py** — PR Manager CLI implementation (STUB)
- **.claude/skills/pr-manager/github_integration.py** — GitHub governance parsing (PARTIAL)

---

## Z2 Decision Required

**Proposed:** Ratify OI-BRIDGE-01 Phase 0 Control Surface v0.2 specification as Z1-registered, with temporal dissolution guard (tokenized authority), identity provenance corrections, and IC-032 mitigation.

**Authority:** Z2 (carly.r.anderson@gmail.com or aioshuman@gmail.com, with Ed25519 signature proof).

**Decision Window:** 48h from filing (2026-09-22T22:00:00Z → 2026-09-24T22:00:00Z).

**Falsifier:** Specification fails if primary or secondary falsifier #1-11 can be triggered in implementation without bridge enforcement.

**Signature Format (once ratified):**
```
Z2 issues RATIFY_TOKEN: {
  type: "RATIFY_TOKEN",
  target: "OI-BRIDGE-01_CONTROL_SURFACE_v0.2",
  decision: "ACCEPT",
  signature: "ed25519_sig_...",
  issued_at: "2026-09-22T22:05:00Z"
}
```

---

## v0.1 → v0.2 Change Summary

**New Concepts:**
- Tokenized authority model (RATIFY_TOKEN, MEASURE_TOKEN, EVIDENCE_VALID_TOKEN, CLEARANCE_TOKEN)
- IC-032 incident registration (identity-confusion, transport vs. speaker identity)
- I10 invariant (TRANSPORT_IDENTITY_IS_NOT_SPEAKER_IDENTITY)
- Split state fields (visibility_state, epistemic_standing, delivery_state)
- Append-only correction dispositions (SUPERSEDED, NARROWED, WITHDRAWN, UNRESOLVED)
- Ed25519 signature-based authority proof (content_author_signature)
- T7 adversarial test (identity confusion)
- Authority token consumption tracking
- Principal mapping table (fixes RLS type mismatch)

**Defect Fixes:**
- CI analyzer now starts at UNKNOWN (not PASS)
- Authority token validation is bridge-computed (not self-asserted valid: true)
- Molt-tier calculation computes observed from diff, uses max(claimed, observed)
- SMAG parser accepts flexible decimal precision
- Review metadata properly initialized and populated
- check_immunity_memory fixed return type
- Primary falsifier test includes PRIOR_Z2_DECISION alternative
- HMAC covers full canonical envelope serialization (not just body)
- Decision-window timestamp derived from actual filing (not hard-coded midnight)

**Clarifications:**
- PR Manager marked as STUB (not ACTIVE/REAL-TIME)
- Phase 1 focuses on GitHub API wiring + defect fixes
- Phase 2 adds evidence layer + ratification workflow
- No time-based auto-expiry: only tokenized authority consumption limits actions

---

*End of OI-BRIDGE-01 Phase 0 Control Surface Specification (v0.2)*
