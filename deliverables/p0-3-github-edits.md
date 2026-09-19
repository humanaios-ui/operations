# P0-3 · Task 4 — GitHub Edit Sheet (`humanaios-ui`)

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (you apply)
**Target:** [github.com/humanaios-ui](https://github.com/humanaios-ui)

**Audit gaps this fixes:** the profile **doesn't link `humanaios.ai`** and **doesn't name Carly** — so GitHub sits outside the entity graph. This wires it in.

> ⚠️ **DOI not yet confirmed.** I couldn't resolve `10.5281/zenodo.21135723` via automated fetch (404 — likely fresh-publish propagation lag or bot-blocking). It matches your record id so it's probably right, but **check the DOI badge on the published Zenodo page** and tell me the exact string. I've marked every DOI spot below `‹confirm›`.

---

## 0 · First: is `humanaios-ui` a User or an Organization?

The edit path differs, so check: open the profile — if it has **"People / Teams"** tabs and no green contribution graph, it's an **Org**; if it has a contribution graph + "Achievements," it's a **User**. Apply the matching column below.

---

## 1 · Profile fields

| Field | User account | Organization |
|---|---|---|
| **Name / Display name** | `Carly R. Anderson` | `HumanAIOS` |
| **Bio / Description** | see §2 | see §2 |
| **Website / URL** | `https://humanaios.ai` *(missing — add)* | `https://humanaios.ai` |
| **Company** | `HumanAIOS LLC` | — |
| **Location** | `Fort Walton Beach, FL` | `Fort Walton Beach, FL` |
| **Social accounts** (User: up to 4) / **Description links** (Org) | ORCID, X, LinkedIn, Substack | same |

**Social/`sameAs` links to add:**
- `https://orcid.org/0009-0003-7540-4245`
- `https://x.com/HumanAIOS`
- `https://www.linkedin.com/in/humanaios`
- `https://substack.com/@humanaios`
- *(and reference the HF org `https://huggingface.co/HumanAIOS` in the README)*

---

## 2 · Bio / description (cleanup)

Your current bio has run-together text ("…Platform.100% of profits…") and says **"Pre-launch"** — but humanaios.ai is live, so that undersells you. Replace with:

**Short (User bio / Org description):**
> Open behavioral-observability infrastructure for AI. Building ACAT — measuring the gap between what AI systems say about themselves and how they behave. Apache-2.0 · 100% of profits to recovery. → humanaios.ai

---

## 3 · Profile README (the SEO/attraction centerpiece — paste-ready)

A profile README renders on your profile page and is indexable. Create it:
- **User:** new repo named exactly `humanaios-ui` (same as the username) → add `README.md`.
- **Org:** new repo named `.github` → file at `profile/README.md`.

Paste this in:

```markdown
## HumanAIOS — Behavioral Observability for AI

Open infrastructure measuring **self-description calibration** in AI systems:
the gap between what AI systems describe about their own behavior and how those
descriptions shift when shown empirical peer data.

Our instrument, **ACAT (AI Calibrated Assessment Tool)**, benchmarks this across
model families — finding a systematic **Self-Assessment Gap** that holds across
providers. Instrument, dataset, and methodology are all open.

### The work
- 🌐 Site — https://humanaios.ai
- 📄 Preprint — DOI [10.5281/zenodo.21135723](https://doi.org/10.5281/zenodo.21135723) ‹confirm DOI›
- 📊 Open dataset — https://huggingface.co/datasets/HumanAIOS/acat-assessments
- 🧭 ORCID — https://orcid.org/0009-0003-7540-4245

### Maintainer
**Carly R. Anderson** — Founder & Principal Investigator, HumanAIOS LLC (Lasting Light AI).
Independent AI-safety research. Open science; 100% of long-term profit reinvested in recovery programs.

*Attraction, not promotion.*
```

---

## 4 · Pinned repositories

Pin the repos that best represent the work, each with a **clear one-line description** (repo descriptions are indexed):
- `lasting-light-ai` — "ACAT / AI governance-awareness assessment platform" *(fix indexation separately — P1-4)*
- `operations` — "Open OR&D governance: calibration, observability, telemetry"
- If there's a dedicated ACAT instrument/API repo, pin it too and link it from humanaios.ai.

Make sure each pinned repo's **About** field (top-right of the repo) has a description + the `humanaios.ai` link + topics (e.g. `ai-safety`, `calibration`, `llm-evaluation`).

---

## 5 · Two housekeeping items
- **Namespace consistency:** GitHub is `humanaios-ui`, HuggingFace is `HumanAIOS`. That's fine — just make sure the README + hub cross-reference both so they read as one entity.
- **`rentahuman.ai/humans/8JC…`** — this is linked from your current bio. Decision still open: keep, fold in, or drop? (It's an un-inventoried surface; I'd drop it from the bio unless it's intentional.)

---

## Apply order
1. Add **website link** (`humanaios.ai`) + **name** → 2. Fix **bio** → 3. Add **social links** → 4. Create the **profile README** → 5. Tidy **pinned repos** + About fields.

Next surface: **HuggingFace** card (apply the P0-1 redline) — or the Chrome-gated **X/LinkedIn** pass once the extension's connected.
