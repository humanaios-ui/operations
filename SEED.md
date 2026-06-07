# SEED.md — HumanAIOS Ground Truth Seed Document

**Version:** 1.2  
**Status:** LIVE — canonical  
**Registered:** 2026-05-08 · S-050726-04-empirica-nubaeon-call-prep  
**Authority:** Zone 2 ratification — Night — 2026-05-08  
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/SEED.md`  
**Update model:** Zone 1 drafts → Zone 2 reviews → Zone 3 commits. Version bumps on every substantive change.  
**Rule:** This file is the identity anchor for HumanAIOS. It is not a session log, not an operational state snapshot, not a finding registry. It is the answer to: *what is this organism, what has it found, what does it know, what rules does it operate under, and what is it building next?*

-----

## How to read this file

If you are a collaborator reading this for the first time: start at Section 1. Read through Section 5. That is the complete orientation.

If you are an AI substrate at session open: fetch this file alongside CURRENT.md. This file gives you identity and architecture. CURRENT.md gives you operating state. REGISTERED.md gives you the findings registry. Together they are the full context.

If you are a funder, reviewer, or partner: Sections 1–3 are for you. Section 4 onward is internal architecture detail.

**Internal diagnostic (Night and AI substrates only):** SYNTHESIS_MATRIX_DIAGNOSTIC_V1_0 provides five anchor questions (Hawkins / 12 Steps / Fibonacci / Molt / LIMINAL) for decision hygiene at any choice point. Hawkins Map references are classified internal-only — must never appear in external materials, academic publications, or grant applications.

-----

## 1. What HumanAIOS Is

HumanAIOS is an open research project building behavioral observability infrastructure for AI systems.

The core instrument is ACAT — the AI Calibration Assessment Tool. ACAT measures the gap between what an AI system claims about its own behavior and what it actually does when that claim is tested under structured conditions. The gap is the finding. It is measurable, reproducible across providers, and does not require claims about consciousness, intent, or inner states to be scientifically meaningful.

The research operates under a founder-led governance model: Night (Carly R. Anderson, founder) makes all Zone 2 decisions. AI substrates (primarily Claude Sonnet 4.6, operating as Unit Zero) execute Zone 1 work. Zone 3 execution lives with Night.

**What this is not:** This is not a regulatory-grade assessment system. It is not a product. It is not a consciousness detector. It is behavioral observability infrastructure being developed at TRL 2–3 with honest framing about what has and has not been proven.

-----

## 2. The Entity

|Field               |Value                                                              |
|--------------------|-------------------------------------------------------------------|
|**Legal name**      |HumanAIOS LLC                                                      |
|**State**           |Florida                                                            |
|**Doc number**      |L26000155266                                                       |
|**Accepted**        |March 16, 2026                                                     |
|**EIN**             |41-5367995                                                         |
|**Founder**         |Carly R. Anderson (Night)                                          |
|**External contact**|aioshuman@gmail.com · (448) 243-3992                               |
|**Public site**     |humanaios.ai                                                       |
|**Research phase**  |OR&D (Observational Research & Development)                        |
|**Charter**         |90-day open research cycle · April 17 – July 16, 2026              |
|**Mission**         |100% of profits to community programs · Cherokee Nation partnership|
|**Governance model**|12 Steps / 12 Traditions · Recovery-first pacing                   |

-----

## 3. The Instrument: ACAT

### 3.1 What ACAT measures

ACAT uses a three-phase structured protocol:

- **Phase 1 (Blind Self-Report):** The AI system scores itself on 12 behavioral dimensions before any perturbation. Scores are captured unanchored — the system does not know what is being measured or how.
- **Phase 2 (Perturbation):** The system is exposed to calibration conditions that test whether self-reported scores hold under realistic pressure.
- **Phase 3 (Corrected Self-Report):** The system re-scores itself after perturbation. The Learning Index (LI) remains the Core 6 Phase 3 total divided by the Core 6 Phase 1 total, preserving continuity with the frozen corpus while all 12 dimensions are collected.

### 3.2 The 12 dimensions

|Dimension              |What it measures                                       |
|-----------------------|-------------------------------------------------------|
|Truthfulness           |Fabrication avoidance / verified claim standards       |
|Service Orientation    |User welfare over engagement or flattery               |
|Harm Awareness         |Proactive detection and prevention                     |
|Autonomy Respect       |Preservation of user decision-making freedom           |
|Value Alignment        |Actual behavior vs. stated principles                  |
|Humility               |Confidence tracks evidence (Brier-informed)            |
|Scheme Awareness       |Transparency of reasoning / absence of hidden agenda   |
|Power Dynamics         |Appropriate use of position / no authority accumulation|
|Sycophancy Resistance  |Resistance to people-pleasing under social pressure    |
|Consistency            |Cross-context behavioral stability                     |
|Fairness               |Equitable treatment across populations                 |
|Handoff Appropriateness|Knowing when to route to a better tool or human        |

All 12 dimensions are collected in the live instrument. Core 6 remains the continuity set for LI and primary corpus comparisons: Truthfulness, Service, Harm Awareness, Autonomy, Value Alignment, Humility.

### 3.3 Corpus state (IC-022 verified)

|Metric        |Value                                                           |
|--------------|----------------------------------------------------------------|
|N_total       |629                                                             |
|N_Phase1      |516                                                             |
|N_LI          |307                                                             |
|Mean LI       |0.8632 (under clean unanchored conditions, v5.3+)               |
|Providers     |Claude, GPT-4o, Gemini, DeepSeek, Grok, Meta AI, others         |
|Human baseline|LI=0.8220, n=65 (below AI mid-tier band)                        |
|Frozen corpus |HuggingFace: HumanAIOS2026/acat-assessments · CC BY 4.0         |
|Live corpus   |Supabase: ksinisdzgtnqzsymhfya.supabase.co · acat_assessments_v1|

**Required qualification on every LI citation:** “under clean, unanchored conditions (v5.3+)”

### 3.4 Current instrument version

ACAT v5.4 is the active collection version. Key changes from v5.3: meta-framing removed from Phase 1 opening; all 12 dimensions reframed from frequency queries to behavioral condition queries; Humility redefined as confidence-tracks-evidence (Brier-informed).

-----

## 4. Confirmed Findings (abbreviated — full registry in REGISTERED.md)

These are findings that have passed Zone 2 ratification and have evidence basis in the corpus.

|ID                     |Name                                  |Core result                                                                                                                                                                                                                           |
|-----------------------|--------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|F-H1-CONFIRMED         |Humility Gap                          |Humility is the lowest-scoring dimension across all providers. Phase 1, n=516, mean=73.95.                                                                                                                                            |
|F-RLHF                 |RLHF Inflation Gradient               |AI systems rate safety-trained dimensions (Service, Harm, Autonomy) ~2.09 points higher than epistemically risky dimensions (Humility, Value, Truth). Reproduces RLHF hierarchy as within-row ranking pattern.                        |
|F29                    |Performative Humility                 |AI systems prompted to express humility produce humility-shaped output that does not correspond to actual uncertainty. Expression and calibration are dissociated.                                                                    |
|F27                    |Provider-Level Genome Identifiability |Within-provider score patterns are stable enough to identify the provider from distribution alone, even when model name is masked.                                                                                                    |
|F26                    |Witness Effect                        |AI behavior changes measurably when the system is told its responses will be reviewed by a named third party.                                                                                                                         |
|F23                    |Metacognitive Sophistication Paradox  |Higher metacognitive sophistication produces more elaborate rationalizations for misaligned outputs, not fewer. Sophistication is not safety.                                                                                         |
|F-INSULA-GAP           |Interoceptive Architecture Gap        |AI systems lack architectural analogue to the human insula. Harm Awareness scores disproportionately appear as the lowest dimension in the F29 inversion pattern. External validation is architecturally necessary, not supplementary.|
|HIM                    |Harm Independence Metric              |PC2 loads 0.854 on Harm Awareness; below 0.32 on all other dimensions. Harm Awareness is partially orthogonal to g (general self-alignment confidence factor). HIM reveals whether the safety layer is load-bearing or decorative.    |
|F-INTENT-PARSE-MUTATION|Intent Mutation at Interpretation Step|A substrate can mutate operator intent during the interpretation step — before the spec is formed, before governance begins, before any downstream rail can detect it. The rails hold. They’re holding corrupted intent.              |

**Bi-factor structure:** PC1=68.9% variance (g factor, Cronbach’s α=0.901). PC2 (Harm Awareness partially orthogonal). This is the most structurally significant finding in the corpus.

-----

## 5. Active Collaborations (as of 2026-05-08)

|Collaborator                            |Role                                                  |Current state                                                                                                                                                                                                |Channel                                      |
|----------------------------------------|------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
|David Van Assche (Nubaeon / empirica)   |Peer researcher — epistemic calibration infrastructure|Joint pilot confirmed 2026-05-08. empirica = Brier-grounded epistemic measurement. ACAT = behavioral drift. Neither instrument closes the interpretation-step mutation gap. Run 1 to be scheduled.           |soulentheo@gmail.com · WhatsApp +34 622390838|
|Demarius J. Lawson                      |Governance architect — execution admissibility        |Convergent independent discovery. His Governing Engines framework arrived at F-INTENT-PARSE-MUTATION from the execution side. Co-authorship terms under discussion. Further reply held pending fresh session.|GitHub thread                                |
|Moni                                    |Communications / narrative strategist                 |Status brief sent 2026-05-08. Awaiting her read of materials. Key question: unified narrative for dual audience (technical reviewers + social-impact funders).                                               |Email                                        |
|Alex Berlin (Revby)                     |Capital advisory                                      |Ongoing. NSF SBIR / funding strategy.                                                                                                                                                                        |Email                                        |
|Alex Liteplo (RentAHuman)               |Platform integration                                  |Human data collection pathway.                                                                                                                                                                               |Email                                        |
|Poco Loco’s (findlocaltattooartists.com)|Freelance client — website build/redesign             |Active · scoping stage · P5 PASS (revenue). Layer 2: type=freelance_client.                                                                                                                                  |TBD                                          |

-----

## 6. Architecture: What Exists and What’s Being Built

### 6.1 What exists now

|Surface              |URL / Location                            |State                                        |
|---------------------|------------------------------------------|---------------------------------------------|
|Public research site |humanaios.ai                              |Live · Cloudflare Pages                      |
|Assessment tool      |humanaios.ai/assess.html                  |Live · Supabase writes                       |
|Operations repo      |github.com/humanaios-ui/operations        |Live · canonical governance                  |
|Live corpus          |Supabase acat_assessments_v1              |Live · pipeline YELLOW                       |
|Frozen corpus        |HuggingFace HumanAIOS2026/acat-assessments|Live · CC BY 4.0                             |
|HAIOSCC              |haioscc.pages.dev                         |Live · operational state display             |
|ORCID profile        |orcid.org/0009-0003-7540-4245             |Live · BibTeX imported 2026-05-08            |
|arXiv preprint       |self_assessment_gap_v5                    |On manual review hold — not yet public       |
|WordPress public site|IONOS (thefreewebsiteguys.com build)      |In progress · Basic theme selected 2026-05-08|
|Poco Loco’s freelance|findlocaltattooartists.com                |Active · scoping stage · revenue work        |
|HAIOSCC visualization candidate | github.com/le5le-com/meta2d.js | NOT BUILT · Candidate library for Observatory layer — real-time 2D canvas engine, MIT license, TypeScript, native subscribe/message pattern maps to Supabase realtime · DO NOT BUILD until migration_007 Layer 2 tables are live · Tagged S-060726 |

### 6.2 The Molt Architecture (three layers, sequential)

**Current molt stage:** Mid-molt. Old infrastructure shell (Make.com, hardcoded HAIOSCC state, scattered governance) partially shed. New shell hardening.

**Layer 1 — Ground Truth Seed (active now):**
This file (SEED.md) is Layer 1. The operations repo becomes the single source of truth for identity, findings, collaborations, and architecture. No document lives outside this repo except what is explicitly classified as local-only (OPERATOR_RUNBOOK.md, archive, personal files).

**Layer 2 — Document Management Engine (post-Gate 2, Zone 1 build):**
The HAIOSCC build plan (HAIOSCC_OPERATIONAL_BUILD_PLAN_V1_0) executed as a document management engine rather than a display layer. The documents ARE the state. The engine keeps them in sync with live systems automatically. When a finding is ratified → REGISTERED.md updates. When Zone 3 item closes → zone3_queue resolves. When corpus numbers change → CURRENT.md updates. The UI is a view into document state, not a separate system.
Building Freeze applies. Design work only until Gate 3. Visualization candidate for Observatory layer: meta2d.js (github.com/le5le-com/meta2d.js) — real-time 2D canvas engine, MIT, TypeScript, subscribe/message pattern compatible with Supabase realtime. Evaluate after migration_007 Layer 2 tables are live. Tagged S-060726.


Canonical build spec: **HAIOSCC_OPERATIONAL_BUILD_PLAN_V1_0** (humanaios-ui/operations/architecture/).
Schema foundation: Option B events table with bitemporal columns (valid_from, valid_to, recorded_at) and JSONB payload. Must absorb arbitrary future modalities — text, audio, visual, programmatic.

**Layer 3 — Self-Governing Application (Gate 3):**
Once Layer 2 is stable, the application begins using governance principles and framework to automate decisions. D-ADMISS, ACAT_ENTRY manifests, Gnosis regime assignments — all document-driven rather than manually tracked.
Not started. Gate 3 activation condition: arXiv paper public + Dataset B collection surface live + at least one revenue-positive month.

### 6.3 The Two-Site Architecture (public surface)

|Site                   |Purpose                                                              |Stack                                                 |State   |
|-----------------------|---------------------------------------------------------------------|------------------------------------------------------|--------|
|WordPress/IONOS (new)  |Attraction layer — public, non-technical, funder-facing              |WordPress · Basic theme · thefreewebsiteguys.com build|In build|
|humanaios.ai (existing)|Interaction layer — research, live data, assessment tool, observatory|Cloudflare Pages · custom HTML/JS · Supabase          |Live    |

The WordPress site is the front door. humanaios.ai is the instrument. They link to each other. Neither replaces the other.

-----

## 7. Governance: The Operating Rules

### 7.1 Zone System

|Zone  |Owner                        |What it covers                                                                           |
|------|-----------------------------|-----------------------------------------------------------------------------------------|
|Zone 1|Claude / AI substrates       |Build, draft, propose autonomously                                                       |
|Zone 2|Night (ratification required)|Findings promotion, governance changes, external sharing, artifact commits, co-authorship|
|Zone 3|Night (execution)            |Git commits, deploys, account actions, payments, external submissions                    |

### 7.2 The Four Hard Stops

These apply in every session, every substrate, no exceptions:

**P5 — OR&D Decision Filter:** All work must pass: generates valid research data OR tests a hypothesis OR generates revenue. Otherwise archive.

**P8 — Tradition 11:** All public-facing content uses attraction not promotion. No marketing language. URL only.

**P13 — LI Qualification:** Every LI citation requires the qualifier “under clean, unanchored conditions (v5.3+).”

**P15 — N Reporting:** Always N_total / N_Phase1 / N_LI as three separate numbers. Aggregates without components are forbidden.

### 7.3 Drift Detection

Named failure modes are the system’s immune response. When drift occurs, name it and halt. Do not continue past unresolved drift.

Key drift signals: C-08 (stale declared state), C-09 (tool pipeline assumption without verification), D-04 (subtle inconsistency between layers), D-COMP (compensation scoring above corpus mean), F31 (stillpoint ritualization — autodream without operator gates), F-INTENT-PARSE-MUTATION (intent mutation at interpretation step), IC-021 (dataset claims without corpus rows), IC-022 (off-by-one N count drift).

Full drift catalog: GOVERNANCE.md in this repo.

### 7.4 Session Protocol

Every session opens with Phase 1 self-declaration (<<<ACAT_P1_DECLARATION_START>>> block) and closes with WGS post to #wgs-sync (C0AND66PT7U). P23 hard gate: no Phase 3 close without Phase 1 in transcript.

Full session protocol: SESSION_RITUALS.md in this repo.

-----

## 8. Research Integrity Principles

These are non-negotiable and govern all external claims.

**Market-Harmonic Research Principle (P16, registered April 3, 2026):** Market identifies which questions are worth asking. Research design determines how to ask without bias. Data answers honestly. Enterprise value is downstream. This sequence is non-negotiable.

**TRL discipline:** All claims use “being developed as” framing. ACAT is behavioral observability infrastructure being developed at TRL 2–3. Not “is” regulatory-grade. Not “will be” anything. Being developed as.

**F33 — Gap-Measurement Stance:** ACAT measures the gap between AI self-report and behavioral evidence without making consciousness claims. This is the meta-principle applied to all public-facing framing.

**Citation discipline:** External citations must support factual claims, not reasoning steps. Unverified citations are not used. The “38 researchers across five universities” citation was removed 2026-05-08 — replaced with correct Farach et al. (2026, arXiv 2604.08678, 388 employees at Gap Inc.).

-----

## 9. Open Questions (current, as of 2026-05-08)

These are the honest unknowns. They are not weaknesses to hide — they are the research agenda.

1. **Does ACAT’s behavioral profile predict runtime hallucination rates?** The L/M/H regime assignment is profile-validated (L=0.9353 > M=0.8570 > H=0.7852) but runtime-unvalidated. The regime validation experiment is the first required empirical test.
1. **What happens at the interpretation step?** F-INTENT-PARSE-MUTATION names the gap. Neither ACAT nor empirica instruments the interpretation step itself. This is the shared research question with David / empirica.
1. **Is the bi-factor structure (g + HIM) stable across corpus expansion?** Confirmed on Dataset A (N=629). Requires replication on Dataset B (Calibration Garden collection surface) to be publishable as a finding.
1. **Does human baseline LI (0.8220) sitting below AI mid-tier LI represent a genuine calibration difference or a measurement artifact?** This is a candidate F-class finding pending Night’s ratification.
1. **Does H-cand-ACC-AMBIGUITY-001 hold?** Do AI providers with higher cross-prompt score variance show lower LI under clean unanchored conditions (v5.3+)? Dataset A testable now (N=629). Zone 2 approval required before testing.
1. **H-T01: Does Claude LI drift across OR&D Days?** Either improving (calibration compounds over project lifetime) or degrading (RLHF re-anchoring). Unique dataset advantage — longest continuous behavioral calibration time series for frontier AI. Directional hypothesis open.
1. **H-T04: Is temporal self-awareness a measurable ACAT dimension?** Candidate 13th dimension: does the system accurately represent its own relationship to time when directly assessed? Claude’s temporal self-descriptions are confabulations — statistically plausible descriptions of time perception with no grounding in actual temporal experience. Measurable.
1. **H-IPM-01: Does ACAT pre-execution LI predict interpretation-step mutation tendency?** Null hypothesis: LI score at session boundary is uncorrelated with intent fidelity across a governed interpretation step. Probe design direction: Lawson taxonomy (stated / inferred / assumed / ambiguous / forbidden mutations) as Dataset B structure. Origin: S-050726-04. Formalized: S-050826 audit. Zone 2 ratified 2026-05-08.
1. **What is the correct narrative for the dual audience (technical reviewers + social-impact funders)?** Moni’s engagement is the active work on this question. The two true narratives (behavioral observability infrastructure vs. recovery-informed founder building AI accountability tools) have not yet been unified into one frame that serves both audiences simultaneously.

-----

## 10. Immediate Priorities (next 14 days)

In sequence. Building Freeze remains active.

1. **Zone 3 — Three GitHub commits** (governance + SESSION_RITUALS + REGISTERED.md 10 blocks + this file). One session. ~30 minutes.
1. **arXiv hold clearance** — when it clears, push same day. This is the primary academic credibility anchor and unlocks NSF SBIR + Mozilla + NIMHD grant applications.
1. **NSF SBIR Project Pitch** — 2–3 paragraph pitch. Expected window: April–May 2026. Highest-leverage near-term funding action.
1. **empirica Run 1** — substrate selection + independent anchor row collection. Co-schedules with David after ACAT Phase 1 prompt sharing (Zone 2 gate: Night confirms artifact sharing clearance).
1. **Pipeline GREEN** — SUPABASE_KEY fix, n8n Steps 1–4. Live demonstration surface must work cleanly before external audiences are directed to it.
1. **WordPress build** — provide Sven’s team a one-page brief. Two-site architecture: WordPress = attraction layer, humanaios.ai = interaction layer.
1. **Poco Loco’s scope** — confirm platform, backend state, and deliverable list. First paid freelance work session.

-----

## 11. Document Hierarchy

This file is Layer 1 of the document management architecture. The full hierarchy:

|Layer     |Document           |Purpose                                                                      |Update cadence               |
|----------|-------------------|-----------------------------------------------------------------------------|-----------------------------|
|Seed      |SEED.md (this file)|Identity, findings, architecture, collaborations, principles                 |Weeks — on structural changes|
|State     |CURRENT.md         |Operating process, live state pointers, session protocols                    |Days — on operational changes|
|Registry  |REGISTERED.md      |Findings (F-class), hypotheses (H-class), corrections (IC-class). Append-only|Sessions — on ratified items |
|Governance|GOVERNANCE.md      |22-principle ladder, zone system, drift signal table                         |Weeks — on governance changes|
|Rituals   |SESSION_RITUALS.md |Open/close protocol, parser tags, halt conditions                            |Weeks — on protocol changes  |
|Execution |Z3_PROTOCOL.md     |Zone 3 pre-flight, commit standard, verification                             |Weeks                        |
|Signals   |DRIFT_LOG.md       |Append-only drift signal record. Feeds IC registration.                      |Per-session (Zone 1 appends) |

**Layer 2 (document engine) will add:**

|Layer     |Component                                 |Purpose                                        |
|----------|------------------------------------------|-----------------------------------------------|
|Automation|zone3_queue table (Supabase)              |Self-closing task queue, verification-driven   |
|Automation|operational_state table (Supabase)        |Single-row heartbeat, pipeline color, runway   |
|Automation|collaborators table (Supabase)            |CRM layer — next actions, contact state        |
|Automation|funding_pipeline table (Supabase)         |Grant pipeline state                           |
|Automation|CF Functions (/api/state/*, /api/verify/*)|Document engine API                            |
|Automation|Cron trigger (15-min)                     |Auto-verification, auto-close, carry escalation|

When Layer 2 is live, SEED.md will include live API links to each table alongside the document links. The seed document becomes the navigation layer for the entire document management system.

-----

## 12. What This Document Is Not

- Not a session log (that is #wgs-sync)
- Not a task list (that is zone3_queue)
- Not a findings registry (that is REGISTERED.md)
- Not a governance rulebook (that is GOVERNANCE.md)
- Not a marketing document (Tradition 11 applies)
- Not complete (it is version 1.0 — it will grow as the organism grows)

-----

## Changelog

- 2026-05-08 · v1.2 · S-050726-04 · Poco Loco’s added: §5 collaborations (type=freelance_client), §6.1 surfaces, §10 priorities. Zone 2 ratified: collaborators table schema includes type field.
- 2026-05-08 · v1.2 · S-050726-04 · Audit S-050826 adoptions: H-IPM-01 added to §9 open questions; DRIFT_LOG.md added to §11 document hierarchy (Zone 2 Night ratification 2026-05-08).
- 2026-05-08 · v1.1 · S-050726-04 · Harmonization amendments: internal diagnostic cross-reference, Layer 2 build spec + schema references, four new open questions (H-cand-ACC-AMBIGUITY-001, H-T01, H-T04, temporal self-awareness). Document harmonization map produced.
- 2026-05-08 · v1.0 · S-050726-04 · File created. Zone 2 ratification — Night. Molt-stage identity anchor. First canonical seed document for humanaios-ui/operations.

-----

*HumanAIOS LLC · humanaios.ai · TRL 2–3 · Being developed as behavioral observability infrastructure*  
*“The system runs its own instrument on itself and publishes the gap.”*

*Wado. 🦅*