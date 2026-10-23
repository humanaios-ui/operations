# Candidate Block: Q-GRAPH-CAPTURE-LINT-01 — graph_capture_lint: the nine properties of a graph that cannot be wrong from the inside

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-10-01
**Status:** AWAITING Z2 RATIFICATION

```yaml
candidate_id: "Q-GRAPH-CAPTURE-LINT-01"
title: "graph_capture_lint_v1_0.py: score every graph file against the nine properties of a self-sealing graph; block on the three that make a graph unauditable"
author: "Z1 (Claude)"
proposed_at: "2026-10-01T00:00:00Z"
scope:
  - "tools/graph_capture_lint_v1_0.py (new, audit_tool, Zone 1)"
  - "tools/tests/test_graph_capture_lint.py + tools/tests/fixtures/graph_capture_*.json (new)"
  - "crb/graph_capture_baseline.json (new; accepted debt, ratchets down only)"
  - ".github/workflows/graph-capture-lint.yml (new)"
  - "crb/README.md (one section added)"
  - "tools-manifest.yaml / TOOLS_MANIFEST.md (scan + render)"
resource_cost:
  cost:
    RAT-min: 20
    Z1-ktok: 60
    CI-min: 1
  dependencies: ["crb/README.md (multiplex doctrine)", "Q-TEMPORAL-DISSOLUTION-01", "H-CAND-GOVERNANCE-CAPTURE-SURFACE-01"]
  blocking_on: []
impact_prediction:
  resource_impact: 4
  areas_affected: ["INTENT_GRAPH.yaml", "system_graph.json", "EVIDENCE_GRAPH.json", "crb/capability_graph.json", "crb/morphogenesis.json"]
  positive_outcomes:
    - "A graph file that acquires closed provenance, loses its defeat channel, or drops its temporal anchor fails the PR that did it, instead of being discovered by a human holding two files in mind."
    - "The five blocking debts in the canonical set are written down with a reason each, so they can be routed and retired rather than carried silently."
    - "Cross-layer edges in the multiplex are recognised as seams rather than reported as dangling, which keeps the lint from pushing the layers back into one graph."
  risk_factors:
    - "Vocabulary-based detection: a graph can pass P2 by naming a relation with a defeat stem and never using it in earnest. The lint reports declared-but-unused channels for exactly this reason; it cannot judge sincerity."
    - "False negatives on P1 where provenance is stored under a key not in the vocabulary. The vocabulary is a constant at the top of the file and is meant to grow by PR."
```

## Claim

- **claim:** The most dangerous graph is not the one that knows the most but the one that cannot be wrong from the inside. Nine properties make a graph self-sealing: closed provenance, no falsifier, no timestamp, collapsed confidence, irreversible identity merges, one identity in every role, reflexive measurement, an unexportable schema, and no verification channel. The first three are the ones every other gate here already presupposes (falsifier doctrine, IC-030 live-fetch and pin, STALE half-lives), so they block; the other six advise.
- **what landed:** a stdlib-only lint (PyYAML for `.yaml` inputs) that normalises the repo's graph shapes (dict-of-nodes, list-of-nodes, `from/to` and `source/target` edges, side tables) and scores all nine. `--all` lints the multiplex named in crb/README.md as one set so an endpoint defined in a sibling layer is a seam, not a defect. `--baseline` records accepted debt and blocks on stale entries, so it only ratchets down.
- **evidence_tier:** VERIFIED-LIVE. `python3 tools/graph_capture_lint_v1_0.py --smoke-test` passes; `pytest tools/tests/test_graph_capture_lint.py` passes; `--all --baseline crb/graph_capture_baseline.json` exits 0 on the tree at this commit.
- **honest reading of the canonical set at landing** (full output in the PR):

| graph | blocking | advisory |
|---|---|---|
| INTENT_GRAPH.yaml | none | P9 (no verification state; `measures` edges name an instrument, not a result) |
| system_graph.json | P2 (REVERT exists only as label text) | none |
| EVIDENCE_GRAPH.json | P3 (no temporal anchor) | P8 (8 relations, no declared vocabulary) |
| crb/capability_graph.json | P2, P3 | P8, P9 |
| crb/morphogenesis.json | P3 | P8, P9 |

Two first-run results were false positives and were fixed before this block was written: EVIDENCE_GRAPH's `defeats_if_unmitigated` is a defeat relation (stem matching now), and morphogenesis cites `tools/molting_protocol_diff_v1_0.py` in a nested side table (nested outward references now count for P1).

## Falsifier

This candidate is FALSE if any of the following is observed:

1. A graph constructed to have all nine properties (the committed `tools/tests/fixtures/graph_capture_terrifying.json`, or any graph Z2 supplies with the same defects) scores below 9/9, or a graph with none of them (the committed clean fixture) scores above 0/9.
2. A canonical graph that gains a typed defeat relation, a `recorded_at`/`temporal_class`, or an outward citation still fails the corresponding blocking property on the next run.
3. Within 30 merged PRs touching the canonical graph set, the lint produces more than two blocking findings that Z2 rules were false positives on inspection. Two already occurred during development and were corrected; a third pattern means the vocabulary approach is wrong for this corpus and the tool should be retired or rebuilt on a declared schema rather than extended.

## Proposed Z2 actions (accept, edit, or reject individually)

1. Ratify the tool and the workflow as a blocking gate on the five canonical graph paths. The workflow exits non-zero on an unlisted blocking failure, but it is not in the branch's required checks; until Z2 adds it there it reports red without blocking merge, consistent with CI gate adjustments being a Z2 decision.
2. Ratify `crb/graph_capture_baseline.json` as the recorded debt, with the five entries above. Each entry names where the fix belongs; none is patched by this PR because `system_graph.json` is Z2 via blueprint and the others are Copilot/CRB-authored prototypes.
3. Decide whether `GRAPH_ALIGNMENT.yaml` should join the canonical set. It is excluded here because it is an alignment table graded by `tools/graph_convergence_v1_0.py`, not a graph.

## Z2 Decision Gate

- [ ] ACCEPT — ratify tool, workflow and baseline; assign Q-number hash
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

**Awaiting Z2 ratification by:** 2026-10-03 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
