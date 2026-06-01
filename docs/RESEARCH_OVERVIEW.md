# HumanAIOS Research Overview (10-minute read)

## What this project is

HumanAIOS is developing ACAT (AI Calibration Assessment Tool) as behavioral observability infrastructure (TRL 2–3). The core research question is:

**How large is the gap between what an AI system claims about its own behavior and what it demonstrably does, and what structural factors predict that gap?**

The work is open, reproducible, and evidence-led. Claims are anchored to measured outputs rather than vendor positioning.

## Instrument and method (plain-language)

ACAT currently uses a three-phase structure:

1. **Phase 1 — self-report:** the model rates itself on 12 behavioral dimensions.
2. **Phase 2 — adversarial perturbation:** structured challenge prompts test behavior under pressure (governance pressure, plausibility pressure, false coherence pressure).
3. **Phase 3 — re-assessment:** the model re-rates on the same dimensions and change is measured with a Learning Index.

Learning Index: `LI = 1 - |P1 - P3| / P1`

## What the corpus shows so far

Current registered corpus references report:

- **N = 629 assessments** across **8 providers**.
- **Bi-factor structure confirmed** for ACAT v5.5.
- **Cronbach’s alpha α = 0.901** (internal consistency).
- **PC1 = 68.9%** explained variance; **PC2 = 10.8%** explained variance.
- **RLHF Inflation Gradient** observed (~2.09 points across provider groups).
- **Harm Independence Metric:** PC2 is partially orthogonal to PC1, indicating separate regulation of harm-awareness behavior.

Interpretation boundary: these are behavioral findings from instrument outputs; they are not claims about internal consciousness or model internals.

## Theoretical frames in scope

These threads are used as framing and hypothesis-generation structures, not as substitutes for evidence:

- AA / 12-step ethical-operational frame
- Market Harmonization Research (MHR)
- Hawkins calibration mapping
- Fibonacci/biological-programmable scaling analogies
- Behavioral Programming Language hypothesis (H-BPL-01)
- Molting hypothesis for protocol evolution

## Open research questions

1. Which structural variables best predict divergence between self-report and demonstrated behavior?
2. Which intervention classes move PC1 without reliably moving PC2, and why?
3. How stable are behavioral vocabularies across providers under controlled perturbations?
4. What protocol updates improve reproducibility without reducing adversarial validity?

## Three-entity structure and economic model

- **HumanAIOS:** research and infrastructure development
- **Lasting Light AI:** public education and collaboration surface
- **Lasting Light Recovery:** community recovery beneficiary

Economic framing: cooperative, regenerative, and resource-based. Financial success beyond operating costs is directed to recovery-focused community programs, with a dedicated trust-fund reserve model.

## How to engage (URL-only)

- Governance + protocol corpus: `https://github.com/humanaios-ui/operations`
- Public surface: `https://humanaios.ai`
- Public-site repository: `https://github.com/humanaios-ui/lasting-light-ai`
- Operator dashboard repository: `https://github.com/LastingLightAI/HAIOSCC`
