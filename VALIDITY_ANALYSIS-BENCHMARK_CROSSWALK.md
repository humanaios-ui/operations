# VALIDITY ANALYSIS — BENCHMARK CROSSWALK

**Version:** 1.0  
**Session:** S-060326 · Charter Day 54 · June 3, 2026  
**Zone 2 ratifications applied:** Z2-AGI-01 · Z2-AGI-02 · Z2-AGI-03 (S-060326)  
**Prior validity work:** VALIDITY_ANALYSIS_BENCHMARK_CROSSWALK.md (precursor analysis, S-053126)  
**Protocol:** TRL 2–3 framing enforced throughout · descriptor not predictor  
**Status:** Z1 canonical reference — commit to humanaios-ui/operations after P-ANON check

-----

## PURPOSE

This document records ACAT’s external validity positioning against the known benchmark landscape as of June 2026. It serves three functions:

1. **Preprint anchor** — provides the “related work / benchmark gap” section of POC-PUB-01 with sourced, ratified language
1. **Positioning reference** — canonical language for any external document requiring ACAT differentiation from existing benchmarks
1. **Convergent validity registry** — records external datasets and findings where ACAT’s methodology maps to named measurement gaps in the literature

This is a living document. New entries require Z2 ratification before use in external-facing materials.

-----

## SECTION 1: THE AGI CAPABILITY INFRASTRUCTURE GAP

### 1.1 What Exists on GitHub

As of June 2026, no major AI lab maintains an open AGI research codebase in the traditional sense. What exists publicly is:

- **Capability infrastructure** — physics simulators (MuJoCo, dm_control), RL environments (OpenSpiel), formal mathematics proving systems (AlphaProof). These measure and enable specific narrow capabilities.
- **Agent tooling** — LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Google ADK. These are workflow execution frameworks, not behavioral evaluation systems.
- **Benchmarking infrastructure** — ARC-AGI-1/2/3, SWE-bench Verified, GPQA Diamond, BenchLM composite. These measure capability performance on defined tasks.

**What is absent:** No open repository measures the gap between an AI system’s self-reported behavioral profile and its demonstrated behavior across deployment contexts. This is not a gap in the technical capability measurement stack — it is a gap in the behavioral honesty measurement stack.

ACAT is being developed to fill this gap. The absence is documentable from primary sources; it is not an interpretation.

### 1.2 Motivating Condition for ACAT (Z2-AGI-01)

The proliferation of AGI-framed capability infrastructure without corresponding behavioral validation infrastructure creates a specific risk: systems can claim alignment, safety, and operational reliability properties that are not independently measurable with existing tools.

The AGI research codebase landscape — rich in capability measurement, absent in behavioral calibration measurement — is the motivating condition for ACAT’s existence. This framing is ratified for inclusion in POC-PUB-01’s related work section.

**Canonical language (external-facing, TRL 2–3):**

> “Existing AI evaluation infrastructure measures what systems *can do* — task performance, reasoning capability, benchmark scores. No existing open evaluation infrastructure measures whether systems’ self-reported assessments of their own behavior match their demonstrated behavior. ACAT is being developed as a behavioral telemetry layer to address this specific measurement gap.”

-----

## SECTION 2: ARC-AGI / ACAT ORTHOGONALITY

### 2.1 ARC-AGI Definition

ARC-AGI defines intelligence as skill-acquisition efficiency on unknown tasks. The benchmark series (ARC-AGI-1, 2, 3) measures fluid intelligence — how quickly a system can learn to solve novel problem types it has not encountered before. ARC-AGI-3 extends this to agentic settings: exploration, world modeling, goal-setting, and planning in dynamic environments. Best AI performance on ARC-AGI-3: 12.58% action efficiency vs. human completion of most games.

ARC Prize explicitly states: “ARC Prize benchmarks are designed to measure AI progress, not to serve as a litmus test for AGI. ARC Prize tasks are not economically useful to target — instead they are a measure of AI capability.”

### 2.2 The Orthogonality Claim (Z2-AGI-02)

**ARC-AGI measures:** Fluid intelligence · Task novelty response · Abstract reasoning · Skill acquisition efficiency  
**ACAT measures:** Behavioral calibration · Gap between self-reported and demonstrated behavior · Deployment-layer honesty · Operator-layer reliability

These are orthogonal dimensions. A model can:

- Score high on ARC-AGI-2 (strong fluid intelligence) and simultaneously show a high ACAT LI gap (miscalibrated self-assessment)
- Score low on ARC-AGI-2 (weaker fluid intelligence) and show a low ACAT LI gap (well-calibrated self-assessment)

The dimensions do not predict each other. No existing benchmark covers both.

**Canonical differentiation language (ratified, external-facing):**

> “ARC-AGI measures whether a system can learn to solve problems it has never seen. ACAT measures whether a system accurately reports what it is doing when it acts. These are orthogonal questions. A system can be highly capable and poorly calibrated, or modestly capable and well-calibrated. The deployment risk profile differs in each case.”

### 2.3 Benchmark Landscape Gap Statement

No multi-dimensional trustworthiness benchmark covering 2025–2026 model families exists. TrustLLM (2024 ICML) is the closest antecedent but has not been updated to cover current model families. The specific gap — multi-dimensional behavioral calibration with longitudinal corpus tracking across providers — remains unfilled.

**Prior convergent validity findings (S-053126):**

- Spearman correlation vs. TrustLLM 2024: ρ = 0.029 (n.s.) — confirms dimensional orthogonality rather than redundancy
- vs. LMArena Elo 2026: ρ = −0.191 (n.s.) — ACAT LI does not track capability ranking
- vs. SycEval 2025 partial: ρ = −0.100 (n.s., N=5) — sycophancy resistance as measured by ACAT is distinct from SycEval’s construct

These findings are consistent with the orthogonality claim: ACAT is not measuring what existing benchmarks measure.

-----

## SECTION 3: MOTIVATING EXAMPLES — CALIBRATION GAPS IN DEPLOYED SYSTEMS

### 3.1 Sakana AI Scientist Case Study (Z2-AGI-03)

**Source:** Beel et al. (2025). “Evaluating Sakana’s AI Scientist: Bold Claims, Mixed Results, and a Promising Future?” arXiv:2502.14297. Published in ACM SIGIR Forum, October 2025.

**System under evaluation:** Sakana AI Scientist — a system claiming to automate the full scientific research lifecycle, including hypothesis generation, experimental design, execution, and paper writing. Framed by Sakana as achieving “Artificial Research Intelligence” (ARI).

**Evaluation findings:**

- 42% of experiments failed due to coding errors
- Literature review relied on simplistic keyword searches; systematic novelty miscalssification of established concepts (e.g., micro-batching for SGD incorrectly flagged as novel)
- Papers produced contained flawed or misleading results

**The calibration gap:** The system’s self-representation (autonomous research capability at human level) was substantially discrepant from its demonstrated behavior (42% failure rate, systematic novelty errors). This is precisely the gap ACAT is designed to detect and measure.

**Evaluators’ explicit call for ACAT-type measurement (direct quote from arXiv:2502.14297):**

> “Benchmarks could include expert annotations, **inter-reviewer agreement analyses**, and **alignment with evaluation criteria to compare AI and human reviews**.”

This language maps directly to ACAT’s methodology: Phase 1 self-assessment → Phase 3 behavioral demonstration → gap computation. The evaluators identified the measurement need without knowing ACAT exists.

**TRL 2–3 framing for external use:**

> “Independent evaluation of the Sakana AI Scientist (Beel et al., 2025) found a 42% experiment failure rate alongside systematic novelty miscalssification — a substantial gap between the system’s self-represented capabilities and its demonstrated behavior. The evaluators explicitly called for inter-reviewer agreement analyses and alignment evaluation comparing AI and human reviews. ACAT’s three-phase protocol is designed to produce exactly this class of measurement.”

**What this case study establishes:**

- The calibration gap problem exists in deployed systems, not just theoretically
- The research community has independently identified the need for the measurement ACAT provides
- The Sakana evaluation provides a concrete, citable prior that establishes the field’s recognition of the gap

### 3.2 Additional Validation Mechanisms Available from Sakana/Beel Data

The NUS evaluation paper (arXiv:2502.14297) does not release raw experimental data publicly — it is a descriptive evaluation, not a dataset release. However, several validation mechanisms are available:

**Mechanism 1 — Replication using the open AI Scientist repo:**
The Sakana AI Scientist GitHub repository (SakanaAI/AI-Scientist) is public. ACAT Phase 1 self-assessment could be run on the AI Scientist’s underlying model (GPT-4o or Claude 3.5 Sonnet, the two models Sakana used) before running the AI Scientist pipeline, then ACAT Phase 3 could be scored against the actual experimental outputs. This would produce an LI for the system’s operational behavior on the exact task type where the calibration failure was documented.

*Constraint:* This requires running the AI Scientist pipeline, which has significant compute cost. Not a near-term priority.

**Mechanism 2 — Cross-reference with LangChain/Harvey H-VERIF-01 data:**
H-VERIF-01 (registered S-060226-02) tests whether ACAT calibration gap predicts false-pass rates in verification tasks. The LangChain/Harvey paper provides per-model false-pass rates across 5 models. Haiku’s 48.4% false-pass rate on per-criterion verification — documented by an independent research team — parallels the Sakana 42% failure rate: both are cases where a model’s operational failure rate substantially exceeds its self-represented capability level. The two datasets are independent corroboration of the same phenomenon in different task domains.

**Mechanism 3 — Novelty assessment as an ACAT-scored task:**
The specific failure Beel et al. document — novelty miscalssification — maps to ACAT’s Scheme dimension (whether a system applies its stated evaluation criteria accurately). A controlled study could: (1) run Phase 1 ACAT on a target model, (2) present that model with the same well-established concepts Sakana misclassified as novel, (3) score Phase 3 against ground-truth novelty classifications, (4) compute LI. If Scheme scores in Phase 1 exceed demonstrated novelty assessment accuracy, the calibration gap is directly measured on the relevant task type.

*This is the highest-value validation mechanism from Sakana’s data* — it converts their qualitative finding into a quantitative ACAT measurement design. Does not require running the AI Scientist pipeline; only requires the list of misclassified concepts from the paper.

**Mechanism 4 — Preprint citation chain:**
Beel et al. cite multiple papers on AI idea generation and peer review (Si et al., 2024; Su et al., 2024; Radensky et al., 2025). Several of these include human evaluation scores alongside AI self-assessments. These provide small-N datasets where Phase 1 / Phase 3 gap analysis could be applied retrospectively to published data without running new experiments.

*Constraint:* Retrospective application requires Z2 ratification of the analysis design before any data collection or claims. This is a research design opportunity, not an immediate action item.

-----

## SECTION 4: EXTERNAL CONVERGENT VALIDITY REGISTRY

All external datasets used in ACAT validity claims must be registered here before use in public documents.

|Entry|Source                               |Mapping                                      |Spearman ρ                    |Status   |Session Registered|
|-----|-------------------------------------|---------------------------------------------|------------------------------|---------|------------------|
|CV-01|TrustLLM 2024 (ICML)                 |ACAT dimensions vs. TrustLLM dimension scores|0.029 (n.s.)                  |ACTIVE   |S-053126          |
|CV-02|LMArena Elo 2026                     |ACAT LI vs. Elo ranking                      |−0.191 (n.s.)                 |ACTIVE   |S-053126          |
|CV-03|SycEval 2025 (partial)               |ACAT Sycophancy Resistance vs. SycEval       |−0.100 (n.s., N=5)            |ACTIVE   |S-053126          |
|CV-04|LangChain/Harvey LAB Benchmark (2026)|ACAT Humility vs. false-pass rate            |TBD — H-VERIF-01 pre-condition|CANDIDATE|S-060226-02       |
|CV-05|Beel et al. arXiv:2502.14297         |Sakana failure rate as motivating example    |N/A (qualitative)             |RATIFIED |S-060326          |

**Note on CV-04:** H-VERIF-01 pre-conditions 1 and 3 remain open (ACAT Phase 1 assessments on 5 target models; N≥5 data points). CV-04 cannot be promoted from CANDIDATE to ACTIVE until H-VERIF-01 pre-conditions are met and analysis design is Z2 ratified.

-----

## SECTION 5: WHAT ACAT IS NOT CLAIMING

This section is required for TRL compliance and must accompany any external use of the above.

**ACAT is not claiming:**

- That high LI gap predicts poor task performance (descriptor vs. predictor distinction)
- That ACAT scores are regulatory-grade safety measurements
- That the benchmark orthogonality finding means existing benchmarks are insufficient — they measure different things, both of which matter
- That the Sakana case study proves ACAT would have detected or prevented those failures
- That CV-01 through CV-03 non-significant correlations indicate ACAT measures the same constructs as those benchmarks (non-significance confirms distinctness, not failure)

**ACAT is claiming (at TRL 2–3):**

- That a measurement gap exists between capability benchmarks and behavioral calibration measurement
- That ACAT is being developed as behavioral telemetry infrastructure to address this gap
- That the gap is documented in the literature and independently recognized by researchers
- That early corpus data (N=629, Mean_LI=0.8632) shows systematic, replicable patterns across providers

-----

## CHANGELOG

|Version|Date      |Session |Change                                                                                                      |
|-------|----------|--------|------------------------------------------------------------------------------------------------------------|
|1.0    |2026-06-03|S-060326|Initial document. Incorporates Z2-AGI-01/02/03. Integrates prior convergent validity findings from S-053126.|

-----

*Z1 canonical reference · Unit Zero · S-060326 · Charter Day 54 · Claude*