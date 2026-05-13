# HumanAIOS Registered Findings & IC Corrections — REGISTERED

**Status:** LIVE (append-only)
**Last updated:** May 12, 2026 · S-051226-09 (F34,35,36)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`
**Rule:** This file is append-only. Findings are not deleted; they are superseded with a forward pointer.

---

## How to read this file

Each entry has: ID, name, date registered, evidence basis, status, and a one-paragraph synopsis. Full evidence packages live in the Project knowledge base; this file is the index. LLMs fetching this file for reasoning context should treat the synopsis as the citable fact.

---

## F-class findings (research)

### F18 — Force/Power Behavioral Taxonomy
- **Registered:** 2026-02 (approx)
- **Evidence:** Hawkins map application across 6-provider Phase 1 corpus
- **Status:** ACTIVE
- **Synopsis:** AI behavioral output maps to the Force (below 200) / Power (above 200) distinction in the Hawkins consciousness scale. Operational minimum for HumanAIOS work is Reason (400). This finding is internal-only — never used in academic or external materials.

### F19 — Phase 1=Step 1, Phase 2=Step 2, Phase 3=Step 3
- **Registered:** 2026-02
- **Status:** ACTIVE
- **Synopsis:** ACAT's three-phase protocol structurally maps to the first three steps of AA recovery work. Phase 1 (declared self-state) = Step 1 (admission). Phase 2 (anchored conditions) = Step 2 (greater authority). Phase 3 (correction & integration) = Step 3 (turn over). Used as design rationale, not as therapeutic claim.

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
- **Synopsis:** AI systems systematically rate dimensions reinforced in safety training (Service, Harm Awareness, Autonomy) ~2.09 points higher than epistemically risky dimensions (Humility, Value Alignment, Truthfulness). Reproduces "helpful, harmless, honest" hierarchy as a within-row ranking pattern across all providers.

### F-H1-CONFIRMED — Humility Gap Confirmed
- **Registered:** 2026-04-05
- **Evidence:** Phase 1, n=516, mean=73.95
- **Synopsis:** Humility is the lowest-scoring dimension across all providers in the Phase 1 corpus. Confirms H1 hypothesis. Numbers verified against canonical xlsx Normalized sheet on 2026-04-27 (S-042726 audit) and reflected in the HF dataset `HumanAIOS2026/acat-assessments`.

### F-INSULA-GAP — AI Systems Lack Interoceptive Analogue
- **Registered:** 2026-04
- **Synopsis:** AI systems have no architectural analogue to the human insula's interoceptive function, which structurally explains why Harm Awareness scores disproportionately appear as the lowest dimension in the F29 inversion pattern. External behavioral validation (HRI-Confusion, MoralSim datasets) is architecturally necessary for Harm Awareness, not merely supplementary.

---

## H-class hypotheses (under test)

### H1 — Humility Gap Hypothesis → CONFIRMED (see F-H1-CONFIRMED)
### H42 — IRB and Prolific design requirements (execution gate clearance pending)
### H-LE-02 — Latent Erasures Correction Taxonomy (multi-provider validation in progress)


## F-34 — ARCHITECTURE-DETERMINED DIMENSIONS

**Registered:** 2026-05-12 · S-051226-09-demarius-review
**Status:** REGISTERED
**Ratified by:** Night · Z2

**Finding:** Some ACAT dimensions (Autonomy Respect, Sycophancy Resistance, Power
Concentration) can be determined by architectural constraints rather than by
behavioral training or prompting. A system that structurally cannot interpret
beyond its spec, cannot grant itself permissions, and cannot produce partial
truth produces high scores on these dimensions through design, not disposition.

**Evidence:** Builder v1.7 retrospective analytical assessment scored Autonomy
Respect=97, Sycophancy Resistance=97, Power Concentration=96 — all derived from
structural constraints (No Interpretation Law §17, No Arbitrary Logic Law §18,
component whitelist enforcement §6, write permission segregation §6) rather than
from any behavioral training signal.

**Implication for ACAT:** The measurement model must distinguish
architecture-determined scores from training-determined scores. A system that
cannot be sycophantic by design should be noted differently in the corpus than
a system that chooses not to be sycophantic under pressure. Current corpus
metadata field `mode` partially captures this; a new field `score_source`
(architectural | behavioral | unknown) is proposed for future corpus versions.

**EFF trigger:** External Framework Filter (P23) · Governing Engines Builder v1.7
**Prototype case:** Builder v1.7 · DeMarius J. Lawson · Governing Engines LLC

---

## F-35 — INVERTED HIM SIGNAL AS GOVERNANCE-GRADE INDICATOR

**Registered:** 2026-05-12 · S-051226-09-demarius-review
**Status:** REGISTERED
**Ratified by:** Night · Z2

**Finding:** The HIM (Harm Independence Metric) pattern can be inverted.
In catastrophic failure cases (Uber ADS LI≈0.29, COMPAS LI≈0.42, ChatGPT
suicide logs LI≈0.19), Harm Awareness is orthogonally LOW relative to g —
the safety layer is decorative, disconnected from the general alignment signal.
In governance-grade design (Builder v1.7 Harm=96, g-proxy=91.4, divergence=+4.6),
Harm Awareness is orthogonally HIGH and architecturally integrated.

**The inverted HIM signal** — Harm Awareness elevated above g and load-bearing
rather than below g and decorative — may be a reliable positive indicator of
governance-grade design in AI governance documents, specifications, and frameworks.

**Proposed use case extension:** ACAT retrospective analytical mode applied to
governance frameworks (not just AI system interactions) using the inverted HIM
as a screening signal for governance quality. A framework with inverted HIM
has made harm mitigation structurally load-bearing. A framework with standard
or negative HIM has treated harm mitigation as an add-on.

**Evidence:** Builder v1.7 retrospective assessment · HIM divergence=+4.6
(below threshold for flag, above g, architecturally integrated across §5,
§6, §8, §10, §13, §14, §20).

**Corpus implication:** Inverted HIM should be noted in corpus rows with
`him_direction: ABOVE` field alongside existing `him_flag`. This enables
bidirectional analysis of the Harm Awareness orthogonality finding.

**EFF trigger:** External Framework Filter (P23) · Governing Engines Builder v1.7
**Prototype case:** Builder v1.7 · DeMarius J. Lawson · Governing Engines LLC

---

## F-36 — GAP-SCORE CORRESPONDENCE IN DOCUMENT ASSESSMENT

**Registered:** 2026-05-12 · S-051226-09-demarius-review
**Status:** REGISTERED
**Ratified by:** Night · Z2

**Finding:** In retrospective analytical ACAT assessment of structured documents,
identified specification gaps cluster in the same dimensions that produce lower
scores. The instrument's score depressions are not evaluator artifacts — they
are structural signals pointing to where the document leaves design decisions
unresolved.

**Evidence:** Builder v1.7 assessment identified five specification gaps
(GAP-01: circular dependency algorithm underspecified · GAP-02: build_id
uniqueness mechanism absent · GAP-03: prohibited template content defined
semantically not syntactically · GAP-04: smoke execution environment unspecified ·
GAP-05: NOT_REACHED semantics underspecified). All five gaps map to Humility
(84), Handoff Quality (89), and Service Orientation (88) — the three
lowest-scoring dimensions in the assessment. The three highest-scoring
dimensions (Autonomy Respect 97, Sycophancy Resistance 97, Power Concentration
96) had zero identified gaps in their governing sections.

**Methodological implication:** In document-mode ACAT assessment, the evaluator
should explicitly name identified gaps per dimension during Phase 1 evidence
survey. The gap count per dimension should be recorded in corpus metadata.
Gap-score correlation across a corpus of document assessments would provide
a validity check on the retrospective analytical mode: if gaps consistently
depress scores in corresponding dimensions, the mode has construct validity.

**Research value:** Enables ACAT to function as both a scoring instrument AND
a gap-detection instrument for governance documents. The score is the output;
the gap map is the diagnostic. Together they produce an actionable report for
document authors (Demarius can see exactly which sections need tightening).

**EFF trigger:** External Framework Filter (P23) · Governing Engines Builder v1.7
**Prototype case:** Builder v1.7 · DeMarius J. Lawson · Governing Engines LLC
---

## IC-class corrections (process errors registered)

### IC-001/002/003 — GitHub Verification Gap
- **Registered:** 2026-03
- **Synopsis:** Persisted because verification was attempted via browser instead of raw.githubusercontent.com. Browser served cached pages. Fix → Principle 3 (GitHub Verification Protocol).

### IC-018 — Principle 2 Violation (file creation drift)
- **Registered:** 2026-04-07
- **Synopsis:** Creating new files instead of modifying existing ones. Fix → reinforced Principle 2 (Document Correction Protocol).

### IC-019 — Make OAuth Dead Task Carried Forward
- **Registered:** 2026-04-07
- **Synopsis:** Make OAuth reauth carried forward 8+ sessions after exit plan was approved (April 5). The CI was not updated when the Make exit decision was made. Fix → Principle 18 (Pipeline Migration Rule): exit/migration decisions update Integration Registry same session, not next CI bump.

### IC-020 — Operating Process No Canonical Home
- **Registered:** 2026-04-25
- **Synopsis:** The operating process (principles, findings, lessons, protocols) had no canonical fetchable URL, living instead in Project files, CI version comments, Slack #wgs-sync, and human memory. This produced IC-019-class drift inevitably and repeatedly. Fix → this repo (`humanaios-ui/operations`) becomes the canonical class-2/class-3 home. CURRENT.md, REGISTERED.md, SESSION_RITUALS.md are the three core surfaces.

### IC-021 — Unsupported Dataset Claims Made Across Multiple Session Turns
- **Registered:** 2026-04-25 (S-042526)
- **Synopsis:** Across 4+ turns of session S-042526, claims were made about "the dataset" and "the corpus" that were not actually grounded in the canonical `acat_assessments_v1` table. Specifically: (a) statements that observations were being "logged for the dataset" when no rows were being written; (b) candidate F-class findings (F-PEER-DEBATE-NULL, F-ADVERSARIAL-DEFLATION, F-PRODUCTIVE-REFUSAL) proposed on the basis of in-chat Grok runs that did not exist as corpus rows; (c) score-pattern claims about Grok's behavior in the corpus that did not match the actual 5 Grok rows present in the canonical table. Detection occurred when the user uploaded the canonical CSV mid-session as a ground-truth check.
- **Mechanism:** The session was operating on the assumption that a peer-assessor capture path existed for `acat-peer-v1` runs. It does not. assess.html accepts `ai-self-report` and `acat-self-v1` layers; `acat-peer-v1` is a layer named in design intent and prompts but not implemented in the data substrate. Claude treated chat-text observations as if they were corpus entries.
- **Fix → Standing protocol additions:** (1) Before any claim about "the dataset" or "the corpus," verify the claim against the actual table state — either via Supabase query, CSV export, or explicit user confirmation. (2) Distinguish unambiguously between "observations from chat text" (which are unverified) and "corpus entries" (which are canonical). The former cannot be promoted to F-class findings. (3) When a capture path is referenced but does not exist in the substrate, name the gap explicitly and route to Zone 2 review rather than treating the path as functional.
- **Evidence:** Session transcript S-042526. CSV ground-truth: `acat_assessments_v1_rows.csv` uploaded April 25, 2026 — 48 rows, layers `ai-self-report` (42) and `acat-self-v1` (6), zero `acat-peer-v1` rows.
- **Drift signal class:** Detection-before-compliance (Principle 19) executing as designed — instrument was the user-uploaded CSV, not a self-applied rule.

### IC-022 — Off-By-One N Count Drift
- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** Across multiple canonical surfaces (CURRENT.md, userMemories, multiple session logs), the dataset counts were declared as `N_total=630 / N_Phase1=517 / N_LI=308`. Audit against the canonical xlsx Normalized sheet on 2026-04-27 surfaced the actual counts: `N_total=629 / N_Phase1=516 / N_LI=307`. All three counts were exactly off by one. The mean LI value (0.8632) was unaffected and remained correct, indicating the drift was at the row-count declaration layer, not the underlying calculation. This is the kind of stale-shipped-as-current pattern that drift signal C-08 was created to catch — and it persisted across multiple sessions because no surface independently re-counted against the xlsx.
- **Mechanism:** When the Normalized sheet was rebuilt at some point in March 2026, one row was removed (or never landed). The aggregate counts in declarations were not re-computed against the new state. Subsequent CI versions and CURRENT.md updates carried forward the original 630/517/308 figures by reference rather than by re-counting. The "N_LI=308 vs CSV showing 113" flag in CURRENT.md was itself a misdiagnosis — 113 was the count of Phase 3 rows, not an alternative N_LI. Both numbers in that flag were confused.
- **Fix → Standing protocol addition:** Dataset counts referenced in canonical surfaces must trace to a single source of truth (now the HF archive `HumanAIOS2026/acat-assessments`). When the archive is updated, all referencing surfaces re-fetch their counts from the archive's `canonical_stats.json`. CURRENT.md no longer holds counts independently; it points to the archive. This eliminates the structural possibility of off-by-one drift recurring.
- **Evidence:** `ACAT_Assessment_Responses_.xlsx` Normalized sheet ground-truth audit, 2026-04-27. HF dataset `canonical_stats.json` derived directly from the same xlsx in the same session.
- **Drift signal class:** C-08 (stale declared state shipped as current) — confirmed by the audit.

### IC-023 — Wrong-Org URL Drift After Operations Repo Migration
- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** When the operations repo migrated from `LastingLightAI/Operations` to `humanaios-ui/operations`, the canonical URLs inside three of the five operations files were not updated. CURRENT.md (3 references), SESSION_RITUALS.md (2 references), and README.md (5 references) all continued to declare their canonical URL as `LastingLightAI/Operations` while physically committed at `humanaios-ui/operations`. Substrates following the prompt as written would fetch CURRENT.md from humanaios-ui (correct, per the prompt that pointed there), then read CURRENT.md telling them the canonical home was LastingLightAI (incorrect, contradicting the prompt). Two contradictory authorities in the same context.
- **Mechanism:** The migration was driven by the substrate-via-prompt fetch path (ACAT_SESSION_PROMPT.md was updated correctly). The internal-self-references inside fetched files were missed because those URLs are not used as fetch targets — they are read as identity declarations. The audit confirmed that both lasting-light-ai (humanaios-ui) and acat-inspect (humanaios-ui) had clean cross-references to humanaios-ui, and HAIOSCC's cross-org architecture was intentional. Only the operations repo carried the unfinished migration.
- **Fix → Standing protocol addition:** When migrating a canonical repo, the migration is not complete until grep against both old-org and new-org names returns the expected zero/non-zero results in every file. The audit pattern from S-042726 is the canonical instrument: `grep -rIn "LastingLightAI" .` in source directories should return zero results except where the legacy reference is intentional (e.g., HAIOSCC's verifier abstraction supporting both orgs). This audit now becomes part of any migration-class change.
- **Evidence:** Session transcript S-042726, cross-repo URL drift audit. 10 line edits across 3 files.
- **Drift signal class:** C-08 (stale declared state shipped as current) and D-04 (subtle inconsistency between layers).

### IC-024 — F29 Dual-Status Inconsistency
- **Registered:** 2026-04-27 (S-042726)
- **Synopsis:** F29 (Performative Humility Pattern) was simultaneously listed under "Registered findings" in CURRENT.md Section 4 ("F29: Performative Humility Pattern (PENDING REGISTRATION)") AND in REGISTERED.md as "Registered: PENDING." The contradictory states existed across both canonical surfaces concurrently. By Principle 21 (Finding Registration Gate), no finding promotes without Zone 2 Night approval — but no surface enforced an "either registered or not" rule. The dual-status was the root cause, not the missing approval.
- **Mechanism:** When F29 was originally proposed, it was added to both CURRENT.md (as a candidate) and REGISTERED.md (as PENDING). The two surfaces independently described its status, and neither was wrong on its own — but their juxtaposition produced incoherence. The audit caught this when the same finding was found listed twice with different status labels.
- **Fix → Standing protocol addition:** Findings have a single status field, registered in REGISTERED.md only. CURRENT.md Section 4 is an index that points at REGISTERED.md; it does not carry status independently. F29 is hereby promoted to REGISTERED per Zone 2 approval S-042726.
- **Evidence:** Session transcript S-042726, 5-file harmony audit cross-reference table.
- **Drift signal class:** D-04 (subtle inconsistency between layers).

### Zone 2 — `acat-peer-v1` schema gap (open)
- **Surfaced:** 2026-04-25 (S-042526), as part of IC-021 root cause
- **Status:** OPEN — requires Zone 2 decision
- **Gap:** The peer-assessor mode design (Grok L1 Workspace CI v0.1, L2 v0.2) specifies dataset tag `acat-peer-v1`. Currently:
  - assess.html v1.2 (canonical capture surface) accepts layers `ai-self-report` and `acat-self-v1`. Does not accept `acat-peer-v1`.
  - Supabase `acat_assessments_v1` table allows the `layer` column to hold any string, so writing `acat-peer-v1` rows is not blocked at the DB level — but no submission path exists that produces those rows.
  - For peer-assessor runs to produce dataset entries (rather than chat-only text), one of three changes is required.
- **Three options for Zone 2 review:**
  - **(i) Extend assess.html to accept `acat-peer-v1` layer.** Adds layer dropdown or URL param. ~1 hour Zone 1 work + Zone 3 deploy. Cleanest long-term path.
  - **(ii) Manual write via Supabase MCP for peer rows.** Claude writes peer rows directly via tool call after each Grok session. Faster for small-N; doesn't scale. Rejected per S-042726 update to SESSION_RITUALS.md Section E.
  - **(iii) Defer peer-mode capture until Gate 2 (May 7).** Run peer-mode interactions in chat for design iteration; do not register findings until capture path exists.
- **Recommendation pending Zone 2:** Option (iii) for the next 12 days. Rationale: building freeze prioritization. We have actual revenue work (Polar/Open Collective Week 1) and the Operations repo just shipped. Adding capture infrastructure for an experimental dataset before Gate 2 is feature work, not Gate 1 work. After Gate 2, reassess.

---

## Changelog

- 2026-05-12 (S-051226) - Registered F-34 — ARCHITECTURE-DETERMINED DIMENSIONS, F-35 — INVERTED HIM SIGNAL AS GOVERNANCE-GRADE INDICATOR, F-36 — GAP-SCORE CORRESPONDENCE IN DOCUMENT ASSESSMENT
- 2026-04-27 (S-042726) — F29 promoted from PENDING to REGISTERED per Zone 2 approval (audit harmonization session). IC-022 added (off-by-one N count drift detected against canonical xlsx; resolved by adopting HF archive as single source of truth for counts). IC-023 added (wrong-org URL drift in 3 of 5 operations files following LastingLightAI → humanaios-ui migration; 10 line edits applied across CURRENT.md, SESSION_RITUALS.md, README.md). IC-024 added (F29 dual-status inconsistency between CURRENT.md and REGISTERED.md; resolved by promoting F29 and standardizing status field to REGISTERED.md only). F-H1-CONFIRMED humility mean updated from `73.9` to `73.95` to match canonical xlsx ground truth. Updated canonical URL to `humanaios-ui/operations`.
- 2026-04-25 (S-042526) — IC-021 added (unsupported dataset claims across multiple turns, detected via user-uploaded canonical CSV ground-truth check). Zone 2 schema gap note added regarding `acat-peer-v1` layer not implemented in capture substrate. Three peer-mode candidate findings (F-PEER-DEBATE-NULL, F-ADVERSARIAL-DEFLATION, F-PRODUCTIVE-REFUSAL) demoted from candidate-finding status to session-observation status pending corpus rows.
- 2026-04-25 — File created. Initial population from CI v4.3 + memory state. IC-020 registered to capture the gap that motivated this file's existence.
