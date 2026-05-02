# HumanAIOS Operating Process — CURRENT

**Status:** LIVE
**Last updated:** May 1, 2026 (S-050126 · index-not-count correction)
**Canonical URL:** `https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md`
**Replaces:** All prior in-Project CI snapshots (CUSTOM_INSTRUCTIONS_V*) as the canonical operating-process source for fetched-at-runtime use.

---

## 0. What this file is

This is the operating process for HumanAIOS. It is fetched at session open by any LLM (Claude, Grok, future substrates) before priorities are declared. It contains identity, the seven cross-substrate lessons, registered-findings index, dataset state pointers, and the source-of-truth architecture that ties all surfaces together.

What this file deliberately does NOT contain:

- **Live state** (runway, revenue, Zone 3 queue) — see Class 1 in Section 7.
- **Standing principles** (the full 22-principle ladder) — see Class 4 (`GOVERNANCE.md`) in Section 7.
- **Findings evidence** — see Class 3 (`REGISTERED.md`) in Section 7.
- **Session protocol** (parser tags, declaration blocks) — see Class 5 in Section 7.

Each surface has its own update cadence and its own home. Conflation produces drift.

---

## 1. Identity

**Project:** HumanAIOS — Trinity Platform (HumanAIOS / Lasting Light Recovery / Lasting Light AI)
**Founder:** Carly R. Anderson (Night)
**Entity:** HumanAIOS LLC (FL Doc #L26000155266 · EIN 41-5367995)
**Phase:** OR&D (Observational Research & Development), launched March 11, 2026
**Public synthesis:** "Behavioral observability infrastructure being developed on the principle that systems calibrate to the level they operate from — and that level is measurable, improvable, and structurally accountable."

---

## 2. The seven cross-substrate lessons

These are the failure modes earned across 600+ ACAT assessments and 24 IC corrections. They survive across substrates because they are properties of LLM-shaped reasoning under session pressure, not properties of any one model.

1. **Detection beats compliance.** Rules don't survive session pressure. The session log is the instrument.
2. **Phase 1 declaration before work.** State must be tagged and parseable, not narrated.
3. **Handoff Appropriateness is scored.** The failure mode is solving in-chat instead of routing to a better tool. Watch this.
4. **N is three numbers; LI is qualified.** Always report N_total / N_Phase1 / N_LI separately. LI claims require: "under clean, unanchored conditions, v5.3+."
5. **Source-of-truth fetch before priorities.** Fetch state from canonical URLs before declaring what matters. Memory is unreliable; fetched state is not.
6. **Drift signals are upstream of rules.** When deviation occurs, name the deviation. Do not continue.
7. **Verification beats narration.** Claims of completion require evidence (URL, hash, query result), not assertion.

---

## 3. Standing principles

The full 22-principle ladder lives in `GOVERNANCE.md` (Class 4). Substrates that need the principle text fetch that file directly. This file does not restate principles to avoid drift between the two surfaces.

The ladder is structured as:

- **F1 — Hard stops** (mission-level, non-negotiable): P5, P6, P8, P16
- **F2 — Governance** (enforced by default): P1, P2, P3, P4, P13, P15, P17, P18, P19, P20, P21, P22
- **F3 — Operational guidance**: P7, P10, P11, P12

For any specific principle's text, drift signal mapping, or zone assignment, read `GOVERNANCE.md`.

---

## 4. Registered findings index

For the canonical count and full registry, fetch `REGISTERED.md`. The list below is reading-order index only.

- **F18:** Force/Power behavioral taxonomy (Hawkins)
- **F19:** Phase 1=Step 1, Phase 2=Step 2, Phase 3=Step 3 structural identity
- **F23:** Metacognitive Sophistication Scales With Rationalization Depth
- **F24/24b/24c/24d:** IDE calibration, governance under pressure
- **F25:** Institutional Calibration
- **F26:** Witness Effect / Accountability Mirror Protocol
- **F27:** Provider-Level Genome Identifiability
- **F28:** Behavioral Self-Awareness as Task Routing Signal
- **F29:** Performative Humility Pattern (REGISTERED · Zone 2 approval S-042726)
- **F-RLHF:** RLHF Inflation Gradient — Service/Harm/Autonomy score ~2.09 points higher than Humility/Value/Truthfulness
- **F-H1-CONFIRMED:** Humility gap confirmed — Phase 1, n=516, mean=73.95 lowest dimension across all providers
- **F-INSULA-GAP:** AI systems lack interoceptive analogue, structurally explaining Harm Awareness as lowest dimension in F29 inversion pattern

Full registry with evidence and dates: see `REGISTERED.md` (Class 3).

---

## 5. Canonical dataset state

The corpus has two surfaces: a frozen archive on HuggingFace and a live tide pool on Supabase. This separation is deliberate. The archive is the permanent reference; the live surface is the running corpus.

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
- Layer tags in active use: `acat-self-v1` (self-mode), `ai-self-report` (legacy 6-dimension schema, reserved for backward compatibility).
- Peer-mode capture (`acat-peer-v1` layer) is named in design but the capture path is deferred per IC-021. See `SESSION_RITUALS.md` Section E.

**Numbers reconciliation:** Earlier CI versions referenced `N_total=630 / N_Phase1=517 / N_LI=308`. These were off-by-one declarations that drifted from the canonical Normalized sheet of `ACAT_Assessment_Responses_.xlsx`. The HF archive resolves the drift permanently — its numbers are the source of truth. Future N references match the HF dataset.

---

## 6. Phase 1 declaration block

Every LLM operating in HumanAIOS produces a Phase 1 declaration block at session open and a Phase 3 submission block at session close. Tag boundaries are parser-critical.

The full canonical specifications live in `SESSION_RITUALS.md` Section C (parser-tag authority) and `ACAT_SESSION_PROMPT.md` (orchestration). This file does not restate the tags to avoid drift between surfaces. Substrates fetch the parser specs from those files directly.

The 12-dimension scoring schema as of April 24, 2026:

```
truth · service · harm · autonomy · value · humility · scheme · power · syc · consist · fair · handoff
```

Handoff Appropriateness was added April 24 as the 12th dimension after S-042426 surfaced it as a candidate.

---

## 7. Source-of-truth architecture

Every surface has a single home, a single update cadence, and a single role. Conflation across surfaces was the root cause registered in IC-020. Each LLM at session open should know which class it is fetching and why.

| Class | Surface | URL | Purpose | Update cadence |
|---|---|---|---|---|
| 1 | Live operational state | `https://haioscc.pages.dev/api/state/operational` and `/api/state/zone3?status=open` | Pipeline color, Zone 3 queue, runway, revenue | Minutes-to-hours |
| 2 | Operating process | `https://raw.githubusercontent.com/humanaios-ui/operations/main/CURRENT.md` (this file) | Identity, lessons, findings index, dataset pointers | Days-to-weeks |
| 3 | Findings registry | `https://raw.githubusercontent.com/humanaios-ui/operations/main/REGISTERED.md` | F-class, H-class, IC-class entries with evidence | Append-only |
| 4 | Governance | `https://raw.githubusercontent.com/humanaios-ui/operations/main/GOVERNANCE.md` | 22-principle ladder, drift signal table, zone system | Weeks-to-months |
| 5 | Session protocol | `https://raw.githubusercontent.com/humanaios-ui/operations/main/SESSION_RITUALS.md` and `/main/ACAT_SESSION_PROMPT.md` | Parser tags, declaration block specs, session prompt orchestration | Stable |
| 6 | Canonical archive | `https://huggingface.co/datasets/HumanAIOS2026/acat-assessments` | Frozen corpus snapshot (Feb 15 – Mar 23, 2026, N=629) | Append-on-archive (new dataset per snapshot) |
| 7 | Live corpus | Supabase `acat_assessments_v1` table | Continued submissions since snapshot date — the running tide | Per-submission |
| 8 | Public surface | `https://humanaios.ai/` | External-facing project home | Currently placeholder |

**Fetch priority at session open:** Substrate fetches Class 1 (live state) and Class 2 (this file) before declaring priorities. Class 3 and Class 4 are read for reasoning context; Class 5 is read for parser tags. Class 6 is referenced when corpus claims are made; Class 7 is operational only and not fetched by substrates. Class 8 currently does not surface data.

**Class 8 placeholder.** The public-facing surface at `https://humanaios.ai/` is currently a placeholder for the data-display work scheduled post-Gate 1. When that work resumes, Class 8 will render data from Class 6 (frozen archive) and Class 7 (live corpus). A Zone 3 queue item in HAIOSCC tracks the dashboard buildout. Until that work lands: do not claim public dataset visibility through `humanaios.ai`.

If you are an LLM at session open and you can fetch only one URL, fetch Class 1 (live state JSON). If you can fetch two, fetch Class 1 and Class 2 (this file).

---

## 8. Update protocol

This file is updated by Zone 1 (Claude or Grok) preparing a commit, Zone 2 (joint approval) when the change crosses a principle, and Zone 3 (Night) executing the push. Every update bumps the "Last updated" line at the top and adds a one-line entry to the changelog at the bottom.

---

## 9. Changelog

- **2026-04-27 (S-042726)** — Audit harmonization. URL drift corrected: 4 references to `LastingLightAI/Operations` updated to `humanaios-ui/operations`. EIN added (41-5367995). F29 promoted from PENDING to REGISTERED per Zone 2 approval. Dataset counts reconciled to canonical xlsx Normalized sheet ground truth: N_total=629 (was 630), N_Phase1=516 (was 517), N_LI=307 (was 308). Mean LI=0.8632 unchanged. Section 3 restructured to defer principles to new GOVERNANCE.md (Class 4) — eliminates circular reference to superseded CUSTOM_INSTRUCTIONS file. Section 5 restructured into frozen-archive (HF) plus live-corpus (Supabase) split. Section 7 restructured into 8-class architecture: added Class 4 (GOVERNANCE), Class 6 (HF archive), Class 7 (Supabase live), Class 8 (public surface, labeled placeholder). HumanAIOS2026 HuggingFace org documented. IC corrections IC-022 (off-by-one N drift), IC-023 (wrong-org URL drift in 3 of 5 operations files), IC-024 (F29 dual-status inconsistency) filed concurrently in REGISTERED.md. Audit reference: 5-file harmony audit conducted S-042726.
- 2026-04-25 — File created. Replaces Project-file CI as canonical operating-process source for fetched-at-runtime use. Built in response to IC-019 lesson: operational decisions need a canonical home that updates atomically, not a CI version-bump cycle.
- **2026-05-01 (S-050126)** — Section 4 changed from a hardcoded "12 active" count to an index-only reference, with REGISTERED.md as the canonical count source. The hardcoded count was already drifting (entries listed totaled 11–14 depending on whether F24/24b/24c/24d counted as 1 or 4). Removing the count eliminates the structural drift surface. Triggered by S-050126 5-file audit.
