# Phase 0 — HumanAIOS Discoverability Audit & Prioritized Backlog

**Practice:** empirica-outreach · **For:** Carly R. Anderson (Night) / HumanAIOS LLC
**Date:** 2026-07-02 · **Status:** Review-ready (Carly approves → we start Phase 1)
**Method:** Read-only recon of every public surface (search, WebFetch, ORCID public API, HuggingFace org). Two surfaces (X, LinkedIn) are bot-walled and deferred to an authenticated Chrome pass.

**North star:** attraction, not promotion. Every item below grows *discovery + credibility*. Nothing here is broadcasting.

---

## TL;DR — the four things that actually matter

1. **The open corpus is live — but pointed at the wrong door.** *(Corrected 2026-07-02.)* The ACAT corpus **is** public at `HumanAIOS/acat-assessments` (608 rows, your 6 dimensions). The real problem: the portfolio — and likely the hub — reference a *different, empty* org, `HumanAIOS2026`, which 401s; and the live dataset has **no README/card, no license metadata, and no links home**. So your best citable/indexable asset exists but is mis-linked and under-dressed. The fix is cheap: repoint everything to `HumanAIOS`, dress the dataset card, retire the empty org — *not* republish.
2. **Your citation engine is stuck in one queue.** The arXiv preprint is on moderation hold (arXiv-side, unpredictable). Don't wait on it — stand up a **DOI-issuing, Scholar-indexed** node now (Zenodo/OSF) so citations can start accruing. arXiv stays in flight in parallel.
3. **Search can't consolidate "you."** Your name renders three ways across surfaces (*Carly Anderson* / *Carly R Anderson* / *Carly R. Anderson*), your preprint has **two different titles**, and "Anderson + cognition" collides with J.R. Anderson (ACT*). Pick **one** canonical name + **one** canonical title, anchor everything to your ORCID, and the collision starts resolving.
4. **The hub works; the graph around it is broken.** humanaios.ai is indexed and on-message — but only **1 page** is indexed, GitHub doesn't link back to it, ORCID's employment is empty, and Substack has no link home. The pieces exist; they just don't point at each other.

---

## Discoverability Scorecard

Legend: ✅ good · ⚠️ partial / needs work · ❌ missing/broken · — n/a

| Surface | Indexed? | Entity-coherent? | Cross-linked to hub? | Concept-tuned? | Grade |
|---|---|---|---|---|---|
| **humanaios.ai** (hub) | ✅ indexed, on-message snippet | ⚠️ good copy, no verified schema markup | ⚠️ links out, but graph incomplete | ✅ ranks for concept terms | **B** |
| **lasting-light-ai** (GitHub Pages) | ❌ likely client-rendered → empty shell to crawlers | ⚠️ names HumanAIOS, not Carly | ⚠️ unclear | ❌ no crawlable content | **D** |
| **haioscc.pages.dev** | ⚠️ a "command center" app — probably shouldn't be indexed | — | ❌ none | — | **C (hygiene)** |
| **ORCID** `0009-0003-7540-4245` | ✅ (Scholar-trusted) | ⚠️ bio good; **employment empty**; name = "Carly Anderson" | ✅ links humanaios.ai | ✅ | **B–** |
| **HuggingFace** `HumanAIOS/acat-assessments` | ✅ dataset public (608 rows) | ⚠️ no card/license/credit | ⚠️ no links home | ⚠️ underleveraged | **C** |
| **HuggingFace** `HumanAIOS2026` (stale org) | ✅ but **empty** (0 datasets) | ❌ | — | — | **retire** |
| **GitHub** `humanaios-ui` | ✅ | ❌ no Carly name; fragmented vs `HumanAIOS2026` | ❌ **does not link humanaios.ai** | ⚠️ | **C** |
| **Substack** `@humanaios` | ⚠️ thin | ⚠️ "Carly R Anderson"; 6 subs | ❌ no website link | ⚠️ | **C– (greenfield)** |
| **arXiv** (ID 7336774) | ❌ moderation hold | ⚠️ title drift | — | ✅ | **Blocked** |
| **Google/Semantic Scholar** | ❌ no node at all | ❌ Anderson namesake collision | — | — | **F** |
| **X** `@HumanAIOS` | *unverified (402)* | *unverified* | *unverified* | *unverified* | *Chrome pass* |
| **LinkedIn** `/in/humanaios` | *unverified (999)* | *unverified* | *unverified* | *unverified* | *Chrome pass* |

**Conversion channels (not discovery surfaces):** Slack, Gmail (`aioshuman@gmail.com`), Zernio — these are where discovered attention becomes relationships. They anchor Phase 3 measurement, not SEO.

---

## Prioritized Backlog

Ranked by *impact × how much it unblocks other work*. Effort is rough (S/M/L). "Owner" reflects our mode: I draft, you approve/publish.

### P0 — Credibility & citation (do first; these gate everything downstream)

| # | Action | Why | Effort | Owner |
|---|---|---|---|---|
| P0-1 | **Fix corpus pointers + dress the dataset card**: repoint portfolio/hub/all surfaces from `HumanAIOS2026` → `HumanAIOS/acat-assessments`; add a README/dataset-card + license (Apache 2.0) + links to humanaios.ai and the preprint; retire the empty `HumanAIOS2026` org; reconcile the 608-vs-629 row count | The corpus is live but mis-linked and undressed — this converts an existing asset into a citable, discoverable one. Cheap, high payoff. | S–M | I draft card + cross-links; you publish |
| P0-2 | **Stand up a citable preprint node now** on Zenodo (immediate DOI, Scholar-indexed) and/or OSF — route around the arXiv hold | Unlocks the entire citation-authority audience without waiting on arXiv's queue. | M | I draft metadata/abstract/keywords; you upload |
| P0-3 | **Canonicalize identity**: one name form (**"Carly R. Anderson"**), one preprint title, ORCID on every surface | Lets search + Scholar consolidate one author entity and defeat the namesake collision. | S | I produce the canonical-identity sheet; you apply |

### P1 — Authority & entity graph

| # | Action | Why | Effort | Owner |
|---|---|---|---|---|
| P1-1 | **Fill ORCID**: add HumanAIOS LLC employment; reconcile the works to the one canonical title | Employment + consistent works are strong disambiguation signals, currently unused. | S | You (I supply exact text) |
| P1-2 | **Repair cross-links** into one graph: GitHub org → humanaios.ai; Substack → hub; hub ↔ ORCID/HF/GitHub/Substack/preprint (bidirectional) | Turns scattered surfaces into one entity search engines can walk. | S–M | I map every link; you apply |
| P1-3 | **Add JSON-LD structured data** to humanaios.ai: `Organization`, `Person` (with `sameAs` → ORCID/LinkedIn/X), `Dataset`, `SoftwareApplication` (ACAT API) | Makes ACAT + corpus surface as real, rich objects; strengthens entity resolution. | M | I draft the markup; you deploy |
| P1-4 | **Fix lasting-light-ai indexation** — prerender/SSR or ship real static content so crawlers see more than a shell | A JS shell is invisible to search; right now it can't attract anyone. | M–L | I spec the fix; you/dev apply |

### P2 — Surface area, hygiene & measurement

| # | Action | Why | Effort | Owner |
|---|---|---|---|---|
| P2-1 | **Set index policy** on haioscc.pages.dev (likely `noindex` — it's an app, not content) | Keeps the index focused on real content surfaces. | S | You |
| P2-2 | **Inventory the stray surface** `rentahuman.ai/humans/8JC…` linked from GitHub — keep, fold in, or drop | Uncounted surfaces fragment the entity. | S | Decide together |
| P2-3 | **Verify X + LinkedIn** bios/links via the authenticated Chrome pass; align to canonical identity | Close the two unverified surfaces. | S | I run Chrome; you approve edits |
| P2-4 | Expand indexed surface area beyond 1 page — this is what the Phase 2 concept-content engine delivers | More on-topic pages = more ways to be found. | (Phase 2) | Ongoing |

---

## Canonical Identity Sheet — LOCKED (Carly-approved 2026-07-02)

These are now fixed; every Phase 1 edit applies them identically everywhere:

| Field | Canonical value | Notes / reconciliation needed |
|---|---|---|
| **Name form** | **Carly R. Anderson** | ORCID currently credits "Carly Anderson" — update to match. |
| **Preprint title** | **ACAT: Benchmarking Self-Description Calibration in Large Language Models** | ORCID lists a divergent title ("The Self-Assessment Gap…") — reconcile to this. |
| **Canonical hub** | `https://humanaios.ai/` | The one true home; everything links here. |
| **Substack** | `@humanaios` | Portfolio's `@carlyranderson` is stale — fix the portfolio. |
| **HuggingFace org** | `HumanAIOS` (holds `acat-assessments`) | Retire/redirect the empty `HumanAIOS2026`; repoint all references. |
| **Disambiguation anchor** | ORCID `0009-0003-7540-4245` | Linked (`sameAs`) from every surface. |

---

## What I couldn't verify this pass

- **X `@HumanAIOS`** — 402 paywall to automated fetch.
- **LinkedIn `/in/humanaios`** — 999 anti-scraping block.
- **humanaios.ai raw HTML / JSON-LD** — Cloudflare bot-challenge (403); Google crawls it fine, but I need the authenticated browser to read the actual markup.

All three are quick to close with one authenticated **Chrome pass** — which I'd fold into the start of Phase 1 (I'll be editing those surfaces then anyway).

---

## Status & next step

Audit approved · canonical identity locked (above) · corpus finding corrected. **Phase 1 is open.** First moves (the P0 items) unblock the most for all four audiences at once:
- **P0-1** — fix corpus pointers + dress the dataset card (`HumanAIOS/acat-assessments`)
- **P0-2** — stand up a Zenodo/OSF DOI node (route around the arXiv moderation hold)
- **P0-3** — apply the canonical identity across all surfaces (+ close the X / LinkedIn Chrome pass)
