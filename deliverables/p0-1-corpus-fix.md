# P0-1 — ACAT Corpus: Card Redline + Repoint Checklist

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (you apply/publish)
**Target:** `https://huggingface.co/datasets/HumanAIOS/acat-assessments`

> **Recalibration up front:** the corpus is in good shape. The dataset **is** public and the card **already exists and is strong** (Apache-2.0, good discovery tags, full schema, LI math, findings, provider table, biases, citation). My Phase 0 audit was too pessimistic here — it inferred "missing" from incomplete fetches. So P0-1 is a **surgical redline of what's already there**, not a rebuild. Five small fixes, one of which is genuinely important.

---

## Fix 1 — 🔴 Broken pointer inside the card (do this first)

The card's own **How to Use** example loads the *empty* org, so anyone who copy-pastes it hits a dead 401:

```diff
- dataset = load_dataset("HumanAIOS2026/acat-assessments")
+ dataset = load_dataset("HumanAIOS/acat-assessments")
```

This is the single highest-value fix in all of P0-1 — it's the exact "wrong door" from the audit, sitting in your most-copied code block.

## Fix 2 — Canonical citation (title + author + ORCID)

The BibTeX currently uses a **third** distinct title and a non-canonical author form. Align to the locked identity:

```diff
  @misc{anderson2026acat,
-   title={Self-Assessment Gap in AI Systems: Measuring Calibration Accuracy Across Six Behavioral Dimensions},
+   title={ACAT: Benchmarking Self-Description Calibration in Large Language Models},
-   author={Anderson, Carly (Night)},
+   author={Anderson, Carly R.},
    year={2026},
-   note={arXiv preprint arXiv:submit/7336774},
+   note={Preprint (arXiv moderation pending); DOI: <ZENODO_DOI once P0-2 lands>},
    institution={HumanAIOS / Lasting Light AI},
+   howpublished={\url{https://orcid.org/0009-0003-7540-4245}},
    url={https://humanaios.ai}
  }
```

- **Title:** three versions exist across arXiv/ORCID/this card — this collapses them to the one canonical form so Scholar can consolidate one work.
- **Author:** `Anderson, Carly R.` matches the locked name; helps defeat the namesake collision.
- **ORCID** added as the disambiguation anchor.

## Fix 3 — Non-resolvable arXiv id

Inline text reads `arXiv preprint: arXiv:submit/7336774`. That `submit/…` id is a *submission handle*, not a citable arXiv id, and the paper is on moderation hold — so today it resolves to nothing.

```diff
- The ACAT instrument and research program are maintained by HumanAIOS / Lasting Light AI (Night, Founder; Cherokee Nation citizen). arXiv preprint: arXiv:submit/7336774.
+ The ACAT instrument and research program are maintained by HumanAIOS / Lasting Light AI
+ (Carly R. Anderson, Founder). Preprint: DOI <ZENODO_DOI> (P0-2); arXiv id pending moderation.
```

*(Swap in the Zenodo DOI from P0-2 — that becomes your resolvable, Scholar-indexed citation anchor while arXiv is stuck.)*

## Fix 4 — ⚠️ Stats reconciliation (needs your decision)

The card and the portfolio report **different headline numbers**. Search/citation-wise it's fine that they differ; credibility-wise they must not contradict:

| Metric | Dataset card | Portfolio (v5.3+ frozen) |
|---|---|---|
| Total rows / N | 608 | 629 |
| Mean Learning Index | 0.843 | 0.8632 |
| Complete LI records | 278 | 307 |
| Model/analysis scope | "35-model" | — |

**Which is canonical?** Likely the frozen v5.3+ archive (629) is a later cut than what's published (608). Tell me which is the source of truth and I'll align the other surface to it — I won't guess and hard-code a number into your published research.

## Fix 5 — Optional enrichers (low effort, nice lift)

- Add a **Links** line near the top: hub (`humanaios.ai`), ORCID, GitHub (`humanaios-ui`), Substack (`@humanaios`) — turns the card into a hub-graph node.
- Once the Zenodo DOI exists, add HF's `doi:` frontmatter field so the dataset itself is citable with a DOI badge.

---

## Repoint checklist (`HumanAIOS2026` → `HumanAIOS`)

The empty `HumanAIOS2026` org is the fragmentation source. Everywhere it (or the wrong dataset path) appears, repoint:

- [ ] **HF card** — the `load_dataset(...)` line (Fix 1). ✅ redline ready above.
- [ ] **Portfolio** — "Selected contributions" / "Key outputs" list the archive as `HumanAIOS2026/acat-assessments` → change to `HumanAIOS/acat-assessments`.
- [ ] **humanaios.ai hub** — verify the "open dataset on Hugging Face" link target points to `HumanAIOS/acat-assessments`. *(I couldn't read the hub's HTML — Cloudflare-blocked; I'll confirm this in the Phase-1 Chrome pass.)*
- [ ] **Empty `HumanAIOS2026` org** — retire it, or set its profile to redirect/point at `HumanAIOS` so stray inbound links don't dead-end.
- [ ] Grep any other surfaces (Substack posts, GitHub READMEs, X bio links) for `HumanAIOS2026`.

---

## What I need from you
1. **Fix 4** — which stats are canonical (608/0.843/278 vs 629/0.8632/307)?
2. Green-light Fixes 1–3 + 5 as written, and I'll hand you the final paste-ready README.

Then P0-1 closes and we move to **P0-2** (Zenodo/OSF DOI) — which also feeds the `<ZENODO_DOI>` placeholders above.
