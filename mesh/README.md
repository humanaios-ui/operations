# `mesh/` — Local Mesh Coordination Layer

**Status:** Z1 candidate — **not ratified**. Nothing in this directory carries Z2 authority.
**Zone:** Z-000 (`operations`)
**Constitutional entry point:** `constitution.json` (22 principles) + `tools/agents/_shared/constitution_checker.py`
**Charter:** [`MESH_LOCAL_CHARTER_V0_1.md`](./MESH_LOCAL_CHARTER_V0_1.md)
**Pinned at derivation:** `operations` @ `44347b79b1d6351bd10bbb5fb6c45b9ead6bd42e` (HISTORICAL_RECORD)

---

## What this is

A **local** coordination surface for a subset of Empirica practices, held inside `operations`
rather than in the remote `humanaios-ui/empirica-practice-mesh` repository.

Practices covered in this first drop:

| practice | zone | resolution class | local record |
|:--|:--|:--|:--|
| `humanaios` | Z-001 | AMBIGUOUS | [`practices/humanaios/`](./practices/humanaios/) |
| `website` | planned (see `PLANNED_REPOS.md`) | AMBIGUOUS | [`practices/website/`](./practices/website/) |
| `grok-crossref` | not zoned | UNAMBIGUOUS | [`practices/grok-crossref/`](./practices/grok-crossref/) |

Classes are read from `ledgers/PRACTICE_RESOLUTION_MAP.md`, not restated independently.

## What this is not

- **Not a resolution target.** Creating a local record does not make it the target the
  `ledgers/mesh_pins_090826.json` resolver reads. That is Z2 decision **D1**, open.
- **Not authority.** A practice record grants no Z1 cap, no Z2 ratification right, no Z3
  execution right. Membership is not authority.
- **Not a replacement** for `humanaios-ui/empirica-practice-mesh`. The remote mesh directories
  remain the scaffold of record until Z2 rules otherwise.
- **Not ratified.** No Z2 hash is attached to any file here.

## Contents

```
mesh/
  README.md                        this file
  MESH_LOCAL_CHARTER_V0_1.md       authority boundary + constitution mapping
  practice_local.schema.json       record schema (additionalProperties: false)
  CROSS_REFERENCE_REGISTER.md      practice → open PR/issue binding
  practices/<id>/practice.yaml     one record per practice
  practices/<id>/README.md         human-readable summary of that record
  conformance/                     evidence from running the constitution checker
```

## Z2 decision requested

Filed as `z1-inbox/2026-09-22/Q-MESH-LOCAL-COORDINATION-01.md`.
