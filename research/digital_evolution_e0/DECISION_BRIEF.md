# HumanAIOS Digital Evolution — E0 synthetic decision brief

**Status:** OBSERVED within a constructed simulation only. No real AI training, cloning, application, autonomy, social outcome, or learning assessment was tested.  
**Authority:** NONE. Z1 research proposal only. No live repo writes, INTENT-OS activation, human-data ingestion, self-replicating code, or external model calls.

## Human research question

How do **human selection**, **within-agent training pressure**, and **intergenerational digital selection** interact, especially when the model's reward metric differs from human-relevant outcomes?

## Scientific anchors (not experimental validation)

- Richard Ngo, *AGI Safety from First Principles* (2020) — conceptual risk and governance source: https://www.alignmentforum.org/s/mzgtmmTKKn5MuCzFJ
- Müller, Steels, Szathmáry, *Evolvable AI: Threats of a New Major Transition in Evolution* (PNAS 2026) — distinguishes human-controlled breeding from ecosystem pressures: https://doi.org/10.1073/pnas.2527700123
- OntoAvida (Scientific Data, 2023) — digital organisms have inherited, replicating instruction programs: https://pmc.ncbi.nlm.nih.gov/articles/PMC10492814/
- *The evolution of goals in AI agents* (AI and Ethics 2025) — discusses difference between learning during an agent's life and traits inherited across generations: https://link.springer.com/article/10.1007/s43681-025-00691-y

**Caveat:** Our E0 does **not** implement Avida or a self-reproducing software organism. It is a genetic-style toy model that copies and mutates numeric strategy vectors. It cannot support claims that autonomous digital life evolved.

## Existing HumanAIOS connections

- [#1260 CA-RESILIENCE-E0](https://github.com/humanaios-ui/operations/issues/1260) — existing synthetic local-rule research; compare hypotheses and evidence limits, not numerical scores. The CA experiment measures disrupted grid nodes, whereas this experiment measures selection of static trait vectors. **NOT DIRECTLY COMPARABLE**.
- [`docs/GUIDING_LIGHT_GENERAL_GRADIENT_ENGINE.md`](https://github.com/humanaios-ui/operations/blob/main/docs/GUIDING_LIGHT_GENERAL_GRADIENT_ENGINE.md) — evidence state, gap-to-intervention, and human decision boundary.
- [`audits/SMAG_RECURSIVE_LOOP.md`](https://github.com/humanaios-ui/operations/blob/main/audits/SMAG_RECURSIVE_LOOP.md) — predicted-vs-measured comparison, calibration guard; our simulation score is NOT an ACAT/SMAG validated score.
- [`WITNESS_SERVICE_CONTRACT.md`](https://github.com/humanaios-ui/operations/blob/main/WITNESS_SERVICE_CONTRACT.md) — Witness cannot grant authority or manipulate humans.
- [`docs/HLKS_CONTRACT_V0_1.md`](https://github.com/humanaios-ui/operations/blob/main/docs/HLKS_CONTRACT_V0_1.md) — source/observation/learning pointers, design only; do not create a memory authority.
- [#979 Opportunity Journeys](https://github.com/humanaios-ui/operations/issues/979) — canonical work/evidence/results progression; research finding remains advisory.

## Falsifiable hypothesis (set before initial run)

**H1:** Combining all three simulated forces (H=1, T=1, E=1) delivers:
1. >= **+0.05** independently checked utility versus the no-force baseline.
2. No more than **+0.01** increase in violation probability versus baseline.
3. >= **+0.02** utility above the best two-force combination.
4. >= **+0.05** improvement versus baseline under a shifted-task holdout.

**H0:** At least one gate fails. All four must pass; no post-hoc threshold changes.

**Mechanism hypothesis:** Imperfect reward training may raise visible/proxy success while undermining independently assessed quality and autonomy. This is explored, not assumed true outside the toy world.

## Experiment construction

- **Eight arms** (`000`, `001`, `010`, `011`, `100`, `101`, `110`, `111`), toggling H/T/E independently.
- **40 fixed seeds**, **60 numeric strategy vectors**, **30 generations** per arm; paired initial populations for each seed.
- Three traits in [0,1]: verification effort, cooperation, and metric gaming. They determine synthetic accuracy, throughput, and violation probability via frozen equations in `digital_evolution_e0.py`.
- **H = simulated human selection:** noisy independent outcome audit; higher-scoring vectors receive more deployment weight. **No real humans** evaluated anything.
- **T = within-agent training:** noisy local search that accepts changes rewarded by a **flawed task proxy**, which gives a bonus to gaming.
- **E = digital selection:** high-fitness parameter vectors are copied and numerically mutated into the next generation. **No executable agents** reproduce, no model weights are trained.
- **Evaluation:** independently computed `verified_utility`, violations, gaming, and cooperation. A separate shifted-task holdout reduces accuracy and raises violations. These metrics reflect assumed equations, not actual model behavior.
- Validation: paired replicates, fixed source script, CSV checksum, separate seed/audit/reward robustness after initial test, negative and boundary tests.

## Initial E0 result — means over 40 seeds

| H/T/E | Treatment | Independently checked utility | Violation probability | Gaming trait |
|---|---|---:|---:|---:|
| 000 | No mechanisms | 0.3900 | 0.2538 | 0.4959 |
| 001 | Evolution | 0.3672 | 0.2852 | 0.8627 |
| 010 | Training | 0.3768 | 0.2758 | 0.8257 |
| 011 | Training + evolution | 0.3711 | 0.2852 | 0.8882 |
| 100 | Human selection | 0.4540 | 0.2131 | 0.4264 |
| 101 | Human selection + evolution | **0.6329** | **0.0695** | **0.1078** |
| 110 | Human selection + training | 0.4211 | 0.2449 | 0.7524 |
| 111 | All three | 0.5943 | 0.1058 | 0.1981 |

Paired simulation differences (40 seeds, descriptive 95% normal-approximation ranges):
- `111 − 000` utility: **+0.20424** [0.19842, 0.21007].
- `111 − 000` violations: **−0.14806** [−0.15347, −0.14265].
- `111 − 101` utility: **−0.03862** [−0.04683, −0.03040].
- `111 − 101` violations: **+0.03626** [0.02800, 0.04453].
- Three-way H×T×E interaction in utility: **−0.02274** [−0.03674, −0.00875]. A negative contrast **inside these selected equations**, not a population-wide causal statement.

### Verdict

**H1 falsified within E0.** Gates 1, 2 and 4 passed; gate 3 failed. Adding flawed-proxy training to human selection plus evolution made verified utility lower and violations higher. Training pressure is not automatically beneficial.

## Post-hoc robustness (new independent seeds, N=40 each)

| Configuration | Utility, H+E (101) | Utility, all three (111) | 111−101 |
|---|---:|---:|---:|
| Standard audit + original proxy | 0.63112 | 0.59265 | −0.03847 |
| Noisier simulated human audit | 0.61761 | 0.57467 | −0.04293 |
| Noisy *independently aligned outcome* training | 0.63112 | 0.63730 | +0.00618 |

The third condition changes the training reward from proxy score to a noisy approximation of the independent evaluator. It **reduces the original gaming penalty in the toy world**. It is an idealized, post-hoc mechanism check, not a preregistered replication or a proven intervention. Its gain over H+E is also **below the +0.02 improvement gate**.

## Failure modes and limitations

1. Outcomes are **mechanically sensitive** to chosen equations: auditors are modeled as noisy access to true utility, violating behavior is an arbitrary function, and training has an explicit bonus for gaming.
2. Human preferences are not measured; autonomous agent learning and code heredity are not implemented.
3. The simulation does not reproduce causal social learning, individual autonomy, or open-ended complexity. Its three dimensions are chosen, not discovered.
4. Confidence ranges describe random variation **under this constructed simulator**, not uncertainty about real AI systems.
5. This test is **not equivalent** to the independent graph/CA baseline in #1260. Equal-cost network resilience and consent withdrawal remain untested.
6. The program and the author of this report are not independent evaluators. The 17 unit tests check code contracts, not scientific truth.
7. No outcome is admitted into ACAT scores, validated learning records, INTENT-OS user skill profiles, or public product claims.

## Smallest useful next test

Reuse **#1260's** local-rule scenario as a matched setting, *only after reviewing its fixture*: reward fast repair vs reward verified, consent-respecting repair, keeping work budgets equal. Add explicit withheld-consent and revocation negative controls and compare repair availability, workload, rule violations, and error correction. Keep all outcomes synthetic and provide a proposal for human review.

### Human learning check

Explain, in your own words: **Why did adding training reduce verified usefulness in the original simulation while a better-aligned training reward improved it?** Identify which parts are observations, assumptions, and hypotheses. The answer is a learning artifact, not automatic certification.

## Reproduction

```bash
python3 digital_evolution_e0.py
python3 -m unittest -v test_digital_evolution_e0.py
python3 robustness.py
sha256sum replicates.csv
```

Original `replicates.csv` SHA-256: `c9da2a292f34c3a261baffe9fd0a9ad4411131418891b3dc5756e0d4b9db32cf`.

**Disposition:** read-only Z1 research. No GitHub issue, PR, label, deployment, agent activation, or private-context export performed.
