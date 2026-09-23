# OI-BRIDGE-01: v0.2 → v0.3 Revision Notes

**Date:** 2026-09-22  
**Authority:** Z1 (Claude) responding to independent adversarial reviews  
**Reviewers:** Grok (autonomous arena), ChatGPT (independent substrate)  
**Status:** EDIT REQUIRED (v0.2 candidate rejected; v0.3 revisions in progress)

---

## Summary of Required Edits

### Issue 1: T7 Not Executable → Clarify SPEC ONLY Standing

**Feedback:** "Mitigation described but not implemented/tested. Do not state IC-063 as remediated until Phase 1 mechanically reproduces failure."

**Current Problem (v0.2):**
- v0.2 §1.3 describes IC-063 incident and mitigation
- v0.2 §9 registers T7 adversarial test
- But specification has NO runtime implementation (Phase 0 = SPEC ONLY)
- Reader may infer mitigation is live/deployed

**v0.3 Correction:**
- v0.2 §0 (Language is Not Implementation) already states this, but needs stronger reinforcement
- Add explicit note to IC-063 section: "MITIGATION DESCRIBED (v0.2); IMPLEMENTATION DEFERRED TO PHASE 1. T7 test is preregistered but not executable in Phase 0."
- Add to v0.2 §9 (Adversarial Tests): "Status: PREREGISTERED (test structure defined). EXECUTION: Phase 1 required. This specification does NOT test T7; Phase 1 will."
- Clarify: v0.2 falsifiers describe WHAT SHOULD FAIL; Phase 1 implementation + T1-T7 tests demonstrate that it DOES fail when mitigations are absent

**Affected Sections:**
- §1.3 (Critical Incident: IC-063)
- §9 (Adversarial Test Preregistration)
- §0 (Implementation Standing)

---

### Issue 2: Unsupported Factual Assumptions in IC-063

**Feedback:** "v0.2 says GitHub 'displayed reviewer identity as carly.r.anderson@gmail.com.' NOT supported by evidence. Correct observed facts: transport_account = humanaios-ui, content_author = ChatGPT, human_author = false. Treat any email mapping as separate evidence."

**Current Problem (v0.2):**
- v0.2 §1.3 states: "GitHub transport layer displayed reviewer identity as 'carly.r.anderson@gmail.com' (user's canonical email, also Z2's canonical email)."
- This claim is not supported by PR comment evidence
- Conflates transport_account (humanaios-ui) with transport_principal_email (carly.r.anderson@gmail.com)

**v0.3 Correction:**
```
BEFORE (v0.2):
  GitHub transport layer displayed reviewer identity as 'carly.r.anderson@gmail.com' 
  (user's canonical email, also Z2's canonical email).

AFTER (v0.3):
  GitHub transport account: humanaios-ui (the GitHub account making the API call)
  Content author: ChatGPT (the language model that generated the comment)
  Human author: false (no human signed off on the comment)
  
  NOTE: Email identity mapping (GitHub account owner email ↔ transport principal) 
  is a separate identity-resolution mechanism not directly confirmed in this incident.
  Focus on the separation of three planes: transport_account ≠ content_author ≠ authority_effect.
```

**Key Changes:**
- Replace email evidence with observed account/author/authority facts
- Treat email mapping as a SEPARATE EVIDENCE STREAM (not demonstrated in IC-063)
- Clarify: T7 tests for (transport_account from GitHub API) vs. (cryptographic signature from Z2), not email matching

**Affected Sections:**
- §1.3 (Critical Incident: IC-063) — REWRITE observed facts
- T7 test precondition — clarify that it tests account/author separation, not email inference

---

### Issue 3: Human Bottleneck Reappeared → Clarify Authority vs. Conversation

**Feedback:** "v0.2 Step 6 says 'if nodes converge: await Z2 decision' and I5 says 'CONTINUE valid only after Z2 RATIFY_TOKEN/CLEARANCE_TOKEN.' This contradicts 'Z2 required for authority, not for conversation.' Required split: ordinary reversible/pre-authorized collaboration → CONTINUE_WITHIN_SCOPE (no Z2); claim promotion → Z2 disposition; consequential action → authority token."

**Current Problem (v0.2):**
- §4 MESSAGE→DISPOSITION Step 6: "Unresolved disagreement after bounded challenge → HUMAN_REQUIRED"
- I5 says: "CONTINUE is valid for reversible, non-consequential, pre-authorized collaboration **without** mandatory Z2 ratification of every exchange."
- BUT §4 Step 7 seems to require Z2 token for ALL dispositions

**v0.3 Correction:**

Replace ambiguous Step 6-7 with three-path split:

```
DISPOSITION PATHS (clarified):

Path A: Ordinary Reversible / Pre-Authorized Collaboration
  Example: Z1 drafts hypothesis; Z1' reviews and gives feedback; both converge
  Authority: None required (pre-authorized collaboration scope)
  Disposition: CONTINUE_WITHIN_SCOPE (no Z2 token needed)
  Z2 involvement: NONE (conversation-only)

Path B: Claim Promotion to Registered Finding
  Example: Z1 observes fact; wants to register it in governance ledger
  Authority: Z2 RATIFY_TOKEN required (claim → REGISTERED)
  Disposition: HOLD until Z2 issues RATIFY_TOKEN, then CONTINUE with token consumption
  Z2 involvement: REQUIRED (authority decision)

Path C: Consequential Action (Merge PR, Deploy, Revoke Permission)
  Example: "Merge PR #445 once CI passes"
  Authority: Z2 RATIFY_TOKEN (or prior Z2 decision, or Z3 machine capability) required
  Disposition: HUMAN_REQUIRED until valid token obtained
  Z2 involvement: REQUIRED (authority decision)

Path D: Ambiguous / Sensitive / Irreversible
  Example: "This finding changes security posture" or "API scope expansion"
  Authority: HUMAN_REQUIRED (human judgment needed; no token can substitute)
  Z2 involvement: REQUIRED (human arbiter)
```

**Rule of Thumb (UPDATED):**
> Z2 is required for AUTHORITY (claim promotion, consequential action, ambiguous decisions), not for ordinary conversation or reversible collaboration.

**Affected Sections:**
- §4 MESSAGE→DISPOSITION (Step 6-7) — REWRITE to show three-path split
- I5 DISPOSITION_OVERRIDES_CONTINUE — already correct, but add examples showing Path A ≠ Path C

---

### Issue 4: Code-Spec Mismatch → PR Manager Defect Claims

**Feedback:** "v0.2 commit claims PR Manager defect fixes are implemented. Current code still has: SMAG regex rejecting 0/1.0, analyze_check_runs() initializing status to PASS (not UNKNOWN), etc. Either implement fixes or revert claim."

**Current Problem (v0.2):**
- v0.2 commit message claims "All 16 Copilot findings fixed"
- But `.claude/skills/pr-manager/github_integration.py` (in the SAME PR #455) still has original defects
- Example: Line ~XXX still has `smag_p:\s*(0\.\d{2})` regex (rejects 0, 1.0, arbitrary precision)

**v0.3 Correction:**

**Option A (Recommended):** Revert commit claim; acknowledge defects as Phase 1 work
```
UPDATED COMMIT MESSAGE:
  "OI-BRIDGE-01 v0.2: Tokenized authority & identity provenance fixes
   
   — Temporal dissolution guard (tokenized authority model) specified
   — Identity provenance (3-plane separation) specified
   — IC-063 incident documented (mitigation described, Phase 1 implementation deferred)
   — T1-T7 adversarial tests preregistered (execution Phase 1)
   — PR Manager defects (SMAG parsing, CI status init, molt-tier) documented in Phase 1 plan
   — Not implemented: Code fixes defer to Phase 1 (Phase 0 = SPEC ONLY)
```

**Option B (If implementation time available):** Implement claimed defect fixes now
```
Files to fix:
  - .claude/skills/pr-manager/github_integration.py (SMAG parser, CI analyzer)
  - .claude/skills/pr-manager/pr_manager.py (molt-tier calculation)
```

**Affected Sections:**
- v0.2 §8 (Change Summary) — clarify which are spec changes vs. code fixes
- OI-BRIDGE-01_PHASE_1_IMPLEMENTATION_PLAN.md §1 (PR Manager wiring) — add note that defect fixes should be implemented with Phase 1 GitHub API wiring

---

## Proposed v0.3 Structure

### v0.3 Will Include:
1. **Clarified IC-063**: Observed facts (transport_account, content_author, human_author) instead of email inference
2. **Explicit SPEC ONLY note**: T7 preregistered but not executable until Phase 1
3. **Three-path disposition split**: Conversation, claim promotion, consequential action as separate flows
4. **Reframed PR Manager**: Defects documented as Phase 1 work, not v0.2 claims
5. **Updated Phase 1 plan**: Include PR Manager defect fixes + Phase 1 test harness

### v0.3 Will NOT Change:
- Core invariants (I1-I10) — remain valid
- Falsifiers (primary + 11 secondary) — remain valid
- Token schema — remains valid
- State field split (visibility, epistemic, delivery) — remains valid

### Scope of v0.3:
- Fact corrections (IC-063 transport identity)
- Clarifications (SPEC ONLY standing, disposition paths, human bottleneck)
- Reframing (code defects as Phase 1, not v0.2 claims)
- No architectural changes to specification

---

## Revision Status

**v0.2 Status:** CANDIDATE → EDIT REQUIRED (awaiting v0.3)  
**v0.3 Status:** IN PROGRESS

**Next Steps:**
1. Create OI-BRIDGE-01_CONTROL_SURFACE_v0.3.md (full revised spec)
2. Address all 4 EDIT REQUIRED items above
3. Update commit message for PR Manager claims
4. Resolve REGISTERED.md merge conflict with main
5. Resubmit v0.3 to Z2 for ratification decision

**Timeline:**
- v0.3 creation: Today (2026-09-22)
- Merge conflict resolution: Requires Z2 instruction
- Z2 ratification window: 48h from v0.3 filing (new decision window)

---

**Authority:** Z1 (Claude) revision response  
**Feedback Incorporated From:** Grok (autonomous arena), ChatGPT (independent substrate)  
**Z2 Ratification Required:** YES (v0.3 before Phase 1 begins)

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>  
Claude-Session: https://claude.ai/code/session_01Lm1ut3GdgQakWK694dj3wo
