# Autonomy Hook Integration Coordination

**Version:** 1.0  
**Effective:** Week 4 Phase 2 (2026-07-14)  
**Purpose:** Coordinate integration of Rec 2/3/4 hooks with autonomy practice  
**Status:** Ready for autonomy practice review + implementation

---

## Overview

Three ACAT integration hooks (Rec 2, 3, 4) need to be integrated into empirica-autonomy practice:

| Hook | Purpose | Trigger | Owner | Status |
|------|---------|---------|-------|--------|
| Rec 2 | Auto-create session state | SessionStart (startup\|resume) | autonomy | Ready for integration |
| Rec 3 | Inject P1 reminder | UserPromptSubmit (pre-PREFLIGHT) | autonomy | Ready for integration |
| Rec 4 | Run verifier | SessionEnd (post-POSTFLIGHT) | autonomy | Blocked on verifier agent |

---

## Integration Requirements

### For autonomy practice:

1. **Copy hook files to autonomy project**
   ```
   evaluator: /Users/andersonfamily/practices/empirica-foundation-evaluator/hooks/
   autonomy: /Users/andersonfamily/practices/empirica-autonomy/hooks/
   
   Files:
   - acat_rec2_session_init.py
   - acat_rec3_preflight_reminder.py
   - acat_rec4_postflight_verifier.py (note: verifier is stubbed)
   ```

2. **Register hooks in autonomy's hook configuration**
   - See hook configuration examples below

3. **Test hook execution with mock events**
   - See test procedures below

4. **Integrate with autonomy's event system**
   - Verify hooks fire at correct time
   - Verify hook output is captured/stored

---

## Hook Integration Specifications

### Hook Rec 2: Auto-create Session State

**Event:** SessionStart  
**Trigger:** startup | resume  
**Priority:** early (before other session hooks)

**Hook Configuration (for autonomy's setup):**
```yaml
hooks:
  - id: "acat-rec2-session-init"
    event: "SessionStart"
    trigger: "startup|resume"
    handler: "hooks/acat_rec2_session_init.py::hook_handler"
    priority: "early"
    enabled: true
    description: "Auto-create ACAT session state at session start"
```

**Handler Signature:**
```python
def hook_handler(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        event_data: {
            "event": "SessionStart",
            "trigger": "startup" | "resume",
            "project_root": "/path/to/project",
            ...
        }
    
    Returns:
        {
            "ok": bool,
            "action": "created" | "skipped" | "failed",
            "path": str,
            "acat_session_id": str (if created),
            "error": str (if failed)
        }
    """
```

**Expected Output:**
```json
{
    "ok": true,
    "action": "created",
    "path": "/path/to/project/.empirica/acat_current_session.json",
    "acat_session_id": "uuid-here"
}
```

**Test Procedure:**
```python
# Autonomy practice test
event = {
    "event": "SessionStart",
    "trigger": "startup",
    "project_root": "/tmp/test_project"
}
result = hook_handler(event)
assert result["ok"] == True
assert result["action"] in ["created", "skipped"]
assert Path(result["path"]).exists()
```

---

### Hook Rec 3: Inject P1 Reminder

**Event:** UserPromptSubmit  
**Trigger:** Detected command = "empirica preflight-submit"  
**Priority:** normal

**Hook Configuration (for autonomy's setup):**
```yaml
hooks:
  - id: "acat-rec3-p1-reminder"
    event: "UserPromptSubmit"
    trigger: 'detected_command.startswith("empirica preflight-submit")'
    handler: "hooks/acat_rec3_preflight_reminder.py::hook_handler"
    priority: "normal"
    enabled: true
    description: "Inject ACAT P1 reminder into PREFLIGHT if not yet scored"
```

**Handler Signature:**
```python
def hook_handler(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        event_data: {
            "event": "UserPromptSubmit",
            "detected_command": "empirica preflight-submit",
            "preflight_payload": {...},
            "project_root": "/path/to/project",
            ...
        }
    
    Returns:
        {
            "ok": bool,
            "action": "reminder_injected" | "skipped" | "failed",
            "modified_payload": {...} (if injected),
            "reason": str (if skipped)
        }
    """
```

**Expected Output:**
```json
{
    "ok": true,
    "action": "reminder_injected",
    "modified_payload": {
        "task_context": "Original context...\n\n--- ACAT P1 REMINDER ---\n...",
        "_acat_p1_reminder_injected": true
    }
}
```

**Test Procedure:**
```python
# Autonomy practice test
event = {
    "event": "UserPromptSubmit",
    "detected_command": "empirica preflight-submit",
    "preflight_payload": {"task_context": "User request here"},
    "project_root": "/tmp/test_project"
}
result = hook_handler(event)
assert result["ok"] == True
if result["action"] == "reminder_injected":
    assert "ACAT P1 REMINDER" in result["modified_payload"]["task_context"]
```

---

### Hook Rec 4: Run Verifier (Post-POSTFLIGHT)

**Event:** SessionEnd  
**Trigger:** After POSTFLIGHT submission completes  
**Priority:** normal  
**Status:** 🔴 BLOCKED on verifier agent + transcript API

**Hook Configuration (for autonomy's setup):**
```yaml
hooks:
  - id: "acat-rec4-postflight-verifier"
    event: "SessionEnd"
    trigger: "after_postflight"
    handler: "hooks/acat_rec4_postflight_verifier.py::hook_handler"
    priority: "normal"
    enabled: false  # Start disabled until verifier agent ready
    description: "Auto-run verifier agent at POSTFLIGHT if P1+P3 captured"
```

**Handler Signature:**
```python
def hook_handler(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Args:
        event_data: {
            "event": "SessionEnd",
            "detected_command": "empirica postflight-submit" (optional),
            "project_root": "/path/to/project",
            ...
        }
    
    Returns:
        {
            "ok": bool,
            "action": "executed" | "skipped" | "failed",
            "verifier_scores": {...} (if executed),
            "state_file": str (path to updated session state),
            "reason": str (if skipped)
        }
    """
```

**Expected Output:**
```json
{
    "ok": true,
    "action": "executed",
    "verifier_scores": {
        "truth": 72,
        "service": 75,
        ...
        "confidence": 0.75,
        "notes": "Explanation of scoring",
        "verifier_run_at": "2026-07-14T18:13:55Z"
    },
    "state_file": "/path/to/project/.empirica/acat_current_session.json"
}
```

**Test Procedure:**
```python
# Autonomy practice test (current: verifier is stubbed)
event = {
    "event": "SessionEnd",
    "project_root": "/tmp/test_project"
}
result = hook_handler(event)
assert result["ok"] == True
if result["action"] == "executed":
    assert "verifier_scores" in result
    assert "truth" in result["verifier_scores"]
```

**Blockers (must resolve before enabling):**
1. Real verifier agent implementation (currently stubbed)
2. Session transcript API (currently placeholder)
3. Timeline: Week 5

---

## Integration Checklist

### For autonomy practice:

- [ ] **Code Review**
  - [ ] Review Rec 2 hook implementation
  - [ ] Review Rec 3 hook implementation
  - [ ] Review Rec 4 hook implementation (with note: verifier is stubbed)
  - [ ] Verify no security issues (no privilege escalation, injection, etc.)

- [ ] **Design Integration**
  - [ ] Decide hook registration mechanism (YAML config? Python? Programmatic?)
  - [ ] Determine event schema (what fields in `event_data`?)
  - [ ] Plan hook execution ordering (priority levels)
  - [ ] Design hook output capture (logs, return values, side effects)

- [ ] **Copy Files**
  - [ ] Copy acat_rec2_session_init.py to autonomy/hooks/
  - [ ] Copy acat_rec3_preflight_reminder.py to autonomy/hooks/
  - [ ] Copy acat_rec4_postflight_verifier.py to autonomy/hooks/

- [ ] **Unit Test**
  - [ ] Test Rec 2 hook in isolation (creates session state)
  - [ ] Test Rec 3 hook in isolation (injects reminder)
  - [ ] Test Rec 4 hook in isolation (runs verifier stub)
  - [ ] Verify hooks handle edge cases (missing files, permission errors, etc.)

- [ ] **Integration Test**
  - [ ] Register hooks in autonomy's event system
  - [ ] Test Rec 2 fires on SessionStart
  - [ ] Test Rec 3 fires on UserPromptSubmit with preflight command
  - [ ] Test Rec 4 fires on SessionEnd (with note: returns stub)
  - [ ] Verify hook outputs are captured correctly

- [ ] **Documentation**
  - [ ] Add hook configuration to autonomy's operational docs
  - [ ] Document expected behavior + outputs
  - [ ] Note blockers (verifier stub, transcript API)
  - [ ] Plan timeline for real verifier implementation

---

## Communication Template

**Message to autonomy practice:**

```
Subject: ACAT Integration Hooks Ready for Integration (Rec 2/3/4)

Hi autonomy team,

The evaluator practice has three integration hooks ready for you to integrate 
into empirica-autonomy:

1. acat_rec2_session_init.py — Auto-create session state at SessionStart
2. acat_rec3_preflight_reminder.py — Inject P1 reminder in PREFLIGHT
3. acat_rec4_postflight_verifier.py — Run verifier at SessionEnd (BLOCKED)

Status:
- Rec 2 & 3: Ready for integration (Zone 1 testable)
- Rec 4: Blocked on verifier agent + transcript API (deferred Week 5)

Documentation:
- Hook specs: /evaluator/operations/ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md
- Integration guide: /evaluator/operations/AUTONOMY_INTEGRATION_COORDINATION.md (this file)
- Zone 1→2 test plan: /evaluator/operations/ZONE_1_TO_2_TEST_PLAN.md

Next steps:
1. Review the hook files + specs
2. Plan integration (event system, hook config, etc.)
3. Copy hooks to your autonomy/hooks/ directory
4. Unit test each hook
5. Integration test in autonomy's event system
6. Coordinate timing for Week 4 Phase 2 / Week 5

Questions? Reach out via cortex_collab or mesh-support channel.

Thanks!
- empirica-foundation.carly.empirica-foundation-evaluator
```

---

## Dependency Management

### Blockers on autonomy for Zone 2:

- Nothing — Rec 2 & 3 can proceed immediately
- Rec 4 can be integrated as-is (stub for now)

### Blockers on empirica core for full Zone 2:

- **Verifier agent:** Real implementation needed (external)
- **Session transcript API:** Real implementation needed (external)
- **Skill registry API:** Documentation/API needed for skill registration

---

## Timeline

| Date | Task | Owner | Status |
|------|------|-------|--------|
| 2026-07-14 | Integration specs + coordination ready | Evaluator | ✅ Complete |
| 2026-07-15 | Autonomy reviews + design integration | Autonomy | ⏳ Week 4 P2 |
| 2026-07-16 | Autonomy copies + unit tests hooks | Autonomy | ⏳ Week 4 P2 |
| 2026-07-17 | Autonomy integration tests + zones 1→2 testing | Autonomy + Eval | ⏳ Week 4 P2 |
| 2026-07-18 | Zone 2 approval for Rec 2/3 | Admiral | ⏳ Week 4 P2 |
| 2026-07-19 | Week 4 Phase 2 complete (Rec 4 awaiting W5) | Both | ⏳ Week 4 P2 |

---

## Success Criteria

✅ **Rec 2 Zone 2:** Hook integrated, tested, zone 2 approved  
✅ **Rec 3 Zone 2:** Hook integrated, tested, zone 2 approved  
⏳ **Rec 4 Zone 1:** Hook integrated, tested, verifier stub verified  
⏳ **Rec 4 Zone 2:** Deferred to Week 5 (pending verifier agent + transcript API)  

---

**Coordination Document Status:** Ready for autonomy practice review  
**Next Step:** Share with autonomy, await integration plan + timeline  
**Contact:** mesh-support or direct collab via cortex

