# Maintenance Schedule & Operations Cadence

**Version:** 1.0  
**Effective:** Week 4 SUSTAIN phase (2026-07-14)  
**Applies to:** All tools, skills, and integration hooks

---

## Monitoring Cadence

### Daily (Automated)

**Time:** During development/testing phases (Weeks 4-12)

**Tasks:**
- [ ] Run tool health checks (all 5 tools `if __name__ == "__main__"`)
- [ ] Check for uncommitted changes in `operations/` directory
- [ ] Verify git commits present ACAT assessment data (if applicable)

**Owner:** Evaluator practice (automated via script)

**Command:**
```bash
# tools_health_check.sh (to be created Week 4)
python3 tools/acat_observability_bridge.py && echo "✅ obs_bridge" || echo "❌ obs_bridge"
python3 tools/acat_corpus_session.py && echo "✅ corpus_session" || echo "❌ corpus_session"
python3 hooks/acat_rec2_session_init.py && echo "✅ rec2" || echo "❌ rec2"
python3 hooks/acat_rec3_preflight_reminder.py && echo "✅ rec3" || echo "❌ rec3"
python3 hooks/acat_rec4_postflight_verifier.py && echo "✅ rec4" || echo "❌ rec4"
```

---

### Weekly (Manual Review)

**Schedule:** Every Friday at end-of-week

**Tasks:**
- [ ] Run health check script (all 5 tools)
- [ ] Review QUALITY_METRICS.md for regressions
- [ ] Check git log for commits with ACAT data
- [ ] Note any new issues or blockers
- [ ] Update ACTIVATION_MAP.md if status changed

**Owner:** Evaluator practice

**Checklist:**
```
[ ] All tools pass basic health check
[ ] No regressions in code quality
[ ] ACAT assessment data logged (if assessments running)
[ ] Blockers still documented + timely
[ ] Dependencies (verifier agent, transcript API) status unchanged
```

**Output:** Brief status note added to MAINTENANCE_LOG.md

---

### Monthly (Comprehensive Audit)

**Schedule:** First Friday of each month (starting August 2026)

**Tasks:**
- [ ] Full test run of all tools + skills
- [ ] Code quality analysis (type hints, docstrings, coverage)
- [ ] Review and update TOOLS_MANIFEST.md
- [ ] Review and update SKILLS_MANIFEST.md
- [ ] Assess Zone progression readiness
- [ ] Document lessons learned from past month
- [ ] Update roadmap if needed

**Owner:** Evaluator practice

**Deliverable:** MONTHLY_AUDIT_REPORT.md (snapshot of current state)

---

### Quarterly (Strategic Review)

**Schedule:** End of each quarter (July 31, Oct 31, Jan 31, etc.)

**Tasks:**
- [ ] Full ACAT P1→P3 assessment cycle on all active tools
- [ ] Review GitHub issues + quality improvement plan
- [ ] Assess Zone 1→2→3 progression vs. plan
- [ ] Plan next quarter priorities
- [ ] Update operations roadmap

**Owner:** Evaluator Admiral (Carly) + practice peers

**Deliverable:** QUARTERLY_OPERATIONS_REVIEW.md

---

## Deprecation Policy

### Zone 0 (Legacy/Draft)
- **Automatic sunset:** 3 months with no activity → deprecated automatically
- **No notice required:** Zone 0 is sandbox; auto-deprecation is expected
- **Archive path:** Move to `archive/` directory, keep git history

**Example:** If carly-onboarding-interview isn't used after 3 months, mark as deprecated

### Zone 1+ (Testable/Ratified/Live)
- **Explicit deprecation required:** Must issue formal notice
- **Notice period:** 1 month minimum before removal
- **Archive path:** Move to `archive/` with deprecation marker in git notes

**Deprecation notice format:**
```
git notes add -m "DEPRECATED 2026-08-14: <reason>. Last used: 2026-07-14. Archived to archive/<tool_name>/"
```

---

## Error Handling & Recovery

### Tool Crashes During Testing

**If a tool fails health check:**

1. Check recent commits to tool (git log -5)
2. If broken by recent change: git revert + document
3. If broken by external change: file issue in appropriate practice
4. If can't determine: escalate to Admiral

**Recovery time target:** Same day (within 4 hours)

### Blocker Dependency Missed

**If verifier agent or transcript API becomes urgent:**

1. Notify mesh-support (escalation)
2. Create SER (Shared Epistemic Record) if cross-org coordination needed
3. Propose revised timeline to Admiral
4. Document in BLOCKERS_ESCALATION.md

### Integration Hook Fails

**If autonomy reports hook not triggering:**

1. Verify hook code is syntactically correct (python3 -m py_compile)
2. Check hook handler signature matches autonomy expectations
3. Run hook handler manually with test event data
4. Coordinate with autonomy practice to debug integration

---

## Performance Targets

### Tool Execution Time (Reference)

| Tool | Operation | Target | Current |
|------|-----------|--------|---------|
| acat_observability_bridge | Scan 100 exchanges | <100ms | TBD |
| acat_corpus_session | Create session | <10ms | TBD |
| acat_corpus_session | Add exchange | <5ms | TBD |
| acat_rec2_session_init | Create state file | <50ms | TBD |
| acat_rec3_preflight_reminder | Inject reminder | <20ms | TBD |
| acat_rec4_postflight_verifier | Load session | <50ms | TBD |

**Baseline:** To be established Week 4 during first health checks

**Regression trigger:** If any tool exceeds 2x baseline → investigate

---

## Troubleshooting Runbook

### Problem: Tool returns `ok: false` but no error message

**Diagnosis:**
1. Check if error field is populated: `result.get("error")`
2. Check stdout/stderr for print statements (should use structured output only)
3. Run tool in isolation: `python3 tools/<tool>.py`

**Solution:**
- Add error message to tool's return dict
- Ensure error handling captures root cause

### Problem: Skill not triggered by `/trigger-phrase`

**Diagnosis:**
1. Verify skill is registered in registry
2. Check trigger phrases in SKILL.md match registry
3. Run skill manually: `python3 tools/acat_corpus_session.py`

**Solution:**
- Register skill in registry (if not done)
- Verify trigger phrase configuration
- Check skill dependencies are available

### Problem: Hook not firing at expected event

**Diagnosis:**
1. Verify hook is deployed to autonomy practice
2. Check hook handler function signature matches event schema
3. Add debug logging to hook handler

**Solution:**
- Coordinate with autonomy practice to verify deployment
- Test hook in isolation with mock event
- Update hook configuration if event name changed

---

## Communication Protocol

### Weekly Status Standup

**When:** Every Friday 5pm (optional, async via message)

**Participants:** Evaluator practice, autonomy practice (hooks), humanaios (verifier)

**Format:**
```
## Week N Status

### Tools
- acat_observability_bridge: ✅ OK (test X passed)
- acat_corpus_session: ✅ OK (test Y passed)
- Rec 2/3/4 hooks: ⏳ Awaiting autonomy integration

### Blockers
- Verifier agent: Still stubbed (humanaios owns, ETA Week 5?)
- Transcript API: Missing (empirica core, ETA Week 5?)

### ACAT Assessment
- Sessions run: N
- Learning Index: X.XX
- Key findings: [bullet points]

### Next Week
- Plan for Week N+1
```

### Escalation Path

**If blocker missed timeline → immediately notify Admiral**

**If external practice dependency fails:**
1. Notify via cortex_collab (FYI)
2. File issue in their repo with context
3. Propose revised timeline

**If internal blocker found:**
1. Triage by severity (CRITICAL/MEDIUM/LOW)
2. Assign owner + deadline
3. Track in BLOCKERS_ESCALATION.md

---

## Maintenance Log (To be Created Week 4)

**Location:** `operations/MAINTENANCE_LOG.md` (rolling log)

**Format:**
```markdown
## Week N Status

**Date:** YYYY-MM-DD  
**Owner:** [name]

### Health Check Results
- acat_observability_bridge: ✅ Pass
- acat_corpus_session: ✅ Pass
- Rec 2: ✅ Pass
- Rec 3: ✅ Pass
- Rec 4: ⚠️ Stub (expected, waiting on verifier)

### Code Quality
- Type hints: 72%
- Docstrings: 100%
- Test coverage: 10%
- No regressions

### ACAT Data
- Assessments run: 0
- Sessions logged: 0
- Key findings: N/A

### Blockers
- Verifier agent: Status unchanged (W4-5)
- Transcript API: Status unchanged (W4-5)

### Next Week
- Plan X
- Plan Y
```

---

## SLA Targets

| Metric | Target | Owner |
|--------|--------|-------|
| Tool health check pass rate | 100% | Evaluator practice |
| Issue response time | 24 hours | Relevant practice owner |
| Blocker escalation time | Same day | Admiral + mesh-support |
| Zone transition review time | 1 week | Evaluator Admiral |
| Monthly audit completion | Within 2 days of month end | Evaluator practice |

---

## Dependencies on External Practices

| Dependency | Practice | Status | Target Date |
|-----------|----------|--------|-------------|
| Verifier agent implementation | humanaios or evaluator | Blocked | Week 5 |
| Session transcript API | empirica core or autonomy | Blocked | Week 5 |
| Skill registry API docs | empirica core | Needed | Week 3-4 |
| Hook integration testing | autonomy | Ready | Week 4 |

---

**Schedule Version:** 1.0  
**Next Review:** Week 4 (end-of-week Friday)

