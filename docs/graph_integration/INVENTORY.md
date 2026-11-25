# HumanAIOS graph integration inventory (PR #896)

Status: proposed observational interoperability; no production migration or admission authority.

## Graph files on main (pinned 2026-11-25, main `4abc5da3`)

This is the one file-level graph list. It answers step 1 of "Mapping and deployment order" below. Each row is keyed by path plus git blob, never by node count or version label, because counts and labels collide (see "Clashes"). Owner is `@humanaios-ui` for every row (the `*` default in `.github/CODEOWNERS`); "Built by" is the git author or the author the file names. "Repo owner account" means commits made under the repository owner's own login.

| Graph | Path | Blob | Question it answers | Built by | Size and state |
|---|---|---|---|---|---|
| System graph | `system_graph.json` | `69ca0817` | What parts exist, and is each OPERATED, LAID or PLANNED? | Claude (generator) | v0.2, 60 nodes, 73 edges, 12 orphans; CI freshness check |
| Admission ruling graph | `ADMISSION_RULING_GRAPH.md` | `f27eb4ef` | Which PRs were admitted, and which PR carried each Z2 ruling? | Claude + bot | 427 events, 165 PRs; hand-run snapshot, lags the ledger |
| Intent graph | `INTENT_GRAPH.yaml` | `2b77918c` | What do we believe, why, and does anything contradict it? | Claude (Z1) | 29 nodes, 54 edges; PROPOSED |
| Evidence graph | `EVIDENCE_GRAPH.json` | `d2924163` | Is each Witness Phase 0 claim established? | Copilot | 15 nodes, 12 edges; no time anchor |
| Knowledge graph v0.1 | `kg/humanaios_kg_v0_1.json` | `1a1e2aa2` | Which reference books inform which repo areas, with a repo trace? | Claude | 22 nodes, 16 edges; snapshot of the Supabase kg tables, as of 2026-10-16 |
| Cross-chat graph | `chat_graph/source/humanaios_cross_chat_knowledge_graph.v0.1.json` | `235b4199` | What did past chats claim, and what backs it? | Repo owner account | 195 nodes, 213 edges; frozen source, non-canonical |
| Program graph | `program_graph.py` | `6d970b6c` | Which initiative is this work for, at what cost per unit? | Claude | Code only, reads the intent graph; proposed |
| Capability graph | `crb/capability_graph.json` | `be4c0523` | Which agent capabilities exist, and does each end in evidence? | Repo owner account | 11 stages, 9 nodes, 14 edges; prototype |
| Morphogenesis | `crb/morphogenesis.json` | `df13972e` | How may the graphs change shape, and what review does each change need? | Repo owner account | 9 edges; prototype, non-enforcing |
| System graph timeline | `graph_timeline/system_graph_timeline.json` | `97949460` | When did each system graph part first appear and last change? | Claude | 22 nodes, 53 edges at 2026-10-15; no workflow rebuilds it |
| Workflow dependency graph | `docs/WORKFLOW_DEPENDENCY_GRAPH.md` | `3a70343a` | Which CI workflows depend on which, and what review class each needs? | Repo owner account | Counts 49 workflows; dated 2026-09-20 |
| Calibration evidence graph | `docs/design/calibration-evidence-graph.ttl` | `c6a0f401` | Do calibration claims and their evidence have the required shape? | Repo owner account | RDF plus SHACL check; tests in `tests/calibration_graph/` |
| Machine substrate graph | `tools/machine_graph/collect_macos.py` | `ad186ca2` | What can this machine already do, before we install or research? | Repo owner account | macOS collector; no snapshot committed |
| Identity graph | `entry_protocol/identity_graph.py` | `42965dfa` | Who is speaking: transport, human or AI session, kept apart? | Repo owner account | Code prototype v0.5 |
| SCVC milestone graph | `experiments/scvc_v02/milestone_graph.json` | `052de41d` | Which continuity milestones are reached? | Repo owner account | 5 milestones; synthetic, no authority |
| Codebase Atlas | `architecture/codebase_atlas.py` | `23e770b1` | How do files and folders connect, as a clickable map? | Repo owner account | 14 components; output built on demand |

### Graphs not on main

| Graph | Where | Question it answers | Size and state |
|---|---|---|---|
| Knowledge graph v0.2 proposal | PR #1310, `kg/humanaios_kg_v0_2_proposal.json` | Which links finish the KG: dependency, evidence, decision, outcome? | 19 new nodes, 73 edges; open draft PR, all edges unratified |
| Repository knowledge graph | PR #630, `tools/repository_knowledge_graph_v0_1.py` | What is in the repo, with a citation for every edge? | Compiler plus schema; PR closed without merge 2026-10-16 |
| 358-node research graph | Private; pinned by a receipt in PR #1310 | Research graph behind the KG work | Two snapshots, 358 nodes each, 53 and 83 edges; not published |

### Clashes

- **Shared labels.** "v0.2" names the system graph, the KG v0.2 proposal and an older hand-written `system_graph_v0.2.md` on Drive (19 nodes, 44 edges, per `PROGRAM_GRAPH_MAPPING.md`). "73 edges" names the system graph and the KG v0.2 proposal. "22 nodes" names KG v0.1 and the system graph timeline. "19 nodes" names the KG v0.2 new nodes and the old Drive system graph.
- **Stale counts.** The timeline is 22 nodes and 53 edges against 60 and 73 in `system_graph.json`. `AGENT_GRAPH_COMPARISON.md` gives the intent graph 26 nodes; the file has 29. `docs/WORKFLOW_DEPENDENCY_GRAPH.md` counts 49 workflows; `.github/workflows/` holds 106 workflow files.
- **Reader without its graph.** `tools/graph_lookup_v0_1.py` is on main; the graph it reads comes from PR #630, which was closed without merge.
- **Status clash.** `system_graph.json` marks Intent-OS OPERATED and cites `INTENT_GRAPH.yaml`, which says PROPOSED.
- **Other lists.** `PROGRAM_GRAPH_MAPPING.md` (7 layers) and the canonical set in `tools/graph_capture_lint_v1_0.py` (5 graphs) also list graphs. The lint set does not cover KG v0.1, the cross-chat graph, the timeline or the admission ruling graph.

### Not graphs

84 tracked paths contain "graph". 7 match only inside "holographic" (`tools/holographic_orchestrator.py`, its 3 tests and fixture, `supabase/migrations/20260916_holographic_jobs.sql`, `z1-inbox/2026-09-16/HOLOGRAPHIC_HYPOTHESIS_PROTOCOL.md`). The rest are the graphs above, their tools, tests, workflows and Z1 inbox papers, plus three schemas with no data: Witness Arena graph event, oracle graph delta, observation projection. `kg/`, `crb/morphogenesis.json` and Codebase Atlas are graphs without "graph" in their names.

## Design surfaces (PR #896)

The table below is the original design-level view. It keeps each surface's trust boundary. For file lookup, use the tables above.

| Surface | Producer / input | Output | Consumers | Trust boundary |
|---|---|---|---|---|
| Repository graph (#630, open proposal) | Deterministic repository compiler; tracked tree and allowlisted metadata | Graph schema, machine-readable graph and GraphML | graph_lookup and reviewer inspection | Snapshot observations and bounded inference, not successful CI or admission |
| Codebase Atlas (#835) | Tracked files, AST imports, valid links, workflow invocations | HTML/SVG, JSON, Markdown, Mermaid; evidence sidebar | Humans and advisory graph views | Read-only path-pinned projection; never authoritative system_graph |
| Temporal graph (#841) | system_graph.json plus Git history | graph_timeline/system_graph_timeline.json and HTML | Timeline viewers | Commit dates do not establish ratification; unresolved implementations remain flagged |
| Evidence Graph | Evidence references and associated claims | Existing independently validated records | Review and research | A graph edge does not attest independent execution |
| Session Graph | Session observations and references | Session records | Continuity and research | Private session content must not be projected publicly by default |
| SCVC | Continuity verification observations and independently witnessed outcomes | SCVC records and evidence | Milestone reasoning | Verified witness evidence distinct from proposed claims |
| Repository Coordinator | Governed admission policy, authenticated reviews, CI and decisions | Admission receipts and state | Protected workflow | Only authorized control plane makes decisions |

## Overlap and preservation
- Atlas and repository graph both describe repository topology. Retain their individual producers; normalize *copies* of their observations into the interchange format rather than run another canonical compiler.
- Temporal graph dates describe Git activity; SCVC describes continuity claims. Never merge them into a single authoritative timestamp.
- Evidence, Session, SCVC, and Coordinator have different provenance and disclosure rules. A common node/edge shape is not permission to merge trust levels.
- #630 remains a proposal until independently admitted; do not turn its projected output into a policy dependency.
- `graph_lookup` is a downstream reader, not proof the proposed compiler is deployed.

## Initial integration contract
See `docs/graph_integration/observation_projection_v0.schema.json`.
One projection is a **read-only derived copy** with explicit source refs, exact source revision, observation time, evidence class, and uncertainty state. The contract defines no commands, writes, admissions or promotions.

## Mapping and deployment order
1. Inventory actual producer paths and consumer imports at each pinned repository head. Rows above are design-level, not a verified comprehensive file enumeration.
2. Run fixture-only contract tests offline.
3. Add source-specific adapters as separate read-only PRs, measuring unmapped records and source coverage.
4. Compare Atlas and #630 observations against common file-revision fixtures; preserve disagreements as conflicts.
5. Only after validated adapters exist, wire an opt-in advisory query/view. Never put projection output in Coordinator authorization input.

## Known gaps and falsifiers
- Incomplete implementation-to-file matches in #841 must be `unresolved`, never fabricated links.
- Missing evidence, unknown revisions, contradictory claims, and redacted private sources must not appear verified.
- A comment or graph observation cannot stand in for authenticated APPROVED review or exact-head protected CI.
- Fail closed on malformed record identifiers, duplicate IDs, missing source, invalid graph endpoints, attempted authority fields or unsupported confidence states.

## Acceptance for PR #896
- Inventory, non-authoritative versioned exchange schema, standalone test fixtures and tests.
- No privileged workflow/policy/manifest edits.
- Run tests on PR head; require CodeRabbit and required human APPROVED review plus separately verified protected CI before any admission.
