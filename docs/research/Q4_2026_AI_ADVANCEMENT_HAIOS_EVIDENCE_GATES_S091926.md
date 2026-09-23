# Q4 2026 AI Advancement × HAIOS Evidence Gates

**Related issue:** #413  
**Status:** Z1 research forecast / proposed validation path; unratified  
**Research cutoff:** 2026-09-19  
**Forecast window:** 2026-10-01 through 2026-12-31  
**Authority boundary:** This document records analysis and testable hypotheses. It does not authorize a build, governance amendment, registration, deployment, or autonomous agent action.

## Research question

How might Q4 advances in agent capability, delegation, monitoring, and external evaluation change the significance of HumanAIOS's claim-versus-demonstration research?

**Inference:** Agent capability and commercial monitoring are likely to advance faster than independently verifiable evidence about what agents actually did. HAIOS's potential contribution is a portable evidence test: preserve the original claim and authority, observe bounded behavior, reconcile missing channels, and leave the judgment with a human.

## Evidence boundary as of September 19

The [canonical SEED](../../SEED.md) describes ACAT as research at TRL 2–3. The Learning Index is a Phase 3 / Phase 1 self-report ratio under its defined protocol; behavioral predictive validity is a separate empirical question. The September 18 *HumanAIOS-Open-Arena-Development-Brief* and *HumanAIOS-Decision-Review-Pilot* are proposals. The training-provenance and companion agent-observability packages pass planted synthetic tests and retain **NO_GATE** for real-world completeness and containment. Their toy tools have no real side effects. Treat drafts, synthetic demonstrations, live observations, and replicated findings as different evidence classes.

## Explicit mapping

| External development | HAIOS mapping | Potential significance if validated | Required evidence |
| --- | --- | --- | --- |
| Anthropic reports Claude “leads” 26% of its AI R&D under human supervision. Its approximately 30,000 concurrently active agents and 100% action-monitoring figures concern its most-used internal platform, not all agent activity. [Source](https://www.anthropic.com/institute/measuring-pace-of-ai-development) | ACAT tests claims against perturbations; Decision Review compares a stated goal and evidence with a resulting recommendation. | A reproducible claim-versus-demonstration measure might remain useful as models change. | Held-out behavior, matched model/prompt versions, independent labels, uncertainty intervals, and replication; LI alone cannot establish this. |
| Identity, delegated authority, and asynchronous work are priorities in the [MCP roadmap](https://modelcontextprotocol.io/development/roadmap); [Microsoft Agent 365](https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/) already offers inventory and controls. | Goal Keeper, goal and permission versioning, Zone 2 human decisions, Zone 3 execution, and action receipts. | A reviewer could determine which goal and authority applied when an agent acted. | Capture identity, authorized changes, revocations, and actual actions at the relevant execution boundary; a model transcript alone is insufficient. |
| Evaluation boundaries failed in the [OpenAI/Hugging Face incident](https://openai.com/index/hugging-face-model-evaluation-security-incident/) and [three incidents identified in Anthropic's review of 141,006 relevant runs](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals/). That denominator is specific to the review, not a general incident rate. | Witness action records, Jester planted faults, Witch common-observer failures, and explicit NO_GATE on missing channels. | Replace an unsupported “no violation observed” conclusion with a scoped account of what was and was not visible. | Independently controlled capture; OS/network reconciliation; planted bypasses; detection recall, detection time, and false alerts on clean tasks. |
| [Embedded external evaluation](https://www.anthropic.com/news/accenture-embedded-evaluation) is emerging, but access, reporting, and funding standards are unsettled. | Separately operated Open Arena runners, fixed fixtures, blinded review. | Make disagreements and missing evidence inspectable in a repeatable small study. | Raw records, frozen criteria, independent operation and adjudication; two accounts or model names do not prove independent genesis. |
| [EU transparency enforcement began in August](https://digital-strategy.ec.europa.eu/en/news/commission-starts-enforcing-ai-act-rules-and-new-transparency-requirements-2-august/); the [GPAI training-content template](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models) is a minimal public summary. | Source Echo tests copied origin versus corroboration; the provenance witness binds recorded inputs to a checkpoint. | Clarify the exact limits of a lineage claim. | A trusted input-time witness. Synthetic identical-text/different-source tests show why complete source identities cannot be inferred from weights or responses alone. No compliance claim follows. |

## Q4 forecast ledger

Probabilities are **analyst judgments**, not measured frequencies or organizational promises. Resolve each against new, public evidence dated after 2026-09-19. Score on 2027-01-01; record ambiguous outcomes separately.

| ID | Event by 2026-12-31 | P | Resolution rule and HAIOS implication |
| --- | --- | ---: | --- |
| F1 | OpenAI makes Astra available in some limited form and publishes its system card. | 70% | A release plus card count; another preparation update does not. OpenAI says availability is planned “soon,” with restricted advanced cyber access. Compare capability, allowed scope, and monitoring claims. [Source](https://openai.com/index/path-to-astra/) |
| F2 | MCP publishes a new or revised formal proposal or working-group deliverable on agent identity/delegation or asynchronous tasks/events. | 75% | Require a dated artifact after September 19; the current roadmap alone does not count. Do not infer ratification or universal adoption. HAIOS should version its actor, permission, and event schema. [Source](https://modelcontextprotocol.io/development/roadmap) |
| F3 | Anthropic names another embedded evaluator and describes at least its intended access or test scope. | 75% | A named organization plus scope count; a generic partnership announcement does not. Reporting standards and independence remain questions to test. [Source](https://www.anthropic.com/news/accenture-embedded-evaluation) |
| F4 | A frontier lab and an outside evaluator publish a **new independent verification** of agent-monitoring effectiveness with an action denominator and capture scope. | 30% | A named evaluator or self-reported coverage alone does not count. This is the test of whether outside oversight becomes measurable in practice. [Source](https://www.anthropic.com/institute/measuring-pace-of-ai-development) |
| F5 | At least one substantive follow-up on the 2026 evaluation containment incidents publishes findings about boundaries, egress, or monitoring. | 60% | A concrete postmortem or external review counts; a general reassurance does not. Use the described failure classes to challenge synthetic fixtures. [Anthropic](https://www.anthropic.com/news/improving-alignment-security-efforts), [OpenAI](https://openai.com/index/hugging-face-model-evaluation-security-incident/) |
| F6 | No deployed frontier model publishes an independently verified, complete document-by-document training-input inventory. | 95% | One such inventory with a credible completeness audit falsifies the forecast. A public summary or output inspection does not count. [Source](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models) |

## Conditional HAIOS research checkpoints

These dates describe a proposed way to resolve the HAIOS hypotheses; they are not assertions that the work is authorized, scheduled, or deployed. Preserve the current OR&D and building gates. Zone 1 may draft the research contract; Night retains Zone 2 ratification and Zone 3 execution.

| Checkpoint | Research artifact | Gate |
| --- | --- | --- |
| October | Preregister all 12 Arena fixtures, source and actor IDs, authorized goal versions, planted faults, three comparison conditions (provenance-only, action-only, joined), and blinded adjudication. | Synthetic passes stay labeled synthetic. Unknown lineage, missing action records, or unauthorized goal amendments remain NO_GATE. |
| November, only if authorized | One bounded real-agent run with an observer outside agent control; reconcile tool, OS, and network evidence; plant an unobserved path. | Report capture by action class, missed events, detection latency, false alerts per clean task, and checkpoint-input binding. An unresolved path blocks completeness claims. |
| December, only if authorized | Blind review of the Arena record. If a low-stakes Decision Review pilot proceeds, measure corrected decision-critical omissions, independent verification, added effort, and repeat use. | The September briefs' **provisional five-operator pilot signals** are at least two separately verified corrections, median added effort at most 15 minutes, and at least three of five returning. A five-person pilot cannot establish population reliability. |

**Project-level prediction:** The most informative Q4 result is likely to be an exact evidence boundary: either a successfully reconciled bounded trace or a documented NO_GATE when an action path escapes observation. Any stronger ACAT behavioral-prediction or general agent-oversight claim requires preregistered external validation and replication.

**Related scope:** `humanaios-ui/operations#361` is a read-only multi-agent boundary audit; `humanaios-ui/operations#363` specifies a separate paired governance-versus-platform experiment. This forecast neither changes nor supersedes either pilot.
