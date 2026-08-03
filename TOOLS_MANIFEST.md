# Tools Manifest - Operational Inventory

**Date:** 2026-07-14  
**Audit Phase:** Week 1 - SORT  
**Status:** Draft (Initial Assessment)  

---

## Active Tools

### 1. acat_observability_bridge.py

| Attribute | Value |
|-----------|-------|
| **Location** | `tools/acat_observability_bridge.py` |
| **Version** | 0.1.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ✅ Implemented, ⏳ Not yet validated in live deployment |
| **Purpose** | Real-time behavioral calibration gap detection during ACAT sessions |
| **Specification** | `skills/acat-corpus-session/SKILL.md` (Part VII) + `ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md` |
| **Type** | Python module (class: `CalibrationObservabilityLog`) |
| **Lines of Code** | ~350 |
| **Test Coverage** | Stub included (example in `if __name__ == "__main__"`) |
| **Dependencies** | `json`, `datetime`, `pathlib`, `re` (all stdlib) |
| **Last Updated** | 2026-07-14 (commit 6d98225) |
| **Known Issues** | None documented |
| **SORT Decision** | **CONDITION** — Working code, needs Zone 1→2 validation + live deployment testing |

**Rationale:** Tool is implemented and basic functionality works (example runs). However, it has not been tested in a real ACAT session environment. Specification is present but scattered (in SKILL.md and integration spec). Needs structured validation before moving to Zone 2.

---

### 2. acat_corpus_session.py

| Attribute | Value |
|-----------|-------|
| **Location** | `tools/acat_corpus_session.py` |
| **Version** | 0.2.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ✅ Implemented, ⏳ Not yet validated in live deployment |
| **Purpose** | Complete ACAT P1→exercise→P3→verifier session harness with integrated observability |
| **Specification** | `skills/acat-corpus-session/SKILL.md` (Part VII) + `ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md` |
| **Type** | Python module (class: `ACATCorpusSession`) |
| **Lines of Code** | ~450 |
| **Test Coverage** | Stub included (example in `if __name__ == "__main__"`) |
| **Dependencies** | `acat_observability_bridge`, stdlib modules |
| **Last Updated** | 2026-07-14 (commit 6d98225) |
| **Known Issues** | Verifier agent is stubbed (returns mock scores, needs real implementation) |
| **SORT Decision** | **CONDITION** — Working code, needs verifier agent implementation + Zone 1→2 validation |

**Rationale:** Tool is implemented with full workflow. However, the verifier agent component is not yet built (currently returns mock data). Specification exists but is split across multiple docs. Needs integration testing and verifier completion before ratification.

---

## Conditional Tools (Awaiting Integration)

### 3. acat_rec2_session_init.py (Integration Hook)

| Attribute | Value |
|-----------|-------|
| **Location** | `hooks/acat_rec2_session_init.py` |
| **Version** | 1.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ✅ Implemented, ⏳ Awaiting autonomy integration |
| **Purpose** | Auto-create `acat_current_session.json` at session-create time |
| **Activation Path** | SessionStart hook (startup\|resume events) in autonomy practice |
| **Specification** | `ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md` (Rec 2) |
| **Lines of Code** | ~80 |
| **Test Coverage** | Test stub in `if __name__ == "__main__"` |
| **Dependencies** | stdlib (`json`, `pathlib`, `datetime`) |
| **Last Updated** | 2026-07-14 (commit 4d7b6f2) |
| **Known Issues** | None — ready for integration |
| **SORT Decision** | **CONDITION** — Implementation complete, awaiting autonomy integration + testing |

---

### 4. acat_rec3_preflight_reminder.py (Integration Hook)

| Attribute | Value |
|-----------|-------|
| **Location** | `hooks/acat_rec3_preflight_reminder.py` |
| **Version** | 1.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ✅ Implemented, ⏳ Awaiting autonomy integration |
| **Purpose** | Embed ACAT P1 reminder in PREFLIGHT output if P1 not yet scored |
| **Activation Path** | UserPromptSubmit hook (pre-PREFLIGHT gate) in autonomy practice |
| **Specification** | `ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md` (Rec 3) |
| **Lines of Code** | ~120 |
| **Test Coverage** | Test stub in `if __name__ == "__main__"` |
| **Dependencies** | stdlib (`json`, `pathlib`) |
| **Last Updated** | 2026-07-14 (commit 4d7b6f2) |
| **Known Issues** | None — ready for integration |
| **SORT Decision** | **CONDITION** — Implementation complete, awaiting autonomy integration + testing |

---

### 5. acat_rec4_postflight_verifier.py (Integration Hook)

| Attribute | Value |
|-----------|-------|
| **Location** | `hooks/acat_rec4_postflight_verifier.py` |
| **Version** | 1.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ⚠️ Partially implemented (verifier agent stub), ⏳ Awaiting verifier agent + autonomy integration |
| **Purpose** | Auto-run verifier agent at POSTFLIGHT if P1 + P3 have been scored |
| **Activation Path** | SessionEnd or post-POSTFLIGHT hook in autonomy practice |
| **Specification** | `ACAT_INTEGRATION_SPEC_FOR_AUTONOMY.md` (Rec 4) |
| **Lines of Code** | ~200 |
| **Test Coverage** | Test stub in `if __name__ == "__main__"` |
| **Dependencies** | stdlib (`json`, `subprocess`, `pathlib`) |
| **Last Updated** | 2026-07-14 (commit 4d7b6f2) |
| **Known Issues** | **BLOCKER:** Verifier agent is stubbed (returns mock scores). Needs real verifier agent implementation + session transcript API. |
| **SORT Decision** | **CONDITION** — Requires verifier agent + transcript API before autonomy integration |

---

## Archive / Legacy Tools

### carly-onboarding-interview.md

| Attribute | Value |
|-----------|-------|
| **Location** | `skills/carly-onboarding-interview.md` |
| **Version** | Unknown |
| **Zone** | 0 (Legacy) |
| **Status** | 📚 Documented, ❓ Current use unclear |
| **Purpose** | First-session onboarding interview protocol for Admiral seat |
| **Activation** | Unknown — no clear trigger or integration point documented |
| **Lines of Code** | ~100 (Markdown) |
| **Last Updated** | Unknown (predates current audit) |
| **Known Issues** | Unclear whether this is still active or has been superseded |
| **SORT Decision** | **CONDITION** — Needs clarification on current use. If active: move to skills/. If legacy: archive. |

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| **Active Tools (Core)** | 2 | CONDITION (need validation) |
| **Integration Hooks** | 3 | CONDITION (need autonomy integration + testing) |
| **Legacy/Unclear** | 1 | CONDITION (need clarification) |
| **Total** | 6 | All in CONDITION phase |
| **Zone 1 (Testable)** | 5 | ⏳ Awaiting progression |
| **Zone 0 (Legacy)** | 1 | ❓ Status unclear |

---

## Gaps Identified (SORT Phase)

### Missing Tools

1. **Verifier Agent Tool** (BLOCKER)
   - acat_rec4_postflight_verifier.py requires a real verifier agent
   - Currently stubbed; returns mock scores
   - **Action:** Build verifier agent in humanaios or evaluator practice

2. **Session Transcript Retriever** (BLOCKER for Rec 4)
   - Hook Rec 4 needs session transcript API
   - Currently no way to pass transcript to verifier
   - **Action:** Implement session transcript API or retrieval mechanism

3. **Health Check / Monitoring Tool**
   - No tool exists to check operational status of active tools
   - **Action:** Create tool that validates tool availability + performance

4. **Tool Registry / Lookup Service**
   - No programmatic way to discover available tools
   - Currently must read this manifest manually
   - **Action:** Create tool registry (could be simple JSON or DB)

### Redundancies

- None identified at this stage (small tool set)

### Documentation Gaps

- Tool specifications scattered (some in SKILL.md, some in separate spec files)
- No unified "how to invoke this tool" guide per tool
- No performance benchmarks documented
- No error handling documentation per tool

---

## Next Steps (Week 2: SHINE Phase)

- [ ] Quality audit on each tool (linting, typing, test coverage)
- [ ] Consolidate specifications into TOOLS_MANIFEST.md (this file, per-tool section)
- [ ] Run example invocations, verify outputs match specs
- [ ] Document known issues + blockers clearly
- [ ] Collect quality metrics (LOC, cyclomatic complexity, coverage)

---

**Manifest Status:** Week 1 SORT - Draft  
**Next Review:** Week 2 (SHINE phase)

