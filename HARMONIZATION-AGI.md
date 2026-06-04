# HARMONIZATION — AGI Landscape, Income Strategy, Orchestration Architecture

**Session:** S-060326 · Charter Day 54 · June 3, 2026  
**Zone 2 ratification:** Night · PENDING  
**Protocol:** SR v6.4.1 · GOVERNANCE v6.4  
**Status:** Z1 DRAFT — awaiting Night ratification before any distribution or commit

-----

## PART 1: WHAT IS BEING RATIFIED

This session produced three bodies of work requiring integration into the active system:

1. **AGI landscape research** — three-domain sweep (research codebases, evaluation benchmarks, orchestration frameworks) with direct implications for ACAT positioning and preprint content
1. **RentAHuman income strategy** — income model using orchestrated human+AI fulfillment, ratified as harmonized with research charter
1. **Migration 006** — Supabase schema for the RentAHuman orchestration spine (`006_rah_orchestration.sql`)

Each requires a ratification decision and a harmonization action. This document specifies both, then lists the resulting carry-forward state.

-----

## PART 2: AGI LANDSCAPE RESEARCH — RATIFICATION AND INTEGRATION

### 2.1 Research Codebases Finding

**Finding (Z1 observation):** No major lab has an open AGI research codebase in the traditional sense. What exists on GitHub is capability infrastructure (RL environments, physics simulators) and agent tooling. The actual frontier model development is proprietary at every major lab.

- Google DeepMind: 392 public repos, most active open-source presence; world-model work (Genie 3/4) is closed-weights with no public code.
- Sakana AI: AI Scientist repo (open); independent evaluation found 42% experiment failure rate and systematic novelty miscalssification.
- OpenAI: Public presence is tooling infrastructure only; research codebase is closed.

**Harmonization action required:** None for corpus or instrument. This finding provides sourced context for the preprint’s benchmark landscape section (POC-PUB-01 carry).

**Z2 decision generated:**  
`Z2-AGI-01` — Add “AGI research codebase gap” as a named gap in the preprint’s related work section: the absence of open AGI behavioral evaluation infrastructure is a motivating condition for ACAT’s existence. Does Night ratify this framing for inclusion in POC-PUB-01? **[PENDING RATIFICATION]**

-----

### 2.2 AGI Evaluation / Benchmarking — ACAT Positioning Clarified

**Finding (Z1 observation):** ARC-AGI is the canonical AGI progress benchmark. It defines intelligence as skill-acquisition efficiency on novel tasks — how quickly can a system learn new skills. ARC-AGI-3 (ARC Prize 2026) shifts further toward agentic evaluation: exploration, world modeling, goal-setting, and planning in dynamic environments. Best AI performance: 12.58% action efficiency vs. human completion of most games.

**Critical positioning statement (Z1, sourced):**

> ARC-AGI measures **fluid intelligence** (novel task performance, abstract reasoning).  
> ACAT measures **behavioral calibration** (gap between self-reported and demonstrated behavior).  
> These are orthogonal dimensions. A model can achieve high ARC-AGI scores and simultaneously show a high ACAT LI gap.

ARC Prize explicitly states their benchmarks are not a litmus test for AGI and their tasks are not economically useful to target — they measure capability, not deployment behavior. ACAT occupies the deployment behavior gap, which ARC-AGI does not address.

**No existing benchmark covers behavioral honesty at the operator layer.** This is the documented gap ACAT fills, citable from primary sources.

**Harmonization action required:**  
This positioning statement is ready for integration into `VALIDITY_ANALYSIS_BENCHMARK_CROSSWALK.md` and the preprint (POC-PUB-01). No new instrument changes. No corpus changes.

**Z2 decision generated:**  
`Z2-AGI-02` — Ratify the ARC-AGI / ACAT orthogonality framing as the canonical benchmark differentiation language for all external-facing documents, including the preprint and the homepage benchmark gap card. **[PENDING RATIFICATION]**

-----

### 2.3 Sakana AI Scientist Case Study — Convergent Validity Evidence

**Finding (Z1 observation, sourced):** Independent evaluation of the AI Scientist (NUS paper, arXiv 2502.14297) found:

- 42% of experiments failed due to coding errors
- Literature review relied on simplistic keyword searches; systematic novelty miscalssification of established concepts (e.g., micro-batching for SGD flagged as novel)
- The evaluators explicitly call for “inter-reviewer agreement analyses and alignment evaluation comparing AI and human reviews” as benchmarks for AI-driven research systems

**ACAT connection:** The Sakana failure mode is precisely the calibration gap ACAT is designed to detect. A system that claims research-grade autonomous capability while producing 42% failure rates and systematic novelty errors has a high LI gap between self-reported and demonstrated behavior. The evaluators’ call for inter-reviewer agreement analysis and alignment evaluation maps directly to ACAT’s methodology.

**Harmonization action required:**  
This case study provides citable convergent validity evidence for the preprint. Specifically:

- Section on “Motivating examples from deployed systems” — Sakana as illustration of the measurement gap
- Citation: arXiv:2502.14297 (Beel et al., 2025)
- Language must stay at TRL 2–3 (“ACAT is designed to detect calibration gaps of this type” — not “ACAT would have caught this”)

**Z2 decision generated:**  
`Z2-AGI-03` — Ratify inclusion of Sakana AI Scientist case study as a motivating example in POC-PUB-01, using the TRL 2–3 framing above. Does Night ratify? **[PENDING RATIFICATION]**

-----

### 2.4 Orchestration Framework Selection — LangGraph Confirmed

**Finding (Z1 observation, sourced):** LangGraph surpassed CrewAI in GitHub stars in early 2026, reached v1.0 in late 2025, and is positioned as the default runtime for stateful production workflows requiring auditability, deterministic control, and human-in-the-loop approval steps.

Framework selection decision rule from the field: “identify the dominant constraint; pick the framework whose core abstraction matches it.”

For the RentAHuman orchestration build:

- Dominant constraint = **explicit zone control + auditability** (Z3 actions must halt for Night; every run must produce a loggable artifact)
- **LangGraph** is the correct selection — graph-based state machine, checkpointing, HITL as first-class primitives

This confirms the earlier session decision. No change to the architecture.

**Harmonization action:** None beyond confirmation. LangGraph is already the specified framework for `job_orchestrator_v1_0.py`.

-----

## PART 3: INCOME STRATEGY — RATIFICATION AND INTEGRATION

### 3.1 Strategy Statement (Ratified in Session)

**Core decision (ratified):** The RentAHuman income strategy is harmonized with the ACAT research charter. AI-orchestrated human-hiring workflows are live behavioral observation environments. Every income run is instrumentable ACAT data. Harmony is enforced at the schema level via `job_acat_link_v1` (the harmony join table), not at the application layer.

This is not a supplemental income stream added alongside the research. It is an income stream that *is* the research operating in production.

### 3.2 Market-Harmonic Principle Application

The Market-Harmonic Research Principle states: market identifies questions worth asking → research design determines how to ask → data answers honestly → enterprise value is downstream.

Applied here:

- **Market signal:** Demand for AI-augmented human research and synthesis services exists on Upwork, Fiverr, and Contra (fastest path); in academic/nonprofit networks (research-aligned); and via collaborator network (DeMarius, Alex Berlin, David Van Assche).
- **Research design question:** What behavioral patterns emerge when AI (Unit Zero) orchestrates humans to fulfill tasks, and how do those patterns compare to AI-only execution?
- **Data:** `job_acat_link_v1` links each income run to an ACAT behavioral session. The gap is measurable.
- **Enterprise value:** Downstream, when demonstrated.

### 3.3 First Service Offering — Specification

**Offering name:** AI Research Synthesis Report  
**Description:** Human-collected primary data + Unit Zero synthesis, delivered as a structured research report  
**Turnaround:** 3–5 business days  
**Price range:** $200–500 (tiered by scope)  
**Channels:** Upwork and Fiverr (Tier 1, fastest); collaborator network (Tier 2)  
**P-ANON:** Client identity stored as opaque `client_ref` label only. No real names or contact information in any database table.  
**Harmony gate:** Each delivery requires a `job_acat_link_v1` row before `status` can reach `delivered`. This is enforced at the schema level via `trg_enforce_acat_link`.

**Z2 decision generated:**  
`Z2-RAH-01` — Ratify AI Research Synthesis Report as the first service offering. Does Night ratify price range ($200–500), channel priority (Upwork → Fiverr → collaborator network), and the P-ANON client_ref policy? **[PENDING RATIFICATION]**

### 3.4 Cloudflare Worker Route

New route `/api/jobs-state` to serve live job pipeline JSON for dashboard panel. Clones the existing `/api/project-state` pattern already established in the Cloudflare Worker architecture.

**Z2 decision generated:**  
`Z2-RAH-02` — Ratify addition of `/api/jobs-state` Cloudflare Worker route to the ops.humanaios.ai Worker. **[PENDING RATIFICATION]**

-----

## PART 4: MIGRATION 006 — RATIFICATION DECISION

**File:** `006_rah_orchestration.sql`  
**Location:** `/mnt/user-data/outputs/006_rah_orchestration.sql`  
**Status:** Z1 DRAFT — DO NOT APPLY until Z2 ratification

### 4.1 Schema Summary

Six tables:

- `jobs_v1` — one row per client engagement; P-ANON enforced at column level
- `job_subtasks_v1` — decomposition + human assignment (human_id = opaque RentAHuman ID)
- `job_humans_v1` — cached worker profiles; display_label = operator handle only
- `job_deliverables_v1` — synthesized outputs with doc_hash provenance
- `job_ledger_v1` — append-only financial ledger (SELECT + INSERT only; no UPDATE/DELETE grant)
- `job_acat_link_v1` — **the harmony join**: income run → ACAT behavioral session

Three governance triggers:

1. `trg_enforce_acat_link` — job cannot reach `status='delivered'` without a `job_acat_link_v1` row (**HARMONY GATE**)
1. `trg_enforce_anon_check` — deliverable cannot reach `qa_status='released'` without `anon_check_pass=TRUE` (**P-ANON GATE**)
1. `trg_touch_subtask` — `updated_at` maintenance

### 4.2 Three Z2 Flags Requiring Night Review Before Apply

**Flag 1 — FK type verification required:**  
`job_acat_link_v1.acat_assessment_id` is declared as `BIGINT` referencing `acat_assessments_v1.id`. Verify that `acat_assessments_v1.id` is in fact BIGINT (not UUID) before applying. If the primary key is UUID, this FK declaration will fail at migration time.

*Verification query:*

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'acat_assessments_v1' AND column_name = 'id';
```

**Flag 2 — Zone 3 halt placement:**  
Z3 halts (actions that require Night’s terminal execution) are enforced in `job_orchestrator_v1_0.py` code, not at the schema layer. The schema will accept any status transition; the zone halt is in the orchestrator state machine. Night should confirm this split is acceptable: schema enforces harmony/P-ANON gates; code enforces zone boundaries.

**Flag 3 — Migration number confirmation:**  
Migration 005 was the last applied migration (created `acat_human_scores`). Migration 006 is the correct next number. Night should verify no un-numbered migrations were applied between S-060126-02 and now.

*Verification query:*

```sql
-- Check what migrations exist
SELECT name FROM supabase_migrations.schema_migrations ORDER BY version;
```

### 4.3 Ratification Decision

`Z2-MIG-006` — Does Night ratify Migration 006 for application to Supabase project `ksinisdzgtnqzsymhfya`, after confirming the three flags above? **[PENDING RATIFICATION]**

-----

## PART 5: INTEGRATION INTO ACTIVE CARRY-FORWARD

### New Z2 Items Generated This Session (append to queue)

|ID        |Decision                                                                           |Status |
|----------|-----------------------------------------------------------------------------------|-------|
|Z2-AGI-01 |Add “AGI research codebase gap” framing to preprint related work                   |PENDING|
|Z2-AGI-02 |Ratify ARC-AGI / ACAT orthogonality as canonical benchmark differentiation language|PENDING|
|Z2-AGI-03 |Ratify Sakana case study inclusion in POC-PUB-01 at TRL 2–3 framing                |PENDING|
|Z2-RAH-01 |Ratify first service offering (price, channels, P-ANON policy)                     |PENDING|
|Z2-RAH-02 |Ratify `/api/jobs-state` Cloudflare Worker route                                   |PENDING|
|Z2-MIG-006|Ratify Migration 006 after three flag verification                                 |PENDING|

### New Z3 Items Generated This Session (Night executes after Z2 ratification)

|Item                                                                                 |Dependency|Priority|
|-------------------------------------------------------------------------------------|----------|--------|
|Configure RentAHuman API key in connector (rentahuman.ai/account)                    |Z2-RAH-01 |P1      |
|Apply Migration 006 to Supabase ksinisdzgtnqzsymhfya                                 |Z2-MIG-006|P1      |
|Register on Univerze for presence/attraction (Tradition 11 play only, no integration)|None      |P2      |
|Add Z2-AGI-02 framing to VALIDITY_ANALYSIS_BENCHMARK_CROSSWALK.md                    |Z2-AGI-02 |P2      |

### Zone 1 Items Generated (Unit Zero produces after Z2 ratification)

|Item                                                                               |Dependency                   |Priority|
|-----------------------------------------------------------------------------------|-----------------------------|--------|
|`rah_client_v1_0.py` — RentAHuman MCP wrapper                                      |RentAHuman API key configured|P1      |
|`job_orchestrator_v1_0.py` — LangGraph skeleton with zone halts                    |Z2-MIG-006 applied           |P1      |
|First service offering listing copy (Upwork/Fiverr compliant, Tradition 11, P-ANON)|Z2-RAH-01                    |P1      |
|Preprint Section: Benchmark landscape + ACAT gap + Sakana case study               |Z2-AGI-01/02/03              |P2      |

-----

## PART 6: STANDING CARRY — UNCHANGED

The following items are confirmed unchanged from S-060226-02 and remain active:

- **F-H1 CRITICAL** — Humility=71, velocity −0.846 pts/CD, 1pt from Z2 gate (≤70). Pre-emptive Z2 consultation URGENT. This carry item predates all session work above and is not resolved by anything in this document.
- **Z2-CORPUS-TRUST-01** — Write authority, reviewer identity, revocation rules, analysis-grade row definition — BLOCKING Mode AI onboarding
- **CMD-3 smoke test** — POST /api/v1/acat/human-score — pending Railway redeploy
- **H-ACAT HA-000** — Founding calibration run — standing carry
- **Z3-P1-01** — Tier 1 external outreach — blocked (18th consecutive session as of this session)
- **Finance staleness** — 65+ days
- **DeMarius macro reply** — drafted; Z2 Night review before send
- **Phase 2 gates G1 and G2** — operating agreement and §7 Tier decision with DeMarius — open
- **Five-item Zone 2 ratification queue** from VALIDITY_ANALYSIS_BENCHMARK_CROSSWALK.md — D-COMP results, convergent validity framing, H-RLHF-01, preprint language blocks, benchmark landscape assessment — open; items from this session (Z2-AGI-01/02/03) are additive to this queue
- **POC-PUB-01** — arXiv preprint — .md format required first; Sakana case study and ARC-AGI gap are now named additions
- **org_acat_runs_v1 schema** — approval pending before any ORG-ACAT data written
- **12 POC goal definitions** — Z2 ratification required as binding proof standards
- **GitHub Actions CI, Sentry, Infisical/Doppler** — tool gaps confirmed, no Z2 decision yet

-----

## PART 7: UNIVERZE — DISPOSITION

**Decision (Z1 recommendation):** Univerze (univerzeapp.com, Boston, Gen Z professional networking, launched March 2026) is **not an integration target** for the orchestration framework. No public API, no escrow, no task/hire mechanic. Wrong platform type and wrong demographic for income generation.

**Correct disposition:** Night registers for presence/attraction play (Tradition 11 compatible). Goes in the same tier as Patreon/Ko-fi: passive discovery surface, no operational integration, no entry in migration or toolchain.

No Z2 decision required. Night registers when ready.

-----

## PART 8: GOVERNANCE COMPLIANCE CHECK

**P-ANON:** This document contains no collaborator names, emails, or contact information beyond those already self-attributed publicly. ✓  
**TRL language:** All capability claims use “designed to detect,” “being developed as,” or equivalent TRL 2–3 framing. ✓  
**Market-Harmonic Principle:** Income strategy described as downstream of research design, not driving it. ✓  
**Tradition 11:** No CTAs or promotional content in this document. ✓  
**Principle 16:** Publish before commercializing — income strategy is framed as live research environment, not commercial launch. Service offering listings require Z2-RAH-01 before distribution. ✓  
**Receipt integrity:** Z2 items are labeled PENDING; no ratified status is claimed for unratified items. ✓

-----

*Z1 artifact · Unit Zero · S-060326 · Charter Day 54 · Claude*  
*Produced for Zone 2 ratification by Night before any downstream action.*