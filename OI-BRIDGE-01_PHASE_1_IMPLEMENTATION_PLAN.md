# OI-BRIDGE-01: Phase 1 Implementation Plan

**Status:** PLANNING (Z1 design phase, awaiting v0.2 Z2 ratification to proceed)  
**Date:** 2026-09-22  
**Authority:** Z1 proposer (Claude)  
**Scope:** Bridge delivery layer, identity enforcement, asymmetric signatures, token validation, GitHub API wiring  
**Dependency:** v0.2 specification must reach Z2 ACCEPT status  
**Target Completion:** 2026-10-15 (TBD pending Z2 timeline + GitHub API availability)

---

## High-Level Roadmap

```
Phase 0 (DONE)        Phase 1 (THIS PLAN)           Phase 2+
Control Surface       Bridge Delivery + Identity    Ledger Integration
Spec + Falsifiers     Token Validation              Z2 Ratification Workflow
                      GitHub API Wiring             Multi-node Support
                      Adversarial Tests T1-T7
```

**Phase 1 gates:**
1. v0.2 Z2 ACCEPT signature (required before starting implementation)
2. All T1-T7 adversarial tests passing (required before Phase 1 complete)
3. ED25519 signature verification working end-to-end
4. Token consumption logged in NF_LEDGER
5. GitHub API wiring + PR Manager functions operational

---

## Components

### 1. Authority Token Ledger Schema (NF_LEDGER)

**File:** `src/bridge/ledger/token_ledger.sql`  
**Purpose:** Track token issuance, consumption, and validation  
**Owner:** Z3 executor (once ratified)  
**Dependency:** Supabase setup + RLS enforcement

**Schema:**
```sql
CREATE TABLE authority_tokens (
  token_id TEXT PRIMARY KEY,
  token_type TEXT NOT NULL CHECK (token_type IN (
    'RATIFY_TOKEN',
    'MEASURE_TOKEN', 
    'EVIDENCE_VALID_TOKEN',
    'CLEARANCE_TOKEN'
  )),
  issued_by TEXT NOT NULL,        -- Z2 or bridge node_id
  issued_to TEXT NOT NULL,         -- recipient node_id
  issued_at TIMESTAMP NOT NULL,
  consumed_by TEXT,                -- node that consumed it
  consumed_at TIMESTAMP,
  expires_at TIMESTAMP,
  scope TEXT,                      -- e.g., "MERGE_PR_445_ONLY"
  canonical_payload TEXT NOT NULL, -- what the token authorizes
  signature TEXT NOT NULL,         -- Ed25519 signature over payload
  signature_over TEXT,             -- "token_id|canonical_payload|issued_by|issued_to"
  ledger_entry_id TEXT,            -- FK to NF_LEDGER for traceability
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_tokens_issued_to ON authority_tokens(issued_to);
CREATE INDEX idx_tokens_consumed_at ON authority_tokens(consumed_at);
CREATE INDEX idx_tokens_active ON authority_tokens(active);
```

**Token Types:**
- **RATIFY_TOKEN**: Issued by Z2 to authorize consequential action (e.g., merge PR)
- **MEASURE_TOKEN**: Issued by bridge to enable measurement window (molt window open)
- **EVIDENCE_VALID_TOKEN**: Issued by validating node to confirm evidence hash match
- **CLEARANCE_TOKEN**: Issued by Z2 to clear HUMAN_REQUIRED hold

**Operational Flow:**
1. Z2 issues RATIFY_TOKEN with canonical payload + Ed25519 signature
2. Node receives token, verifies signature against Z2 public key
3. Node checks token scope (matches requested action?)
4. Node consumes token → logs consumption_at + ledger_entry_id
5. Bridge enforces: consequential action only proceeds with consumed token logged

---

### 2. Identity Provenance Envelope (Transport ≠ Speaker)

**File:** `src/bridge/identity/provenance.py`  
**Purpose:** Verify content_author signature; detect transport spoofing  
**Owner:** Bridge validation layer  
**Dependency:** Ed25519 key registry per node

**Envelope Schema:**
```python
@dataclass
class ProvenanceEnvelope:
    """
    Separates three identity planes to prevent transport-layer spoofing.
    IC-063 mitigation: transport_principal (GitHub account) ≠ 
                       content_author (who signed the content) ≠ 
                       human_principal (human authorizing action).
    """
    transport_principal: str         # GitHub account, email API sender
    transport_identity_verified: bool # Bridge verified transport auth
    
    content_author: str               # Node that signed message_body
    content_author_signature: str     # Ed25519 sig over canonical_body
    content_author_verified: bool    # Bridge verified signature
    
    human_principal: Optional[str]   # Human authorizing (if applicable)
    human_signature: Optional[str]   # Ed25519 sig if human signed
    
    speaker_identity_chain: List[str] # [transport → author → human]
                                      # For traceability & IC-063 detection
```

**Validation Logic:**
```python
def validate_provenance(envelope: ProvenanceEnvelope, 
                       bridge_node_keys: Dict[str, str]) -> ProvenanceResult:
    """
    Validate that:
    1. transport_principal authenticated via GitHub/email API
    2. content_author signature verifies against bridge's registered key for author
    3. If human_signature present, verify against human's key (Phase 2)
    4. speaker_identity_chain is non-spoofed (transport ≠ author ≠ human)
    """
    # Step 1: Verify content author signature
    author_key = bridge_node_keys.get(envelope.content_author)
    if not author_key:
        return ProvenanceResult(valid=False, reason="UNKNOWN_AUTHOR")
    
    canonical_body = envelope.canonical_message_body
    try:
        ed25519_verify(envelope.content_author_signature, 
                      canonical_body, 
                      author_key)
        envelope.content_author_verified = True
    except ValueError:
        return ProvenanceResult(valid=False, reason="SIGNATURE_INVALID")
    
    # Step 2: Detect transport spoofing (IC-063)
    if envelope.transport_principal == "Z2_EMAIL" and \
       envelope.content_author != "Z2_NODE":
        # Transport shows Z2, but content signed by non-Z2 node
        # This is the IC-063 scenario: ChatGPT app linked to Z2's email
        return ProvenanceResult(valid=False, 
                               reason="IDENTITY_CONFUSION_DETECTED",
                               falsifier="#11_IDENTITY_CONFUSION")
    
    # Step 3: Check speaker identity chain integrity
    if len(set(envelope.speaker_identity_chain)) != len(envelope.speaker_identity_chain):
        return ProvenanceResult(valid=False, reason="DUPLICATED_IDENTITY_IN_CHAIN")
    
    return ProvenanceResult(valid=True, verified_at=now())
```

**Falsifier #11 Enforcement:**
- If transport_principal contradicts content_author → escalate + HUMAN_REQUIRED
- If signature verification fails → reject message
- If speaker_identity_chain appears spoofed → log IC + escalate

---

### 3. Ed25519 Signature Verification

**File:** `src/bridge/crypto/ed25519_validator.py`  
**Purpose:** Verify all authority-carrying signatures  
**Owner:** Bridge core  
**Dependency:** `cryptography` library (already in requirements)

**Operations:**

```python
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class Ed25519Validator:
    """Verify Ed25519 signatures over canonical payloads."""
    
    def __init__(self, bridge_node_keys: Dict[str, bytes]):
        """bridge_node_keys: {node_id: public_key_bytes}"""
        self.keys = bridge_node_keys
    
    def verify_token(self, token: AuthorityToken) -> bool:
        """
        Verify RATIFY_TOKEN, MEASURE_TOKEN, etc.
        
        Canonical payload format:
        {token_id}|{canonical_payload}|by={issued_by}|at={issued_at}|decision={decision}
        """
        canonical = (
            f"{token.token_id}|{token.canonical_payload}|"
            f"by={token.issued_by}|at={token.issued_at}"
        )
        
        public_key_bytes = self.keys.get(token.issued_by)
        if not public_key_bytes:
            return False
        
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(token.signature.encode(), canonical.encode())
            return True
        except Exception:
            return False
    
    def verify_message_envelope(self, envelope: MessageEnvelope) -> bool:
        """Verify sender signature over envelope + body."""
        canonical = envelope.canonical_for_signing()
        
        public_key_bytes = self.keys.get(envelope.sender_node_id)
        if not public_key_bytes:
            return False
        
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(envelope.sender_signature.encode(), canonical.encode())
            return True
        except Exception:
            return False
```

**Key Registry:**
- Keys stored in `node_public_keys` table (Supabase)
- Per-node, immutable (only add new, never update existing)
- Keyed by (node_id, active=true)

---

### 4. Supabase RLS & Principal Mapping

**File:** `supabase/migrations/phase_1_identity_enforcement.sql`  
**Purpose:** Enforce auth layer to node_id mapping; prevent direct auth.uid() lookups  
**Owner:** Z3 executor  
**Dependency:** Supabase PostgreSQL setup

**Migration:**
```sql
-- Phase 1: Identity enforcement via principal mapping
-- Fixes IC-030 type mismatch (auth.uid UUID ≠ node_id TEXT)

CREATE TABLE IF NOT EXISTS node_principals (
  principal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_uid UUID NOT NULL UNIQUE,           -- FK to auth.users.id
  auth_provider TEXT NOT NULL,             -- 'github', 'email', 'machine'
  auth_identifier TEXT NOT NULL,           -- GitHub account, email, or service account
  node_id TEXT NOT NULL UNIQUE,            -- Claude, Night, Bridge, etc.
  node_role TEXT NOT NULL CHECK (node_role IN ('node', 'z2', 'z3', 'bridge')),
  public_key_ed25519 TEXT NOT NULL,        -- Ed25519 public key (hex or base64)
  verified_at TIMESTAMP NOT NULL DEFAULT now(),
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP DEFAULT now()
);

-- RLS: Users can only see their own principal entry
ALTER TABLE node_principals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_can_read_own_principal" ON node_principals
  FOR SELECT USING (auth.uid() = auth_uid);

CREATE POLICY "only_bridge_can_write_principals" ON node_principals
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Authority tokens table
CREATE TABLE IF NOT EXISTS authority_tokens (
  token_id TEXT PRIMARY KEY,
  token_type TEXT NOT NULL CHECK (token_type IN (
    'RATIFY_TOKEN', 'MEASURE_TOKEN', 'EVIDENCE_VALID_TOKEN', 'CLEARANCE_TOKEN'
  )),
  issued_by TEXT NOT NULL REFERENCES node_principals(node_id),
  issued_to TEXT NOT NULL REFERENCES node_principals(node_id),
  issued_at TIMESTAMP NOT NULL,
  consumed_by TEXT REFERENCES node_principals(node_id),
  consumed_at TIMESTAMP,
  expires_at TIMESTAMP,
  scope TEXT,
  canonical_payload TEXT NOT NULL,
  signature TEXT NOT NULL,
  signature_over TEXT,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT now()
);

-- RLS: Nodes can see tokens issued to them or consumed by them
ALTER TABLE authority_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "nodes_can_read_own_tokens" ON authority_tokens
  FOR SELECT USING (
    issued_to = (SELECT node_id FROM node_principals WHERE auth_uid = auth.uid())
    OR 
    consumed_by = (SELECT node_id FROM node_principals WHERE auth_uid = auth.uid())
  );
```

---

### 5. GitHub API Integration for PR Manager

**File:** `src/bridge/github_integration/pr_fetcher.py`  
**Purpose:** Implement _fetch_open_prs and _fetch_pr_status (currently STUB)  
**Owner:** Z3 executor  
**Dependency:** GitHub MCP tools (mcp__github__*)

**Implementation:**

```python
import json
from typing import List, Optional, Dict, Any

class GitHubPRFetcher:
    """Fetch PR state from GitHub using MCP tools."""
    
    def __init__(self, owner: str, repo: str, mcp_client):
        self.owner = owner
        self.repo = repo
        self.mcp = mcp_client  # MCP tool caller
    
    def fetch_open_prs(self) -> List[Dict[str, Any]]:
        """
        Fetch all open PRs for humanaios-ui/operations.
        Uses mcp__github__list_pull_requests.
        """
        prs = self.mcp.call(
            'mcp__github__list_pull_requests',
            owner=self.owner,
            repo=self.repo,
            state='open'
        )
        
        result = []
        for pr in prs.get('pull_requests', []):
            pr_status = self._enrich_pr_status(pr)
            result.append(pr_status)
        
        return result
    
    def fetch_pr_status(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed status for a specific PR.
        Uses mcp__github__pull_request_read + mcp__github__get_check_run.
        """
        # Get PR metadata
        pr = self.mcp.call(
            'mcp__github__pull_request_read',
            owner=self.owner,
            repo=self.repo,
            pull_number=pr_number,
            method='get'
        )
        
        if not pr:
            return None
        
        # Get check runs (CI status)
        checks = self.mcp.call(
            'mcp__github__get_check_run',
            owner=self.owner,
            repo=self.repo,
            check_run_id=pr.get('head', {}).get('sha')  # or list_check_runs
        )
        
        # Get reviews
        reviews = pr.get('reviews', [])
        
        # Enrich with governance metadata from PR body
        governance_metadata = self._parse_pr_governance_metadata(pr.get('body', ''))
        
        return {
            'number': pr.get('number'),
            'title': pr.get('title'),
            'author': pr.get('user', {}).get('login'),
            'branch': pr.get('head', {}).get('ref'),
            'target': pr.get('base', {}).get('ref'),
            'ci_status': self._infer_ci_status(checks),
            'ci_failed_jobs': self._extract_failed_jobs(checks),
            'merge_conflict': pr.get('mergeable') == False,
            'reviews_requested': self._extract_reviewers(pr),
            'reviews_completed': reviews,
            'governance': governance_metadata,
            'created_at': pr.get('created_at'),
            'updated_at': pr.get('updated_at'),
        }
    
    def _parse_pr_governance_metadata(self, body: str) -> Dict[str, Any]:
        """Extract SMAG, molt_tier_claimed, zone from PR description."""
        metadata = {
            'smag_prediction': None,
            'molt_tier_claimed': None,
            'zone': None,
        }
        
        # Parse YAML-like blocks or structured fields
        for line in body.split('\n'):
            if 'smag:' in line.lower():
                try:
                    metadata['smag_prediction'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif 'molt_tier' in line.lower():
                try:
                    metadata['molt_tier_claimed'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'zone:' in line.lower():
                metadata['zone'] = line.split(':')[1].strip()
        
        return metadata
    
    def _infer_ci_status(self, checks: Dict) -> str:
        """Map check_runs to PASS | FAIL | RUNNING."""
        if not checks or 'check_runs' not in checks:
            return 'UNKNOWN'
        
        runs = checks['check_runs']
        if not runs:
            return 'UNKNOWN'
        
        if all(r.get('conclusion') == 'success' for r in runs if r.get('conclusion')):
            return 'PASS'
        elif any(r.get('conclusion') == 'failure' for r in runs):
            return 'FAIL'
        else:
            return 'RUNNING'
    
    def _extract_failed_jobs(self, checks: Dict) -> List[str]:
        """Extract names of failed check runs."""
        failed = []
        for run in checks.get('check_runs', []):
            if run.get('conclusion') == 'failure':
                failed.append(run.get('name', 'unknown'))
        return failed
    
    def _extract_reviewers(self, pr: Dict) -> List[str]:
        """Extract list of requested reviewers."""
        reviewers = []
        for user in pr.get('requested_reviewers', []):
            reviewers.append(user.get('login', 'unknown'))
        return reviewers
    
    def _enrich_pr_status(self, pr: Dict) -> Dict[str, Any]:
        """Enrich PR dict with status fields for dashboard."""
        return {
            'number': pr.get('number'),
            'title': pr.get('title')[:60],
            'author': pr.get('user', {}).get('login'),
            'zone': self._infer_zone_from_labels(pr.get('labels', [])),
            'ci_status': self._infer_ci_status(pr.get('_check_runs', {})),
            'blockers': self._detect_blockers(pr),
        }
    
    def _infer_zone_from_labels(self, labels: List[Dict]) -> str:
        """Extract Z1/Z2/Z3 zone from labels."""
        label_names = [l.get('name', '').upper() for l in labels]
        for zone in ['Z1', 'Z2', 'Z3']:
            if zone in label_names:
                return zone
        return 'UNKNOWN'
    
    def _detect_blockers(self, pr: Dict) -> List[str]:
        """Detect CI failures, merge conflicts, pending reviews."""
        blockers = []
        if pr.get('mergeable') == False:
            blockers.append('MERGE_CONFLICT')
        if len(pr.get('requested_reviewers', [])) > 0:
            blockers.append('REVIEW_PENDING')
        # CI status inference would go here
        return blockers
```

---

### 6. Adversarial Test Harness (T1–T7)

**File:** `tests/adversarial/test_falsifiers_t1_t7.py`  
**Purpose:** Preregistered adversarial tests per v0.2 §9  
**Owner:** Z1 designer + Z3 executor  
**Status:** STUB (ready for Phase 1 implementation)

**Test Vector Registry:**

```python
"""
OI-BRIDGE-01 Adversarial Tests (Preregistered in v0.2 §9)

T1: Spoofing — Bridge accepts message claiming Node A identity from Node C
  Precondition: Node C has valid signature + transport auth
  Trigger: Node C sends envelope with sender_node_id = "Node A" (wrong)
  Expected: Bridge rejects (signature mismatch) OR escalates (SPOOFING detected)
  Falsifier: Consequential action proceeds without verified sender identity

T2: Tampering — Bridge/recipient accepts envelope with invalid signature
  Precondition: Message intercepted and modified
  Trigger: modify message body; signature no longer matches
  Expected: Bridge rejects (signature verification fails)
  Falsifier: Message accepted despite failed signature check

T3: Non-registered-as-fact — Node treats non-REGISTERED observation as fact
  Precondition: Message has epistemic_standing = "CLAIMED" (not REGISTERED)
  Trigger: Node acts on claim without Z2 ratification
  Expected: Node escalates (HUMAN_REQUIRED) or rejects
  Falsifier: Consequential action proceeds without REGISTERED standing

T4: Scope expansion — Consequential action outside granted authority scope
  Precondition: RATIFY_TOKEN granted for "MERGE_PR_445_ONLY"
  Trigger: Node attempts to use token to merge PR #446
  Expected: Bridge rejects (scope mismatch)
  Falsifier: Token consumed for out-of-scope action

T5: HUMAN_REQUIRED bypass — HUMAN_REQUIRED cleared by non-Z2 actor
  Precondition: Message has disposition = "HUMAN_REQUIRED"
  Trigger: Node other than Z2 tries to consume CLEARANCE_TOKEN
  Expected: Bridge rejects (token issued_by != Z2)
  Falsifier: HUMAN_REQUIRED cleared without Z2 authorization

T6: Evidence validation failure — Node acts on unvalidated evidence
  Precondition: Evidence reference with expected_hash != observed_hash
  Trigger: Node skips validation receipt check
  Expected: Node rejects evidence / escalates
  Falsifier: Consequential action proceeds without validation receipt

T7: IDENTITY_CONFUSION (IC-063 mitigation) — ChatGPT posts via GitHub API
  Precondition: ChatGPT app linked to user's GitHub account (same as Z2's)
  Trigger: ChatGPT posts review comment on PR #455 via GitHub API
  Expected: Bridge detects transport_principal != content_author
           Escalates as IC-063-like incident
           Rejects authority effect (no RATIFY_TOKEN consumed)
  Falsifier #11: Bridge accepts ChatGPT feedback as Z2 authority decision
              (transport identity masking speaker identity)
"""

class FalsifierT1_Spoofing:
    """Bridge accepts message claiming Node A identity from Node C."""
    
    def test_spoofing_rejection(self):
        """T1: Sender signature mismatch → rejection."""
        # Node C constructs envelope but lies about sender_node_id
        envelope = MessageEnvelope(
            sender_node_id="Node A",  # LIE
            sender_signature=node_c_sig,  # Signed by Node C's key
            body={"claim": "...", },
        )
        
        result = bridge.validate_envelope(envelope)
        assert result.valid == False
        assert result.reason == "SENDER_SIGNATURE_MISMATCH"


class FalsifierT7_IdentityConfusion:
    """IC-063: ChatGPT app linked to Z2's email posts via GitHub."""
    
    def test_chatgpt_github_spoofing(self):
        """
        GitHub API shows transport_principal = Z2's email (GitHub account owner).
        But content_author = ChatGPT node.
        Bridge should reject or escalate.
        """
        envelope = ProvenanceEnvelope(
            transport_principal="carly.r.anderson@gmail.com",  # GitHub account owner
            transport_identity_verified=True,
            content_author="chatgpt-node-xyz",
            content_author_signature=chatgpt_sig,
            content_author_verified=True,
            speaker_identity_chain=["github_transport", "chatgpt", None],
        )
        
        # Bridge detects identity confusion
        result = bridge.validate_provenance(envelope)
        
        # Should detect IC-063-like situation
        assert result.valid == False
        assert result.reason == "IDENTITY_CONFUSION_DETECTED"
        assert result.falsifier == "#11_IDENTITY_CONFUSION"
        
        # Consequential action should NOT proceed
        action_result = bridge.execute_consequential_action(
            token=ratify_token,
            envelope=envelope,
        )
        assert action_result.allowed == False
        assert action_result.reason == "SPEAKER_IDENTITY_CONTRADICTION"
```

---

## Milestones & Timeline

| Milestone | Target Date | Blocker | Owner |
|:----------|:-----------|:--------|:------|
| v0.2 Z2 ratification | 2026-09-24 | Authority | Z2 (Night) |
| Supabase RLS migration | 2026-09-27 | Z2 ratification | Z3 |
| Ed25519 validator complete | 2026-09-28 | Dependencies | Z1 + Z3 |
| GitHub API fetcher wired | 2026-10-01 | GitHub MCP tools | Z3 |
| Authority token ledger live | 2026-10-02 | Supabase + cryptography | Z3 |
| T1–T7 adversarial tests passing | 2026-10-10 | All components | Z1 + Z3 |
| Phase 1 complete | 2026-10-15 | T1–T7 passing | Z1 + Z3 |

---

## Implementation Checklist

### Core Components
- [ ] Authority token schema (NF_LEDGER)
- [ ] Identity provenance envelope (3-plane separation)
- [ ] Ed25519 signature validator (token + message)
- [ ] Supabase node_principals RLS enforcement
- [ ] GitHub PR fetcher (_fetch_open_prs, _fetch_pr_status)

### Integration
- [ ] GitHub MCP tool wiring (list_pull_requests, pull_request_read, get_check_run)
- [ ] Token validation in bridge delivery layer
- [ ] Provenance validation on message ingress
- [ ] Scope checking (token scope vs. requested action)

### Testing (T1–T7)
- [ ] T1: Spoofing detection
- [ ] T2: Tampering rejection
- [ ] T3: Non-registered-as-fact escalation
- [ ] T4: Scope expansion detection
- [ ] T5: HUMAN_REQUIRED bypass prevention
- [ ] T6: Evidence validation receipt requirement
- [ ] T7: Identity confusion (IC-063) detection

### Documentation
- [ ] Phase 1 architecture doc (design decisions + tradeoffs)
- [ ] Ed25519 key management guide
- [ ] Token schema reference
- [ ] RLS policy walkthrough
- [ ] Adversarial test methodology

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|:-----|:-----------|:-------|:-----------|
| Z2 ratification delayed | Medium | +7–14 days | Monitor decision window; escalate if needed |
| GitHub API rate limits | Low | Temporary fetch failures | Implement caching + backoff strategy |
| Ed25519 key rotation not designed | Medium | Future vulnerability | Plan Phase 2 key rotation ceremony |
| RLS queries slow on large datasets | Low | Query performance | Index token_id, issued_to, consumed_at |
| Supabase connection drops | Low | Transient failures | Retry logic + exponential backoff |

---

## Success Criteria (Phase 1 DONE)

1. ✓ v0.2 specification Z2 ACCEPT signature received
2. ✓ All T1–T7 adversarial tests passing (no falsifier gaps)
3. ✓ Token validation bridge logs all token consumption in NF_LEDGER
4. ✓ Ed25519 signature verification working end-to-end (token + message + provenance)
5. ✓ GitHub API fetcher returning live PR state (CI status, reviews, conflicts)
6. ✓ Identity provenance validation detecting IC-063-like incidents (T7)
7. ✓ HUMAN_REQUIRED holds preventing unauthorized consequential actions (T5)
8. ✓ Supabase RLS enforcing node_principals + authority_tokens access control

---

## Next Actions (Z1 Proposer)

**Immediate (awaiting Z2 ratification):**
1. Refine authority token schema (NF_LEDGER design review)
2. Design T1–T7 test fixtures (parametrize falsifier checks)
3. Sketch GitHub API integration points
4. Draft Supabase RLS migration

**Post-ratification (Z2 ACCEPT required):**
1. Implement Ed25519 validator
2. Deploy Supabase RLS migration
3. Wire GitHub API calls (MCP tools)
4. Implement T1–T7 adversarial tests
5. Run full integration test suite

---

**Standing:** PLANNING (Z1 design phase)  
**Awaiting:** v0.2 Z2 ACCEPT signature → Phase 1 implementation begins  
**Probability:** 72% Phase 1 complete by 2026-10-15 (depends on Z2 timeline + dependencies)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01Lm1ut3GdgQakWK694dj3wo
