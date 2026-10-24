# HumanAIOS Resource Miner v0.1.8

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

## My AI Footprint: bounded Privacy Footprint Mine

`resource_miner/privacy_footprint.py` adds an on-demand, evidence-only mine for a
user's own supplied text. The v0.1 kernel detects explicit email, phone, and IP
address patterns in memory and can identify the same normalized identifier
across two or more supplied sources. It emits keyed commitments, evidence
locations, conditional privacy-resource requirements, and a QRC-style receipt.
Raw source text and detected values are not emitted.

The control path is:

```text
OAG consent grant -> one RQY audit -> privacy-minimized findings
  -> conditional Resource Miner requirements -> QRC receipt
```

This slice makes no network requests, stores no source content, runs no LLM,
does not fetch provider history, and cannot change or delete anything. An exact
identifier recurrence is a `LINKAGE_CANDIDATE`, not proof of common identity.
`ZERO_MATCHES_OBSERVED` is not proof of no exposure. See
`docs/PRIVACY_FOOTPRINT_MINE.md` and run:

```bash
python3 -m unittest discover -s tests -p 'test_privacy_footprint.py' -v

# Local one-shot run. The command uses an ephemeral in-memory HMAC key.
python3 -m resource_miner.privacy_footprint_cli \
  --input fixtures/privacy_footprint_synthetic.json --pretty
```

## MVP discovery adapters

- **Existing HumanAIOS funding pipeline** — imports canonical `../data/sources.json`.
- **DEV Community public Articles API** — scans challenge announcements through `#devchallenge`; public article listing requires no API key.
- **GitHub issue search** — supports open bounty/prize queries; optional `GITHUB_TOKEN` only increases rate limits.
- **HackerOne Hacker API** — read-only program discovery plus structured scope/exclusion metadata. Credentials are read only from `HACKERONE_API_USERNAME` and `HACKERONE_API_TOKEN`; the adapter never contacts program assets.
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

# HackerOne: enumerate programs visible to the authenticated Hacker API account.
# Do not put API credentials on the command line; set HACKERONE_API_USERNAME
# and HACKERONE_API_TOKEN in the environment.
python3 -m resource_miner.cli scan --source hackerone --dry-run

# One HackerOne program's metadata-only scope graph.
python3 -m resource_miner.cli hackerone-scope --handle eternal

# Arbitrary RSS/Atom feeds
python3 -m resource_miner.cli scan --source rss --rss 'https://example.org/opportunities.xml' --dry-run
```

Without `--dry-run`, output defaults to `data/resources.jsonl`, which is git-ignored because live scans are observations, not curated source code.

### Three `data/resources*.jsonl` files, not one

- `data/resources.seed.jsonl` — curated fixture, hand-verified, checked in (see "First live specimen" above).
- `data/resources.jsonl` — ephemeral local/live scan output, git-ignored (see above).
- `data/resources.snapshot.jsonl` — durable scan output, checked in, refreshed daily by `.github/workflows/resource-miner-scan.yml`. This is what `app.py`'s `GET /api/resources` falls back to when no live scan has run yet in the current process, so results survive a Railway restart/redeploy without reversing the git-ignore decision above.

### Witness feedback on the On-Track view (first-user E0.3)

The three local INTENT-OS views now form a **read-only evidence/choice loop**:

```text
/intent-os       -- Resource Miner discovery + source observations
/my-opportunities -- human selections, survey reports, references and journeys
/on-track        -- Witness P1 declaration -> P2 evidence challenge -> P3 human correction
```

The user-shared methodology reference for the On-Track view is
https://chatgpt.com/share/6adac2b6-8634-83ea-a544-80e060a0dd41 .
This implementation maps the established HumanAIOS **P1 declare → P2 calibrate/challenge → P3 correct** pattern, reviews Truthfulness, Service, Harm Awareness, Autonomy Respect, Value Alignment and Humility as *questions*, and points to **Observe → Measure → Identify Failure → Propose Improvement → Test → Compare → Repeat**. It does not issue ACAT numerical scores or claim that reading a shared conversation alone establishes the method.

**Procedure:** (1) At `/intent-os`, search for an opportunity, open **Report / verify this source**, select `Page returned 404` or `Possibly closed (not confirmed)`, and **Save source observation locally**. (2) At `/on-track`, choose the candidate, record a P1 initial belief (e.g. `CLOSED`), optionally record a falsifier, and click **Review evidence with Witness**. The current local Witness is **deterministic JavaScript** reading the browser's own local review packet, not a connected LLM or an independently authenticated human/AI witness. Its P2 output preserves a 404-versus-closure distinction and explicitly marks conflicting observations for review. (3) In P3 select `RECHECK`, `KEEP_ACTIVE`, or `DISMISS_LOCAL`, and click **Record my local decision**. Only the human can select and confirm a local dismissal. (4) Return to `/intent-os` and repeat search. A dismissed candidate is excluded from the **rendered local list** unless **Show candidates I dismissed locally** is selected. Underlying source rows, upstream candidate counts, provider accounts and other users remain unchanged. Re-running Witness with P3 `KEEP_ACTIVE` reverses the dismissal; exported unsigned feedback preserves the local review.

**Convergent Research test case (October 22, 2026):** The human observed a Lever posting URL return 404 and later reported that the role was absent from the employer board, requesting elimination. Separate fresh public indexing still showed Program Launch Manager on the employer Lever board and an application page. These **contradictory temporal/source observations** must be investigated rather than converted into automatic global archive or applicant ineligibility. `DISMISS_LOCAL` is a human preference; **`OPPORTUNITY_CLOSED_VERIFIED` is NOT emitted**. This prevents one user's session or an ephemeral HTTP error from changing all users' discoveries.

Privacy and control: Reports and local dispositions are stored in **unencrypted origin-scoped browser localStorage**, and the read-only Witness does not call remote AI, Gmail, Discord, GitHub, employment sites or cloud services. Clear local history through the search page and reset P3 to `KEEP_ACTIVE` if you no longer want dismissal. Neither the Witness nor a P3 choice grants authorization for server-side deletion. Future verified de-listing requires independent canonical-source evidence, confidence/expiry policy, an authorized reviewer and a separately admitted backend change.

### Source verification feedback from search results (first-user E0.2)

**Use:** Browse \`/intent-os\` on the local service. Search for a resource. Each result card now has **Report / verify this source**. Open it and choose a human observation:

- \`LINK_FAILED_404\` — the exact URL returned a 404 in your browser; **does NOT prove opportunity closure**.
- \`PAGE_UNAVAILABLE_OTHER\` — another source-loading problem.
- \`SOURCE_WORKING\` — link loaded for the human; not independently checked.
- \`REPLACEMENT_FOUND\` — human supplies candidate replacement URL; official-source recheck required.
- \`POSSIBLY_CLOSED\` — human suspects closure; provider status unknown.
- \`ALREADY_IN_USE\` — user believes this resource is already controlled/used; ownership not independently established.
- \`OTHER\` — other issue or observation.

Add an optional explanation and **replacement/evidence HTTPS URL**. Optionally choose an **evidence file of any type, including PDF (max 10 MiB)**; it is **hashed in this browser only**. The file contents and filename are never transmitted, saved or embedded in the JSON packet. Only MIME type, size and SHA-256 accompany your saved note, URLs, status and time. Keep the original file for a reviewer.

Click **Save source observation locally**. The record is appended to the browser's private source-review queue. The candidate card shows the most recent observation on the next search. **Export verification review packet** downloads \`intent-os-source-verification.json\` with schema \`humanaios.resource_source_review.v0.1\`. Use **Import review packet** to move reports to another origin/port or combine locally. An offline reviewer can execute:

\`\`\`sh
python3 -m resource_miner.source_review --input /path/to/intent-os-source-verification.json
\`\`\`

This produces **review tasks**, never an \`OPPORTUNITY_CLOSED\`, \`VERIFIED_ELIGIBLE\` or \`SOURCE_CATALOG_UPDATED\` claim. The user-supplied fields may be inaccurate or manipulated. **No central submission, server save, GitHub issue, auto source deletion, global ranking change or automatic source recheck is performed.** A separate authenticated user-controlled evidence intake and independently approved review queue is needed for remote submission. Never commit a packet containing personal notes, browsing artifacts or screenshots to public GitHub.

**First example (2026-10-22):** Human observed a 404 from the Convergent Research Program Launch Manager Lever link. Later the public official Convergent Research job board still listed Program Launch Manager, so the correct user-visible task is \`RECHECK_SOURCE_URL_AND_OFFICIAL_BOARD\` rather than silently archiving the job. Browser screenshot is user evidence for URL failure, not proof that the employer withdrew the role. This is a test of correcting stale source links, not filtering relevant opportunities based on link status alone.

**Checkbox clarification:** The initial \`/my-opportunities\` view shows synthetic demonstration events. A previously completed event is deliberately checked and read-only. Choose **Start a blank-action checklist** for a fresh editable set of unchecked human actions; this clears the synthetic prefilled action events and retains a clearly synthetic discovery label. If you have a real record, import its JSON instead of creating duplicate events. Recording a human statement does not prove third-party receipt.

### E0.1: checkbox reports + browser-private evidence attachment

The **Record an explicit human report** section now contains three independent **checkboxes** (selected, survey submitted, Discord joined) rather than a dropdown. The checkboxes are available with an editable/imported journey, and already recorded events display as checked and cannot be submitted twice. Recording is a user assertion, never participant qualification or third-party consent. To correct an existing recorded claim, edit the exported sanitized journey JSON deliberately and re-import; the prototype does not silently delete earlier receipts.

**Attach supporting evidence:** open an editable record; paste a link into the evidence URL field, select its related claim or **Context only**, optionally paste a short excerpt (max 750 characters), and click **Attach evidence locally**. Example forms: a Gmail message URL and a Discord message URL. Neither one is fetched by the application. An Apart Discord community **rules** message is *context-only*, not proof of membership or permission for a bot to read server messages. Follow the server's posted rules, including respectful collaboration, IP attribution, and no self-promotion.

**Evidence trust boundary:** the UI stores link/excerpt records separately from the \`project_journey\` JSON passed to \`POST /api/my-opportunities/project\`. A pasted Gmail URL has not undergone a Gmail connector read or sender/signature verification. A Discord link or excerpt has not been independently authenticated or granted redistribution rights. Simply attaching a URL cannot add an event or promote \`HUMAN_REPORT\` to \`PROVIDER_EMAIL_OBSERVED\` or \`PARTICIPANT_QUALIFIED\`. No server evidence upload endpoint is introduced.

**Persistence and migration:** \`Export private JSON bundle\` now downloads a single **sensitive plaintext** \`intent-os-private-evidence-bundle.json\` containing both the sanitized journey and browser-local evidence records; import supports this new bundle and the old journey-only JSON format. Browser save is **explicit**, not automatic, and includes private evidence links/excerpts. Storage is **unencrypted** and scoped by browser origin/port. Export the bundle before switching ports or wiping browser data, and import it at the new origin. Avoid passwords, access tokens, highly sensitive snippets, or material you don't have permission to retain. Never commit bundle contents to public GitHub or share them over Discord.

**Read-only boundary:** the public \`/intent-os\` page still performs public discovery. New evidence additions do not cause mail sends, Discord reads/posts, form submission, cloud saves, or code changes.

## My Opportunities: local-only journey interface (first-user E0)

The new **My Opportunities** interface is backed by the real `resource_miner.opportunity_journey.project_journey` reducer, not a static status diagram. It deliberately **does not** import Gmail, Calendar, or Discord accounts or prove participation on its own. The default Apart sprint record is explicitly a **synthetic demonstration**, and real-life status must be imported in a user-controlled JSON record.

**Run on your Mac (the server MUST bind to loopback):**

```bash
cd humanaios-funding-pipeline/resource-miner
python3 app.py --host 127.0.0.1 --port 8766
```

Browse `http://127.0.0.1:8766/intent-os` and select **My Opportunities**, or open `http://127.0.0.1:8766/my-opportunities` directly. The entry link is shown only when the local-only projection route is reachable.

The page shows an Apart Research starter journey with separate proof categories for discovery, selection, signup welcome email, human-reported survey submission, calendar event and Discord join. It explicitly keeps `PARTICIPANT_QUALIFIED`, research submission and funding/awards **unverified**. Suggestions are review tasks, not automatically executed actions.

To work with **your own record** without sharing it:

1. Select **Use editable starter** to load synthetic fields, then **Export current JSON** as a template, or import an existing bounded JSON record using the file input.
2. **Replace all `SYNTHETIC-*` evidence references with your own short opaque local identifiers** before regarding it as your real report. Those identifiers are *claims* in this offline file, not automatically verified evidence. Do not insert email addresses, names, private URLs or message contents.
3. Add a report using the **Record my report** selector; only human-selected, survey-submitted and Discord-joined report kinds may be added. A human cannot assert provider participant qualification via this UI.
4. **Export current JSON** to save a local backup, or choose **Save privately in this browser**. Browser persistence is explicit, not automatic, is **unencrypted**, and survives reload on the same origin/port only. Deleting the browser's saved record does not delete exported files.
5. The `POST /api/my-opportunities/project` route only computes a bounded projection; it performs **no server-side file write**. If you do not save or export, the unsaved imported/edited record is lost on reload.

**Security boundary:** `GET /my-opportunities`, `GET /api/my-opportunities`, `GET /api/my-opportunities/starter`, and `POST /api/my-opportunities/project` return 404 if the app is not bound to loopback, or the client IP/Host/Origin are not local and allowed. In particular, **Azure Container Apps with `--host 0.0.0.0` cannot serve the private journey interface**. This is a local privacy prototype, **not user authentication**. Do not expose your local machine with a tunnel or reverse proxy; production requires explicit login, a user-specific storage boundary, and independent authorization review. The public Resource Miner `/intent-os` route and its search API are unchanged.

To test:

```bash
python3 -m unittest discover -s tests -p 'test_opportunity_journey_e0.py' -v
python3 -m unittest discover -s tests -p 'test_my_opportunities_http.py' -v
python3 -m unittest discover -s tests -p 'test_intent_os_bridge.py' -v
```

**Existing Mac worktree protection:** The user's original `operations` worktree has unrelated uncommitted work. Never `git reset --hard`, `git clean`, `git checkout`, or pull onto that worktree to try this feature. From an already clean `operations-intent-os` worktree, `git fetch origin feat/intent-os-opportunity-journey-e0-20261022`, then `git worktree add --detach ../operations-my-opportunities FETCH_HEAD`. Launch the new checkout on port `8767` first so the running port `8766` service stays available. When ready to switch, stop the 8766 server with Ctrl+C and run the newer code on 8766. Do not delete the previous worktree until independently verified.

## Run as an HTTP service

`app.py` (repo root of this directory, sibling to the `resource_miner/` package) exposes the same discovery pipeline over stdlib HTTP, no third-party dependencies added:

```bash
python3 app.py --host 0.0.0.0 --port 8766
```

- `GET /api/health` — liveness.
- `GET /api/needs` — the current Need Graph.
- `GET /api/requirements` — explicit Resource Requirement Objects used for deficit-aware matching.
- `GET /api/resources` — **operator-only**, returns live scan or snapshot; requires HTTP admin authentication because stored scans may include private source observations.
- `GET|POST /api/scan` — **operator-only** HTTP scanning. Requires a separately provisioned `RESOURCE_MINER_ADMIN_TOKEN` (at least 32 characters) and matching `X-Resource-Miner-Admin-Token` header. Without these, returns HTTP 403. This endpoint accepts source/path options and can persist output, so it MUST NOT be exposed anonymously. CLI scanning remains available without the HTTP admin token.
- `GET /api/entitlement/handoff?resource_id=<id>` — **operator-only**, emits a typed, provenance-bearing handoff from stored scans. Requires HTTP admin authentication; eligibility remains unverified and authority effect remains `NONE`.


**HTTP admin boundary:** Configure the token in your deployment secret manager, not in source code, a repository issue, a browser, or the public INTENT-OS page. The admin API is disabled without a configured strong token. Requests to `/api/scan`, `/api/resources`, and `/api/entitlement/handoff` need `X-Resource-Miner-Admin-Token`. Use a trusted non-browser operator client for those endpoints. Existing remote scan or Entitlement Navigator clients need explicit authorized credential wiring before reuse. Check reverse-proxy access logs do not store secret headers. Authentication is not authorization for arbitrary external target testing; source-specific policy still applies. The public `/intent-os` and `/api/intent` routes remain unauthenticated but read-only; deploy only with upstream rate/request-concurrency controls.

## INTENT-OS: human objective -> Resource Miner (public read-only bridge)

The **existing Resource Miner HTTP service** now serves a small mobile-friendly INTENT-OS page.

- Open `/intent-os` (or `/`) on the running Resource Miner service.
- Enter one plain-language goal and choose `Public discovery + curated funding` or `Last stored funding snapshot`.
- The page calls `POST /api/intent` on the **same origin** and displays up to 10 matching resource candidates with source links to verify, provenance, limits and an unsigned reproducibility digest.
- Live mode uses the existing **public DEV Community adapter** plus the curated HumanAIOS funding source, and discloses any upstream failure. Snapshot mode reads the previously committed funding snapshot without network.
- This is not the previous E0/E1 synthetic demonstration, and it does not require the user to operate GitHub or the terminal once the service is deployed. This is an HTTP integration against existing candidate models, not a new adapter protocol.

Example:

```bash
python3 app.py --host 127.0.0.1 --port 8766
# Open http://127.0.0.1:8766/intent-os
curl -sS -X POST http://127.0.0.1:8766/api/intent \
  -H 'Content-Type: application/json' \
  -d '{"objective":"Find compute credits for AI research","source_mode":"live"}'
```

**Privacy / authority:** Do not enter private identifying details. The HTTP service does not persist the objective. No cookies, third-party scripts, account access, applications, purchases, outreach, eligibility determination or authorization are performed. The returned SHA-256 selection digest is *not* an authenticated witness receipt. Resource descriptions are untrusted text rendered as text, not instructions. Only the public funding pipeline and DEV candidate classes are allowed through this new route; private Gmail and HackerOne discovery are excluded even if they exist elsewhere in the repository.

**Operational limits:** The live feed may be unavailable; the service will say so and show labeled curated results instead. The funding catalog is not a live eligibility source. The existing deployed service must be updated to the approved commit before the new page works. Reusing the existing Railway start command is sufficient; do not treat a green PR as evidence that public deployment has happened.

Tests:

```bash
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_intent_os_bridge.py' -v
```

## HackerOne scope and authorization boundary

The HackerOne adapter is intentionally split into three layers:

```text
HackerOne Hacker API
  -> ResourceCandidate discovery
  -> ProgramScopeGraph (program -> structured asset -> exclusion)
  -> authorize_security_action()
  -> PASSIVE_RECON | MANUAL_TESTING | BOUNDED_AUTOMATION
     | NOT_AUTHORIZED | SCOPE_CLARIFICATION_REQUIRED
```

The first two layers read **HackerOne metadata only**. They do not contact a program asset.

The authorization gate in `resource_miner/security_authorization.py` is a pure decision function. It has
`execution_capability=NONE` and requires explicit inputs for program currentness, policy review,
method permission, and human authorization. Missing/ambiguous scope information fails closed.
Destructive action, denial of service, social engineering, credential attacks, and bulk data access
are denied by the gate.

Core invariants:

```text
SCOPE_LISTING != AUTHORIZATION
IN_SCOPE_ASSET != ALL_METHODS_ALLOWED
PROGRAM_POLICY != HUMAN_AUTHORIZATION
AUTHORIZATION_DECISION != EXECUTION
AMBIGUITY => FAIL_CLOSED
```

The HackerOne source is deliberately **not exposed through the unauthenticated Resource Miner HTTP
service**. A HackerOne account can expose private-program metadata; publishing that through the
existing service would cross the current privacy boundary.


## HackerOne portfolio → capability match → ranked review queue

The portfolio layer extends metadata-only HackerOne discovery without adding target execution:

```text
HackerOne programs
  -> program policy + structured scopes + exclusions
  -> Machine Substrate Graph capability evidence
  -> per-asset capability match
  -> deterministic readiness score
  -> ranked review queue
  -> downstream policy/method review
  -> Security Authorization Gate
```

The rank is **investigation readiness**, not exploit value and not authorization. It is driven primarily by
explicitly observed capability coverage and current scope state. Bounty eligibility contributes only a
small signal; severity is preserved as scope metadata but does not increase rank.

Capability evidence is derived from `tools/machine_graph` observation states. Missing tools remain
`UNKNOWN` or `OBSERVED_UNAVAILABLE`; the matcher never converts absence of evidence into capability.

To refresh the local capability snapshot on macOS:

```bash
python3 tools/machine_graph/collect_macos.py \
  --root "$HOME/HumanAIOS-machine-scan" \
  --venv "$HOME/HumanAIOS-machine-scan/shacl-test/venv" \
  --output "$HOME/HumanAIOS-machine-scan/machine-graph/machine-substrate.json"
```

Then build the authenticated HackerOne portfolio queue:

```bash
export HACKERONE_API_USERNAME='YOUR_HACKERONE_API_IDENTIFIER'
export HACKERONE_API_TOKEN='YOUR_HACKERONE_API_TOKEN'

python3 -m resource_miner.cli hackerone-portfolio \
  --machine-graph "$HOME/HumanAIOS-machine-scan/machine-graph/machine-substrate.json" \
  --out "$HOME/HumanAIOS-machine-scan/hackerone/ranked-portfolio.json"
```

The output intentionally lives outside the repository in this example because an authenticated HackerOne
account may expose private-program metadata.

Each queue entry includes:
- program and scope identity;
- asset class;
- submission/bounty eligibility;
- candidate review mode;
- required capability and evidence references;
- missing capability evidence;
- effort class;
- readiness score and rationale;
- `authorization_state=NOT_EVALUATED`.

Core invariants:

```text
PORTFOLIO_VISIBILITY != AUTHORIZATION
CAPABILITY_CLAIM != CAPABILITY_EVIDENCE
CAPABILITY_MATCH != METHOD_PERMISSION
RANK != AUTHORIZATION
QUEUE_ENTRY != EXECUTION
```

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
- My AI Footprint — `EVIDENCE_SOURCE` only; an explicit grant bound to one query ID may inspect user-supplied text in memory, but replay prevention is not implemented, and persistent Mine resolution emits `ROLE_ONLY` without reading private content.

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


### Evidence files, Show more, and teaching the Witness

Source review accepts any file type, including PDFs, images, documents, text and
archives (1 byte to 10 MiB). Files are hashed locally, never parsed, executed,
uploaded or retained by the app. Saved in browser storage and review exports:
notes, URLs, selected status, observation time, MIME type, byte size and SHA-256.
The filename and file contents are not saved. Keep the original evidence file.
For compatibility, attachment metadata still uses the existing `evidence.screenshot`
field; old image-only review packets remain supported. A fingerprint does not
prove source availability or verify a document's claims.

The search API returns every match within its existing 500-row examination bound.
The browser starts with ten cards; **Show more** reveals the next ten without
repeating the search. Counts reflect the currently visible cards. Witness local
dismissals stay separate and reversible through **Show candidates I dismissed locally**.

Each card has **Teach the Witness about this resource**. Save a note and choose
**Remember note only**, **Show this earlier**, or **Show this later**. Notes and
preferences persist only in this browser, capped at 100 lessons. Preferences reorder
future local displays while keeping every eligible candidate accessible. They do
not change shared ranking, provider data, source verification, or model weights.
**Export Witness lessons** creates a separate JSON packet for human review;
**Clear Witness lessons** reverses these local preferences. No automatic central
submission, model training, or promotion of a human note into verified evidence occurs.
