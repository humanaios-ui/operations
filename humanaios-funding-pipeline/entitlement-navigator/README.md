# Entitlement Navigator — v0.2

A local-first, evidence-bearing investigation engine for this operational question:

> **Is there an existing asset, legally cognizable benefit, or funding pathway attached to an individual, household, business, nonprofit, estate, property, or ancestral chain — and what exact evidence and action are required to establish or obtain it?**

v0.2 changes the front door from a Cherokee-specific questionnaire to a **general intake + adaptive interrogation + research + action** pipeline. Cherokee Nation, trust/IIM, Dawes, allotment, and probate pathways remain first-class seed modules rather than assumptions applied to every user.

## Core pipeline

```text
General user statement
→ legal applicant/entity graph
→ adaptive interrogation
→ user evidence / document ingestion
→ authoritative research queue
→ deterministic predicate resolution
→ asset / benefit / funding classification
→ evidence gap
→ prioritized action/application/claim path
→ agency or authority decision
→ resolved case
```

The engine maintains a provenance boundary between:

- `USER_ASSERTED`
- `USER_FILE_CLUE`
- `RESEARCH_CANDIDATE`
- `CORROBORATED`
- `AUTHORITY_VERIFIED`

A clue may route research. It does **not** silently become a legal fact.

## Result classes

`RULE_MATCH` · `CONDITIONAL_MATCH` · `INVESTIGATE` · `INELIGIBLE` · `CLOSED_HISTORICAL` · `GENERAL_OPPORTUNITY`

The software never issues an award, title determination, probate decision, lending decision, citizenship determination, or final agency eligibility decision.

## Run locally

Requires Python 3.10+ and only the Python standard library.

```bash
cd operations/humanaios-funding-pipeline/entitlement-navigator
python3 app.py
```

Open:

```text
http://127.0.0.1:8765
```

The service binds to localhost by default. User intake, genealogy interview state, and imported GEDCOM text are evaluated in memory unless the user explicitly exports or runs the local import script.

## Adaptive intake

The browser starts with three general questions:

1. What is happening / what are you trying to find, recover, fund, protect, or apply for?
2. Which legal applicant roles are involved?
3. Which outcomes should be investigated?

The server then selects the next discriminating question from active domains instead of presenting a fixed survey. Current domain modules include:

- tribal/citizenship;
- business capital and procurement;
- education/training;
- household assistance;
- housing/property;
- genealogy/estate/trust assets;
- general federal funding discovery.

The question router is in `entitlement/interrogator.py`.

## Genealogy evidence module

v0.2 supports two inputs.

### A. Import an existing GEDCOM

`entitlement/genealogy.py` parses GEDCOM 5.5.1-style exports, builds parent/family links, traces direct ancestors from a focus person, follows linked evidence records, and scans only for **research-routing clues** such as:

- Cherokee Nation;
- Native American;
- Indian Territory;
- Dawes;
- allotment;
- Final Roll / enrollment;
- probate;
- trust/restricted land;
- IIM.

Those clues do not establish enrollment, allotment ownership, current title, heirship, or an IIM account.

### B. Build genealogy through interrogation

`entitlement/genealogy_builder.py` can construct a conservative genealogy draft from user answers. It asks for:

- best-known full name;
- alternate/maiden/spelling variants;
- birth/death date and place;
- parents;
- tribal/Native/agency/allotment clues;
- the evidence source supporting each assertion.

It exports a GEDCOM-compatible draft. User-provided clues are explicitly marked as user-reported notes rather than verified facts.

## Genealogy → property / trust research pipeline

```text
person identity
→ direct ancestral relationship
→ authoritative historical enrollment, if relevant
→ census/enrollment card
→ enrollment packet
→ allotment jacket / parcel
→ exact legal description
→ title chain
→ probate / heirship
→ present trust/restricted ownership
→ associated IIM / estate trust funds
→ agency-verified action
```

No link may be skipped. A Dawes ancestor is not proof of current ownership.

## Private evidence boundary

Raw genealogy is never intended for source control.

```text
private/
  evidence/genealogy/       # raw GEDCOM — gitignored
  derived/                  # names, direct-ancestor graph — gitignored
  cases/                    # local case files / generated case skills — gitignored

evidence/
  manifests/                # sanitized hashes/counts/categories only
```

`.gitignore` excludes the entire `private/` directory.

To import a GEDCOM into the local evidence boundary:

```bash
python3 scripts/import_genealogy.py /path/to/tree.ged --focus "Focus Person Name"
```

If `--focus` is omitted, the parser may provisionally use the first individual in an Ancestry export and records that assumption as `assumed_first_individual`.

## Case-specific genealogy remains private

Do not commit hashes, counts, names, direct-ancestor graphs, or research clues from a real user's GEDCOM. The repository ships only `evidence/manifests/genealogy-manifest.example.json`; local imports write case material under the git-ignored `private/` boundary.

## Research queue

`entitlement/research.py` converts unresolved pathways into tasks with:

- purpose;
- primary authority;
- source URL;
- required inputs;
- success evidence;
- dependency chain;
- evidence state.

The genealogy module generates the dependent sequence `GEN-01 → GEN-02 → GEN-03 → GEN-04` for Dawes identity resolution, allotment retrieval, title/probate reconstruction, and BTFA/IIM verification.

General discovery generates separate tasks for SAM.gov Assistance Listings and Grants.gov. Grants.gov's public `search2` API remains implemented in `entitlement/grants.py` and opportunities remain `GENERAL_OPPORTUNITY` until their applicant eligibility is parsed and tested.

## Case files and generated skills

`entitlement/casefile.py` composes:

- user-asserted profile;
- derived evidence with separate provenance;
- relevant deterministic pathways;
- research queue;
- prioritized actions.

`entitlement/skillgen.py` then converts that case into an agent-ready research skill enforcing the same evidence chain and stop conditions.

A reusable static skill also lives at:

```text
skills/entitlement-evidence-research/SKILL.md
```


## Integration with the HumanAIOS funding pipeline

When this project lives at `operations/humanaios-funding-pipeline/entitlement-navigator/`, it automatically discovers the canonical funding dataset at `../data/sources.json`.

`entitlement/funding_adapter.py` exposes that dataset as a discovery source without converting its existing tags into eligibility claims. The local API endpoint is:

```text
POST /api/funding/local/search
```

Example:

```json
{
  "keyword": "native",
  "native_only": true,
  "categories": ["native", "research_grant"],
  "limit": 25
}
```

Returned records are classified `GENERAL_OPPORTUNITY` with `eligibility_assessed=false` until authoritative program criteria are tested. The case research queue also includes `DISCOVERY-LOCAL-FUNDING` ahead of SAM.gov and Grants.gov discovery.

## API

### `POST /api/interrogate/next`

```json
{"profile": {}}
```

Returns the next highest-value question or `complete: true`.

### `POST /api/case/evaluate`

```json
{
  "profile": {
    "intake_statement": "Find inherited assets and current assistance.",
    "applicant_roles": ["Individual", "Estate / heir"],
    "funding_goals": ["Estate / inheritance", "Tribal trust land / IIM"]
  },
  "genealogy_patch": null,
  "genealogy_summary": null
}
```

### `POST /api/genealogy/import`

```json
{
  "gedcom_text": "0 HEAD\n...",
  "focus_query": "Optional Focus Person"
}
```

Returns a sanitized genealogy summary plus a derived routing patch. It does not return person names.

### `POST /api/genealogy/start`
Starts the genealogy interrogator.

### `POST /api/genealogy/answer`
Advances a genealogy interview draft.

### `POST /api/genealogy/export`
Exports the interview draft as GEDCOM.

### `POST /api/skill/generate`
Generates a case-specific research skill from a case file.

### `POST /api/grants/search`
Searches current Grants.gov opportunities through the public API.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

v0.2 currently includes regression tests for the original deterministic engine plus tests for:

- general-first intake;
- non-tribal general funding routing;
- genealogy activation;
- GEDCOM clue vs. Dawes fact separation;
- genealogy-to-GEDCOM export;
- suppression of unactivated unknown programs.

## Production roadmap

1. Add official Assistance Listings ingestion and deterministic applicant-type parsing.
2. Add source snapshots, hashes, verification timestamps, and stale-rule alerts.
3. Add entity-resolution scoring for historical records: name, age/date, family relations, geography, and record identifiers.
4. Add an evidence ledger so each research observation changes a predicate by an explicit receipt.
5. Add application packet generation only after a specific pathway reaches submission-ready status.
6. Add encrypted local document vault and explicit consent gates for identity documents.
7. Add agency-response tracking and closure receipts.
8. Keep all genealogy/title research falsifiable: record negative searches and contradictions rather than pruning them silently.

## Legal / operational boundary

This is a screening, research orchestration, and evidence-management tool. It does not replace the administering tribe, BIA, BTFA, NARA, HUD, a lender, a probate judge, an attorney, an accountant, or any other authority that makes the underlying legal or eligibility determination.
