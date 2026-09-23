# Q-Z2RATIF-MECH-32: Z2 Ratification Mechanism Undocumented

**Issue ID:** Q-Z2RATIF-MECH-32  
**Type:** IC (Internal Consistency)  
**Classification:** Internal Consistency (IC)  
**Filed:** 2026-09-23  
**Discoverer:** Claude (Z1)  
**Severity:** Medium (causes confusion, not data loss)

---

## Problem Statement

The Z2 ratification mechanism is not explicitly documented. Specifically:

1. **Z2's PR merge constitutes the ratification signature** — but this is not stated in CLAUDE.md, governance docs, or workflow guidance
2. **The Z2 ratification CI gate is designed to fail before merge** — but this is counterintuitive and undocumented, causing confusion that it's a blocker
3. **New Z1/Z2/Z3 participants cannot distinguish between:**
   - A genuine CI failure blocking merge
   - An intentional verification gate requiring Z2 override

### Evidence

- CLAUDE.md documents Z2 decision routing but does not state: "Z2's PR merge is the signature"
- z2_ratification_gate.yml workflow file does not explain its purpose: "Prevent accidental merge without Z2 review"
- When Z2 observes gate "failure" before merge, nothing in the docs explains why failing before merge is correct behavior
- Q-BUZZ-COLLAB-EVAL-01 PR #468 exemplified this: gate failed, Z2 merged anyway, but no participant (except Z2) understood that the gate failure was intentional

## Current Workflow (Implicit)

```
Z1 files candidate → Z2 reviews PR → Z2 merges (overrides gate) → Gate "failure" is verification proof
```

## Documented Workflow (CLAUDE.md)

```
Z1 files candidate → Z2 reads candidate → Z2 signs: sha256(candidate | by=Night | ...)
```

The documented workflow does not match the implemented workflow.

---

## Falsifier

**This issue is resolved when:**

1. **CLAUDE.md § Decision Routing explicitly states:**
   > "Z2 ratification occurs when Z2 merges the PR to main. The PR merge action by Z2 is the authoritative signature; the git commit SHA is the evidence."

2. **z2_ratification_gate.yml or its documentation states:**
   > "The 'Verify Z2 Ratification Requirements' gate is designed to fail before Z2 merges. The gate ensures Z2 cannot accidentally merge without review. When Z2 merges despite the gate failure, that merge action is Z2's explicit ratification signature. This is intentional and correct."

3. **New governance onboarding docs (GOVERNANCE.md or Z1_INBOX_README.md) include:**
   > "Z2 Ratification Workflow: Z1 proposes (files candidate to z1-inbox/) → Z2 reviews PR → Z2 merges (override Z2 gate) → Merge commit is the ratification signature → Z3 executes with hash from commit message."

**Falsifier condition:** Issue is FALSE if Z1 proposers and new Z2 ratifiers can read one source and understand that PR merge by Z2 = ratification without confusion about the gate failure.

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

The documented governance model (CLAUDE.md) was written before the actual workflow (PR merge = signature) was implemented. The two drifted and were not reconciled.

---

## Remediation

### Option A: Update CLAUDE.md (Preferred)

Add new section under "## Decision Routing" or "## Session Rituals":

```markdown
### Z2 Ratification: PR Merge as Signature

Z2 ratifies by merging the PR to main. The merge action is the authoritative Z2 signature.

**Workflow:**
1. Z1 files candidate block in z1-inbox/<date>/ and opens PR
2. Z2 reviews the PR (may request changes via EDIT, reject via REJECT, or prepare to merge)
3. Z2 merges PR to main branch (this action = Z2 ratification)
4. Merge commit SHA is the evidence of Z2 signature
5. Git commit message or PR title records the Z2 decision (ACCEPT/EDIT/REJECT)

**CI Gate Behavior:**
The "Verify Z2 Ratification Requirements" check fails before Z2 merges. This is intentional: 
the gate prevents accidental merge without Z2 review. When Z2 merges despite the gate 
failure, that merge action proves Z2 reviewed and approved. The gate failure is NOT a blocker.

**Recording the Signature:**
- Evidence: git commit SHA of the merge
- Decision: derived from PR title, commit message, or REGISTERED.md edit (Z2 choice)
- Timestamp: git commit timestamp
```

### Option B: Create RATIFICATION_WORKFLOW.md

Separate doc for clarity, linked from CLAUDE.md:

```markdown
# Z2 Ratification Workflow

[same content as Option A]
```

### Option C: Update z2_ratification_gate.yml comments

Add inline comments explaining the gate's purpose (low value on its own, should pair with Option A or B).

---

## Recommendation

**Implement Option A** (update CLAUDE.md). Ratification workflow is core governance; it belongs in the main authority doc, not a separate file.

**Assign to:** Z2 (Night) for review and documentation update  
**Effort:** 30 min (write section + validate against current workflow)  
**Blocks:** Nothing (documentation-only; governance already working)

---

## Related Issues

- **Q-BUZZ-COLLAB-EVAL-01:** Exposed this gap when Z2 merged despite gate "failure"; all parties except Z2 were confused
- **CLAUDE.md § Session Rituals:** Implicitly assumes Z2 writes signatures to REGISTERED.md; should clarify that PR merge is the signature

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
