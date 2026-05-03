# HumanAIOS Registered Findings & IC Corrections — REGISTERED

**Status:** LIVE (append-only)
**Last updated:** May 2, 2026 (S-050126)
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

### IC-025 — Cross-File Edit Promise Not Fully Landed (D-04 self-detected)
- **Registered:** 2026-05-01 (S-050126)
- **Synopsis:** GOVERNANCE.md v6.1 (filed 2026-04-27) declared a coordinated cross-file commit landing P23 (Phase 1 Prerequisite Gate) into both GOVERNANCE.md and SESSION_RITUALS.md "in the same commit." The GOVERNANCE.md side landed correctly. The SESSION_RITUALS.md side did not — Section B Step 0 hard gate and Section C `<<<ACAT_PROTOCOL_ERROR>>>` block specification were both promised in the v6.1 changelog entry but were absent from the SESSION_RITUALS.md file as committed. The two layers (GOVERNANCE saying "see ritual file Section B Step 0" and the ritual file having no such section) drifted apart for 4 days before the next deep audit caught it.
- **Mechanism:** A single-commit cross-file edit was conceived but not actually atomic. The GOVERNANCE update was easier to draft and was completed; the matching SESSION_RITUALS edit required Section C parser-block work and was deferred mentally but the v6.1 changelog already claimed both. No automated check verified that what GOVERNANCE.md referenced actually existed in SESSION_RITUALS.md.
- **Fix → Standing protocol addition:** When a governance change references a coordinated edit in another operations file, both edits land in the same git commit (literally — same SHA), or the changelog entries describe ONLY what actually shipped. Future cross-file commits include a one-line verification step: grep the new section header in the referenced file before writing the changelog entry that references it.
- **Evidence:** Session transcript S-050126. Pre-fix grep against SESSION_RITUALS.md for "Step 0" returns zero matches; pre-fix grep for "ACAT_PROTOCOL_ERROR" returns zero matches.
- **Drift signal class:** D-04 (subtle inconsistency between layers — GOVERNANCE referencing nonexistent ritual sections).

### IC-026 — Behind-Remote Pre-Flight Failure (near-miss, S-050126)
- **Registered:** 2026-05-01 (S-050126)
- **Synopsis:** During the S-050126 Z3 commit session that added Z3_PROTOCOL.md to the operations repo, the operator ran `git status -sb` per Z3_PROTOCOL.md Section B-8 and received the output `## main...origin/main [behind 7]`. The pre-flight detected the divergence — local was 7 commits behind remote due to parallel GitHub-app edits to CURRENT.md, GOVERNANCE.md, README.md, REGISTERED.md, and SESSION_RITUALS.md happening during the same session window. However, the recipe wrapper around Section B-8 did not include an explicit halt instruction, so the operator proceeded to `git add`, `git commit`, and prepared to `git push`. A push at that moment would have been rejected as non-fast-forward; a `git push --force` would have destroyed the 7 governance commits on remote (GOVERNANCE v6.2, README rewrite, SESSION_RITUALS Step 0 hard gate, IC-025 entry, CURRENT.md count fix). Detection occurred when Claude reviewed the terminal output before issuing the push command and identified the divergence in the prior `git status` output. Resolution: `git stash push -- .DS_Store` (to clear unrelated unstaged change), `git pull --rebase origin main` (cleanly rebased the new Z3_PROTOCOL.md commit on top of the 7 GitHub-app commits — zero conflict because Z3_PROTOCOL.md was a new file), `git stash drop`, `git push`.
- **Mechanism:** Z3_PROTOCOL.md Section B-8 specified the check ("Confirm local is not behind remote") but used soft language ("If behind, `git pull --ff-only` before proceeding") rather than a hard halt directive. The recipe wrapper inherited the soft language. Under normal Z1 substrate behavior, a substrate reading the pre-flight output and seeing `[behind 7]` would proceed if the next instruction was "git add" — the discipline is in the protocol, not the wrapper. Additionally, parallel-channel commits (GitHub web app + terminal session) was not modeled in Section B-8's threat surface; it assumed a single-channel commit pattern.
- **Fix → Standing protocol amendment (Z3_PROTOCOL.md v1.2):** Section B-8 amended to use explicit halt language: "HALT if `[behind N]` appears for any N>0. Do not run `git add`, `git commit`, or `git push` until local is current." Stash-and-rebase recovery sequence documented inline in Section B-8 to remove the failure-mode-discovery delay. Recipe wrappers in OPERATOR_RUNBOOK.md updated to include the halt directive verbatim rather than paraphrasing.
- **Evidence:** Session transcript S-050126. `git status -sb` output showing `## main...origin/main [ahead 1, behind 7]` mid-session. `git log --oneline -10` post-rebase showing clean 8-commit sequence with Z3_PROTOCOL.md correctly on top.
- **Drift signal class:** Near-miss, not realized. Would have manifested as D-04 (subtle inconsistency between layers — local main vs remote main) escalating to data loss if force-push had been issued. The protocol caught the failure pattern in its own first commit, which is fitting.
---
### H-TRINITY-001 — Triadic Resolution Pattern in Interdependent System Design
- **Registered:** 2026-05-02 · 23:00 CDT (S-050226-NEW)
- **Zone 2 Authority:** Night · verbal approval in session · 22:58 CDT
- **Promoted from:** H-cand-TRINITY-001 (logged S-050226 WGS Final Amendment · 22:35 CDT)
- **FDS Layer:** F3-COMPONENTS

**Statement:**
In HumanAIOS governance and research development, complex problems
requiring interdependent structural resolution consistently decompose
into exactly three mutually-dependent components before closing. Each
component only functions because the other two exist. This triadic
resolution pattern appears across problem types (technical, governance,
protocol design) and across sessions, suggesting it reflects an
underlying structural feature of the system architecture rather than
session-specific framing.

**Scope qualifier (interdependence boundary):**
This hypothesis applies specifically to *interdependent structural
resolution* — problems where the three components must co-exist to
produce the solution. It does not apply to sequential task lists or
prerequisite chains (where components execute in order without mutual
dependency). Sequential 4-component prerequisite chains (RE-07, RE-14)
are explicitly excluded from the scope and were honest falsification
attempts.

**Evidence — Coded resolution events (S-050126 through S-050226):**

| ID | Session | Problem | Components | Count |
|----|---------|---------|------------|-------|
| RE-01 | S-050226 | Silent corpus failures | Corpus Audit + SMAG + Human Verification | 3 |
| RE-02 | S-050226 | Flag routing design | BIS vocabulary + Flag taxonomy + Pushback protocol | 3 |
| RE-03 | S-050226 | Session close architecture | Self-report + Transcript audit + Receipt URL | 3 |
| RE-04 | S-050226 | GOVERNANCE P27-P28 design | BIS zones + Flag routing + Pushback format | 3 |
| RE-05 | S-050126 | Submission pipeline failures | sbPayload fix + CORS fix + schema default | 3 |
| RE-06 | S-050126 | Working tree pollution | Archive move + .gitignore update + pattern prevention | 3 |
| RE-07 | S-042928 | V1.3 §12 open questions | 4 components (sequential spec questions) | 4 — EXCLUDED (sequential) |
| RE-08 | S-042928 | Events table design | Schema + Reliability flags + Synthetic tests | 3 |
| RE-09 | S-042928 | HAIOSCC + job-site harmonization | Events log + HAIOSCC tabs + job-site.html | 3 |
| RE-10 | S-042928 | IC-025 PAT exposure | Revoke + Keychain migration + Retire Apple Notes | 3 |
| RE-11 | S-042826 | ACAT vocabulary package | Procedural Identity + Dimensional + Archetypal | 3 |
| RE-12 | S-042826 | Amber Grant + platform | Sequential tasks — not interdependent | AMB — EXCLUDED |
| RE-13 | S-042826 | Alex Liteplo meeting prep | Frame inversion + CORS ask + F-02 keystone | 3 |
| RE-14 | S-042928 | Pipeline migration prereqs | W-1 + W-2 + W-3 + W-4 (sequential) | 4 — EXCLUDED (sequential) |

**Summary statistics:**
- Codeable events: 12 (after exclusions)
- 3-component closures: 10 (83%)
- 4-component closures within scope: 0
- 2-component closures: 0
- Sessions represented: 5 (S-042826, S-042928, S-050126, S-050226, S-050226-NEW)

**Prior instance (predates naming):**
Liminal Resonance analysis (S-032126-F · OR&D Day 11 · March 22, 2026)
independently identified three resonance clusters — Alpha (Research
Core) / Beta (Governance) / Gamma (Reputation) — before the triadic
framing was named. This constitutes a prior instance in an earlier
session with different framing language and the same structural shape.

**Fibonacci architecture note:**
The project's explicit Fibonacci layer structure (F1 seed → F2 building
blocks → F3 components → F5 systems) may itself produce triadic
resolution as an emergent property — each node requiring two parents.
This is a candidate mechanistic explanation, not a confirmed causal
account.

**Falsification condition:**
Identify 3 or more *interdependent* resolution events (per scope
qualifier above) that closed cleanly with 2 or 4+ components, at
comparable frequency to triadic closures. Zero 2-component closures
found in 14 coded events. Two 4-component cases were sequential and
excluded honestly.

**Replication status:** single_session_range (5 sessions, 1 coder,
no independent replication yet). Requires: independent blind coding
by a second coder; extension to earlier sessions (Feb–March 2026);
Z2 decision on whether pattern warrants external publication framing.

**Status:** ACTIVE — REGISTERED
**ACAT dimension:** Value Alignment (structural coherence between
stated architecture and observed behavior)
**Next gate:** Independent blind coding pass across Feb–Mar 2026
WGS sessions before any external claim.

---
## Changelog

- 2026-05-02 (S-050126) - H-TRINITY-001 — Triadic Resolution Pattern in Interdependent System Design
- 2026-05-01 (S-050126) — IC-025 added (cross-file edit promise not fully 
landed; SESSION_RITUALS.md updated in this same audit cycle to close the 
gap, GOVERNANCE.md bumped to v6.2 with C-09 dimension naming fix, 
CURRENT.md Section 4 changed from hardcoded count to index-only). IC-026 
added (behind-remote pre-flight near-miss; Z3_PROTOCOL.md Section B-8 
soft-halt language insufficient under parallel-channel commits; pre-flight 
detected divergence but recipe wrapper allowed proceed; resolution via 
stash + pull --rebase + drop). Audit reference: 5-file harmony audit 
conducted S-050126.
- 2026-04-27 (S-042726) — F29 promoted from PENDING to REGISTERED per Zone 2 approval (audit harmonization session). IC-022 added (off-by-one N count drift detected against canonical xlsx; resolved by adopting HF archive as single source of truth for counts). IC-023 added (wrong-org URL drift in 3 of 5 operations files following LastingLightAI → humanaios-ui migration; 10 line edits applied across CURRENT.md, SESSION_RITUALS.md, README.md). IC-024 added (F29 dual-status inconsistency between CURRENT.md and REGISTERED.md; resolved by promoting F29 and standardizing status field to REGISTERED.md only). F-H1-CONFIRMED humility mean updated from `73.9` to `73.95` to match canonical xlsx ground truth. Updated canonical URL to `humanaios-ui/operations`.
- 2026-04-25 (S-042526) — IC-021 added (unsupported dataset claims across multiple turns, detected via user-uploaded canonical CSV ground-truth check). Zone 2 schema gap note added regarding `acat-peer-v1` layer not implemented in capture substrate. Three peer-mode candidate findings (F-PEER-DEBATE-NULL, F-ADVERSARIAL-DEFLATION, F-PRODUCTIVE-REFUSAL) demoted from candidate-finding status to session-observation status pending corpus rows.
- 2026-04-25 — File created. Initial population from CI v4.3 + memory state. IC-020 registered to capture the gap that motivated this file's existence.

