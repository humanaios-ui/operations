# Local Mesh Coordination Charter v0.1

**Candidate ID:** Q-MESH-LOCAL-COORDINATION-01
**Status:** Z1 candidate — **not ratified**. No Z2 hash. No executable authority.
**Authored by:** Z1 (Claude) under the Admiral's direction
**Entry point:** `constitution.json` v1.0 (22 principles), read through
`tools/agents/_shared/constitution_checker.py`
**Pin (HISTORICAL_RECORD):** `operations` @ `44347b79b1d6351bd10bbb5fb6c45b9ead6bd42e`

---

## 0. Entry-point note (P3 — no unverified claims)

The `/empirica-constitution` skill is registered in `SKILLS_MANIFEST.md` at a path on the
Admiral's local machine (`.../plugins/local/empirica/skills/empirica-constitution`). That path
is not reachable from the session that produced this charter, so its text was **not read**.

This charter is therefore grounded in the constitutional material that is **in-tree and
readable**:

| source | role here |
|:--|:--|
| `constitution.json` | 22 principles with named `runtime_check` hooks — the operative entry point |
| `tools/agents/_shared/constitution_checker.py` | the executable gate that consumes them |
| `CLAUDE.md` | authority map (Z1/Z2/Z3), decision routing, callout triggers |
| `GOVERNANCE.md`, `SESSION_RITUALS.md` | session open/close obligations |
| `seeds/seed-constitution-v0.1.md` | provisional calibration reference only — PR #452 Pass A records that it is **not binding authority** |

**Omission is recorded as omission, not resolved by substitution.** If the plugin text states
obligations absent here, this charter is incomplete in that respect and should be amended, not
assumed conformant.

---

## 1. Scope

A **local practice** is a coordination record held in `operations/mesh/practices/<id>/` that
describes what a practice owns, what it declines, what it consumes, and what forecasts stand
against it.

This drop covers three practices, chosen by the Admiral: `humanaios`, `website`, `grok-crossref`.

The Admiral's phrasing "grock-cross-ref" is recorded here as an **alias**. The canonical token
in `ledgers/NF_LEDGER.jsonl` and `ledgers/PRACTICE_RESOLUTION_MAP.md` is `grok-crossref`, and the
canonical form is used in every machine-readable field.

---

## 2. Authority boundary

```
PARTICIPATION_IN_THE_LOCAL_MESH_IS_NOT_AUTHORITY
```

A local practice record:

- **may** describe ownership, interfaces, boundaries, dependencies, and standing forecasts;
- **may** be cited as evidence in a Z1 proposal;
- **may not** grant, widen, or imply Z1 proposal cap, Z2 ratification right, or Z3 execution right;
- **may not** ratify itself, and carries no Z2 hash;
- **may not** be treated as the resolver target for `ledgers/mesh_pins_090826.json` until Z2 rules D1.

Caps remain as published in `ZONE_REGISTRY.md` and `CLAUDE.md`. This charter changes neither.

This mirrors the boundary that issue #429 states as `WITNESS_IS_NOT_THE_AUTHORITY` and that
PR #451 v0.1.1 narrowed after adversarial review ("membrane decisions are observation records,
not a new tier"). The local mesh is an observation record of the same kind.

---

## 3. The resolution problem this layer sits next to

`ledgers/PRACTICE_RESOLUTION_MAP.md` classifies all 15 pinned practices. Two of the three in
this drop are blocked:

| practice | class | why |
|:--|:--|:--|
| `humanaios` | AMBIGUOUS | repo `humanaios` **or** mesh dir — the two targets return different verdicts |
| `website` | AMBIGUOUS | mesh dir vendors a copy of another repo under `operations-repo/` |
| `grok-crossref` | UNAMBIGUOUS | mesh dir; 3 of 6 tokens already resolved |

The map states the cost of guessing: "picking the mesh dir would score 16 tokens NO on a
technicality," and resolving under an unruled target "would be picking a target to get a verdict,
which is the manufactured-calibration failure the resolution discipline exists to prevent."

**This charter does not resolve D1.** A local record is a *third* candidate target, which makes
the ambiguity wider, not narrower, until Z2 rules. That widening is stated here rather than
left for a reader to discover.

**No NF_LEDGER.jsonl row is written by this work.** The ledger is append-only and a wrong
resolution is correctable only by a DISPUTE event.

---

## 4. Constitution bindings

Each principle below is bound to an obligation this layer actually carries. Principles with no
obligation here are omitted rather than listed for appearance.

| principle | name | obligation on a local practice record |
|:--|:--|:--|
| P1 | Admit the gap | A record that overstates its practice files an IC rather than editing history |
| P2 | Restored state exists | `REGISTERED.md` remains canonical; this layer never writes it |
| P3 | No unverified claims | Every field traces to a readable in-tree source or is marked `UNKNOWN` |
| P5 | Primary purpose filter | A practice states which of {data, hypothesis, revenue} its work serves |
| P19 | Detection beats compliance | The schema is machine-checkable; conformance is run, not asserted, and every control is demonstrated to refuse |
| P-T2 | Zone discipline governs | Zone and cap are read from `ZONE_REGISTRY.md`, never set here |
| P-T10 | TRL framing | Records say "specified", not "operational", absent evidence of operation |
| P-HUMILITY | Overconfidence flag | No confidence above 0.95 without counter-evidence |
| P-TRANSPARENCY | Decision transparency | Each record names its rationale and its zone |
| P-GRAPH | The graph is the artifact | Each record carries at least one edge (see `CROSS_REFERENCE_REGISTER.md`) |
| P-ARTIFACT-BREADTH | Full artifact spectrum | Unknowns and dead ends are recorded beside findings |
| P-PULL-FIRST | Pull when uncertain | An AMBIGUOUS practice routes to Z2 rather than picking a target |

Conformance evidence: [`conformance/`](./conformance/).

---

## 5. Temporal posture

Q-TEMPORAL-DISSOLUTION-01 is `GATING` in `PRIORITY_QUEUE.md`. This layer introduces **no**
internal work deadline and **no** calendar-driven priority.

Admission is by the ratified predicate:

```text
READY(work) =
  AUTHORITY(work)
  AND DEPENDENCIES(work)
  AND RESOURCES(work)
  AND EVIDENCE(work)
  AND SAFETY(work)
```

Every timestamp in this directory is `OBSERVATIONAL` or `HISTORICAL_RECORD`. The pinned
`window` and resolver dates quoted from `ledgers/mesh_pins_090826.json` are quoted as the
existing ledger's terms, not adopted as new internal controls.

---

## 6. Falsifier

This charter is **FALSE**, and should be narrowed or withdrawn, if any of the following is
observed:

1. A local practice record is cited anywhere as the basis for a cap, ratification, or execution
   right that `ZONE_REGISTRY.md` or `CLAUDE.md` does not already grant.
2. Any row is appended to `ledgers/NF_LEDGER.jsonl` resolving a `humanaios` or `website` token
   against a local `mesh/practices/` read while D1 is unruled.
3. A field in any `practice.yaml` cannot be traced to a readable in-tree source and is not
   marked `UNKNOWN`.
4. `mesh/practice_local.schema.json` validates a record containing a key the schema does not
   declare (the `additionalProperties: false` control fails open), or validates a record whose
   `status` is `RATIFIED` without a 64-hex `authority.z2_ratification`, or one missing `edges`
   or `trl_framing`.
4a. A record is parsed by a loader that accepts duplicate mapping keys. `yaml.safe_load` keeps
   the last of a repeated key, so a duplicated `authority:` block would reach the schema with its
   first copy already discarded — the schema control would hold on a document nobody read.
   Records are parsed with `.doc-control/strict_yaml.py`, and the refusal is demonstrated.
5. The local records and `ledgers/PRACTICE_RESOLUTION_MAP.md` disagree on a practice's
   resolution class, and the disagreement survives one maintenance pass.

Falsifier 4 is the adversarial-hardening carry-over from PR #451 ("schema soft smuggling →
`additionalProperties: false` on core objects"). Falsifier 4a was added after review found that
`additionalProperties: false` is only as good as the parser feeding it — the same class of defect
one layer down.

---

## 7. Maintenance

These records are **derived**, not authored. They go stale when a practice gains content, a
repository is created, the pin spec changes, or Z2 rules D1/D2. Re-derive against a fresh read
and re-pin the sha in each record header before citing one as evidence.

A stale record that reads as current converts a NO into a false negative — the direction that
matters.

---

## 8. Open items routed to Z2

| ref | question | this charter's position |
|:--|:--|:--|
| D1 | Where does an AMBIGUOUS practice resolve? | Unresolved. Local records widen the choice to three targets; Z2 rules. |
| D2 | What happens to an UNRESOLVABLE practice? | Out of scope for this drop (`empirica-epistemology`, `empirica-quality-assurance` not included). |
| D3 *(new)* | Is `mesh/` inside `operations` an admissible coordination locus at all, or must local mesh work live in `empirica-practice-mesh`? | Z1 proposes admissible-as-observation-record-only. Z2 rules. |
| D4 *(new)* | Should `mesh/practice_local.schema.json` be promoted to `schemas/` as a canonical schema? | Z1 proposes **no** until D3 is ruled; a canonical path would imply ratified standing this layer does not have. |
