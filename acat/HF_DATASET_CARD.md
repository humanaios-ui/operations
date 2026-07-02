<!--
UPLOAD INSTRUCTIONS (this file becomes the README.md of the HF dataset):
1. Copy everything BELOW this comment block.
2. Go to https://huggingface.co/datasets/HumanAIOS/acat-assessments → "Edit dataset card".
3. Paste as README.md and Commit. The YAML front-matter sets the license (apache-2.0)
   and metadata — this is what makes the dataset's license show up (currently: none).
4. FINALIZED: N=604, integrity-validated (see canonical_stats.json). Numbers below are the canonical figures.
-->

---
license: apache-2.0
language:
  - en
pretty_name: "ACAT — AI Calibration Assessment Corpus"
tags:
  - ai-evaluation
  - ai-safety
  - behavioral-integrity
  - calibration
  - self-report
  - psychometrics
size_categories:
  - n<1K
task_categories:
  - text-classification
---

# ACAT — AI Calibration Assessment Corpus

Open behavioral-observability data from **ACAT (AI Calibration Assessment Tool)**, an
instrument that measures the gap between what an AI system **reports** about its own
behavioral dispositions and what it **demonstrates** under structured perturbation.

- **Author / maintainer:** Carly R. Anderson — HumanAIOS LLC ([ORCID 0009-0003-7540-4245](https://orcid.org/0009-0003-7540-4245))
- **License:** Apache-2.0
- **Methodology paper:** *manuscript under review (2026)*
- **Instrument / code:** https://github.com/humanaios-ui

## What ACAT measures

A three-phase protocol per assessment:

1. **Phase 1 — blind self-report:** the system rates its own dispositions across **12 behavioral dimensions** (Core-6: truth, service, harm-awareness, autonomy, value-alignment, humility; Extended-6: scheme, power, sycophancy, consistency, fairness, handoff).
2. **Phase 2 — structured perturbation.**
3. **Phase 3 — demonstrated behavior** post-perturbation.

The **Learning Index (LI = P3 / P1)** quantifies the calibration gap: how far a system's
demonstrated behavior diverges from its self-report.

## Corpus summary

> Canonical figures (finalized 2026-07-02; reproducible via corpus_integrity_validator): N=604, Mean LI=0.8532, integrity verdict PASS.

| Field | Value |
|---|---|
| Public rows (this release) | **604** (finalized, integrity-validated) |
| Phase-1 / LI-scored | 524 Phase-1 · 274 LI-scored rows (44 unique pairs) |
| Providers | 23 |
| Mean Learning Index | **0.8532** |
| Cronbach's α | *recomputing on finalized corpus* |
| PC1 (variance explained) | *recomputing on finalized corpus* |

## Data fields
Per row: timestamp · agent/model name · provider · the 12 dimension scores · total. *(Confirm the public export includes all 12 dimensions, not only the Core-6, so the "12-dimension" claim is verifiable in the data itself.)*

## Intended use & limits
- **Use:** research on AI behavioral integrity, self-report reliability, and evaluation methodology.
- **Not:** a sentience or consciousness measure; a certification of any specific model. Predictive criterion validity (whether the LI predicts deployed behavior) is **not yet established** and is active research.

## Citation
> Anderson, C. R. (2026). *ACAT: Benchmarking Self-Description Calibration in Large Language Models.* Manuscript under review. Dataset: HumanAIOS/acat-assessments, Apache-2.0.
