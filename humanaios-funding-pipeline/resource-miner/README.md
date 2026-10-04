# HumanAIOS Resource Miner v0.1.14

Resource Miner is the **broad-discovery layer upstream of Entitlement Navigator**.

It asks:

> What externally available resources could reduce a currently modeled need, and what should be verified next?

At discovery time, a `ResourceCandidate` is best read as a **candidate resource opportunity**: a bounded external path to value that still requires currentness, eligibility, and acquisition resolution. A mine/platform is not itself the controlled resource, and an opportunity is not yet value under the user's control.

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
RESOURCE_MECHANISM != RESOURCE_AFFORDANCE
RESOURCE_AFFORDANCE != BENEFICIARY
NOMINAL_CASH != SPENDABLE_FOR_REQUIREMENT
RESOURCE_GAP != AUTHORIZATION
RESOURCE_DISCOVERY != ELIGIBILITY
```

Each normalized candidate now carries both `resource_types` (the mechanism, such as `grant`, `fellowship`, `compute_credit`, or `paid_work`) and `resource_affordances` (what that mechanism can potentially provide, such as `project_funding`, `self_labor_support`, `compute_capacity`, or `api_capacity`). Explicit Resource Requirement Objects may specify acceptable affordances; when they do, affordance mismatch is a semantic gate rather than an extra relevance score. Program restrictions, beneficiary rules, and exact use-of-funds remain downstream verification questions.

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

## Resource mine → opportunity → controlled resource

Resource Miner now distinguishes the **mine** from the value extracted from it. Existing source catalogs may still contain coarse mine-level or bundled records; source-specific resolvers should decompose those records into bounded opportunities before they are treated as acquisition targets:

```text
RESOURCE MINE
→ RESOURCE OPPORTUNITY
→ ACQUISITION / CLAIM / WORK
→ CONTROLLED RESOURCE
→ RESOURCE AFFORDANCE
→ OUTCOME
```

Examples:

- **Microsoft for Startups** is a resource mine. An eligible Azure startup-credit offer is a resource opportunity. The credit balance actually awarded to the startup is the controlled resource. Compute/API/storage/AI capacity are affordances of that resource.
- **HackerOne** is a resource mine. A specific bounty-bearing program plus its in-scope asset/reward rule is a resource opportunity. A bounty actually awarded after a valid report is a controlled monetary resource; reputation or credential evidence should be represented separately rather than silently merged into cash value.

This extends, rather than replaces, the existing invariants:

```text
MINE != OPPORTUNITY
OPPORTUNITY != CONTROLLED_RESOURCE
CONTROLLED_RESOURCE != RESOURCE_AFFORDANCE
RESOURCE_DISCOVERY != ELIGIBILITY
```

### Persistent Mine registry and tokenized Opportunity resolution

`data/mines.seed.json` is the persistent Mine registry. A Mine is a durable source/ecosystem, not the value extracted from it.

```text
ResourceMine
  -> repeated read-only observation
  -> ResourceCandidate (candidate Resource Opportunity)
  -> stable OPP-* identity
  -> urn:humanaios:resource-opportunity:OPP-...
```

Opportunity identity is derived from `mine_id + opportunity_identity + opportunity_kind`. The display title, published value, evidence, and status may change without minting a new token when the underlying bounded opportunity is still the same.

Mine roles are explicit and non-exclusive:

- `OPPORTUNITY_SOURCE` — may emit bounded external Resource Opportunities;
- `EVIDENCE_SOURCE` — can supply provenance/capability/currentness evidence;
- `GOVERNED_SYSTEM` — preserves proposed/accepted state, review, CI, and history;
- `CONTROLLED_RESOURCE_SOURCE` — reserved for cases where reusable code/data/tooling is itself a controlled capability.

A GitHub repository is therefore **not automatically a Resource Opportunity**. The repository resolver only emits open issues that satisfy explicit high-signal opportunity selectors (for example bounty/reward/prize/paid-work labels). Text inference is disabled by default. Repositories registered only as `EVIDENCE_SOURCE | GOVERNED_SYSTEM` produce a `ROLE_ONLY` resolution receipt and no Resource Opportunities.

The initial registry includes:

- Microsoft for Startups — `OPPORTUNITY_SOURCE | EVIDENCE_SOURCE`; bounded program endpoints are re-observed daily.
- HackerOne — `OPPORTUNITY_SOURCE | EVIDENCE_SOURCE`; the intended resolution unit is `Program x bounty-eligible ScopeAsset`. It remains dependency-gated until the scope-hydrated #680/#683 implementation is present.
- the HumanAIOS repositories — `EVIDENCE_SOURCE | GOVERNED_SYSTEM`; ordinary issues are not promoted into resources.

Run a Mine resolution manually:

```bash
python3 -m resource_miner.cli resolve-mines --dry-run

python3 -m resource_miner.cli resolve-mines \
  --out data/opportunities.snapshot.jsonl \
  --receipts-out data/mine-resolution.snapshot.jsonl \
  --claims-out data/opportunity-claims.snapshot.jsonl \
  --events-ledger data/opportunity-claim-events.jsonl
```

The scheduled `.github/workflows/resource-miner-scan.yml` executes this resolution before the broad Resource Miner scan. Durable outputs are:

- `data/opportunities.snapshot.jsonl` — latest tokenized Mine-derived Resource Opportunities;
- `data/mine-resolution.snapshot.jsonl` — per-Mine observation state and emitted opportunity IDs;
- `data/propositions.snapshot.jsonl` — deterministic `PRP-*` candidate propositions mined from current opportunities;
- `data/opportunity-claims.snapshot.jsonl` — evidence-bearing `CLM-*` Opportunity Claims for the current `OPP-*` set;
- `data/opportunity-claim-events.jsonl` — append-only, hash-chained Claim Evaluation Event ledger from which CLM state can be replayed;
- `data/resources.snapshot.jsonl` — existing broad-discovery snapshot.

Resolution receipts never grant eligibility, warrant, authorization, or execution permission. Observation failure preserves a configured opportunity identity but does not establish currentness.

### Opportunity Claim

Each tokenized Mine-derived opportunity now produces a separate `humanaios.opportunity-claim.v1` object. The opportunity is the stable bounded object; the claim is the revisable epistemic assertion about it.

```text
OPP-* Resource Opportunity
  -> CLM-* Opportunity Claim
       |- EXISTENCE
       |- CURRENTNESS
       |- TERMS
       |- ELIGIBILITY
       |- ATTAINABILITY
       |- evidence
       |- falsifiers
       |- unknowns / constraints
       |- warrant state
       |- authorization state
```

Falsification is facet-local: a closed opportunity falsifies `CURRENTNESS` and retires the claim without erasing historical `EXISTENCE`; materially wrong terms make the claim `CONTESTED`; only an existential falsifier makes the whole claim `FALSIFIED`.

Resource Miner never self-promotes applicant eligibility or authority. New claims start with `ELIGIBILITY=UNASSESSED`, `ATTAINABILITY=UNASSESSED`, `warrant_state=NOT_EVALUATED`, `authorization_state=NOT_REQUESTED`, `actionability_state=NOT_ACTIONABLE`, and `authority_effect=NONE`.

See `docs/OPPORTUNITY_CLAIM.md` and `schemas/opportunity-claim.v1.schema.json`.

### Private Gmail Mine

`aioshuman@gmail.com` is registered as an event-driven `MAILBOX` Mine with roles `OPPORTUNITY_SOURCE | EVIDENCE_SOURCE`.

The public Resource Miner runtime does **not** authenticate to Gmail. The existing private Gmail adapter owns credentials, raw message/thread IDs, bodies, MIME, mailbox URLs, and private event references. Resource Miner consumes only a privacy-minimized projection supplied through the private runtime.

```text
Private Gmail runtime
  -> raw mail stays private
  -> privacy-minimized candidate projection
  -> Resource Miner OPP / PRP / CLM / CEV graph
```

Mail content is always `UNTRUSTED_EVIDENCE`; it has `instruction_authority=NONE` in this path. The separate Daily Digest command processor remains the only mailbox command path and retains its own human-authority rules.

Without the private projection runtime, GitHub Actions must resolve this Mine as `DEPENDENCY_PENDING`; it must not simulate mailbox access.

### Proposition-first mining

Resource Miner now treats normalized source records as evidence containers rather than the final unit of reasoning.

```text
Mine -> record/observation -> OPP-* -> PRP-* -> CLM-* -> CEV-*
```

One opportunity may emit many stable `PRP-*` Proposition Candidates. Proposition identity is semantic (`opportunity + proposition type + predicate + object`), so display-title changes do not change identity while different object values remain distinct.

Direct observations may support observation propositions. Normalizer classifications and text extractions produce testable propositions but do **not** self-validate their external truth. A proposition-bound claim uses `claim_type=OPPORTUNITY_PROPOSITION`; parent opportunity existence/currentness cannot promote an unrelated proposition to `SUPPORTED`.

The scheduled Mine workflow persists `data/propositions.snapshot.jsonl` between the OPP and CLM layers. See `docs/PROPOSITION_MINING.md` and `schemas/proposition-candidate.v1.schema.json`.

### Cross-Mine proposition reconciliation

Resource Miner now relates independent `PRP-*` observations through a separate non-authoritative `PRS-*` layer.

```text
Mine A -> OPP-A -> PRP-A --\
                         -> PRS-*
Mine B -> OPP-B -> PRP-B --/
```

Each proposition carries a `resolution_subject_key`, allowing independent Mines to refer to the same bounded real-world subject without merging their local `OPP-*` or `PRP-*` identities.

Deterministic relations are `SAME_AS | SUPPORTS | CONTRADICTS | QUALIFIES | SUPERSEDES | CONTEXT_FOR | UNRESOLVED`. Resolution states are `SINGLE_SOURCE | CORROBORATED | CONTESTED | QUALIFIED | SUPERSEDED | UNRESOLVED`.

`CORROBORATED` means independent evidence origins made the same normalized assertion. Multiple Mines from the same origin do not count as independent corroboration. It does **not** mean the assertion has been promoted to truth. Every resolution set retains `truth_state=NOT_DETERMINED`, `eligibility_state=NOT_EVALUATED`, `warrant_state=NOT_EVALUATED`, `authorization_state=NOT_REQUESTED`, and `authority_effect=NONE`.

The scheduled Mine workflow persists `data/proposition-resolutions.snapshot.jsonl` between the PRP and CLM layers. See `docs/PROPOSITION_RECONCILIATION.md`.

### Evidence adjudication and verification frontier

After cross-Mine reconciliation, Resource Miner now evaluates the *standing of evidence* without converting source count or source prestige into truth.

```text
PRP-* -> PRS-* -> PAD-* -> VFY-*
```

`SourceStandingProfile` records are scoped by evidence origin and proposition type/predicate. A source can be primary for its own program status while still having no standing for a HumanAIOS machine classification derived from that page.

`PAD-*` states include `PRIMARY_SOURCE_PRESENT`, `MULTI_ORIGIN_NO_PRIMARY`, `NONPRIMARY_SOURCE_ONLY`, `DERIVED_ONLY`, `CONTESTED`, `UNRESOLVED`, and `SOURCE_STANDING_UNKNOWN`.

`VFY-*` frontier items identify missing evidence such as `PRIMARY_SOURCE_MISSING`, `DIRECT_EVIDENCE_MISSING`, `CONFLICT_REQUIRES_RESOLUTION`, `SOURCE_STANDING_UNKNOWN`, or `RELATION_UNRESOLVED`.

Every PAD/VFY object remains non-authoritative: `truth_state=NOT_DETERMINED`, `eligibility_state=NOT_EVALUATED`, `warrant_state=NOT_EVALUATED`, `authorization_state=NOT_REQUESTED`, and `authority_effect=NONE`.

See `docs/EVIDENCE_ADJUDICATION.md`.

### Verification work queue

Open `VFY-*` evidence gaps are compiled into deterministic `VWK-*` epistemic work items.

```text
PAD-* -> VFY-* -> VWK-*
```

Operations are `DISCOVER_PRIMARY_SOURCE`, `SEEK_DIRECT_EVIDENCE`, `RESOLVE_CONFLICT`, `ASSESS_SOURCE_STANDING`, or `DISAMBIGUATE_RELATION`.

Every work item is planning-only: `planning_state=PLANNED`, `execution_state=NOT_AUTHORIZED`, and `authority_effect=NONE`. A queue entry does not authorize browsing, contacting, submitting, purchasing, testing, or any consequential external action.

Because the queue is derived from the current verification frontier, a work item disappears automatically when new evidence closes its originating `VFY-*` gap on replay.

The scheduled Mine workflow persists `data/verification-work-queue.snapshot.jsonl`. See `docs/VERIFICATION_WORK_QUEUE.md`.

### Verification routing

Planned `VWK-*` epistemic work is now compiled into deterministic `VRT-*` capability routes.

```text
VFY-* -> VWK-* -> VRT-*
```

Routes distinguish `EXISTING_MINE_REOBSERVE`, `KNOWN_ORIGIN_REVIEW`, `DISCOVERY_REQUIRED`, `RESOLVER_REQUIRED`, and `SOURCE_STANDING_REVIEW`.

Persistent Mines may declare privacy-safe `evidence_origins` in configuration so the router can recognize that an existing Mine is capable of observing a requested origin. Capability binding does not change source standing and does not grant execution authority.

Every route retains `execution_state=NOT_AUTHORIZED` and `authority_effect=NONE`, including routes whose `capability_state=AVAILABLE`.

The scheduled Mine workflow persists `data/verification-routes.snapshot.jsonl`. See `docs/VERIFICATION_ROUTING.md`.

### Subject-scoped registry query plans

Queryable registry Mines now have a planning-only `RQY-*` layer between capability routing and any observation-authorization decision.

```text
REGISTRY MINE -> PATHWAY OPP -> RQY-* -> OAG-*
```

`RQY-*` stores only a privacy-safe `SUBJ-*` reference and semantic query-field names. Actual claimant/search values are `PRIVATE_RUNTIME_ONLY` and are not accepted by the public query-plan API.

The Colorado Great Colorado Payback Mine declares the reusable `UNCLAIMED_PROPERTY_OWNER_SEARCH` query class with semantic fields `owner_name`, `business_name`, and `last_known_location`. Transport-specific field mapping remains private/adapter-owned.

Every query plan requires an explicit subject request, must bind to an opportunity actually registered under the target REGISTRY Mine, and remains `planning_state=PLANNED`, `execution_state=NOT_AUTHORIZED`, `external_state_change=false`, `authority_effect=NONE`.

Result semantics are deliberately bounded: `NO_MATCH_OBSERVED != NO_ENTITLEMENT` and `MATCH_OBSERVED != OWNERSHIP | ELIGIBILITY | CLAIM_AUTHORIZED | FUNDS_RECOVERED`.

Use `python3 -m resource_miner.cli plan-registry-query ...` to create the plan object. The command does not perform a registry search. See `docs/SUBJECT_SCOPED_REGISTRY_QUERY.md`.

### Exact-query observation authorization

Resource Miner now includes an `OAG-*` Observation Authorization Gate that evaluates one exact `RQY-*` plan without seeing private runtime query values.

```text
RQY-* -> OAG-* -> later QRC-* execution receipt
```

The gate recomputes the RQY identity, verifies the registered Mine/pathway binding, checks the Mine query contract, and binds authorization to the SHA-256 of the canonical public RQY object.

A successful decision is one-shot and observation-only: `decision=ALLOW_OBSERVATION`, `authority_effect=OBSERVATION_ONLY`, `execution_state=NOT_EXECUTED`, `max_executions=1`, `consequence_ceiling=EVIDENCE_ONLY`, and `external_state_change=false`.

The OAG object never contains raw claimant/search values. It records only the opaque `SUBJ-*`, semantic query fields, public query-plan digest, and policy receipt. Private runtime values remain `PRIVATE_RUNTIME_ONLY`, and later execution must attest that those values resolve to the authorized subject binding.

Claim creation/submission/update, document upload, private claim-status access, account or credential mutation, messaging, payment, purchase, and fund transfer are hard-denied. `claim_submission_permitted=false` and `consequential_actions_permitted=false` are schema invariants.

Use `python3 -m resource_miner.cli authorize-registry-observation --query-plan <rqy.json>` to evaluate the gate. The command does not execute the registry query. See `docs/OBSERVATION_AUTHORIZATION_GATE.md`.

### One-shot query execution receipts

`QRC-*` records one completed private registry observation after an exact `OAG-*` authorization has been consumed.

```text
RQY-* -> OAG-* -> private runtime -> QRC-* -> later RMO-*
```

A QRC does not perform the registry query. It records lineage and scope after the private runtime has executed the observation. Minting requires both the exact public `RQY-*` and its covering `OAG-*`.

The receipt requires an opaque `PSB-*` private subject-binding attestation, exact authorized semantic fields, an authorized origin, a one-shot `EXE-*` execution nonce, timestamps, and a bounded result state: `ZERO_MATCHES_OBSERVED`, `MATCHES_OBSERVED`, or `OBSERVATION_FAILED`.

The runtime QRC ledger is append-only and git-ignored. A second receipt for the same `OAG-*` / consumption key is rejected under an exclusive file lock, so the historical OAG remains immutable while the ledger proves one-shot consumption.

No claimant/search values, raw request, raw response, cookies, tokens, or private claim identifiers are accepted into the public receipt. `authority_effect=NONE`: QRC is evidence that observation authority was consumed, not new authority.

Result semantics remain bounded: `ZERO_MATCHES_OBSERVED != NO_ENTITLEMENT` and `MATCHES_OBSERVED != OWNERSHIP | ELIGIBILITY | CLAIM_AUTHORIZED | FUNDS_RECOVERED`.

Use `python3 -m resource_miner.cli record-registry-query-execution ...` only to record an observation already completed by a private runtime. The command has no registry transport. See `docs/QUERY_EXECUTION_RECEIPT.md`.

### Reconstructable Claim state machine

`OpportunityClaim` is now a replayed projection of an append-only `humanaios.claim-evaluation-event.v1` history rather than the sole historical record.

```text
CLAIM_ASSERTED
  -> EVIDENCE_RECORDED*
  -> FALSIFIER_EVALUATED*
  -> FACET_RESOLVED*
  -> deterministic replay
  -> current CLM-* state
```

Each event is hash-addressed and chained through `previous_event_id`, and records actor, method, affected facet, prior/resulting state, evidence, uncertainty, and `authority_effect=NONE`. Replay rejects hash tampering, broken chains, and prior/resulting-state mismatches.

The durable ledger is `data/opportunity-claim-events.jsonl`. Scheduled Mine resolution appends genesis events for new claims and novel evidence events for existing claims while preserving the prior file prefix. `data/opportunity-claims.snapshot.jsonl` is a current-state projection/cache.

The state machine is regression-tested against the `Top Free Online Certifications` concept in `docs/FREE_ONLINE_CERTIFICATION_REPLAY.md`, demonstrating supported, retired, and contested claims without flattening free training, badges, paid exams, and certificates into one boolean.

See `docs/OPPORTUNITY_CLAIM_STATE_MACHINE.md` and `schemas/claim-evaluation-event.v1.schema.json`.

### Demand observations

`resource_miner.demand` adds a read-only demand-evidence layer. Demand may be observed against four distinct subjects:

- `MINE` — platform/program awareness, such as `HackerOne`;
- `OPPORTUNITY` — a claimable/earnable offer, such as `Azure startup credits`;
- `RESOURCE_CLASS` — the kind of value sought, such as `cloud credits for startups` or `bug bounty payout`;
- `NEED` — the underlying problem expressed by a searcher.

Query records also carry an intent class: `NAME | RESOURCE | PROBLEM | ELIGIBILITY | ACTION`.

Provider semantics are deliberately non-interchangeable:

- **Google Trends** CSV ingestion records normalized relative-interest indexes (0–100). These are not absolute search counts and not unique-user counts.
- **Bing Keyword Research** CSV ingestion records search volume/impression observations. These remain query/search-event observations, not deduplicated unique people.

Demand evidence is attached as `DemandSnapshot` records and does **not** alter `VERIFY_NOW | WATCH | ARCHIVE`, applicant eligibility, warrant, or authorization in this increment.

The parsers accept exported CSV evidence so observations can be receipted without scraping provider interfaces. Run the full regression suite with:

```bash
python3 -m unittest discover -s tests -v
```
