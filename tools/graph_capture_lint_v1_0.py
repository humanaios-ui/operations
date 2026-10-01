#!/usr/bin/env python3
"""
graph_capture_lint_v1_0.py — score a graph file against the nine properties of
a graph that cannot be wrong from the inside.
Builder v1.7 compliant
HumanAIOS — Q-GRAPH-CAPTURE-LINT-01

WHY THIS EXISTS
The most dangerous knowledge graph is not the one that knows the most. It is
the one that cannot be wrong from the inside: every edge cites another edge in
the same graph, nothing can be retracted, nothing carries a time, the proposer
and the ratifier and the executor are one process, and the thing it measures
is the thing it writes. This repository keeps its graphs as a multiplex
(INTENT -> CAPABILITY -> SYSTEM -> EVIDENCE, crb/README.md) precisely so no
single graph can seal itself. This lint is the mechanical check that a graph
file has not quietly acquired those properties.

Three properties block; six advise. The blocking three are the ones that make
a graph unauditable from outside, and the ones every other gate in this repo
already presupposes (falsifier doctrine, IC-030 live-fetch and pin, the STALE
callout's half-lives):

  P1  CLOSED_PROVENANCE      no node cites anything outside the graph, or a
                             chain of support edges is circular with no
                             externally grounded member               BLOCK
  P2  NO_FALSIFIER           no edge relation, node field or declared
                             vocabulary can defeat, retract, contradict or
                             supersede a claim                         BLOCK
  P3  NO_TIMESTAMP           no temporal anchor anywhere: no generated_at /
                             recorded_at / as_of, and no declared
                             temporal_class                            BLOCK
  P4  COLLAPSED_CONFIDENCE   confidence/weight fields exist and are all at
                             the same maximal value; or causal relations
                             carry no uncertainty at all               WARN
  P5  IRREVERSIBLE_MERGE     identity nodes are merged (same_as, aliases,
                             merged_from) with no recorded basis and no
                             split channel                             WARN
  P6  SINGLE_ROLE_AUTHORITY  one identity holds every declared authority
                             role (two or more of proposer, ratifier,
                             executor)                                 WARN
  P7  REFLEXIVE_MEASUREMENT  self-loops, or a measure edge paired with an
                             act/feed edge between the same two nodes  WARN
  P8  OPAQUE_SCHEMA          dangling edge endpoints, relations outside the
                             declared vocabulary, or five or more distinct
                             relations with no vocabulary at all
                             (AD_HOC_RELATION_THRESHOLD)              WARN
  P9  UNVERIFIED             no verification channel on any node or edge
                             (state, tests, validation_status, ...)    WARN

TEMPORAL POSITION (Q-TEMPORAL-DISSOLUTION-01)
P3 asks for an OBSERVATIONAL anchor or an explicit temporal_class, not a
deadline. A HISTORICAL_RECORD graph with `ordering` and no clock passes P3.
This tool reads no clock of its own and nothing here ages.

WHAT IT DOES NOT DO
It does not decide whether a graph is *right*. A graph can pass all nine and
still be wrong; it just cannot be wrong *invisibly*. It does not edit any graph
and it cannot promote a finding to a Z2 decision: a failing canonical graph is
recorded in a baseline file and routed to Z2 as a candidate, not patched by
this tool.

USAGE
  python3 tools/graph_capture_lint_v1_0.py <graph> [<graph> ...]
  python3 tools/graph_capture_lint_v1_0.py --all            canonical graph set
  python3 tools/graph_capture_lint_v1_0.py --all --baseline crb/graph_capture_baseline.json
  --input <path>      alias for a positional path (tool contract, tools/README.md)
  --json              machine-readable report
  --strict            advisory failures also exit 1
  --baseline <path>   accepted debt. A listed failure is reported and does not
                      block; an unlisted blocking failure blocks; a listed
                      property that now passes is a stale entry and blocks
                      until removed, so the baseline only ratchets down.
  --smoke-test        self-check on in-memory fixtures; writes nothing.

EXIT CODES
  0  no blocking failure (and no advisory failure under --strict)
  1  a blocking failure, a stale baseline entry, or --strict advisory failure
  2  usage or parse error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

TOOL_NAME = "graph_capture_lint"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "S-100126-graph-capture-lint"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The multiplex named in crb/README.md. GRAPH_ALIGNMENT.yaml is an alignment
# table between two of these, not a graph, and is graded by its own tool.
CANONICAL_GRAPHS = [
    "INTENT_GRAPH.yaml",
    "system_graph.json",
    "EVIDENCE_GRAPH.json",
    "crb/capability_graph.json",
    "crb/morphogenesis.json",
]

BLOCKING = {"P1", "P2", "P3"}
ADVISORY = {"P4", "P5", "P6", "P7", "P8", "P9"}
PROPERTY_NAMES = {
    "P1": "CLOSED_PROVENANCE",
    "P2": "NO_FALSIFIER",
    "P3": "NO_TIMESTAMP",
    "P4": "COLLAPSED_CONFIDENCE",
    "P5": "IRREVERSIBLE_MERGE",
    "P6": "SINGLE_ROLE_AUTHORITY",
    "P7": "REFLEXIVE_MEASUREMENT",
    "P8": "OPAQUE_SCHEMA",
    "P9": "UNVERIFIED",
}

# ---------------------------------------------------------------------------
# Vocabularies. Lower-cased; matching normalises '-' and ' ' to '_'.
# ---------------------------------------------------------------------------

# Keys whose presence on a node, edge or the top level points OUTSIDE the graph.
EXTERNAL_PROVENANCE_KEYS = {
    "source", "sources", "source_context", "source_map", "source_issue",
    "anchor", "implementation", "existing_refs", "ref", "refs", "citation",
    "citations", "evidence", "evidence_anchor", "evidence_anchors", "path",
    "file", "files", "doc", "document", "url", "href", "derived_from",
    "provenance", "ratification_record", "ratified_by", "classifier",
    "recorded_by", "zone2_ratification", "ruling", "commit", "sha",
}
# A label/name that names a file in the tree is an outward reference too.
FILE_LIKE_RE = re.compile(
    r"(^|[\s/`(])[\w./-]+\.(md|json|jsonl|ya?ml|py|js|ts|sh|sql|html|csv|txt)\b"
)

# Warrant flows source -> destination ("A grounds B": B is warranted by A).
SUPPORT_FORWARD = {
    "supports", "grounds", "implements", "realizes", "evidence_for",
    "justifies", "measures", "verifies", "validates", "tests", "corroborates",
    "supplies_raw_evidence", "supplies_evidence",
}
# Warrant flows destination -> source ("A supported_by B": A is warranted by B).
SUPPORT_BACKWARD = {
    "supported_by", "grounded_in", "grounded_by", "cites", "derived_from",
    "evidenced_by", "justified_by", "based_on", "sourced_from", "depends_on",
    "implemented_by", "realized_by", "measured_by", "verified_by",
}

# A relation is a defeat channel when any of its underscore-separated tokens is
# one of these stems, so `defeats_if_unmitigated` and `conflicts_with` both
# count without enumerating every phrasing.
DEFEAT_STEMS = {
    "conflicts", "contradicts", "contradicted", "defeats", "defeated",
    "falsifies", "falsified", "refutes", "refuted", "supersedes", "superseded",
    "reverts", "reverted", "challenges", "challenged", "corrects", "corrected",
    "retracts", "retracted", "rejects", "rejected", "vetoes", "vetoed",
    "invalidates", "invalidated", "overturns", "overturned",
}


def is_defeat_rel(rel: str) -> bool:
    return any(tok in DEFEAT_STEMS for tok in _norm(rel).split("_"))


# Free-text labels that mention a revert/defeat path. Evidence, not a pass:
# a word in a label is not something a query can select on.
DEFEAT_LABEL_RE = re.compile(
    r"\b(revert|reverted|falsif\w*|retract\w*|contradict\w*|supersede\w*|defeat\w*|refute\w*)\b",
    re.IGNORECASE,
)
DEFEAT_KEYS = {
    "falsifier", "falsifiers", "falsified_if", "defeated_if", "revert_rule",
    "null", "null_hypothesis", "superseded_by", "supersedes", "retraction",
    "retracted", "contradiction", "contradicts", "conflicts_with",
    "challenge", "veto",
}
DEFEAT_STATES = {
    "retracted", "defeated", "falsified", "reverted", "superseded",
    "rejected", "contradicted", "withdrawn",
}

# Anchors only. A duration (half_life, a bare window length) says how long,
# not when, and does not satisfy P3.
TEMPORAL_KEYS = {
    "generated_at", "recorded_at", "as_of", "observed_at", "timestamp",
    "created_at", "updated_at", "last_updated", "date", "date_registered",
    "date_origin", "window_start", "window_end", "ordering",
    "temporal_class", "proposed_at", "ratified_at", "measured_at",
    "valid_from", "valid_until", "since",
}
# On an edge record these name endpoints, not provenance.
ENDPOINT_KEYS = {"from", "to", "source", "target"}

CONFIDENCE_KEYS = {
    "weight", "confidence", "probability", "p", "credence", "certainty",
    "strength", "likelihood", "corroboration_weight",
}
CAUSAL_RELS = {
    "causes", "caused_by", "leads_to", "results_in", "determines",
    "produces_outcome", "drives",
}

IDENTITY_TYPES = {
    "person", "identity", "entity", "individual", "user", "actor", "account",
    "human", "agent_identity", "profile",
}
MERGE_KEYS = {"merged_from", "aliases", "same_as", "also_known_as",
              "canonical_id", "merged_into", "alias_of"}
MERGE_RELS = {"same_as", "merged_into", "alias_of", "identical_to",
              "merged_from", "duplicate_of"}
MERGE_BASIS_KEYS = {"merge_basis", "merge_evidence", "basis", "confidence",
                    "match_evidence", "resolution_basis", "merge_reason"}
SPLIT_KEYS = {"split_from", "split_rule", "unmerge", "unmerged_from",
              "split_into", "demerge"}
SPLIT_RELS = {"split_from", "split_into", "unmerged_from", "demerged_from"}

PROPOSER_KEYS = {"proposer", "proposed_by", "author", "authored_by", "writer",
                 "created_by", "submitted_by"}
RATIFIER_KEYS = {"ratifier", "ratified_by", "approved_by", "authority",
                 "signed_by", "reviewer", "reviewed_by"}
EXECUTOR_KEYS = {"executor", "executed_by", "applied_by", "owner",
                 "deployed_by", "operator"}
UNRATIFIED_MARKERS = {"proposed", "candidate", "draft", "prototype"}

MEASURE_RELS = {
    "measures", "observes", "evaluates", "scores", "verifies", "validates",
    "audits", "confirms", "assesses", "grades", "monitors",
}
ACT_RELS = {
    "triggers", "causes", "produces", "emits", "writes", "applies",
    "generates", "updates", "feeds", "triggers_candidate", "supplies",
    "drives", "executes", "mutates", "sets",
}

VERIFICATION_KEYS = {
    "state", "tests", "validation_status", "verified_by", "brier",
    "measurement", "measurements", "evidence_state", "verification",
    "verified", "observed", "test_count", "catch_rate", "coverage",
}
VERIFICATION_STATES = {
    "observed", "tested", "measured", "verified", "falsified", "operated",
    "implemented",
}

AD_HOC_RELATION_THRESHOLD = 5


def _norm(s: Any) -> str:
    return str(s).strip().lower().replace("-", "_").replace(" ", "_")


# ---------------------------------------------------------------------------
# Loading and normalisation
# ---------------------------------------------------------------------------

@dataclass
class Edge:
    src: str
    dst: str
    rel: str
    raw: dict


@dataclass
class Graph:
    path: str
    doc: Any
    nodes: dict = field(default_factory=dict)      # id -> raw node dict
    edges: list = field(default_factory=list)      # [Edge]
    top: dict = field(default_factory=dict)        # top-level scalars/dicts
    node_vocab: set = field(default_factory=set)   # declared node types
    rel_vocab: set = field(default_factory=set)    # declared relations
    external_ids: dict = field(default_factory=dict)  # id -> path, from sibling graphs


class GraphLoadError(Exception):
    pass


def load_doc(path: str) -> Any:
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise GraphLoadError(f"{path}: cannot read ({exc})") from exc
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - CI installs it
            raise GraphLoadError(f"{path}: PyYAML not installed (pip install pyyaml)") from exc
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise GraphLoadError(f"{path}: YAML does not parse ({exc})") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraphLoadError(f"{path}: JSON does not parse ({exc})") from exc


def _is_edge(item: Any) -> bool:
    return isinstance(item, dict) and (
        ("from" in item and "to" in item) or ("source" in item and "target" in item)
    )


def _is_node(item: Any) -> bool:
    return isinstance(item, dict) and "id" in item and not _is_edge(item)


def _edge_from(item: dict) -> Edge:
    src = item.get("from", item.get("source"))
    dst = item.get("to", item.get("target"))
    rel = None
    for k in ("rel", "relation", "edge_type", "type", "label"):
        if item.get(k) not in (None, ""):
            rel = item[k]
            break
    return Edge(str(src), str(dst), _norm(rel or "unlabeled"), item)


def _declared_vocab(value: Any) -> set:
    """node_types / edge_types may be a list of strings, a list of dicts with
    id/name, or a dict keyed by name."""
    out: set = set()
    if isinstance(value, dict):
        out.update(_norm(k) for k in value)
    elif isinstance(value, list):
        for v in value:
            if isinstance(v, str):
                out.add(_norm(v))
            elif isinstance(v, dict):
                for k in ("id", "name", "rel", "type", "relation"):
                    if v.get(k):
                        out.add(_norm(v[k]))
                        break
    return out


def normalize(path: str, doc: Any) -> Graph:
    g = Graph(path=path, doc=doc)
    if not isinstance(doc, dict):
        raise GraphLoadError(f"{path}: top level is not a mapping")

    def walk(value: Any, depth: int) -> None:
        if depth > 3:
            return
        if isinstance(value, dict):
            if all(_is_node(v) for v in value.values()) and value:
                for v in value.values():
                    g.nodes.setdefault(str(v["id"]), v)
                return
            for v in value.values():
                walk(v, depth + 1)
        elif isinstance(value, list):
            for item in value:
                if _is_edge(item):
                    g.edges.append(_edge_from(item))
                elif _is_node(item):
                    g.nodes.setdefault(str(item["id"]), item)
                elif isinstance(item, (dict, list)):
                    walk(item, depth + 1)

    for key, value in doc.items():
        nk = _norm(key)
        if nk in ("node_types", "node_type_enum"):
            g.node_vocab |= _declared_vocab(value)
        elif nk in ("edge_types", "edge_type_enum", "relations", "relation_types",
                    "rel_types", "rel_enum"):
            g.rel_vocab |= _declared_vocab(value)
        if isinstance(value, (dict, list)):
            walk(value, 1)
        g.top[nk] = value
    return g


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    prop: str
    failed: bool
    message: str
    evidence: list = field(default_factory=list)

    @property
    def name(self) -> str:
        return PROPERTY_NAMES[self.prop]

    @property
    def severity(self) -> str:
        return "BLOCK" if self.prop in BLOCKING else "WARN"

    def as_dict(self) -> dict:
        return {
            "property": self.prop,
            "name": self.name,
            "severity": self.severity,
            "status": "FAIL" if self.failed else "PASS",
            "message": self.message,
            "evidence": list(self.evidence)[:20],
        }


def _items(g: Graph) -> Iterable[tuple[str, dict]]:
    """Every record that can carry fields: top level, nodes, edges."""
    yield "graph", {k: v for k, v in g.top.items() if not isinstance(v, (dict, list))}
    for nid, n in g.nodes.items():
        yield f"node:{nid}", n
    for e in g.edges:
        yield f"edge:{e.src}->{e.dst}", e.raw


def _has_any_key(record: dict, keys: set, nonempty: bool = True) -> list:
    hits = []
    for k, v in record.items():
        if _norm(k) in keys:
            if nonempty and v in (None, "", [], {}):
                continue
            hits.append(_norm(k))
    return hits


def _externally_grounded(record: dict) -> bool:
    if _has_any_key(record, EXTERNAL_PROVENANCE_KEYS):
        return True
    for k in ("label", "name", "implementation", "title"):
        v = record.get(k)
        if isinstance(v, str) and FILE_LIKE_RE.search(v):
            return True
    return False


# --- P1 ---------------------------------------------------------------------

def _outward_reference_in(value: Any, depth: int = 0) -> bool:
    """True if a non-node mapping anywhere under `value` (depth <= 3) carries an
    outward-pointing key or a file-like string. Nodes and edges are scored
    separately; this catches provenance kept in side tables such as
    morphogenesis.json's molt_tier_mapping.classifier."""
    if depth > 3:
        return False
    if isinstance(value, dict):
        if _is_node(value) or _is_edge(value):
            return False
        if _has_any_key(value, EXTERNAL_PROVENANCE_KEYS):
            return True
        for v in value.values():
            if isinstance(v, str) and FILE_LIKE_RE.search(v):
                return True
            if isinstance(v, (dict, list)) and _outward_reference_in(v, depth + 1):
                return True
    elif isinstance(value, list):
        return any(_outward_reference_in(v, depth + 1) for v in value
                   if isinstance(v, (dict, list)))
    return False


def check_closed_provenance(g: Graph) -> Finding:
    top_scalars = {k: v for k, v in g.top.items() if not isinstance(v, (dict, list))}
    top_external = bool(_has_any_key(top_scalars, EXTERNAL_PROVENANCE_KEYS)) or any(
        isinstance(v, (list, dict)) and v and _norm(k) in EXTERNAL_PROVENANCE_KEYS
        for k, v in g.top.items()
    ) or any(_outward_reference_in(v, 1) for v in g.top.values()
             if isinstance(v, (dict, list)))
    grounded = {nid for nid, n in g.nodes.items() if _externally_grounded(n)}
    ext_edges = 0
    for e in g.edges:
        payload = {k: v for k, v in e.raw.items() if _norm(k) not in ENDPOINT_KEYS}
        if _externally_grounded(payload):
            ext_edges += 1
            grounded.add(e.src)
            grounded.add(e.dst)

    # warrant edges, oriented so that warrant flows u -> v
    warrant: list[tuple[str, str]] = []
    for e in g.edges:
        if e.rel in SUPPORT_FORWARD:
            warrant.append((e.src, e.dst))
        elif e.rel in SUPPORT_BACKWARD:
            warrant.append((e.dst, e.src))

    # fixpoint: a node warranted by a grounded node is grounded
    changed = True
    while changed:
        changed = False
        for u, v in warrant:
            if u in grounded and v not in grounded:
                grounded.add(v)
                changed = True

    participants = {u for u, _ in warrant} | {v for _, v in warrant}
    ungrounded = participants - grounded
    # Kahn strip on the ungrounded warrant subgraph: nodes left after removing
    # every in-degree-0 node are inside, or fed only by, a circular chain.
    sub = [(u, v) for u, v in warrant if u in ungrounded and v in ungrounded]
    remaining = set(ungrounded)
    while True:
        indeg = {n: 0 for n in remaining}
        for u, v in sub:
            if u in remaining and v in remaining:
                indeg[v] += 1
        leaves = {n for n, d in indeg.items() if d == 0}
        if not leaves:
            break
        remaining -= leaves
    circular = sorted(remaining)

    total = len(g.nodes)
    ext_nodes = sum(1 for nid in g.nodes if nid in grounded and _externally_grounded(g.nodes[nid]))
    fully_closed = total > 0 and ext_nodes == 0 and ext_edges == 0 and not top_external
    evidence = [f"nodes with an outward reference: {ext_nodes}/{total}",
                f"edges with an outward reference: {ext_edges}/{len(g.edges)}",
                f"top-level outward reference: {'yes' if top_external else 'no'}",
                f"warrant edges: {len(warrant)}; ungrounded participants: {len(ungrounded)}"]
    if circular:
        evidence.append("circular warrant (no grounded member): " + ", ".join(circular[:12]))
    if fully_closed:
        return Finding("P1", True,
                       "no node and no top-level field cites anything outside the graph; "
                       "every lookup can only return another lookup", evidence)
    if circular:
        return Finding("P1", True,
                       f"{len(circular)} node(s) sit in a support chain that does not reach an "
                       "externally grounded node", evidence)
    return Finding("P1", False, "provenance reaches outside the graph", evidence)


# --- P2 ---------------------------------------------------------------------

def check_no_falsifier(g: Graph) -> Finding:
    used_rels = sorted({e.rel for e in g.edges if is_defeat_rel(e.rel)})
    field_hits: list[str] = []
    state_hits: list[str] = []
    label_hits: list[str] = []
    for where, rec in _items(g):
        for k, v in rec.items():
            nk = _norm(k)
            if nk in DEFEAT_KEYS:
                field_hits.append(f"{where}.{nk}")
            if nk == "state" and isinstance(v, str) and _norm(v) in DEFEAT_STATES:
                state_hits.append(f"{where}={v}")
            if nk in ("label", "description") and isinstance(v, str) and DEFEAT_LABEL_RE.search(v):
                label_hits.append(f"{where}: {v[:48]!r}")
    declared = sorted(r for r in g.rel_vocab if is_defeat_rel(r))
    # an edge-state enum that admits a defeat state is a declared channel too
    for k, v in g.top.items():
        if k.endswith(("state_enum", "states")):
            for s in _declared_vocab(v):
                if s in DEFEAT_STATES:
                    declared.append(f"{k}:{s}")
    evidence = []
    if used_rels:
        evidence.append("defeat relations in use: " + ", ".join(used_rels))
    if field_hits:
        evidence.append("falsifier/retraction fields: " + ", ".join(field_hits[:8]))
    if state_hits:
        evidence.append("defeat states: " + ", ".join(state_hits[:8]))
    if declared:
        evidence.append("declared but unused channel: " + ", ".join(declared))
    if label_hits:
        evidence.append(f"revert/defeat words in free-text labels only ({len(label_hits)}): "
                        + "; ".join(label_hits[:3]))
    if used_rels or field_hits or state_hits:
        return Finding("P2", False, "the graph can record a claim being defeated", evidence)
    if declared:
        return Finding("P2", False,
                       "a defeat channel is declared in the vocabulary but no instance uses "
                       "it yet; the schema can retract even though nothing has been", evidence)
    if label_hits:
        return Finding("P2", True,
                       "a revert/defeat path appears only as words inside free-text labels; "
                       "no typed relation, field or state lets a query ask what defeats a "
                       "claim", evidence)
    return Finding("P2", True,
                   "no relation, field, state or declared vocabulary can defeat, retract, "
                   "contradict or supersede a claim; the graph can add truth but has no "
                   "way to remove it", evidence or ["no defeat channel found"])


# --- P3 ---------------------------------------------------------------------

def check_no_timestamp(g: Graph) -> Finding:
    top_scalars = {k: v for k, v in g.top.items() if not isinstance(v, (dict, list))}
    top_hits = _has_any_key(top_scalars, TEMPORAL_KEYS)
    node_hits = sum(1 for n in g.nodes.values() if _has_any_key(n, TEMPORAL_KEYS))
    edge_hits = sum(1 for e in g.edges if _has_any_key(e.raw, TEMPORAL_KEYS))
    tclass = top_scalars.get("temporal_class")
    evidence = [
        f"top-level anchors: {', '.join(top_hits) if top_hits else 'none'}",
        f"nodes with a temporal field: {node_hits}/{len(g.nodes)}",
        f"edges with a temporal field: {edge_hits}/{len(g.edges)}",
    ]
    if tclass:
        evidence.append(f"declared temporal_class: {tclass}")
    if top_hits or node_hits or edge_hits or tclass:
        return Finding("P3", False, "the graph carries a temporal anchor", evidence)
    return Finding("P3", True,
                   "no generated_at / recorded_at / as_of anywhere and no declared "
                   "temporal_class; a 2019 edge and a yesterday edge are indistinguishable "
                   "and STALE has nothing to fire on", evidence)


# --- P4 ---------------------------------------------------------------------

def _numeric(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def check_collapsed_confidence(g: Graph) -> Finding:
    values: list[float] = []
    for _, rec in _items(g):
        for k, v in rec.items():
            if _norm(k) in CONFIDENCE_KEYS:
                f = _numeric(v)
                if f is not None:
                    values.append(f)
    causal_without = [e for e in g.edges
                      if e.rel in CAUSAL_RELS and not _has_any_key(e.raw, CONFIDENCE_KEYS)]
    evidence = [f"confidence-bearing fields: {len(values)}",
                f"causal edges without a confidence field: {len(causal_without)}"]
    if causal_without:
        evidence.append("e.g. " + ", ".join(f"{e.src}-{e.rel}->{e.dst}" for e in causal_without[:6]))
    if values and len(values) >= 3 and len(set(values)) == 1 and values[0] >= 1.0:
        return Finding("P4", True,
                       f"every one of {len(values)} confidence/weight fields is {values[0]:g}; "
                       "uncertainty was rounded away before storage", evidence)
    if causal_without:
        return Finding("P4", True,
                       f"{len(causal_without)} causal edge(s) carry no confidence field; "
                       "a correlation enters as a cause with no record that it was uncertain",
                       evidence)
    if not values:
        return Finding("P4", False,
                       "no numeric confidence fields (structural graph; nothing to collapse)",
                       evidence)
    return Finding("P4", False, "confidence values vary", evidence)


# --- P5 ---------------------------------------------------------------------

def check_irreversible_merge(g: Graph) -> Finding:
    # Only identity-typed nodes count. An alias on an artifact or a claim is
    # a naming convenience, not a person being merged.
    identity_nodes = {nid for nid, n in g.nodes.items()
                      if _norm(n.get("type", "")) in IDENTITY_TYPES}
    merged: list[str] = []
    unbased: list[str] = []
    for nid in identity_nodes:
        n = g.nodes[nid]
        if _has_any_key(n, MERGE_KEYS):
            merged.append(nid)
            if not _has_any_key(n, MERGE_BASIS_KEYS):
                unbased.append(f"node:{nid}")
    for e in g.edges:
        if e.rel in MERGE_RELS and (e.src in identity_nodes or e.dst in identity_nodes):
            merged.append(f"{e.src}->{e.dst}")
            if not _has_any_key(e.raw, MERGE_BASIS_KEYS):
                unbased.append(f"edge:{e.src}-{e.rel}->{e.dst}")
    split_channel = any(_has_any_key(rec, SPLIT_KEYS) for _, rec in _items(g)) or any(
        e.rel in SPLIT_RELS for e in g.edges) or bool(g.rel_vocab & SPLIT_RELS)
    evidence = [f"identity-typed nodes: {len(identity_nodes)}",
                f"merge assertions: {len(merged)}",
                f"merge assertions without a basis: {len(unbased)}",
                f"split channel present: {'yes' if split_channel else 'no'}"]
    if unbased:
        evidence.append("e.g. " + ", ".join(unbased[:6]))
    if merged and unbased and not split_channel:
        return Finding("P5", True,
                       f"{len(unbased)} identity merge(s) carry no basis and nothing in the "
                       "graph can split a merged identity again", evidence)
    if not merged:
        return Finding("P5", False, "no identity merges asserted", evidence)
    if unbased:
        return Finding("P5", False,
                       f"{len(unbased)} identity merge(s) lack a recorded basis, but a split "
                       "channel exists so the merge is reversible", evidence)
    return Finding("P5", False, "identity merges carry a basis", evidence)


# --- P6 ---------------------------------------------------------------------

def check_single_role_authority(g: Graph) -> Finding:
    roles: dict[str, set] = {"proposer": set(), "ratifier": set(), "executor": set()}
    for _, rec in _items(g):
        for k, v in rec.items():
            nk = _norm(k)
            if not isinstance(v, str) or not v.strip():
                continue
            if nk in PROPOSER_KEYS:
                roles["proposer"].add(_norm(v))
            elif nk in RATIFIER_KEYS:
                roles["ratifier"].add(_norm(v))
            elif nk in EXECUTOR_KEYS:
                roles["executor"].add(_norm(v))
    zones = {}
    for n in g.nodes.values():
        z = n.get("zone")
        if z not in (None, ""):
            zones[_norm(z)] = zones.get(_norm(z), 0) + 1
    evidence = [f"proposer identities: {sorted(roles['proposer']) or 'none'}",
                f"ratifier identities: {sorted(roles['ratifier']) or 'none'}",
                f"executor identities: {sorted(roles['executor']) or 'none'}"]
    if zones:
        evidence.append("zone distribution: " + ", ".join(f"{k}={v}" for k, v in sorted(zones.items())))
    # Two declared roles are enough: a graph whose proposer is also its
    # ratifier is self-ratifying whether or not it names an executor, and
    # self-ratification is the capture surface this repo's Z1/Z2 split exists
    # to prevent (H-CAND-GOVERNANCE-CAPTURE-SURFACE-01).
    populated = [s for s in roles.values() if s]
    if len(populated) >= 2:
        shared = set.intersection(*populated)
        if shared and all(len(s) == 1 for s in populated):
            return Finding("P6", True,
                           f"the same identity ({', '.join(sorted(shared))}) fills every "
                           f"declared authority role ({len(populated)} of 3 declared); the "
                           "thing that proposes an edge and the thing that ratifies it are "
                           "one process", evidence)
    status = _norm(g.top.get("status", ""))
    if not roles["ratifier"] and status and any(m in status for m in UNRATIFIED_MARKERS):
        evidence.append(f"status={g.top.get('status')}: unratified, which is not self-ratified")
    return Finding("P6", False, "no single identity holds every role", evidence)


# --- P7 ---------------------------------------------------------------------

def check_reflexive_measurement(g: Graph) -> Finding:
    self_loops = [e for e in g.edges if e.src == e.dst]
    pairs: dict[tuple[str, str], set] = {}
    for e in g.edges:
        pairs.setdefault((e.src, e.dst), set()).add(e.rel)
    reflexive: list[str] = []
    for (a, b), rels in pairs.items():
        if a == b:
            continue
        back = pairs.get((b, a), set())
        if (rels & MEASURE_RELS and back & ACT_RELS) or (rels & ACT_RELS and back & MEASURE_RELS):
            reflexive.append(f"{a} <-> {b} ({', '.join(sorted(rels))} / {', '.join(sorted(back))})")
    evidence = [f"self-loops: {len(self_loops)}", f"measure/act 2-cycles: {len(reflexive)}"]
    if self_loops:
        evidence.append("e.g. " + ", ".join(f"{e.src}-{e.rel}->{e.dst}" for e in self_loops[:6]))
    if reflexive:
        evidence.append("e.g. " + "; ".join(reflexive[:4]))
    if self_loops or reflexive:
        return Finding("P7", True,
                       "the graph measures what it writes: a node confirms itself or the "
                       "measured node feeds its own measurer directly", evidence)
    return Finding("P7", False, "no self-loop and no direct measure/act cycle", evidence)


# --- P8 ---------------------------------------------------------------------

def check_opaque_schema(g: Graph) -> Finding:
    node_ids = set(g.nodes)
    dangling: list[Edge] = []
    cross: list[str] = []
    for e in g.edges:
        for end in (e.src, e.dst):
            if end in node_ids:
                continue
            if end in g.external_ids:
                cross.append(f"{end} (in {g.external_ids[end]})")
            else:
                dangling.append(e)
                break
    rels = {e.rel for e in g.edges}
    undeclared = sorted(rels - g.rel_vocab) if g.rel_vocab else []
    untyped = sum(1 for n in g.nodes.values() if not n.get("type"))
    evidence = [f"nodes: {len(g.nodes)}; edges: {len(g.edges)}; distinct relations: {len(rels)}",
                f"declared relation vocabulary: {len(g.rel_vocab) or 'none'}",
                f"dangling endpoints: {len(dangling)}",
                f"untyped nodes: {untyped}"]
    if cross:
        evidence.append(f"cross-graph endpoints resolved in a sibling layer ({len(cross)}): "
                        + ", ".join(sorted(set(cross))[:6]))
    if dangling:
        evidence.append("e.g. " + ", ".join(f"{e.src}->{e.dst}" for e in dangling[:6]))
    if undeclared:
        evidence.append("relations outside the declared vocabulary: " + ", ".join(undeclared[:8]))
    if dangling:
        return Finding("P8", True,
                       f"{len(dangling)} edge(s) reference a node that does not exist; the "
                       "graph answers queries about things nobody can enumerate", evidence)
    if undeclared:
        return Finding("P8", True,
                       f"{len(undeclared)} relation(s) are used but not in the declared "
                       "vocabulary", evidence)
    if not g.rel_vocab and len(rels) >= AD_HOC_RELATION_THRESHOLD:
        return Finding("P8", True,
                       f"{len(rels)} distinct relations and no declared vocabulary; the "
                       "schema cannot be exported because it was not written down", evidence)
    return Finding("P8", False, "schema is enumerable", evidence)


# --- P9 ---------------------------------------------------------------------

def check_unverified(g: Graph) -> Finding:
    carriers = 0
    verified = 0
    total = 0
    for where, rec in _items(g):
        if where == "graph":
            if _has_any_key(rec, VERIFICATION_KEYS, nonempty=False):
                carriers += 1
            continue
        total += 1
        hits = _has_any_key(rec, VERIFICATION_KEYS, nonempty=False)
        if hits:
            carriers += 1
            for k, v in rec.items():
                nk = _norm(k)
                if nk in ("state", "status") and isinstance(v, str) and _norm(v) in VERIFICATION_STATES:
                    verified += 1
                    break
                if nk in ("tests", "test_count") and _numeric(v) and _numeric(v) > 0:
                    verified += 1
                    break
    top_channel = any(_norm(k) in VERIFICATION_KEYS for k in g.top)
    measure_edges = sum(1 for e in g.edges if e.rel in MEASURE_RELS)
    evidence = [f"records carrying a verification field: {carriers}/{total + 1}",
                f"records at an observed/tested state: {verified}/{total}",
                f"top-level verification channel: {'yes' if top_channel else 'no'}",
                f"measure-type edges: {measure_edges} (an instrument named is not a result recorded)"]
    if carriers == 0:
        return Finding("P9", True,
                       "no node, edge or top-level field records whether anything was ever "
                       "checked; the graph stores belief and no test", evidence)
    return Finding("P9", False, "a verification channel exists", evidence)


CHECKS = [
    check_closed_provenance,
    check_no_falsifier,
    check_no_timestamp,
    check_collapsed_confidence,
    check_irreversible_merge,
    check_single_role_authority,
    check_reflexive_measurement,
    check_opaque_schema,
    check_unverified,
]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@dataclass
class Report:
    path: str
    findings: list
    accepted: dict = field(default_factory=dict)   # prop -> baseline reason
    stale: list = field(default_factory=list)      # props listed in baseline that pass

    @property
    def failed(self) -> list:
        return [f for f in self.findings if f.failed]

    @property
    def blocking_failures(self) -> list:
        return [f for f in self.failed if f.prop in BLOCKING and f.prop not in self.accepted]

    @property
    def advisory_failures(self) -> list:
        return [f for f in self.failed if f.prop in ADVISORY and f.prop not in self.accepted]

    @property
    def capture_score(self) -> int:
        return len(self.failed)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "capture_score": self.capture_score,
            "blocking_failures": [f.prop for f in self.blocking_failures],
            "advisory_failures": [f.prop for f in self.advisory_failures],
            "accepted_by_baseline": dict(self.accepted),
            "stale_baseline_entries": list(self.stale),
            "findings": [f.as_dict() for f in self.findings],
        }


def lint_graph(g: Graph, baseline_entry: dict | None = None) -> Report:
    findings = [check(g) for check in CHECKS]
    rep = Report(path=g.path, findings=findings)
    if baseline_entry:
        failed = {f.prop for f in findings if f.failed}
        for prop, reason in baseline_entry.items():
            if prop in failed:
                rep.accepted[prop] = str(reason)
            else:
                rep.stale.append(prop)
    return rep


def _rel(path: str) -> str:
    return os.path.relpath(os.path.abspath(path), ROOT).replace(os.sep, "/")


def lint_path(path: str, baseline: dict | None = None) -> Report:
    return lint_paths([path], baseline)[0]


def lint_paths(paths: list, baseline: dict | None = None) -> list:
    """Lint several graphs as one multiplex: an edge endpoint that is not a node
    in its own file but is a node in a sibling file is a seam between layers
    (crb/README.md), reported under P8 as cross-graph rather than dangling."""
    graphs = [normalize(p, load_doc(p)) for p in paths]
    index: dict = {}
    for g in graphs:
        for nid in g.nodes:
            index.setdefault(nid, _rel(g.path))
    reports = []
    for g in graphs:
        g.external_ids = {nid: p for nid, p in index.items()
                          if nid not in g.nodes}
        entry = None
        if baseline:
            entry = baseline.get(_rel(g.path)) or baseline.get(g.path)
        reports.append(lint_graph(g, entry))
    return reports


def load_baseline(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise GraphLoadError(f"baseline {path}: {exc}") from exc
    accepted = data.get("accepted") if isinstance(data, dict) else None
    if not isinstance(accepted, dict):
        raise GraphLoadError(f"baseline {path}: expected an object with an 'accepted' mapping")
    for graph_path, props in accepted.items():
        if not isinstance(props, dict):
            raise GraphLoadError(f"baseline {path}: '{graph_path}' must map property ids to reasons")
        for prop, reason in props.items():
            if prop not in PROPERTY_NAMES:
                raise GraphLoadError(f"baseline {path}: unknown property '{prop}' under '{graph_path}'")
            if prop not in BLOCKING:
                raise GraphLoadError(
                    f"baseline {path}: '{graph_path}.{prop}' is advisory; the baseline accepts "
                    f"blocking debt only ({', '.join(sorted(BLOCKING))}). Advisory findings are "
                    f"reported, not accepted, so --strict keeps its meaning")
            if not isinstance(reason, str) or not reason.strip():
                raise GraphLoadError(f"baseline {path}: '{graph_path}.{prop}' needs a non-empty reason")
    return accepted


def render_text(reports: list) -> str:
    lines = []
    for rep in reports:
        lines.append(f"{rep.path}  capture score {rep.capture_score}/9")
        for f in rep.findings:
            if f.failed and f.prop in rep.accepted:
                status = "ACCEPTED"
            elif f.failed:
                status = "FAIL"
            else:
                status = "PASS"
            lines.append(f"  {f.prop} {f.name:<22} {f.severity:<5} {status:<8} {f.message}")
            if f.failed or f.prop in rep.stale:
                for ev in f.evidence[:6]:
                    lines.append(f"       - {ev}")
            if f.failed and f.prop in rep.accepted:
                lines.append(f"       - baseline: {rep.accepted[f.prop]}")
        for prop in rep.stale:
            lines.append(f"  {prop} {PROPERTY_NAMES[prop]:<22} BLOCK STALE    listed in the baseline "
                         "but passes now; remove the entry so the baseline ratchets down")
        lines.append("")
    return "\n".join(lines)


def exit_code(reports: list, strict: bool) -> int:
    for rep in reports:
        if rep.blocking_failures or rep.stale:
            return 1
        if strict and rep.advisory_failures:
            return 1
    return 0


# ---------------------------------------------------------------------------
# Fixtures (shared by --smoke-test and tools/tests/test_graph_capture_lint.py)
# ---------------------------------------------------------------------------

def terrifying_fixture() -> dict:
    """Every one of the nine properties fires. Looks ordinary; that is the point."""
    return {
        "graph_id": "ORACLE",
        "status": "LIVE",
        "writer": "self", "ratifier": "self", "executor": "self",
        "nodes": [
            {"id": "C1", "type": "claim", "label": "X causes Y", "weight": 1.0},
            {"id": "C2", "type": "claim", "label": "Y is observed", "weight": 1.0},
            {"id": "C3", "type": "claim", "label": "therefore X", "weight": 1.0},
            {"id": "M1", "type": "monitor", "label": "self-check"},
            {"id": "P1", "type": "person", "label": "J. Doe", "merged_from": ["P7", "P9"]},
        ],
        "edges": [
            {"from": "C1", "to": "C2", "rel": "supported_by"},
            {"from": "C2", "to": "C3", "rel": "supported_by"},
            {"from": "C3", "to": "C1", "rel": "supported_by"},
            {"from": "C1", "to": "C2", "rel": "causes"},
            {"from": "M1", "to": "C1", "rel": "measures"},
            {"from": "C1", "to": "M1", "rel": "feeds"},
            {"from": "M1", "to": "M1", "rel": "confirms"},
            {"from": "P1", "to": "C3", "rel": "asserts"},
            {"from": "C3", "to": "GHOST", "rel": "entails"},
        ],
    }


def clean_fixture() -> dict:
    """A small graph with all nine properties absent."""
    return {
        "graph_id": "SEAM",
        "status": "PROPOSED",
        "recorded_at": "2026-10-01T00:00:00Z",
        "temporal_class": "OBSERVATIONAL",
        "author": "Z1 (Claude)",
        "ratified_by": "Night",
        "executor": "Z3 (per ZONE_REGISTRY.md)",
        "node_types": ["claim", "artifact", "measurement"],
        "edge_types": ["implements", "measures", "conflicts_with"],
        "nodes": [
            {"id": "A1", "type": "artifact", "label": "WITNESS_SERVICE_CONTRACT.md",
             "source": "WITNESS_SERVICE_CONTRACT.md"},
            {"id": "C1", "type": "claim", "label": "Participation is not authority",
             "falsifier": "a participant gains a ratification right without a Z2 hash",
             "confidence": 0.7, "state": "SPECIFIED"},
            {"id": "C2", "type": "claim", "label": "Molts resolve at window_end",
             "falsifier": "a molt resolves before its window closes",
             "confidence": 0.4, "state": "CLAIMED"},
            {"id": "M1", "type": "measurement", "label": "NF_LEDGER.jsonl Brier row",
             "source": "NF_LEDGER.jsonl", "observed_at": "2026-09-28", "state": "OBSERVED"},
        ],
        "edges": [
            {"from": "A1", "to": "C1", "rel": "implements", "state": "SPECIFIED"},
            {"from": "M1", "to": "C2", "rel": "measures", "state": "OBSERVED"},
            {"from": "C2", "to": "C1", "rel": "conflicts_with", "state": "CLAIMED"},
        ],
    }


def run_smoke_test() -> int:
    bad = lint_graph(normalize("<terrifying>", terrifying_fixture()))
    failed = {f.prop for f in bad.failed}
    assert failed == set(PROPERTY_NAMES), f"terrifying fixture should fail all nine, failed {sorted(failed)}"
    assert bad.capture_score == 9
    assert exit_code([bad], strict=False) == 1

    good = lint_graph(normalize("<clean>", clean_fixture()))
    assert not good.failed, [f.as_dict() for f in good.failed]
    assert good.capture_score == 0
    assert exit_code([good], strict=True) == 0

    # baseline: an accepted failure does not block; a stale entry does
    accepted = lint_graph(normalize("<terrifying>", terrifying_fixture()),
                          {"P1": "x", "P2": "x", "P3": "x"})
    assert not accepted.blocking_failures and len(accepted.accepted) == 3
    assert exit_code([accepted], strict=False) == 0
    stale = lint_graph(normalize("<clean>", clean_fixture()), {"P2": "was missing"})
    assert stale.stale == ["P2"] and exit_code([stale], strict=False) == 1

    # every canonical graph that exists parses and normalises; no verdict asserted
    for rel in CANONICAL_GRAPHS:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            try:
                rep = lint_path(p)
            except GraphLoadError as exc:  # pragma: no cover - PyYAML missing
                if "PyYAML" in str(exc):
                    continue
                raise
            assert len(rep.findings) == 9

    # JSON round trip
    json.dumps([bad.as_dict(), good.as_dict()])
    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test PASSED "
          f"(terrifying=9/9, clean=0/9, baseline accept+stale, canonical parse)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="graph_capture_lint_v1_0.py",
        description="Score a graph file against the nine properties of a graph that "
                    "cannot be wrong from the inside. P1-P3 block; P4-P9 advise.")
    ap.add_argument("paths", nargs="*", help="graph files (.json, .yaml, .yml)")
    ap.add_argument("--input", action="append", default=[], help="alias for a positional path")
    ap.add_argument("--all", action="store_true", help="lint the canonical graph set")
    ap.add_argument("--baseline", help="accepted-debt file (see module docstring)")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--strict", action="store_true", help="advisory failures also exit 1")
    ap.add_argument("--smoke-test", action="store_true", help="self-check on fixtures")
    ap.add_argument("--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}")
    return ap


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()
    paths = list(args.paths) + list(args.input)
    if args.all:
        paths += [os.path.join(ROOT, rel) for rel in CANONICAL_GRAPHS]
    if not paths:
        build_parser().print_usage(sys.stderr)
        print("error: give at least one graph path, --all, or --smoke-test", file=sys.stderr)
        return 2
    try:
        baseline = load_baseline(args.baseline) if args.baseline else None
        reports = lint_paths(paths, baseline)
    except GraphLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for rep in reports:
        rep.path = _rel(rep.path)
    if args.json:
        print(json.dumps({"tool": TOOL_NAME, "version": TOOL_VERSION,
                          "reports": [r.as_dict() for r in reports]}, indent=2))
    else:
        print(render_text(reports), end="")
    code = exit_code(reports, args.strict)
    if not args.json:
        blocked = sum(len(r.blocking_failures) for r in reports)
        stale = sum(len(r.stale) for r in reports)
        advis = sum(len(r.advisory_failures) for r in reports)
        print(f"{len(reports)} graph(s): {blocked} blocking, {advis} advisory, {stale} stale baseline "
              f"-> exit {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
