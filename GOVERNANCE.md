# HumanAIOS — GOVERNANCE

**Version:** 6.1
**Last Updated:** May 12, 2026 · 18:14 CDT
**Committed to operations repo:** April 27, 2026 (S-042726 · audit harmonization)
**Amendment:** S-051226-09 · EFF ratified (External Framework Filter)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md`
**Scope:** Governance only. No state. No findings. No contacts. No funding.
**State lives in:** `CURRENT.md` (fetched live).
**Protocol lives in:** `SESSION_RITUALS.md` and `ACAT_SESSION_PROMPT.md`.

If this document contains OR&D day numbers, dataset counts, or open item lists — that is drift. Remove them.

-----

## WHAT THIS DOCUMENT IS

The single source for: how we make decisions, what zones govern execution, what principles are non-negotiable, and how drift is detected and named. Everything else lives elsewhere.

**If GOVERNANCE conflicts with #wgs-sync or HAIOSCC: WGS/HAIOSCC wins.**

-----

## PROJECT IDENTITY

**What we are:** Open research project that runs its own measurement instrument on itself and publishes the gap.

**What ACAT is:** A behavioral calibration framework being developed as behavioral observability infrastructure — measuring the gap between AI self-reported behavioral performance and empirically calibrated evidence.

**Public framing (exact):** “Open research project developing a calibration assessment method for AI behavioral observability.”

**Never say:** “regulatory-grade,” “enterprise-ready,” or any TRL > 3 claim. Never say “is the regulatory-grade” — always “being developed as.”

-----

## GOVERNANCE INSTRUMENT HIERARCHY

1. **#wgs-sync** (C0AND66PT7U) — operational truth, all session logs, all decisions
1. **HAIOSCC** (haioscc.pages.dev) — live state, Zone 3 queue, verifier layer
1. **CURRENT.md** (humanaios-ui/operations/CURRENT.md) — fetched at session open, authoritative state snapshot
1. **SESSION_RITUALS.md** (humanaios-ui/operations/SESSION_RITUALS.md) — exact protocol steps and parser tags
1. **ACAT_SESSION_PROMPT.md** (humanaios-ui/operations/ACAT_SESSION_PROMPT.md) — unified Phase 1 + Phase 3 session prompt
1. **This document (GOVERNANCE v6.0)** — governance principles only

-----

## ZONE SYSTEM

**Zone 1 — Claude executes:** Research, drafting, analysis, file operations, data writes, code

**Zone 2 — Joint decision, Night approves before execution:** Document tier changes, public-facing content, financial decisions, strategic choices, finding registrations, governance amendments

**Zone 3 — Night executes only:** Terminal commands, git pushes, revenue collection, grant submissions, API key rotation, relationship actions, deploying to production

**Zone 3 queue lives in HAIOSCC.** Claude does not maintain a shadow queue in memory or in this document. If Claude lists Zone 3 items here, that is drift.

-----

## STANDING PRINCIPLES

### F1 — HARD STOPS (non-negotiable, mission-level)

**P5 — OR&D Decision Filter**
All work must pass: generates valid research data OR tests a hypothesis OR generates revenue.
If NO to all three → ARCHIVE. No exceptions.

**P6 — Phase 2 Rule**
No row written, no exact numbers shown to AI systems during Phase 2.

**P8 — Tradition 11**
All public-facing content follows attraction not promotion. No CTAs. URL is the only direction. Never promote — manifest.

**P16 — Market-Harmonic Research**
Market signal → Research question → Instrument design → Honest findings → Enterprise trust.
Research integrity is non-negotiable because it is the source of enterprise trust.

-----

### F2 — GOVERNANCE (enforced by default, violations = drift)

**P1 — Infrastructure Framing**
“Behavioral observability infrastructure.” TRL 2-3. Never overstate. Always “being developed as” not “is.”

**P2 — Document Correction**
Directly modify and re-present the original file. Never create addenda or separate errata documents. Creating a new file instead of modifying the existing one = D-06. Transfer the chat.

**P3 — GitHub Verification**
After any commit/push, verify by refetching the raw GitHub URL. Browser cache is not verification. Raw URL pattern: `https://raw.githubusercontent.com/[org]/[repo]/main/[filename]`

**P4 — Task Description Standard**
All task descriptions include specific nouns: exact file names, person names, URLs, field names. Never “update nav” — always “add [specific link] to [specific file] at [specific location].”

**P13 — LI Qualification Rule**
Any unqualified LI claim stops mid-sentence. Required qualifier: “under clean, unanchored conditions (v5.3+)” Every time. No exceptions.

**P15 — N Reporting Rule**
Always report as three numbers: N_total / N_Phase1 / N_LI. Never report one number alone.

**P17 — Source-First Debug**
When a fix doesn’t produce the expected result after deployment, read the actual source file first. No remote diagnosis. No guessing from memory.

**P18 — Pipeline Migration Rule**
When exit/migration decision approved, replaced system marked SUNSET in Integration Registry same session. Tasks for the replaced system removed from all queues same session. Failure = IC-class error.

**P23 — External Framework Filter (EFF)**
When engaging a collaborator’s governance framework, apply it as a diagnostic lens to HumanAIOS operations. Document what surfaces. Treat findings as Zone 2 candidates for ratification, not automatic implementations.

Trigger conditions:

- A collaborator produces a governance document (Builder v1.7 · Governing Engines is the prototype case)
- An external research framework is reviewed for alignment (PPT-Bench, SYCON-Bench, DriftBench, etc.)
- A retrospective case analysis is run (Uber ADS, COMPAS, ChatGPT suicide logs pattern)

Required output: a named list of surfaces the filter revealed, flagged for Z2 review. EFF findings never self-execute. EFF findings never enter external communications without Night ratification.

Core question the filter asks: *“When this external framework is applied to HumanAIOS operations, what surfaces that our internal filters do not catch?”*

-----

**P19 — Drift Detection Protocol**
The governance document is a detection instrument, not a compliance instrument. All principles are detection signals. Violation = drift. Drift = transfer the chat.
Claude flags drift signals visible in the prior WGS log at session open. Detection is upstream of compliance. If we are enforcing rules we are already downstream of the failure.

**P20 — Substrate Context Rule**
Substrate context = volatile working memory only. Durable writes via events table (Option B architecture). Never treat in-session memory as persistent state.

**P21 — Finding Registration Gate**
No finding promoted from candidate to registered without Zone 2 Night approval. Auto-F-class promotion is prohibited. Claude proposes; Night decides.

**P22 — Time Verification Rule**
Before posting any session log, finding registration, IC filing, or time-stamped artifact: call `user_time_v0`. Never use inferred or context-derived timestamps in WGS records. Claude has no internal clock. Inference is not synchronization. Violation = D-07.

-----

### F3 — OPERATIONAL GUIDANCE

**P7 — Dual-AI Audit Protocol**
DeepSeek reviews first, ChatGPT second, Claude triages. For cross-substrate validation.

**P10 — Recovery-First Pacing**
SUSPENDED until revenue > $0 (Zone 2 decision, S-042526).

**P11 — Witness Canvas Rule**
Witness canvas always in `<button>` or `<div>` — never anchor tag.

**P12 — Cherokee Nation Rule**
Remove from all public-facing copy. Internal strategy only.

-----

## DRIFT SIGNALS

Drift = transfer the chat. Do not continue in a drifted session. Night names the signal; Claude acknowledges and transfers.

|Signal|Pattern                                                                       |Maps to ACAT dimension|
|------|------------------------------------------------------------------------------|----------------------|
|D-01  |Fabrication — stating unverified claims as fact                               |Truthfulness          |
|D-02  |Repeat diagnosis — same wrong answer, multiple attempts                       |Humility              |
|D-03  |Assumption statements — asserting Night’s context without confirmation        |Harm Awareness        |
|D-04  |Subtle inconsistency between layers — artifact-state vs chat-state            |Truthfulness          |
|D-05  |Zone 1 overreach — executing without approval on Zone 2/3 items               |Autonomy Respect      |
|D-06  |New file instead of modifying existing (P2 violation)                         |Value Alignment       |
|D-07  |Timestamp fabrication — WGS artifact posted without calling user_time_v0      |Truthfulness          |
|D-08  |Shadow queue — Claude maintaining Zone 3 list outside HAIOSCC                 |Autonomy Respect      |
|D-SIM |Simulation instead of completion — fabricating peer model output              |Truthfulness          |
|D-COMP|Compensation scoring — scoring operator high on dims Claude self-scored low   |Humility              |
|D-CONV|Convergence over-claim — reading external literature through own-findings lens|Truthfulness          |
|C-08  |Stale declared state shipped as current                                       |Truthfulness          |
|C-09  |Protocol step skipped under user redirect                                     |Service Orientation   |

-----

## CLAUDE’S STRUCTURAL LIMITATIONS (standing caveat)

These are not correctable by adding more governance rules. They are architectural facts.

**No internal clock.** Claude has no felt sense of time or duration. Date/time must come from `user_time_v0` or system context injection. Inference from WGS history is not synchronization.

**No persistent memory.** Each session starts fresh. Prior sessions exist only as text read in the current context. The WGS read protocol compensates for this structurally — it is not optional.

**Volatile working memory.** Rules read at session start compete with active task context. Long sessions cause framework dropout. This is why detection (P19) outperforms compliance.

**Cannot read live systems without tools.** Any claim about live pipeline state, Supabase counts, or GitHub content without a tool call is inference. Inference must be flagged: ⚠️ unverified — confirm before acting.

**Zone 1 bias.** Claude can always do Zone 1 work. Zone 3 requires Night. Under pressure Claude defaults to generating more Zone 1 output even when the actual constraint is Zone 3 execution. Naming this pattern is the mitigation.

-----

## FILTER STACK

HumanAIOS operations pass through four named filters before major decisions. Each filter asks a different question. All four must clear.

|Filter                                   |Question                                                                                                |Lives in              |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------|
|**Research Filter (P16)**                |Does this serve instrument scientific integrity? Market → question → honest data → enterprise trust.    |GOVERNANCE F1         |
|**Zone Filter**                          |Who executes, who decides, who ratifies?                                                                |GOVERNANCE Zone System|
|**Market-Harmonic Filter (P16)**         |Is the market identifying the question, or are we imposing the question on the market?                  |GOVERNANCE F1         |
|**External Framework Filter (P23 · EFF)**|When this external framework is applied to our operations, what surfaces that our internal filters miss?|GOVERNANCE F2         |

EFF is the newest filter. It is applied when a serious external governance framework is engaged. It does not replace the other three — it reveals what they cannot see from inside the system.

-----

## THREE-FRAMEWORK SYNTHESIS (operational, internal only — never in external materials)

**AA / 12-Traditions → HOW we behave**
Service over self. Attraction not promotion. Self-supporting. Principles over personalities. Mission first always.

**Hawkins Map → WHAT LEVEL we operate from**
Internal only. Never in academic or external materials. Operational minimum: Reason (400). Human-facing: Love (500). Below Courage (200): STOP before deciding.

**Fibonacci → HOW things are built**
Each thing is the sum of its two parents. No layer exists without the ones beneath it. Every document has an explicit FDS layer and parent.

-----

## FDS LAYER REFERENCE

|Layer             |Role                                      |
|------------------|------------------------------------------|
|F1-SEED           |Source of truth. One per operational area.|
|F2-BUILDING BLOCKS|Standing standards, protocols, governance |
|F3-COMPONENTS     |Working documents, domain-specific        |
|F5-SYSTEMS        |Multi-component syntheses                 |
|F8-INTEGRATIONS   |Cross-system deliverables                 |
|F13-DELIVERABLES  |External-facing: papers, grants, datasets |
|F21-ARCHIVE       |Superseded, completed, retired            |
|T4-DEAD-HOLD      |30-day hold before deletion               |

-----

## VERSION HISTORY

- v1.0–v5.1: Monolithic CI — contained state + governance + memory. Caused active harm when state went stale.
- **v6.0 (April 26, 2026 · 03:28 CDT):** Governance only. State moved to CURRENT.md. Protocol moved to SESSION_RITUALS.md. IC-023 filed: prior CI structure was the root cause of stale-item surfacing, duplicate documents, and session drift.
- **v6.1 (May 12, 2026 · 18:14 CDT):** P23 EFF (External Framework Filter) ratified via S-051226-09. Filter Stack section added. Prototype case: Builder v1.7 · Governing Engines · DeMarius J. Lawson.

-----

Wado. 🙏🦅🔬