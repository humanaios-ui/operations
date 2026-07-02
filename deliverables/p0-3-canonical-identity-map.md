# P0-3 — Canonical Identity Map & Application Plan

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (I draft exact text → you apply/publish)
**Purpose:** One source of truth for identity, then a surface-by-surface action list so search engines + Scholar can consolidate **one** entity and defeat the "Carly Anderson" collision. Pure attraction — this is discoverability plumbing, not promotion.

---

## A · Canonical values (the source of truth — locked)

| Field | Canonical value | Locked |
|---|---|---|
| **Name** (everywhere, incl. citations as `Anderson, Carly R.`) | **Carly R. Anderson** | ✅ |
| **Preprint title** | **ACAT: Benchmarking Self-Description Calibration in Large Language Models** | ✅ |
| **Hub URL** | `https://humanaios.ai/` | ✅ |
| **ORCID** (disambiguation anchor; `sameAs` everywhere) | `0009-0003-7540-4245` | ✅ |
| **Substack** | `@humanaios` | ✅ |
| **HuggingFace org** | `HumanAIOS` (dataset `HumanAIOS/acat-assessments`) — retire `HumanAIOS2026` | ✅ |
| **GitHub org** | `humanaios-ui` | ✅ |
| **X** | `@HumanAIOS` | ✅ |
| **LinkedIn** | `/in/humanaios` | ✅ |
| **Paper text license** | CC-BY-4.0 | ✅ |
| **Code + data license** | Apache-2.0 | ✅ |
| **Contact email** | **`aioshuman@gmail.com`** (portfolio standard + arXiv account) — *decision needed:* the paper uses `carly.r.anderson@gmail.com` | ⚠️ confirm |

**The golden rule:** name is `Carly R. Anderson`, and **every surface links to the ORCID**. Those two moves do most of the disambiguation work.

---

## B · Surface-by-surface action list

Legend: 🟢 I can draft exact text now · 🟡 needs your login to apply · 🔵 needs the Chrome pass to verify first

| # | Surface | Change(s) | Current → Canonical | State |
|---|---|---|---|---|
| 1 | **ORCID** | Name; **add Employment**; reconcile Works title; add DOI when live | "Carly Anderson" → "Carly R. Anderson"; add *HumanAIOS LLC — Founder*; Works title → canonical | 🟢🟡 |
| 2 | **HuggingFace** | Apply P0-1 card redline; retire empty `HumanAIOS2026`; creator name | `HumanAIOS2026` refs → `HumanAIOS`; name → canonical | 🟢🟡 |
| 3 | **humanaios.ai** (hub) | Name; add JSON-LD (`Person` w/ `sameAs`→ORCID/LinkedIn/X, `Organization`, `Dataset`, `SoftwareApplication`); verify HF link → `HumanAIOS/acat-assessments`; link out to all nodes | ensure name canonical; add structured data | 🟢🟡 (deploy) |
| 4 | **GitHub** `humanaios-ui` | Add **link to humanaios.ai**; add name "Carly R. Anderson"; note relationship to `HumanAIOS` (HF) | bio has no hub link, no name → add both | 🟢🟡 |
| 5 | **Substack** `@humanaios` | Display name; **add website link → hub**; align bio | "Carly R Anderson" → "Carly R. Anderson"; add hub link | 🟢🟡 |
| 6 | **arXiv account + paper** | Account **name** → canonical; paper corresponding email (per §A decision); pick CC-BY-4.0 at license step | "Carly Anderson" → "Carly R. Anderson" | 🟡 |
| 7 | **Zenodo** (new) | Author = Carly R. Anderson + ORCID; canonical title; CC-BY-4.0 | (from P0-2 pack) | 🟢🟡 |
| 8 | **X** `@HumanAIOS` | Verify bio + link, then align name/link to canonical | unknown → verify | 🔵 |
| 9 | **LinkedIn** `/in/humanaios` | Verify headline/name/link, then align; confirm it's the canonical entity | unknown → verify | 🔵 |
| 10 | **GitHub Pages** `lasting-light-ai` | Name + fix indexation (P1-4); link hub | client-rendered → needs SSR/static + hub link | 🟡 (dev) |
| 11 | **`rentahuman.ai/humans/8JC…`** | Inventory: keep / fold in / drop; if kept, align name + link | stray, un-inventoried | ⚠️ decide |
| 12 | **Portfolio** (`PORTFOLIO_NIGHT_V1_0.md`) | Fix Substack handle (`@carlyranderson`→`@humanaios`); HF org ref; reconcile stats per canonical-stats pass | stale refs → canonical | 🟢🟡 |

---

## C · Task decomposition (mirrored to empirica tasks)

These are the executable units. I draft the exact text/markup for each 🟢 item; you apply the 🟡; the 🔵 wait on a connected browser.

1. **ORCID pass** — name, employment, works-title, (DOI later).
2. **HuggingFace pass** — apply P0-1 card redline, retire `HumanAIOS2026`.
3. **Hub pass** — name + JSON-LD structured data + link graph (I draft the markup).
4. **GitHub + Pages pass** — hub links, name, indexation spec.
5. **Substack pass** — display name + website link + bio.
6. **arXiv + paper pass** — account name + email decision + CC-BY license step.
7. **X + LinkedIn pass** — Chrome-verify then align *(blocked: browser not connected)*.
8. **Portfolio reconcile** — handle/org/stats fixes.

---

## D · The one Chrome pass we still owe

X (`@HumanAIOS`) and LinkedIn (`/in/humanaios`) are the two audit surfaces I've never been able to read (both bot-wall automated fetches). To verify + align them I need the **Claude browser extension connected** (it isn't this session — `tabs_context` returned "extension not connected"). When you've got Chrome with the extension running and you're logged into both, say so and I'll read both profiles and hand you the exact bio/link edits. Everything else in this map can proceed without it.

---

## What I need from you
1. **Email decision** (§A last row): canonical `aioshuman@gmail.com` everywhere, and update the paper? (Or keep the paper's `carly.r.anderson@gmail.com`?)
2. **`rentahuman.ai`** (row 11): keep, fold in, or drop?
3. **Pick a starting surface** and I'll draft its exact edits first. Recommended order: **ORCID → HuggingFace → Substack** (all fast, high-disambiguation-value, no dev/deploy needed), then the hub JSON-LD (needs a deploy), then the Chrome pass for X/LinkedIn.
