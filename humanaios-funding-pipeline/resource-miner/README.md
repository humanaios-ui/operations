# HumanAIOS Resource Miner v0.1.1

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

## Adversarial hardening in v0.1.1

Cross-substrate review of the v0.1 branch found three concrete implementation defects. v0.1.1 fixes those defects without changing the Z2-sensitive routing threshold:

- the package initializer is valid Python source;
- URL canonicalization removes known tracking parameters but **preserves and stably sorts semantic query parameters**, so distinct resource identifiers such as `?id=1` and `?id=2` do not collapse;
- RSS/Atom input is capped at 2 MiB and rejects DTD/entity declarations before `xml.etree.ElementTree` parsing.

Regression tests plant tracking-vs-semantic query cases, an oversized feed, and a DTD/entity payload. The `VERIFY_NOW` threshold remains `0.55`; changing that value changes prioritization policy and is outside this hardening patch.

Redirect aliases are still not resolved before hashing. That is a documented identity limitation rather than a silently claimed capability; adding redirect resolution requires a bounded policy for hops, timeouts, and cross-host redirects.

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

## Explicit resource deficits and resource plans

Resource Miner now separates broad `Need Graph` affinity from explicit `Resource Requirement Objects`.

`data/resource_requirements.seed.json` contains the first gap-derived requirements. A confirmed requirement may contribute to `VERIFY_NOW` ranking; a conditional requirement is retained as information but cannot create work until its activation condition is established. Requirement matching still asserts neither applicant eligibility nor authority.

The resource-plan layer in `resource_miner/planning.py` generalizes this into a typed graph:

```text
NEED
-> CAPABILITY
-> WORK PACKAGE
-> RESOURCE REQUIREMENT
-> CONTROLLED RESOURCE
-> SUBSTITUTION ASSESSMENT
-> RESOURCE GAP
-> externally mineable requirement
```

A plan preserves `UNKNOWN`, `PARTIAL`, `CONDITIONAL`, and internal-composition gaps rather than treating every desired capability as an external funding need.

The first non-production specimen is `data/resource_plans/witness.seed.json`, which maps the proposed Internal HumanAIOS Agent — The Witness into needs, capabilities, bounded work packages, controlled resources, substitution assessments, and externally mineable deficits. It does **not** implement or authorize the Witness runtime.

Core invariants:

```text
NEED != RESOURCE
CAPABILITY != RESOURCE
RESOURCE_REQUIREMENT != RESOURCE
CONTROLLED_RESOURCE != ADEQUATE_SUBSTITUTE
RESOURCE_GAP != AUTHORIZATION
RESOURCE_DISCOVERY != ELIGIBILITY
```

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

### Three `data/resources*.jsonl` files, not one

- `data/resources.seed.jsonl` — curated fixture, hand-verified, checked in (see "First live specimen" above).
- `data/resources.jsonl` — ephemeral local/live scan output, git-ignored (see above).
- `data/resources.snapshot.jsonl` — durable scan output, checked in, refreshed daily by `.github/workflows/resource-miner-scan.yml`. This is what `app.py`'s `GET /api/resources` falls back to when no live scan has run yet in the current process, so results survive a Railway restart/redeploy without reversing the git-ignore decision above.

## Run as an HTTP service

`app.py` (repo root of this directory, sibling to the `resource_miner/` package) exposes the same discovery pipeline over stdlib HTTP, no third-party dependencies added:

```bash
python3 app.py --host 0.0.0.0 --port 8766
```

- `GET /api/health` — liveness.
- `GET /api/needs` — the current Need Graph.
- `GET /api/requirements` — explicit Resource Requirement Objects used for deficit-aware matching.
- `GET /api/resources` — the most recent scan output: `data/resources.jsonl` if present, else `data/resources.snapshot.jsonl`.
- `GET|POST /api/scan` — runs the same discovery -> `enrich()` pipeline as `python3 -m resource_miner.cli scan`, accepting the same `source`/`needs`/`funding_data`/`dev_tag`/`github_query`/`rss` fields as querystring params (GET) or a JSON body (POST). Read-only by default (`persist=false`); pass `persist=1` (or `"persist": true` in a POST body) to write `data/resources.jsonl`, matching this service's Z0/Z1 read-only-discovery framing — nothing here asserts applicant eligibility.
- `GET /api/entitlement/handoff?resource_id=<id>` — emits a typed, provenance-bearing `humanaios.resource-entitlement-handoff.v1` object for a selected live/snapshot resource. The handoff is always `VERIFY_ELIGIBILITY` with `eligibility_assessed=false` and authority effect `NONE`.

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

The runtime handoff is now explicit: `resource_miner.entitlement_handoff.build_entitlement_handoff()` converts the normalized resource into `humanaios.resource-entitlement-handoff.v1`. Entitlement Navigator (or a resolver between the two) should:

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

## Guiding Light handoff

Guiding Light is the pathway-navigation layer downstream of discovery and upstream of a consequential human/authority decision.

```text
Resource Miner
→ ResourceCandidate + provenance + need alignment
→ services/guiding_light_adapters.py
→ Guiding Light target
→ mandatory eligibility remains UNKNOWN unless separately assessed
→ VERIFY_AUTHORITY / domain resolver
→ mapped target
→ REACHABLE / BRIDGE / FRONTIER / HOLD
```

The adapter `resource_candidate_to_target()` may carry forward source URLs and Need Graph scores. It may **not** convert need alignment, route state, or `eligibility_assessed=false` into applicant eligibility. This is covered by `tests/test_guiding_light.py`.