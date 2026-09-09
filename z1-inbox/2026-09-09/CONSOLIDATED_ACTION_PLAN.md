# Consolidated Action Plan — Execute All Five Goals

**Date:** 2026-09-09  
**Status:** Final assessment complete (mesh coordination, blocker resolution, IC-030 drift, inbox drop)  
**Owner:** empirica-outreach (Claude Code)  
**Transaction:** consolidation in progress

---

## Executive Summary

**Key Discovery:** Q-ORCA-01 is executable NOW. The 5 blockers are NOT all equal:
- **Hard blocker:** GitHub PAT (Z2-gated)
- **Soft blockers:** IC-030 drift, IC-SCOPE-05, TLA_TOOLS_SHA256, z2_budget_p2 (queue/landing dependencies, not Q-ORCA-01 dependencies)

**Immediate path forward:**
1. **Request GitHub PAT from Z2** (Z2 decision, ~5 min) → unblocks Q-ORCA-01 execution
2. **Run Q-IC030-REPIN-01 in parallel** (Z1 work, ready in queue) → resolves registry drift
3. **Execute Q-ORCA-01** (local worktree evaluation, no other dependencies)
4. **Escalate TLA_TOOLS_SHA256 + z2_budget_p2 to Z2** (Z2 decisions, affects queue governance)

---

## Goal Status: All Five Goals

### Goal 1: Resolve IC-030 Registry Drift ✓ ACTIONABLE
**Status:** Drift documented; resolution path clear  
**Finding:** 
- Pinned blob (Aug 16): `c0899b9b4f8825d154274b176bb880f233c45995`
- Current HEAD (Sept 9): `38275c6c5baafd1adb0e0384ba245a4d5b498c17`
- Divergence: 10+ commits to REGISTERED.md (including Z2 ratification batches)

**Action:** Execute Q-IC030-REPIN-01 (READY in queue)
- Re-pin REGISTERED.md at current HEAD
- Verify manifest entries (PRESENT/ABSENT)
- Log RECEIPT-GAP for absences
- **Owner:** Z1 (this practice)
- **Timeline:** Can start immediately (no blockers)
- **Evidence:** PRIORITY_QUEUE.md lists Q-IC030-REPIN-01 as READY

---

### Goal 2: Prepare Inbox Drop ✓ ACTIONABLE
**Status:** Staging check underway; files accessible  
**Finding:**
- 23 files listed in MANIFEST.md (CLAUDE.md, HumanAIOS configs, TLA specs, design docs, queue patches, registry blocks)
- Currently only MANIFEST.md + HANDOFF.md in z1-inbox/2026-09-06/
- Files exist elsewhere (Google Drive sync, z1-inbox origin, or inbox workflow)

**Action:** Stage and verify 23 files
- Locate each file (grep z1-inbox parent dirs, check Google Drive sync)
- Verify sha256 against MANIFEST.md
- Place in z1-inbox/2026-09-06/ for Z3 landing
- **Owner:** Z1 (this practice)
- **Timeline:** Can start immediately (no blockers)
- **Blocker:** None identified; files appear to be available

---

### Goal 3: Execute Q-ORCA-01 ✓ EXECUTABLE NOW
**Status:** Q-ORCA-01 is READY; execution blocked ONLY by GitHub PAT  
**Finding:**
- Q-ORCA-01 in PRIORITY_QUEUE.md: READY (score 8, impact 3, unblocks 5)
- Acceptance criteria: Run through Claude Code + Codex + third agent in separate worktrees, hash outputs, surface disagreements
- Falsifier: orca cannot isolate worktrees or expose outputs for hashing
- **NO code dependencies** — it's a local worktree evaluation, not dependent on registry, intake, or landing order

**Action:** Once GitHub PAT approved, execute Q-ORCA-01
- Set up orca evaluation environment
- Run test packet through Claude Code substrate
- Run through Codex substrate (requires orca + Codex setup)
- Run through third agent substrate
- Hash each output, append to optimizer_events.jsonl
- Document DISPUTED callouts
- **Owner:** Z1 (this practice)
- **Timeline:** Immediate (upon GitHub PAT)
- **Blocker:** GitHub PAT only (Z2 decision)

---

### Goal 4: Resolve Specific Blockers ⚠ MIXED

**Blocker 1: GitHub PAT** ❌ Z2-GATED
- **Action:** Escalate to Z2 for decision (~5 min)
- **Impact:** Unblocks Q-ORCA-01 execution + all other landing-order work
- **Owner:** Z2
- **Timeline:** Z2 turnaround time
- **Via mesh:** mesh-support can prioritize in Z2 escalation queue

**Blocker 2: IC-030 Drift** ✓ Z1-RESOLVABLE
- **Action:** Execute Q-IC030-REPIN-01 (already READY in queue)
- **Impact:** Resolves registry pin mismatch; enables landing-order registry work
- **Owner:** Z1 (this practice)
- **Timeline:** Immediate
- **No dependency:** Can run in parallel with GitHub PAT request

**Blocker 3: IC-SCOPE-05** ⚠ HYBRID (NOT blocking Q-ORCA-01)
- **Z1 part:** Design intake schema, commit it, run end-to-end test (no Z2 gate)
- **Z2 part:** Ratify R-001.md with hash
- **Impact:** Unblocks intake-post step (step 8), NOT Q-ORCA-01 (which is local eval)
- **Action:** Z1 can begin schema design; escalate ratification need to Z2
- **Owner:** Z1 + Z2
- **Timeline:** Async (not on critical path for Q-ORCA-01)

**Blocker 4: TLA_TOOLS_SHA256** ❌ Z2-GATED (NOT blocking Q-ORCA-01)
- **Action:** Escalate to Z2 to compute SHA256 of tla2tools.jar v1.8.0 and set in GitHub
- **Impact:** Unblocks research-intake workflow (step 4 of landing order)
- **Owner:** Z2
- **Timeline:** Z2 decision (~5 min)
- **Note:** Only needed for research-intake.yml CI, not Q-ORCA-01

**Blocker 5: z2_budget_p2** ❌ Z2-GATED (Governance constraint, not hard blocker)
- **Action:** Escalate to Z2 to decide Phase 2 envelope size (~5 min)
- **Impact:** Sets regulatory ceiling for Phase 2 work; affects queue regulator
- **Owner:** Z2
- **Timeline:** Z2 decision
- **Note:** Governance constant; doesn't directly block Q-ORCA-01, but required for queue advancement

---

### Goal 5: Mesh Coordination ✓ STRATEGY DEFINED
**Status:** Contact plan ready  
**Finding:**
- Mesh-support can unblock 2–3 blockers (GitHub PAT 70%, IC-SCOPE-05 75%)
- Mesh-support can escalate TLA/budget to Z2 with context
- humanaios can resolve IC-030 if needed

**Action:** Load /cortex-mailbox-send and draft proposal to mesh-support
- Lead with GitHub PAT (removes access blocker)
- Bundle IC-SCOPE-05 (governance question)
- Ask Z2 escalation protocol for TLA_TOOLS_SHA256 + z2_budget_p2
- **Owner:** Z1 (this practice)
- **Timeline:** Immediate (parallel with other actions)
- **Expected outcome:** 2–3 blockers directly resolved + proper escalation routing

---

## Implementation Roadmap

### **Immediate (Next 1–2 hours)**

| Track | Action | Owner | Timeline | Blocker |
|-------|--------|-------|----------|---------|
| **Mesh coordination** | Draft `/cortex-mailbox-send` to mesh-support (GitHub PAT + IC-SCOPE-05) | Z1 | Now | None |
| **IC-030 drift** | Execute Q-IC030-REPIN-01 | Z1 | Now | None |
| **Inbox drop prep** | Locate + stage 23 files, verify hashes | Z1 | Now | None |
| **Z2 escalation** | Ask mesh-support to route GitHub PAT + TLA/budget decisions to Z2 | Z1 via mesh | Now | None |

### **Blocked on Z2 Decision (~5 min)**

| Item | Owner | Blocker | Timeline |
|------|-------|---------|----------|
| **GitHub PAT** | Z2 | Z2 decision | ~5 min |
| **TLA_TOOLS_SHA256** | Z2 | Z2 decision | ~5 min |
| **z2_budget_p2** | Z2 | Z2 decision | ~5 min |

### **Once GitHub PAT Approved**

| Action | Owner | Timeline |
|--------|-------|----------|
| Execute Q-ORCA-01 | Z1 | 30–60 min (depending on orca setup) |

### **Parallel/Async (Can happen anytime)**

| Action | Owner | Timeline | Blocker |
|--------|-------|----------|---------|
| IC-SCOPE-05: design intake schema | Z1 | 1–2 hours | None (Z2 ratification is later) |
| Landing order steps 1–3 (CODEOWNERS, teams) | Z1 | Post-PAT | GitHub PAT |

---

## Risk & Mitigation

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Z2 turnaround delayed beyond 5 min estimate | MEDIUM | Mesh-support escalation makes it high-priority |
| Inbox files cannot be staged (missing or inaccessible) | LOW | Files are listed in manifest; likely in sync queue or z1-inbox origin |
| Orca evaluation uncovers UNexpected dependencies | LOW | Falsifier is clear; accepted criteria documented |
| IC-SCOPE-05 schema design has Z2 disputes | LOW | Schema is design-phase; iterate on feedback |

---

## Conclusion

**All five goals are actionable NOW:**

✅ **Goal 1** — IC-030 drift: Execute Q-IC030-REPIN-01  
✅ **Goal 2** — Inbox drop: Locate & stage files  
✅ **Goal 3** — Q-ORCA-01: Ready to execute (GitHub PAT is only blocker)  
⚠ **Goal 4** — Blockers: 2–3 resolvable by Z1, 3–4 need Z2 decision  
✅ **Goal 5** — Mesh coordination: Contact strategy ready

**Critical path to completion:**
1. Mesh-support contact → GitHub PAT escalation to Z2
2. Z2 approves GitHub PAT (~5 min)
3. Z1 executes Q-ORCA-01
4. Parallel: Q-IC030-REPIN-01, inbox staging, IC-SCOPE-05 schema design

**Next step:** Open `/cortex-mailbox-send` and contact mesh-support.

---

**Prepared by:** empirica-outreach (Claude Code)  
**Consolidation transaction:** d35e33a4-65cf-4fe7-a846-6cb65f940de8 (in progress)  
**Artifacts:** agent assessments (mesh coordination, blocker resolution)
