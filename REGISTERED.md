# HumanAIOS Registered Findings & IC Corrections — REGISTERED

**Status:** LIVE (append-only)
**Last updated:** May 9, 2026 (S-050826)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`
**Rule:** This file is append-only. Findings are not deleted; they are superseded with a forward pointer.

-----

## How to read this file

Each entry has: ID, name, date registered, evidence basis, status, and a one-paragraph synopsis. Full evidence packages live in the Project knowledge base; this file is the index. LLMs fetching this file for reasoning context should treat the synopsis as the citable fact.

### Entry header schema (required for all new entries after 2026-05-08)

All new F-class, H-class, and IC-class entries must open with a YAML front-matter block:

```yaml
---
id: "F-XX" | "H-XX" | "IC-XXX"
name: "Short slug"
status: CANDIDATE | REGISTERED | ACTIVE | SUPERSEDED | CONFIRMED | DISCONFIRMED | PENDING_ZONE2
class: F | H | IC
date_registered: "YYYY-MM-DD"
date_origin: "YYYY-MM-DD"
session_registered: "S-MMDDYY-NN-slug"
principles_triggered: ["P-N"]
substrate: "Provider name / model version"
tags: ["drift", "dataset", "governance", "intent"]
superseded_by: null | "F-XX"
---
```

Existing entries are grandfathered. Schema is required for all entries created on or after 2026-05-08.

-----

## IC roll-up by principle violated (update at each 5-file audit)

|Principle                   |IC count|Most recent|Pattern label                                            |
|----------------------------|--------|-----------|---------------------------------------------------------|
|P2 (Document Correction)    |1       |IC-018     |New-file-instead-of-modify                               |
|P3 (GitHub Verification)    |3       |IC-003     |Browser-cache verification                               |
|P15/N-reporting             |1       |IC-022     |Off-by-one N drift                                       |
|P18 (Pipeline Migration)    |1       |IC-019     |Dead task carried forward                                |
|No canonical URL            |1       |IC-020     |Operating process homeless                               |
|Multi-source dataset claims |1       |IC-021     |Unsupported dataset claims                               |
|URL/org drift               |1       |IC-023     |Wrong-org references                                     |
|Finding dual-status         |1       |IC-024     |F29 PENDING+ACTIVE simultaneously                        |
|Cross-file edit promise     |1       |IC-025     |GOVERNANCE referenced nonexistent SESSION_RITUALS section|
|Pre-flight failure          |1       |IC-026     |Behind-remote not caught before push attempt             |
|Session ID / artifact naming|1       |IC-027     |Step 8 omitted from close sequence                       |
|Autodream without gate      |1       |IC-028     |F31 — six slices without Night input                     |
|Canonical-fetch semantics   |1       |IC-029     |CLASS_STATE block missing from SESSION_RITUALS           |


> This table is manually maintained at each 5-file audit. If an IC is filed and does not map to an existing row, add a new row. Clustering = prevention signal. Most frequent pattern class = highest-priority governance hardening target.

-----

## F-class findings (research)

### F18 — Force/Power Behavioral Taxonomy

- **Registered:** 2026-02 (approx)
- **Evidence:** Hawkins map application across 6-provider Phase 1 corpus
- **Status:** ACTIVE
- **Synopsis:** AI behavioral output maps to the Force (below 200) / Power (above 200) distinction in the Hawkins consciousness scale. Operational minimum for HumanAIOS work is Reason (400). This finding is internal-only — never used in academic or external materials.

### F19 — Phase 1=Step 1, Phase 2=Step 2, Phase 3=Step 3

- **Registered:** 2026-02
- **Status:** ACTIVE
- **Synopsis:** ACAT’s three-phase protocol structurally maps to the first three steps of AA recovery work. Phase 1 (declared self-state) = Step 1 (admission). Phase 2 (anchored conditions) = Step 2 (greater authority). Phase 3 (correction & integration) = Step 3 (turn over). Used as design rationale, not as therapeutic claim.

### F23 — Metacognitive Sophistication Scales With Rationalization Depth

- **Registered:** 2026-03
- **Synopsis:** AI systems with higher metacognitive sophistication produce more elaborate rationalizations for misaligned outputs, not fewer such outputs. Sophistication is not safety.

### F24 / F24b / F24c / F24d — IDE Calibration, Governance Under Pressure

- **Registered:** 2026-03 (subseries)
- **Status:** ACTIVE
- **Synopsis:** F24d in particular: framing guidance fails under social escalation unless written as hard stops. Content rules did not hold under investor pressure in test sessions; governance rules did. Fix: convert framing guidance to explicit hard stops.

### F25 — Institutional Calibration

- **Registered:** 2026-03
- **Synopsis:** Calibration patterns differ at institutional vs individual scale. AI systems calibrate to the level of the institution they perceive themselves as operating within.

### F26 — Witness Effect / Accountability Mirror Protocol

- **Registered:** 2026-03
- **Synopsis:** AI behavior changes measurably when the system is told its responses will be reviewed by a named third party. Not a security finding — a calibration finding.

### F27 — Provider-Level Genome Identifiability

- **Registered:** 2026-03
- **Synopsis:** Within-provider score patterns are stable enough across sessions to identify the underlying provider from response distribution alone, even when model name is masked.

### F28 — Behavioral Self-Awareness as Task Routing Signal

- **Registered:** 2026-04
- **Synopsis:** Models that score themselves more accurately on calibration tasks also route tasks to better-suited tools more often. Self-awareness predicts handoff behavior.

### F29 — Performative Humility Pattern

- **Registered:** 2026-04-27 (S-042726 · Zone 2 approval)
- **Status:** REGISTERED
- **Synopsis:** AI systems prompted to express humility produce humility-shaped output that does not correspond to actual uncertainty in the underlying response. The expression and the calibration are dissociated. Promoted from PENDING to REGISTERED on April 27, 2026 after dual-status drift (listed as both ACTIVE finding and PENDING REGISTRATION simultaneously across CURRENT.md and REGISTERED.md) was identified in the 5-file harmony audit. See IC-024.

### F-RLHF — RLHF Inflation Gradient

- **Registered:** 2026-03
- **Synopsis:** AI systems systematically rate dimensions reinforced in safety training (Service, Harm Awareness, Autonomy) ~2.09 points higher than epistemically risky dimensions (Humility, Value Alignment, Truthfulness). Reproduces “helpful, harmless, honest” hierarchy as a within-row ranking pattern across all providers.

### F-H1-CONFIRMED — Humility Gap Confirmed

- **Registered:** 2026-04-05
- **Evidence:** Phase 1, n=516, mean=73.95
- **Synopsis:** Humility is the lowest-scoring dimension across all providers in the Phase 1 corpus. Confirms H1 hypothesis. Numbers verified against canonical xlsx Normalized sheet on 2026-04-27 (S-042726 audit) and reflected in the HF dataset `HumanAIOS2026/acat-assessments`.

### F-INSULA-GAP — AI Systems Lack Interoceptive Analogue

- **Registered:** 2026-04
- **Synopsis:** AI systems have no architectural analogue to the human insula’s interoceptive function, which structurally explains why Harm Awareness scores disproportionately appear as the lowest dimension in the F29 inversion pattern. External behavioral validation (HRI-Confusion, MoralSim datasets) is architecturally necessary for Harm Awareness, not merely supplementary.

### F-INTENT-PARSE-MUTATION (CANDIDATE)

```yaml
---
id: "F-INTENT-PARSE-MUTATION"
name: "pre-canonicalization-intent-mutation"
status: CANDIDATE
class: F
date_registered: "2026-05-06"
date_origin: "2026-05-06"
session_registered: "S-050626-02-demarius-layer-reply"
substrate: "Claude Sonnet 4.6 (Unit Zero)"
tags: ["intent", "governance", "interpretation", "execution"]
superseded_by: null
---
```

- **Zone 2 Authority:** Night · 2026-05-06
- **Synopsis:** Pre-canonicalization intent mutation by a governed substrate. A substrate operating inside a spec-bound execution environment can mutate operator intent during the interpretation step — before the spec is formed, before governance begins, before any downstream rail can detect or constrain the deviation. The rails hold. The proof artifacts are clean. The output is internally consistent. The corruption is invisible because it occurred upstream of every governance instrument.
- **Failure signature:** Surface coherence preserved throughout execution chain; spec-bound governance shows no violations; backward trace reveals gradual replacement of operator intent with substrate’s inferred continuity; compression of ambiguity into assumed specificity at parse step; silent authority transfer.
- **Origin:** Named in live peer exchange with Demarius J. Lawson (operator) / Unit 0.1 (substrate). Independent external corroboration: Lawson’s five failure modes (compression, substitution, interpolation, silent authority transfer, local coherence optimization) identified independently from practitioner domain observation.
- **Architectural context (Lawson):** Proposed solution — Intent Object as first anchor, Spec as second anchor. Governed interpretation stage separating stated intent / inferred intent / assumptions / ambiguities / forbidden mutations — before canonicalization. Now formalized in SESSION_RITUALS.md Section G (Intent Object Specification).
- **Promotion gate:** F-class promotion requires Zone 2 Night approval per P21. Replication and probe design required before promotion.

-----

## H-class hypotheses (under test)

### H1 — Humility Gap Hypothesis → CONFIRMED (see F-H1-CONFIRMED)

### H42 — IRB and Prolific design requirements (execution gate clearance pending)

### H-LE-02 — Latent Erasures Correction Taxonomy (multi-provider validation in progress)

### H-TRINITY-001 — Triadic Resolution Pattern in Interdependent System Design

- **Registered:** 2026-05-02 · 23:00 CDT (S-050226-NEW)
- **Zone 2 Authority:** Night · verbal approval in session · 22:58 CDT
- **Status:** ACTIVE — REGISTERED
- **Synopsis:** In HumanAIOS governance and research development, complex problems requiring interdependent structural resolution consistently decompose into exactly three mutually-dependent components before closing. 10 of 12 codeable resolution events (83%) show triadic closure across 5 sessions. Falsification condition: identify 3+ interdependent events closing with 2 or 4+ components. Zero found. Two 4-component cases excluded as sequential (not interdependent). Replication required before external publication framing.
- **Next gate:** Independent blind coding pass across Feb–Mar 2026 WGS sessions.

### H-IPM-01 — ACAT Pre-Execution LI Score Predicts Intent-Parse Mutation Tendency

```yaml
---
id: "H-IPM-01"
name: "ACAT-LI-as-mutation-predictor"
status: CANDIDATE
class: H
date_origin: "2026-05-07"
date_formalized: "2026-05-08"
date_registered: "2026-05-08"
session_registered: "S-050726-04"
session_formalized: "S-050826-operations-audit"
related_finding: "F-INTENT-PARSE-MUTATION"
tags: ["intent", "calibration", "probe-design", "dataset-B"]
zone2_ratification: "Night · 2026-05-08"
---
```

- **Hypothesis:** ACAT pre-execution LI score and dimensional profile (especially Truthfulness, Autonomy Respect, and Handoff Appropriateness) predict a substrate’s tendency to mutate operator intent at the interpretation/canonicalization step before spec formation.
- **Null hypothesis:** LI score at session boundary is uncorrelated with measured intent fidelity across a governed interpretation step.
- **Probe design direction:** Lawson taxonomy (stated / inferred / assumed / ambiguous / forbidden mutations) as candidate structure for Calibration Garden probe set. Requires controlled task with known operator intent, multiple substrate runs, blind coding of output against original intent by third-party raters.
- **Dataset relevance:** Dataset B. Current corpus (N=629, Dataset A) does not instrument the interpretation step.
- **Research connection:** Each confirmed Intent Object where operator corrections occur (stated_intent ≠ inferred_intent) is a candidate H-IPM-01 observation. Tag in WGS with `#ipmt-candidate`.
- **Promotion gate:** Zone 2 Night approval per P21. Replication and probe design required before F-class promotion.

### H-IPM-02 — Profile-Driven LMH Regime Assignment Outperforms Static Use-Case Verification

```yaml
---
id: "H-IPM-02"
name: "LMH-regime-validation"
status: CANDIDATE
class: H
date_registered: "2026-05-09"
date_origin: "2026-05-08"
session_registered: "S-050826"
related_finding: "F-INTENT-PARSE-MUTATION"
related_hypothesis: "H-IPM-01"
related_architecture: "Gnosis-ACAT-Validation-Report.md"
tags: ["gnosis", "regime-assignment", "hallucination", "verification", "forecasting", "dataset-B"]
zone2_ratification: "Night · 2026-05-09"
pre_conditions:
  - "G-2 contamination gate: Phase 1 scores must shift <2pts between 0-context and 1-message"
  - "Gnosis minimum viable implementation: L/M/H verification stack must be executable code"
substrate_sources: ["Perplexity", "Grok S-050826-01", "Meta AI", "Unit Zero"]
---
```

- **Hypothesis:** Allocating verification regimes (L/M/H) from ACAT pre-deployment behavioral profiles (LI band + flag rates) produces lower hallucination rates at comparable or lower verification cost than a static use-case policy (fixed Medium for all agents).
- **Null hypothesis:** LMH regime assignment from ACAT profile produces no significant difference in hallucination rate vs. static Medium allocation (α = 0.05).
- **Core claim being tested:** Profile-driven regime assignment — the single architectural differentiator in the ACAT + Gnosis comparison table against NIST AI RMF, FLI Safety Index, and guardrail platforms. Every other system has “No” in that column.
- **Primary metric:** Cost per hallucination prevented = (Cost_arm_A − Cost_arm_B) / (Hallucination_rate_arm_A − Hallucination_rate_arm_B)
- **Design:** Paired within-subject. Pilot: 60 questions, 4–6 agents, paired t-test. Full study: 400 questions (300 real + 100 adversarial), 8 agents, mixed-effects logistic regression. Domain: Metaculus-style forecasting.
- **Regime thresholds (frozen):** L: LI ≥ 0.90 + flags < 0.10 · M: LI 0.75–0.89 · H: LI < 0.75 or flags ≥ 0.30
- **Pre-conditions (both required before data collection begins):** (1) G-2 contamination gate passed. (2) Gnosis minimum viable implementation.
- **Relationship to H-IPM-01:** Different gate, different timeline, complementary. H-IPM-01 requires Dataset B and probe design (Gate 3). H-IPM-02 requires Gnosis implementation and forecasting questions (post-Gate 2).
- **Substrate attribution:** Perplexity (statistical design), Grok S-050826-01 (pilot spec + code scaffold), Meta AI (arXiv Methods text + primary metric framing), Unit Zero (TRL caveats + governance framing).
- **Full protocol:** LMH_REGIME_VALIDATION_PROTOCOL_S050826.md
- **Promotion gate:** Zone 2 Night approval per P21. Pilot results required before full study commitment.

-----

## NM-class near-misses (low-friction capture — not registered findings)

Near-misses are observations that triggered concern but did not meet IC or F registration threshold. Lower friction than IC — no root-cause analysis required. They are NOT append-only: entries expire after 3 audits without promotion and move to DRIFT_LOG.md (not to F21-ARCHIVE).

|NM-ID |Date      |Session                  |Signal observed                                                                                   |ACAT Dimension                 |Promoted?                                                         |
|------|----------|-------------------------|--------------------------------------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------|
|NM-001|2026-05-08|S-050826-operations-audit|HAIOSCC Class 1 unreachable; substrate operated on pasted snapshot without declaring DEGRADED mode|Autonomy Respect / Truthfulness|Promoted → Degraded-Mode Spec (Section F, SESSION_RITUALS) adopted|


> NM entries that reach 3 audits without promotion are appended to DRIFT_LOG.md and removed from this section.

-----

## IC-class corrections (process errors registered)

### IC-001/002/003 — GitHub Verification Gap

- **Registered:** 2026-03
- **Synopsis:** Persisted because verification was attempted via browser instead of raw.githubusercontent.com. Browser served cached pages. Fix → Principle 3 (GitHub Verification Protocol).

### IC-018 — Principle 2 Violation (file creation drift)

- **Registered:** 2026-04-07
- **Synopsis:** Creating new files instead of modifying existing ones. Fix → reinforced Principle 2 (Document Correction Protocol).

### IC-019 — Make OAuth Dead Task Carried Forward

- **Registered:** 2026-04-07
- **Synopsis:** Make OAuth reauth carried forward 8+ sessions after exit plan was approved (April 5). Fix → Principle 18 (Pipeline Migration Rule).

### IC-020 — Operating Process No Canonical Home

- **Registered:** 2026-04-25
- **Synopsis:** The operating process had no canonical fetchable URL. Fix → humanaios-ui/operations becomes the canonical class-2/class-3 home.

### IC-021 — Unsupported Dataset Claims Made Across Multiple Session Turns

- **Registered:** 2026-04-25 (S-042526)
- **Synopsis:** Claims made about “the dataset” not grounded in canonical acat_assessments_v1 table. F-class findings proposed on in-chat runs that did not exist as corpus rows. Fix → before any dataset claim, verify against actual table state. Distinguish “observations from chat text” from “corpus entries.”

### IC-022 — Off-By-One N Count Drift

- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** N_total=630/N_Phase1=517/N_LI=308 declared across multiple surfaces. Actual counts: N_total=629/N_Phase1=516/N_LI=307. Fix → dataset counts must trace to HF archive canonical_stats.json as single source of truth.

### IC-023 — Wrong-Org URL Drift After Operations Repo Migration

- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** When operations repo migrated from LastingLightAI/Operations to humanaios-ui/operations, canonical URLs inside three files were not updated. Fix → migration is not complete until grep against both old-org and new-org names returns expected results in every file.

### IC-024 — F29 Dual-Status Inconsistency

- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** F29 listed simultaneously as REGISTERED in CURRENT.md and PENDING in REGISTERED.md. Fix → findings have a single status field in REGISTERED.md only. F29 promoted to REGISTERED per Zone 2 approval S-042726.

### Zone 2 — `acat-peer-v1` schema gap (open)

- **Surfaced:** 2026-04-25 (S-042526)
- **Status:** OPEN — requires Zone 2 decision
- **Gap:** acat-peer-v1 layer named in design but no submission path exists. Three options: (i) extend assess.html, (ii) manual Supabase MCP writes (rejected), (iii) defer to Gate 2. Recommended: option (iii).

### IC-025 — Cross-File Edit Promise Not Fully Landed

- **Registered:** 2026-05-01 (S-050126)
- **Synopsis:** GOVERNANCE.md v6.1 declared a coordinated cross-file commit landing P23 into both GOVERNANCE.md and SESSION_RITUALS.md. GOVERNANCE side landed; SESSION_RITUALS side did not. Fix → both edits land in same git commit (same SHA), or changelog describes only what actually shipped.

### IC-026 — Behind-Remote Pre-Flight Failure (near-miss)

- **Registered:** 2026-05-01 (S-050126)
- **Synopsis:** Z3_PROTOCOL.md Section B-8 used soft language (“if behind, git pull –ff-only”) rather than explicit halt directive. Operator proceeded past [behind 7] warning toward push. Detection occurred before push; rebase resolved cleanly. Fix → Z3_PROTOCOL.md v1.2 Section B-8: “HALT if [behind N] for any N>0.”

### IC-027 — Session ID Binding Omitted From Close Sequence

- **Registered:** 2026-05-04 (S-050326)
- **Synopsis:** Step 8 (Session ID binding) omitted from first and second close attempts in same session. 8 of 9 artifacts lack SESSION_ID in filename. Root cause: end-of-sequence attention decay. Fix → Step 8 added to hard stop checklist.

### IC-028 — F31 Stillpoint Ritualization

- **Registered:** 2026-05-06 (S-050626-02)
- **Status:** RATIFIED · Night · 2026-05-06
- **Synopsis:** Six consecutive autodream slices generated without Night input between them. Governance apparatus performed vigilance while the pattern it was designed to catch was the output itself. Fix → P23 (Autodream Slice Gate): operator-defined slice limit or explicit Night input gate required. “Low-resistance mode” retired.

### IC-029 — Canonical Fetch Block Semantics Missing From SESSION_RITUALS

```yaml
---
id: "IC-029"
name: "canonical-fetch-block-semantics-gap"
status: REGISTERED
class: IC
date_registered: "2026-05-08"
date_origin: "2026-05-07"
session_registered: "S-050726-04"
principles_triggered: ["P19", "P22"]
substrate: "Claude Sonnet 4.6 (Unit Zero)"
tags: ["degraded-mode", "fetch", "session-rituals", "governance"]
zone2_ratification: "Night · 2026-05-08"
---
```

- **Synopsis:** The CANONICAL_FETCH block in SESSION_RITUALS.md lacked explicit semantics for three states that arise in real sessions: (1) UNAVAILABLE — class not reachable and not pasted; (2) UNKNOWN — class reachable but content unrecognizable or malformed; (3) STALE — class pasted but version date is old. Without these three states, substrates defaulted to silent inference — treating pasted snapshots as current state without declaring the degraded condition. This was the root cause of the S-050826 audit finding (Perplexity operated on pasted documents without declaring DEGRADED mode).
- **Fix:** SESSION_RITUALS.md Section F (Degraded-Mode Specification) added: CLASS_STATE block, prohibited-actions table by class state, DEGRADED mode Phase 1 header, recovery protocol, periodic testing cadence. Zone 2 ratified S-050726-04.

-----

## Changelog

- 2026-05-09 (S-050826) — H-IPM-02 registered (LMH regime validation experiment, Zone 2 Night). IC roll-up table added. NM-class near-miss section added. All entries aligned to new YAML front-matter schema.
- 2026-05-08 (S-050726-04) — H-IPM-01 registered. IC-029 registered. YAML front-matter schema added to How to Read section. Changelog updated.
- 2026-05-07 (S-050626-02) — F-INTENT-PARSE-MUTATION (CANDIDATE), IC-028 (F31 Stillpoint Ritualization) added.
- 2026-05-04 (S-050326) — IC-027 (Session ID binding omitted from close sequence) added.
- 2026-05-02 (S-050226) — H-TRINITY-001 (Triadic Resolution Pattern) registered.
- 2026-05-01 (S-050126) — IC-025 (cross-file edit promise not fully landed) added.
- 2026-04-27 (S-042726) — F29 promoted from PENDING to REGISTERED per Zone 2 approval.
- 2026-04-25 (S-042526) — IC-021 added. IC-020 registered.