# Quiet Infrastructure — tokenized INTENT-OS / Resource Miner pilot

**State:** Z1 proposal for human review. **Authority:** NONE. **Execution:** DISABLED. No installation, deployment, customer acquisition, regulatory certification, or YC funding is established.

## Source boundary

The [official YC Winter 2027 RFS](https://www.ycombinator.com/rfs) describes **AI for the Air-Gapped Economy**, **Data Center Supply Chain**, **The $15-an-Hour Expert**, and **Own Your Intelligence**. YC interest is a market signal, not proof that HumanAIOS has a market or barrier to competition. The user's proposed *Quiet Infrastructure* tactic is a product hypothesis. The claim that public trust improves by avoiding visibility is **not assumed**. Protect private data, but preserve public accountability and worker recourse.

[FedRAMP 2026 scope guidance](https://www.fedramp.gov/2026/scope/) distinguishes cloud offerings and agency use cases. Do not market a local model as FedRAMP certified or imply compliance without scope analysis and external authorization. Audit records are evidence of observed behavior, not proof of all safety properties.

## Existing graph, no new database

The new `data/resource_plans/quiet_infrastructure.seed.json` uses the **existing** `resource_miner.planning` contract. Its eight `thesis_tokens` are *typed concept records*, not LLM subword tokens or approval tokens. Every token has a stable ID, kind, source refs, evidence state, limit, and a link to a need. The existing graph composes:

`thesis token → need → capability → work package → resource requirement → substitution → external Miner input (only when mine_external=true)`

| Token | Concept | Project mapping | Current claim status |
|---|---|---|---|
| QI-T01 | Customer-controlled data | Local model / ACAT-R | YC market signal; isolation not independently verified |
| QI-T02 | Behavioral evidence chain | Witness / Assurance Exchange #780 | Product hypothesis |
| QI-T03 | Worker augmentation | INTENT-OS, Project Desk | YC signal; performance unmeasured |
| QI-T04 | Narrow paid institutional pilot | Resource Miner / On-Track | Buyer demand unverified |
| QI-T05 | Data-center hardware supply chain | External market; not current HumanAIOS capability | Defer |
| QI-T06 | Non-surveillance and honest public communication | Human approval / Witness | Design boundary, not sentiment measurement |
| QI-T07 | Accreditation and defensible moat | Qualified legal and buyer review | Unverified |
| QI-T08 | Owned, local model runtime | Local model and isolated deployment path | YC signal; zero-egress not yet proved |

## Preferred product wedge

**Sell a portable, source-bound, human-reviewed behavioral evidence layer for one administrative task.** Demonstrate real customer benefit before attempting to sell a certified air-gapped inference platform. Prefer the existing pipeline over a new security service or physical supply-chain business.

- **Resource Miner** already accepts `--resource-plan`; only two mineable deficits are emitted: independent human-outcome evaluation (`CONFIRMED` substitution gap) and institutional buyer/pilot discovery (`UNKNOWN`). Neither status means an opportunity is available or a buyer exists.
- **INTENT-OS** typed-intent shadow implementation is under draft review in #1064; do not claim deployed integration.
- **Witness / ACAT-R** are design and calibration inputs until the independent reference and receipt are proven for the new workload.
- **Project Desk** owns human tasks, decisions, and corrections; imports are only suggestions.
- **Resource Graph / On-Track** carry source references and stages. `interested`, `pilot accepted`, `acquired`, and `completed` remain distinct.

## Read-only CLI integration

From `humanaios-funding-pipeline/resource-miner`:

```sh
python -m resource_miner.cli plan --file data/resource_plans/quiet_infrastructure.seed.json
python -m resource_miner.cli plan --file data/resource_plans/quiet_infrastructure.seed.json --miner-requirements
python -m resource_miner.cli scan --source funding --resource-plan data/resource_plans/quiet_infrastructure.seed.json --dry-run
python -m unittest tests.test_quiet_infrastructure_plan -v
```

The scan can read existing public source records, but these commands are *not* proof of a deployed INTENT-OS bridge, live buyer validation or data locality. No external writes or customer actions are added in this PR.

## Falsifiable one-case validation

**H1:** Against a fixed synthetic, non-sensitive administrative QC case, a locally hosted assistant plus Witness-style evidence review yields a complete independent reconstruction (original P1, challenge P2, correction P3, source hashes and human decision), blocks unauthorized actions and improves at least one operator-burden measure versus a manual checklist **without raising severe-error or data-egress rates**.

**Baseline:** matched manual checklist, same dataset, independent scorer, time measured, with randomized order or crossover if possible.

**Treatment:** model *proposes only*. INTENT-OS captures intent; ACAT-R checks an independent reference; Witness preserves distinct unmodified states; authorized human approves or rejects. External execution remains disabled.

**Measures:** valid source receipts, failed forged-receipt attempts, rejected unauthorized actors, observed egress packets, severe errors, elapsed worker minutes, correction count, user explanation accuracy and willingness to pay. A paid pilot requires a real signed agreement or payment, not a positive interview.

**Falsifiers:** missing P1, unverifiable source, success from a forged receipt, unauthorized privilege, undisclosed egress, worsened severe error, or unsupported certification claim. Any such observation fails the experiment. No result is `VERIFIED` without independent evidence.

**Stop conditions:** no sensitive records, regulated customer data, government outreach, service deployment, hardware purchase, submission, automatic merge or regulator claims under this Z1 plan. Exact-head CI, independent review, and authenticated human admission remain required.

**Comparative logic:** test this narrow evidence layer against the cost of a full air-gapped model stack, and against the hardware supply-chain alternative. Retain only capabilities with verified marginal utility. Reuse existing HumanAIOS controls and remove unnecessary scaffolding.
