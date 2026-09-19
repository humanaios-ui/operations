# Q-INTENT-OS-WITNESS-LEDGER-01

**Tier:** 2 (Architecture / Governance)  
**Status:** Candidate (awaiting Z2 ratification)  
**Proposed by:** Claude (Z1 proposer)  
**Date filed:** 2026-09-19  
**Session:** https://claude.ai/code/session_012WCbNY31capoZ99NtXQuQC

---

## Problem Statement

Current HumanAIOS governance captures **technical execution** (git commits, CI/CD, code changes) but not **human decision-making and oversight** that shaped the machine work. This creates an audit trail gap:

- **Visible:** Machine commits (noreply@anthropic.com), PR merges, code diffs
- **Missing:** Human prompts, concepts, approval decisions, time investment, ratification timestamps

Example from this session (2026-09-19):
- Claude (Z1→Z3): Stopped hook logic, rebase, merge conflict resolution
- Night (Z2): Concepts (dual-authority model), approval decisions (allow both emails), governance framing

The merge commit (da7ec90) has Co-Author trailers, but no machine-readable record of:
- _When_ Night approved the dual-authority model
- _What_ Night decided (governance rationale)
- _Why_ it matters (threat model, scalability constraint)
- Linkage from human decision to machine execution

This gaps becomes critical at scale: As HumanAIOS onboards independent Z3 executors with their own stop hooks, authority, and Z2 gates, we need a **canonical witness ledger** that captures all human-machine decision nodes.

---

## Proposed Solution: INTENT-OS Witness Ledger

**INTENT-OS maintains an append-only ledger** of governance decisions, indexed by decision ID, capturing both human and machine actors:

### Ledger Entry Schema

```json
{
  "decision_id": "Q-INTENT-OS-WITNESS-LEDGER-01",
  "timestamp_utc": "2026-09-19T18:45:00Z",
  "actor_type": "human|machine",
  "actor_email": "carly.r.anderson@gmail.com|noreply@anthropic.com",
  "actor_role": "Z2|Z1|Z3",
  "decision_class": "approve|propose|execute|ratify",
  "title": "Approve dual-authority stop hook governance model",
  "context": "Stop hook must allow both Z2 authorized emails for machine and human actors",
  "authority_level": "Z2",
  "artifacts": {
    "pr": "humanaios-ui/operations#416",
    "commit": "da7ec90",
    "session_url": "https://claude.ai/code/session_012WCbNY31capoZ99NtXQuQC",
    "registered_md_entry": "Q-INTENT-OS-WITNESS-LEDGER-01"
  },
  "rationale": "INTENT-OS allows Z2 machine commits via authorized noreply@anthropic.com; human Z2 (Night) approves dual-authority model to represent both actors",
  "falsifier": "Stop hook rejects unauthorized emails; if either Z2 email is removed without ratification, falsifier trips and IC is filed"
}
```

### Ledger Integration Points

1. **Stop hook queries INTENT-OS** (Tier 2 implementation):
   - Instead of hardcoded email list, query `/api/z2-authorized-emails`
   - Cache locally; fall back to hardcoded list if INTENT-OS unavailable
   - Enables onboarding users with their own emails without code changes

2. **PR merges record decision**:
   - When Z2 merges a PR, INTENT-OS logs: actor (Z2 email), decision (approve), timestamp, artifacts
   - Becomes audit trail for regulatory/compliance review

3. **Z1 proposals include witness context**:
   - Candidate blocks link to prior INTENT-OS decision that authorized the work
   - Example: "Q-INTENT-OS-WITNESS-LEDGER-01 approved dual-authority model (Night, 2026-09-19 18:45)"

4. **Z3 execution logged**:
   - When Z3 (Claude) executes rebased commits, log: actor, execution type, commit range, timestamp
   - Creates chain: Human approved → Machine proposed → Machine executed → Human ratified (merge)

### Audit Trail Example (This Session)

```
2026-09-19 18:42 UTC | Z2 | Night (human)    | carly.r.anderson@gmail.com | Concept    | Dual-authority stop hook model required for INTENT-OS
2026-09-19 18:43 UTC | Z1 | Claude (machine) | noreply@anthropic.com      | Propose    | Update stop hook logic (lines 83-84, 104)
2026-09-19 18:44 UTC | Z3 | Claude (machine) | noreply@anthropic.com      | Execute    | Rebase 51 commits to Z2 machine authority
2026-09-19 18:45 UTC | Z3 | Claude (machine) | noreply@anthropic.com      | Propose    | PR #416 as Z3 ratification stamp
2026-09-19 18:XX UTC | Z2 | Night (human)    | carly.r.anderson@gmail.com | Ratify     | Merge PR #416 (when approved)
```

Each row links to: decision ID, session URL, commit SHAs, REGISTERED.md entry, rationale.

---

## Implementation Path

### Phase 1 (Tier 2 Foundation)
- [ ] Design INTENT-OS Witness Ledger schema (done, above)
- [ ] Add `/api/z2-authorized-emails` endpoint to INTENT-OS
- [ ] Update stop hook to query it (with local fallback)
- [ ] Manual ledger entry creation via CLI/Python

### Phase 2 (Integration)
- [ ] Auto-log Z2 merges via GitHub webhook
- [ ] Link PRs to ledger entries via commit message trailer
- [ ] Add REGISTERED.md references to decision IDs

### Phase 3 (Scale)
- [ ] Z1 candidate blocks include decision context
- [ ] Z3 execution logs to ledger automatically
- [ ] INTENT-OS board shows decision timeline + actors

---

## Why This Matters

**Governance scalability:** As HumanAIOS onboards independent Z3 executors (10s→100s of humans and machines), you can't maintain a hardcoded stop-hook email list. INTENT-OS witness ledger becomes the source of truth.

**Audit & compliance:** Regulatory review of "who decided what, when" is answered by ledger queries, not git archaeology.

**Human-machine collaboration record:** This session's question—"how do we represent that human concepts and machine execution happened together?"—is answered by the ledger linking human decisions to machine acts.

**INTENT-OS as witness, not just authority:** Currently INTENT-OS authorizes machine commits. Witness ledger makes it the canonical record of _why_ those commitments are valid.

---

## Falsifier (Required by Governance Model)

**Falsified if:**
1. INTENT-OS ledger is modified retroactively without Z2 signature
2. Z2 authorized email is removed from stop hook without corresponding ledger entry
3. A Z3 executor's commits are not logged to INTENT-OS within 48h of execution
4. A human decision (Z2 approval) is missing from ledger for any merged PR

**Remediation:** File IC candidate blocking new Z3 assignments until ledger integrity is restored.

---

## References

- CLAUDE.md: Z-roles, dual-authority model, INTENT-OS as Z2 machine authorization
- PR #416: Example of human-machine co-authored governance merge
- FRAMEWORK_MAPPING.md: Maps 5 AI engineering concepts to Z-roles
- Session context: This conversation (2026-09-19 17:00–18:45 UTC)

---

## Next Step

**For Z2 (Night):**
Ratify this Tier 2 architecture proposal to unlock stop-hook INTENT-OS integration and witness-ledger foundation for scaling HumanAIOS governance.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012WCbNY31capoZ99NtXQuQC
