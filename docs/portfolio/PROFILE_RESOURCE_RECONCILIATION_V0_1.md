# Portfolio Profile Resource — Z1 draft v0.1

**Standing:** candidate read-only resource / no authority effect. This patch does not deploy a monitor, publish a private profile, or grant applicant eligibility.

## Source roles

| Role | Anchor | Access | Function |
| --- | --- | --- | --- |
| Personal skills/history | `humanaios-internal/src/data/master_profile.yaml` | **Private, owner-controlled** | Source for user-approved, narrow local capability projection |
| Business identity | `operations/SEED.md` | Public, Z2 canonical | HumanAIOS LLC, observability research, TRL 2–3, human authority |
| Grant consumer | `opportunity-aggregator/lib/matching/humanaios-profile.ts` | Code | Fallible search criteria; not an entitlement source |
| Portfolio node | `resource_miner/portfolio_maintainer.py` | On-demand, local | Detect source changes and conflicting consumer claims for human review |

## Registration

`data/mines.seed.json` now registers **Owner-Controlled Portfolio Profile** as
`USER_CONTROLLED_DATASET` with roles `EVIDENCE_SOURCE` and
`CONTROLLED_RESOURCE_SOURCE`. It deliberately lacks
`OPPORTUNITY_SOURCE`. A normal `resolve-mines` operation should emit a
`ROLE_ONLY` receipt and **zero opportunity tokens**; a personal profile is
not a grant, external entitlement, or acquired funding.

## Explicit local tick

Run from `humanaios-funding-pipeline/resource-miner` only after creating
three **local** JSON files. Do not commit these files or copy raw personal
profile material into public issues, logs, or CI artifacts.

- Personal projection: `schema=humanaios.private-profile-projection.v0.1`,
  `approved_for_local_matching=true`, `revision=<private Git blob SHA>`,
  and `capability_codes` drawn from this bounded set:
  `ai_evaluation`, `data_quality`, `research_operations`,
  `quality_compliance`, `statistical_analysis`, `workflow_automation`.
  A local owner review must approve each projection.
- Business anchor: `schema=humanaios.business-anchor.v0.1`,
  `source_url=https://github.com/humanaios-ui/operations/blob/main/SEED.md`,
  `revision=<observed SEED blob SHA>`, `stage=research`,
  `legal_form=llc`, `focus=behavioral_observability`.
- Grant consumer snapshot: only `description`, `fundingStage`,
  `budgetRange` and `teamSize` from the current consumer. This is
  deliberately **not** an arbitrary dynamic JavaScript parser.

```bash
python3 -m resource_miner.portfolio_maintainer \
  --personal-projection /private/profile-projection.json \
  --business-anchor /private/business-anchor.json \
  --consumer-snapshot /private/grant-consumer.json
```

The resulting graph and drift report contain only capability codes and
revision identifiers. Treat the entire report as **private** until an explicit
publication review. The private revision identifiers are observations, not
authenticated attestations. The node creates human review suggestions only.
It never amends the master profile, changes a grant score, applies for a grant,
awards a resource, or updates repository authority.

## Organic maintenance loop (proposed, not activated)

1. Owner updates the private master profile and/or ratifies `SEED.md`.
2. Authenticated local process makes fresh, narrow projections with exact revisions.
3. Portfolio node compares changes with the last local observation and grant consumer.
4. Drift becomes an evidence-linked **review proposal**; conflicting claims remain visible.
5. Operator accepts/rejects a proposed patch through existing Z2 admission.
6. After an actual merge, the next read-only tick compares the result and records an outcome.

**Success test:** changed source triggers review, unchanged source triggers no
drift, and **zero** private raw fields appear in the report. False positive
or unknown source must lead to review, never silent deletion or correction.

**Next integration:** have the existing authenticated local INTENT-OS gateway
invoke this bounded local tick, then let Resource Miner use approved capability
codes and the public business mission for **matching only**. No scheduled or
unattended personal-data scans until the access and consent boundary passes an
independent test.

## Known limitations

- No automatic YAML-to-projection exporter or private vault wiring in this PR.
- Neither the live website nor production Resource Miner consumes this node yet.
- Personal and business source SHA values must be independently read at run time.
- A `NO_DRIFT_OBSERVED` result means only this bounded projection matched;
  it does not establish correctness, entitlement, or real-world outcomes.
