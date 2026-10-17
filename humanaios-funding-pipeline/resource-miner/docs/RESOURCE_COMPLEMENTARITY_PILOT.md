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

At a hypothetical 120-minute budget, the existing Resource Miner individual
ranking (captured need/requirement matches, using its `_ranking_score`) ranks
Microsoft first in this 3-candidate subset. That top singleton covers one of
the three declared target affordances. The best feasible singleton under the
new coverage objective also covers one. The three-source bundle covers three.
Reported coverage delta is +2 affordance classes **against both** baselines. This is not a
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

## Milestone 2 — executable outcome negative control

Run from `humanaios-funding-pipeline/resource-miner`:

```bash
python3 -m resource_miner.outcome_probe
```

This **executes real local Resource Miner processing** over actual checked-in,
provenance-bearing resource records. The exact same `CREATE_RESOURCE_VERIFICATION_QUEUE`
task is executed twice: once with the previously selected individual resource
(using the existing Resource Miner ordering), and once with the three-resource
combination, under the same hypothetical review budget.

A receipt includes input source ref, time measured in nanoseconds by the
local Python process, output SHA-256 hashes, generated verification questions,
explicit budget assumptions, and missing live-provider prerequisites. It
**does not claim** the Python host is Azure or the resources have actually
worked together.

**Falsification result:** The bundle generates three *unverified source-review*
questions versus one for the baseline. Both generate **zero** independently
verified provider accesses or completed verified outcomes. The bundle's added
capability coverage is not a demonstrated useful-task improvement. Both
outputs remain read-only, unactionable. The extra hypothetical review minutes
are not actual money or recorded labor.

**Live interoperability remains BLOCKED:** Azure compute must be witnessed
independently on a real owned workload; Cerebras requires an authenticated,
permitted, bounded inference call; Langfuse requires a functioning authorized
trace ingestion and independent readback. A host-environment string, a cached
resource candidate, or a passed mock is not proof of any of these. The
preflight only reports missing configuration names; it never prints keys,
makes external calls, or upgrades permissions. Having all settings present
still returns `PREFLIGHT_ONLY_NOT_AUTHORIZED`.

No secret-bearing GitHub Actions PR job was added. Credentialed external work
must pass protected human authorization, cost and data-boundary review and
independent witness checks before a separate live workflow is enabled. Never
send private HumanAIOS source material or client data to model providers
without documented data authorization.

**What would prove real synergy:** Run the *same pinned and independently
scored public/synthetic task* on authorized Azure compute with a control arm
(Azure-only deterministic processing) and an experimental arm
(Azure + Cerebras inference + Langfuse trace with independent receipt).
Collect outcome quality (claim precision and completeness), wall-clock time,
actual API tokens/charge, workload cost, and verified telemetry readback.
A larger input list or mere trace count does not count as a better outcome.
If cost rises without improved useful output, the result is negative.
