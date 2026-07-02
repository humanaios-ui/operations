# HumanAIOS SEO/Attraction — Execution Checklist

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Updated:** 2026-07-02 · Single source of truth for "what's ready + what's needed from you"

**North star:** attraction, not promotion. One consolidated entity → all four audiences find you.

---

## ✅ Done
- **Zenodo preprint PUBLISHED** — DOI `10.5281/zenodo.21135723` (live, wired into all deliverables).
- Full **discoverability audit** + strategy (`phase0-discoverability-audit.md`).
- **License locked:** CC-BY-4.0 (paper) / Apache-2.0 (code + data).
- **Canonical identity locked:** name `Carly R. Anderson`, title *ACAT: Benchmarking…*, hub `humanaios.ai`, Substack `@humanaios`, HF org `HumanAIOS`, ORCID anchor.

---

## 🟢 Apply queue — drafts ready, waiting on you (in priority order)

| # | Task | Draft | Effort | Notes |
|---|---|---|---|---|
| 1 | **ORCID** — name, **employment**, websites, keywords, Works (DOI auto-import) | `p0-3-orcid-edits.md` | ~7 min | Highest disambiguation value. Do Works step now (Zenodo is live). |
| 2 | **HuggingFace card** — fix `load_dataset` pointer, citation → canonical + DOI, retire `HumanAIOS2026` | `p0-1-corpus-fix.md` | ~10 min | ⚠️ Fix 4 (stats) needs your number decision first. |
| 3 | **Substack** — display name, **add hub link**, About page | `p0-3-substack-edits.md` | ~5 min | Confirm publication name. |
| 4 | **GitHub** — add hub link + name, bio, profile README | `p0-3-github-edits.md` | ~8 min | Check user-vs-org first (README path differs). |
| 5 | **Hub JSON-LD** — paste block into `humanaios.ai` `<head>` + validate | `p0-3-hub-jsonld.md` | ~5 min | Confirm logo/API URLs. Needs a site deploy. |
| 6 | **arXiv** — open submission detail; if PDF-from-TeX, re-upload TeX source; else send email A/B | `arxiv-hold-action-plan.md` | ~15 min | Diagnosis + 2 ready emails inside. |
| 7 | **Portfolio reconcile** — Substack handle, HF org, stats | (part of `p0-3-canonical-identity-map.md`) | ~5 min | After stats decision. |

---

## 🟡 Open decisions (only you can make these)

1. **Canonical stats** — which numbers are authoritative? *(gates HF Fix 4 + portfolio)*
   - Paper/Zenodo: 35 models, SAG 67.8, **LI 0.87** · Dataset card: 608 rows, **LI 0.843** · Portfolio: 629 / **0.8632** / 307.
   - Recommended: paper governs citation layer, dataset card governs corpus layer, align portfolio to match. *(Or verify via Supabase once you authenticate.)*
2. **Canonical email** — `aioshuman@gmail.com` everywhere (+ fix the paper), or keep the paper's `carly.r.anderson@gmail.com`?
3. **`rentahuman.ai`** surface — keep, fold in, or drop from bios?
4. **Substack publication name** — confirm current name.
5. **GitHub account type** — user or org? (picks the profile-README path)

---

## 🔵 Blocked / deferred (not on the critical path)

- **X + LinkedIn** identity pass — needs the **Claude browser extension connected** + you logged in. Then I verify + hand you exact edits.
- **Supabase MCP** — configured; needs your **OAuth** (`claude /mcp` in a regular terminal). Once done, I can query the corpus to **settle the canonical stats** definitively.
- **`lasting-light-ai`** indexation — client-rendered; needs an SSR/prerender/static fix (dev work).
- **Agent Skills** (`npx skills add supabase/agent-skills`) — optional; your call to run.

---

## 📁 Deliverable index (all in `deliverables/`, branch `outreach/phase0-audit`)
| File | What |
|---|---|
| `phase0-discoverability-audit.md` | The audit + P0/P1/P2 backlog |
| `p0-1-corpus-fix.md` | HF dataset card redline + repoint |
| `p0-2-zenodo-submission-pack.md` | Zenodo deposit (published) |
| `arxiv-hold-action-plan.md` | arXiv hold diagnosis + 2 emails |
| `p0-3-canonical-identity-map.md` | Master identity map (12 surfaces) |
| `p0-3-orcid-edits.md` · `p0-3-substack-edits.md` · `p0-3-github-edits.md` · `p0-3-hub-jsonld.md` | Per-surface edits |
| `zenodo-api-helpers.md` | Run-it-yourself Zenodo API scripts |
| `EXECUTION-CHECKLIST.md` | This file |

---

## Suggested order of operations
1. **Apply ORCID** (Zenodo's live — do the Works auto-import) → biggest single win.
2. **Decide the canonical stats** → unblocks HuggingFace + portfolio.
3. **Apply HuggingFace, Substack, GitHub, Hub JSON-LD** → the entity graph is now consolidated.
4. **Work the arXiv hold** (check TeX source first).
5. When convenient: **authenticate Supabase** (I verify stats) + **connect Chrome** (I finish X/LinkedIn).

That completes P0. Then P1 (JSON-LD deploy, `lasting-light-ai` indexation) and P2 (the Phase-2 content engine on Substack) are the compounding follow-ons.
