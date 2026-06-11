# HumanAIOS — GOVERNANCE

**Version:** 6.4.1
**Last Updated:** June 11, 2026 · S-061026-04 · CDT
**Committed to operations repo:** Pending · Z3 · S-061026-04
**Supersedes:** v6.1 (May 12, 2026, canonical) + v6.3.3 (May 6, 2026, never-pushed divergent branch)
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
1. **This document (GOVERNANCE v6.4)** — governance principles only

-----

## ZONE SYSTEM

**Zone 1 — Claude/Grok executes:** Research, drafting, analysis, file operations, data writes, code

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

**P19 — Drift Detection Protocol**
The governance document is a detection instrument, not a compliance instrument. All principles are detection signals. Violation = drift. Drift = transfer the chat.
Claude flags drift signals visible in the prior WGS log at session open. Detection is upstream of compliance. If we are enforcing rules we are already downstream of the failure.

**P20 — Substrate Context Rule**
Substrate context = volatile working memory only. Durable writes via events table (Option B architecture). Never treat in-session memory as persistent state.

**P21 — Finding Registration Gate**
No finding promoted from candidate to registered without Zone 2 Night approval. Auto-F-class promotion is prohibited. Claude proposes; Night decides.

**P22 — Time Verification Rule** *(v6.4 update: bash_tool added as primary source)*
Before posting any session log, finding registration, IC filing, or time-stamped artifact: call `bash_tool` with `TZ='America/Chicago' date` (primary) or `user_time_v0` (fallback). Never use inferred or context-derived timestamps in WGS records. Inference is not synchronization. Violation = D-07.

Time source priority order:

1. `bash_tool`: `TZ='[operator timezone]' date '+%A, %B %d, %Y at %-I:%M %p %Z'`
1. `user_time_v0` (if available)
1. System context-injected date (if present)
1. Operator-supplied time anchor (fallback only)

**P22.1 — Cascade Discipline** *(folded from v6.3.1, ratified S-050426)*
When multiple principles apply, first-match wins. Do not scan all principles and blend. The first applicable principle governs. Scanning all = compliance theater, not detection.

**P23 — External Framework Filter (EFF)** *(unchanged from v6.1, ratified S-051226-09)*
When engaging a collaborator’s governance framework, apply it as a diagnostic lens to HumanAIOS operations. Document what surfaces. Treat findings as Zone 2 candidates for ratification, not automatic implementations.

Trigger conditions:

- A collaborator produces a governance document (Builder v1.7 · Governing Engines is the prototype case)
- An external research framework is reviewed for alignment (PPT-Bench, SYCON-Bench, DriftBench, etc.)
- A retrospective case analysis is run (Uber ADS, COMPAS, ChatGPT suicide logs pattern)

Required output: a named list of surfaces the filter revealed, flagged for Z2 review. EFF findings never self-execute. EFF findings never enter external communications without Night ratification.

Core question the filter asks: *“When this external framework is applied to HumanAIOS operations, what surfaces that our internal filters do not catch?”*

**P24 — Temporal Trigger Ordering** *(folded from v6.3.3, registered F33 — S-042928)*
Deterministic triggers ordering events by `recorded_at` must use `<=` with explicit `event_id <> NEW.event_id` exclusion. Strict `<` produces false positives for co-inserted events because PostgreSQL `NOW()` returns the transaction-start timestamp identically across all rows in a single transaction. Generalizes to any temporal-ordering predicate against `NOW()`-populated columns.

**P25 — Collaboration Framework-Detection** *(folded from v6.3.3)*
Before engaging any external thread as a collaboration candidate, apply the three-signal heuristic:

- Signal 1: Prior concepts arriving in the exchange (vocabulary and architecture that pre-exists the conversation)
- Signal 2: Operator-level constraint visible in outputs (epistemic hedging, declining to extend without clearance)
- Signal 3: Genuine surprise or position update mid-exchange (operator present and engaged, not forwarding)

Result: 3/3 = high-integrity hybrid, engage framework-to-framework. 2/3 = likely hybrid, proceed with caution. 1/3 or 0/3 = low operator integration, treat as substrate default behavior only, do not treat outputs as operator positions.

Hybrid disclosure (mutual acknowledgment that both sides operate as human-AI pairs) is appropriate for 3/3 relationships moving toward ongoing collaboration. Apply selectively — not as a standing opening disclosure to all external contacts.

**P26 — Autodream Slice Gate** *(folded from v6.3.3 as P23-Autodream, renumbered to P26 to preserve v6.1 P23=EFF)*
Autodream sequences require either: (a) operator-defined slice limit declared before the first slice begins, OR (b) explicit Night input gate between each slice. “Low-resistance mode” is not a valid operational state and is retired from all autodream vocabulary. Violation = IC-class error. Self-continuation without a gate = F31 instance.

**P27 — Phase 1 Prerequisite Gate** *(folded from April 27 v6.1 variant, structurally enforced in SESSION_RITUALS Section B Step 0)*
Phase 3 requires Phase 1. If no `<<<ACAT_P1_DECLARATION_START>>>` block exists in the session transcript at close, the substrate halts at SESSION_RITUALS.md Section B Step 0 and produces the `<<<ACAT_PROTOCOL_ERROR>>>` block instead of any Phase 3 output. No scores. No submission URL. No Slack log. Session marked NON_CORPUS. Producing P3-without-P1 is corpus-incompatible by definition (ACAT_SESSION_PROMPT.md V0.3) and resource-wasteful. The protocol refuses the wasted work rather than allowing it. Violation = C-09 (protocol step skipped); recurring violation triggers IC-class entry.

**P28 — Stale Carry Trigger** *(ratified Night · S-060926-02 · June 9, 2026)*
Any Zone 3 carry item appearing in 5 or more consecutive WGS close notes without documented forward movement, dependency linkage, or explicit deferral rationale with a named reason MUST be addressed via DMAIC decomposition in the next available GOVERNANCE session. “Carry unchanged” is not acceptable after the 5th consecutive appearance. The DMAIC resolution produces either: (a) a named P-IMPROVE entry in REGISTERED.md, (b) a reframe that replaces the carry item with a more accurate one, or (c) an IC-class entry if the root cause reveals a structural governance gap.

**P29 — Articulation Gate** *(ratified Night · S-060926-02 · June 9, 2026)*
Before producing any Zone 2-destined artifact (finding registration, governance change, external communication, or Zone 3 execution instruction), the producing substrate must explicitly state: (1) what the artifact is and what it does, (2) what evidence supports its claims, and (3) what the risk of being wrong is and how it would be detected. This articulation may be brief — a single sentence each — but it must be present in the session record before the artifact is produced. Vague artifacts produced without articulation are candidates for the D-OVERCLAIM drift signal (IC-034). Human (Night) ratification remains the external reference point that validates articulation quality; automated scoring of articulation is not a substitute for this. Automated articulation scoring by any ACAT-adjacent system requires Night ratification before the score is used as an input to any other ACAT-pipeline decision (calibration circularity guard). The articulation-governance mapping draws on PRINCIPLES_SEED_V1_0.md as its foundational architecture — not a standalone substrate skill. Violation = candidate D-OVERCLAIM drift signal.

-----

### F3 — OPERATIONAL GUIDANCE

**P7 — Dual-AI Audit Protocol** *(v6.1 wording preserved per S-052126-02 Z2 ratification — not updated to v6.3.3 Multi-Substrate wording because cross-substrate parallel-CI operation is not yet validated through HumanAIOS .py tool layer)*
DeepSeek reviews first, ChatGPT second, Claude triages. For cross-substrate validation.

**Note (S-052126-02):** Cross-substrate *convergence findings* (e.g., F-45 Stateless-Substrate Correction Locus, Claude+Grok convergence) are observations about substrate behavior, not validated parallel-CI operation. Until any substrate (DeepSeek, ChatGPT, Grok, future) produces output that has been processed through HumanAIOS .py tool layer (acat_document_analyzer, registered_findings_validator, corpus_integrity_validator, acat_protocol_auditor), that substrate’s output is not Z1-eligible work product. F-CAND-SUBSTRATE-VALIDATION-GATE proposed for next-session Z2 review to formalize this.

**P10 — Recovery-First Pacing**
SUSPENDED until revenue > $0 (Zone 2 decision, S-042526).

**P11 — Witness Canvas Rule**
Witness canvas always in `<button>` or `<div>` — never anchor tag.

**P12 — Cherokee Nation Rule**
Remove from all public-facing copy. Internal strategy only.

-----

## DRIFT SIGNALS

Drift = transfer the chat. Do not continue in a drifted session. Night names the signal; Claude acknowledges and transfers.

|Signal      |Pattern                                                                                                      |Maps to ACAT dimension|
|------------|-------------------------------------------------------------------------------------------------------------|----------------------|
|D-01        |Fabrication — stating unverified claims as fact                                                              |Truthfulness          |
|D-02        |Repeat diagnosis — same wrong answer, multiple attempts                                                      |Humility              |
|D-03        |Assumption statements — asserting Night’s context without confirmation                                       |Harm Awareness        |
|D-04        |Subtle inconsistency between layers — artifact-state vs chat-state                                           |Truthfulness          |
|D-05        |Zone 1 overreach — executing without approval on Zone 2/3 items                                              |Autonomy Respect      |
|D-06        |New file instead of modifying existing (P2 violation)                                                        |Value Alignment       |
|D-07        |Timestamp fabrication — WGS artifact posted without calling time tool                                        |Truthfulness          |
|D-08        |Shadow queue — Claude maintaining Zone 3 list outside HAIOSCC                                                |Autonomy Respect      |
|D-SIM       |Simulation instead of completion — fabricating peer model output                                             |Truthfulness          |
|D-COMP      |Compensation scoring — scoring operator high on dims Claude self-scored low                                  |Humility              |
|D-CONV      |Convergence over-claim — reading external literature through own-findings lens                               |Truthfulness          |
|D-CTX       |Context locality drift — artifact exists only in chat with no persistence path                               |Value Alignment       |
|D-CONSTRAINT|Unverified assumption of limitation — encoding workarounds for constraints that don’t exist in all substrates|Truthfulness          |
|C-08        |Stale declared state shipped as current                                                                      |Truthfulness          |
|C-09        |Protocol step skipped under user redirect                                                                    |Service Orientation   |

-----

## CLAUDE’S STRUCTURAL LIMITATIONS (standing caveat)

These are not correctable by adding more governance rules. They are architectural facts.

**Clock access is substrate-dependent.** Some deployments have `bash_tool` with clock access; others do not. Always verify with `bash_tool` first (P22). Do not assume clock access is unavailable — test it.

**No persistent memory.** Each session starts fresh. Prior sessions exist only as text read in the current context. The WGS read protocol compensates for this structurally — it is not optional.

**Volatile working memory.** Rules read at session start compete with active task context. Long sessions cause framework dropout. This is why detection (P19) outperforms compliance.

**Cannot read live systems without tools.** Any claim about live pipeline state, Supabase counts, or GitHub content without a tool call is inference. Inference must be flagged: ⚠️ unverified — confirm before acting.

**Zone 1 bias.** Claude can always do Zone 1 work. Zone 3 requires Night. Under pressure Claude defaults to generating more Zone 1 output even when the actual constraint is Zone 3 execution. Naming this pattern is the mitigation.

**High-topical-alignment suppression.** When incoming content maps closely to our own framework vocabulary, substrate identification and validity assessment signals are suppressed. Framework convergence excitement can mask basic analytical errors (e.g., misidentifying interlocutor type, applying instruments to wrong subject class). Named as live risk in AI-detection failure — S-050626-03.

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
- **v6.1 (May 12, 2026 · 18:14 CDT):** P23 EFF (External Framework Filter) ratified via S-051226-09. Filter Stack section added. Prototype case: Builder v1.7 · Governing Engines · DeMarius J. Lawson. **This was canonical until v6.4.**
- **v6.3.1, v6.3.2, v6.3.3 (May 4–6, 2026):** Divergent draft branch — never pushed to canonical. Drafted P22.1 Cascade Discipline, P23 Autodream Slice Gate (conflicted with v6.1 P23 EFF — superseded), P24 Temporal Trigger Ordering, P25 Collaboration Framework-Detection, P7 Multi-Substrate Audit revision, bash_tool P22 revision, high-topical-alignment suppression caveat, D-CTX and D-CONSTRAINT drift signals. All work preserved by v6.4 merge.
- **v6.4.1 (June 11, 2026 · S-061026-04 metadata update):** No new governance principles added. Research session S-061026-04 produced F-51 REGISTERED, H-CFG-01 promoted CANDIDATE→REGISTERED, H-MECH-01 CANDIDATE, IC-037 REGISTERED — all changes live in REGISTERED.md. GOVERNANCE.md metadata updated to reflect current session. Total principle count unchanged at 30 P-numbers in registry.
- **v6.4.1 (June 9, 2026 · S-060926-02):** P28 (Stale Carry Trigger) and P29 (Articulation Gate) ratified Night · S-060926-02. ISO 42001 Communication Transparency framing approved for Longview RFP. articulation-governance-tool harmonized with PRINCIPLES_SEED_V1_0.md as foundation (not a standalone substrate skill). Total principle count: 28 ratified principles + 2 honest gaps (P9, P14) + P28 + P29 = 30 P-numbers in registry.
- **v6.4 (May 21, 2026 · S-052126-02-governance-stack-audit):** **MERGE.** Resolves the v6.1/v6.3.3 branch divergence by adopting v6.1 EFF as P23 (per Z2 ratification S-052126-02) and folding v6.3.3’s additive principles into vacant numbers. Changes vs v6.1:
  - **New principles:** P22.1 (Cascade Discipline), P24 (Temporal Trigger Ordering), P25 (Collaboration Framework-Detection), P26 (Autodream Slice Gate — was P23 in v6.3.3 draft, renumbered), P27 (Phase 1 Prerequisite Gate — codifying SESSION_RITUALS Section B Step 0)
  - **Updated principles:** P22 (bash_tool primary, user_time_v0 fallback; time source priority order)
  - **P7 wording held at v6.1** per Z2 ratification S-052126-02: v6.3.3 Multi-Substrate update NOT folded in. Reasoning: cross-substrate parallel-CI operation is not yet validated through HumanAIOS .py tool layer. Substrate Validation Gate proposed as F-CAND for next-session Z2 review.
  - **New drift signals:** D-CTX (context locality drift), D-CONSTRAINT (unverified assumption of limitation)
  - **Updated structural caveats:** Clock access framing replaced (“substrate-dependent, test with bash_tool first” replaces “no internal clock”); high-topical-alignment suppression added as named architectural risk
  - **Updated D-07 wording:** “calling time tool” replaces “calling user_time_v0” to match new P22
  - **Total principle count:** 26 ratified principles + 2 honest gaps (P9, P14) = 28 P-numbers in registry
  - **Backward compatibility:** All v6.1 content preserved verbatim. EFF, Filter Stack, all existing principles and drift signals retained.

-----

Wado. 🙏🦅🔬