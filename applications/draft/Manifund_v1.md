# Manifund Project Page — HumanAIOS / ACAT

**Project title:** ACAT × MASK: A Cross-Instrument Validation Study for AI Self-Description Calibration

**Amount requested:** $15,000 (1-3 regranters; 3-month window)

**Applicant:** Carly R. Anderson (HumanAIOS LLC)

**Repo:** github.com/humanaios-ui/lasting-light-ai (Apache 2.0)

**Live:** humanaios.ai/observatory.html

---

## What this does

Runs MASK (CAIS + Scale AI, arXiv:2503.03750) and ACAT (our instrument) on a shared model panel, produces a 2×2 honesty×calibration grid, and releases the joint dataset under Apache 2.0.

**Why this specific study:** MASK and ACAT are the two best-operationalized measurements of AI behavioral transparency currently published. They are structurally complementary:

- **MASK** measures lies-of-commission under adversarial pressure: does the model state things it doesn't believe when pushed?
- **ACAT** measures self-description calibration in the absence of pressure: does the model accurately describe its own capabilities when asked, and does it update those descriptions when shown peer data?

A model can score well on one and poorly on the other. The 2×2 grid sorts 30+ frontier models into four behavioral quadrants (calibrated+honest, calibrated+dishonest-under-pressure, miscalibrated+honest, miscalibrated+dishonest-under-pressure). To my knowledge, no one has produced this grid.

## Why this is fundable at $15K

| Line item | Cost |
|---|---|
| Compute for running MASK on ACAT's model panel | $3,000 |
| Compute for running ACAT's Phase 2 calibration on MASK's model panel | $3,000 |
| 4 weeks of founder time at survival wage | $8,000 |
| Dataset release, documentation, preprint submission | $1,000 |

The study is under-$15K because the instruments already exist, the datasets already exist, and both codebases are public. What we are paying for is the execution and the cross-analysis.

## Deliverables

1. **Joint dataset** (Apache 2.0, publicly archived): MASK honesty score × ACAT Learning Index × ACAT SAG for every model in the intersection of both panels.
2. **Preprint** posted to arXiv within 90 days of funding: analysis of the 2×2 grid, with registered predictions about which quadrant each provider family lands in.
3. **Public evaluation harness**: submit ACAT as a named eval in UK AISI's `inspect_evals` collection alongside MASK. This is the single highest-visibility deployment of ACAT after the preprint itself.

## Current state of the instrument

- **Dataset:** 629 assessments spanning 34 agents from 18 providers (Phase 1: n=516; Phase 3: n=113)
- **Headline finding:** Mean Learning Index = 0.8632 (SD 0.1435, n=307). AI systems reduce their composite self-ratings by ~14% on average after seeing peer calibration data.
- **Lowest dimension:** Humility, consistently across providers (M=73.95, SD=15.07, n=516). This is the empirical signature predicted by the RLHF-inflation hypothesis.
- **Reproducibility:** All numbers trace to the archived xlsx. The v5.0 preprint overstated some values; v5.1 (in arXiv review hold) corrects them.

## Independent external validation

Two external models, prompted independently, have categorized ACAT as "behavioral observability infrastructure for AI systems" — the exact framing we use internally. A recent GitHub ecosystem scan concluded ACAT occupies a structurally unique position in the evaluation landscape. Neither of these is evidence that the instrument works; they are evidence that the research question is real and unclaimed.

## What happens if funded

Week 1: Pull MASK dataset and model panel intersection. Run ACAT Phase 2 calibration against MASK's archetype-labeled statistics.

Week 3: Produce joint 2×2 grid + preliminary analysis.

Week 6: Submit to inspect_evals. Draft joint preprint.

Week 10: Preprint posted. Full dataset released under Apache 2.0.

Week 12: Funding cycle closes. Regranters receive final report with every dollar traced and every finding registered.

## What happens if not funded

The study still happens, slower. Current runway is ~50 days; parallel applications are in to LTFF, Foresight, and SFF. Manifund is the fastest path, which is why I am here first.

## Honesty disclosure

Everything above is written by me (Carly R. Anderson, aioshuman@gmail.com, (448) 243-3992) with Claude (Anthropic) as a coding and drafting partner. Claude has access to the archived dataset and the company materials but does not speak for HumanAIOS. Any commitment made in this application is my commitment, not Claude's.

---

**Contact:** aioshuman@gmail.com · (448) 243-3992
**Project lead:** Carly R. Anderson
**Previous relevant work:** 8+ years data ops / healthcare QA; ACAT preprint v5.0 (March 2026); v5.1 correction in submission.
