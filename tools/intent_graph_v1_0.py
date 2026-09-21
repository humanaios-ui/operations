#!/usr/bin/env python3
"""
intent_graph_v1_0.py — validate INTENT_GRAPH.yaml against the tree and render it.
Builder v1.7 compliant
HumanAIOS — Q-INTENT-GRAPH-01

Answers the question that previously required reading five prose documents and
holding them in mind at once: what grounds this objective, what measures it,
what enforces it, and what in the tree contradicts it.

  check                  validate the graph; exit 1 on any error
  render                 write INTENT_GRAPH.md
  render --check         exit 1 if INTENT_GRAPH.md is out of sync (CI mode)
  trace <node-id>        print one node's grounding, measurement and conflicts
  --input <path>         read a graph other than INTENT_GRAPH.yaml; renders to
                         stdout, so trying a candidate graph cannot overwrite
                         the canonical page
  --smoke-test           self-check on a fixture; no filesystem writes

What it does NOT do: it does not decide anything. It refuses a graph that has
drifted from the tree and it prints what is unresolved. Ratification remains a
Z2 act; this tool has no opinion about which side of a conflict is right.

TEMPORAL POSITION (Q-TEMPORAL-DISSOLUTION-01)
This tool reads no clock. It has no cadence, emits no due date, and its findings
do not age. A conflict row is as open on the day it is written as a year later;
what closes it is a Z2 decision, not elapsed time.

VALIDATION RULES (all mechanical, all re-runnable)
  E1  every node id is unique
  E2  every node type is in node_types
  E3  every node source path resolves in the tree     <- the anti-drift rule
  E4  every edge endpoint names an existing node
  E5  every edge rel is in edge_types
  E6  every objective reaches a vision by `realizes`
  E7  every objective and gate has >=1 inbound `grounds`
  E8  every conflicts_with edge carries status and, when OPEN, a q_ref
  E9  the `from` side of an OPEN conflicts_with edge is marked status CONFLICTED.
      The edge is directional on purpose — `from` is the artifact that departs,
      `to` is the standard it departs from. Marking the standard "conflicted"
      would read as though the policy were the defect.
  E10 no node carries an unclassified internal temporal control in its own text.
      This file is exempt from the line scanner in
      tests/test_temporal_dissolution_gate.py, because a `conflicts_with` row
      exists precisely to quote the defect it reports and a line scanner cannot
      tell a quotation from a control. E10 restores that enforcement where it
      belongs: on node text, which is the graph speaking in its own voice.
  W1  a node marked CITED_NOT_IMPLEMENTED is reported, never fatal
  W2  an objective with no inbound `measures` edge is reported
  W3  a mission no objective in this tree realizes is reported
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "intent_graph"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-092126-intent-graph"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(ROOT, "INTENT_GRAPH.yaml")
OUTPUT = os.path.join(ROOT, "INTENT_GRAPH.md")

# E10. The full RISK_PATTERNS set from tests/test_temporal_dissolution_gate.py,
# adapted for field text rather than diff lines: the gate's `^\s*(schedule|cron):`
# is line-anchored, which means nothing inside a YAML scalar, so it is matched on
# a word boundary here instead. The compact unit alternatives (48h, 2d) are kept —
# dropping them was the hole this set is closing.
#
# Parity matters more here than anywhere else in this file: INTENT_GRAPH.yaml is
# exempt from the line scanner, so E10 is the *only* thing standing between a node
# statement and a control the gate would have rejected. Any pattern added to
# RISK_PATTERNS belongs here too; `--smoke-test` asserts the two sets agree.
TEMPORAL_RISK = (
    re.compile(r"\b(deadline|due_at|window_end|respond_within|complete_within|start_after)\s*[:=]", re.I),
    re.compile(r"\b(due|deadline)\s+(by|on)\b", re.I),
    re.compile(r"\boverdue\b", re.I),
    re.compile(
        r"\b(must|shall|required\s+to|respond|complete|finish|deliver)\b.{0,60}"
        r"\bwithin\s+\d+\s*(seconds?|minutes?|hours?|days?|weeks?|s|m|h|d|w)\b",
        re.I,
    ),
    re.compile(r"\b(schedule|cron)\s*:", re.I),
)
ALLOWED_TEMPORAL_CLASSES = {
    "OBSERVATIONAL",
    "TECHNICAL_SAFETY",
    "REGULATORY_EXTERNAL",
    "HISTORICAL_RECORD",
}

# E11. The status vocabulary. Documented in INTENT_GRAPH.yaml's header comment;
# without this it was documented and unenforced, so `PROPOSD` would have read as
# an unknown status and been treated as "not CONFLICTED" by E9.
NODE_STATUSES = {
    "LIVE",
    "PROPOSED",
    "CONFLICTED",
    "CITED_NOT_IMPLEMENTED",
}

# E12. What each edge type is allowed to connect. An edge whose rel is spelled
# correctly but points the wrong way — `grounds` from an objective to a
# principle, say — reverses the meaning of the graph while passing every other
# check. `conflicts_with` is deliberately unconstrained: any two live artifacts
# can contradict each other.
EDGE_DOMAINS: dict[str, tuple[set[str], set[str]]] = {
    "realizes": ({"objective", "mission"}, {"mission", "vision"}),
    "grounds": ({"principle"}, {"objective", "gate"}),
    "measures": ({"instrument"}, {"objective"}),
    "enforces": ({"gate"}, {"principle"}),
    "constrains": ({"gate", "principle"}, {"objective", "gate", "instrument"}),
}

# Node types this validator actually has structural rules for. A type declared in
# the graph but absent here is reported (W5): the file's own header says adding a
# type without teaching the validator what it means is a lint failure, and that
# claim was previously unenforced.
KNOWN_NODE_TYPES = {"vision", "mission", "principle", "objective", "gate", "instrument"}

GENERATED_BANNER = (
    "<!-- GENERATED FILE — do not hand-edit.\n"
    "     Source: INTENT_GRAPH.yaml · Renderer: tools/intent_graph_v1_0.py\n"
    "     Regenerate: python3 tools/intent_graph_v1_0.py render -->"
)

# Render order for the layer sections and the mermaid subgraphs.
LAYER_ORDER = ("vision", "mission", "principle", "objective", "gate", "instrument")

STATUS_MARK = {
    "LIVE": "live",
    "PROPOSED": "proposed",
    "CONFLICTED": "conflicted",
    "CITED_NOT_IMPLEMENTED": "cited, not implemented",
}

# Mermaid node shapes per type, so the canvas carries the layer distinction
# visually rather than only in the label.
SHAPE = {
    "vision": ("([", "])"),
    "mission": ("[", "]"),
    "principle": ("{{", "}}"),
    "objective": ("[", "]"),
    "gate": ("[/", "/]"),
    "instrument": ("[(", ")]"),
}


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys.

    `yaml.safe_load` silently keeps the last of a duplicated key, so a second
    `nodes:` or `edges:` block would hide everything in the first one — and hide
    it *before* E1–E10 ever run, so `check` would pass on a graph with content
    missing. For a governance SSOT that is the worst possible failure: silent,
    and it reads as a clean bill of health. Mirrors `.z1-control/validate.py`,
    which refuses duplicate keys for the same reason.
    """


def _no_duplicates(loader: yaml.Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def load(path: str = GRAPH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.load(handle, Loader=StrictLoader)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return data


def _nodes(graph: dict) -> list[dict]:
    return list(graph.get("nodes") or [])


def _edges(graph: dict) -> list[dict]:
    return list(graph.get("edges") or [])


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def validate(graph: dict, root: str = ROOT) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors are merge-blocking; warnings are not."""
    errors: list[str] = []
    warnings: list[str] = []

    node_types = set(graph.get("node_types") or {})
    edge_types = set(graph.get("edge_types") or {})
    nodes = _nodes(graph)
    edges = _edges(graph)

    by_id: dict[str, dict] = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            errors.append("E1 a node has no id")
            continue
        if nid in by_id:
            errors.append(f"E1 duplicate node id: {nid}")
            continue
        by_id[nid] = node

        ntype = node.get("type")
        if ntype not in node_types:
            errors.append(f"E2 {nid}: unknown node type {ntype!r}")

        status = node.get("status")
        if status not in NODE_STATUSES:
            errors.append(
                f"E11 {nid}: unknown status {status!r}. One of "
                f"{', '.join(sorted(NODE_STATUSES))}. A misspelled status reads as "
                f"'not CONFLICTED' to E9, which is how a known contradiction goes quiet."
            )

        source = node.get("source")
        if not source:
            errors.append(f"E3 {nid}: no source path")
        else:
            resolved = _resolve_in_tree(str(source), root)
            if resolved is None:
                errors.append(
                    f"E3 {nid}: source escapes the repository root: {source}. "
                    f"E3 claims the graph describes *this* tree; an absolute path or "
                    f"one climbing out of it would satisfy the letter of that check "
                    f"while pointing somewhere else."
                )
            elif not os.path.exists(resolved):
                errors.append(f"E3 {nid}: source does not resolve in the tree: {source}")

        if node.get("status") == "CITED_NOT_IMPLEMENTED":
            warnings.append(f"W1 {nid}: cited by {node.get('source')} with no implementation found")

        # E10 — the graph's own voice is held to the policy it records.
        own_text = " ".join(
            str(node.get(field) or "") for field in ("name", "statement", "note")
        )
        if any(pattern.search(own_text) for pattern in TEMPORAL_RISK):
            declared = str(node.get("temporal_class") or "").upper()
            if declared not in ALLOWED_TEMPORAL_CLASSES:
                errors.append(
                    f"E10 {nid}: node text carries an internal temporal control with no "
                    f"permitted temporal_class. A node describing such a control belongs "
                    f"in a conflicts_with row, not in a node statement."
                )

    # Edges.
    inbound: dict[tuple[str, str], list[str]] = {}
    realizes: dict[str, list[str]] = {}
    conflicted: set[str] = set()

    for index, edge in enumerate(edges):
        src, dst, rel = edge.get("from"), edge.get("to"), edge.get("rel")
        where = f"edge[{index}] {src}-{rel}->{dst}"

        if rel not in edge_types:
            errors.append(f"E5 {where}: unknown rel {rel!r}")
        for endpoint in (src, dst):
            if endpoint not in by_id:
                errors.append(f"E4 {where}: no such node {endpoint!r}")

        if src not in by_id or dst not in by_id:
            continue

        inbound.setdefault((dst, rel), []).append(src)
        if rel == "realizes":
            realizes.setdefault(src, []).append(dst)

        # E12 — an edge pointing the wrong way reverses the graph's meaning.
        domain = EDGE_DOMAINS.get(rel)
        if domain:
            allowed_from, allowed_to = domain
            src_type = by_id[src].get("type")
            dst_type = by_id[dst].get("type")
            if src_type not in allowed_from or dst_type not in allowed_to:
                errors.append(
                    f"E12 {where}: `{rel}` connects {src_type} → {dst_type}; it is "
                    f"defined as {'|'.join(sorted(allowed_from))} → "
                    f"{'|'.join(sorted(allowed_to))}"
                )

        if rel == "conflicts_with":
            status = edge.get("status")
            if status not in {"OPEN", "RESOLVED"}:
                errors.append(f"E8 {where}: conflicts_with needs status OPEN or RESOLVED")
            elif status == "OPEN":
                if not edge.get("q_ref"):
                    errors.append(
                        f"E8 {where}: an OPEN conflict must name the candidate that would "
                        f"resolve it (q_ref). Noticed-and-left is the failure P-ADMISSION refuses."
                    )
                # Directional: only the departing side is marked. See E9.
                conflicted.add(src)

    # E6 — every objective reaches a vision through realizes.
    visions = {nid for nid, n in by_id.items() if n.get("type") == "vision"}
    for nid, node in by_id.items():
        if node.get("type") != "objective":
            continue
        if not _reaches(nid, visions, realizes):
            errors.append(f"E6 {nid}: no `realizes` path to a vision — orphan objective")

    # E7 — grounding.
    for nid, node in by_id.items():
        if node.get("type") not in {"objective", "gate"}:
            continue
        if not inbound.get((nid, "grounds")):
            errors.append(f"E7 {nid}: no principle grounds this {node.get('type')}")

    # E9 — a conflicted node must say so.
    for nid in sorted(conflicted):
        if by_id[nid].get("status") != "CONFLICTED":
            errors.append(
                f"E9 {nid}: carries an OPEN conflicts_with edge but status is "
                f"{by_id[nid].get('status')!r}, not CONFLICTED"
            )

    # W2 — measurement.
    for nid, node in by_id.items():
        if node.get("type") == "objective" and not inbound.get((nid, "measures")):
            warnings.append(f"W2 {nid}: no instrument measures this objective")

    # W3 — a mission nothing in this tree works toward. Not an error: the work
    # may live in another repo. Worth seeing rather than inferring from silence.
    for nid, node in by_id.items():
        if node.get("type") == "mission" and not inbound.get((nid, "realizes")):
            warnings.append(f"W3 {nid}: no objective in this repository realizes this mission")

    # W4 — vision cardinality. The vocabulary says "Expected count 1"; two
    # visions is not obviously an error but it is never accidental.
    if len(visions) != 1:
        warnings.append(
            f"W4 {len(visions)} vision nodes ({', '.join(sorted(visions)) or 'none'}); "
            f"the vocabulary expects exactly 1"
        )

    # W5 — a type the graph declares that this validator has no rule for. The
    # header claims adding one is a lint failure; this is that lint.
    for declared in sorted(set(node_types) - KNOWN_NODE_TYPES):
        warnings.append(
            f"W5 node type {declared!r} is declared but the validator has no "
            f"structural rule for it — it is checked only for id and source"
        )
    for declared in sorted(set(edge_types) - set(EDGE_DOMAINS) - {"conflicts_with"}):
        warnings.append(
            f"W5 edge type {declared!r} is declared but has no entry in "
            f"EDGE_DOMAINS — its endpoints are unchecked"
        )

    return errors, warnings


def _resolve_in_tree(source: str, root: str) -> str | None:
    """Absolute path for `source` inside `root`, or None if it escapes.

    Returns None for an absolute source and for anything whose real path lands
    outside the repository root, so E3 cannot be satisfied by a path that is not
    in this tree.
    """
    if os.path.isabs(source) or (os.path.altsep and source.startswith(os.path.altsep)):
        return None
    root_real = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root_real, source))
    if candidate != root_real and not candidate.startswith(root_real + os.sep):
        return None
    return candidate


def _reaches(start: str, targets: set[str], forward: dict[str, list[str]]) -> bool:
    seen: set[str] = set()
    stack = [start]
    while stack:
        current = stack.pop()
        if current in targets:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(forward.get(current, ()))
    return False


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _esc(text: object) -> str:
    return (str(text) if text is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def _oneline(text: object) -> str:
    return " ".join(str(text or "").split())


def _mermaid_label(node: dict) -> str:
    # Mermaid chokes on quotes and brackets inside labels; the id plus a short
    # name is enough to read the canvas, and the tables below carry the prose.
    name = _oneline(node.get("name") or node.get("id"))
    name = name.replace('"', "").replace("[", "").replace("]", "")
    return f'{node["id"]}<br/>{name}'


def render(graph: dict, errors: list[str], warnings: list[str]) -> str:
    nodes = _nodes(graph)
    edges = _edges(graph)
    by_id = {n["id"]: n for n in nodes if n.get("id")}
    by_type: dict[str, list[dict]] = {}
    for node in nodes:
        by_type.setdefault(node.get("type", "?"), []).append(node)

    out: list[str] = []
    add = out.append

    add(GENERATED_BANNER)
    add("")
    add("# INTENT_GRAPH.md — how vision, mission, principles and objectives interact")
    add("")
    add(f"**Candidate:** {graph.get('q_id', '—')}  ")
    add(f"**Status:** {graph.get('status', '—')} — not effective until Z2 ratification hash  ")
    add(f"**Source of truth:** `INTENT_GRAPH.yaml` (edit there; this file is rendered)  ")
    add(f"**Temporal class:** {graph.get('temporal_class', '—')} · scheduling authority: "
        f"{str(graph.get('scheduling_authority', False)).lower()}")
    add("")
    add("This page is a projection. It states nothing that is not in the graph, and the")
    add("graph states nothing whose source does not resolve in the tree.")
    add("")

    # --- the canvas ---------------------------------------------------------
    add("---")
    add("")
    add("## The canvas")
    add("")
    add("Read it upward: instruments measure objectives, principles ground them, objectives")
    add("realize missions, missions realize the vision. A crossed edge (`x--x`) is a live")
    add("contradiction, labelled with the candidate open against it.")
    add("")
    add("```mermaid")
    add("flowchart BT")

    conflict_edges = [e for e in edges if e.get("rel") == "conflicts_with"]

    for layer in LAYER_ORDER:
        members = by_type.get(layer, [])
        if not members:
            continue
        add(f"  subgraph {layer.upper()}[{layer}]")
        for node in members:
            open_shape, close_shape = SHAPE.get(layer, ("[", "]"))
            add(f'    {node["id"]}{open_shape}"{_mermaid_label(node)}"{close_shape}')
        add("  end")

    add("")
    for edge in edges:
        rel = edge.get("rel")
        if rel == "conflicts_with":
            continue
        arrow = {
            "realizes": "-->",
            "grounds": "-.->",
            "measures": "==>",
            "enforces": "-.->",
            "constrains": "-.->",
        }.get(rel, "-->")
        add(f'  {edge["from"]} {arrow}|{rel}| {edge["to"]}')

    for index, edge in enumerate(conflict_edges):
        add(f'  {edge["from"]} x--x|conflicts: {edge.get("q_ref", "unfiled")}| {edge["to"]}')

    # Style the conflicted nodes so the contradiction is visible at a glance.
    conflicted_ids = sorted(
        {e["from"] for e in conflict_edges if e.get("status") == "OPEN"}
    )
    if conflicted_ids:
        add("")
        add("  classDef conflicted stroke-dasharray: 4 3,stroke-width:2px")
        add(f"  class {','.join(conflicted_ids)} conflicted")
    add("```")
    add("")

    # --- open conflicts -----------------------------------------------------
    add("---")
    add("")
    add("## Open contradictions")
    add("")
    open_conflicts = [e for e in conflict_edges if e.get("status") == "OPEN"]
    if not open_conflicts:
        add("None recorded.")
        add("")
    else:
        add("Each row is two live artifacts that cannot both be right. `q_ref` names the")
        add("candidate that would settle it — an open row with no candidate fails validation.")
        add("")
        add("| Between | And | Candidate | What contradicts |")
        add("|:--|:--|:--|:--|")
        for edge in open_conflicts:
            add(
                f'| `{edge["from"]}` | `{edge["to"]}` | {_esc(edge.get("q_ref"))} '
                f'| {_esc(_oneline(edge.get("detail")))} |'
            )
        add("")
        for edge in open_conflicts:
            evidence = edge.get("evidence") or []
            if not evidence:
                continue
            add(f'**{edge["from"]} ↔ {edge["to"]} — evidence**')
            add("")
            for item in evidence:
                add(f"- {_oneline(item)}")
            add("")

    # --- layers -------------------------------------------------------------
    add("---")
    add("")
    add("## Layers")
    add("")
    for layer in LAYER_ORDER:
        members = by_type.get(layer, [])
        if not members:
            continue
        add(f"### {layer.title()}")
        add("")
        add("| Id | Name | Statement | Source | State |")
        add("|:--|:--|:--|:--|:--|")
        for node in members:
            source = _esc(node.get("source"))
            anchor = node.get("anchor")
            source_cell = f"`{source}`" + (f" · {_esc(anchor)}" if anchor else "")
            add(
                f'| `{node["id"]}` | {_esc(node.get("name"))} '
                f'| {_esc(_oneline(node.get("statement")))} | {source_cell} '
                f'| {STATUS_MARK.get(node.get("status"), _esc(node.get("status")))} |'
            )
        add("")

    # --- grounding crosswalk ------------------------------------------------
    add("---")
    add("")
    add("## Grounding crosswalk")
    add("")
    add("For each principle: what it grounds, and what mechanically enforces it. A principle")
    add("with no enforcing gate is honoured by convention, which is a thing worth seeing.")
    add("")
    add("| Principle | Grounds | Enforced by |")
    add("|:--|:--|:--|")
    for node in by_type.get("principle", []):
        pid = node["id"]
        grounded = [e["to"] for e in edges if e.get("rel") == "grounds" and e.get("from") == pid]
        enforcers = [e["from"] for e in edges if e.get("rel") == "enforces" and e.get("to") == pid]
        enforcer_cells = []
        for gid in enforcers:
            status = by_id.get(gid, {}).get("status")
            mark = " ⚠️" if status == "CITED_NOT_IMPLEMENTED" else ""
            enforcer_cells.append(f"`{gid}`{mark}")
        add(
            f"| `{pid}` {_esc(node.get('name'))} "
            f"| {', '.join(f'`{g}`' for g in grounded) or '—'} "
            f"| {', '.join(enforcer_cells) or '— convention only'} |"
        )
    add("")

    # --- validator report ---------------------------------------------------
    add("---")
    add("")
    add("## Validator report")
    add("")
    add("Produced by `python3 tools/intent_graph_v1_0.py check`.")
    add("")
    if errors:
        add(f"**{len(errors)} error(s)** — merge-blocking:")
        add("")
        for item in errors:
            add(f"- {item}")
        add("")
    else:
        add("No errors: every node resolves to a path in the tree, every objective reaches")
        add("the vision, every objective and gate is grounded, and every open contradiction")
        add("names a candidate.")
        add("")
    if warnings:
        add(f"**{len(warnings)} warning(s)** — reported, not blocking:")
        add("")
        for item in warnings:
            add(f"- {item}")
        add("")

    add("---")
    add("")
    add("## How to use this with the other side")
    add("")
    add("- **Night (Z2)** edits meaning in `INTENT_GRAPH.yaml`: node statements, `status`,")
    add("  and the resolution of a `conflicts_with` row. Those are decisions.")
    add("- **Claude (Z1)** edits structure: proposes edges, keeps `source` honest, files a")
    add("  new `conflicts_with` row the moment it reads two artifacts that disagree, and")
    add("  regenerates this page.")
    add("- **Neither** hand-edits this file.")
    add("")
    add("The exchange that previously needed a session — *does this still ground out in")
    add("anything we said we believed?* — is `trace <node-id>`.")
    add("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# trace
# ---------------------------------------------------------------------------


def trace(graph: dict, node_id: str) -> str:
    nodes = {n["id"]: n for n in _nodes(graph) if n.get("id")}
    if node_id not in nodes:
        return f"no such node: {node_id}"
    edges = _edges(graph)
    node = nodes[node_id]

    lines = [
        f"{node_id} — {node.get('name')}  [{node.get('type')} · {node.get('status')}]",
        f"  source: {node.get('source')}",
        f"  {_oneline(node.get('statement'))}",
        "",
    ]

    def show(title: str, rows: list[str]) -> None:
        lines.append(f"  {title}:")
        lines.extend(f"    {row}" for row in (rows or ["—"]))
        lines.append("")

    show(
        "grounded by",
        [f"{e['from']} ({nodes[e['from']].get('name')})"
         for e in edges if e.get("rel") == "grounds" and e.get("to") == node_id],
    )
    show(
        "measured by",
        [f"{e['from']} ({nodes[e['from']].get('source')})"
         for e in edges if e.get("rel") == "measures" and e.get("to") == node_id],
    )
    show(
        "realizes",
        [f"{e['to']} ({nodes[e['to']].get('name')})"
         for e in edges if e.get("rel") == "realizes" and e.get("from") == node_id],
    )
    conflicts = [
        e for e in edges
        if e.get("rel") == "conflicts_with" and node_id in (e.get("from"), e.get("to"))
    ]
    show(
        "conflicts",
        [f"[{e.get('status')}] with {e['to'] if e['from'] == node_id else e['from']} "
         f"— {e.get('q_ref', 'UNFILED')}: {_oneline(e.get('detail'))}"
         for e in conflicts],
    )
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# smoke test
# ---------------------------------------------------------------------------

_FIXTURE = """
version: 1
node_types: {vision: v, objective: o, principle: p, gate: g, instrument: i}
edge_types: {realizes: r, grounds: g, measures: m, enforces: e, conflicts_with: c}
nodes:
  - {id: V, type: vision, name: V, source: README.md, status: LIVE}
  - {id: P, type: principle, name: P, source: README.md, status: LIVE}
  - {id: O, type: objective, name: O, source: README.md, status: LIVE}
  - {id: I, type: instrument, name: I, source: README.md, status: LIVE}
edges:
  - {from: O, to: V, rel: realizes}
  - {from: P, to: O, rel: grounds}
  - {from: I, to: O, rel: measures}
"""


def run_smoke_test() -> int:
    failures: list[str] = []

    def check(label: str, condition: bool) -> None:
        print(f"  {'PASS' if condition else 'FAIL'}  {label}")
        if not condition:
            failures.append(label)

    print("intent_graph smoke test")

    base = yaml.safe_load(_FIXTURE)
    errors, warnings = validate(base, root=ROOT)
    check("clean fixture validates", errors == [])
    check("clean fixture has no warnings", warnings == [])

    # E3 — a source that is not in the tree is fatal, not cosmetic.
    drifted = yaml.safe_load(_FIXTURE)
    drifted["nodes"][2]["source"] = "does/not/exist.md"
    errors, _ = validate(drifted, root=ROOT)
    check("unresolved source is an error", any(e.startswith("E3") for e in errors))

    # E6 — an objective that reaches nothing is an orphan.
    orphan = yaml.safe_load(_FIXTURE)
    orphan["edges"] = [e for e in orphan["edges"] if e["rel"] != "realizes"]
    errors, _ = validate(orphan, root=ROOT)
    check("ungrounded objective is an orphan", any(e.startswith("E6") for e in errors))

    # E7 — ungrounded objective.
    ungrounded = yaml.safe_load(_FIXTURE)
    ungrounded["edges"] = [e for e in ungrounded["edges"] if e["rel"] != "grounds"]
    errors, _ = validate(ungrounded, root=ROOT)
    check("objective with no principle is an error", any(e.startswith("E7") for e in errors))

    # E8 — an open conflict with no candidate is refused.
    unfiled = yaml.safe_load(_FIXTURE)
    unfiled["nodes"].append({"id": "O2", "type": "objective", "name": "O2",
                             "source": "README.md", "status": "CONFLICTED"})
    unfiled["nodes"][2]["status"] = "CONFLICTED"
    unfiled["edges"] += [
        {"from": "O2", "to": "V", "rel": "realizes"},
        {"from": "P", "to": "O2", "rel": "grounds"},
        {"from": "O", "to": "O2", "rel": "conflicts_with", "status": "OPEN"},
    ]
    errors, _ = validate(unfiled, root=ROOT)
    check("open conflict without q_ref is an error", any(e.startswith("E8") for e in errors))

    # E9 — a conflicted node must declare it.
    undeclared = yaml.safe_load(_FIXTURE)
    undeclared["nodes"].append({"id": "O2", "type": "objective", "name": "O2",
                                "source": "README.md", "status": "LIVE"})
    undeclared["edges"] += [
        {"from": "O2", "to": "V", "rel": "realizes"},
        {"from": "P", "to": "O2", "rel": "grounds"},
        {"from": "O", "to": "O2", "rel": "conflicts_with", "status": "OPEN", "q_ref": "Q-X"},
    ]
    errors, _ = validate(undeclared, root=ROOT)
    check("undeclared conflicted status is an error", any(e.startswith("E9") for e in errors))

    # E11 — a misspelled status must not read as "not CONFLICTED".
    typo = yaml.safe_load(_FIXTURE)
    typo["nodes"][2]["status"] = "PROPOSD"
    errors, _ = validate(typo, root=ROOT)
    check("misspelled status is an error", any(e.startswith("E11") for e in errors))

    # E12 — a correctly spelled rel pointing the wrong way reverses the meaning.
    reversed_edge = yaml.safe_load(_FIXTURE)
    reversed_edge["edges"] = [
        {"from": "O", "to": "P", "rel": "grounds"} if e["rel"] == "grounds" else e
        for e in reversed_edge["edges"]
    ]
    errors, _ = validate(reversed_edge, root=ROOT)
    check("reversed `grounds` edge is an error", any(e.startswith("E12") for e in errors))

    # W4 — vision cardinality is reported, not enforced.
    two_visions = yaml.safe_load(_FIXTURE)
    two_visions["nodes"].append({"id": "V2", "type": "vision", "name": "V2",
                                 "source": "README.md", "status": "LIVE"})
    errors, warnings = validate(two_visions, root=ROOT)
    check("second vision warns but does not block",
          errors == [] and any(w.startswith("W4") for w in warnings))

    # W5 — a type the graph declares that the validator cannot reason about.
    widened = yaml.safe_load(_FIXTURE)
    widened["node_types"]["ritual"] = "a type the validator knows nothing about"
    _, warnings = validate(widened, root=ROOT)
    check("undeclared-to-validator node type warns", any(w.startswith("W5") for w in warnings))

    # A duplicate mapping key must raise, not silently drop the first block.
    duped = "version: 1\nnodes: []\nnodes: []\n"
    try:
        yaml.load(duped, Loader=StrictLoader)
        check("duplicate mapping key is refused", False)
    except yaml.constructor.ConstructorError as exc:
        check("duplicate mapping key is refused", "duplicate key" in str(exc))
    if yaml.safe_load(duped).get("nodes") != []:  # pragma: no cover - tripwire
        check("safe_load still takes the last duplicate; revisit StrictLoader", False)

    # E3 must refuse a source that leaves the tree, however it is spelled.
    for label, escape in (("absolute", "/etc/passwd"),
                          ("parent-climbing", "../../../../etc/passwd")):
        escaped = yaml.safe_load(_FIXTURE)
        escaped["nodes"][2]["source"] = escape
        errors, _ = validate(escaped, root=ROOT)
        check(f"{label} source path is refused",
              any(e.startswith("E3") and "escapes" in e for e in errors))

    # E10 — a temporal control in the graph's own voice is refused...
    leaky = yaml.safe_load(_FIXTURE)
    leaky["nodes"][2]["statement"] = "Work is overdue when the review interval elapses."
    errors, _ = validate(leaky, root=ROOT)
    check("temporal control in node text is an error", any(e.startswith("E10") for e in errors))

    # ...unless it is classified, and...
    classified = yaml.safe_load(_FIXTURE)
    classified["nodes"][2]["statement"] = "Records an overdue flag for provenance."
    classified["nodes"][2]["temporal_class"] = "HISTORICAL_RECORD"
    errors, _ = validate(classified, root=ROOT)
    check("classified temporal reference is allowed", not any(e.startswith("E10") for e in errors))

    # ...a conflicts_with row may quote the defect it reports without tripping it.
    quoting = yaml.safe_load(_FIXTURE)
    quoting["nodes"].append({"id": "O2", "type": "objective", "name": "O2",
                             "source": "README.md", "status": "LIVE"})
    quoting["nodes"][2]["status"] = "CONFLICTED"
    quoting["edges"] += [
        {"from": "O2", "to": "V", "rel": "realizes"},
        {"from": "P", "to": "O2", "rel": "grounds"},
        {"from": "O", "to": "O2", "rel": "conflicts_with", "status": "OPEN", "q_ref": "Q-X",
         "detail": "renders documents visibly overdue once the interval elapses"},
    ]
    errors, _ = validate(quoting, root=ROOT)
    check("conflicts_with row may quote a prohibited control", errors == [])

    # W2 — missing measurement is a warning, not a block.
    unmeasured = yaml.safe_load(_FIXTURE)
    unmeasured["edges"] = [e for e in unmeasured["edges"] if e["rel"] != "measures"]
    errors, warnings = validate(unmeasured, root=ROOT)
    check("unmeasured objective warns but does not block",
          errors == [] and any(w.startswith("W2") for w in warnings))

    # E10 must not be weaker than the scanner it stands in for. Anything the gate
    # would flag on a diff line, E10 flags in node text — checked against the
    # gate's own patterns rather than a copy of them, so the two cannot drift
    # apart silently. One-directional on purpose: E10 being stricter is fine.
    try:
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from tests.test_temporal_dissolution_gate import is_risky as gate_is_risky
    except Exception as exc:  # pragma: no cover - reported, not raised
        check(f"gate patterns importable for parity check ({exc})", False)
    else:
        corpus = [
            "complete_within: 48h",
            "respond_within: 30 seconds",
            "window_end: 2026-10-01T00:00:00Z",
            "start_after: 2026-10-01",
            "due_at: 2026-10-01",
            "due by 2026-10-01",
            "deadline on Friday",
            "this row is overdue",
            "must respond within 2d",
            "shall complete within 48 hours",
            "schedule: 0 0 * * *",
            "cron: 5 4 * * *",
        ]
        gate_flags = [s for s in corpus if gate_is_risky(s)]
        missed = [s for s in gate_flags
                  if not any(p.search(s) for p in TEMPORAL_RISK)]
        check(f"E10 catches everything the gate catches ({len(gate_flags)} samples)",
              missed == [])
        if missed:
            for sample in missed:
                print(f"        gate flags, E10 misses: {sample!r}")

    # This module is exempt from the line scanner in
    # tests/test_temporal_dissolution_gate.py because its E10 fixtures must quote
    # the patterns they detect. That exemption is only safe while the tool reads
    # no clock, so the claim is a test rather than a comment.
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_source = handle.read()
    clock_imports = re.findall(r"^\s*(?:import|from)\s+(time|datetime|calendar)\b",
                               own_source, re.M)
    check("tool reads no clock (no time/datetime/calendar import)", clock_imports == [])

    # Render must be deterministic — CI --check depends on it.
    first = render(base, [], [])
    second = render(base, [], [])
    check("render is deterministic", first == second)
    check("render emits a mermaid canvas", "```mermaid" in first)

    # The real graph must load and render.
    try:
        live = load()
        render(live, *validate(live))
        check("INTENT_GRAPH.yaml loads and renders", True)
    except Exception as exc:  # pragma: no cover - reported, not raised
        check(f"INTENT_GRAPH.yaml loads and renders ({exc})", False)

    print(f"\n{'OK' if not failures else str(len(failures)) + ' FAILED'}")
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("command", nargs="?", default="check",
                        choices=["check", "render", "trace"])
    parser.add_argument("node", nargs="?", help="node id, for `trace`")
    parser.add_argument("--input", default=GRAPH, metavar="PATH",
                        help="graph to read (default: INTENT_GRAPH.yaml). A graph "
                             "other than the default renders to stdout instead of "
                             "overwriting the canonical page.")
    parser.add_argument("--check", action="store_true",
                        help="with `render`: exit 1 if INTENT_GRAPH.md is out of sync")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    graph = load(args.input)
    errors, warnings = validate(graph)
    # Only the canonical graph owns the canonical page; anything else prints.
    is_default = os.path.realpath(args.input) == os.path.realpath(GRAPH)

    if args.command == "trace":
        if not args.node:
            print("trace needs a node id", file=sys.stderr)
            return 2
        known = {n.get("id") for n in _nodes(graph)}
        if args.node not in known:
            # Exit nonzero: a typo'd id previously printed "no such node" and
            # returned success, so a script asking "is this grounded?" read a
            # missing node as a clean answer.
            print(f"no such node: {args.node}", file=sys.stderr)
            return 1
        print(trace(graph, args.node))
        return 0

    if args.command == "check":
        for item in warnings:
            print(f"::warning::{item}")
        for item in errors:
            print(f"::error::{item}")
        print(f"{len(_nodes(graph))} nodes, {len(_edges(graph))} edges, "
              f"{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1 if errors else 0

    # render
    text = render(graph, errors, warnings)
    if not is_default:
        if args.check:
            print("::error::--check compares the canonical page; it needs the "
                  "default --input", file=sys.stderr)
            return 2
        sys.stdout.write(text)
        return 1 if errors else 0
    if args.check:
        current = ""
        if os.path.exists(OUTPUT):
            with open(OUTPUT, encoding="utf-8") as handle:
                current = handle.read()
        if current != text:
            print("::error::INTENT_GRAPH.md is out of sync with INTENT_GRAPH.yaml "
                  "(run: python3 tools/intent_graph_v1_0.py render)")
            return 1
        print("INTENT_GRAPH.md in sync")
        return 0

    with open(OUTPUT, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"wrote {os.path.relpath(OUTPUT, ROOT)} "
          f"({len(_nodes(graph))} nodes, {len(_edges(graph))} edges, "
          f"{len(errors)} error(s), {len(warnings)} warning(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
