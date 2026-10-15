# Candidate Block: Q-REPO-GRAPH-LOOKUP-01 — read-only, citation-bearing graph lookup for §A

```yaml
candidate_id: "Q-REPO-GRAPH-LOOKUP-01"
title: "Give §A session open a read-only lookup over the PR #630 repository graph, pinned to commit and integrity-checked"

description: |
  - Gap: PR #630 (repository knowledge graph) compiles a graph with a pinned head_commit,
    an integrity digest and per-edge provenance, and ships a `query` subcommand. Nothing
    in §A reads it. Its output directory is gitignored (`outputs/`), so no pinned copy
    exists in the tree at session open. The existing `query` does not compare the graph's
    commit with HEAD and does not verify the integrity digest before answering.
  - Proposal: `tools/graph_lookup_v0_1.py`, stdlib only, read-only. It refuses a graph whose
    digest does not verify or whose authority_effect is not NONE. It reports FRESH / STALE /
    DIRTY / UNKNOWN against the current repository HEAD. Each answer cites the node, its
    incident edges, and each edge's provenance (source_ref, locator, source_hash).
  - It does not build the graph, does not write, does not import the #630 module, and does
    not change §A. Wiring it into §A is a separate Z2 decision.

author: "Z1 (Claude)"
proposed_at: "2026-10-15T00:00:00Z"

scope:
  - "operations"
  - "tools/graph_lookup_v0_1.py"
  - "tools/tests/test_graph_lookup_v0_1.py"
  - "tools-manifest.yaml (HAIOS-TOOL-224)"
  - "TOOLS_MANIFEST.md"
  - ".tool-control/baseline_tests.yaml"

resource_cost:
  cost:
    RAT-min: 5
    Z1-ktok: 40
    CI-min: 3
  dependencies: ["PR #630", "tools/repository_knowledge_graph_v0_1.py", "ZONE_REGISTRY.md", "CLAUDE.md"]
  blocking_on: ["PR #630 merge (for a graph on main; the tool itself has no import dependency)"]

impact_prediction:
  resource_impact: 3
  areas_affected:
    - "operations (diagnostic tooling)"
    - "section A session open (proposed consumer, not changed here)"
  positive_outcomes:
    - "Session open can ask a graph question and get cited, commit-pinned answers"
    - "A stale or tampered graph is visibly refused, not silently trusted"
  risk_factors:
    - "Graph answers read as authority if a session treats them as ratified facts; authority_effect NONE and GRAPH_IS_NOT_AUTHORITY must hold in use"
    - "Graph file is about 43 MB; a rebuild is about 32 s per session if no pinned copy is kept"
    - "Lookup is substring matching over node id and label, not semantic search"

falsifier: |
  This proposal is FALSE if any of the following is observed:
  1. A graph with a modified node label passes `load_graph` (integrity check fails to refuse), or
  2. An answer is produced for a graph whose `source.head_commit` differs from the repository
     HEAD without a STALE state being reported, or
  3. Running the tool changes the graph file bytes or the repository `git status --porcelain
     --ignored` output (read-only claim fails), or
  4. The compiler's own `validate` accepts a graph that this tool's digest check refuses on
     the same bytes (the two integrity implementations disagree).

evidence:
  - "PR #630 head 1345e02 (merge with main; conflicts with main resolved in this session)"
  - "tools/repository_knowledge_graph_v0_1.py: `query` subcommand; `_graph_digest`; `_canonical_bytes`"
  - "outputs/ listed in .gitignore; graph output not tracked"
  - "Real graph built from PR 630 head: integrity 92e5a930…, source.head_commit 1345e027…, 117 incident edges for artifact:SESSION_RITUALS.md; lookup reports FRESH against that worktree and withholds answers with --require-fresh against a dirty tree"
  - "tools/tests/test_graph_lookup_v0_1.py: 13 passed"
  - "SESSION_RITUALS.md §A has no graph step (checked 2026-10-15)"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-GRAPH-CONVERGENCE-01", "Q-GRAPH-CAPTURE-LINT-01"]
external_constraint: null
links:
  - name: "PR #630 (repository knowledge graph, repaired)"
    url: "https://github.com/humanaios-ui/operations/pull/630"
```

---

## Notes for Z2

- **Repair done, not merged.** PR #630 had three merge conflicts with `main` (quality-baseline.yml,
  TOOLS_MANIFEST.md, tools/intent_os_test_harness_v1_0.py). The pushed fix is a merge commit
  `1345e02` onto `salvage/repository-knowledge-graph-v0`. It takes main's pytest list, registers
  `tools/tests/test_repository_knowledge_graph_v0_1.py` in `.tool-control/baseline_tests.yaml`,
  and regenerates TOOLS_MANIFEST.md with the repo tooling. Checks run: manifest scan, validate,
  selftest, render --check; enumeration guard 6/6; graph regression suite 24 passed.
  Merge and admission remain Z2 acts.
- **ID collision avoided.** The new tool row first received HAIOS-TOOL-223, which the ratified
  HCM record already cites. It is recorded as HAIOS-TOOL-224 here. Z2 should confirm the ID.
- **Not done here:** no change to SESSION_RITUALS.md §A, no graph committed, no CI gate added.
  Wiring the lookup into §A and deciding whether a pinned graph is committed are Z2 decisions.
