# HumanAIOS Knowledge Dashboard: three-source bridge (Z1 proposal)

## Scope

This implementation connects the **derived** repository-knowledge graph from PR #630 to the **source-link** Codebase Atlas merged in PR #835, then adds **historical file observations** from the still-open temporal PR #841. It is a translation/read model, never a new governance ledger.

**No graph edge can approve an admission, establish a CI pass, promote a warrant, ratify a finding, or authorize a merge.** Every projection fixes `authority_effect: NONE`, `can_authorize: false`, `can_execute: false`, `merge_authority: false`.

The bridge never reaches network endpoints or runs external actions. Source paths are explicit input files. It neither fetches private chat content nor republishes it.

## Branch and head status at development start

- **PR #630:** `1345e027921a0e2a6d1355220b6d37277b75a281`, base for this stacked branch; NOT merged when built.
- **PR #835:** merged; Codebase Atlas provides `architecture/codebase_atlas.py` and its generated `atlas.json` in a checkout that contains that merge.
- **PR #841:** `2e30b982c7ee61b7e16278dff5af9cc6ff95680a`, NOT merged. The committed example `graph_timeline/system_graph_timeline.json` declares a different short source head (`4f5d2fe9`). Treat the dates as historical observations, not current exact-head proof.
- This branch is based on #630's implementation. **A single checked-out tree containing both #630 and #835 must be independently constructed or reconciled** before claiming same-head integration. Do not assume merged #835 code exists in #630's older branch.

## Produce source exports (after authorized branch reconciliation)

Build RKG from the target checkout:

```bash
python3 tools/repository_knowledge_graph_v0_1.py build
python3 tools/repository_knowledge_graph_v0_1.py validate \
  --graph outputs/repository-knowledge-graph/graph.json
```

Build Atlas on **the same exact checkout HEAD**, with a clean tree:

```bash
python3 architecture/codebase_atlas.py \
  --repo-root . --out /tmp/haios-atlas
```

Generate #841's temporal output from complete Git history **only after its code is legitimately available** on the checkout. Until then, use a separately retrieved, commit-pinned historical export; it must remain labeled as a draft:

```bash
python3 temporal_graph_timeline.py
```

Then run the read-only adapter and renderer:

```bash
python3 architecture/knowledge_dashboard/observation_bridge.py --smoke-test
python3 architecture/knowledge_dashboard/render.py --smoke-test
python3 -m unittest architecture/knowledge_dashboard/test_observation_bridge.py

python3 architecture/knowledge_dashboard/observation_bridge.py \
  --rkg outputs/repository-knowledge-graph/graph.json \
  --atlas /tmp/haios-atlas/atlas.json \
  --timeline graph_timeline/system_graph_timeline.json \
  --output /tmp/haios-dashboard-projection.json

python3 architecture/knowledge_dashboard/render.py \
  --projection /tmp/haios-dashboard-projection.json \
  --out /tmp/haios-dashboard.html
```

Open the HTML in a browser. It is self-contained: no CDN and no GitHub writes. The graph color differentiates RKG, Atlas, and time observations. Search, select, zoom, pause animation, and scrub historical dates.

## Evidence boundaries

- RKG source must declare `DERIVED_READ_MODEL`, pass its own validation, and identify the exact 40-character repository head.
- Atlas must carry the correct repository name, 40-character head, and explicitly prohibit merge authority.
- If Atlas and RKG full commit pins differ, output is `DIFFERENT_HEAD_NO_CONVERGENCE_CLAIM`. Do not patch over it.
- Historical dates in #841 are observed git file dates when `date_source: git`. Fallback dates remain **FALLBACK_DATE**; they do not prove implementation timestamps.
- Identity joins use only exact RKG `artifact:<path>` and Atlas evidence paths. No keyword matching, name similarity, or source agreement grants proof.
- A declared edge is not a test pass or production execution. The UI is a review tool, not an admission evaluator.
- If a source export is unavailable, halt the **full three-source build**. Use the separate ChatGPT local dashboard with explicit status labels for partial displays.

## Tests / falsifiers

The tests reject unvalidated RKG, forged Atlas authority, dangling graph links, fuzzy identity, and stale-head convergence. The smoke tests remain entirely synthetic. Protected CI must independently verify the branch before any consideration of admission or merge.

## Human decision

The repository operator decides whether to ratify the source/identity mapping. An independent reviewer must establish exact-head CI, admission evidence, and host-side enforcement. This change performs none of those decisions.
