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
| **Version** | `v1.0` |
| **Language** | `eng` |
| **Keywords** | §3 |
| **Access right** | Open Access |
| **License** | See §5 recommendation |
| **Related identifiers** | §4 |
| **Communities** | Suggest: *Artificial Intelligence*, *OpenAIRE*; search "AI safety"/"alignment" communities to join |
| **Funding** | None (self-funded) unless you want to credit anything |

---

## 2 · Draft abstract (DRAFT — verify against the actual paper)

> ⚠️ I do **not** have the paper text, so this is synthesized from your HuggingFace dataset card + portfolio. Treat every bracketed value as "confirm against paper / reconcile per P0-1 Fix 4." Do not publish until you've checked it against what the paper actually claims.

Large language models routinely describe their own behavioral tendencies, yet whether those self-descriptions are *calibrated* to demonstrated behavior is largely unmeasured. We introduce **ACAT (AI Calibrated Assessment Tool)**, an open instrument that quantifies the gap between an AI system's blind self-report and its self-report after exposure to empirical calibration data, across six behavioral dimensions — truthfulness, service, harm awareness, autonomy respect, value alignment, and humility.

From a corpus of **[N]** paired assessment sessions spanning **[18+]** providers, we derive two metrics: the **Self-Assessment Gap (SAG)** and the **Learning Index (LI = post-calibration ÷ blind self-report total)**. We find a systematic gap: **[85.7%]** of systems reduced their self-ratings after calibration exposure (mean LI **[0.843]**); the effect holds across model families and is independent of collection method (API vs. web interface); and **humility** shows the largest cross-provider gap. Psychometric analysis indicates high internal consistency (**Cronbach's α = [0.901]**) and a **bi-factor** latent structure, with provider-level behavioral signatures detectable.

ACAT releases open, reproducible infrastructure — instrument, corpus, and public gap measurement — for research on AI self-description calibration, behavioral observability, and governance. Dataset and code are released openly.

*(~190 words. Trim/expand to Zenodo's taste; Scholar indexes the first ~150 words most heavily, so keep the ACAT definition + the headline finding in the opening sentences.)*

---

## 3 · Keywords

```
AI calibration, self-assessment, large language models, LLM evaluation,
behavioral observability, AI alignment, AI governance, psychometrics,
Learning Index, self-description calibration, model evaluation, RLHF
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

## 5 · License recommendation (your call)

There's a real distinction worth getting right:

- **The preprint text** → recommend **CC-BY-4.0**. It's the scholarly-standard license for preprints, maximizes citation/reuse/translation (pure attraction), and is what Scholar/repositories expect. Apache-2.0 is a *software* license and is an awkward fit for a PDF.
- **The code + dataset** → keep **Apache-2.0** (already on HF) — appropriate for software/data.

So: **CC-BY-4.0 on the Zenodo preprint, Apache-2.0 stays on the corpus/code.** This is consistent with your open-science commitment and is standard practice, not a contradiction. But it's your decision — tell me if you'd rather keep everything Apache-2.0 and I'll adjust.

---

## 6 · OSF alternative (optional, complementary)

Zenodo = DOI + repository. **OSF Preprints** = a preprint-server UI (looks more like a paper landing page) and is also Scholar-indexed. They're not mutually exclusive — some deposit to both. All the metadata above (title, abstract, authors, keywords, license, links) is reusable verbatim on OSF. My recommendation: **Zenodo first** (it's the DOI engine), add OSF later if you want a second discovery surface. No need to do both to start.

---

## 7 · One thing to confirm before you upload

- **arXiv coexistence:** depositing to Zenodo does **not** conflict with your arXiv submission — they're independent systems and cross-posting is normal and allowed. The arXiv moderation hold is about arXiv's own review, not exclusivity. When arXiv clears, we link the records (§4). *(Flagging so it's a conscious choice, not a surprise.)*

---

## What I need from you
1. **The paper PDF (or text)** — so I can finalize the abstract from what it actually says (not my reconstruction).
2. **Stats** (same open item as P0-1 Fix 4) — locks the bracketed numbers.
3. **License** — confirm CC-BY-4.0 for the preprint text (or tell me otherwise).

Give me the PDF + those two answers and I'll return a final, publish-ready metadata block (and the finalized P0-1 README with the real DOI dropped in). Then P0 is essentially closed and we move to **P0-3** (canonical identity applied across surfaces + the X/LinkedIn Chrome pass).
