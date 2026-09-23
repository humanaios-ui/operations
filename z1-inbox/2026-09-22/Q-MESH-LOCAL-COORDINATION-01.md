# Q-MESH-LOCAL-COORDINATION-01 — Local mesh coordination layer for three practices

**Status:** Z1 candidate · awaiting Z2 ratification · **no Z2 hash**
**Filed:** 2026-09-22 (OBSERVATIONAL — carries no scheduling authority)
**Pin (HISTORICAL_RECORD):** `operations` @ `44347b79b1d6351bd10bbb5fb6c45b9ead6bd42e` (= `origin/main` at session open)

---

```yaml
candidate_id: "Q-MESH-LOCAL-COORDINATION-01"

title: "Local mesh coordination layer in operations/mesh/ for humanaios, website, grok-crossref"

description: |
  Adds `mesh/` to the operations repository: a local coordination surface holding one record per
  practice, a record schema with closed vocabularies, a cross-reference register binding the
  practices to five open governance artifacts, and executed conformance evidence.

  Two of the three practices (`humanaios`, `website`) are AMBIGUOUS in
  ledgers/PRACTICE_RESOLUTION_MAP.md and cannot have their forecast tokens resolved while Z2
  decision D1 is open. The records describe each practice without selecting a resolution target,
  so coordination proceeds without manufacturing a verdict.

  This candidate makes the ambiguity wider, not narrower: a local record is a third candidate
  target where there were two. That is stated here rather than left for a reader to find.

author: "Z1 (Claude)"
proposed_at: "2026-09-22T00:00:00Z"

scope:
  - "operations (Z-000) — new directory mesh/"
  - "z1-inbox/2026-09-22/"
  - "No change to REGISTERED.md, PRIORITY_QUEUE.md, ZONE_REGISTRY.md, MOLT_STATE.md, NF_LEDGER.jsonl, constitution.json"

resource_cost:
  estimated_effort_units: 3
  dependencies:
    - "constitution.json"
    - "tools/agents/_shared/constitution_checker.py"
    - "ledgers/PRACTICE_RESOLUTION_MAP.md"
    - "ledgers/NF_LEDGER.jsonl"
    - "ledgers/mesh_pins_090826.json"
    - "ZONE_REGISTRY.md"
    - "PLANNED_REPOS.md"
  blocking_on:
    - "D1 (PRACTICE_RESOLUTION_MAP.md) — unresolved; this candidate does not depend on D1 being ruled, but two of its three records stay unresolvable until it is"

impact_prediction:
  resource_impact: 4
  areas_affected:
    - "Z-000 operations"
    - "practice coordination for humanaios, website, grok-crossref"
  positive_outcomes:
    - "Each of the three practices has one readable record of what it owns, declines, consumes and forecasts"
    - "The five linked governance artifacts are bound to the practices they constrain, with each artifact's disclaimers carried alongside its claims"
    - "Three adversarial findings from PR #451 are carried as implemented controls rather than cited"
    - "Coordination proceeds on the two blocked practices without writing a ledger verdict"
  risk_factors:
    - "A third candidate resolution target widens D1"
    - "A local record could be read as standing the layer does not have; the schema pins authority.grants_authority to const false, and the charter states the boundary, but a reader can still misread a directory named mesh/"
    - "Records are derived and go stale when a practice gains content or a repo is created"
    - "mesh/conformance/*.py sits outside tools/, so builder-lint.yml and tool-manifest.yml do not run on it; stated in the file header and routed to Z2 as D4"

falsifier: |
  This candidate is FALSE, and should be narrowed or withdrawn, if any of the following is observed:

  1. A local practice record is cited anywhere as the basis for a proposal cap, ratification
     right, or execution right that ZONE_REGISTRY.md or CLAUDE.md does not already grant.
  2. Any row is appended to ledgers/NF_LEDGER.jsonl resolving a `humanaios` or `website` token
     against a read of mesh/practices/ while D1 is unruled.
  3. A field in any practice.yaml cannot be traced to a readable in-tree source and is not marked
     UNKNOWN.
  4. mesh/practice_local.schema.json validates a record containing a key the schema does not
     declare — the additionalProperties: false control fails open.
  5. The local records and ledgers/PRACTICE_RESOLUTION_MAP.md disagree on a practice's resolution
     class and the disagreement survives one maintenance pass.

  Falsifier 4 is executable: `python3 mesh/conformance/validate_mesh.py` runs it as negative
  case 1 and exits nonzero if the control fails open.

evidence:
  - "mesh/conformance/CONFORMANCE_RUN.md — verbatim output of both conformance scripts; 11 checks, 0 violations, exit 0"
  - "mesh/conformance/validate_mesh.py — 3 positive cases, 8 negative controls demonstrated to refuse"
  - "mesh/conformance/run_constitution_check.py — constitution.json v1.0 (22 principles) run over this drop's commits, decision, finding and artifact graph"
  - "ledgers/PRACTICE_RESOLUTION_MAP.md — resolution classes and the D1/D2 statement, quoted not restated"
  - "ledgers/NF_LEDGER.jsonl — 14 token rows across the three practices, read at the pinned sha"
  - "mesh/CROSS_REFERENCE_REGISTER.md — claim/disclaimer pairs for PRs #454, #452, #451 and issues #389, #429"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: []
regulatory_deadline: null
links:
  - name: "PR #454 — OSF OAuth independent audit"
    url: "https://github.com/humanaios-ui/operations/pull/454"
  - name: "PR #452 — CT-001 constitutional tuning reconstruction"
    url: "https://github.com/humanaios-ui/operations/pull/452"
  - name: "PR #451 — Witness Arena v0.1.1"
    url: "https://github.com/humanaios-ui/operations/pull/451"
  - name: "Issue #389 — blind independent AI reviewer"
    url: "https://github.com/humanaios-ui/operations/issues/389"
  - name: "Issue #429 — Q-WITNESS-COMMONS-ASSURANCE-01 (closed, merged via #431)"
    url: "https://github.com/humanaios-ui/operations/issues/429"
```

---

## Entry-point disclosure (P3, P1)

The coordination request asked for `/empirica-constitution` to be run. That skill is registered
in `SKILLS_MANIFEST.md` at a path on the Admiral's local machine
(`.../plugins/local/empirica/skills/empirica-constitution`), which the session that produced this
candidate cannot reach. **Its text was not read.**

The entry point used instead is the constitutional material that is in-tree and executable:
`constitution.json` v1.0 read through `tools/agents/_shared/constitution_checker.py`, with
`CLAUDE.md`, `GOVERNANCE.md` and `SESSION_RITUALS.md` for authority and ritual.

This is recorded as an omission, not repaired by substitution. If the plugin text carries
obligations absent here, this candidate is incomplete in that respect and should be edited
rather than assumed conformant. Per issue #429 §7, `OMISSION_IS_EVIDENCE_METADATA`.

---

## Temporal posture (Q-TEMPORAL-DISSOLUTION-01)

The resource-state gate is `GATING` in `PRIORITY_QUEUE.md`. This candidate introduces no internal
work deadline and no calendar-driven priority. Every timestamp in `mesh/` is `OBSERVATIONAL` or
`HISTORICAL_RECORD`; the schema closes `provenance.temporal_class` to the four permitted classes,
and `mesh/conformance/validate_mesh.py` negative case 7 demonstrates that
`INTERNAL_WORK_DEADLINE` is refused.

The `window` and resolver dates quoted from `ledgers/mesh_pins_090826.json` are quoted as that
ledger's existing terms, not adopted as new controls.

---

## Decisions requested of Z2

| ref | question | Z1 position |
|:--|:--|:--|
| **D3** | Is `mesh/` inside `operations` an admissible coordination locus, or must local mesh work live in `empirica-practice-mesh`? | Admissible **as an observation record only**. Z2 rules. |
| **D4** | Should `mesh/practice_local.schema.json` be promoted to `schemas/`, and `mesh/conformance/*.py` to `tools/`? | **Not yet.** A canonical path implies ratified standing this layer does not have, and would place unratified scaffolding under blocking CI gates. Revisit after D3. |
| **D1** *(pre-existing)* | Where does an AMBIGUOUS practice resolve? | Unresolved. This candidate widens the choice from two targets to three and resolves nothing. |

D2 (`UNRESOLVABLE` practices) is out of scope: `empirica-epistemology` and
`empirica-quality-assurance` are not in this drop.

---

## What this candidate does not do

- Does not write `REGISTERED.md`. That file is Z2 sole write.
- Does not append to `ledgers/NF_LEDGER.jsonl`. No token is resolved, struck, or voided.
- Does not change any zone, cap, executor assignment, or constant.
- Does not claim conformance to all 22 principles. `constitution_checker.py` implements a subset;
  a clean run is evidence about the implemented checks and silence about the rest.
- Does not constitute a blind review of the five linked artifacts. It was assembled by a single
  reader with all five visible — the condition PR #452 Pass B is specified to avoid.
