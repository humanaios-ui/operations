# P0-3 · Task 5 — Substack Edit Sheet

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (you apply)
**Profile:** `substack.com/@humanaios`

**Scope note:** this is the *identity/discoverability* pass (P0-3) — name, bio, links, About-page SEO. It is **not** the content engine (that's Phase 2). Goal here: make Substack a clean node in the hub graph, not a stranded profile with 6 subscribers and no link home.

> **What I could verify** (audit): handle `@humanaios`, display name "Carly R Anderson", a short bio, **no website link**, ~6 subscribers. **What I couldn't** (needs the browser): your exact *publication* name, whether an About page/posts exist, custom domain. Items below tagged 🔎 depend on that — confirm/adjust when you're in the dashboard.

---

## 1 · Profile (Settings → your profile)

| Field | Set to |
|---|---|
| **Display name** | `Carly R. Anderson` *(add the period — currently "Carly R Anderson")* |
| **Handle** | `@humanaios` *(keep — canonical)* |
| **Bio** (short) | see below |
| **Website / link** | `https://humanaios.ai` *(currently missing — add it)* |

**Bio (paste):**
> Founder, HumanAIOS LLC. I build **ACAT** — an open instrument measuring the gap between what AI systems say about themselves and how they actually behave. Open science, Apache-2.0. → humanaios.ai

---

## 2 · Social / cross-links (Settings → profile links, if available)

Add whatever link slots the profile offers — these are your `sameAs` anchors:

- `https://humanaios.ai`
- `https://orcid.org/0009-0003-7540-4245`
- `https://huggingface.co/datasets/HumanAIOS/acat-assessments`
- `https://github.com/humanaios-ui`
- `https://x.com/HumanAIOS`

---

## 3 · Publication settings 🔎 (Dashboard → Settings)

*(Applies if `@humanaios` has a publication, which the subscriber count implies.)*

| Field | Recommended value |
|---|---|
| **Publication name** | `HumanAIOS` (or `HumanAIOS — Behavioral Observability for AI`) |
| **Short description / tagline** *(this is your SEO meta description)* | `Open research on AI self-description calibration — measuring the gap between what AI systems claim about themselves and what they demonstrate. From HumanAIOS / Lasting Light AI.` |
| **Logo / cover** | Keep consistent with humanaios.ai branding |
| **Topics/categories** | `Technology`, `AI`, `Science` |

---

## 4 · About page 🔎 (Dashboard → Settings → About)

This is the highest-SEO-value piece — an indexable page that both explains the work *and* wires the whole entity graph together. Paste-ready:

---

**About HumanAIOS**

HumanAIOS builds open **behavioral observability** infrastructure for AI systems. Our core instrument, **ACAT (AI Calibrated Assessment Tool)**, measures *self-description calibration* — the gap between what AI systems describe about their own behavior and how those descriptions shift when they see empirical peer data.

Across 35 models from 11 providers, ACAT finds a systematic **Self-Assessment Gap**: systems reduce their self-ratings once shown calibration data. Everything is open — the instrument, the dataset, and the methodology.

**The work**
- 🌐 Site: [humanaios.ai](https://humanaios.ai)
- 📄 Preprint: DOI [10.5281/zenodo.21135723](https://zenodo.org/records/21135723) *(live once you publish the Zenodo deposit)*
- 📊 Open dataset: [HumanAIOS/acat-assessments](https://huggingface.co/datasets/HumanAIOS/acat-assessments)
- 💻 Code: [github.com/humanaios-ui](https://github.com/humanaios-ui)
- 🧭 ORCID: [0009-0003-7540-4245](https://orcid.org/0009-0003-7540-4245)

**Who**
Carly R. Anderson — Founder & Principal Investigator, HumanAIOS LLC (Lasting Light AI). Independent AI-safety and behavioral-observability research. Open science; 100% of long-term profit reinvested in recovery programs.

*Attraction, not promotion.*

---

## 5 · Apply order
1. **Display name** (add the period) → 2. **Add website link** (the missing-link fix) → 3. **Bio** → 4. **Publication tagline** 🔎 → 5. **About page** 🔎.

## What I need from you
- Confirm the **publication name** (or tell me the current one and I'll tune the tagline/About to match).
- The 🔎 items are best done together in one dashboard pass — ping me from the browser if you want me to verify the current state live (once the Chrome extension is connected).

Next surface after this: **HuggingFace** (apply the P0-1 card redline) — or we regroup once you've published Zenodo + applied ORCID/Substack.
