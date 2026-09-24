# HumanAIOS Resource Miner v0.1

Resource Miner is the **broad-discovery layer upstream of Entitlement Navigator**.

It asks:

> What externally available resources could reduce a currently modeled need, and what should be verified next?

A resource may be a contest, hackathon, grant, bounty, rebate, credit, fellowship, procurement call, training program, research-access offer, dataset, or other externally available capability.

## Boundary

```text
Internet / public sources
  -> Resource Miner
  -> normalized ResourceCandidate + provenance
  -> Need Graph mapping
  -> VERIFY_NOW | WATCH | ARCHIVE
  -> Entitlement Navigator / resolver
  -> applicant-specific eligibility evidence
  -> application / claim / work item
  -> outcome receipt
```

The Miner does **not** emit `YOU QUALIFY`, `APPLY_NOW`, or a funding commitment. Every candidate starts with `eligibility_assessed=false` unless a downstream resolver establishes the applicant predicates.

## MVP discovery adapters

- **Existing HumanAIOS funding pipeline** — imports canonical `../data/sources.json`.
- **DEV Community public Articles API** — scans challenge announcements through `#devchallenge`; public article listing requires no API key.
- **GitHub issue search** — supports open bounty/prize queries; optional `GITHUB_TOKEN` only increases rate limits.
- **Generic RSS/Atom** — accepts feed URLs for additional contest, rebate, research, program, and opportunity sources.

The adapter boundary is intentionally small so Devpost, HackerEarth, utility rebates, startup/cloud credits, tribal programs, procurement portals, and open-source bounty networks can be added without changing the resource schema.

## Need Graph

`data/needs.seed.json` is a **candidate needs model**, not a canonical strategic record. v0.1 seeds:

- independent validation and benchmarking;
- compute and infrastructure;
- revenue and non-dilutive capital;
- visibility and dissemination;
- contracts and procurement;
- research collaboration and access;
- training and credentials.

Each mapping stores both its score and the exact type/text signals that caused it.

## Routing

The Miner uses only three routing states:

- `VERIFY_NOW` — strongly maps to an active need; authoritative currentness and applicant eligibility should be resolved next.
- `WATCH` — plausible but weaker/unmapped/upcoming; retain without creating work prematurely.
- `ARCHIVE` — deadline is demonstrably past or the resource is stale.

This keeps pursue/do-not-pursue decisions downstream where effort, rights, applicant identity, constraints, and human authority can be evaluated.

## First live specimen: DEV + Kaggle Benchmarking Challenge

`data/resources.seed.jsonl` contains a public regression specimen verified from DEV's announcement and contest rules on 2026-09-24:

- challenge opened 2026-09-23;
- entry deadline 2026-10-11;
- five winners;
- $500 cash per winner / $2,500 total prize pool;
- Kaggle benchmark + public DEV submission required.

The seed is not applicant eligibility. It tests whether Resource Miner can represent a time-bounded external resource and map it to validation, research, revenue, and dissemination needs.

## Run

From `humanaios-funding-pipeline/resource-miner/`:

```bash
python3 -m unittest discover -s tests -v

# Existing curated funding + DEV challenge discovery
python3 -m resource_miner.cli scan --dry-run

# Existing canonical funding dataset only
python3 -m resource_miner.cli scan --source funding --dry-run

# DEV challenges
python3 -m resource_miner.cli scan --source devto --dev-tag devchallenge --dry-run

# GitHub bounties/prizes
python3 -m resource_miner.cli scan --source github --github-query 'is:issue is:open label:bounty' --dry-run

# Arbitrary RSS/Atom feeds
python3 -m resource_miner.cli scan --source rss --rss 'https://example.org/opportunities.xml' --dry-run
```

Without `--dry-run`, output defaults to `data/resources.jsonl`, which is git-ignored because live scans are observations, not curated source code.

## ResourceCandidate contract

Each candidate carries:

- stable resource ID and canonical URL;
- discovery source/method/timestamp;
- title, sponsor, description, tags;
- resource type(s);
- provisional deadline only when explicitly extractable near closing/deadline language;
- cash mentions without treating them as guaranteed individual value;
- source evidence;
- need matches and causal signals;
- route;
- `eligibility_assessed=false` / `eligibility_status=UNASSESSED` by default.

## Entitlement Navigator handoff

The normalized resource record is the handoff. Entitlement Navigator (or a resolver between the two) should:

1. verify the primary/current source;
2. identify legally permitted applicant types;
3. test geography, age, entity, project, timing, rights/IP, prior-work, and other predicates;
4. preserve failed predicates and contradictory evidence;
5. only then convert the candidate into an actionable application/work item.

## Next increments

1. Add source-specific resolvers for DEV challenges, Devpost/HackerEarth, utility rebates, startup/cloud credits, procurement, and bounty networks.
2. Add source snapshots/hashes and stale-source detection.
3. Add append-only discovery receipts rather than overwriting scan output.
4. Feed repository constraints/open needs into the Need Graph automatically.
5. Add outcome calibration: predicted relevance/effort/value -> actual result -> improved future routing.
