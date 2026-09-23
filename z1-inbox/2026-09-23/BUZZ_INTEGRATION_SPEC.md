# BUZZ_INTEGRATION_SPEC: HumanAIOS Z1/Z2/Z3 Governance on Buzz

**Status:** Phase 0 Deliverable (awaiting Z2 RATIFY on Q-BUZZ-COLLAB-EVAL-01)  
**Date:** 2026-09-23  
**Scope:** Detailed mapping of HumanAIOS governance operations to Buzz affordances, integration points with GitHub/CI/Slack, and feasibility assessment per operation.

---

## 1. Terminology & Roles

| Term | Meaning | Buzz Mapping |
|------|---------|---|
| **Z1** | Proposer (Claude AI) | `#proposals` channel member, posts event-text messages |
| **Z2** | Ratifier (Night) | Nostr keypair `pk_night`, posts signed RATIFY events |
| **Z3** | Executor (per-repo human or agent) | Nostr keypair per executor, posts signed VERDICT events |
| **Proposal** | Z1 candidate block (F/IC/H) | Event `kind=1` (text note), tagged `t:proposal`, thread root |
| **Ratification** | Z2 decision (ACCEPT/EDIT/REJECT) | Event `kind=1`, tagged `t:ratify`, in proposal thread, signed by pk_night |
| **Verdict** | Z3 execution record (merged/deployed/failed) | Event `kind=1`, tagged `t:verdict`, in proposal thread, signed by executor keypair |
| **Relay** | Single source of truth (events log) | Buzz relay instance (self-hosted or Railway-managed) |
| **Thread** | Discussion sequence | Nostr event thread (parent event ID in tags) |

---

## 2. Workflows: Current State vs. Proposed

### 2.1 Workflow: Z1 Proposes → Z2 Ratifies → Z3 Executes

#### Current (Email + GitHub)

```
Z1 (Claude)
  └─→ Write Q-BUZZ-... .md in z1-inbox/2026-09-23/
      └─→ Paste into email to Night
          └─→ Night reads, replies email (ACCEPT/EDIT/REJECT)
              └─→ Claude transcribes decision into REGISTERED.md + commit msg
                  └─→ Z3 (executor) reads REGISTERED.md + commit, merges PR
                      └─→ Posts Slack message "Merged Q-BUZZ-..." (unsigned)

AUDIT TRAIL GAPS:
  - Email transcript not version-controlled (IC-030, IC-031)
  - Decision signature is implicit (trust email sender)
  - Z3 executor not recorded as signed author
  - Proposal, decision, verdict are in 3 different systems (z1-inbox/, email, GitHub)
```

#### Proposed (Buzz Relay)

```
Z1 (Claude)
  └─→ buzz-cli message send --channel proposals --body "$(cat Q-BUZZ-COLLAB-EVAL-01.md)"
      └─→ Event created: { kind: 1, tags: [["t", "proposal"], ["channel", "proposals"]], 
                           content: "...", created_at: NOW, sig: Z1_SIGNATURE }
          └─→ Buzz relay stores event, indexes by tag + FTS, pub/sub notifies subscribers
              └─→ Z2 (Night) sees thread notification in Buzz desktop app
                  └─→ Reads proposal in UI, clicks "✅ RATIFY" button
                      └─→ Event created: { kind: 1, tags: [["t", "ratify"], ["e", proposal_id], 
                                           ["response", "accept"], ["hash", "sha256(...)"]], 
                                           content: "...", created_at: NOW, sig: pk_night }
                          └─→ Relay stores RATIFY event, CI gate listens for it
                              └─→ Z3 executor (GitHub Actions) receives webhook: proposal → verify gate
                                  └─→ Gate queries Buzz: "Any RATIFY event for proposal_id signed by pk_night?"
                                      └─→ Finds event, verifies signature (Schnorr), compares hash
                                          └─→ CI gate passes, PR merges automatically OR Z3 manually merges
                                              └─→ Z3 executor posts VERDICT event: 
                                                 { kind: 1, tags: [["t", "verdict"], ["e", proposal_id], 
                                                   ["response", "merged"]], content: "...", sig: z3_key }
                                                   └─→ Event recorded in relay, visible to all, searchable

AUDIT TRAIL COMPLETE:
  - All events (proposal, ratify, verdict) signed + indexed in single relay
  - No transcription, no email digest
  - Z2 signature is cryptographically verifiable (Schnorr)
  - Z3 executor's signature links to their Nostr keypair (unique per executor)
  - Full thread is searchable + queryable in Buzz, Slack integration, or API
```

---

### 2.2 Workflow: Z1 Contests Z2 Decision

#### Current

```
Z1: "Decision IC was wrong, I'm re-proposing"
→ Email Night again (within 48h window)
→ Night re-reads, replies (ACCEPT/EDIT/REJECT with "contest_response=...")
→ Claude transcribes new decision
→ REGISTERED.md updated
```

#### Proposed

```
Z1: Posts message in proposal thread
    buzz-cli message send --thread <proposal-id> --body "Contest: IC beyond 48h, re-proposing..."
    → Event created, tagged in same thread

Z2 (Night): Sees new message in thread, re-reads context
    → Reacts with 🔴 or replies with new RATIFY event
    buzz-cli reaction add --message-id <contest-id> --emoji 🔴 (rejection)
    OR
    buzz-cli message send --thread <proposal-id> --body "RATIFY (contest response)..."
    → New RATIFY event created, tagged with contest_response field in tags

CI gate: Queries Buzz for latest RATIFY event in thread (by created_at)
    → Finds new event, verifies signature, merges with new hash if ACCEPT
```

**Improvement:** Replay-safe. The final RATIFY event is canonical; all prior decisions are visible in thread for audit.

---

### 2.3 Workflow: Molt Candidate → Ratified → Applied

#### Current

```
Code (molt_cycle.py): Generates MOLT_CANDIDATE JSON
  → Writes to z1-inbox/2026-09-23/molt_ABC.json
  → Posts Slack message (unsigned) "New molt candidate ABC"
  → Waits for email approval from Night

Night: Receives email, reads candidate, replies ACCEPT/EDIT/REJECT
  → Claude transcribes into MOLT_STATE.md + git commit

Code (molt_cycle.py): Checks MOLT_STATE.md for ratified molts
  → Applies molt to constants/*.json
  → Measures at window close
  → Keeps or reverts
```

#### Proposed

```
Code (molt_cycle.py): Generates MOLT_CANDIDATE JSON
  → buzz-cli message send --channel molts --body "$(jq . molt_ABC.json)"
  → Event created: { kind: 1, tags: [["t", "molt-candidate"], ["molt_id", "ABC"]], 
                     content: JSON, sig: CODE_KEY }
                     
Night: Notification in Buzz #molts channel
  → Reads molt, sees:
    - Prediction (pinned post in thread)
    - Window (end date in thread)
    - Revert rule (anti-cascade policy in thread)
    - Falsifier (description of failure condition)
  → buzz-cli reaction add --message-id <molt-id> --emoji ✅ ACCEPT
  OR posts new message: "EDIT: change threshold from 0.5 to 0.6"
  OR reacts with ❌ REJECT
  
  → Event created: { kind: 1, tags: [["t", "molt-ratify"], ["molt_id", "ABC"], 
                     ["response", "accept"]], content: "...", sig: pk_night }

Code (molt_cycle.py): Queries Buzz for molt-ratify event matching molt_id
  → Finds ACCEPT event signed by pk_night
  → Applies molt to constants/
  → Stores event_id in molt state (proof of ratification)
  → Measures at window close
  → If falsifier tripped: REVERT event posted to Buzz
    buzz-cli message send --channel molts --body "MOLT REVERTED: ABC falsified at 2026-09-24 12:00Z"
    → Event: { kind: 1, tags: [["t", "molt-revert"], ["molt_id", "ABC"]], sig: CODE_KEY }
  → Files IC candidate for revert analysis
```

**Improvement:** MOLT_STATE.md is generated from Buzz events, not a primary source. Anti-cascade rules are checked against Buzz event history (no manual ledger keeping).

---

## 3. Event Schema: Proposal/Ratify/Verdict/Molt Lifecycle

### 3.1 Proposal Event (Z1 Files Candidate)

```json
{
  "kind": 1,
  "created_at": 1695484800,
  "tags": [
    ["t", "proposal"],
    ["proposal_id", "Q-BUZZ-COLLAB-EVAL-01"],
    ["class", "H"],
    ["zone", "operations"],
    ["falsifier", "Buzz relay cannot run HumanAIOS governance if..."]
  ],
  "content": "# Q-BUZZ-COLLAB-EVAL-01: Buzz as HumanAIOS Coordination Layer\n\n... full proposal markdown ...",
  "pubkey": "Z1_PUBKEY",  // Claude's Nostr public key
  "sig": "SCHNORR_SIGNATURE"
}
```

### 3.2 Ratification Event (Z2 Accepts/Edits/Rejects)

```json
{
  "kind": 1,
  "created_at": 1695488400,
  "tags": [
    ["t", "ratify"],
    ["e", "PROPOSAL_EVENT_ID"],  // NIP-10 root reference
    ["p", "Z1_PUBKEY"],  // reply to Z1
    ["response", "accept"],  // or "edit" / "reject"
    ["decision_hash", "sha256(Q-BUZZ-COLLAB-EVAL-01 | by=Night | at=2026-09-23T14:30:00Z | decision=ACCEPT)"]
  ],
  "content": "RATIFY Q-BUZZ-COLLAB-EVAL-01\n\nFeasibility is high. Proceed with Phase 1 pilot.",
  "pubkey": "pk_night",  // Z2's Nostr public key (authoritative)
  "sig": "SCHNORR_SIGNATURE"  // Cryptographic proof Night signed this
}
```

### 3.3 Verdict Event (Z3 Executes & Reports)

```json
{
  "kind": 1,
  "created_at": 1695496800,
  "tags": [
    ["t", "verdict"],
    ["e", "PROPOSAL_EVENT_ID"],  // root reference
    ["response", "merged"],  // or "deployed" / "failed" / "partial"
    ["commit", "abc123def456789"],  // git SHA
    ["ci_run", "run_12345"],  // CI job ID for traceability
    ["timestamp", "2026-09-23T16:45:00Z"]
  ],
  "content": "VERDICT: Merged PR #462. CI passed. Deployed to main.\n\nMerge commit: abc123\nCI logs: https://github.com/...",
  "pubkey": "Z3_EXECUTOR_PUBKEY",  // Executor's Nostr public key
  "sig": "SCHNORR_SIGNATURE"
}
```

### 3.4 Molt Events (Molt Candidate → Ratify → Apply → Revert)

#### Molt Candidate
```json
{
  "kind": 1,
  "tags": [
    ["t", "molt-candidate"],
    ["molt_id", "ABC-20260923"],
    ["constant_name", "AGENT_HUMILITY_THRESHOLD"],
    ["prior_value", "0.5"],
    ["new_value", "0.6"],
    ["window_end", "2026-09-30T00:00:00Z"],
    ["prediction", "Threshold increase improves calibration by 2-3% on RLHF benchmark"]
  ],
  "content": "Molt candidate ABC: Change AGENT_HUMILITY_THRESHOLD from 0.5 to 0.6...\n\n**Falsifier:** ...",
  "pubkey": "CODE_KEY",
  "sig": "SCHNORR_SIGNATURE"
}
```

#### Molt Ratify
```json
{
  "kind": 1,
  "tags": [
    ["t", "molt-ratify"],
    ["e", "MOLT_CANDIDATE_EVENT_ID"],
    ["molt_id", "ABC-20260923"],
    ["response", "accept"],
    ["revert_rule", "K=3, anti-cascade frozen on 2nd consecutive revert"]
  ],
  "content": "RATIFY molt ABC. Prediction and falsifier are sound. Proceed.",
  "pubkey": "pk_night",
  "sig": "SCHNORR_SIGNATURE"
}
```

#### Molt Applied (code posts event)
```json
{
  "kind": 1,
  "tags": [
    ["t", "molt-applied"],
    ["molt_id", "ABC-20260923"],
    ["commit", "xyz789abc123"],
    ["timestamp", "2026-09-23T17:00:00Z"]
  ],
  "content": "Applied molt ABC: AGENT_HUMILITY_THRESHOLD 0.5 → 0.6. Measuring until 2026-09-30.",
  "pubkey": "CODE_KEY",
  "sig": "SCHNORR_SIGNATURE"
}
```

#### Molt Revert (if falsifier tripped)
```json
{
  "kind": 1,
  "tags": [
    ["t", "molt-revert"],
    ["molt_id", "ABC-20260923"],
    ["reason", "falsified"],
    ["timestamp", "2026-09-27T10:30:00Z"],
    ["measurement_data", "calibration declined 1.2% vs. baseline"]
  ],
  "content": "REVERT molt ABC: Falsifier tripped. Calibration declined 1.2%. Filed IC-999 for analysis.",
  "pubkey": "CODE_KEY",
  "sig": "SCHNORR_SIGNATURE"
}
```

---

## 4. Integration Points

### 4.1 GitHub Webhook → Buzz NIP-34 Event

**Trigger:** PR opened/closed, commit pushed, CI result

**Flow:**
```
GitHub → (webhook) → Buzz REST endpoint
  Payload: { event: "pull_request", action: "opened", number: 123, ... }
  
Buzz (or webhook handler): 
  → Parse GitHub event
  → Create NIP-34 event (or NIP-1 with git tags)
  → Sign with CODE_KEY
  → Post to relay
  
Buzz relay: 
  → Stores event
  → Emits to #code-sync channel (or PR-specific thread)
```

**Example NIP-34 Git Event (PR opened):**
```json
{
  "kind": 30023,  // NIP-34 git repo announcement
  "tags": [
    ["d", "github.com/humanaios-ui/operations/pull/123"],
    ["name", "PR #123: Buzz integration"],
    ["web", "https://github.com/humanaios-ui/operations/pull/123"],
    ["git-http", "https://github.com/humanaios-ui/operations.git"],
    ["description", "Integrate Buzz relay as coordination layer"],
    ["branch", "claude/buzz-library-eval-y92lvd"]
  ],
  "content": "Pull request #123 opened: Buzz integration...",
  "pubkey": "CODE_KEY",
  "sig": "..."
}
```

### 4.2 Buzz → GitHub CI Gate (Merge Verification)

**Trigger:** PR merge requested by Z3 (human or bot)

**Gate Logic (GitHub Actions):**
```yaml
# .github/workflows/buzz-z2-gate.yml
name: Buzz Z2 Ratification Gate

on:
  pull_request:
    types: [synchronize, opened]

jobs:
  verify-z2:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch commit message
        run: |
          COMMIT_MSG=$(git log -1 --pretty=%B)
          PROPOSAL_ID=$(echo "$COMMIT_MSG" | grep -oP 'Q-[A-Z0-9-]+' | head -1)
          DECISION_HASH=$(echo "$COMMIT_MSG" | grep -oP 'sha256\([^)]+\)' | head -1)
          echo "PROPOSAL_ID=$PROPOSAL_ID" >> $GITHUB_ENV
          echo "DECISION_HASH=$DECISION_HASH" >> $GITHUB_ENV

      - name: Query Buzz relay
        run: |
          # NIP-01 filter: events tagged with proposal_id, response=accept, signed by pk_night
          QUERY=$(cat <<'EOF'
          [{
            "kinds": [1],
            "tags": {
              "e": ["${{ env.PROPOSAL_ID }}"],
              "t": ["ratify"],
              "response": ["accept"]
            },
            "#pubkey": "${{ secrets.BUZZ_Z2_PUBKEY }}"
          }]
          EOF
          )
          
          # Query relay (localhost:3000 in dev, hosted URL in prod)
          RATIFY_EVENT=$(curl -s "${{ secrets.BUZZ_RELAY_URL }}" \
            -H "Content-Type: application/json" \
            -d "$QUERY" | jq '.event')
          
          echo "RATIFY_EVENT=$RATIFY_EVENT" >> $GITHUB_ENV

      - name: Verify Nostr signature
        run: |
          # Use nostr crate to verify signature
          cargo install nostr-cli  # or use pre-built binary
          EVENT_JSON=$(echo '${{ env.RATIFY_EVENT }}' | jq -c .)
          VALID=$(nostr-cli verify-sig "$EVENT_JSON")
          
          if [[ "$VALID" != "true" ]]; then
            echo "❌ Z2 signature invalid"
            exit 1
          fi
          echo "✅ Z2 signature valid"

      - name: Verify decision hash
        run: |
          HASH_IN_EVENT=$(echo '${{ env.RATIFY_EVENT }}' | jq -r '.decision_hash')
          
          if [[ "$HASH_IN_EVENT" != "${{ env.DECISION_HASH }}" ]]; then
            echo "❌ Decision hash mismatch"
            echo "  Commit has: ${{ env.DECISION_HASH }}"
            echo "  Event has:  $HASH_IN_EVENT"
            exit 1
          fi
          echo "✅ Decision hash matches"

      - name: Approve merge
        run: |
          echo "✅ Z2 RATIFIED. Merge approved."
          # GitHub auto-merge can now proceed
```

### 4.3 Buzz → Slack Integration

**Trigger:** Events in Buzz relay posted to Slack channel

**Flow:**
```
Buzz relay → (webhook or relay subscription) → Slack API

On Nostr event (kind=1, tagged "proposal" / "ratify" / "verdict"):
  → Slack message posted to #buzz-governance channel
  → Message format: "@Night: Q-BUZZ-COLLAB-EVAL-01 ratified ✅"
  → Include link to event in Buzz relay (or relay URL + event ID)
```

**Example Slack Hook:**
```python
# Pseudo-code: Buzz → Slack webhook
def on_ratify_event(event):
    proposal_id = event.tags.get("e")
    pubkey = event.pubkey
    response = event.tags.get("response")  # accept/reject/edit
    
    slack_msg = f"🔏 **Z2 Ratified**: {proposal_id} → **{response.upper()}**\n"
    slack_msg += f"Signer: {pubkey[:16]}... (Z2)\n"
    slack_msg += f"Event: [Link](https://relay:3000/{event.id})\n"
    
    slack.api_call("chat.postMessage", channel="#buzz-governance", text=slack_msg)
```

### 4.4 buzz-cli: Agent Interface (Z1/Z3 Tool Use)

**Tool signature for Claude Code / LLM agents:**

```typescript
/**
 * Post a message to a Buzz channel or thread
 * @param channel - Channel name (e.g., "proposals", "molts", "verdicts")
 * @param body - Message body (markdown)
 * @param thread_id - Optional parent event ID (replies to thread)
 * @param tags - Custom NIP-01 tags (t:proposal, t:ratify, etc.)
 * @returns Event ID, relay URL, event signature
 */
async function buzzCliMessageSend(
  channel: string,
  body: string,
  thread_id?: string,
  tags?: Record<string, string[]>
): Promise<{ event_id: string; relay_url: string; sig: string }> {
  // bash: buzz-cli message send --channel <ch> --body <body> [--thread <id>] [--tags t:proposal ...]
  // Returns JSON: { event_id, relay_url, sig }
}

/**
 * Add a reaction emoji to a message
 * @param message_id - Event ID to react to
 * @param emoji - Unicode emoji or NIP-30 emoji code
 * @returns Reaction event ID
 */
async function buzzCliReactionAdd(
  message_id: string,
  emoji: string
): Promise<{ event_id: string }> {
  // bash: buzz-cli reaction add --message-id <id> --emoji <emoji>
}

/**
 * Query Buzz relay for events matching filter
 * @param filter - NIP-01 filter (kinds, tags, authors, etc.)
 * @returns Array of events
 */
async function buzzCliQuery(
  filter: Record<string, any>
): Promise<{ events: NostrEvent[] }> {
  // bash: buzz-cli query --filter '<json filter>'
  // Returns JSON: { events: [...] }
}
```

**Usage Example (Claude in z1-inbox proposal filing):**
```bash
#!/bin/bash
# File a Z1 proposal to Buzz (Python script, called from Claude Code session)

PROPOSAL_FILE="z1-inbox/2026-09-23/Q-BUZZ-COLLAB-EVAL-01.md"
PROPOSAL_ID=$(basename "$PROPOSAL_FILE" .md)

buzz-cli message send \
  --channel proposals \
  --body "$(cat "$PROPOSAL_FILE")" \
  --tags "t:proposal" "proposal_id:$PROPOSAL_ID" "class:H" "zone:operations" \
  --output json > /tmp/proposal_event.json

echo "✅ Filed proposal to Buzz"
jq . /tmp/proposal_event.json
```

---

## 5. REGISTERED.md Synchronization

### Option A: REGISTERED.md Canonical, Buzz as Reference Log

**Approach:** Keep REGISTERED.md as the system-of-record (append-only). Buzz stores all intermediate events (proposal, ratification, verdict). On demand, regenerate REGISTERED.md from Buzz events (for audit/verification).

**Pros:**
- No change to current REGISTERED.md workflow.
- Buzz is supplementary, not critical.
- Easier fallback if Buzz fails.

**Cons:**
- Requires dual-write (REGISTERED.md + Buzz).
- Transcription errors still possible.

**Implementation:**
```python
# Script: sync-registered-to-buzz.py
# Read REGISTERED.md entries (F/IC/H/MOLT)
# For each entry, post to Buzz as event (kind=1, tagged "registry-entry")
# Store event ID back in REGISTERED.md (for audit trail)

# Reverse: regenerate-registered-from-buzz.py
# Query Buzz for events tagged "registry-entry"
# Reconstruct REGISTERED.md entries from event content
# Verify hash chain integrity
```

### Option B: Buzz Canonical, REGISTERED.md as Export

**Approach:** Buzz relay is the single source of truth. REGISTERED.md is generated from Buzz events at session open (per IC-030 ritual). No manual REGISTERED.md writes; only Buzz events matter.

**Pros:**
- Single source of truth (no dual-write).
- Eliminates transcription errors.
- REGISTERED.md is verifiable from Buzz.

**Cons:**
- Breaking change to current workflow.
- REGISTERED.md becomes a derived artifact (requires re-generation).
- Requires migration of existing entries.

**Implementation:**
```bash
# Session §A ritual (new):
# 1. git fetch origin
# 2. BUZZ_RELAY_URL=$(grep -r BUZZ_RELAY_URL .env)
# 3. query-registered-from-buzz.sh > REGISTERED_REGENERATED.md
# 4. diff REGISTERED_REGENERATED.md REGISTERED.md (should match, unless new entries)
# 5. Proceed if hashes match; error if not

# Proposed entries are posted to Buzz (not z1-inbox/)
# CI gate regenerates REGISTERED.md from Buzz before merge
```

**Decision:** Recommend Option A for Phase 1 (safer), migrate to Option B in Phase 2 (if Buzz proves reliable).

---

## 6. Deployment Architecture

### Single-Relay (Dev/Pilot)

```
┌─────────────────────────────────────────────────────┐
│ Local Machine (or VPS)                              │
│                                                     │
│  Buzz Relay (Rust)                                  │
│  ├─ Nostr WS on :3000                              │
│  ├─ REST API on :3001                              │
│  └─ Admin CLI on local socket                      │
│                                                     │
│  Backend Services:                                  │
│  ├─ Postgres 15 (events + FTS index)               │
│  ├─ Redis 7 (pub/sub, rate limit, cache)           │
│  └─ MinIO / S3 (media storage)                     │
│                                                     │
│  CI/Webhook Handler                                │
│  ├─ GitHub webhook → Buzz REST                     │
│  ├─ Slack app → Buzz REST                          │
│  └─ buzz-cli (agent interface)                     │
│                                                     │
└─────────────────────────────────────────────────────┘
     ↓                     ↑
     │                     │
  GitHub              Slack + Desktop App
  (CI gate)          (Human UI + notifications)
```

### Multi-Community Hosting (Production Roadmap)

```
┌─────────────────────────────────────────────────────┐
│ Hosted Buzz (Railway or similar)                     │
│                                                     │
│  Buzz Relay (Rust, HA)                              │
│  ├─ Load balanced WS (:443/wss)                    │
│  ├─ REST API (HTTPS)                                │
│  ├─ Multi-community mode (tenant isolation)        │
│  └─ Admin dashboard                                │
│                                                     │
│  Shared Backend:                                    │
│  ├─ Postgres 15 (multi-tenant schema)              │
│  ├─ Redis cluster (pub/sub, presence)              │
│  └─ S3 (Blossom protocol)                          │
│                                                     │
│  Integrations:                                      │
│  ├─ GitHub + per-org CI gate                       │
│  ├─ Slack + per-workspace                          │
│  └─ Custom webhooks (per-community)                │
│                                                     │
└─────────────────────────────────────────────────────┘
     ↓                          ↑
     │                          │
  GitHub (31 repos)      Slack + Buzz Apps
  (CI gates per repo)    (Human + Agent UI)
```

---

## 7. Rollout Plan: Phase 1 (Pilot)

### Week 1: Setup

- [ ] Stand up local Buzz relay (Docker + Hermit, per Buzz README)
- [ ] Configure `.env`: Postgres, Redis, MinIO
- [ ] Create Nostr keypairs: `pk_z1` (Claude), `pk_night` (Z2), `pk_z3_demo` (Z3 demo)
- [ ] Wire GitHub webhook → Buzz REST handler
- [ ] Wire Slack app → Buzz relay
- [ ] Test `buzz-cli` message send / query / reaction add

### Week 2: Test Proposal Workflow

- [ ] File 2–3 test proposals (Q-TEST-...) to Buzz #proposals channel
- [ ] Z2 (Night) ratifies one via Buzz (reaction + message)
- [ ] CI gate verifies Z2 signature + hash match
- [ ] Z3 executor merges PR with VERDICT event
- [ ] Full thread is searchable in Buzz, Slack, GitHub

**Acceptance:** Single proposal lifecycle (propose → ratify → merge) completes end-to-end with signed events + searchable audit.

### Week 3: Document UX + Plan Phase 2

- [ ] Record user experience: What was smooth? What was awkward?
- [ ] Measure decision latency (email vs. Buzz): Is Buzz faster or slower?
- [ ] Check relay uptime (if local Buzz went down, how hard was recovery?)
- [ ] Draft Phase 2 plan: REGISTERED.md sync, z1-inbox → Buzz migration, Z3 training

**Deliverable:** `PHASE_1_POSTMORTEM.md` — lessons learned, recommendation for Phase 2.

---

## 8. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| **Buzz relay crashes mid-workflow** | Medium | High (blocks governance) | (a) Use managed Buzz (Railway SLA); (b) Local backup relay; (c) Fallback to email for ratification |
| **Z2 signature verification fails in CI** | Low | High (gate broken) | Test signature verification in local CI before Phase 1; pre-test with Rust `nostr` crate |
| **Z1/Z3 adoption resistance** | Medium | Medium (slow migration) | Training in Phase 2; provide `buzz-cli` wrappers (shell scripts) for common tasks |
| **REGISTERED.md diverges from Buzz** | Low | Medium (audit confusion) | Implement Option A (Buzz as reference); regenerate REGISTERED.md on demand to verify |
| **Slack integration is noisy** | Low | Low (UX only) | Filter events; allow channel muting; default to summary digest (hourly, not real-time) |
| **GitHub → Buzz webhook is lossy** | Low | Medium (missed decisions) | Log webhook payloads; alert on failures; manually re-post missed events |

---

## 9. Success Metrics (Phase 1)

- [ ] **Proposal-to-ratify latency:** ≤ 24h (vs. current 48h+ email cycle)
- [ ] **Audit trail completeness:** 100% of decisions (propose, ratify, verdict) have signed Nostr events
- [ ] **Searchability:** All three workflow types (proposal, molt, verdict) are findable by proposal_id + timestamp
- [ ] **Z2 adoption:** Night ratifies at least 3 proposals via Buzz (vs. email)
- [ ] **CI gate reliability:** 100% of approved merges verify Z2 signature; 0% false negatives
- [ ] **No regression:** Existing REGISTERED.md entries remain readable; no merge conflicts

---

## 10. Appendix: Buzz CLI Reference

```bash
# Install buzz-cli (from block/buzz release or build from source)
cargo install buzz-cli

# Configure relay + keypair
export BUZZ_RELAY_URL=ws://localhost:3000
export BUZZ_PRIVATE_KEY=<Z1_OR_Z3_SECRET_KEY>

# Post a message
buzz-cli message send \
  --channel proposals \
  --body "# Q-TEST-01\n\nTest proposal" \
  --tags t:proposal proposal_id:Q-TEST-01 zone:operations

# React to a message
buzz-cli reaction add \
  --message-id abc123def456 \
  --emoji ✅

# Query events
buzz-cli query \
  --filter '{"kinds":[1],"tags":{"t":["proposal"]}}' \
  --output json

# Subscribe to channel (live updates)
buzz-cli subscribe \
  --channel proposals \
  --output json

# Set presence (online/away)
buzz-cli presence set --status online --message "Working on Q-BUZZ-01"
```

---

**Status:** Phase 0 Deliverable  
**Next:** Z2 (Night) ratifies Q-BUZZ-COLLAB-EVAL-01 to proceed with Phase 1 pilot  
**Authors:** Claude, S-092326-01-buzz-eval
