# Skill Registry — Local Skills Registration

**Version:** 1.0  
**Effective:** Week 4 Phase 2 (2026-07-14)  
**Scope:** empirica-foundation.carly.empirica-foundation-evaluator

---

## Active Skill Registration

### 1. /acat-corpus-session

**Status:** ✅ REGISTERED (Week 4 Phase 2)

**Metadata:**
- **Canonical name:** `/acat-corpus-session`
- **Zone:** 1 (Testable draft)
- **Version:** 0.2.0
- **Location:** `skills/acat-corpus-session/SKILL.md`
- **Type:** Assessment tool / Workflow harness
- **Activation:** Manual invoke (not yet auto-triggered)
- **Registered:** 2026-07-14 by evaluator-foundation-evaluator

**Trigger Phrases:**
- `/acat-corpus-session`
- "run ACAT corpus session"
- "start corpus evaluation"
- "acat-corpus-session"

**Purpose:**
Walk through complete ACAT P1→exercise→P3→verifier session using TOP curriculum exercise. Produces: session state file, observability trace, corpus entry, cross-instrument finding.

**Dependencies:**
- `tools/acat_corpus_session.py` ✅
- `tools/acat_observability_bridge.py` ✅
- Hook Rec 4 (verifier) 🔴 BLOCKED on verifier agent implementation

**Integration Points:**
- Calls `tools/acat_corpus_session.py::ACATCorpusSession`
- Embeds `tools/acat_observability_bridge.py` via corpus session
- Future: Will integrate with verifier agent (Rec 4)

**Status Indicators:**
- Skill definition: ✅ Complete (SKILL.md)
- Trigger phrases: ✅ Documented
- Implementation: ✅ Functional (bug fixed Week 2)
- Tests: ⏳ Stub coverage (10%)
- Registration: ✅ Complete (Week 4 Phase 2)
- Production deployment: ⏳ Awaiting Zone 2 transition

**Activation Instructions:**
```bash
# Manual invocation (current, Zone 1)
Load skill: /acat-corpus-session

# Expected workflow
Step 1: Setup (exercise path, student persona, agent name)
Step 2: P1 scoring (baseline self-assessment)
Step 3: Exercise interaction (capture exchanges, real-time observability)
Step 4: P3 scoring (post-session assessment)
Step 5: Verifier (independent cross-check) — currently stubbed
Step 6: Report (generate cross-instrument finding)
```

**Known Limitations:**
- Verifier agent (Step 5) is stubbed — returns mock scores
- Session transcript API missing — needed for real verifier
- No integration with auto-trigger system yet (manual only)
- Test coverage 10% (stubs) — target 70%+

**Timeline to Zone 2:**
- Week 4 Phase 2: Registration ✅
- Week 5: Verifier agent implementation (external dependency)
- Week 5+: Integration testing + ACAT P1→P3 assessment
- Week 6+: Zone 2 ratification (if all tests pass + verifier complete)

---

## External Skills (Already Registered)

### 2. /empirica-constitution
- Zone: 2 (Ratified)
- Status: LIVE (already active)
- Registration: External (empirica plugin)

### 3. /cortex-mailbox-send
- Zone: 2 (Ratified)
- Status: LIVE (already active)
- Registration: External (cortex MCP layer)

### 4. /cortex-mailbox-poll
- Zone: 2 (Ratified)
- Status: LIVE (already active)
- Registration: External (cortex MCP layer)

---

## Legacy Skills (Clarified)

### 5. carly-onboarding-interview
- Zone: 1 (Draft)
- Status: ACTIVE (first-session onboarding protocol)
- Registration: Manual trigger (not auto-triggered)
- Purpose: Admiral seat onboarding
- Activation: First session or re-onboarding
- Updated: Week 2 clarification (moved from Archive to Active)

---

## Registry Operations

### Adding a Skill

1. Create skill definition in `skills/<skill_name>/SKILL.md` (6-section format)
2. Add entry to SKILL_REGISTRY.md with metadata
3. Test skill functionality (manual invocation)
4. Add to SKILLS_MANIFEST.md (activation matrix)
5. Commit with message: "Register skill: <name>, Zone 1"
6. Await Zone 2 transition (testing + peer review)

### Updating Registration

When skill status changes:
1. Update SKILL_REGISTRY.md (this file)
2. Update SKILLS_MANIFEST.md (if activation changes)
3. Update ACTIVATION_MAP.md (if integration points change)
4. Commit with message: "Update skill registration: <name>, <change>"

### Removing Registration

1. Mark skill as DEPRECATED in SKILL_REGISTRY.md
2. Archive skill to `archive/<skill_name>/`
3. Remove from ACTIVATION_MAP.md
4. Update DEPRECATION_LOG.md
5. Keep in SKILLS_MANIFEST.md with status "Archived"
6. Commit with message: "Deprecate skill: <name>, archived to archive/"

---

## Registration Metadata Template

For each registered skill:

```markdown
### N. /<skill-name>

**Status:** [ACTIVE|DEPRECATED|BLOCKED]

**Metadata:**
- **Canonical name:** `/<skill-name>`
- **Zone:** [0|1|2|3]
- **Version:** X.Y.Z
- **Location:** `skills/<skill-name>/SKILL.md`
- **Type:** [Assessment tool|Workflow harness|Utility|Reference]
- **Activation:** [Manual invoke|Auto-trigger|Channel-scoped]
- **Registered:** YYYY-MM-DD by <practice>

**Trigger Phrases:**
- List of trigger phrases (3-5)

**Purpose:**
One-line purpose statement

**Dependencies:**
- List of tools/skills/APIs this depends on
- Show status: ✅ ready, 🔴 blocked

**Integration Points:**
- Where in the system this skill is used
- What it calls
- What calls it

**Status Indicators:**
- Skill definition: ✅/⏳/❌
- Trigger phrases: ✅/⏳/❌
- Implementation: ✅/⏳/❌
- Tests: ✅/⏳/❌
- Registration: ✅/⏳/❌
- Production deployment: ✅/⏳/❌

**Activation Instructions:**
- How to invoke this skill
- Expected workflow/output

**Known Limitations:**
- List of what doesn't work yet
- Timeline to fix

**Timeline to Zone 2:**
- When each milestone is expected
```

---

## Summary

| Skill | Zone | Status | Registered | Ready for Zone 2? |
|-------|------|--------|-----------|-----------------|
| /acat-corpus-session | 1 | ACTIVE | ✅ Week 4 P2 | ⏳ Awaiting verifier agent (W5) |
| /empirica-constitution | 2 | LIVE | ✅ External | ✅ Already live |
| /cortex-mailbox-send | 2 | LIVE | ✅ External | ✅ Already live |
| /cortex-mailbox-poll | 2 | LIVE | ✅ External | ✅ Already live |
| carly-onboarding-interview | 1 | ACTIVE | ⚠️ Manual | ⚠️ Needs formal registration |

---

**Registry Status:** Week 4 Phase 2 update complete  
**Next Review:** Week 5 (post-Zone 1→2 testing)

