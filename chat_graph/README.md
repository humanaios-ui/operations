# Cross-chat longitudinal evidence graph

**Planning surface:** #677  
**Status:** derived, non-canonical  
**Authority effect:** none

This directory converts the cross-chat semantic index into an append-only, provenance-bearing longitudinal graph.

## Why this exists

The predecessor graph is useful for navigation but its assertions were synthesized from retrievable chat history. A chat synthesis is not independent evidence. This layer preserves that graph unchanged, converts its semantic statements into explicit assertions, binds addressable sources, and records corrections/state changes as events.

## Files

- `source/humanaios_cross_chat_knowledge_graph.v0.1.json` — frozen predecessor.
- `evidence/github_hydration_2026-10-02.json` — first live source-observation overlay.
- `build_longitudinal_graph.py` — deterministic stdlib compiler/validator.
- `schema/longitudinal_graph.schema.json` — structural contract.
- `HYDRATION_RECEIPT_2026-10-02.json` — receipt from the verified first build.
- `generated/` — derived output; intentionally rebuildable rather than authoritative.

## Model

The graph separates:

1. **Entity** — a stable referent.
2. **Assertion** — what chat synthesis or a source says about a referent.
3. **Source** — an addressable provenance object.
4. **Event** — an append-only observation, hydration, correction, contradiction, supersession, implementation, test or outcome record.

Hydration describes source binding, not truth:

`CHAT_DERIVED -> SOURCE_LOCATED -> SOURCE_OBSERVED -> CROSS_VERIFIED`

`CONTESTED` and `SUPERSEDED` preserve disagreement and historical state.

## Longitudinal rule

Never silently rewrite old graph state. If later evidence differs, append a correction/supersession event and retain the prior assertion.

The first pass demonstrates this with three corrections:
- `ISSUE_358` was synthesized as an Issue; GitHub identifies #358 as a PR.
- `ISSUE_560` was synthesized as an Issue; GitHub identifies #560 as a PR.
- PR #534 was described from an earlier unmerged snapshot; later GitHub state observes it merged.

## Build

```bash
python3 chat_graph/build_longitudinal_graph.py --check
python3 chat_graph/build_longitudinal_graph.py
```

Expected first-build counts:
- entities: 195
- assertions: 444
- sources: 40
- events: 40
- source-hydrated entities: 30

## Relationship to existing graph infrastructure

This does **not** replace `EVIDENCE_GRAPH.json`, `INTENT_GRAPH.yaml`, or the repository knowledge graph in PR #630. It is an additional source/projection.

After #630 lands, the intended integration is an adapter that exposes:
- provenance view,
- longitudinal view,
- unhydrated view,
- conflict/correction view.

No source binding, inference, graph membership, or participation grants authority, warrant, authorization, or execution capability.
