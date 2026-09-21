# GOVERNANCE_FILES.md — Authoritative Registry

> Rendered from `.gov-control/governance-files.yaml` (SSOT) by `.gov-control/render.py`.
> **Do not hand-edit — edit the SSOT.** CI blocks when the two disagree.

**Purpose:** Single source of truth for all governance files, their structure, authority, and location.  
**Updated:** 2026-09-21  
**Authority:** Z2 (Night) — ratifies file definitions, structure changes, ownership  
**Model:** Resource-based (no arbitrary time deadlines; resource_cost & capacity-driven)

**Status is derived, not declared.** Each row's status is computed by stat-ing
the declared path when this file is rendered. There is no `status` field in the
SSOT to fall out of date, and `validate.py` rejects one if it is ever added.

---

## File Registry

### Core Governance (Z2 Writes)

The files Z2 signs. A change to any of these needs a ratification receipt; CI refuses the merge without one.

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **`REGISTERED.md`** | Canonical append-only registry of findings (F), integrity corrections (IC), hypotheses (H), drift classes (D), rulings (R) and governance directives (GD). The index that binds every independent verification stream; entries are superseded by addition, never deleted. (spec: `REGISTRY_SPEC.md`) | Markdown, append-only; per-entry YAML front-matter | Z2 sole write (ratification receipt; Z1 proposes via PR) | Z1 read, Z2 write | ✅ PRESENT |
| **`CLAUDE.md`** | Authority map; Z-roles, escalation paths, decision routing, callout triggers | Markdown | Z2 ratifies changes | Z1 read, Z2 write | ✅ PRESENT |
| **`PRIORITY_QUEUE.md`** | Eligible work ordered by the ratified RBE-OPS constraint allocator. Ranks which candidates get scarce ratification attention. Never ordered by elapsed time — internal calendar deadlines are prohibited by Q-TEMPORAL-DISSOLUTION-01. | Markdown; resource-scored rows | Z2 ratifies allocation constants and cost pins | Z1 read, Z2 ratify | ✅ PRESENT |
| **`ZONE_REGISTRY.md`** | Active repos (31 zones), Z3 executor assignments, per-zone resource caps | Markdown tables | Z2 ratifies zone list, executors, caps | Z1 read, Z2 write | ✅ PRESENT |
| **`MOLT_STATE.md`** | Molt lifecycle state machine (PROPOSED → MEASURING → KEEP/REVERT) and the anti-cascade rules. Tracks the journey; NF_LEDGER holds the outcome. | Markdown state chart + ledger | Z2 ratifies molt transitions | Z1 read, Z2 write | ✅ PRESENT |
| **`FRAMEWORK_MAPPING.md`** | Maps 5 AI engineering concepts → Z-roles, governance files, CI/CD gates | Markdown | Z2 ratification pending (Q-FRAMEWORK-MAPPING-01) | Z1 read | ✅ PRESENT |

### Reference Docs (Z1 Reads; Z2 Ratifies Structure)

Read during the session rituals. These shape how work is done; they do not themselves carry ratified state.

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **`BOOT_PROCESS_MAP.md`** | Maps session rituals (§A open, §B close) onto boot-chain stages and names the halt conditions — including A.1, the REGISTERED.md live-fetch whose failure hard-halts the session (IC-030). | Markdown stages + flowchart | Z2 ratifies design | Z1 read, Z2 write | ✅ PRESENT |
| **`PLANNED_REPOS.md`** | Roadmap (aspirational repos); resource budget per planned zone | Markdown | Z2 ratifies roadmap | Z1 read, Z2 write | ✅ PRESENT |
| **`GOVERNANCE_FILES.md`** | This file; the rendered registry of all governance files | Markdown — rendered from .gov-control/governance-files.yaml | Z2 ratifies definitions | Z1 read, Z2 write | ✅ PRESENT |
| **`CANDIDATE_BLOCK_TEMPLATE.md`** | Template for Z1 proposals; falsifier, resource_cost, impact | Markdown + YAML example | Z2 ratifies template | Z1 read | ✅ PRESENT |
| **`SESSION_RITUALS.md`** | The §A open / §B close protocol, substrate-agnostic. Canonical parser-tag specification: where another operations file restates a parser-critical tag, this file wins. | Markdown | Z2 ratifies amendments (signed rulings) | Z1 read, Z2 write | ✅ PRESENT |
| **`REGISTRY_SPEC.md`** | Ratified specification of the findings registry itself — canonical store, entry classes, entry schema, write rules, the IC-030 read rule, and the derived-views doctrine. Governs what counts as a registry entry. | Markdown | Z2 ratified 2026-08-04 | Z1 read, Z2 write | ✅ PRESENT |

### System State (Code Writes; Z1/Z2 Read)

Written by instruments, not by hand. These carry the measurements that registry entries cite.

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **`ledgers/NF_LEDGER.jsonl`** | Append-only measurement ledger; every VERDICT/CYCLE/MEASURE event, hash-chained. §B.6 receipt reconciliation walks session claims against this file. (spec: `ledgers/NF_EVENT_SCHEMA.md`) | JSONL | Code append | Code write, all read | ✅ PRESENT |
| **`ledgers/NF_EVENT_SCHEMA.md`** | The event format actually in force (narrowed Q-NF-SCHEMA-01 scope) | Markdown | Z2 ratifies schema changes | Z1 read, Z2 write | ✅ PRESENT |
| **`NF_LEDGER_SCHEMA_v1.md`** | Forward design for the unified single-record ledger. Not the format in force — see ledgers/NF_EVENT_SCHEMA.md for what instruments write today. | Markdown | Z2 ratifies schema changes | Z1 read, Z2 write | ✅ PRESENT |
| **`system_graph.json`** | Dependency topology; zones as nodes, inter-repo edges | JSON graph | Z2 (via blueprint); regenerated by system_graph_generator.py | Code write, all read | ✅ PRESENT |
| **`behavior_spec.json`** | Z3 agent capability caps; tool limits, rate budgets, resource allocations | JSON | Z2 ratifies | Z1 read, Z2 write | ✅ PRESENT |
| **`molt_ledger.jsonl`** | Molt measurement outcomes; one line per completed molt | JSONL | Code append | Code write, all read | ✅ PRESENT |

### Derived Views (Rendered — never hand-edited)

Each is a VIEW of a machine-readable SSOT, regenerated by a renderer and held in sync by a blocking CI check. Editing one by hand is the drift this section exists to prevent — the renderer will overwrite it and `--check` will fail the merge first.

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **`CONTROLLED_DOCUMENTS.md`** | Controlled-document index — companion to REGISTERED.md (documents, not findings) (SSOT: `document-registry.yaml`; via `.doc-control/render.py`) | Markdown — rendered | Z2 ratifies registry contents | All read | ✅ PRESENT |
| **`Z1_INBOX_INDEX.md`** | Conversion index — which candidates await Z2, which are ratified, what each asks (SSOT: `z1-inbox/INDEX.yaml`; via `.z1-control/render.py`) | Markdown — rendered | Z2 signs ratifications (.z1-control/ratify.py) | Z1 write, Z2 read | ✅ PRESENT |
| **`TOOLS_MANIFEST.md`** | Tool inventory by category; surfaces tools awaiting Z2 ratification (SSOT: `tools-manifest.yaml`; via `.tool-control/render.py`) | Markdown — rendered | Z2 ratifies tool classifications | All read | ✅ PRESENT |
| **`REGISTERED_FAILURE_MODES.md`** | The registry turned on itself — registry failure modes (RFM-nn) mapped to standing orders and industrial failure modes. Every count is produced by the scanner and re-verified by `--verify-doc`, which fails if the map drifts from the registry. (SSOT: `REGISTERED.md`; via `tools/registered_failure_mode_scan_v0_1.py`) | Markdown — tool-verified | Z2 ratification pending | Z1 read | ✅ PRESENT |

### Proposal Staging (Z1 Drafts; Z2 Ratifies)

Where a candidate lives before it is registry-final. Per REGISTRY_SPEC.md read rules, anything here is labelled reconciliation-pending and is never presented as ratified.

| File | Purpose | Format | Authority | R/W | Status |
|:-----|:--------|:-------|:----------|:----|:-------|
| **`z1-inbox/`** | Candidate blocks and records, filed by date, before REGISTERED.md submission | Markdown, one file per candidate | Z1 author | Z1 write, Z2 read | ✅ PRESENT |
| **`z1-inbox/INDEX.yaml`** | SSOT for the inbox; declares which files are candidates (ask Z2 for a decision) and which are records (ask nothing). decision_due is derived from the CLAUDE.md window, not hand-set. | YAML | Z1 author; .z1-control/validate.py enforces | Z1 write, Z2 read | ✅ PRESENT |
| **`registry-candidates/`** | Entries staged in registry-ready form awaiting the operator's append. Z1 prepares; Z2/Z3 assigns sequential numbers and commits — no self-numbering (G-4 / IC-030). | Markdown | Z1 stages, Z2 appends | Z1 write, Z2 append | ✅ PRESENT |

---

## File Dependencies & Boot Order

**§A (Session Open) — read in this order:**

A.1. **`REGISTERED.md`** — Live-fetch at HEAD and pin SHA (IC-030). HALT if the fetch fails — no valid registry.
A.2. **`ZONE_REGISTRY.md`** — Verify this repo is an active zone; confirm proposal cap
A.3. **`REGISTERED.md`** — Read at the pinned SHA; load live entries
A.4. **`PRIORITY_QUEUE.md`** — Load eligible work, allocator-ordered
A.5. **`MOLT_STATE.md`** — Load open molts; check anti-cascade consistency
A.6. **`BOOT_PROCESS_MAP.md`** — Verify ritual steps and halt conditions

**Note:** CLAUDE.md authority context is assumed established before §A starts.
Boot order takes precedence over logical authority hierarchy; resource-based
gates enforce both.

**§B (Session Close) — write/emit in this order:**

B.6. **`ledgers/NF_LEDGER.jsonl`** — Walk every session claim against the ledger (receipt reconciliation)
B.6b. **`ledgers/NF_LEDGER.jsonl`** — Emit receipt (claim → matched ledger entry); report RECEIPT-GAP for any claim without one
B.7. **`z1-inbox/`** — Harvest F/IC/H candidates into z1-inbox/<date>/HANDOFF.md
B.8. **`PRIORITY_QUEUE.md`** — Z2 signs the handoff; ratified candidates move into the queue

---

## Authorization Model (Resource-Based)

All Z2 writes require:

1. Ratification receipt — date + form (in-session \| PR \| ruling id) + scope note
2. Resource cost estimate — the candidate states what it will consume
3. Impact prediction — scored by resource_impact, never by deadline
4. Falsifier — required on hypotheses; tested at measurement time

**No time-based gates.** Only resource-capacity and regulatory compliance.

---

## Status Symbols

- ✅ PRESENT — path resolves at render time
- 🔴 MISSING — declared here, absent from the tree. `validate.py` treats this as an
  ERROR and blocks the merge: either the file lands, or its row leaves the SSOT.

There is no 🟡 state. A file is in the tree or it is not, and the renderer looks
rather than asking. The old symbol set carried NEW and STRUCTURED, which are
claims about intent rather than observations, and intent is what went stale.
