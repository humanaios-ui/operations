# HumanAIOS Program Graph Mapping
## Graphs as a Project-Management Layer for Programs → INTENT-OS → Tokenized Utility

**Source:** Z1 synthesis of existing repository precedent (not an external framework — see Part 1)
**Mapping Date:** 2026-10-02
**Authority:** Z2 (Night) ratification pending
**Status:** Z1 candidate for REGISTERED.md — Layer 5 of the concept-to-code stack
**Code:** [`program_graph.py`](./program_graph.py) (stdlib only) · standing check: `python3 program_graph.py --smoke-test`

---

## Executive Summary

This repository already runs six graph-shaped structures. None of them spans repositories, and only one — the Resource/RBE-OPS Economy — carries cost at all, and only at the individual work-order level, never aggregated across an initiative. That is the actual gap — not "we need graphs," which we have in abundance, and not "we need cost accounting," which already exists and is ratified, but "we need the layer that aggregates work *and* its already-tracked cost across the 31-repo enterprise, at the granularity of a named initiative rather than one PR at a time." *(Correction, 2026-10-02, via Copilot PR review on #671: the original wording here said "none of them carries cost," which directly contradicted Part 1 §6 below — fixed.)*

| Layer | Status today | What it answers | Primary file(s) |
|:---|:---|:---|:---|
| System Graph | Built | What components/processes exist, and are they OPERATED? | `system_graph.json` |
| **Intent Graph** | **Built, proposed (`Q-INTENT-GRAPH-01`), not yet ratified** | **What do we believe, why, and does it still ground out?** | `INTENT_GRAPH.yaml`, `tools/intent_graph_v1_0.py` |
| Session Graph | Informal convention | What unit of engineering work happened, and what did it touch? | Issue titles `[Session Graph] ...`, `z1-inbox/*/HANDOFF.md` |
| Repository / Object Coordinator | Built | Where does this PR/issue stand procedurally right now? | `REPOSITORY_COORDINATOR_POLICY.json`, `repository_coordinator_v0_1.py` |
| Attention Router | Proposed, not built | Who must act next, on what, clustered by root cause? | Issue #640 (spec only) |
| Resource / RBE-OPS Economy | Ratified (`b6b8233d...`, Night, 2026-09-13), partially wired | What did this cost, in which non-commensurable unit? | `RESOURCE_UNITS.yaml`, `PRIORITY_QUEUE.md`, `RESOURCE_LEDGER.jsonl` |
| **Programs (this proposal)** | **Proposed** | **Which multi-repo initiative is this in service of, what Objective does it realize, and what is its cost/benefit density?** | **This document + `program_graph.py`** |

**Reading rule:** every row in Parts 1–2 below ends in a real file this session verified exists and, where claimed ratified, a real hash. A row that cites a mechanism which does not actually run, or that overclaims status relative to what its own source document says, is not a mapping and does not belong here.

Read after `AUTHORIZATION_EVIDENCE_MAPPING.md` (Layer 4). This layer does not propose new infrastructure for measuring AI cost or for grounding claims — `Z1-ktok` is already a REGISTERED, ratified resource unit with a working instrument, and `INTENT_GRAPH.yaml` is already a working (if unratified) typed graph with a real validator. It proposes the single missing node type — **Program** — that connects them.

---

## Part 1 — The graphs that already exist (grounding, not invention)

Unlike Layers 1–4, this layer does not map an external framework onto HumanAIOS. It maps HumanAIOS onto *itself* — naming six structures this repository already runs, most of them by convention or as an unratified candidate rather than by finished design.

### 1. System Graph — built
`system_graph.json` (v0.2) is a populated node graph of the governance machinery's own components — `Q` (Priority Queue), `FS` (Findings Scan), `OM` (Operator Model), and others — each carrying `type`, `status` (`OPERATED`/`LAID`), `zone`, `implementation`, `tests`, `phase`. The *capability* graph: what exists and whether it runs. **Stops at:** one repository.

### 2. Intent Graph — built, proposed, not yet ratified
`INTENT_GRAPH.yaml` (candidate `Q-INTENT-GRAPH-01`, status `PROPOSED — not effective until Z2 ratification hash`, rendered by `tools/intent_graph_v1_0.py` into `INTENT_GRAPH.md`) is a real, working, validated typed graph with six node kinds — **Vision → Mission → Principle → Objective → Gate → Instrument** — connected by typed edges (`realizes`, `grounds`, `enforces`, `conflicts_with`, `measures`). It is not aspirational prose: its validator (`python3 tools/intent_graph_v1_0.py check`) runs today, confirms every node resolves to a real path in the tree, every Objective reaches the Vision, and reports 7 live warnings including unimplemented gates and un-instrumented objectives. It also tracks five *live contradictions* between artifacts as first-class graph edges (e.g. `O-IDENTITY-ANCHOR x--x V-HAIOS`, citing a ratified TRL correction in `OPS_ROADMAP_V1.2.md` that was never propagated to `SEED.md`) — a genuinely rigorous piece of infrastructure.

Its ten current Objectives — `O-MOLT-CYCLE`, `O-REGISTRY`, `O-QUEUE`, `O-TEMPORAL-GATE`, `O-WITNESS`, `O-DECISION-ROUTING`, `O-DOC-CONTROL`, `O-IDENTITY-ANCHOR`, `O-CORPUS-INTEGRITY`, `O-INTENT-GRAPH` — are standing structural commitments ("Rank eligible work by impact...", "Human-machine decision attribution...") that each `realizes` one of three Missions. **Stops exactly where this proposal picks up:** an Objective is timeless and does not carry cost, start date, or a list of in-flight PRs. Nothing today connects "we are committed to `O-WITNESS`" to "issues #620–624 and PRs #606/#630 are the current work advancing it, at this cost, this far along."

### 3. Session Graph — informal convention
Issues #619, #622, #624, #625, #629, #640, #665 and others carry a `[Session Graph]` title prefix — a real, load-bearing convention marking an issue as a bounded unit of engineering work, but a string in a title, not a queryable structure. `list_issue_fields` for this repo returns an empty array: no custom field backs this convention today.

### 4. Repository / Object Coordinator — built
`REPOSITORY_COORDINATOR_POLICY.json` / `repository_coordinator_v0_1.py` classify every PR into `ACTIVE | ADMITTED_TO_EVALUATION | CONTROL_PLANE | ADMISSION_REVIEW | WORKBENCH | MAINTENANCE | CAPACITY_CONTENTION` — *where does this work object belong*, computed live. **Stops at:** individual objects; no notion of a multi-issue initiative.

### 5. Attention Router — proposed, not built
Issue #640 is a complete, rigorous spec (typed flag schema, root-cause clustering, head-bound lifecycle, ten falsifiers) for a routing axis orthogonal to the Coordinator's lanes: *who must act next*. Its own diagram already names the shape this proposal extends — see Part 3.

### 6. Resource / RBE-OPS Economy — ratified, partially wired
`RESOURCE_UNITS.yaml` is **ratified** (`status: RATIFIED`, `ratification_hash: b6b8233dd06400f565e5e21286cc0fec65a71472adfa1ebb98045f2dfaeff2a2`, ratified by Night, 2026-09-13T17:33:00Z) and registers 14 non-commensurable units across 7 dimensions. `Z1-ktok` ("Z1 proposer thousand-tokens") is one of them: "one thousand model tokens spent by a Z1 proposer," capped at 100/session via `behavior_spec.json`, measured by `agent_caps_runtime.py`'s `CapEnforcer`, recorded as `SPEND` rows in `RESOURCE_LEDGER.jsonl`. `PRIORITY_QUEUE.md` runs a real allocator on top of it: `density = benefit / cost[RAT-min]` for costed rows; `UNPRICED_ROW_POLICY = REFUSED_TO_START` for rows with no price at all. **Stops at:** the individual work-order level — nothing rolls `SPEND` rows up by initiative.

Six real structures. Two of them (System Graph, Intent Graph) are single-repo and timeless; two (Session Graph, Coordinator) are single-repo and per-object; one (Attention Router) is a spec with no code; one (RBE-OPS) is ratified and priced but ungrouped. The missing layer sits across all six.

---

## Part 2 — Programs: the node type that connects Objective to work

**Definition.** A **Program** is a new node type for `INTENT_GRAPH.yaml`'s own schema, sitting between `OBJECTIVE` and raw work items: a named, multi-repo, time-bound initiative that `realizes` one or more existing Objectives, groups a set of System-Graph components, Session-Graph issues, and Coordinator-tracked PRs, and carries a resource cost vector. It is proposed as an *extension* of the existing Intent Graph schema and its real validator/renderer — not a new parallel tool for the structural half of the problem. (`program_graph.py`, Part 6, is new, but it is new for the arithmetic — cost/benefit/density — not for grounding or contradiction-checking, which `tools/intent_graph_v1_0.py` already does well.)

Programs are not invented for this document — they already exist as *implicit* clusters in this repository's own issue history, each one already realizing an existing Objective whether or not anyone has said so in a machine-checkable way:

| Program | Constituent nodes (this repo alone) | Realizes (existing Objective) | Status |
|:---|:---|:---|:---|
| **Custody & Provenance Chain** | Issues #620, #621, #622, #624; PRs #623 (merged), #606 (open), #630 (open) | `O-WITNESS` ("Human-machine decision attribution") | In progress |
| **INTENT-OS Attention Control Plane** | Issues #640, #641, #665 | **None of the 10 existing Objectives name this.** A real gap the graph surfaces, not papered over — see below. | Spec-only, zero PRs |
| **HumanAIOS Resource System** | Issue #588, #599, #611; merged Resource Miner PR #500 | `O-QUEUE` (resource-based work admission) — partial fit; `O-QUEUE` is about *ranking* work, this Program is about *managing acquired resources*, which is adjacent but not identical | Anchor issue open, scaffold not started |
| **Concept-to-Code Stack** | `FRAMEWORK_MAPPING.md` → `BOOT_PROCESS_MAP.md` → `FIVE_RINGS_MAPPING.md` → `AUTHORIZATION_EVIDENCE_MAPPING.md` → **this document** | `O-INTENT-GRAPH` ("Shared intent substrate... machine-checkable rather than re-derived by reading") | 4 layers ratified/proposed; this is Layer 5 |
| **Knowledge/Substrate Graphs** | Repository graph (#593/#629/#630), Machine Substrate Graph (#596/#653), Calibration Evidence Graph (#595/#594); graph capture lint (#651, `tools/graph_capture_lint_v1_0.py`); **external source, proposed 2026-10-04 (Z1 proposal pending Z2 ratification Q-PROGRAM-GRAPH-MAPPING-01):** the Google Drive "HumanAIOS Knowledge Graph" folder `1RHGZ_W8utqEcZim0Wnw2K5Wt1A2v6ug1` (see *Proposed external sources* below) | No existing Objective; closest is `O-CORPUS-INTEGRITY` but that's about one specific corpus, not graph infrastructure generally | 3 sibling schemas, **no shared node/edge primitive between them**; one external mirror with a one-way sync rule |

**Proposed external sources (Knowledge/Substrate Graphs Program, pending Z2 ratification Q-PROGRAM-GRAPH-MAPPING-01).** Proposed 2026-10-04 as a *source*, not a canonical graph; promotion of any file in it to canonical is a Z2 decision. Ratification will move these to "Registered."

| Drive object | Drive id | Role | Sync rule |
|:---|:---|:---|:---|
| "HumanAIOS Knowledge Graph" folder | `1RHGZ_W8utqEcZim0Wnw2K5Wt1A2v6ug1` | Mirror and intake area for graph material assembled from chat exports | Source only. Nothing in it is read as authority by any repo tool. |
| `system_graph.rendered.md` | `1c1ImGD9-YItzdbJRKtY61W7ilewaqQVL` (Documentation subfolder `1Xd70PMIcOicKaZ009yx3SUYP0TtuBApm`) | Rendered copy of `system_graph.json` | **GitHub renders to Drive, never the reverse.** Produced by `tools/system_graph_render_v1_0.py`; its header carries the source sha256 and the rendering commit. The earlier hand-written `system_graph_v0.2.md` (19 nodes, 44 edges against the source's 22 and 53) is marked superseded and kept for the record. |
| `entity_schema_v1.1.json` | `1HpUUUqEkBs7qxcQXlHTBiNNTwJ_8_7f3` (Schema & Templates subfolder `1wUq0gbFD_wNtaikId8yK_3VNF4BNjPNj`; v1.0 kept as `1SQtYxobANz7UbEZA1hsJewINT4cx9q_R`) | Entity/relationship schema for export-derived entities | Extends v1.0 with `as_of`, a `source` locator per entity, an evidence object aligned with `schemas/system_stance_v1.schema.json` (relation, kind, locator, observation), a retraction channel (`SUPERSEDES`, status `RETRACTED`) and the shared advisory constants. These are the fields `graph_capture_lint` P1–P3 require. |
| `INTEGRATED_SSOT.json` | not yet created (verified absent 2026-10-04) | Planned union of Claude export + Grok files + system graph | Must pass `python3 tools/graph_capture_lint_v1_0.py <file>` with no P1–P3 failure before it is cited anywhere in this repository; no baseline entry may be created for it. Until then it is a Drive-side working file. |

Two findings fall directly out of doing this exercise, neither assumed going in:

1. **A missing Objective, not just a missing Program.** The INTENT-OS Attention Control Plane Program has no existing Objective to realize. That is itself exactly the kind of gap `INTENT_GRAPH.yaml`'s validator is built to surface (it already reports 7 non-blocking warnings of this shape). This document does not resolve that gap — adding `O-ATTENTION-ROUTING` as an eleventh Objective is a Z2 call, listed in Action Items below, not decided here.
2. **Three graphs, one week, zero shared primitive.** `system_graph.json` uses `{id, type, status, zone}`; the Machine Substrate Graph uses `{nodes, edges, omissions}` with a closed observation-state vocabulary; the Calibration Evidence Graph is RDF/Turtle validated against a formal PROV-O/SHACL ontology — a different graph technology altogether. A Program node that tracks "the Knowledge/Substrate Graphs Program" as a single entity would have surfaced this immediately. A single-repo, single-PR view structurally cannot.

**What a Program node carries**, as a proposed addition to `INTENT_GRAPH.yaml`'s actual schema — verified directly against `tools/intent_graph_v1_0.py` rather than assumed, after the first draft of this section got the field names wrong (see note below the example):

```yaml
# In the file's `nodes:` list:
- id: PROGRAM-CUSTODY-PROVENANCE-01
  type: program                       # new node type, alongside vision/mission/principle/objective/gate/instrument
  name: "Custody & Provenance Chain"
  statement: "Attribute decisions and actions to their true origin — human, AI, or
    shared-account-unknown — without treating GitHub account identity as proof of
    either, so Z3 executor onboarding does not collapse authority."
  status: LIVE                        # one of NODE_STATUSES: LIVE | PROPOSED | CONFLICTED | CITED_NOT_IMPLEMENTED
  persistence: RATIFIED               # default; a Program is tracked until closed, not ephemeral session state
  source: "PROGRAM_GRAPH_MAPPING.md"  # this document, at its actual repo-root path
  constituent_nodes:
    - {repo: operations, type: issue, ref: 620}
    - {repo: operations, type: issue, ref: 621}
    - {repo: operations, type: pr, ref: 623, state: merged}
    - {repo: operations, type: pr, ref: 606, state: open}
    - {repo: operations, type: pr, ref: 630, state: open}

# In the file's separate, top-level `edges:` list — not nested inside the node:
- {from: PROGRAM-CUSTODY-PROVENANCE-01, to: O-WITNESS, rel: realizes}
```

*Correction (2026-10-02, via Copilot PR review on #671): the first draft of this example used `kind:` (the real field, confirmed at `tools/intent_graph_v1_0.py:303`, is `type:`), an inline `realizes: [...]` list inside the node (edges are a separate top-level list keyed by `from`/`to`/`rel`, confirmed at lines 353-362), a lowercase, invented `state: in_progress` (the real enum, `NODE_STATUSES` at line 116, is `{LIVE, PROPOSED, CONFLICTED, CITED_NOT_IMPLEMENTED}` — none of which means "done"; see open question below), and a `source:` path (`z1-inbox/2026-10-02/...`) that doesn't exist — this document lives at the repo root. All four are fixed above, verified against the cited lines rather than re-guessed.*

**Schema changes this actually requires** (not yet made — proposed here, decided in Action Items):

1. `INTENT_GRAPH.yaml`'s own `node_types:` vocabulary block (line 79) gets one new entry, in the same style as its five existing ones: `program: A named, time-bound, multi-repo initiative that realizes one or more objectives and carries tracked resource cost.`
2. `tools/intent_graph_v1_0.py`'s `KNOWN_NODE_TYPES` (line 319) gets `"program"` added to the set.
3. `tools/intent_graph_v1_0.py`'s `EDGE_DOMAINS["realizes"]` (line 128) is currently `({"objective", "mission"}, {"mission", "vision"})` — it does not permit `objective` as a target at all today, only `mission`/`vision`. It needs to become `({"objective", "mission", "program"}, {"mission", "vision", "objective"})` so `program → objective` validates, while the existing `objective → mission` and `mission → vision` edges keep working unchanged.

**Open question this surfaces, not resolved here:** `NODE_STATUSES` has no value for "a Program finished successfully and is now closed." Objectives never need one — they're standing commitments that persist until superseded, not initiatives that complete. A Program is explicitly time-bound, so this is a real, new case, not an oversight to route around quietly. Whether that's a fifth status value (e.g. `COMPLETE`) or a `persistence` transition out of `RATIFIED` is a Z2 design call, listed in Action Items.

A Program with no `realizes` edge at all is not silently allowed under this design — the validator already flags objectives with no instrument the same way (W2 warnings); a Program should get the equivalent treatment, specified at implementation time, not invented here.

`cost_to_date` and `benefit_to_date` are deliberately *not* part of the node shape above — they live in `program_graph.py`'s output (Part 4), not in `INTENT_GRAPH.yaml` itself, because `INTENT_GRAPH.yaml`'s own stated job is grounding and contradiction, not arithmetic. Keeping the resource rollup in a separate tool mirrors the existing, working separation between `system_graph.json` (what exists) and `RESOURCE_UNITS.yaml`/`PRIORITY_QUEUE.md` (what it costs) — this document does not collapse that separation, it extends the pattern one level up.

---

## Part 3 — Connecting to INTENT-OS

Issue #640's two orthogonal axes — **Object Lane** (where work stands) and **Attention Route** (who acts next) — state explicitly "these axes must never be collapsed." Program is a third, equally orthogonal axis:

```
                                REPOSITORY GRAPH
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
         OBJECT COORDINATOR    ATTENTION ROUTER       PROGRAM GRAPH   ← this proposal
                │                     │                     │
         where it belongs      who acts next         which initiative,
                │                     │               realizing which
                │                     │               Objective, at what cost
                └─────────────────────┼─────────────────────┘
                                      │
                                ATTENTION GRAPH
                                      │
                                 INTENT-OS UI
```

Concretely, this adds one line to #640's own worked example, free of charge once issue #625 (which PR #627 implements) carries a `program_id`:

> PR #627 · ROOT CAUSE: Legacy implementation transplanted onto current control plane · Route: `AGENT_ACTIONABLE` · Human required: NO · **Program: none assigned — untagged work**

*Untagged* is informative on its own — it lets Z2 ask a question neither the Coordinator nor the Router can answer today: how much open work is in service of no named initiative, realizing no Objective, at all? This composes with, and does not replace, #640's existing integration points (`repository_coordinator_v0_1.py` lanes, `intent-os-refresh.yml`'s `MECHANICAL`/`NEEDS-HUMAN` distinction, the T0–T7 harness tiers, custody receipts from #620–#624). No merge or implementation authority is implied, consistent with every prior layer in this stack and with #640's own closing line.

---

## Part 4 — Drilling down to tokenized utility

"Tokenized" here means exactly what `RESOURCE_UNITS.yaml` already means by it, applied one level up — **not** a cryptocurrency, **not** a single fungible score. This matters precisely because `RESOURCE_UNITS.yaml` is ratified (hash `b6b8233d...`) on a principle `INTENT_GRAPH.yaml` names explicitly as `P-NON-COMMENSURABLE`: *"Resource cost is a vector of registered natural units. No scalar effort unit, no numeraire, no cross-dimension conversion."* The file's own header is blunter: *"units in different dimensions DO NOT convert. There is no numeraire. The only legal exchange rate is a PRICE event measured at a named constraint, over a named window, with n ≥ shadow_price_min_n observations and a source. Anything else is refused by the ledger."*

This document does not attempt that conversion, does not invent a shortcut around it, and treats both constraints as binding:

1. **Every cost figure in this proposal stays a vector.** `{Z1-ktok: 340, Z3-hr: 2, CI-min: 85}` is never summed into one number. If Z2 ever wants a blended cross-unit Program score, that requires the same `PRICE event` mechanism `RESOURCE_UNITS.yaml` already defines — paired observations, a named constraint, a minimum sample size — not a convenience formula invented by this document.
2. **`UNPRICED_ROW_POLICY = REFUSED_TO_START` governs individual `PRIORITY_QUEUE.md` rows, not Programs.** A Program's own aggregate cost showing `UNMEASURED` (because no Program mapping exists yet for its work orders) is a reporting gap to close, not a bypass of admission discipline. No individual work item skips pricing or starts unpriced because it is tagged to a Program — every constituent issue/PR still clears `O-QUEUE`'s existing Band A/B/UNPRICED gate exactly as today. Programs aggregate *after* pricing, never instead of it.

**The mechanism, respecting both constraints — and a third:** `RESOURCE_LEDGER.jsonl` is append-only and hash-chained; `docs/RESOURCE_UNITS.md` states plainly that "any edited prior line" breaks `verify`. A `program_id` field cannot be retrofitted onto *existing* `SPEND` rows, and the real `SPEND` event shape (`tools/resource_ledger_v0_1.py`) has no generic tag field at all — it carries `{type, at, by, order_id, unit, qty, source, obligation_class}`, nothing more. *(Correction, 2026-10-02, via Copilot PR review on #671: the original wording here proposed tagging existing ledger rows in place — not possible without breaking chain verification. Fixed below.)*

1. A new, separate, append-only mapping file (e.g. `program_orders.jsonl`) records `{order_id, program_id, assigned_at, assigned_by}` rows — it maps work orders to Programs without touching `RESOURCE_LEDGER.jsonl`'s own rows at all, historical or future. Assigning (or reassigning) an order to a Program is itself just a new line appended to *this* file, never an edit to the ledger.
2. `program_graph.py` reads `RESOURCE_LEDGER.jsonl` `SPEND` rows (keyed by `order_id`, quantity in `qty`) and joins them against the mapping file to attribute cost per Program — a read-only join, not a ledger mutation.
3. Sums are kept by `program_id`, per unit, **as a vector, never collapsed**: `{Z1-ktok: 340, Z3-hr: 2, CI-min: 85}`.
4. Benefit is counted exactly as `PRIORITY_QUEUE.md` already counts it — `impact` of ratified work plus impact of work it unblocked — summed per Program instead of per row.
5. Density is computed per unit, using `PRIORITY_QUEUE.md`'s own existing Band A/B logic unchanged, one level up: an explicit zero cost ranks by raw benefit (Band A — no density computed, matching `cost[RAT-min] == 0` today); a positive cost computes `density[unit] = benefit / cost[unit]` (Band B); no cost recorded for that unit at all is `UNMEASURED`, distinct from both — mirroring `priority_queue_engine.py`'s own documented rule that "a missing key is 'nobody costed this,' which is not the same claim as 'this costs nothing.'"

**Worked illustration** (numbers below are illustrative placeholders for the *shape* of the output, explicitly not real measurements — real ones require wiring steps 1–2, which this document proposes but does not implement):

| Program | Z1-ktok spent (illustrative) | Ratified capabilities delivered | density (capabilities / 100 Z1-ktok) |
|:---|---:|---:|---:|
| Custody & Provenance Chain | ~340 | 1 (PR #623) | 0.29 (Band B) |
| Concept-to-Code Stack | ~900 | 4 (Layers 1–4 ratified) | 0.44 (Band B) |
| INTENT-OS Attention Control Plane | — | 0 (spec only, no PR yet) | `UNMEASURED` — no `SPEND` rows exist for this Program at all, distinct from a Program that spent zero on purpose |

This is the literal answer to "drilling down to tokenized utility": Z2 gets a `density` column per unit, in the same non-commensurable-vector spirit `RESOURCE_UNITS.yaml` already ratifies, at the granularity that actually matches a continue/stop decision — not "should I merge this PR" (the existing queue already answers that) but "is this multi-week initiative worth the AI-compute it is drawing, relative to the others competing for the same 100-Z1-ktok/session cap."

**Falsifier for this layer:** if Program-level density never changes which initiative Z2 chooses to continue relative to an ungrouped, PR-by-PR view, this layer is a reporting artifact, not a decision instrument, and should be retired — mirroring `Z1-ktok`'s own falsifier exactly ("if sessions routinely complete work orders without the cap binding, Z1-ktok is abundant and does not belong in the allocation problem").

---

## Part 5 — Where this lives across the real GitHub surfaces

| Surface | Role in the Program layer |
|:---|:---|
| **Issues** | Program *constituent nodes* — already true via the `[Session Graph]` convention. Gap: no custom field exists yet (`list_issue_fields` returns empty) to make Program membership queryable instead of inferred from title text. |
| **Pull Requests** | The *edges* that move a Program's nodes from proposed to delivered; additions/deletions/commit counts are a rough proxy for `Z1-ktok` draw until real ledger-tagging (Part 4) lands. |
| **Projects (v2)** | The natural home for a literal Program board — GitHub Projects v2 supports items from multiple repositories under one org-level project, the cross-repo aggregation none of the six existing graphs do today. One Project per Program, with a custom `Z1-ktok spent` field, is buildable with zero new tooling. |
| **Discussions** | The Z1-proposes/Z2-decides deliberation surface for a Program's charter — parallel to how `REGISTERED.md`/`z1-inbox/` do candidate review today, natively threaded, visible without pinning a SHA first. |
| **Agents** | Where Z3 executor assignment — today a markdown table in `ZONE_REGISTRY.md` with most seats `TBD` — could become live instead of a static document awaiting delegation. |
| **Security** | Already a source of Program-relevant signal: this session's dependency PRs (#644, #645, #646) and custody/admission work (#606, #623) both touch this tab; its findings are cost/urgency signal a Program rollup should ingest. |
| **Wiki** | A candidate long-form home for Program *charters*, instead of an ever-growing flat list of root `*_MAPPING.md` files — though `CLAUDE.md`'s CODEOWNERS already route `*.md` to `@humanaios-ui/doc-control`, so moving charter content off-repo is an explicit Z2 call, not a default this document makes. |
| **Enterprise (`humanaios-ai`)** | The actual scope boundary. Programs span repositories by definition; their canonical definition cannot live inside one repo's issue tracker. Until GitHub-native enterprise-level Projects are adopted org-wide, this document proposes `operations` remains the source-of-truth repo for Program *definitions* — consistent with its own description as "class 2/3 source of truth" — with other repos' issues/PRs carrying a `program_id` tag by reference. |

---

## Part 6 — Minimal executable companion

`program_graph.py` implements only the rollup arithmetic from Part 4 — reading `Program` nodes (the `type: program` extension proposed in Part 2), an order-to-program mapping, and `RESOURCE_LEDGER.jsonl` `SPEND` rows, computing cost vectors and density. It does not implement GitHub API wiring, ledger-tagging, or UI, and it does not duplicate `tools/intent_graph_v1_0.py`'s grounding/contradiction validation — that stays exactly where it is.

```python
TOOL_NAME = "program_graph"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"

# density(program, unit) = program.benefit / program.cost[unit]   # PRIORITY_QUEUE.md's formula, one level up
# Never summed across units — P-NON-COMMENSURABLE applies here exactly as it does to O-QUEUE.
# Zero cost with nonzero benefit returns an explicit "undefined" sentinel, never 0 or inf —
# "no cost incurred yet" must not be misread as "infinitely good."
```

`python3 program_graph.py --smoke-test` builds the three illustrative Programs from Part 4's table, confirms `density` matches `benefit/cost` exactly for costed programs, confirms the zero-cost case returns the `undefined` sentinel rather than a divide-by-zero or a silent `0`, and confirms no code path ever sums two different units into one number.

---

## Action Items for Z2 Ratification

- [ ] Ratify this mapping as reference architecture (Layer 5 of the concept-to-code stack)
- [ ] Decide: add `type: program` as a new node type to `INTENT_GRAPH.yaml`'s schema — concretely, the `node_types:` vocabulary entry, `KNOWN_NODE_TYPES`, and the `EDGE_DOMAINS["realizes"]` extension specified in Part 2 — vs. a fully separate file
- [ ] Decide: the open status-vocabulary question from Part 2 (does a completed Program need a new `NODE_STATUSES` value, or a `persistence` transition?)
- [ ] Decide: `program_orders.jsonl` (the append-only order-to-program mapping proposed in Part 4) as a new file, including who may append to it
- [ ] Decide: should `O-ATTENTION-ROUTING` be added as an eleventh Objective, so the INTENT-OS Attention Control Plane Program (issue #640) has something to `realize`? Today it has none — a real gap this document surfaces but does not resolve
- [ ] Decide: `program_id` as a native GitHub issue/PR custom field vs. a repo-internal convention field
- [ ] Decide: GitHub Projects (v2) as the Program board surface — requires org-level, not just repo-level, Project creation
- [ ] Decide whether `RESOURCE_LEDGER.jsonl` SPEND rows should be retrofitted with `program_id` tags, or only tagged going forward
- [ ] Link `PROGRAM_GRAPH_MAPPING.md` in `CLAUDE.md`'s Framework Reference section (Layer 5)
- [ ] Append RATIFY event with Z2 hash

---

## Appendix: Quick Reference

| Question | Existing layer that answers it | Layer this document adds |
|:---|:---|:---|
| Does this component exist and run? | System Graph | — |
| What do we believe, and does it still ground out? | Intent Graph (`Q-INTENT-GRAPH-01`, unratified) | Programs become a new node kind within it |
| What work happened this session? | Session Graph (convention) | Program tag makes it cross-session and cross-repo |
| Where does this PR stand right now? | Repository Coordinator | — |
| Who must act on this signal next? | Attention Router (#640, unbuilt) | Program axis composes alongside it |
| What did this cost? | RBE-OPS / `RESOURCE_UNITS.yaml` (ratified) | Rolled up per-Program, still non-commensurable |
| **Which initiative is this in service of, realizing which Objective, and is it worth continuing?** | **Nothing today** | **Programs (this document)** |

---

**Generated by:** Claude (Z1 Proposer)
**For ratification by:** Night/Admiral (Z2 Ratifier)
**For execution by:** Z3 Executors (per `ZONE_REGISTRY.md`)
