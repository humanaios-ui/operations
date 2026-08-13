# Activation Map — Tools & Skills Live Status

**Date:** 2026-07-14  
**Phase:** Week 3 STANDARDIZE  
**Status:** Week 1 inventory mapped to activation points

---

## Quick Reference

| Resource | Type | Zone | Status | Activation |
|----------|------|------|--------|------------|
| acat_observability_bridge.py | Tool | 1 | ⏳ Testable | Embedded in acat_corpus_session.py |
| acat_corpus_session.py | Tool | 1 | ✅ Functional* | Invoked by /acat-corpus-session skill |
| acat_rec2_session_init.py | Hook | 1 | ⏳ Ready | autonomy:SessionStart hook |
| acat_rec3_preflight_reminder.py | Hook | 1 | ⏳ Ready | autonomy:UserPromptSubmit hook |
| acat_rec4_postflight_verifier.py | Hook | 1 | 🔴 Blocked** | autonomy:SessionEnd hook |
| /acat-corpus-session | Skill | 1 | ⏳ Defined*** | Not registered; manual load |
| /empirica-constitution | Skill | 2 | ✅ Live | Active in system prompt |
| /cortex-mailbox-send | Skill | 2 | ✅ Live | Cortex mesh layer |
| /cortex-mailbox-poll | Skill | 2 | ✅ Live | Cortex mesh layer |
| carly-onboarding-interview | Skill | 1 | ⚠️ Active | First-session trigger (manual) |

**Legend:**
- *: Bug fixed in Week 2; ready for testing
- **: Blocked on verifier agent + transcript API (W4-5)
- ***: Defined but not registered in skill registry

---

## TOOLS — Activation Points

### 1. acat_observability_bridge.py

**Zone:** 1 (draft)  
**Status:** ⏳ Testable (code ready, not yet validated in live session)  
**Purpose:** Real-time behavioral calibration detection

**Activation Path:**
```
Imported by:
  └─ tools/acat_corpus_session.py (line 23)
      └─ Invoked by /acat-corpus-session skill (Step 3: Exercise interaction)
          └─ Called via ACATCorpusSession.add_exchange() (line 139)
```

**Integration Points:**
- `ACATCorpusSession.set_p1_scores()` initializes observability log (line 113-117)
- `ACATCorpusSession.add_exchange()` processes exchanges through bridge (line 138-139)
- `ACATCorpusSession.set_p3_scores()` computes observability summary (line 157-169)

**Activation Status:**
- Code: ✅ Implemented
- Tests: ❌ Stub only (10% coverage)
- Integration: ⏳ Ready (awaiting acat_corpus_session testing)
- Production: ❌ Not deployed

**Health Check:**
```bash
python3 tools/acat_observability_bridge.py
# Expected: Prints observability summary + statusline segment
```

---

### 2. acat_corpus_session.py

**Zone:** 1 (draft → testable after bug fix)  
**Status:** ✅ Functional (bug fixed Week 2)  
**Purpose:** Complete ACAT P1→P3→verifier session harness

**Activation Path:**
```
Imported by:
  └─ /acat-corpus-session skill (invoked via LoadSkill)
      └─ Can be called manually: python3 tools/acat_corpus_session.py
```

**Integration Points:**
- Step 1 (Setup): `ACATCorpusSession.__init__()` creates session
- Step 2 (P1): `ACATCorpusSession.set_p1_scores()` records baseline
- Step 3 (Exercise): `ACATCorpusSession.add_exchange()` processes interactions
- Step 4 (P3): `ACATCorpusSession.set_p3_scores()` records post-session
- Step 5 (Verifier): Calls external verifier (stubbed)
- Step 6 (Report): `ACATCorpusSession.generate_cross_instrument_finding()` produces output

**Activation Status:**
- Code: ✅ Implemented (bug fixed)
- Tests: ❌ Stub only (10% coverage)
- Integration: ⏳ Ready (awaiting skill registration)
- Production: ❌ Not deployed

**Health Check:**
```bash
python3 tools/acat_corpus_session.py
# Expected: Prints cross-instrument finding + learning index
```

---

### 3. acat_rec2_session_init.py

**Zone:** 1 (draft → testable)  
**Status:** ⏳ Ready for autonomy integration  
**Purpose:** Auto-create `.empirica/acat_current_session.json` at session start

**Activation Path:**
```
Activated by:
  └─ empirica-autonomy:SessionStart hook (startup|resume)
      └─ Calls hook_handler(event_data)
          └─ Creates acat_current_session.json in .empirica/
```

**Hook Configuration (for autonomy):**
```yaml
hooks:
  - event: SessionStart
    trigger: startup|resume
    handler: hooks/acat_rec2_session_init.py::hook_handler
    priority: early  # Run before other hooks
```

**Integration Status:**
- Code: ✅ Implemented
- Hook: ❌ Not integrated (awaiting autonomy practice)
- Tests: ❌ Stub only
- Production: ❌ Not deployed

**Manual Test:**
```bash
python3 hooks/acat_rec2_session_init.py
# Expected: Creates .empirica/acat_current_session.json with blank state
```

---

### 4. acat_rec3_preflight_reminder.py

**Zone:** 1 (draft → testable)  
**Status:** ⏳ Ready for autonomy integration  
**Purpose:** Inject ACAT P1 reminder into PREFLIGHT if not yet scored

**Activation Path:**
```
Activated by:
  └─ empirica-autonomy:UserPromptSubmit hook (pre-PREFLIGHT gate)
      └─ Calls hook_handler(event_data)
          └─ Injects reminder into PREFLIGHT payload
              └─ Reminder appears in PREFLIGHT output
```

**Hook Configuration (for autonomy):**
```yaml
hooks:
  - event: UserPromptSubmit
    trigger: detected_command == "empirica preflight-submit"
    handler: hooks/acat_rec3_preflight_reminder.py::hook_handler
    priority: normal
```

**Integration Status:**
- Code: ✅ Implemented
- Hook: ❌ Not integrated (awaiting autonomy practice)
- Tests: ❌ Stub only
- Production: ❌ Not deployed

**Manual Test:**
```bash
python3 hooks/acat_rec3_preflight_reminder.py
# Expected: Prints P1 reminder injection payload
```

---

### 5. acat_rec4_postflight_verifier.py

**Zone:** 1 (draft)  
**Status:** 🔴 BLOCKED on verifier agent + transcript API  
**Purpose:** Auto-run verifier agent at POSTFLIGHT if P1+P3 captured

**Activation Path:**
```
Would be activated by:
  └─ empirica-autonomy:SessionEnd hook (post-POSTFLIGHT)
      └─ Calls VerifierAgent.execute()
          └─ Runs verifier agent (CURRENTLY STUBBED)
              └─ Stores verifier_scores in session state
```

**Hook Configuration (for autonomy):**
```yaml
hooks:
  - event: SessionEnd
    trigger: after POSTFLIGHT submission
    handler: hooks/acat_rec4_postflight_verifier.py::hook_handler
    priority: normal
```

**Blockers:**
1. **Verifier agent is stubbed** (lines 118-148)
   - Returns mock scores `{truth: 72, service: 75, ...}`
   - Needs real verifier agent that scores transcript

2. **Session transcript API missing** (lines 99-111)
   - `get_session_transcript()` returns placeholder
   - Needs way to retrieve session content from empirica

**Timeline:** Weeks 4-5 (after dependencies resolved)

**Status:**
- Code: ⚠️ Implemented (stubs)
- Hook: ❌ Not integrated
- Blocking items: 2 (verifier, transcript API)
- Production: ❌ Not deployable

---

## SKILLS — Activation Status

### 1. /acat-corpus-session (Local)

**Zone:** 1 (draft)  
**Status:** ⏳ Defined but not registered  
**Type:** Assessment tool / Workflow harness  
**Location:** `skills/acat-corpus-session/SKILL.md`

**Registration Status:**
- Skill definition: ✅ Complete (SKILL.md exists)
- Trigger phrases: ✅ Documented (`/acat-corpus-session`, "run ACAT corpus session")
- Implementation: ⏳ Functional (bug fixed in Week 2)
- Registry entry: ❌ Not registered (no activation)
- Discoverability: ❌ Not discoverable via `/` trigger

**Manual Invocation (current):**
```bash
# User must know the skill exists and manually load it
# Loads via: /acat-corpus-session or explicit skill load
```

**Activation Steps (Week 3+):**
1. Register skill in empirica skill registry
2. Configure trigger phrases
3. Set Zone 1 status
4. Test manual invocation
5. Proceed to Zone 2 after testing

**Dependencies:**
- `tools/acat_corpus_session.py` ✅
- `tools/acat_observability_bridge.py` ✅
- `tools/acat_rec4_postflight_verifier.py` 🔴 (blocked)

**Ready for activation:** Partial (works without Rec 4, but less complete)

---

### 2. /empirica-constitution (External, Zone 2)

**Zone:** 2 (ratified)  
**Status:** ✅ LIVE  
**Type:** Reference / Governance framework  
**Location:** External (empirica plugin)

**Activation Status:**
- Registry: ✅ Registered
- Triggers: ✅ Active (`/empirica-constitution`, "practice model", "mesh discipline")
- Discovery: ✅ Discoverable
- Production: ✅ Live

**Integration:** Already integrated into empirica system prompt

---

### 3. /cortex-mailbox-send (External, Zone 2)

**Zone:** 2 (ratified)  
**Status:** ✅ LIVE  
**Type:** Mesh communication / Workflow utility  
**Location:** External (cortex MCP layer)

**Activation Status:**
- Registry: ✅ Registered
- Triggers: ✅ Active (for sending messages in mesh)
- Discovery: ✅ Discoverable
- Production: ✅ Live

**Integration:** Part of cortex mesh layer (see empirica-cortex-prompt.md)

---

### 4. /cortex-mailbox-poll (External, Zone 2)

**Zone:** 2 (ratified)  
**Status:** ✅ LIVE  
**Type:** Mesh communication / Listener  
**Location:** External (cortex MCP layer)

**Activation Status:**
- Registry: ✅ Registered
- Triggers: ✅ Active (automatic on inbox events)
- Discovery: ✅ Discoverable
- Production: ✅ Live

**Integration:** Part of cortex mesh layer

---

### 5. carly-onboarding-interview (Local, Zone 1)

**Zone:** 1 (draft → clarified)  
**Status:** ⚠️ Active (clarified Week 2)  
**Type:** Onboarding workflow / Interview protocol  
**Location:** `skills/carly-onboarding-interview.md`

**Purpose:** First-session onboarding for Carly's Admiral seat. Sets up foundation practices, epistemic profiles, demonstration harnesses.

**Trigger:** Manual invocation (first session only, or when re-onboarding)
- When: Carly's first session on empirica-foundation-evaluator seat
- How: User or Claude Code initiates onboarding flow
- Status: Not auto-triggered (requires explicit invocation)

**Activation Status:**
- Skill definition: ✅ Complete (well-documented protocol)
- Trigger: ⚠️ Manual only (not auto)
- Registry entry: ❓ Unclear (may be registered already)
- Discoverability: ⚠️ Partial (works if user knows about it)
- Production: ✅ Active (used during onboarding)

**Next Step (Week 3):**
- Clarify trigger mechanism (SessionStart event? Manual invocation?)
- Add to SKILLS_MANIFEST.md with status
- Register in skill registry if not already done

---

## Activation Roadmap

### Week 3 (STANDARDIZE) — No new activations

**Tasks:**
- Document this activation map
- Clarify carly-onboarding-interview trigger
- Prepare registration checklist for Week 4

**Status:** ⏳ Waiting on standards templates + skill registry documentation

### Week 4 (SUSTAIN Phase 1) — Begin activations

**Planned activations:**
- [ ] Register /acat-corpus-session in skill registry (Zone 1)
- [ ] Test /acat-corpus-session manual invocation
- [ ] Integrate Rec 2 + Rec 3 hooks into autonomy (requires autonomy practice)

**Blocked activations:**
- [ ] Rec 4 hook integration (depends on verifier agent + transcript API)

### Week 5+ (IMPLEMENTATION) — Production deployments

**Zone 1→2 transitions:**
- acat_observability_bridge.py (test coverage + refinements)
- acat_corpus_session.py (integration testing)
- /acat-corpus-session skill (live testing)

**Zone 2→3 transitions:**
- Once live testing passes + ACAT assessments complete

---

## Health Check Procedure

**Weekly (during Weeks 3-12):**

Run this to verify all active tools/skills are operable:

```bash
# Test each tool's basic functionality
echo "=== Tool Health Checks ==="

echo "1. acat_observability_bridge:"
python3 tools/acat_observability_bridge.py > /tmp/obs_check.json && echo "✅ OK" || echo "❌ FAILED"

echo "2. acat_corpus_session:"
python3 tools/acat_corpus_session.py > /tmp/corpus_check.json && echo "✅ OK" || echo "❌ FAILED"

echo "3. acat_rec2_session_init:"
python3 hooks/acat_rec2_session_init.py > /tmp/rec2_check.json && echo "✅ OK" || echo "❌ FAILED"

echo "4. acat_rec3_preflight_reminder:"
python3 hooks/acat_rec3_preflight_reminder.py > /tmp/rec3_check.json && echo "✅ OK" || echo "❌ FAILED"

echo "5. acat_rec4_postflight_verifier:"
python3 hooks/acat_rec4_postflight_verifier.py > /tmp/rec4_check.json && echo "✅ OK" || echo "❌ FAILED"

echo ""
echo "=== Skill Discovery ==="
# Once registered: Check that /acat-corpus-session is discoverable
# Command would depend on skill registry API
```

---

## Integration Checklist (For autonomy practice)

**When autonomy is ready to integrate Rec 2/3 hooks:**

- [ ] Review hook specifications (ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md)
- [ ] Copy hooks to autonomy project
- [ ] Add SessionStart hook for Rec 2 (priority: early)
- [ ] Add UserPromptSubmit hook for Rec 3 (priority: normal)
- [ ] Test hooks in isolation
- [ ] Test hooks in integrated flow
- [ ] Document in autonomy's operations/ACTIVATION_MAP.md

**Rec 4 (verifier hook) — deferred to Weeks 4-5 pending dependencies**

---

## Status Summary

| Category | Count | Ready | Blocked | Timeline |
|----------|-------|-------|---------|----------|
| Tools | 5 | 4 | 1 | Rec 4 deferred to W4-5 |
| Skills (local) | 2 | 1 | 1 | /acat-corpus-session ready |
| Skills (external) | 2 | 2 | 0 | Already active |
| Hooks | 3 | 2 | 1 | Rec 2+3 ready for autonomy |
| **TOTAL** | **12** | **9** | **3** | **75% ready** |

---

**Map Status:** Week 3 STANDARDIZE complete  
**Next Review:** Week 4 (SUSTAIN phase)  
**Last Updated:** 2026-07-14

