# Bounded resource complementarity pilot (issue #826)

**Standing:** Z1 / OBSERVATION ONLY. No resource is acquired, no external API called,
no application submitted, and no admission or authorization established.

## Why

The existing Resource Miner ranks individual `ResourceCandidate` records by
Need and Requirement fit. This pilot asks whether an explicitly selected bundle
can cover more *distinct source-reported capability affordances* than the best
feasible individual resource under the **same review-effort budget**.

This does **not** test real-world interoperability, return on investment, cash,
actual value generated, applicant eligibility, access, or whether an opportunity
is currently open. These remain unknown. A coverage increase is a **planning
hypothesis**, not verified operational synergy.

## Reproducible specimen

Source: tracked Resource Miner `data/resources.snapshot.jsonl` on
`humanaios-ui/operations` main commit
`5985a388f5b153b6451fc2ef72285d53a4844d61`. It contains
curated observations dated 2026-10-02, not a live re-check as of October 14.

Three distinct external provider domains observed in that snapshot:

| ID | Name | Source-reported affordance | Scenario-only review cost |
| --- | --- | --- | --- |
| RES-436E920AFDEDD702 | Microsoft for Startups | compute_capacity | 30 min |
| RES-487A19443972682F | Langfuse OSS | infrastructure_capacity | 45 min |
| RES-03FF4746A9EE5A3E | Cerebras Free API | api_capacity | 45 min |

Microsoft is marked `ALREADY_ACQUIRED` in the dated Resource Miner snapshot;
this is **not** confirmation of a present usable credit balance.
The other two are `CANDIDATE` only.
All require appropriate verification before practical use.
The assumed 30/45/45-minute review costs are **scenario inputs**, not observed
real-world labor measurements.

Run from `humanaios-funding-pipeline/resource-miner`:

```bash
python3 -m resource_miner.combinations
python3 -m unittest discover -s tests -v
```

Use `--config <file>` and `--snapshot <file>` to replay an alternative bounded
scenario. The module has no network or write capability.

At a hypothetical 120-minute budget, the best single candidate covers one
of the three declared target affordances; the three-source combination covers
three. Reported coverage delta is +2 affordance classes. This is not a
percentage improvement in usefulness, efficiency or money; objectives were
intentionally chosen to exercise complementarity.

At 80 minutes, only pairs fit (coverage 2); at 50 minutes no pair fits.
The objective function counts unique declared affordances; it cannot
establish whether the inputs can be combined into a working service.

## Safety boundaries

- Distinguish `resource_state=CANDIDATE` from `ALREADY_ACQUIRED`, and both
  from proven availability and practical interoperability.
- Ignore archived/passed/expired entries; require bounded candidate IDs,
  distinct IDs, declared non-negative review cost and source-bound evidence.
- A matching source URL is merely a provenance link, never independent proof.
- Output is always `verified_synergy=NOT_ESTABLISHED`,
  `verified_interoperability=NOT_ESTABLISHED`,
  `authorization_state=NOT_REQUESTED`,
  `actionability_state=NOT_ACTIONABLE`,
  `authority_effect=NONE`, and `execution_capability=NONE`.
- No mutation of Resource Miner routing, URA, Opportunity Claim, INTENT-OS,
  Repository Coordinator, or main resource schemas.
- Protected/required PR CI and independently approved admission remain
  separate questions; the comparator must never promote its own result.

## Follow-up falsification gate

Before claiming an actual resource synergy: verify independent current
provider terms and resource access; check licensing, privacy and technical
compatibility; measure one bounded operational outcome against the *same*
single-resource baseline; repeat under an independently recorded witness.
Until then, the +2 signal is a **hypothesis only**.

Existing `.github/workflows/resource-miner-pr.yml` runs the test by
`python3 -m unittest discover -s tests -v` for changed Resource Miner paths.
Check **exact head SHA**, test logs and admission evidence before merging.
