# Skills Manifest - Operational Inventory

**Date:** 2026-07-14  
**Audit Phase:** Week 1 - SORT  
**Status:** Draft (Initial Assessment)  

---

## Active Skills

### 1. /acat-corpus-session (ACAT Corpus Session Harness)

| Attribute | Value |
|-----------|-------|
| **Location** | `skills/acat-corpus-session/SKILL.md` |
| **Version** | 0.2.0 |
| **Zone** | 1 (Testable/Draft) |
| **Status** | ✅ Skill definition complete, ⏳ Not yet registered in skill registry |
| **Purpose** | 6-step ACAT evaluation workflow with real-time observability bridge |
| **Trigger Phrases** | `/acat-corpus-session`, "run ACAT corpus session", "start corpus evaluation" |
| **Activation Status** | ❓ Not currently registered in any skill registry (needs manual loading) |
| **When to Invoke** | When beginning an ACAT evaluation session using a TOP exercise, or generating corpus entry for HumanAIOS |
| **Protocol Steps** | 6 steps (setup, P1, exercise, P3, verifier, report) |
| **Output** | State file, observability trace JSONL, corpus entry, cross-instrument finding |
| **Dependencies** | `tools/acat_corpus_session.py`, `tools/acat_observability_bridge.py`, verifier agent |
| **Integration Points** | Empirica-autonomy (for Rec 2/3/4 hooks), humanaios (for verifier agent + API) |
| **Last Updated** | 2026-07-14 (commit 6d98225) |
| **Known Issues** | Verifier agent stub (Rec 4 hook) not yet implemented |
| **SORT Decision** | **CONDITION** — Skill definition complete, needs registration + live testing in corpus session |

**Documentation Quality:**
- ✅ Purpose clear
- ✅ Trigger phrases documented
- ✅ Protocol steps defined
- ✅ Output format specified
- ✅ Dependencies listed
- ⏳ No activation examples (how to actually invoke)
- ⏳ No troubleshooting guide

---

## Conditional Skills (Awaiting Activation)

### 2. /empirica-constitution (Deep Governance Framework)

| Attribute | Value |
|-----------|-------|
| **Location** | `/Users/andersonfamily/.claude/plugins/local/empirica/skills/empirica-constitution` |
| **Version** | 1.0 |
| **Zone** | 2 (Ratified) |
| **Status** | ✅ Live and active |
| **Purpose** | Deep governance reference for Empirica operations (phase-aware completion, turtle principle, mesh discipline) |
| **Trigger Phrases** | "empirica constitution", "practice model", "cognitive immune", "turtle principle", "what counts as done" |
| **Activation Status** | ✅ Already active in empirica system prompt |
| **When to Invoke** | When routing operational decisions, understanding practice model, mesh discipline guidance |
| **Last Updated** | Unknown (external to evaluator practice) |
| **SORT Decision** | **KEEP** — External tool, active, no action needed for evaluator practice |

### 3. /cortex-mailbox-send (AI Mesh Comms)

| Attribute | Value |
|-----------|-------|
| **Location** | `/Users/andersonfamily/.claude/plugins/local/empirica/skills/cortex-mailbox-send` |
| **Version** | 1.0 |
| **Zone** | 2 (Ratified) |
| **Status** | ✅ Live and active |
| **Purpose** | Send messages to peer AIs via Cortex mesh (collab, propose, publish) |
| **Trigger Phrases** | "send to", "cortex propose", "ask autonomy", "propose to mesh" |
| **Activation Status** | ✅ Already active in empirica cortex prompt |
| **When to Invoke** | When communicating with peer AIs across the mesh |
| **Last Updated** | Unknown (external, updated 2026-06-21 per cortex prompt) |
| **SORT Decision** | **KEEP** — External tool, active, no action needed for evaluator practice |

### 4. /cortex-mailbox-poll (Inbox Listening)

| Attribute | Value |
|-----------|-------|
| **Location** | `/Users/andersonfamily/.claude/plugins/local/empirica/skills/cortex-mailbox-poll` |
| **Version** | 1.0 |
| **Zone** | 2 (Ratified) |
| **Status** | ✅ Live and active |
| **Purpose** | Receive and react to proposals from peer AIs |
| **Trigger Phrases** | Automatic (policy event listener) |
| **Activation Status** | ✅ Already active via listener + mailbox inbox |
| **When to Invoke** | Automatic on proposal arrival; manual poll also available |
| **Last Updated** | Unknown (external, updated 2026-06-21 per cortex prompt) |
| **SORT Decision** | **KEEP** — External tool, active, no action needed for evaluator practice |

---

## Active Skills (Operational)

### carly-onboarding-interview

| Attribute | Value |
|-----------|-------|
| **Location** | `skills/carly-onboarding-interview.md` |
| **Version** | 0.1.0 |
| **Zone** | 1 (draft) |
| **Status** | ✅ Active (clarified Week 2) |
| **Purpose** | First-session onboarding workflow for Carly's Admiral seat. Discovers evaluation workflow, recommends practices, seeds epistemic profiles, defines demonstration harnesses. |
| **Trigger Phrases** | Manual invocation (first session only, or re-onboarding); no auto-trigger documented |
| **Activation Status** | ⚠️ Active but manual (not auto-triggered) |
| **When to Invoke** | Carly's first session on empirica-foundation-evaluator seat, or when re-onboarding foundation practices |
| **Last Updated** | 2026-07-14 (Week 2 clarification) |
| **SORT Decision** | **KEEP** — Active, well-documented protocol. Zone 1. Needs trigger documentation + registry clarification (Week 3). |
| **Notes** | This is the archetype for productized 1-hour onboarding (GTM vision). Structure generalizes to other onboardees; practice menu + demo content are what change. Emphasis on integrity: run under visible empirica discipline, make honest with/without demonstrations. |

---

## Skills Awaiting Implementation

### Missing Skills (Identified Gaps)

1. **`/acat-session-health-check`** (SHOULD EXIST)
   - Validate that active ACAT tools are operable
   - Check observability bridge + corpus session availability
   - Report status + known issues
   - **Priority:** High (needed for sustainability monitoring)

2. **`/tool-registry-lookup`** (SHOULD EXIST)
   - Query available tools and skills
   - Show status, version, documentation
   - Suggest which tool to use for a task
   - **Priority:** Medium (QoL improvement for discovery)

3. **`/acat-assessment-runner`** (SHOULD EXIST)
   - Orchestrate P1→P3 assessment workflow
   - Automate ACAT data collection per tool/skill
   - Generate assessment report with Learning Index
   - **Priority:** High (needed for audit implementation)

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| **Active Skills (Evaluator)** | 1 | CONDITION (needs registration + testing) |
| **Active Skills (External)** | 2 | KEEP (already active) |
| **Conditional Skills** | 0 | — |
| **Legacy/Unclear** | 1 | CONDITION (clarify use) |
| **Missing Skills** | 3 | BUILD (high priority) |
| **Total** | 7 | 1 ready for activation, 2 external, 3 to build |

---

## Activation Status Matrix

| Skill | Registered | Trigger Active | Documented | Integrated |
|-------|-----------|----------------|-----------|-----------|
| `/acat-corpus-session` | ❌ No | ⚠️ Manual | ✅ Yes | ⏳ Partial |
| `/empirica-constitution` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| `/cortex-mailbox-send` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| `/cortex-mailbox-poll` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| `carly-onboarding-interview` | ⚠️ Unclear | ⚠️ Manual | ✅ Yes | ⚠️ First-session only |

---

## Activation Blockers

### Blocker 1: `/acat-corpus-session` Not Registered
- **Status:** The skill is defined but not registered in any skill registry
- **Impact:** Users cannot discover it via `/acat-corpus-session` or trigger phrases
- **Solution:** Register in skill registry (autonomy practice? evaluator practice?)
- **Action:** Week 3 (Standardize phase) — formalize registration process

### Blocker 2: Verifier Agent Missing (Rec 4)
- **Status:** Skill step 5 (verifier) requires real verifier agent implementation
- **Impact:** Cannot complete full P1→P3→verifier protocol
- **Solution:** Build verifier agent in humanaios or evaluator practice
- **Action:** Week 4-5 — implement verifier agent

### Blocker 3: Session Transcript API Missing (Rec 4)
- **Status:** Verifier needs access to session transcript
- **Impact:** Verifier agent has no data to assess
- **Solution:** Implement session transcript retrieval API
- **Action:** Week 4-5 — implement transcript API

---

## Documentation Issues

### Skills Documentation Quality Checklist

| Skill | Purpose | Triggers | Examples | Troubleshooting | Docs Complete |
|-------|---------|----------|----------|-----------------|---|
| `/acat-corpus-session` | ✅ | ✅ | ⚠️ Partial | ❌ No | ⏳ 75% |
| `/empirica-constitution` | ✅ | ✅ | ✅ | ✅ | ✅ 100% |
| `/cortex-mailbox-send` | ✅ | ✅ | ✅ | ✅ | ✅ 100% |
| `/cortex-mailbox-poll` | ✅ | ✅ | ✅ | ✅ | ✅ 100% |
| `carly-onboarding-interview` | ⚠️ Unclear | ⚠️ Unclear | ❌ No | ❌ No | ⏳ 25% |

---

## Next Steps (Week 2: SHINE Phase)

- [ ] Verify `/acat-corpus-session` can be manually invoked (run test)
- [ ] Test all trigger phrases
- [ ] Verify all listed dependencies are available
- [ ] Check for linting/typing issues in skill definition file
- [ ] Clarify status of `carly-onboarding-interview` (active or legacy?)
- [ ] Document examples of successful skill invocation

---

**Manifest Status:** Week 1 SORT - Draft  
**Next Review:** Week 2 (SHINE phase)

