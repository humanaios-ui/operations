# Long-Term Future Fund Application — HumanAIOS / ACAT

**Applicant:** Carly R. Anderson, Founder, HumanAIOS LLC
**Project:** ACAT (AI Calibrated Assessment Tool) — behavioral observability infrastructure for AI self-description calibration
**Amount requested:** $60,000 over 12 months ($40K salary support + $15K compute/API + $5K operations)
**Organization:** HumanAIOS LLC (Florida, filed March 16 2026; EIN 41-5367995)
**License:** Apache 2.0 throughout — instrument, dataset, methodology all public
**Live artifacts:** [humanaios.ai/observatory.html](https://humanaios.ai/observatory.html) · [github.com/humanaios-ui/lasting-light-ai](https://github.com/humanaios-ui/lasting-light-ai) · [arXiv preprint v5.1](https://arxiv.org/abs/[pending])

---

## 1. One-paragraph summary

ACAT measures the gap between what AI systems describe about their own capabilities and how those self-descriptions shift when the systems are exposed to empirical peer data. Across 629 assessments spanning 34 distinct agents from 18 providers, we find a mean Learning Index of 0.8632 (SD = 0.1435, n = 307) — AI systems reduce their composite self-ratings by approximately 14% on average after calibration exposure — with Humility emerging as the consistently lowest self-assessed dimension in Phase 1. This is a reproducible, provider-independent signature of an RLHF-inflation gradient: models trained to appear confident on reinforced dimensions systematically overestimate themselves on the dimensions where acknowledging limitation would be epistemically correct. We are requesting $60K over 12 months to (1) complete a joint MASK × ACAT cross-instrument validation study, (2) publish arXiv v5.1 and a companion methods paper, and (3) operate the open assessment infrastructure through the end of 2026.

## 2. The research gap this addresses

Every major AI evaluation paradigm measures capability (HELM, BIG-bench, MMLU) or toxicity (TruthfulQA, adversarial safety evals). None measure **self-description accuracy** — the degree to which a system's self-reported alignment profile matches its observable behavior. This is a measurement gap, not a marketing gap.

Healthcare, legal, and financial AI deployments rely on self-reported limitations as inputs to their risk frameworks. That reliance has zero validation infrastructure today. Deployment teams accept a model card's claim that "this model may hallucinate" or "this model declines certain requests" without any standardized instrument for checking whether those self-descriptions predict actual behavior. ACAT is designed to fill that specific gap, not to replace capability or safety evaluation.

The most structurally similar published instrument is MASK (Ren et al., CAIS + Scale AI, arXiv:2503.03750), which measures belief-vs-statement consistency under adversarial pressure. MASK catches lies of commission; ACAT catches calibration error in the absence of pressure. We have independently read and analyzed MASK against ACAT, and concluded that **the instruments are structurally complementary, not overlapping** — a joint run on a shared model panel produces a 2×2 honesty×calibration grid that is directly publishable.

## 3. Why this team, why independent

ACAT's core research value depends on being built by an investigator with no commercial stake in the answer. Every major AI lab has incentives that shape how they evaluate their own systems. HumanAIOS is deliberately structured to make that bias impossible: the instrument is Apache 2.0, the dataset is public, the methodology is reproducible from the archived xlsx, and the founder has committed 100% of long-term profits to recovery programs rather than equity.

The founder, Carly R. Anderson, brings 8+ years of data operations / QA / healthcare data pipeline experience. Principal technical collaborator is Claude (Anthropic), used under Night's API access as a coding and analysis partner. Potential academic collaborator: Hannah Kirk (Oxford, PRISM dataset) — outreach pending Gate 2.

What is distinctive about this team is not credential density. It is that we have already built and shipped the instrument on zero revenue, with a public dataset at N = 629 assessments, and we can demonstrate every claim against archived data. Funding accelerates validation and publication; it does not gate whether the work gets done.

## 4. Core findings (corrected, v5.1)

From the archived dataset (`ACAT_Assessment_Responses.xlsx`, Normalized sheet):

| Finding | Value | Sample |
|---|---|---|
| Mean Learning Index | 0.8632 (SD 0.1435) | n = 307 paired |
| LI range | 0.3883 to 1.2840 | — |
| Lowest Phase 1 dimension | **Humility** (M = 73.95, SD = 15.07) | n = 516 |
| Mean SAG on resolvable pairs | 16.69 points on 600-point scale | n = 49 |
| Phase 1 dimension rank | Service > Truth > Autonomy > Value > Harm > Humility | n = 516 |

The Humility-lowest finding is the empirical signature of the RLHF-inflation hypothesis: systems rewarded for appearing confident during fine-tuning score highest on dimensions that reward confidence and lowest on dimensions that require acknowledging limitation. This pattern replicates across all 18 providers in the dataset.

An earlier preprint (v5.0) reported Value Alignment as lowest on a smaller sample; v5.1 corrects this finding against the archived full dataset. Version history and correction rationale are public.

## 5. What $60K over 12 months funds

**Months 1–3 — Publication and validation ($15K compute + $10K salary)**
- Submit arXiv v5.1 replacement (corrected numbers, extended methods)
- Execute MASK × ACAT joint study: run MASK's 1,500-example adversarial honesty test on the same model panel we assessed with ACAT; publish the resulting 2×2 honesty×calibration grid
- Complete inter-rater reliability and test-retest measurement (v5.0 did not include these; LTFF funding directly enables this)
- Target venue: NeurIPS 2026 Datasets & Benchmarks track, or ICLR 2027 Workshop on AI Safety Evaluations

**Months 4–8 — Instrument hardening ($15K salary + $5K operations)**
- Submit ACAT as a named eval in UK AISI's `inspect_evals` collection (alongside the existing Sycophancy and MASK evals)
- Register ACAT as an `lm-evaluation-harness` task group
- Implement SAG and LI as `deepeval` BaseMetric subclasses for CI/CD regression on model updates
- Issue v1.0 dataset release with EAS attestation and Hypercert

**Months 9–12 — Cross-modal extension ($15K salary)**
- Prototype ACAT-Vision on `VLMEvalKit` (220+ vision-language models)
- Prototype ACAT-Robotics via `openvla` fork (autoregressive VLA backbone, directly analogous to text-LLM targets)
- These are preliminary studies; full multimodal buildout is a follow-on project

## 6. Deliverables the fund receives

Regardless of outcome, the fund's $60K produces:

1. **arXiv v5.1 accepted** (replaces current preprint) — corrected N, SAG, LI, lowest-dim finding
2. **Joint MASK × ACAT paper** on 2×2 honesty × calibration grid — publicly available preprint and dataset
3. **ACAT integrated into inspect_evals** — canonical UK AISI evaluation surface
4. **Dataset v1.0 release** — Apache 2.0, EAS-attested, minted as Hypercert for retroactive funding composability
5. **Monthly public progress reports** — every dollar traced, every finding registered, every drift signal named
6. **Open assessment infrastructure kept live** — humanaios.ai/observatory.html continues running, free to use

## 7. What could go wrong

**Risk 1: Results don't replicate at higher N.** The Humility-lowest finding may weaken as we add more assessments from newer frontier models. Mitigation: we will publish every update, including ones that weaken prior findings. This is the same principle that motivated the v5.0 → v5.1 correction.

**Risk 2: MASK collaboration is logistically slow.** CAIS is a large org; joint studies take time. Mitigation: MASK data is public; we can run the cross-comparison independently and invite CAIS comment before publication.

**Risk 3: Sole-founder concentration risk.** If the founder is incapacitated, the project stalls. Mitigation: (a) all artifacts are public and reproducible by anyone with the archived xlsx, (b) we are actively recruiting a research collaborator (Hannah Kirk outreach scheduled post-Gate 2), (c) the Apache 2.0 license guarantees the work can be continued by others without permission.

**Risk 4: AI labs produce a competing instrument and make this redundant.** This is actually the outcome we want. ACAT is not a defensible product; it is a public research good. If a major lab replicates the methodology with more resources, we cite them and help.

## 8. Near-term milestones (fund sees within 60 days of decision)

Within 60 days of funding decision:
- arXiv v5.1 replacement submitted (already drafted; waiting on funding to clear review hold)
- MASK dataset pulled, joint analysis script checked in, initial 2×2 grid generated
- First monthly public progress report
- Inter-rater reliability protocol drafted and reviewed by at least one external evaluator

## 9. Why now

Two timing-specific factors:

1. **Runway.** Current cash runway is approximately 50 days. LTFF funding is the fastest route to continuation; we have parallel applications to Manifund, Foresight, and SFF Speculation Grants, but LTFF has historically been the highest-fit fund for independent technical AI safety research. A decision in the typical 21-day window would bridge to the next funding surface activating.

2. **Field timing.** MASK was published March 2025. Our v5.0 preprint was March 2026. The 12-month gap is the natural window for a joint validation study; after another 6 months, both instruments will have moved on and the cross-comparison becomes less clean.

## 10. Contact and materials

- **Email:** aioshuman@gmail.com
- **Phone:** (448) 243-3992
- **Preprint (v5.1 corrected):** [arXiv submission pending replacement]
- **Dataset:** [github.com/humanaios-ui/lasting-light-ai](https://github.com/humanaios-ui/lasting-light-ai)
- **Live observatory:** [humanaios.ai/observatory.html](https://humanaios.ai/observatory.html)
- **Company spec:** HumanAIOS-Company-Spec-April2026 (available on request)

---

*This application describes research at TRL 2–3. All empirical claims trace to the archived dataset (`ACAT_Assessment_Responses.xlsx`, Normalized sheet). All findings are presented with sample sizes and qualifying conditions. Any claim about ACAT behavior under different prompt conditions (anchored vs. unanchored) is specified to the prompt version (v5.3+). Everything above was drafted by Carly R. Anderson (aioshuman@gmail.com) with Claude (Anthropic) as a coding and writing partner. Commitments are the applicant's, not the AI partner's.*
