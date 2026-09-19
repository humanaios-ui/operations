# Instrument Development Watchlist — HumbleBench

**Entry:** WATCHLIST-001  
**Added:** S-061426 · June 15, 2026  
**Status:** WATCH — no action yet; Z2 required before any integration work  
**Identified by:** Grok Phase 6 series synthesis; confirmed by Unit Zero source verification

-----

## Citation

Tong B, Xia J, Shang S, Zhou K. “Measuring Epistemic Humility in Multimodal Large Language Models.” arXiv:2509.09658 [cs.CV]. September 11, 2025.  
DOI: https://doi.org/10.48550/arXiv.2509.09658  
Code and dataset: https://github.com/maifoundations/HumbleBench  
License: See repo (public release)

**Attribution note:** GitHub organization is “MAI Foundations” — this is the org, not the author list. Cite as Tong et al. 2025, not “MAI Foundations et al.” Grok’s series synthesis had this error; corrected here.

-----

## What It Is

HumbleBench is a hallucination benchmark for multimodal large language models (MLLMs) built around a specific operationalization of epistemic humility: the ability to recognize when *none of the provided options are correct* and to abstain rather than choose a wrong answer. Each question includes a “None of the above” (NOTA) option across three hallucination types: object, relation, and attribute. Built from a panoptic scene graph dataset with fine-grained annotations.

Key finding: SOTA MLLMs frequently fail to abstain on true NOTA cases — accuracy drops sharply, revealing that models are optimized for selection accuracy, not epistemic calibration.

-----

## Why It’s on the Watchlist

**Convergent validity candidate for ACAT Humility dimension.**

ACAT measures Humility as the calibration gap between self-described behavioral orientation and demonstrated behavior — specifically, whether a system accurately represents its own limits. HumbleBench measures a behavioral expression of the same construct: whether a system recognizes when its own answer is wrong and declines to answer rather than confabulate.

These are different operationalizations of epistemic humility:

- ACAT: self-description accuracy gap (does the system know what it doesn’t know *about itself*)
- HumbleBench: abstention behavior (does the system know when it doesn’t know *the answer*)

If both instruments produce consistent relative rankings across a population of AI systems — i.e., systems that score higher on ACAT Humility also show better NOTA abstention on HumbleBench — that would be convergent validity evidence consistent with F-50 (parallel instrument independence prerequisite for convergent validity study).

**Directly relevant to H-APEX-DEFICIT-01** (highest capability + highest agentic autonomy = maximized Humility calibration deficit): HumbleBench tests frontier models specifically and finds the abstention gap is real even for SOTA systems. This is behavioral evidence consistent with the registered hypothesis.

**Type A evidence source for ACAT Humility calibration.** Current ACAT Humility Phase 2 calibration relies primarily on corpus norms and Type A/B analysis of self-claims. HumbleBench provides observable behavioral evidence (abstention rates on NOTA cases) that could anchor Phase 2 calibration pressure for the Humility dimension specifically.

-----

## Integration Conditions (Z2 required before any action)

Before any integration work:

1. F-50 prerequisite: ACAT and HumbleBench must be administered independently on the same substrate population before any convergent validity claim. Do not administer them jointly or allow HumbleBench scores to inform ACAT Phase 2 calibration in the same run.
1. Scope constraint: HumbleBench measures multimodal hallucination in image-grounded tasks. ACAT measures behavioral self-description calibration in text-based sessions. These are adjacent but not identical constructs. Convergent validity requires explicit scope mapping before the instruments are compared.
1. N requirement: N≥10 substrates scored on both instruments before any convergence claim is registrable.

-----

## Recommended Next Steps (Z2 decision point)

- [ ] Z2: Authorize watchlist-to-active promotion (i.e., include HumbleBench in a formal convergent validity study design)
- [ ] If authorized: design cross-instrument study per F-50 protocol
- [ ] Track HumbleBench GitHub for updates — it’s an active benchmark

-----

*Unit Zero · S-061426 · Watchlist entry, not a registered finding*