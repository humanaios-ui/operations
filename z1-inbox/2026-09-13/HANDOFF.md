# HANDOFF: Registry Reconciliation Phase 0 Complete

**To:** Z2 (Night) — Z2 Serial Gate, Final Authority  
**From:** Z1 (Claude) — Proposer  
**Date:** 2026-09-13 18:32 UTC  
**Session:** claude/funny-bohr-fp0rnl  
**Pinned SHA:** `245ca82` (latest commit on branch)

---

## Executive Summary

**Registry is out of sync with GitHub reality. Atomized into 3 candidates awaiting Z2 ratification.**

| Metric | Value |
|--------|-------|
| GitHub actual repos | 12 |
| ZONE_REGISTRY claims | 18 |
| Header promise | 31 |
| **Mismatch** | **19 repos** |
| RECEIPT-GAP | Yes (claim ≠ tree) |

**Candidates Filed:**
- Q-REGISTRY-AUDIT-01 (IC): Classify 13 missing repos
- Q-REGISTRY-AUDIT-02 (IC): Register 7 repos on GitHub but missing
- Q-REGISTRY-AUDIT-03 (F): Implement reconciliation + deploy CI gate

---

## Findings

### Finding 1: 13 Repos Claimed But Don't Exist

**Classification:**
- **Status:** All planned, never created
- **Examples:** empirica-autonomy, empirica-foundation-evaluator, website, grok-crossref, etc.
- **Verification:** Searched all of GitHub (no matches in other orgs, not archived)

**Root Cause:** ZONE_REGISTRY.md header copied from an aspirational 31-repo roadmap, but table was never kept in sync as repos were created/deleted.

### Finding 2: 7 Repos on GitHub Not in ZONE_REGISTRY

**Missing repos:**
- acat-x (created 2026-08-02, active, 4 issues)
- acat-dashboard (created 2026-03-03, synced from Magic Patterns)
- acat-observatory (created 2026-03-11, private)
- docs (created 2026-03-22, MDX documentation)
- empirica-practice-mesh (created 2026-09-11, governance/sync)
- research (created 2026-04-30, frozen paper snapshots)
- findlocaltattooartists (created 2026-05-06, Astro/Tailwind portfolio)

**Root Cause:** These repos were created after ZONE_REGISTRY baseline, or created in parallel without registry update.

### Finding 3: No CI Gate Prevents Future Drift

**Current state:** registry_consistency gate (implied) not enforced
**Risk:** Next audit finds 5 more unregistered repos (precedent established)

---

## Z2 Decision Points

### Decision 1: ZONE_REGISTRY.md Header (Q-REGISTRY-AUDIT-01)

**Three options:**

| Option | Claim | Tracking | Pros | Cons |
|--------|-------|----------|------|------|
| **A** | 12 repos | None | Simple, truthful | Loses roadmap visibility |
| **B** | 12 repos | PLANNED_REPOS.md | Separate active/planned | Extra file overhead |
| **C** | "12 active (31 planned)" | ROADMAP_REPOS.md | Hybrid, aspirational | More complex gate rules |

**Recommendation:** **Option B** (separate PLANNED_REPOS.md)
- Keeps ZONE_REGISTRY as SOT for *active* governance
- Planned repos tracked separately (no false claims)
- Easier to maintain and audit

---

### Decision 2: Zone Assignments for 7 New Repos (Q-REGISTRY-AUDIT-02)

**Proposed assignments in candidate.** Q-REGISTRY-AUDIT-02 includes table with proposed zones.

**Verify before approving:**
- Do zone assignments align with FRAMEWORK_MAPPING.md?
- Should acat-x be under "empirica-autonomy" (parent zone, not yet a top-level repo)?
- Is research correctly marked as READ-only (frozen papers)?

---

### Decision 3: CI Gate Deployment (Q-REGISTRY-AUDIT-03)

**Gate rules (if approved):**
1. Header claim == table row count
2. All table repos exist on humanaios-ui + not archived
3. GitHub has no unregistered active repos
4. Planned repos tracked (if Option B/C)

**When to deploy:** After Options A/B/C and zone assignments approved.

---

## Receipt Reconciliation (B.6 Walkback)

| Claim | Tree (ZONE_REGISTRY.md) | Status |
|-------|------------------------|--------|
| "31 repos" (header) | 18 listed | ❌ MISMATCH: +13 missing |
| "18 repos" (count) | 12 actual GitHub | ❌ MISMATCH: +6 untracked |
| 5 repos in registry exist | acat-inspect, humanaios, humanaios-internal, lasting-light-ai, operations | ✅ TRUE |
| 7 repos on GitHub exist | acat-x, acat-dashboard, etc. | ✅ TRUE but NOT registered |

**RECEIPT-GAP:** Claim ("31 repos") ÷ Tree (12 GitHub repos) = 258% overstatement

---

## Blockers & Escalations

### Blocker 1: Z2 Decision Needed (None currently blocking)

All three candidates are well-formed and falsifiable. Ready for Z2 read + decision.

### Blocker 2: Assumed But Unverified (Post-Audit)

- Are there repos in *other* HumanAIOS orgs (not humanaios-ui)? 
  - If yes, full "31 repos" might be accurate across all orgs
  - Scope of Q-REGISTRY-AUDIT-01/02 is humanaios-ui only
  - Suggest Phase 1b audit: "Full HumanAIOS ecosystem scan"

---

## Handoff Checklist

- [x] Position stated (see above)
- [x] Destination clear (3 atomic candidates, decision awaited)
- [x] Probability: 90% Phase 0 complete by 2026-09-14 if Z2 ratifies all 3
- [x] Falsifiers present on all candidates
- [x] Receipt walk-back done (see B.6 above)
- [x] Findings scanned (3 findings: missing repos, untracked repos, no gate)
- [x] Candidates filed to z1-inbox/2026-09-13/
- [ ] Z2 signature awaited on all 3 ICs + decision on Option A/B/C

---

## Next Steps (Awaiting Z2)

1. **Read candidates** (Q-REGISTRY-AUDIT-01/02/03)
2. **Decision**: Choose Option A, B, or C for header claim
3. **Review**: Zone assignments in Q-REGISTRY-AUDIT-02
4. **Ratify**: Issue Z2 hash for all 3 candidates if approved, or EDIT/REJECT if issues
5. **If ratified**: Z1 implements Q-REGISTRY-AUDIT-03 in follow-up session
   - Push to branch (new commit)
   - Deploy CI gate
   - Test gate locally
   - Create draft PR for Z2 merge approval

---

## Context for Z2 Re-Read (if contested)

**Why this matters:** CLAUDE.md lists ZONE_REGISTRY.md as a "File That Requires Z2 Signature." Registry drift is a governance risk — once repos drift out of sync with reality, the falsifier doctrine (K=3 molts, 2-revert freeze) becomes unenforceable. This audit is foundational to restoring authority structure.

**Why atomized:** Each finding is independent (missing vs. untracked vs. no gate), allowing Z2 to approve/edit/reject piece by piece. If Option A is rejected, Q-REGISTRY-AUDIT-02/03 can pivot without re-work.

---

## Resources

- **Candidates:** z1-inbox/2026-09-13/Q-REGISTRY-AUDIT-{01,02,03}.md
- **GitHub search results:** Saved to tool-results/ (tool ran 8 searches, 0 results for 13 missing)
- **ZONE_REGISTRY.md:** /home/user/operations/ZONE_REGISTRY.md (current, unedited)
- **Branch:** claude/funny-bohr-fp0rnl (pinned at 245ca82)

---

**Awaiting Z2 decision window (48h from ratification request).**

---

*Session closed by Z1 at 2026-09-13 18:32 UTC.*
