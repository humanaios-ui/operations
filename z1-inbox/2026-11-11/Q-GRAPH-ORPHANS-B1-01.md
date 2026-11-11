# Candidate Block: Q-GRAPH-ORPHANS-B1-01 — graph orphan wiring, batch one (GNER, TDG, CUST)

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-11-11
**Status:** AWAITING Z2 RATIFICATION
**Tracker:** issue #1175 (the sixteen documented orphans). **Carrier:** the pull request that adds this file. Tier 2 by measurement (`system_graph.json`).

```yaml
candidate_id: "Q-GRAPH-ORPHANS-B1-01"
title: "Wire three documented orphans (GNER, TDG, CUST) with edges proven by code, and add the two nodes those edges need"
author: "Z1 (Claude)"
proposed_at: "2026-11-11T00:00:00Z"
scope:
  - "system_graph_generator.py (two nodes, three edges, four updated notes, ACATR implementation list)"
  - "system_graph.json and docs/SYSTEM_GRAPH.md (regenerated; not edited by hand)"
  - "tools/tests/test_system_graph_generator.py (one test pins each edge to its evidence line)"
resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 150
    CI-min: 2
  dependencies: ["Q-SYSTEM-GRAPH-REGEN-01 (merged; ratification recorded separately)", "issue #1175"]
  blocking_on: []
impact_prediction:
  resource_impact: 2
  areas_affected: ["system_graph.json", "docs/SYSTEM_GRAPH.md"]
  positive_outcomes:
    - "Three nodes leave the orphan list because a line of code proves each link, not because a name matches."
    - "Each edge is pinned by a test to the line that proves it, so removing that line fails CI and sends the edge back for review."
  risk_factors:
    - "A docstring or an import shows that one file uses another. It does not show how often, or that the use matters to the system. The edges say 'depends on', nothing stronger."
    - "Two new nodes (CPGA, IGV) carry status LAID from file evidence; neither is run by a workflow."
```

## Claim

- **claim:** Of the sixteen orphan nodes added in Q-SYSTEM-GRAPH-REGEN-01, three have a proven link. Adding those edges takes the graph from 58 nodes and 70 edges to 60 nodes and 73 edges, and the orphan list from sixteen to twelve.
- **evidence (each executed, not only read):**

| edge | evidence | how it was run |
|---|---|---|
| `GNER -> ACATR` | `experiments/acat_r_comparison/study.py:66`: `from gner_verify_e1 import reconcile`, with `SOURCE=ROOT/"tools/gner_verify_e1.py"` at line 11. The workflow `acat-r-second-runtime-comparison.yml` runs the study (line 22). | `python3 experiments/acat_r_comparison/study.py --run-owned-offline` exits 0 |
| `TDG -> IGV` | `tools/intent_graph_v1_0.py:1056`: `from tests.test_temporal_dissolution_gate import is_risky as gate_is_risky`, with the comment at lines 1049-1052 that E10 is "checked against the gate's own patterns rather than a copy of them". | `python3 tools/intent_graph_v1_0.py check` exits 0 |
| `CPGA -> CUST` | `tools/control_plane_github_adapter_v0_1.py:8`: the adapter's output is "the raw observation shape consumed by control_plane_custody_observer_v0_1.py". The adapter's tests pass its output to `observer.normalize_observation(raw)` (`tools/tests/test_control_plane_github_adapter_v0_1.py:86, 109`). | the seven adapter tests pass |

- **evidence_tier:** VERIFIED-LIVE for the three links as stated. `python3 system_graph_generator.py --check` exits 0 under three hash seeds.
- **checked and not wired (recorded in each node's `notes`):**
  - the P19 bot's exemption list names `gner_notification_e0.py`: an exemption, not a data flow;
  - `external-contribution-admission-witness.yml` requires the temporal gate's run to be green: a real dependency, but that workflow is not a node. The same lines also require the coordinator's and the CI-prediction runs, so one new node could carry three edges. Left for a later batch;
  - the coordinator reads the queue state of `Q-TEMPORAL-DISSOLUTION-01`, not the gate workflow;
  - no consumer of the custody observer's receipts was found, so CUST has no outgoing edge.
- **not claimed:** that any of the three links matters operationally; that CPGA or IGV run in production; anything about the twelve remaining orphans.

## Z2 decisions needed (accept, edit, or reject individually)

1. **Three edges.** `GNER -> ACATR`, `TDG -> IGV`, `CPGA -> CUST`.
2. **Two new nodes.** `CPGA` (Control-Plane GitHub Adapter) and `IGV` (Intent Graph Validator), both Z1, LAID. They exist only to carry proven edges.
3. **ACATR implementation list.** It now also names `experiments/acat_r_comparison` and `acat-r-second-runtime-comparison.yml`, the files that import GNER.
4. **Tier 2 requirements not done by Z1:** a `REGISTERED.md` entry (Z2 sole write) and an ADV run. **ADV run: NOT RUN.**

## Falsifier

This candidate is FALSE if any of the following is observed:

1. A cited line no longer exists, or says something other than what is claimed: `test_batch_one_edges_keep_their_evidence` fails.
2. Any of the three edges points the wrong way (the provider is the importer, not the imported module).
3. `python3 system_graph_generator.py --check` exits non-zero on the merged head.
4. A node left with no edge has an empty `notes` field: `test_every_orphan_has_a_note` fails.

## Z2 Decision Gate

- [ ] ACCEPT — ratify items 1-3; Z2 supplies the registry entry and ADV run for item 4
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

Ratification instrument, in two steps. Z1 signs neither.

1. **Merge the pull request.** The merge lands the graph change and this file. This candidate carries no Intent-OS relay Ruling block, so a merge alone leaves it `awaiting_z2` with no `z2_hash`.
2. **Record the decision with the canonical signer, from a checkout of `main` after the merge:**

```
python3 .z1-control/ratify.py Q-GRAPH-ORPHANS-B1-01 --decision ACCEPT --by Night          # dry run
python3 .z1-control/ratify.py Q-GRAPH-ORPHANS-B1-01 --decision ACCEPT --by Night --apply  # writes the ruling and index entry
```

The signer hashes the candidate's exact bytes, so edit this file only before step 2.

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
