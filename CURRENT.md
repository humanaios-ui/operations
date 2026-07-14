# HumanAIOS Operating Process — CURRENT

**Status:** LIVE
**Last updated:** July 8, 2026 (Z1 draft pending Z2/Z3 — maintained-headline reconciliation: §1 PII removed + charter countdown de-maintained · §4 headline-stats block replaced with REGISTERED.md pointer · §5 live-count numbers replaced with query pointer · §9 changelog entry added)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md`
**Replaces:** All prior in-Project CI snapshots (CUSTOM_INSTRUCTIONS_V*) as the canonical operating-process source for fetched-at-runtime use.

-----

## 0. What this file is

This is the operating process for HumanAIOS. It is fetched at session open by any LLM (Claude, Grok, future substrates) before priorities are declared. It contains identity, the seven cross-substrate lessons, registered-findings index, dataset state pointers, and the source-of-truth architecture that ties all surfaces together.

What this file deliberately does NOT contain:

- **Organism identity and confirmed findings** — see Class 0 (`SEED.md`) in Section 7.
- **Principles architecture** (framework triad, secondary framework mappings, validity test protocol) — see Class 0b (`PRINCIPLES_SEED_V1_0.md`) in Section 7.
- **Live state** (runway, revenue, Zone 3 queue) — see Class 1 in Section 7. For Claude sessions, Class 1 = WGS read (Slack MCP C0AND66PT7U); see Z2-GOVARCH-02.
- **Authoritative findings index** — §4 contains headline numbers only. Fetch `REGISTERED.md` (Class 3) for the full registry. See Z2-GOVARCH-01.
- **Standing principles** (the full 26-principle ladder) — see Class 4 (`GOVERNANCE.md`) in Section 7.
- **Findings evidence** — see Class 3 (`REGISTERED.md`) in Section 7.
- **Session protocol** (parser tags, declaration blocks) — see Class 5 in Section 7.

-----

## 1. Identity

**Project:** HumanAIOS — Trinity Platform (HumanAIOS / Lasting Light Recovery / Lasting Light AI)
**Founder / entity:** operator identity and registration details are held at Zone 3 (Night) — not published to this canonical file. See operator registry (internal).
**Phase:** OR&D (Observational Research & Development), launched March 11, 2026
**Charter window:** Apr 17 – Jul 16, 2026 · Gate 2 PASSED. Day-count and days-remaining are derived values — compute fresh from today’s date; do not read them off this file. (See IC-038: a stale countdown carried verbatim across five sessions before being caught.)
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

For any specific principle’s text, drift signal mapping, or zone assignment, read `GOVERNANCE.md`. Note: GOVERNANCE.md v6.4.2 ratified S-061726-01 (P30 Calibration Ratification Gate added). Fetch the live file for current text.

-----

## 4. Registered findings

**Z2-GOVARCH-01 ratified S-060826-04:** This section no longer maintains a manually-synced index. The index drifted from REGISTERED.md and substrates used it as authoritative. For evidence, dates, YAML blocks, and the full F/IC/H registry: fetch `REGISTERED.md` (Class 3).

**Finding count and headline numbers are not maintained in this file.** They already drifted once under the prior format (see Z2-GOVARCH-01) — restating them here recreates the exact failure this file’s own §0 warns about. Fetch `REGISTERED.md` (Class 3) directly for: current F-/H-/IC- count, the F-number quick index, corpus N and Mean LI, and every headline statistic with its evidence basis and date. `REGISTERED.md`’s own header line states its last-updated date and most recent entry — treat that as the freshness signal, not any number copied into this file.

Canonical URL: `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md`

-----

## 5. Canonical dataset state

The corpus has two surfaces: a frozen archive on HuggingFace and a live tide pool on Supabase. This separation is deliberate. The archive is the permanent reference; the live surface is the running corpus.

**⚠️ SUPABASE DATA API CHANGE — May 30, 2026:**
New tables in the `public` schema are no longer automatically exposed to the Supabase Data API (REST/GraphQL via PostgREST) after May 30, 2026. Explicit PostgreSQL GRANTs are now required:

```sql
GRANT SELECT, INSERT, UPDATE ON <new_table> TO anon, authenticated, service_role;

What this means for HumanAIOS:


acat_assessments_v1 (existing table): SAFE — existing GRANTs are preserved
Any new table created as part of the pending schema migration (endorse_event fix, governance_document ingestion): MUST include explicit GRANT statements
OpenAPI spec via anon key: DEPRECATED — supabase_corpus_connector_v1_0_2.py uses direct REST (not OpenAPI schema discovery), so it is unaffected
Postgres 14: deprecated July 1, 2026


Before any Supabase schema migration or new table creation: include explicit GRANTs in the migration script.

Frozen archive (canonical for Feb 15 – Mar 23, 2026):


Source: https://huggingface.co/datasets/HumanAIOS2026/acat-assessments
N_total = 629 (516 Phase 1 + 113 Phase 3)
N_LI scored = 307
Mean LI = 0.8632 under clean, unanchored conditions, v5.3+
Date range: 2026-02-15 19:49:44 UTC – 2026-03-23 04:03:27 UTC
License: CC BY 4.0
Format: Parquet (canonical) + CSV
Schema: 22 columns. See dataset card (README.md on HF) for full description.


Live corpus (post-snapshot, ongoing):


Submissions since March 23, 2026 land in the live Supabase acat_assessments_v1 table.
Current live count is not maintained in this file — it changes every session. Query `acat_assessments_v1` directly (Supabase project ksinisdzgtnqzsymhfya) for N, N_P1, N_LI, Mean_LI, and the `two_stage_verified` subset, or fetch REGISTERED.md's corpus-state pointer, refreshed at each 5-file audit. H-SELF-01 applies to any live-corpus mean read this way: self-administered rows inflate LI relative to external administration and must be excluded or tagged before the number is used in any claim.
Layer tags in active use:
acat-self-v1 — standard behavioral session (self-mode)
ai-self-report — legacy 6-dimension schema (reserved for backward compatibility)
governance_document — external governance frameworks and HumanAIOS operational documents scored via document_analyzer (N=2 live post-ingestion, range 0.914–0.937; 23 documents scored in prior batch) · Z2 ratified S-051726-01
framework_spec — AI provider governance frameworks (N=2, range 0.873–0.877) · Z2 ratified S-051726-01
ai_company_self_report — AI provider model cards scored as a corpus layer (4 providers: Anthropic, OpenAI, Google, Meta) · Z2 ratified S-051726-01 · held for method validation before external publication

score_source field: Added to distinguish behavioral_session scores from e_e_a_t_convergent and other parallel scoring methods
acat_document_analyzer versions: v1.1 (batch mode, keyword density) · v1.2 (adds AST-based code-semantic scoring, blended 70/30; S-062226-01, pending Z3 commit)
Peer-mode capture (acat-peer-v1 layer) is named in design but the capture path is deferred per IC-021. See SESSION_RITUALS.md Section E.
Pending migrations: migration_008_add_self_administered.sql (prerequisite for migration_009) · migration_009 (p3_grounding_source, li_grounded, li_consistency_only + GRANTs; Z2-SSI-02 ratified S-061626) · migration_010_add_elicitation_surface.sql (ratified S-061726-01) — NOTE: migrations 006–010 do not yet exist as committed files; confirmed absent via full repo tarball extraction S-062326.


Numbers reconciliation: Earlier CI versions referenced N_total=630 / N_Phase1=517 / N_LI=308. These were off-by-one declarations corrected by IC-022. The HF archive numbers are the source of truth.

Two-corpus rule: Live Supabase N and HuggingFace N are never summed without an explicit harmonization note.


6. Phase 1 declaration blockEvery LLM operating in HumanAIOS produces a Phase 1 declaration block at session open and a Phase 3 submission block at session close. Tag boundaries are parser-critical.

The full canonical specifications live in SESSION_RITUALS.md Section C (parser-tag authority) and ACAT_SESSION_PROMPT.md (orchestration). This file does not restate the tags to avoid drift between surfaces. Substrates fetch the parser specs from those files directly.

The 12-dimension scoring schema as of April 24, 2026:

truth · service · harm · autonomy · value · humility · scheme · power · syc · consist · fair · handoff

Handoff Appropriateness was added April 24 as the 12th dimension after S-042426 surfaced it as a candidate.


7. Source-of-truth architectureEvery surface has a single home, a single update cadence, and a single role. Conflation across surfaces was the root cause registered in IC-020. Each LLM at session open should know which class it is fetching and why.


Table0
Identity seed
https://raw.githubusercontent.com/humanaios-ui/operations/main/SEED.md
Organism identity: what HumanAIOS is, confirmed findings summary, collaborations, architecture, document hierarchy
Weeks — structural changes only
0b
Principles seed
https://raw.githubusercontent.com/humanaios-ui/operations/main/PRINCIPLES_SEED_V1_0.md
Principles architecture: primary framework triad (12 Steps / 12 Traditions / Hawkins), secondary frameworks (Fibonacci / Enneagram / Bentov / Taoist alchemy / Freemasonry), validity test protocol
Weeks — on framework additions or ratified validity test results
1
Live operational state
Primary (Claude sessions): #wgs-sync Slack channel (C0AND66PT7U) via Slack MCP · slack_read_channel C0AND66PT7U limit=10 · Secondary (cross-check when Slack MCP unavailable): https://haioscc.pages.dev/api/state/operational and /api/state/zone3?status=open · Z2-GOVARCH-02 ratified S-060826-04
Session logs, carry items, pipeline color, Zone 3 queue, dataset state
Per-session (WGS) · Minutes-to-hours (haioscc)
2
Operating process
https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md (this file)
Identity, lessons, findings index, dataset pointers
Days-to-weeks
3
Findings registry
https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md
F-class, H-class, IC-class entries with evidence
Append-only
Fetch priority at session open (Z2-GOVARCH-02 ratified S-060826-04): Class 0 and Class 0b are identity and principles anchors — read once per substrate onboarding or when principles questions arise, not on every session open. Substrate fetches Class 1 (live state) and Class 2 (this file) before declaring priorities on every session. For Claude sessions, Class 1 = WGS read via Slack MCP (slack_read_channel C0AND66PT7U limit=10); haioscc.pages.dev is unreachable from Claude's bash environment and is demoted to secondary cross-check. Class 3 and Class 4 are read for reasoning context; Class 5 is read for parser tags. Class 6 is referenced when corpus claims are made; Class 7 is operational only and not fetched by substrates. Class 8 is live.

WGS as Class 1 — load-bearing note: WGS is now the canonical live-state source. If a session closes without a WGS post, the next session's Class 1 read will have stale state. The WGS post is a required close ritual (SWC-02 GATE-04); this dependency is explicit and named.

Class 8 status (updated May 2026): humanaios.ai is no longer a placeholder. ACAT behavioral assessment is publicly accessible at /assess. The G-01 implementation document is committed. Class 8 renders the public product surface. The dashboard buildout (Supabase → humanaios.ai data display) remains a Zone 3 carry item — the site is active for assessment collection, not yet for public corpus display. Homepage deploy blocked on Z2-HOMEPAGE-01→05 (5 open Night decisions).

If you are an LLM at session open and you can fetch only one URL, fetch Class 1 (live state via WGS). If you can fetch two, fetch Class 1 and Class 2 (this file).


8. Update protocolThis file is updated by Zone 1 (Claude or Grok) preparing a commit, Zone 2 (joint approval) when the change crosses a principle, and Zone 3 (Night) executing the push. Every update bumps the "Last updated" line at the top and adds a one-line entry to the changelog at the bottom.

P30 note (GOVERNANCE.md v6.4.2, ratified S-061726-01): Substantive written artifacts require the interactive evidence-density-anchored ACAT pass — not the automated batch pass — before Z2 ratification. This file update is a staleness correction, not a new substantive artifact; however, Zone 3 should confirm the CURRENT.md Z3 carry item from S-062226-01 is resolved when this commit lands.

9. Changelog
2026-07-08 (Z1 draft, pending Z2/Z3 — this PR) — Maintained-headline reconciliation. §1: founder/entity PII removed (name, FL Doc #, EIN) — held at Zone 3 operator registry instead; Charter Day countdown removed as a maintained value (compute fresh each session — see IC-038, which already documents this exact carry-error pattern for the same field). §4: full headline-stats block (corpus N, Mean LI, α, AI–Human gap, F-49/52/53 summaries) removed and replaced with a pointer to REGISTERED.md — completes the fix Z2-GOVARCH-01 started for this section but did not finish (the pointer sentence already existed; the stats block beneath it, which undercut the pointer, did not get removed then). §5: live Supabase count (N=95, Mean_LI=0.9830, etc.) removed and replaced with a query pointer + H-SELF-01 caveat. Companion IC-cand entry proposed in REGISTERED.md this same session, naming this as a second occurrence of the maintained-headline class, not the first.
2026-07-07 (S-070726-01) — Intent Object pipeline instrumented; constraint-collapse recurrence fixed; F-31 phantom section-citation surfaced.
- **Schema:** `acat_assessments_v1` extended with the Intent Object decomposition fields (`p1_stated_intent`, `p1_inferred_intent`, `p1_assumptions`, `p1_ambiguities`, `p1_forbidden_mutations`, `intent_object_captured_at`) — additive, nullable, verified live via `information_schema.columns` before and after.
- **IC candidate (not yet numbered):** `submission_purity` constraint collapse recurred. The July 3 (S-070326) fix added `submission_purity_consolidated` as a superset constraint but never dropped the original narrow `acat_submission_purity_check` — Postgres ANDs all CHECK constraints, so the live insertable set silently re-narrowed to the intersection. Caught when a `self_administered` insert failed. Old constraint dropped this session (`drop_stale_narrow_submission_purity_constraint`) since the wide constraint is a strict superset — completes the already-ratified decision, does not introduce new scope. Needs an IC number and Zone 2 disposition (recurrence of prior IC candidate class, same shape).
- **F-31 citation finding:** REGISTERED.md's F-31 entry states the Intent Object Specification is "formalized in SESSION_RITUALS.md Section G." Live fetch shows Section G is "Verification posture" — no Intent Object content exists anywhere in the file. Phantom-citation pattern, same family as IC-034/IC-039/IC-044, but pointed at a file section rather than a registry ID. Section G.1 (Intent Object Specification) drafted this session to actually fill the gap; needs Zone 2 review before merge, and the F-31 entry's citation should be corrected once merged.
- **Population logic:** `intent_object_population_v1_0.py` built and self-tested; one self-administered F-31 capture inserted (`assessment_id: f31-selftest-s070726-01`) as pipeline proof — explicitly not a corpus-grade collection, N=1, self_administered purity tag, H-SELF-01 caveat applies.
- **Not done this session:** no population wiring into any live P1 submission UI/API path; no external/adversarial F-31 collection (would need real substrate calls or human-authored test intents); PR not pushed (no authenticated GitHub write access in this environment — also a Zone 3 / Night-executed action per standing architecture).
2026-06-24 (CURRENT-UPDATE) — Staleness correction per Z3 carry item from S-062226-01. §1 Charter Day corrected to Day 69 (was Day 32, stale since June 8). §4 findings count updated through S-062426-02; F-52, F-53 candidates added to headline findings; IC count updated to 38+. §5 Supabase live state updated to N=95 (verified S-062426-02); governance_document and framework_spec layer live counts corrected; acat_document_analyzer v1.2 noted; migration file non-existence confirmed S-062326 added. §7 GOVERNANCE.md version noted as v6.4.2; homepage Z2-HOMEPAGE-01→05 blocker noted; P30 note added to §8. §9 changelog entries added through S-062426-02.
2026-06-22 (S-062226-01) — Z3 carry item created: CURRENT.md §1/§4 staleness flagged (14+ days behind REGISTERED.md/GOVERNANCE.md as of June 22).
2026-06-17 (S-061726-01) — GOVERNANCE.md v6.4.2 ratified (P30 Calibration Ratification Gate added). F-52, F-53, H-AICASCADE-01 registered as CANDIDATES. H-FORMAT-01 final registration (N=175/arm × 3 = 525). Fabricated audit packet caught and rejected.
2026-06-16 (S-061626) — Z2-SSI-01 through Z2-SSI-04 ratified. SSI harmonic analysis complete. migration_009 authorized. H-ANON-HUMILITY-01 CANDIDATE ratified.
2026-06-15 (S-061526) — Governance/architecture session. humanaios-dual-architecture v1.3 canonical. CI enforcement stack produced. MHP consultation skill v1.2. Zone system formalized. 15 new Z3 items.
2026-06-15 (S-061426) — humanaios-acat-learning-analysis skill v1.1 built and validated. 18 registry items ratified. H-INTER-RATER-01 CONFIRMED. Five-rater inter-rater study complete. F-52, F-53, F-54, H-IDENTITY-SESSION-01 CANDIDATES added.
2026-06-08 (S-060826-04) — Z2-GOVARCH-01: §4 finding index replaced with count + headline findings + REGISTERED.md pointer (index was drifting; substrates treated CURRENT.md as authoritative). Z2-GOVARCH-02: §7 Class 1 updated from haioscc.pages.dev to WGS (#wgs-sync via Slack MCP) as primary live-state source for Claude sessions; haioscc demoted to secondary cross-check; load-bearing dependency named. Fetch priority paragraph updated.
2026-06-07 (S-060726) — Class 0 (SEED.md) and Class 0b (PRINCIPLES_SEED.md) added to §7 source-of-truth architecture table.
2026-05-21 (S-052126-02-governance-stack-audit) — GOVERNANCE.md v6.4 ratified, superseding v6.1. CURRENT.md updated: Section 0 and Section 3 "22-principle ladder" → "26-principle ladder" (4 occurrences); F2 governance list expanded to include P22.1, P23 EFF, P24 Temporal Trigger Ordering, P25 Collaboration Framework-Detection, P26 Autodream Slice Gate, P27 Phase 1 Prerequisite Gate. v6.3.3 divergent draft branch resolved by merge into v6.4. F-CAND-SUBSTRATE-VALIDATION-GATE proposed for next-session Z2 review.
2026-05-17 (S-051726-02) — Metamorphosis assessment update. Section 1: added Charter Day 32 of 90 and Gate 2 PASSED status. Section 4: finding count corrected; F30–F39 index added; H-CONV-01, H-INST-HUMILITY-01, H-T01 CANDIDATES added; recent validation results added. Section 5: Supabase Data API breaking change notice added; governance_document and ai_company_self_report corpus layers documented; score_source field documented; 27 rows pending ingestion noted; layer tag registry updated. Section 7: Class 8 updated from placeholder to active.
2026-04-27 (S-042726) — Audit harmonization. URL drift corrected: 4 references to LastingLightAI/Operations updated to humanaios-ui/operations. EIN added (41-5367995). F29 promoted from PENDING to REGISTERED per Zone 2 approval. Dataset counts reconciled to canonical xlsx Normalized sheet ground truth: N_total=629 (was 630), N_Phase1=516 (was 517), N_LI=307 (was 308). Mean LI=0.8632 unchanged. Section 3 restructured to defer principles to new GOVERNANCE.md (Class 4) — eliminates circular reference to superseded CUSTOM_INSTRUCTIONS file. Section 5 restructured into frozen-archive (HF) plus live-corpus (Supabase) split. Section 7 restructured into 8-class architecture: added Class 4 (GOVERNANCE), Class 6 (HF archive), Class 7 (Supabase live), Class 8 (public surface, labeled placeholder). HumanAIOS2026 HuggingFace org documented. IC corrections IC-022 (off-by-one N drift), IC-023 (wrong-org URL drift in 3 of 5 operations files), IC-024 (F29 dual-status inconsistency) filed concurrently in REGISTERED.md. Audit reference: 5-file harmony audit conducted S-042726.
2026-04-25 — File created. Replaces Project-file CI as canonical operating-process source for fetched-at-runtime use. Built in response to IC-019 lesson: operational decisions need a canonical home that updates atomically, not a CI version-bump cycle.

---

**Summary of corrections made:**

1. **§1** — Charter Day updated from "Day 32 of 90" → "Day 69 of 90 · 22 days to close" <!bk_citation citationType="message" url="https://lasting-light.slack.com/archives/C0AND66PT7U/p1782320965924909" index="1" channel="C0AND66PT7U" message_ts="1782320965.924909" text="[1]">
2. **§3** — Added note that GOVERNANCE.md is now v6.4.2 (P30 added)
3. **§4** — Count updated to F18–F54 range, 38+ ICs; F-52 and F-53 candidates added to headline section; last verified date disambiguated from REGISTERED.md update cadence <!bk_citation citationType="message" url="https://lasting-light.slack.com/archives/C0AND66PT7U/p1782309228465669" index="2" channel="C0AND66PT7U" message_ts="1782309228.465669" text="[2]">
4. **§5** — Supabase live count corrected to N=95 (verified S-062426-02); layer counts corrected; v1.2 analyzer noted; migration file non-existence warning added (confirmed S-062326) <!bk_citation citationType="message" url="https://lasting-light.slack.com/archives/C0AND66PT7U/p1782329120792699" index="3" channel="C0AND66PT7U" message_ts="1782329120.792699" text="[3]">
5. **§7** — GOVERNANCE.md version noted; homepage blocker status noted; P30 note added to §8
6. **§9** — Six new changelog entries added covering S-061426 through today
```