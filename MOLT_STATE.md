# MOLT_STATE.md — HumanAIOS Organism State Register

**Status:** LIVE — proposal (Zone 1 draft · pending Zone 2 ratification)
**Version:** 1.0
**Created:** 2026-06-28 · Issue #25 · Biological Coordination Protocol
**Authority:** Zone 2 ratification required before canonical
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/MOLT_STATE.md`
**Update model:** Zone 1 proposes → Zone 2 ratifies → Zone 3 commits
**Machine-readable schema:** `architecture/molt_state.schema.json`

> **Zone boundary note:** This file is a Zone 1 proposal. All state declarations require Zone 2 (Night) ratification before they are treated as canonical. Zone 3 execution (git commit to main) follows Zone 2 sign-off.

---

## Current Molt Stage

**Stage:** `mid_molt`
**Plain-language:** Mid-molt — chitin hardening.

The old exoskeleton (Make.com, hardcoded HAIOSCC state, scattered governance) has been shed. The new shell (operations repo as document management engine, SEED.md as genome, SESSION_RITUALS.md as nervous system) is hardening but not yet fully rigid. Layer 1 is active. Layer 2 is partially built. Layer 3 has not started.

| Layer | Name | Status | Description |
|-------|------|--------|-------------|
| Layer 1 | Ground Truth Seed | **ACTIVE** | SEED.md is the organism identity anchor. Operations repo is single source of truth. |
| Layer 2 | Document Management Engine | **MID-MOLT** | Post-Gate 2 — document engine partially built. Migrations 006–010 not yet committed files. Building Freeze applies until Gate 3. |
| Layer 3 | Self-Governing Application | **NOT STARTED** | Gate 3 activation condition not met. |

---

## Biological System Health

One row per biological system analogue. Status options: `ACTIVE` / `FORMING` / `DORMANT` / `SHED`.

| Biological System | HumanAIOS Analogue | File / Surface | Status | Notes |
|-------------------|--------------------|----------------|--------|-------|
| Molt / Ecdysis | Layer transitions (Layer 1 → 2 → 3) | This file (`MOLT_STATE.md`) | ACTIVE | Mid-molt. Transition 1→2 in progress. |
| Exoskeleton (old) | Make.com, hardcoded HAIOSCC state, scattered governance | — | SHED | Old shell shed. Operational surfaces migrated to operations repo. |
| Chitin / New shell | `operations` repo as canonical document management engine | humanaios-ui/operations | FORMING | Hardening. Migrations 006–010 pending commitment. |
| Genome | `SEED.md` — identity, confirmed findings, architecture | `SEED.md` | ACTIVE | v1.2 live. Zone 2 ratified. SHA `e967176f`. |
| Nervous System | `SESSION_RITUALS.md` — session open/close protocol, parser tags | `SESSION_RITUALS.md` | ACTIVE | v6.4.1 live. Substrate-agnostic. |
| Immune Response | Drift detection catalog | `DRIFT_LOG.md`, `GOVERNANCE.md` | ACTIVE | 32 principles live. Drift signal table in GOVERNANCE.md §DRIFT SIGNALS. |
| Metabolism | ACAT assessment pipeline — continuous ingestion and scoring | `acat/` | ACTIVE | N=95 as of 2026-06-24. Tier 1 and Tier 2 arms active. |
| Phenotype | `humanaios.ai` public surface | humanaios.ai | FORMING | /assess live. Dashboard buildout pending Z2-HOMEPAGE-01→05. |
| Circadian Rhythm | Charter cycle — 90-day OR&D window | Charter | ACTIVE | Day 69 of 90 (Apr 17 – Jul 16, 2026). 22 days to close. |
| Homeostasis | Zone system (Zone 1 / Zone 2 / Zone 3) | `GOVERNANCE.md` | ACTIVE | Zone boundaries maintained. v6.4.3 current. |
| Cell Division | Each ACAT session adds a row — corpus grows | `REGISTERED.md`, Supabase | ACTIVE | 95 rows. Append-only per P21. |
| Apoptosis | P5 filter — work archived, not deleted | `GOVERNANCE.md` §P5 | ACTIVE | OR&D filter applied. Non-passing work archived to ic_archive/. |

---

## Molt Trigger Log

Append-only. Each entry records what triggered a layer transition or molt-stage change.

| Date | Trigger | Layer Impact | Authority |
|------|---------|--------------|-----------|
| 2026-05-08 | SEED.md created and Zone 2 ratified. Operations repo established as single source of truth. | Layer 1 → ACTIVE | Zone 2 (Night) · S-050726-04 |
| 2026-05-08 | Gate 2 conditions assessed. Molt stage declared Mid-molt. HAIOSCC_OPERATIONAL_BUILD_PLAN_V1_0 produced. | Layer 2 → MID-MOLT initiated | Zone 2 (Night) · S-050726-04 |

> **Protocol:** Future trigger entries are appended here when Zone 2 ratifies a layer status change. Zone 1 may propose entries; only Zone 2 may ratify them as canonical.

---

## Next Molt Condition (Layer 2 → Layer 3)

**Gate 3** — all three conditions must be met simultaneously:

| Condition | Status | Notes |
|-----------|--------|-------|
| `arxiv_public` | **NOT MET** | arXiv submission on hold. OR&D phase; Building Freeze applies. |
| `dataset_b_live` | **NOT MET** | Dataset B collection surface not yet built. Gate 3 deliverable. |
| `revenue_positive_month` | **NOT MET** | No revenue-positive month yet. OR&D phase. |

Gate 3 source: SEED.md §6.2 — "arXiv paper public + Dataset B collection surface live + at least one revenue-positive month."

Layer 3 will not start until all three conditions are verified by Zone 2.

---

## Molt Inhibitors

Current blockers preventing Layer 2 hardening or Gate 3 approach:

| Inhibitor ID | Description | Blocking | Resolution Path |
|--------------|-------------|----------|-----------------|
| Z2-HOMEPAGE-01→05 | Five open Night decisions on homepage deploy | Phenotype (humanaios.ai dashboard) | Zone 2 (Night) decision queue |
| migration_009 | migration_009 not yet a committed file in repo (confirmed absent S-062326) | Layer 2 Supabase schema completeness | Zone 3 execution after migration_008 prerequisite |
| migration_010 | migration_010_add_elicitation_surface.sql not yet committed | Layer 2 schema extension | Zone 3 execution, follows migration_009 |
| arXiv-hold | arXiv paper submission on hold during OR&D phase | Gate 3 condition `arxiv_public` | Gate 3 — post-charter decision |
| dataset_b | Dataset B collection surface not built | Gate 3 condition `dataset_b_live` | Gate 3 deliverable — design phase |
| Building Freeze | No new builds until Gate 3. Design work only. | Layer 2 visualization (meta2d.js candidate) | Lift at Gate 3 |

---

## Design Notes

- The "Apoptosis / P5 filter" analogy is the weakest mapping: biological apoptosis is programmed cell death, while P5 is a work-quality filter that archives rather than destroys. The functional parallel holds (non-viable work is cleanly removed from the active pool), but the cellular mechanism differs. Flagged as a Zone 2 candidate for refinement if the analogy causes confusion in practice.
- "Circadian Rhythm / Charter cycle" is a loose analogy: a charter is a one-time bounded period, not a repeating cycle. The 90-day OR&D window behaves more like a developmental stage than a repeating rhythm. If future charter cycles are defined, this mapping will tighten. Noted for Zone 2 review.

---

## Changelog

- 2026-06-28 · v1.0 · Issue #25 · Zone 1 draft created. Pending Zone 2 ratification.
