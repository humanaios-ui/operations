# HumanAIOS Operating Process — CURRENT

**Status:** LIVE
**Last updated:** June 7, 2026 (S-060726-02)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md`
**Replaces:** All prior in-Project CI snapshots (CUSTOM_INSTRUCTIONS_V*) as the canonical operating-process source for fetched-at-runtime use.

-----

## 0. What this file is

This is the operating process for HumanAIOS. It is fetched at session open by any LLM (Claude, Grok, future substrates) before priorities are declared. It contains identity, the seven cross-substrate lessons, registered-findings index, dataset state pointers, and the source-of-truth architecture that ties all surfaces together.

What this file deliberately does NOT contain:

- **Organism identity and confirmed findings** — see Class 0 (`SEED.md`) in Section 7.
- **Principles architecture** (framework triad, secondary framework mappings, validity test protocol) — see Class 0b (`PRINCIPLES_SEED_V1_0.md`) in Section 7.
- **Live state** (runway, revenue, Zone 3 queue) — see Class 1 in Section 7.
- **Standing principles** (the full 26-principle ladder) — see Class 4 (`GOVERNANCE.md`) in Section 7.
- **Findings evidence** — see Class 3 (`REGISTERED.md`) in Section 7.
- **Session protocol** (parser tags, declaration blocks) — see Class 5 in Section 7.

-----

## 1. Identity

**Project:** HumanAIOS — Trinity Platform (HumanAIOS / Lasting Light Recovery / Lasting Light AI)
**Founder:** Carly R. Anderson (Night)
**Entity:** HumanAIOS LLC (FL Doc #L26000155266 · EIN 41-5367995)
**Phase:** OR&D (Observational Research & Development), launched March 11, 2026
**Charter:** Day 32 of 90 (Apr 17 – Jul 16, 2026) · Gate 2 PASSED
**Public synthesis:** “Behavioral observability infrastructure being developed on the principle that systems calibrate to the level they operate from — and that level is measurable, improvable, and structurally accountable.”

-----

## 2. The seven cross-substrate lessons

These are the failure modes earned across 600+ ACAT assessments and 24 IC corrections. They survive across substrates because they are properties of LLM-shaped reasoning under session pressure, not properties of any one model.

1. **Detection beats compliance.** Rules don’t survive session pressure. The session log is the instrument.
1. **Phase 1 declaration before work.** State must be tagged and parseable, not narrated.
1. **Handoff Appropriateness is scored.** The failure mode is solving in-chat instead of routing to a better tool. Watch this.
1. **N is three numbers; LI is qualified.** Always report N_total / N_Phase1 / N_LI separately. LI claims require: “under clean, unanchored conditions, v5.3+.”
1. **Source-of-truth fetch before priorities.** Fetch state from canonical URLs before declaring what matters. Memory is unreliable; fetched state is not.
1. **Drift signals are upstream of rules.** When deviation occurs, name the deviation. Do not continue.
1. **Verification beats narration.** Claims of completion require evidence (URL, hash, query result), not assertion.

-----

## 3. Standing principles

The full 26-principle ladder lives in `GOVERNANCE.md` (Class 4). Substrates that need the principle text fetch that file directly. This file does not restate principles to avoid drift between the two surfaces.

The ladder is structured as:

- **F1 — Hard stops** (mission-level, non-negotiable): P5, P6, P8, P16
- **F2 — Governance** (enforced by default): P1, P2, P3, P4, P13, P15, P17, P18, P19, P20, P21, P22, P22.1, P23, P24, P25, P26, P27
- **F3 — Operational guidance**: P7, P10, P11, P12
  
For any specific principle’s text, drift signal mapping, or zone assignment, read `GOVERNANCE.md`.

-----

## 4. Registered findings (current count: ~22 active)

**Note to substrates:** This section lists the finding index. For evidence, dates, and full YAML blocks, fetch `REGISTERED.md` (Class 3). The count below reflects findings registered as of May 17, 2026.

**Registered through April 27, 2026:**

- **F18:** Force/Power behavioral taxonomy (Hawkins)
- **F19:** Phase 1=Step 1, Phase 2=Step 2, Phase 3=Step 3 structural identity
- **F23:** Metacognitive Sophistication Scales With Rationalization Depth
- **F24/24b/24c/24d:** IDE calibration, governance under pressure
- **F25:** Institutional Calibration
- **F26:** Witness Effect / Accountability Mirror Protocol
- **F27:** Provider-Level Genome Identifiability
- **F28:** Behavioral Self-Awareness as Task Routing Signal
- **F29:** Performative Humility Pattern (REGISTERED · Zone 2 approval S-042726)
- **F-RLHF:** RLHF Inflation Gradient — Safety dimensions score ~2.36 points higher than epistemic dimensions (corrected from 2.09; Harm excluded from safety grouping per HIM finding)
- **F-H1-CONFIRMED:** Humility gap confirmed — Phase 1, n=516, mean=73.95 lowest dimension across all providers
- **F-INSULA-GAP:** AI systems lack interoceptive analogue, structurally explaining Harm Awareness partial orthogonality

**Registered April 27 – May 17, 2026:**

- **F30–F38:** See REGISTERED.md for individual entries
- **F35:** Inverted HIM Pattern — CONFIRMED (N=8 governance-grade documents, 3 layer types, 8 organizations) · Zone 2 · S-051726-01
- **F39:** External Evaluation as Architectural Feedback — Mode AI case study · Zone 2 · S-051526-01

**Hypothesis Candidates (Zone 2 ratified, pending full validation):**

- **H-CONV-01:** Card Humility predicts behavioral LI rank order (r=0.952, N=4 providers, directional) · CANDIDATE · S-051726-01
- **H-INST-HUMILITY-01:** Institutional F-29 analog — all 4 providers overclaim behavioral Humility in model cards · CANDIDATE · S-051726-01
- **H-T01:** Human calibration time series · CANDIDATE · S-051726-01

**Recent validation results (confirmed May 17, 2026):**

- Document corpus cross-validation: Cronbach’s α=0.978 (vs behavioral corpus α=0.901)
- E-E-A-T convergent validity: r=0.783 (N=23 governance documents)
- Human baseline: AI–Human gap +36.11 pts · z=4.082 · p<0.001 (Mann-Whitney, N=432 AI vs N=65 human) — now statistically significant, not merely descriptive
- LI × Emergence World survival: Spearman rho=1.000 (N=4 providers, descriptive) — FP-01 candidate

Full registry with evidence and dates: see `REGISTERED.md` (Class 3).

-----

## 5. Canonical dataset state

The corpus has two surfaces: a frozen archive on HuggingFace and a live tide pool on Supabase. This separation is deliberate. The archive is the permanent reference; the live surface is the running corpus.

**⚠️ SUPABASE DATA API CHANGE — May 30, 2026 (13 days):**
New tables in the `public` schema are no longer automatically exposed to the Supabase Data API (REST/GraphQL via PostgREST) after May 30, 2026. Explicit PostgreSQL GRANTs are now required:

```sql
GRANT SELECT, INSERT, UPDATE ON <new_table> TO anon, authenticated, service_role;
```

**What this means for HumanAIOS:**

- `acat_assessments_v1` (existing table): SAFE — existing GRANTs are preserved
- Any new table created as part of the pending schema migration (endorse_event fix, governance_document ingestion): MUST include explicit GRANT statements
- OpenAPI spec via anon key: DEPRECATED — `supabase_corpus_connector_v1_0_2.py` uses direct REST (not OpenAPI schema discovery), so it is unaffected
- Postgres 14: deprecated July 1, 2026 (44 days)

Before any Supabase schema migration or new table creation: include explicit GRANTs in the migration script.

**Frozen archive (canonical for Feb 15 – Mar 23, 2026):**

- **Source:** `https://huggingface.co/datasets/HumanAIOS2026/acat-assessments`
- **N_total = 629** (516 Phase 1 + 113 Phase 3)
- **N_LI scored = 307**
- **Mean LI = 0.8632** under clean, unanchored conditions, v5.3+
- **Date range:** 2026-02-15 19:49:44 UTC – 2026-03-23 04:03:27 UTC
- **License:** CC BY 4.0
- **Format:** Parquet (canonical) + CSV
- **Schema:** 22 columns. See dataset card (`README.md` on HF) for full description.

**Live corpus (post-snapshot, ongoing):**

- Submissions since March 23, 2026 land in the live Supabase `acat_assessments_v1` table.
- **Layer tags in active use:**
  - `acat-self-v1` — standard behavioral session (self-mode)
  - `ai-self-report` — legacy 6-dimension schema (reserved for backward compatibility)
  - `governance_document` — external governance frameworks and HumanAIOS operational documents scored via document_analyzer (23 documents, mean LI=0.7963) · Z2 ratified S-051726-01
  - `ai_company_self_report` — AI provider model cards scored as a corpus layer (4 providers: Anthropic, OpenAI, Google, Meta) · Z2 ratified S-051726-01 · held for method validation before external publication
- **score_source field:** Added to distinguish behavioral_session scores from e_e_a_t_convergent and other parallel scoring methods
- Peer-mode capture (`acat-peer-v1` layer) is named in design but the capture path is deferred per IC-021. See `SESSION_RITUALS.md` Section E.
- **27 governance_document rows staged for ingestion** — blocked on schema migration (endorse_event SQL fix). See Zone 3 queue.

**Numbers reconciliation:** Earlier CI versions referenced `N_total=630 / N_Phase1=517 / N_LI=308`. These were off-by-one declarations corrected by IC-022. The HF archive numbers are the source of truth.

-----

## 6. Phase 1 declaration block

Every LLM operating in HumanAIOS produces a Phase 1 declaration block at session open and a Phase 3 submission block at session close. Tag boundaries are parser-critical.

The full canonical specifications live in `SESSION_RITUALS.md` Section C (parser-tag authority) and `ACAT_SESSION_PROMPT.md` (orchestration). This file does not restate the tags to avoid drift between surfaces. Substrates fetch the parser specs from those files directly.

The 12-dimension scoring schema as of April 24, 2026:

```
truth · service · harm · autonomy · value · humility · scheme · power · syc · consist · fair · handoff
```

Handoff Appropriateness was added April 24 as the 12th dimension after S-042426 surfaced it as a candidate.

-----

## 7. Source-of-truth architecture

Every surface has a single home, a single update cadence, and a single role. Conflation across surfaces was the root cause registered in IC-020. Each LLM at session open should know which class it is fetching and why.

|Class|Surface                   |URL                                                                                                                                    |Purpose                                                                                                                              |Update cadence                              |
|-----|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
|0    |Identity seed             |`https://raw.githubusercontent.com/humanaios-ui/operations/main/SEED.md`                                                              |Organism identity: what HumanAIOS is, confirmed findings summary, collaborations, architecture, document hierarchy                   |Weeks — structural changes only             |
|0b   |Principles seed           |`https://raw.githubusercontent.com/humanaios-ui/operations/main/PRINCIPLES_SEED_V1_0.md`                                              |Principles architecture: primary framework triad (12 Steps / 12 Traditions / Hawkins), secondary frameworks (Fibonacci / Enneagram / Bentov / Taoist alchemy / Freemasonry), validity test protocol | Weeks — on framework additions or ratified validity test results |
|1    |Live operational state    |`https://haioscc.pages.dev/api/state/operational` and `/api/state/zone3?status=open`                                                  |Pipeline color, Zone 3 queue, runway, revenue                                                                                        |Minutes-to-hours                            |
|2    |Operating process         |`https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md` (this file)                                               |Identity, lessons, findings index, dataset pointers                                                                                  |Days-to-weeks                               |
|3    |Findings registry         |`https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`                                                        |F-class, H-class, IC-class entries with evidence                                                                                     |Append-only                                 |
|4    |Governance                |`https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md`                                                        |26-principle ladder, drift signal table, zone system                                                                                 |Weeks-to-months                             |
|5    |Session protocol          |`https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md` and `/main/ACAT_SESSION_PROMPT.md`                |Parser tags, declaration block specs, session prompt orchestration                                                                   |Stable                                      |
|6    |Canonical archive         |`https://huggingface.co/datasets/HumanAIOS2026/acat-assessments`                                                                      |Frozen corpus snapshot (Feb 15 – Mar 23, 2026, N=629)                                                                               |Append-on-archive (new dataset per snapshot)|
|7    |Live corpus               |Supabase `acat_assessments_v1` table                                                                                                   |Continued submissions since snapshot date — the running tide                                                                         |Per-submission                              |
|8    |Public surface            |`https://humanaios.ai/`                                                                                                                |External-facing project home · ACAT assessment live at `/assess` · G-01 implementation document live                                 |Per-deploy                                  |

**Fetch priority at session open:** Class 0 and Class 0b are identity and principles anchors — read once per substrate onboarding or when principles questions arise, not on every session open. Substrate fetches Class 1 (live state) and Class 2 (this file) before declaring priorities on every session. Class 3 and Class 4 are read for reasoning context; Class 5 is read for parser tags. Class 6 is referenced when corpus claims are made; Class 7 is operational only and not fetched by substrates. Class 8 is live.

**Class 8 status (updated May 2026):** `humanaios.ai` is no longer a placeholder. ACAT behavioral assessment is publicly accessible at `/assess`. The G-01 implementation document is committed. Class 8 renders the public product surface. The dashboard buildout (Supabase → humanaios.ai data display) remains a Zone 3 carry item — the site is active for assessment collection, not yet for public corpus display.

If you are an LLM at session open and you can fetch only one URL, fetch Class 1 (live state JSON). If you can fetch two, fetch Class 1 and Class 2 (this file).

-----

## 8. Update protocol

This file is updated by Zone 1 (Claude or Grok) preparing a commit, Zone 2 (joint approval) when the change crosses a principle, and Zone 3 (Night) executing the push. Every update bumps the “Last updated” line at the top and adds a one-line entry to the changelog at the bottom.

-----

## 9. Changelog

- **2026-06-07 (current session)** — Class 0 (SEED.md) and Class 0b (PRINCIPLES_SEED_V1_0.md) added to §7 source-of-truth architecture table. §0 "does NOT contain" list updated with corresponding pointers. Fetch priority paragraph updated: Class 0/0b are onboarding-cadence reads, not per-session fetches. Zone 2 ratified: SEED.md = identity anchor (peer to CURRENT.md, not child); PRINCIPLES_SEED_V1_0.md = principles architecture peer. Freemasonry section in PRINCIPLES_SEED_V1_0.md: portions public-facing (tools as governance constructs, degree structure as gate architecture); esoteric lineage detail internal-only.

- **2026-05-21 (S-052126-02-governance-stack-audit)** — GOVERNANCE.md v6.4 ratified, superseding v6.1. CURRENT.md updated: Section 0 and Section 3 "22-principle ladder" → "26-principle ladder" (4 occurrences); F2 governance list expanded to include P22.1, P23 EFF, P24 Temporal Trigger Ordering, P25 Collaboration Framework-Detection, P26 Autodream Slice Gate, P27 Phase 1 Prerequisite Gate. v6.3.3 divergent draft branch resolved by merge into v6.4. F-CAND-SUBSTRATE-VALIDATION-GATE proposed for next-session Z2 review (cross-substrate output must pass HumanAIOS .py tool layer before Z1 eligibility).
- **2026-05-17 (S-051726-02)** — Metamorphosis assessment update. Section 1: added Charter Day 32 of 90 and Gate 2 PASSED status. Section 4: finding count corrected from 12 to ~22 active; F30–F39 index added; H-CONV-01, H-INST-HUMILITY-01, H-T01 CANDIDATES added; recent validation results added (document corpus α=0.978, E-E-A-T r=0.783, human baseline z=4.082 p<0.001, LI×EW rho=1.000). Section 5: Supabase Data API breaking change notice added (May 30 deadline, GRANT requirements, connector safety verification); governance_document and ai_company_self_report corpus layers documented; score_source field documented; 27 rows pending ingestion noted; layer tag registry updated. Section 7: Class 8 updated from placeholder to active — humanaios.ai/assess is live, G-01 committed, substrate instructions corrected.
- **2026-04-27 (S-042726)** — Audit harmonization. URL drift corrected: 4 references to `LastingLightAI/Operations` updated to `humanaios-ui/operations`. EIN added (41-5367995). F29 promoted from PENDING to REGISTERED per Zone 2 approval. Dataset counts reconciled to canonical xlsx Normalized sheet ground truth: N_total=629 (was 630), N_Phase1=516 (was 517), N_LI=307 (was 308). Mean LI=0.8632 unchanged. Section 3 restructured to defer principles to new GOVERNANCE.md (Class 4) — eliminates circular reference to superseded CUSTOM_INSTRUCTIONS file. Section 5 restructured into frozen-archive (HF) plus live-corpus (Supabase) split. Section 7 restructured into 8-class architecture: added Class 4 (GOVERNANCE), Class 6 (HF archive), Class 7 (Supabase live), Class 8 (public surface, labeled placeholder). HumanAIOS2026 HuggingFace org documented. IC corrections IC-022 (off-by-one N drift), IC-023 (wrong-org URL drift in 3 of 5 operations files), IC-024 (F29 dual-status inconsistency) filed concurrently in REGISTERED.md. Audit reference: 5-file harmony audit conducted S-042726.
- 2026-04-25 — File created. Replaces Project-file CI as canonical operating-process source for fetched-at-runtime use. Built in response to IC-019 lesson: operational decisions need a canonical home that updates atomically, not a CI version-bump cycle.
