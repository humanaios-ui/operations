<!--
UPLOAD INSTRUCTIONS (this file becomes the README.md of the HF dataset):
1. Copy everything BELOW this comment block.
2. Go to https://huggingface.co/datasets/HumanAIOS/acat-assessments → "Edit dataset card".
3. Paste as README.md and Commit. The YAML front-matter sets the license (apache-2.0)
   and metadata — this is what makes the dataset's license show up (currently: none).
4. ⚠️ RECONCILE THE ROW COUNT FIRST: the live dataset shows 608 rows; your CV/apps say 629.
   Set the numbers below to whatever is actually true, and make the CV + both apps match.
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

> ⚠️ **Confirm these against the actual uploaded rows before publishing.** The live viewer
> currently shows **608 rows**; the research archive is cited elsewhere as **629 assessments**
> (516 Phase-1 / 307 LI-scored). State the true relationship — e.g. "608 in this cleaned
> public release, from a 629-assessment archive" — and make the CV + both funding apps match.

| Field | Value |
|---|---|
| Public rows (this release) | 608 *(confirm)* |
| Full research archive | 629 assessments (516 Phase-1, 307 LI-scored) *(confirm)* |
| Providers | 18 *(confirm the public export matches)* |
| Mean Learning Index | 0.8632 (clean, unanchored, v5.3+) |
| Cronbach's α | 0.901 |
| PC1 (variance explained) | 68.9% |

## Data fields
Per row: timestamp · agent/model name · provider · the 12 dimension scores · total. *(Confirm the public export includes all 12 dimensions, not only the Core-6, so the "12-dimension" claim is verifiable in the data itself.)*

## Intended use & limits
- **Use:** research on AI behavioral integrity, self-report reliability, and evaluation methodology.
- **Not:** a sentience or consciousness measure; a certification of any specific model. Predictive criterion validity (whether the LI predicts deployed behavior) is **not yet established** and is active research.

## Citation
> Anderson, C. R. (2026). *ACAT: Benchmarking Self-Description Calibration in Large Language Models.* Manuscript under review. Dataset: HumanAIOS/acat-assessments, Apache-2.0.
