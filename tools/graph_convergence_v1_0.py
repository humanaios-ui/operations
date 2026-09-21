#!/usr/bin/env python3
"""
graph_convergence_v1_0.py — grade convergence between two agent-authored graphs.
Builder v1.7 compliant
HumanAIOS — Q-GRAPH-CONVERGENCE-01

Answers Night's question: "do we have a mechanism for determining INDEPENDENT
convergence, and graphing it? Would divergence be useful?"

The mechanism is not similarity. Two agents reading the same repository and
agreeing are not two witnesses; they are two transcriptions of one document, and
counting that as agreement manufactures confidence out of a single source. So
this tool grades every declared correspondence by SOURCE DISJOINTNESS and by the
access record, and reports a corroboration weight that is zero whenever the two
sides could have got the answer from the same place.

  check                  validate GRAPH_ALIGNMENT.yaml; exit 1 on any error
  grade                  print the convergence/divergence table
  render                 write GRAPH_CONVERGENCE.md
  render --check         exit 1 if GRAPH_CONVERGENCE.md is out of sync (CI mode)
  --alignment <path>     read an alignment other than GRAPH_ALIGNMENT.yaml;
                         renders to stdout so a candidate cannot overwrite the
                         canonical page
  --smoke-test           self-check on fixtures; no filesystem writes

What it does NOT do: it does not decide which graph is right, and it cannot
promote a pair to INDEPENDENT. Independence is computed from the declared source
sets and the declared access record. An author asserting its own independence is
precisely the claim this grading exists to check, so there is no field it could
write to assert it.

TEMPORAL POSITION (Q-TEMPORAL-DISSOLUTION-01)
This tool reads no clock. `ordering` is a causal record — which artifact existed
before which — not a schedule. No grade improves or decays because time passed.

GRADES (and why each weight is what it is)
  INDEPENDENT        1.0   disjoint sources AND the later author could not reach
                           the earlier graph. Two methods arriving separately.
  SEQUENTIAL_UNREAD  0.3   disjoint sources, but the earlier graph was reachable
                           and the later author asserts it did not read it. An
                           agent's claim about its own reading is not checkable
                           from the tree, so this is discounted, not trusted.
  SHARED_SOURCE      0.0   the two nodes cite a source in common, directly or
                           through declared lineage. Agreement is transcription.
                           This is the common case here and it is the finding,
                           not a defect in the tool.
  UNSOURCED          0.0   one side's derivation was never recorded. Unknown
                           provenance is not independence: a node nobody can
                           trace cannot corroborate anything.
  CONTAMINATED       0.0   the later author read the earlier graph.
  BACKFILL_UNGRADED  0.0   asserted after the fact by an author who already knew
                           the outcome. Counts for coverage, never for evidence.
  NOT_CONVERGENCE    0.0   a FALSE_FRIEND row. Recorded so it is not re-aligned.

VALIDATION RULES (all mechanical, all re-runnable)
  A1  every alignment endpoint names a node that exists in its graph
  A2  no node pair is aligned twice
  A3  every declared source path resolves in the tree; absolute and escaping
      paths are refused
  A4  every alignment kind and divergence class is in the vocabulary
  A5  every alignment and divergence row carries a non-empty basis
  A6  a BACKFILL row may not be graded INDEPENDENT or SEQUENTIAL_UNREAD
  A7  every graph declares an explicit access grade toward the other
  A8  a relation alignment names rels that exist in both vocabularies
  A9  a FALSE_FRIEND row contributes no corroboration weight
  A10 a divergence row names at least one side
  A11 the two graphs have distinct `ordering` values
  A12 every source_lineage path resolves in the tree and the closure terminates
  W1  an EVIDENCE node with no source_map entry is reported. It cannot be
      graded above UNSOURCED, so an under-populated map costs coverage rather
      than inflating independence.
  W2  a node in either graph that no alignment row and no divergence row mentions
      is reported as uncompared
  W3  total corroboration weight of 0.0 is reported: the comparison found no
      independent agreement at all
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

TOOL_NAME = "graph_convergence"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-092126-graph-convergence"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIGNMENT = "GRAPH_ALIGNMENT.yaml"
RENDER_TARGET = "GRAPH_CONVERGENCE.md"

ALIGNMENT_KINDS = {"SAME_REFERENT", "RELATED", "FALSE_FRIEND"}
DIVERGENCE_CLASSES = {"COVERAGE_GAP", "ONTOLOGY_DIVERGENCE", "CONTRADICTION"}
RELATION_KINDS = {"SAME", "PARTIAL"}
ACCESS_GRADES = {"UNAVAILABLE", "AVAILABLE_UNREAD_ASSERTED", "READ"}

GRADE_WEIGHT = {
    "INDEPENDENT": 1.0,
    "SEQUENTIAL_UNREAD": 0.3,
    "SHARED_SOURCE": 0.0,
    "UNSOURCED": 0.0,
    "CONTAMINATED": 0.0,
    "BACKFILL_UNGRADED": 0.0,
    "NOT_CONVERGENCE": 0.0,
}

GRADE_NOTE = {
    "INDEPENDENT": "disjoint sources; earlier graph unreachable",
    "SEQUENTIAL_UNREAD": "disjoint sources; reachable, author asserts unread",
    "SHARED_SOURCE": "cites a source in common — transcription, not agreement",
    "UNSOURCED": "one side's derivation was never recorded",
    "CONTAMINATED": "later author read the earlier graph",
    "BACKFILL_UNGRADED": "asserted after the outcome was known",
    "NOT_CONVERGENCE": "declared FALSE_FRIEND",
}


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys instead of silently
    keeping the last one. A duplicate key in an alignment file would drop a
    declared row before any validation rule could see it."""


def _no_duplicates(loader: yaml.Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


# ---------------------------------------------------------------------------
# loading and adapters
# ---------------------------------------------------------------------------

def load_alignment(path: str = ALIGNMENT, root: str = ROOT) -> dict[str, Any]:
    with open(os.path.join(root, path) if not os.path.isabs(path) else path,
              encoding="utf-8") as fh:
        return yaml.load(fh, Loader=StrictLoader) or {}


def _resolve_in_tree(source: str, root: str) -> str | None:
    """Resolve a declared source path inside the tree, or None.

    Refuses absolute paths and any path escaping the root. Mirrors E3 in
    tools/intent_graph_v1_0.py; the two rules must stay the same shape, because
    a source that escapes the tree cannot be re-checked by a later reader.
    """
    if not source or os.path.isabs(source):
        return None
    candidate = os.path.normpath(os.path.join(root, source))
    if not (candidate == root or candidate.startswith(root + os.sep)):
        return None
    return candidate if os.path.exists(candidate) else None


def source_closure(sources: list[str], lineage: dict[str, list[str]]) -> set[str]:
    """Expand a source set over declared lineage.

    Path-level disjointness under-detects the shared-source case: CLAUDE.md and
    WITNESS_SERVICE_CONTRACT.md are different files, and the second derives its
    serial-gate and falsifier language from the first. Two nodes citing them
    separately are still reading one doctrine. `source_lineage` in
    GRAPH_ALIGNMENT.yaml declares those derivations, and this expands each node's
    sources to their closure before the intersection is taken.

    Cycle-safe: a lineage loop terminates on the visited set rather than
    recursing, so a malformed declaration cannot hang the tool (A12).
    """
    seen: set[str] = set()
    stack = list(sources)
    while stack:
        src = stack.pop()
        if src in seen:
            continue
        seen.add(src)
        stack.extend(lineage.get(src) or [])
    return seen


def adapt_intent(path: str, root: str) -> dict[str, dict]:
    """INTENT_GRAPH.yaml -> {node_id: {label, sources, rels}}.

    Sources come off the artifact itself: every intent node carries `source`.
    """
    with open(os.path.join(root, path), encoding="utf-8") as fh:
        graph = yaml.load(fh, Loader=StrictLoader) or {}
    out: dict[str, dict] = {}
    for node in graph.get("nodes") or []:
        src = node.get("source")
        out[node["id"]] = {
            "label": node.get("statement") or node.get("label") or node["id"],
            "sources": [src] if src else [],
            "type": node.get("type", ""),
            "provenance": node.get("provenance", ""),
        }
    rels = {e.get("rel") for e in (graph.get("edges") or []) if e.get("rel")}
    return {"nodes": out, "rels": rels}


def adapt_evidence(path: str, root: str, source_map: dict) -> dict[str, dict]:
    """EVIDENCE_GRAPH.json -> the same shape.

    This graph carries no per-node source, so sources come from the declared
    source_map in GRAPH_ALIGNMENT.yaml. That is Z1 attributing sources to
    another agent's nodes and is flagged as such by W1.
    """
    with open(os.path.join(root, path), encoding="utf-8") as fh:
        graph = json.load(fh)
    out: dict[str, dict] = {}
    for node in graph.get("nodes") or []:
        nid = node["id"]
        out[nid] = {
            "label": node.get("label", nid),
            "sources": list(source_map.get(nid) or []),
            "type": node.get("type", ""),
            "provenance": node.get("provenance", ""),
            "declared_sources": nid in source_map,
        }
    rels = {e.get("relation") for e in (graph.get("edges") or []) if e.get("relation")}
    return {"nodes": out, "rels": rels}


# ---------------------------------------------------------------------------
# grading — mechanical, not a judgment
# ---------------------------------------------------------------------------

def grade_row(row: dict, left: dict, right: dict, later_access: str,
              lineage: dict[str, list[str]] | None = None) -> tuple[str, str]:
    """Return (grade, detail) for one alignment row.

    Order matters. Backfill and FALSE_FRIEND short-circuit before any source
    comparison, because neither is a claim about two methods agreeing.
    """
    if str(row.get("provenance", "")).upper() == "BACKFILL":
        return "BACKFILL_UNGRADED", "row marked provenance: BACKFILL"
    if (left.get("provenance") or "").upper() == "BACKFILL" or \
       (right.get("provenance") or "").upper() == "BACKFILL":
        return "BACKFILL_UNGRADED", "an endpoint node is marked BACKFILL"
    if row.get("kind") == "FALSE_FRIEND":
        return "NOT_CONVERGENCE", "declared FALSE_FRIEND"

    lineage = lineage or {}
    left_src = source_closure(list(left.get("sources") or []), lineage)
    right_src = source_closure(list(right.get("sources") or []), lineage)
    if not left_src or not right_src:
        side = "intent" if not left_src else "evidence"
        return "UNSOURCED", f"{side} side declares no source; provenance unknown"

    overlap = sorted(left_src & right_src)
    if overlap:
        direct = sorted(set(left.get("sources") or []) & set(right.get("sources") or []))
        via = "" if direct else " (via declared lineage)"
        return "SHARED_SOURCE", "shared: " + ", ".join(overlap) + via
    if later_access == "READ":
        return "CONTAMINATED", "later author read the earlier graph"
    if later_access == "AVAILABLE_UNREAD_ASSERTED":
        return "SEQUENTIAL_UNREAD", "reachable; unread is asserted, not shown"
    return "INDEPENDENT", "disjoint sources; earlier graph unreachable"


def _later_access(graphs: list[dict]) -> str:
    """The access grade of the graph authored second, toward the first.

    Only this direction can contaminate: the earlier author could not have read
    an artifact that did not yet exist.
    """
    ordered = sorted(graphs, key=lambda g: g.get("ordering", 0))
    return ((ordered[-1].get("access") or {}).get("grade") or "READ")


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def validate(align: dict, graphs: dict[str, dict], root: str = ROOT
             ) -> tuple[list[str], list[str], list[dict]]:
    errors: list[str] = []
    warnings: list[str] = []

    declared = {g["id"]: g for g in (align.get("graphs") or [])}
    if set(declared) != {"INTENT", "EVIDENCE"}:
        errors.append(f"A7: expected graphs INTENT and EVIDENCE, got {sorted(declared)}")
        return errors, warnings, []

    # A7 / A11
    orderings = []
    for gid, g in declared.items():
        access = g.get("access") or {}
        grade = access.get("grade")
        if grade not in ACCESS_GRADES:
            errors.append(f"A7: graph {gid} access grade {grade!r} not in {sorted(ACCESS_GRADES)}")
        if not str(access.get("basis") or "").strip():
            errors.append(f"A7: graph {gid} declares no basis for its access grade")
        orderings.append(g.get("ordering"))
    if len(set(orderings)) != len(orderings):
        errors.append(f"A11: graphs share an ordering value: {orderings}")

    # A3 — every declared source resolves
    for gid, data in graphs.items():
        for nid, node in data["nodes"].items():
            for src in node["sources"]:
                if _resolve_in_tree(src, root) is None:
                    errors.append(f"A3: {gid}.{nid} source {src!r} does not resolve in the tree")

    # W1 — evidence nodes with no declared sources
    for nid, node in graphs["EVIDENCE"]["nodes"].items():
        if not node.get("declared_sources"):
            warnings.append(f"W1: EVIDENCE.{nid} has no source_map entry; an empty "
                            f"source set is disjoint from everything and inflates independence")

    # A8 — relation vocabulary
    for rel in align.get("relations") or []:
        if rel.get("kind") not in RELATION_KINDS:
            errors.append(f"A4: relation kind {rel.get('kind')!r} not in {sorted(RELATION_KINDS)}")
        if rel.get("intent") not in graphs["INTENT"]["rels"]:
            errors.append(f"A8: relation {rel.get('intent')!r} is not used in INTENT_GRAPH.yaml")
        if rel.get("evidence") not in graphs["EVIDENCE"]["rels"]:
            errors.append(f"A8: relation {rel.get('evidence')!r} is not used in EVIDENCE_GRAPH.json")
        if not str(rel.get("basis") or "").strip():
            errors.append(f"A5: relation {rel.get('intent')}/{rel.get('evidence')} has no basis")

    # A12 — lineage paths must resolve, same rule as A3
    lineage: dict[str, list[str]] = {}
    for row in align.get("source_lineage") or []:
        src = row.get("source")
        derives = list(row.get("derives_from") or [])
        for path in [src] + derives:
            if _resolve_in_tree(path or "", root) is None:
                errors.append(f"A12: source_lineage path {path!r} does not resolve in the tree")
        if not str(row.get("basis") or "").strip():
            errors.append(f"A5: source_lineage row for {src!r} carries no basis")
        lineage.setdefault(src, []).extend(derives)

    later = _later_access(list(declared.values()))
    seen: set[tuple[str, str]] = set()
    graded: list[dict] = []
    mentioned: set[tuple[str, str]] = set()

    for row in align.get("alignments") or []:
        i, e = row.get("intent"), row.get("evidence")
        if row.get("kind") not in ALIGNMENT_KINDS:
            errors.append(f"A4: alignment kind {row.get('kind')!r} not in {sorted(ALIGNMENT_KINDS)}")
        if not str(row.get("basis") or "").strip():
            errors.append(f"A5: alignment {i}<->{e} carries no basis")
        if i not in graphs["INTENT"]["nodes"]:
            errors.append(f"A1: alignment names INTENT node {i!r}, which does not exist")
            continue
        if e not in graphs["EVIDENCE"]["nodes"]:
            errors.append(f"A1: alignment names EVIDENCE node {e!r}, which does not exist")
            continue
        if (i, e) in seen:
            errors.append(f"A2: pair {i}<->{e} is aligned more than once")
            continue
        seen.add((i, e))
        mentioned.add(("INTENT", i))
        mentioned.add(("EVIDENCE", e))

        grade, detail = grade_row(row, graphs["INTENT"]["nodes"][i],
                                  graphs["EVIDENCE"]["nodes"][e], later, lineage)
        weight = GRADE_WEIGHT[grade]

        # A6 — backfill can never be independent. Defence in depth: grade_row
        # short-circuits on BACKFILL, so reaching this branch means the grading
        # order was changed and the rule must fail loudly rather than silently.
        if str(row.get("provenance", "")).upper() == "BACKFILL" and \
                grade in {"INDEPENDENT", "SEQUENTIAL_UNREAD"}:
            errors.append(f"A6: backfilled row {i}<->{e} graded {grade}; "
                          f"a backfilled assertion is not a witness")
        # A9 — a false friend must not carry weight
        if row.get("kind") == "FALSE_FRIEND" and weight != 0.0:
            errors.append(f"A9: FALSE_FRIEND row {i}<->{e} carries weight {weight}")

        graded.append({"intent": i, "evidence": e, "kind": row["kind"],
                       "grade": grade, "weight": weight, "detail": detail,
                       "basis": row.get("basis", "")})

    for row in align.get("divergences") or []:
        if row.get("class") not in DIVERGENCE_CLASSES:
            errors.append(f"A4: divergence class {row.get('class')!r} not in {sorted(DIVERGENCE_CLASSES)}")
        if not str(row.get("basis") or "").strip():
            errors.append(f"A5: divergence {row.get('class')} carries no basis")
        if row.get("intent") is None and row.get("evidence") is None:
            errors.append("A10: divergence row names neither side")
        for gid, key in (("INTENT", "intent"), ("EVIDENCE", "evidence")):
            val = row.get(key)
            if val and val in graphs[gid]["nodes"]:
                mentioned.add((gid, val))

    # W2 — coverage. Reported as one line per graph: a warning per uncompared
    # node buries the graded table under noise, and the number is the finding.
    for gid, data in sorted(graphs.items()):
        uncompared = [n for n in data["nodes"] if (gid, n) not in mentioned]
        if uncompared:
            shown = ", ".join(uncompared[:6])
            more = f" (+{len(uncompared) - 6} more)" if len(uncompared) > 6 else ""
            warnings.append(
                f"W2: {gid} coverage {len(data['nodes']) - len(uncompared)}/"
                f"{len(data['nodes'])} nodes compared; uncompared: {shown}{more}")

    total = sum(r["weight"] for r in graded)
    if graded and total == 0.0:
        warnings.append("W3: total corroboration weight is 0.0 — this comparison "
                        "found no independent agreement. Every aligned pair shares "
                        "a source, has unrecorded provenance, was read, or is a "
                        "declared false friend.")

    return errors, warnings, graded


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------

def _esc(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _oneline(text: object) -> str:
    return " ".join(str(text).split())


def grade_report(align: dict, graded: list[dict], errors: list[str],
                 warnings: list[str]) -> str:
    lines = [f"{TOOL_NAME} v{TOOL_VERSION} — {len(graded)} aligned pairs"]
    for row in graded:
        lines.append(f"  {row['intent']:<22} <-> {row['evidence']:<4} "
                     f"{row['kind']:<13} {row['grade']:<18} w={row['weight']:.1f}  {row['detail']}")
    total = sum(r["weight"] for r in graded)
    lines.append(f"  {'TOTAL CORROBORATION WEIGHT':<45} {total:.1f}")
    for w in warnings:
        lines.append(f"  ::warning:: {w}")
    for e in errors:
        lines.append(f"  ::error:: {e}")
    return "\n".join(lines)


def render(align: dict, graphs: dict[str, dict], graded: list[dict],
           errors: list[str], warnings: list[str]) -> str:
    declared = {g["id"]: g for g in (align.get("graphs") or [])}
    total = sum(r["weight"] for r in graded)
    n_ind = sum(1 for r in graded if r["grade"] == "INDEPENDENT")

    out: list[str] = []
    A = out.append
    A("<!-- GENERATED by tools/graph_convergence_v1_0.py — do not edit by hand. -->")
    A(f"<!-- Source of truth: {ALIGNMENT}. Regenerate: "
      f"python3 tools/graph_convergence_v1_0.py render -->")
    A("")
    A("# GRAPH_CONVERGENCE — what two agent-authored graphs actually agree on")
    A("")
    A(f"**Candidate:** {align.get('q_id', '—')} · **Status:** {align.get('status', '—')}")
    A("")
    A("## Headline")
    A("")
    A(f"- Aligned pairs: **{len(graded)}**")
    A(f"- Graded INDEPENDENT: **{n_ind}**")
    A(f"- Total corroboration weight: **{total:.1f}**")
    A(f"- Declared divergences: **{len(align.get('divergences') or [])}**")
    A("")
    if total == 0.0:
        A("> Every aligned pair scores zero. That is the result, not a failure of")
        A("> the method: the two agents read the same repository, so where they")
        A("> agree they are both transcribing one source. The comparison's whole")
        A("> signal is in the divergence table below.")
        A("")

    A("## The graphs")
    A("")
    A("| Graph | Author | Path | Authored | Access to the other | Grade |")
    A("|---|---|---|---|---|---|")
    for gid in ("EVIDENCE", "INTENT"):
        g = declared.get(gid, {})
        acc = g.get("access") or {}
        A(f"| {gid} | {_esc(g.get('author'))} | `{_esc(g.get('path'))}` | "
          f"{_esc(g.get('ordering'))} | {_esc(acc.get('to'))} | `{_esc(acc.get('grade'))}` |")
    A("")

    A("## Convergence, graded")
    A("")
    A("Weight is computed, never declared. A pair scores only when the two nodes")
    A("cite no source in common *and* the later author could not reach the earlier")
    A("graph. Anything else is transcription or inheritance.")
    A("")
    A("| Intent | Evidence | Kind | Grade | Weight | Why |")
    A("|---|---|---|---|---|---|")
    for row in graded:
        A(f"| `{row['intent']}` | `{row['evidence']}` | {row['kind']} | "
          f"**{row['grade']}** | {row['weight']:.1f} | {_esc(row['detail'])} |")
    A(f"| | | | **TOTAL** | **{total:.1f}** | |")
    A("")

    A("## Divergence")
    A("")
    A("Under shared sources, agreement is the expected outcome and carries no")
    A("information. Disagreement is the surprise, and it is the only part of this")
    A("comparison that survives the grading above.")
    A("")
    for row in align.get("divergences") or []:
        left = row.get("intent") or "—"
        right = row.get("evidence") or "—"
        A(f"### {row.get('class')} · INTENT `{left}` vs EVIDENCE `{right}`")
        A("")
        A(_oneline(row.get("basis", "")))
        A("")

    A("## Relation vocabularies")
    A("")
    A("| Intent rel | Evidence rel | Kind | Note |")
    A("|---|---|---|---|")
    for rel in align.get("relations") or []:
        A(f"| `{_esc(rel.get('intent'))}` | `{_esc(rel.get('evidence'))}` | "
          f"{_esc(rel.get('kind'))} | {_esc(_oneline(rel.get('basis', '')))} |")
    A("")

    A("## Canvas")
    A("")
    A("```mermaid")
    A("graph LR")
    A("  subgraph EVIDENCE[\"EVIDENCE_GRAPH.json · Copilot\"]")
    for row in graded:
        A(f"    E_{row['evidence']}[\"{row['evidence']}\"]")
    A("  end")
    A("  subgraph INTENT[\"INTENT_GRAPH.yaml · Claude\"]")
    for row in graded:
        A(f"    I_{row['intent'].replace('-', '_')}[\"{row['intent']}\"]")
    A("  end")
    # Edges belong outside both subgraphs: an edge declared inside one adopts
    # that subgraph as its container and the cross-graph link renders wrong.
    for row in graded:
        arrow = {"SAME_REFERENT": "---", "RELATED": "-.-", "FALSE_FRIEND": "-.-"}[row["kind"]]
        A(f"  E_{row['evidence']} {arrow}>|{row['kind']} · {row['grade']} "
          f"w={row['weight']:.1f}| I_{row['intent'].replace('-', '_')}")
    A("```")
    A("")

    if warnings:
        A("## Warnings")
        A("")
        for w in warnings:
            A(f"- {_oneline(w)}")
        A("")
    if errors:
        A("## Errors")
        A("")
        for e in errors:
            A(f"- {_oneline(e)}")
        A("")

    A("## Backfill")
    A("")
    bp = align.get("backfill_policy") or {}
    A(f"Backfilling is permitted (`permitted: {bp.get('permitted')}`) and forced to")
    A(f"`{bp.get('grade_forced')}` at weight {bp.get('weight')}. A backfilled row counts for")
    A("coverage and never for corroboration: its author has already seen how the")
    A("artifact turned out, which makes them a reader of the answer, not a witness.")
    A("")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> int:
    """Fixture-driven self-check. Writes nothing."""
    failures: list[str] = []
    ran = [0]

    def check(name: str, cond: bool) -> None:
        ran[0] += 1
        if not cond:
            failures.append(name)

    # -- grading table -------------------------------------------------------
    shared_l = {"sources": ["A.md"], "provenance": ""}
    shared_r = {"sources": ["A.md", "B.md"], "provenance": ""}
    disjoint_l = {"sources": ["A.md"], "provenance": ""}
    disjoint_r = {"sources": ["B.md"], "provenance": ""}
    empty_r = {"sources": [], "provenance": ""}
    plain = {"kind": "SAME_REFERENT"}

    g, _ = grade_row(plain, shared_l, shared_r, "UNAVAILABLE")
    check("shared sources beat an unavailable access grade", g == "SHARED_SOURCE")

    g, _ = grade_row(plain, disjoint_l, disjoint_r, "UNAVAILABLE")
    check("disjoint + unavailable is INDEPENDENT", g == "INDEPENDENT")

    g, _ = grade_row(plain, disjoint_l, disjoint_r, "AVAILABLE_UNREAD_ASSERTED")
    check("disjoint + asserted-unread is SEQUENTIAL_UNREAD", g == "SEQUENTIAL_UNREAD")

    g, _ = grade_row(plain, disjoint_l, disjoint_r, "READ")
    check("disjoint + read is CONTAMINATED", g == "CONTAMINATED")

    g, _ = grade_row(plain, disjoint_l, empty_r, "UNAVAILABLE")
    check("an undeclared source set is UNSOURCED, not independent", g == "UNSOURCED")

    g, d = grade_row(plain, disjoint_l, disjoint_r, "UNAVAILABLE",
                     {"B.md": ["A.md"]})
    check("declared lineage collapses a disjoint pair to SHARED_SOURCE",
          g == "SHARED_SOURCE" and "via declared lineage" in d)

    check("a lineage cycle terminates",
          source_closure(["A.md"], {"A.md": ["B.md"], "B.md": ["A.md"]}) == {"A.md", "B.md"})

    g, _ = grade_row({"kind": "FALSE_FRIEND"}, disjoint_l, disjoint_r, "UNAVAILABLE")
    check("FALSE_FRIEND never converges", g == "NOT_CONVERGENCE")

    g, _ = grade_row({"kind": "SAME_REFERENT", "provenance": "BACKFILL"},
                     disjoint_l, disjoint_r, "UNAVAILABLE")
    check("a backfilled row cannot be INDEPENDENT", g == "BACKFILL_UNGRADED")

    g, _ = grade_row(plain, {"sources": ["A.md"], "provenance": "BACKFILL"},
                     disjoint_r, "UNAVAILABLE")
    check("a backfilled endpoint node cannot be INDEPENDENT", g == "BACKFILL_UNGRADED")

    check("every grade has a weight", set(GRADE_WEIGHT) == set(GRADE_NOTE))
    check("only INDEPENDENT scores 1.0",
          [k for k, v in GRADE_WEIGHT.items() if v == 1.0] == ["INDEPENDENT"])

    # -- access direction ----------------------------------------------------
    later = _later_access([
        {"ordering": 1, "access": {"grade": "UNAVAILABLE"}},
        {"ordering": 2, "access": {"grade": "READ"}},
    ])
    check("the later-authored graph's access is the one that grades", later == "READ")
    later = _later_access([
        {"ordering": 2, "access": {"grade": "READ"}},
        {"ordering": 1, "access": {"grade": "UNAVAILABLE"}},
    ])
    check("ordering, not list order, picks the later graph", later == "READ")

    # -- path resolution -----------------------------------------------------
    check("absolute source refused", _resolve_in_tree("/etc/passwd", ROOT) is None)
    check("escaping source refused", _resolve_in_tree("../../etc/passwd", ROOT) is None)
    check("empty source refused", _resolve_in_tree("", ROOT) is None)
    check("missing source refused", _resolve_in_tree("no/such/file.md", ROOT) is None)
    check("real source resolves", _resolve_in_tree("CLAUDE.md", ROOT) is not None)

    # -- strict loader -------------------------------------------------------
    try:
        yaml.load("a: 1\na: 2\n", Loader=StrictLoader)
        check("duplicate YAML keys are refused", False)
    except yaml.constructor.ConstructorError:
        check("duplicate YAML keys are refused", True)

    # -- temporal purity -----------------------------------------------------
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        src = fh.read()
    for mod in ("time", "datetime", "calendar"):
        check(f"tool imports no {mod}; it must read no clock",
              not re.search(rf"^\s*(import {mod}\b|from {mod} import)", src, re.M))

    # -- the real files ------------------------------------------------------
    align = load_alignment()
    smap = align.get("source_map") or {}
    graphs = {
        "INTENT": adapt_intent("INTENT_GRAPH.yaml", ROOT),
        "EVIDENCE": adapt_evidence("EVIDENCE_GRAPH.json", ROOT, smap),
    }
    errors, warnings, graded = validate(align, graphs)
    check("the shipped alignment validates", not errors)
    check("the shipped alignment grades at least one pair", bool(graded))
    check("A9 holds on the shipped alignment",
          all(r["weight"] == 0.0 for r in graded if r["kind"] == "FALSE_FRIEND"))
    check("render produces a document", len(render(align, graphs, graded, errors, warnings)) > 500)

    print(f"{TOOL_NAME} smoke test: {ran[0] - len(failures)}/{ran[0]} checks")
    for f in failures:
        print(f"  ::error::{f}")
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="check",
                    choices=["check", "grade", "render"])
    ap.add_argument("--alignment", default=ALIGNMENT,
                    help="read a different alignment file; render goes to stdout")
    ap.add_argument("--check", action="store_true",
                    help="with render: exit 1 if the rendered page is out of sync")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    align = load_alignment(args.alignment)
    smap = align.get("source_map") or {}
    declared = {g["id"]: g for g in (align.get("graphs") or [])}
    try:
        graphs = {
            "INTENT": adapt_intent(declared["INTENT"]["path"], ROOT),
            "EVIDENCE": adapt_evidence(declared["EVIDENCE"]["path"], ROOT, smap),
        }
    except KeyError as exc:
        print(f"::error::alignment does not declare graph {exc}")
        return 2

    errors, warnings, graded = validate(align, graphs)

    if args.command in ("check", "grade"):
        print(grade_report(align, graded, errors, warnings))
        return 1 if errors else 0

    page = render(align, graphs, graded, errors, warnings)
    if args.alignment != ALIGNMENT:
        sys.stdout.write(page)
        return 1 if errors else 0

    target = os.path.join(ROOT, RENDER_TARGET)
    if args.check:
        existing = ""
        if os.path.exists(target):
            with open(target, encoding="utf-8") as fh:
                existing = fh.read()
        if existing != page:
            print(f"::error::{RENDER_TARGET} is out of sync with {ALIGNMENT}; "
                  f"run: python3 tools/{TOOL_NAME}_v1_0.py render")
            return 1
        print(f"{RENDER_TARGET} is in sync")
        return 1 if errors else 0

    with open(target, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote {RENDER_TARGET} ({len(graded)} pairs, "
          f"total weight {sum(r['weight'] for r in graded):.1f})")
    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
