# Q-Z2RATIF-MECH-32: Z2 Ratification Mechanism Undocumented

**Issue ID:** Q-Z2RATIF-MECH-32  
**Type:** IC (Internal Consistency)  
**Classification:** Internal Consistency (IC)  
**Filed:** 2026-09-23  
**Discoverer:** Claude (Z1)  
**Severity:** Medium (causes confusion, not data loss)

---

## Problem Statement

The Z2 ratification mechanism for relay-managed board-ruling blocks is **fragmented across multiple documents** and **not unified in the canonical CLAUDE.md authority reference**. This causes participants to misunderstand the merge-as-signature design and mistake the CI gate for a blocker.

**Specifically:**

1. **Z2 PR merge = ratification is documented in multiple places but not linked from CLAUDE.md:**
   - `docs/INTENT_OS_BOARD_RUNBOOK.md` documents the relay workflow
   - `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md` documents the signature contract
   - `z2_ratification_gate.yml` (lines 102–108) describes the gate's purpose
   - **Missing: single authoritative reference in CLAUDE.md § Decision Routing**

2. **The Z2 ratification CI gate's design is undocumented in the authority doc:**
   - Gate intentionally fails before Z2 merges (prevents accidental merge without review)
   - Z2 merge despite gate failure = proof of intentional ratification
   - New participants confuse this with a genuine blocker

3. **Result: participants cannot find one unified source to understand the workflow**
   - Q-BUZZ-COLLAB-EVAL-01 PR #468 exemplified this: gate failed, Z2 merged, others assumed it was an error
   - Z1 proposers wait for explicit hash instead of observing PR merge
   - New Z2 ratifiers believe the gate failure blocks merge

## Fragmented Documentation

**What exists but is scattered:**
- INTENT_OS_BOARD_RUNBOOK.md documents the merge workflow
- Z2_RULING_MERGE_IS_RATIFICATION.md documents the signature contract
- z2_ratification_gate.yml comments explain the gate design

**What's missing from CLAUDE.md:**
- Unified explanation of relay-managed block ratification (merge = signature)
- Explicit link to gate behavior (intentional pre-merge failure)
- Clarification that Z2 merge action = ratification signal

**Root cause:** Documentation was written incrementally as the workflow evolved. Authority reference (CLAUDE.md) was not updated to integrate the relay-managed block ratification model, leaving participants to search multiple files or miss the guidance entirely.

---

## Falsifier

**This issue is resolved when:**

**Single source of truth in CLAUDE.md § Decision Routing links relay-managed block ratification to existing guidance:**
1. CLAUDE.md adds a section explaining that Z2 PR merge = ratification signal for relay-managed blocks
2. Section references (links to) existing authoritative docs:
   - Z2_RULING_MERGE_IS_RATIFICATION.md (signature contract)
   - z2_ratification_gate.yml (gate design and purpose)
   - INTENT_OS_BOARD_RUNBOOK.md (relay workflow)
3. Gate behavior is explained: intentional pre-merge failure, not a blocker

**Falsifier condition:** Issue is resolved when Z1 proposers and new Z2 ratifiers can read CLAUDE.md and find authoritative unified guidance on:
1. Z2's PR merge = ratification signal for relay-managed blocks
2. Why the gate fails before merge (intentional verification)
3. How this differs from standard candidates (explicit Z2 signature via ratify.py)

---

## Impact

**Severity:** Medium  
**Scope:** Z1 proposers, Z2 ratifiers, Z3 executors

- Z1 proposers may incorrectly wait for explicit hash in REGISTERED.md instead of observing the PR merge
- New Z2 ratifiers may believe the gate failure is a blocker and not merge
- Z3 executors may not understand that the merge commit is the authoritative signature
- Confusion compounds in multi-proposal cycles, leading to stalled governance

---

## Root Cause

Documentation of relay-managed block ratification (merge = signature) exists in multiple places but is not unified or cross-linked from the canonical CLAUDE.md authority reference. CLAUDE.md was written before the relay workflow evolved, and the authority doc was not updated to integrate the new model.

---

## Remediation

**Add section to CLAUDE.md § Decision Routing** (unified source):

Include a new subsection that:
1. Explains that Z2's PR merge = ratification signature for relay-managed blocks
2. Links to existing authoritative sources:
   - `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md` (signature contract)
   - `z2_ratification_gate.yml` (gate design and purpose)
   - `docs/INTENT_OS_BOARD_RUNBOOK.md` (relay workflow)
3. Clarifies gate behavior: intentional pre-merge failure is verification, not a blocker
4. Distinguishes from standard candidates (explicit Z2 signature via ratify.py)

**Effort:** 20-30 min (write section linking existing docs, no new content creation)  
**Blocks:** None (documentation-only; governance already working as intended)

---

## Recommendation

**Assign to:** Z2 (Night) for governance decision and CLAUDE.md integration  
**Decision required:** Should CLAUDE.md § Decision Routing be updated to link and unify existing relay-managed block ratification guidance?  
**Effort (if ACCEPT):** 20-30 min (write section linking existing docs)  
**Blocks:** Nothing (documentation-only; governance already working)

**Note:** This is a documentation/integration issue, not a workflow issue. The relay-managed block ratification (merge = signature) is already implemented and documented in multiple places; the gap is unification in the canonical authority reference.

---

## Related Issues

- **Q-BUZZ-COLLAB-EVAL-01 PR #468:** Exposed confusion when Z2 merged despite gate "failure"; participants misunderstood the intentional pre-merge failure behavior
- **Documentation distribution:** Guidance on merge-as-signature exists in `Z2_RULING_MERGE_IS_RATIFICATION.md`, `INTENT_OS_BOARD_RUNBOOK.md`, and gate comments, but not linked from CLAUDE.md

---

## Appendix: Why This Matters

The Z2 ratification gate is a critical control:
- It prevents Z1 from ratifying their own proposals (Z1 can open PR, only Z2 can merge)
- It requires Z2's explicit action (not just approval in comment, but actual merge)
- It creates an auditable chain: proposal → review → merge → execution

But if Z1/Z2/Z3 don't understand that merge = signature, the control becomes invisible. New Z2 ratifiers might believe the gate failure is a bug and skip merging. Z1 proposers might not understand that their job ends when PR is opened.

This doc gap undermines the control's value.

---

**Filed by:** Claude (Z1)  
**Session:** S-092323-02-ic-discovery  
**Awaiting:** Z2 RATIFY signature on Q-Z2RATIF-MECH-32
