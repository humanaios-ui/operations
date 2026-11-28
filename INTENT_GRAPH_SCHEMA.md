# INTENT_GRAPH schema and editing protocol

`INTENT_GRAPH.yaml` is the proposed shared intent substrate for HumanAIOS.
Vision, missions, principles, and objectives are stated across repository
documents; the graph makes their relationships explicit so they can be checked
mechanically. `tools/intent_graph_v1_0.py` validates the graph against this tree
and renders `INTENT_GRAPH.md` and the derived five-module view.

## Status and authority

The graph is candidate `Q-INTENT-GRAPH-01`, status `PROPOSED`. It is not
effective until a Z2 ratification hash exists. Z2 ratifies meaning; Z1 proposes
structure, maintains source accuracy, and records unresolved conflicts. The
renderer is mechanical and does not resolve or prioritize conflicts.

## Node vocabulary

```yaml
node_types:
  vision: One end-state the organization is organized around; expected count 1.
  mission: A durable line of work that, if successful, realizes the vision.
  principle: A rule of decision that grounds objectives and gates.
  objective: Named work with a control surface in the tree.
  gate: A mechanical check that refuses work failing a principle.
  instrument: Code that produces a measurement other nodes depend on.
```

## Edge vocabulary

```yaml
edge_types:
  realizes: Objective → mission → vision.
  grounds: Principle → objective or gate; the authority under which it operates.
  measures: Instrument → objective; produces evidence used to judge it.
  enforces: Gate → principle; mechanical refusal that makes a principle operative.
  constrains: Gate or principle → objective, gate, or instrument; limits without grounding.
  conflicts_with: >-
    Directional: `from` is the departing artifact and `to` is the standard. Both are live
    in the tree. An OPEN edge has a `q_ref`, and only the departing node is marked
    `CONFLICTED`. Details and evidence live in `CONFLICTS.yaml`.
```

## Node status

| Status | Meaning |
|---|---|
| `LIVE` | Implemented, in the tree, and doing its job. |
| `PROPOSED` | Written and awaiting Z2 ratification. |
| `CONFLICTED` | Live, but contradicted by an OPEN `conflicts_with` edge. |
| `CITED_NOT_IMPLEMENTED` | Named by an authority document; no implementation found. |

## Persistence

Persistence classes are state classes, not durations. They name the event that
ends a node's life and do not introduce clock authority. The graph currently has
28 `RATIFIED` nodes, one `TRANSMISSION` node (`O-DECISION-ROUTING`), and no
`SESSION` nodes. The missing SESSION layer is a recorded finding, not an
implicit session-capture mechanism. E15 prevents a durable node from depending
on a less durable one.

| Class | Ends when | Continuity mapping |
|---|---|---|
| `SESSION` | The session ends; working state, in-context reasoning, or an unwritten draft. | `EPHEMERAL` |
| `TRANSMISSION` | The handoff it exists for resolves; a candidate, handoff, or finding in flight. | `QUALIFICATION_PROOF` |
| `RATIFIED` | A Z2 act supersedes it; durable tree memory. | `STANDING_SIGIL` |

Nodes default to `RATIFIED`.

## Source stability

Every node has a repository-relative `source` and a 16-character lowercase
hexadecimal `source_hash`. A source without `anchor` hashes its complete byte
content. An anchored Markdown source hashes the matched heading section, ending
before the next heading of the same or higher level. Anchors may identify a
heading title or a bold section label; missing or ambiguous anchors fail E3b.
Changing source content requires updating the expected hash in the graph.

The graph's node that points back to `INTENT_GRAPH.yaml` uses the deterministic
graph-content fingerprint: hash values in `source_hash` fields are masked before
hashing, avoiding a self-referential digest while still detecting changes to
the graph content.

## Temporal position

The graph carries no scheduling authority. `recorded_at` is observational
provenance; elapsed time does not make a node urgent, stale, expired, or
reordered. Sources and edges change validity through state changes, not age.

## Editing protocol

- Z2 edits meaning: node statements and statuses, or resolution of conflict
  edges.
- Z1 proposes structural edges, maintains source accuracy, and records
  conflicts it finds.
- Do not hand-edit `INTENT_GRAPH.md` or `INTENT_GRAPH_MODULES.md`; render them
  from the graph with the companion tool.
- Preserve every unresolved conflict until an authorized resolution changes its
  status. A derived view does not change graph authority.
