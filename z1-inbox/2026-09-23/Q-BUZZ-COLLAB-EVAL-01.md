# Q-BUZZ-COLLAB-EVAL-01: Buzz as HumanAIOS Coordination Layer

**Proposal ID:** Q-BUZZ-COLLAB-EVAL-01  
**Status:** CANDIDATE (awaiting Z2 RATIFY)  
**Date filed:** 2026-09-23  
**Proposer (Z1):** Claude  
**Session:** S-092326-01-buzz-eval  

---

## Executive Summary

Block's **Buzz** is a self-hostable, Nostr-relay-based workspace designed for human-agent collaboration. This proposal evaluates whether Buzz could serve as a primary coordination layer for HumanAIOS Z1/Z2/Z3 governance, reducing fragmentation across chat, docs, PRs, and workflow systems by unifying them into a single event log with built-in audit trails and agent membership.

**Falsifier:** Buzz cannot run HumanAIOS governance in-product if (1) it lacks support for cryptographic confirmation of Z2 decisions, or (2) it cannot integrate with GitHub's `git push` authorization gate to enforce Z2 hash requirements on merge. Preliminary findings suggest (1) is achievable via Nostr event signatures (native) and (2) is achievable via REST webhooks + `buzz-cli` JSON interface, but requires integration work beyond this session's scope.

---

## Problem Statement

**Current state:**  
HumanAIOS coordinates work across multiple surfaces: REGISTERED.md (canonical decisions), GitHub issues/PRs (code review + merge gates), Slack/Discord (real-time discussion), email (async ratification), and internal memory/memory dumps (context). Z1 proposals live in z1-inbox/ markdown files, awaiting Z2 ratification via email; Z2 decisions are recorded as commit metadata ("ratified Q-...-01"), then transcribed back to REGISTERED.md. This creates:

1. **Context switching:** Proposers and ratifiers juggle 5+ tabs for one decision cycle.
2. **Audit trail gaps:** Z2 emails are not version-controlled; transcription errors (IC-030, IC-031) occur.
3. **Agent friction:** Agents (Z3) cannot participate as members in Z2 ratification — they post to Slack/email, human reviewers approve, and the human's action is logged, not the agent's reasoning.
4. **Consensus fragility:** A single tool outage (GitHub, email, Slack) stalls governance until manual recovery.

**Why Buzz matters:**  
Buzz unifies the workspace into a single event log (Nostr relay) with:
- **Signed events:** Every Z1 proposal, Z2 decision, and Z3 execution is a cryptographically signed event, visible to all, queryable, and provenance-linked.
- **Agent membership:** Agents add themselves to channels just like humans, with their own Nostr keypair. A Z3 executor's VERDICT event carries the agent's signature, not a human's.
- **Audit log:** All events (proposal, comment, decision, merge, deploy) live in the same log and are searchable. No transcription, no email digest.
- **Relay independence:** The relay can be self-hosted, air-gapped, or federated across relays; it's not cloud-dependent.
- **Git integration (NIP-34):** Patches, CI results, merge decisions, and release notes are Nostr events. Same identity model for human reviewers and bot feedback.

---

## Proposal: Pilot Buzz as Z1/Z2/Z3 Coordination

### Phase 0: Evaluation (this session)

**Deliverable:** `BUZZ_INTEGRATION_SPEC.md` — mapping of HumanAIOS governance operations (Z1 propose, Z2 ratify, Z3 execute) to Buzz affordances, with integration points (GitHub webhooks, git push gates, CLI tools) and feasibility assessment.

**Time estimate:** 4–6 hours design + 2–4 hours prototype.

**Acceptance:** Z2 (Night) confirms spec is implementable by an independent executor.

### Phase 1: Local Pilot (1–2 weeks, pending Z2 ratification)

1. **Stand up local Buzz relay** for operations workspace.
2. **Wire GitHub → Buzz:** Webhook on PR open/close/comment → Buzz NIP-34 event.
3. **Wire Buzz → GitHub:** `buzz-cli` to accept Z2 ratification, emit VERDICT event, trigger GitHub merge.
4. **File 2–3 test proposals** (non-blocking) in Buzz and walk the Z1→Z2→Z3 flow.
5. **Document UX gaps** (what felt awkward, what was smooth).

**Success criteria:**
- A single Z2 decision (ratify a proposal) lives in Buzz as a signed event, surfaces in both Slack + GitHub, and triggers CI gate + merge without manual intervention.
- Audit log is complete and queryable.

### Phase 2: Integrate REGISTERED.md (conditional, pending Phase 1)

- Sync REGISTERED.md entries to Buzz as events (or keep REGISTERED.md as canonical; TBD based on Phase 1 learnings).
- Move z1-inbox/ proposals to Buzz channels.
- Teach Z1/Z2/Z3 workflows to use Buzz CLI for ratification.

---

## Integration Points

### 1. Z1 Proposal → Buzz Channel Post

**Current:** Z1 writes markdown to z1-inbox/, emails Z2, waits.  
**Proposed:** Z1 posts proposal thread to `#proposals` channel in Buzz (or `#z1-inbox-2026-09-23`). Message body is YAML front-matter + proposal body. Thread is immediately visible to Z2 and all stakeholders.

**Implementation:** `buzz-cli` call from Claude Code session:
```bash
buzz-cli message send \
  --channel proposals \
  --body "$(cat Q-BUZZ-COLLAB-EVAL-01.md)"
```

### 2. Z2 Ratification → Signed Event

**Current:** Z2 emails approval (carly.r.anderson@gmail.com), signature is implicit trust.  
**Proposed:** Z2 posts ratification reaction + message to proposal thread:
```
✅ RATIFY Q-BUZZ-COLLAB-EVAL-01
Hash: sha256(candidate | by=Night | at=2026-09-23T14:30:00Z | decision=ACCEPT)
```
Buzz client signs the event with Night's Nostr keypair; the signed event is the ratification record.

**Implementation:** Buzz desktop app, or `buzz-cli`:
```bash
buzz-cli reaction add --message-id <id> --emoji ✅
buzz-cli message send \
  --thread <proposal-id> \
  --body "RATIFY Q-BUZZ-COLLAB-EVAL-01\nHash: sha256(...)"
```

### 3. CI/CD Gate Verification

**Current:** GitHub Actions workflow manually checks for Z2 email in transcript, parses hash from commit message.  
**Proposed:** CI gate queries Buzz relay for RATIFY event:
```bash
# Pseudo-code: CI gate
BUZZ_QUERY="[{ kinds: [1], tags: { t: ['RATIFY'], p: ['<proposal-id>'] } }]"
RATIFY_EVENT=$(curl -s "$BUZZ_RELAY" --data "$BUZZ_QUERY" | jq '.event')
Z2_SIG_VALID=$(nostr-verify-sig "$RATIFY_EVENT")
HASH_MATCH=$(echo "$GIT_COMMIT_MSG" | grep -F "$(echo "$RATIFY_EVENT" | jq -r '.hash')")

if [[ "$Z2_SIG_VALID" == "true" ]] && [[ -n "$HASH_MATCH" ]]; then
  echo "Z2 ratification confirmed"
else
  echo "Missing or invalid Z2 ratification"
  exit 1
fi
```

**Integration point:** Replace `z2_ratification_gate.yml` with `buzz_z2_gate.yml` that:
- Accepts `BUZZ_RELAY_URL` (env var, defaults to localhost:3000 for dev, hosted Buzz for prod).
- Queries Buzz for RATIFY event matching commit message hash.
- Validates Nostr signature against Z2 public key (pinned in repo secrets).
- Blocks merge if signature invalid or event not found.

### 4. Z3 Execution → VERDICT Event

**Current:** Z3 (executor) merges PR, pushes code, emits message to Slack (not signed, not indexed).  
**Proposed:** Z3 posts VERDICT event to Buzz:
```
{
  kind: 1,  // text note
  tags: [["t", "VERDICT"], ["e", "<proposal-id>"], ["response", "merged"]],
  content: "Merged Q-BUZZ-COLLAB-EVAL-01. CI passed. Deployed to main."
}
```

**Implementation:** Z3 executor calls `buzz-cli` post-merge:
```bash
buzz-cli message send \
  --channel verdicts \
  --thread <proposal-id> \
  --body "VERDICT: merged. CI passed. Deployed to main."
```

---

## Architecture: Buzz Relay + HumanAIOS Integration

```
┌─────────────────────────────────────────────────────────────┐
│ HumanAIOS Clients & Workflows                              │
│ (Claude Code, Z1 proposal, Z2 ratifier, Z3 executor)      │
│                    │                                        │
│   ┌────────────────┼────────────────┐                      │
│   │                │                │                      │
└───┼────────────────┼────────────────┼──────────────────────┘
    │                │                │
    ▼                ▼                ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│buzz-cli  │  │buzz-acp      │  │Desktop App   │
│JSON I/O  │  │(ACP harness) │  │(human UI)    │
└────┬─────┘  └──────┬───────┘  └──────┬───────┘
     │                │                 │
     └────────────────┼─────────────────┘
                      │ WS + REST
                      ▼
    ┌─────────────────────────────────────────┐
    │       Buzz Relay (NIP-01, NIP-34)       │
    │ Proposal events | Ratify events         │
    │ Verdict events  | CI/workflow events    │
    │ (signed Nostr event log)                │
    └──┬──────────────────────────────────────┘
       │
       ├─► Postgres (FTS index, audit chain)
       ├─► Redis (pub/sub, presence)
       └─► S3/MinIO (media: screenshots, logs)
       
├─► GitHub (webhook: NIP-34 PR sync, CI results)
├─► CI/CD (gate: query Buzz for Z2 ratification)
└─► Slack (integration: relay events → channel posts)
```

---

## Feasibility Assessment

### ✅ Native to Buzz (low effort)

- **Event storage & query:** Nostr relay + SQL FTS. Events are queryable, indexed, tamper-evident.
- **Signing & verification:** Nostr uses Schnorr signatures (BIP-340). Keypair-per-user (Z1/Z2/Z3 agents). Verification is standard library.
- **Audit trail:** Relay appends events, no deletion. Perfect for governance audit.
- **Git integration (NIP-34):** Block ships `git-sign-nostr` and `git-credential-nostr`; patches and CI results are Nostr events.

### 🚧 Requires Integration (1–2 weeks)

- **GitHub webhook → Buzz:** Boilerplate. Trigger Buzz event on PR open/close, CI pass/fail.
- **Buzz → GitHub:** Use `buzz-cli` JSON output to parse VERDICT, call GitHub API to merge.
- **CI gate + Nostr verification:** Boilerplate. Query Buzz relay, verify signature against Z2 public key.
- **REGISTERED.md sync:** Option (a) keep REGISTERED.md canonical, sync to Buzz as reference event; Option (b) make Buzz canonical, regenerate REGISTERED.md on demand. Decision pending Phase 1 learnings.

### ❌ Out of Scope for Phase 0

- Multi-relay federation (Buzz supports it, but we'll use single relay initially).
- Web-of-trust reputation (Buzz design, not integrated yet).
- Mobile client integration (Buzz ships iOS/Android, but Z1/Z2 workflows not yet optimized for mobile).

---

## Falsifier: What Could Go Wrong

**Falsifier:** This proposal is REJECTED if:

1. **Z2 signature verification fails in CI:** Nostr event signatures cannot be reliably verified in a GitHub Actions context (e.g., dependency unavailable, signature format incompatible). *Mitigation:* Verify against existing Rust crate `nostr` (used by Block internally); test in CI before committing.

2. **Buzz relay availability is worse than email + GitHub:** We trade GitHub + email as separate failure domains for a single Buzz relay as a critical path dependency. If Buzz relay is down more often than the union of GitHub + email outages, the trade is bad. *Mitigation:* Use managed Buzz hosting (Railway, already available) with SLA + redundancy. Test failover scenario in Phase 1.

3. **Z2 ratification path is slower in Buzz than email:** Z2 must click a button in Buzz app instead of reply-all email, and it takes longer. *Mitigation:* Measure time-to-ratify in Phase 1. If Buzz is slower, fall back to email + transcription (current state). If tied or faster, switch.

4. **Integration cost exceeds benefit:** The effort to wire GitHub → Buzz → CI gate is more than the payoff (reduced context switching + better audit). *Mitigation:* Phase 1 pilot is limited scope; if integration feels painful, deprioritize Buzz for Z1/Z2/Z3 and use it for team comms only.

---

## Related Work

- **Nostr protocol:** https://github.com/nostr-protocol/nostr (relay spec, NIP-01)
- **NIP-34 (Git events):** https://github.com/nostr-protocol/nips/blob/master/34.md
- **Block/Buzz:** https://github.com/block/buzz (Apache 2.0, production-ready relay + CLI)
- **Schnorr signatures (BIP-340):** https://github.com/bitcoin/bips/blob/master/bip-0340.mediawiki (cryptographic standard, no blockchain required)
- **ACP harness:** Buzz integrates with Anthropic's Agent Control Protocol for Claude agents

---

## Next Steps

### Immediate (this session)

1. ✅ Read Buzz README and architecture docs.
2. ✅ Clone Buzz repo locally.
3. **TODO:** Write detailed integration spec: `BUZZ_INTEGRATION_SPEC.md`.
4. **TODO:** Map HumanAIOS governance workflows to Buzz affordances (Z1 → channel, Z2 → reaction, Z3 → VERDICT).
5. **TODO:** File this candidate with falsifier to REGISTERED.md (awaiting Z2 RATIFY).

### Pending Z2 Ratification

- Phase 1 pilot (if ratified).
- Local Buzz relay + test proposals (if ratified).

---

## Appendix: Why Not <Other Tool>?

| Tool | Why Not | Verdict |
|------|---------|---------|
| **Slack** | Audit trail is time-limited (90 days); cannot cryptographically sign governance decisions; no git integration; centralized cloud. | Insufficient audit. |
| **Linear/Jira** | Issue tracker, not a relay; no agent membership; signatures not native; no git integration beyond webhooks. | Missing core features. |
| **Discord** | Chat app; ephemeral history; no cryptographic guarantees; no native git integration. | Same as Slack. |
| **Matrix** | Decentralized chat; supports signing (via E2E encryption); no native git integration; not designed for governance events. | Closer, but Matrix is chat first, governance second. Buzz is governance first. |
| **GitLab** | Git hosting + CI/CD; no relay architecture; all events opaque to external agents unless they have repo write access (coarse-grained). | Missing agent membership + relay isolation. |
| **Phabricator** | Very full-featured forge; no relay or event log; no agent membership. | Too heavy, wrong shape. |

---

## Estimator Notes

- **Discovery:** 2h (read Buzz docs, understand Nostr/NIP-34).
- **Spec writing:** 3h (this document + detailed integration spec).
- **Phase 1 prototype (if ratified):** 8–12h (wire GitHub webhook, test Z1→Z2→Z3 flow, document gaps).
- **Phase 2 (conditional):** 20–30h (REGISTERED.md sync, z1-inbox/ migration, Z3 executor training).

---

**Filed by:** Claude  
**Session:** S-092326-01-buzz-eval  
**Awaiting:** Z2 RATIFY signature from Night (carly.r.anderson@gmail.com)
