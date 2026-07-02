# P0-2 — Zenodo Submission Pack (ACAT Preprint)

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Review-ready (you upload the PDF + publish)
**Goal:** Mint an immediate, resolvable, Scholar-indexed **DOI** for the ACAT preprint — independent of the arXiv moderation queue — and use it as the canonical citation anchor everywhere (fills the `<ZENODO_DOI>` placeholders in P0-1).

> **Why Zenodo now:** arXiv is stuck in moderation with no ETA. Zenodo (CERN-operated) mints a DOI on publish, is indexed by Google Scholar + OpenAIRE, and lets you version the record later. This gives the research-authority + citation audiences a real, citable node **today**. arXiv stays in flight; when it clears, we cross-link the two (see Related Identifiers).

---

## 1 · Ready-to-paste Zenodo metadata

Fill Zenodo's *New upload* form with these values. *(Field labels are stable but verify against the live form as you go.)*

| Zenodo field | Value |
|---|---|
| **Upload type** | Publication |
| **Publication type** | Preprint |
| **DOI** | *(leave blank — Zenodo mints one; or "Reserve DOI" to get it before publishing so you can print it in the PDF)* |
| **Publication date** | *(date you publish, or the paper's completion date)* |
| **Title** | `ACAT: Benchmarking Self-Description Calibration in Large Language Models` |
| **Authors** | `Anderson, Carly R.` · ORCID `0009-0003-7540-4245` · Affiliation `HumanAIOS LLC (Lasting Light AI)` |
| **Description** | Draft abstract in §2 (verify vs paper) |
| **Version** | `v1.0` (Zenodo record; paper is Preprint **v5.0**, March 2026) |
| **Language** | `eng` |
| **Keywords** | §3 |
| **Access right** | Open Access |
| **License** | See §5 recommendation |
| **Related identifiers** | §4 |
| **Communities** | Suggest: *Artificial Intelligence*, *OpenAIRE*; search "AI safety"/"alignment" communities to join |
| **Funding** | None (self-funded) unless you want to credit anything |

---

## 2 · Abstract — FINAL (from the paper, v5.0)

Use the paper's own abstract **verbatim** — this Zenodo record describes *this paper*, so the abstract should match the PDF exactly:

> We introduce ACAT (AI Calibrated Assessment Tool), an open-source instrument that measures self-description calibration in AI systems. Using a three-phase protocol—blind self-report, empirical calibration, and corrected self-report—we quantify the Self-Assessment Gap (SAG): the difference between what AI systems describe about their own capabilities and how those descriptions change when exposed to empirical peer data. Across 35 models from 11 providers, assessed by two independent collectors using different methods (API-based and manual web-based), we find a mean SAG of 67.8 points on a 600-point scale (SD = 62.3). The Learning Index (LI)—the ratio of post-calibration to pre-calibration composite scores—averages 0.87 (SD = 0.12), meaning AI systems reduce their self-ratings by approximately 13% after encountering calibration information. These findings reproduce across both data collection methods with no statistically significant difference in LI between collectors (t(22.4) = −1.46, p > .05). We identify five behavioral response patterns and three anomalous categories, with Value Alignment emerging as the consistently weakest self-assessed dimension across all models and providers. Humility score is the strongest single-dimension predictor of overall calibration response. The instrument, dataset, and methodology are freely available. ACAT measures self-description consistency—how AI systems describe their limitations and how those descriptions shift when calibration data is introduced—providing a diagnostic foundation for transparency practices independent of predictive validity.

✅ Self-consistent, no bracket-filling needed. **Critical:** these are the paper's **35-model** numbers (SAG 67.8, LI **0.87**). Do **not** overwrite them with the corpus/portfolio figures (0.843 / 0.8632) — those describe a different, larger object. See the stats note in §4.

---

## 3 · Keywords

```
AI Self-Assessment, Self-Description Calibration, Behavioral Transparency,
AI Governance, Learning Index, Self-Assessment Gap, large language models,
LLM evaluation, AI alignment, calibration, RLHF, psychometrics
```

*(Zenodo keywords double as discovery terms. These mirror the concept vocabulary the audit found people actually search — and deliberately pair "self-description calibration" with the broader "LLM evaluation" / "AI governance" terms so the record surfaces to adjacent readers.)*

---

## 4 · Related identifiers (the hub graph — this is where attraction compounds)

Add each on the Zenodo form as *Related identifier* + *Relation*:

| Identifier | Relation | Purpose |
|---|---|---|
| `https://huggingface.co/datasets/HumanAIOS/acat-assessments` | **is supplemented by** | Links preprint → open corpus (reviewers can replicate) |
| `https://humanaios.ai/` | **is documented by** | Ties the DOI to the canonical hub |
| `https://orcid.org/0009-0003-7540-4245` | *(author ORCID — attach on the author, not here)* | Author disambiguation |
| GitHub repo (e.g. `github.com/humanaios-ui/...`) | **is supplemented by** | Code provenance |
| arXiv id *(when moderation clears)* | **is identical to** / **is previous version of** | Merges the two records so citations consolidate |

> After publish, the reverse links matter too: update the **HF dataset card** (P0-1 Fix 2/3) to cite this DOI, add the DOI to **ORCID → Works**, and put it on **humanaios.ai**. That closes the loop — every surface points at one citable object.

---

## 5 · License — researched + confirmed (one decision for you)

I checked this against arXiv's own license documentation:

- **arXiv recommends CC-BY-4.0** as the most liberal option and states that, all else equal, you should maximize access by using it. The choice is **irrevocable**.
- **Apache-2.0 is a *software* license** — and it is **not in arXiv's license menu at all** (arXiv offers only CC-BY-4.0, CC-BY-SA-4.0, CC-BY-NC-SA-4.0, CC0, or the arXiv perpetual non-exclusive license). Your PDF currently brands itself "Apache 2.0 License," but you literally cannot select Apache when submitting to arXiv — a document license must be chosen regardless.

**Recommendation (confirmed): CC-BY-4.0 on the paper text (Zenodo *and* arXiv); keep Apache-2.0 on the code + dataset.** The split is standard open-science practice and fully consistent with your open commitment — the paper is a document; the corpus/instrument are software/data. Because it's irrevocable, this is the one call I want you to make consciously. Say the word and I lock CC-BY-4.0 into both the Zenodo metadata and the P0-1 citation.

---

## 6 · OSF alternative (optional, complementary)

Zenodo = DOI + repository. **OSF Preprints** = a preprint-server UI (looks more like a paper landing page) and is also Scholar-indexed. They're not mutually exclusive — some deposit to both. All the metadata above (title, abstract, authors, keywords, license, links) is reusable verbatim on OSF. My recommendation: **Zenodo first** (it's the DOI engine), add OSF later if you want a second discovery surface. No need to do both to start.

---

## 7 · One thing to confirm before you upload

- **arXiv coexistence:** depositing to Zenodo does **not** conflict with your arXiv submission — they're independent systems and cross-posting is normal and allowed. The arXiv moderation hold is about arXiv's own review, not exclusivity. When arXiv clears, we link the records (§4). *(Flagging so it's a conscious choice, not a surprise.)*

---

## What I need from you
1. ✅ **Paper** — received; abstract finalized above (verbatim from the PDF). No longer blocking.
2. **License** — one conscious, irrevocable call: confirm **CC-BY-4.0** for the paper text (§5). I won't set it without your yes.
3. **Stats governance** — agree that the **paper's** numbers (35 models, SAG 67.8, LI 0.87) govern the Zenodo record, while the *corpus* numbers stay on the *dataset* card. Your "canonical stats" pass then aligns the portfolio to whichever object each figure describes.

Say **"yes CC-BY"** and I'll drop the final license into both this pack and the P0-1 citation — making P0-1 + P0-2 publish-ready. Then we move to **P0-3** (canonical identity across surfaces + X/LinkedIn Chrome pass).
