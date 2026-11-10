# Candidate Block: Q-SYSTEM-GRAPH-REGEN-01 — regenerate system_graph.json, define "valid" for a feedback loop, and gate its freshness

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-11-10
**Status:** AWAITING Z2 RATIFICATION
**Carrier:** PR #1158 (draft). Tier 2 by measurement (`system_graph.json`, `.github/workflows/`).

```yaml
candidate_id: "Q-SYSTEM-GRAPH-REGEN-01"
title: "Regenerate system_graph.json (58 nodes, 70 edges), count loop-closing edges as feedback, add a freshness gate"
author: "Z1 (Claude)"
proposed_at: "2026-11-10T00:00:00Z"
scope:
  - "system_graph_generator.py (Edge.feedback, Node.notes, --write / --check CLI, 36 added nodes)"
  - "system_graph.json (regenerated), docs/SYSTEM_GRAPH.md (re-rendered), tools/system_graph_render_v1_0.py (shows node notes)"
  - ".github/workflows/system-graph-freshness.yml (new)"
  - "tools/tests/test_system_graph_generator.py (new), tools/tests/test_repository_coordinator_v0_1.py (two oracle tests read the committed graph instead of pinning 22 nodes), .tool-control/baseline_tests.yaml (one line)"
  - "ci_predictions/pr.json (CI prediction for the carrier PR)"
resource_cost:
  cost:
    RAT-min: 25
    Z1-ktok: 400
    CI-min: 3
  dependencies: ["Q-GRAPH-CAPTURE-LINT-01 (awaiting_z2; graph-capture-lint reads system_graph.json)", "Q-TEMPORAL-DISSOLUTION-01"]
  blocking_on: []
impact_prediction:
  resource_impact: 3
  areas_affected: ["system_graph.json", "docs/SYSTEM_GRAPH.md", "oracles/engine/oracle_engine_v0_1.py (reads the graph)", ".github/workflows/"]
  positive_outcomes:
    - "The graph stops reporting valid=False for a loop that is meant to be a loop, so a real new cycle can be seen when it appears."
    - "A graph that drifts from its generator, or sits unregenerated, fails a check instead of being found by a person."
  risk_factors:
    - "The 16 feedback edges are Z1's judgement of which edges close a loop. A wrong choice hides a real cycle behind the flag. The test only proves the set is minimal, not correct."
    - "Node statuses on the added nodes come from files present in the tree, not from proof the code ran."
    - "The freshness check sees drift and age. It cannot see a missing node."
```

## Claim

- **claim:** `system_graph.json` was last generated 2026-09-13 and carried `valid=False` (cycle error). The governance system is a deliberate loop, so a strict acyclicity test over every edge cannot pass. The graph also omitted work merged since (473 PRs by GitHub search on 2026-11-08).
- **what landed:** the 16 loop-closing edges are flagged `feedback: true` and skipped by the cycle check; forward edges stay acyclic. 20 nodes were added with at least one edge backed by a reference in the cited files, and 16 real subsystems are kept as documented orphans, each with a `notes` field saying why no edge was proven. A `--write` / `--check` CLI and a PR-and-weekly freshness workflow keep the file from going stale again.
- **evidence_tier:** VERIFIED-LIVE for structure. `python3 system_graph_generator.py --check` exits 0; the baseline test list (1278 tests at the last full run) passes locally; every cited implementation path was checked to exist. CI on head `354017d3` passed all checks and all nine pinned CI predictions were right; the head that carries the orphans and this block has not yet been through CI at the time of writing.
- **review history:** an automated review (Copilot, PR #1158) found three edges the cited files do not support (CI predictions to NF, receipts to the notification relay, ACAT API to HIAE). Z1 then audited every added edge by the same test and removed three more (temporal gate to CIG, receipts to MODE, ACAT API to ACAT-R). Six edges were removed in total; the CI-prediction edge now targets its own ledger node (`CIL`). The five nodes left without an edge each carry a note naming what was checked.
- **not claimed:** that any added node runs in production; that the 473-PR sort is complete (98 were sorted by a second pass, #1129–#1157 were read by title only); that the freshness gate would catch a missing node.

## Z2 decisions needed (accept, edit, or reject individually)

1. **Graph content.** Ratify 58 nodes and 70 edges as the canonical process graph.
2. **Meaning of "valid".** Ratify that edges flagged `feedback` are excluded from the cycle check, and review the 16 flagged edges: REG→PRS, REG→FS, REG→Q, REG→MOLT, NF→Q, Z2→MOLT, CONST→TC, CONST→Q, CONST→PRS, CONST→AG, ML→EV, MOLT→NF, MOLT→ADV, MK→CIG, Q→RL, Z2→RL.
3. **New gate.** Ratify `system-graph-freshness.yml`: PR and push check (valid, equals generator output, render in sync), weekly age check with a 45-day limit that opens a tracking issue. The 45 is a new constant; Z2 may set it, or require a molt record for it.
4. **Statuses.** Review the nodes Z1 marked OPERATED from workflow and file evidence only: TDG, MTC, CIP, SMAG, IOS, RCO, SG, ORC, ACAT, RMN. Demote any to LAID if the run is unproven.
5. **Documented orphans.** Keep the 16 orphan nodes visible with notes (ACATR, ATLAS, CUST, DIGEST, EXPS, GL, GNER, GPCS, HIAE, HOBJ, ITEL, MODE, OBS, ORCID, TDG, WEB), or reject any of them. Each note states what was and was not checked.
6. **Tier 2 requirements not done by Z1:** a `REGISTERED.md` entry (Z2 sole write) and an ADV run. **ADV run: NOT RUN.**
7. **Test edits.** Two oracle tests in `tools/tests/test_repository_coordinator_v0_1.py` stop pinning the old 22-node count. The Drive snapshot values (19 and 22) stay pinned because the Drive copy is genuinely stale.

## Falsifier

This candidate is FALSE if any of the following is observed:

1. `python3 system_graph_generator.py --check` exits non-zero on a clean checkout of the merged head, or the committed JSON differs from generator output (ignoring `generated_at`).
2. Clearing the `feedback` flag on any one of the 16 edges leaves the graph valid (the set is not minimal): `tools/tests/test_system_graph_generator.py::test_feedback_set_is_minimal` fails.
3. A new cycle among non-feedback edges leaves the graph valid: `test_new_forward_cycle_is_detected` fails.
4. A node's cited implementation path does not exist, or an edge's cited reference cannot be found in the cited file. Z2 or any reviewer can check both by reading the node entry.
5. A node with no edges has an empty `notes` field (`test_every_orphan_has_a_note` fails).
6. Within 30 merged PRs after ratification, a real new cycle is merged because a wrong feedback flag hid it.

## Z2 Decision Gate

- [ ] ACCEPT — ratify items 1–5 and 7; Z2 supplies the registry entry and ADV run for item 6
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

Ratification instrument: Z2's merge of PR #1158 (2026-09-18 ruling) or `python3 .z1-control/ratify.py` on this file. Z1 does not sign.

---

*Generated by Claude (Z1) for Z2 (Night) ratification*
