"""
test_graph_capture_lint.py
Builder v1.7 compliant - graph_capture_lint_tests
HumanAIOS - S-100126-graph-capture-lint
Tests for tools/graph_capture_lint_v1_0.py.

Covers:
  1. the terrifying fixture fails all nine properties; the clean fixture fails none
  2. each property fires on a minimal graph that has only that defect
  3. normalisation handles the repo's graph shapes (dict-of-nodes, list-of-nodes,
     from/to and source/target edges, nested side tables)
  4. baseline: accepted failures do not block, stale entries do, malformed
     baselines are refused
  5. cross-graph endpoint resolution under multi-path linting
  6. CLI exit codes 0 / 1 / 2 and the --json shape
  7. run_smoke_test

Run:
    pytest tools/tests/test_graph_capture_lint.py -v
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_NAME = "test_graph_capture_lint"
TOOL_VERSION = "1.0.0"

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
MODULE_PATH = TOOLS_DIR / "graph_capture_lint_v1_0.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("graph_capture_lint_v1_0", MODULE_PATH)
assert spec and spec.loader
gcl = importlib.util.module_from_spec(spec)
# dataclasses resolve postponed annotations through sys.modules[cls.__module__];
# register before exec so the module's @dataclass decorators can find it.
sys.modules[spec.name] = gcl
spec.loader.exec_module(gcl)


def run_smoke_test() -> bool:
    return gcl.run_smoke_test() == 0


def _lint(doc: dict, name: str = "<mem>", baseline: dict | None = None):
    return gcl.lint_graph(gcl.normalize(name, doc), baseline)


def _failed(doc: dict) -> set:
    return {f.prop for f in _lint(doc).failed}


def _clean() -> dict:
    return copy.deepcopy(gcl.clean_fixture())


# ---------------------------------------------------------------------------
# 1. fixtures
# ---------------------------------------------------------------------------

def test_terrifying_fixture_fails_all_nine():
    doc = json.loads((FIXTURES / "graph_capture_terrifying.json").read_text())
    rep = _lint(doc)
    assert {f.prop for f in rep.failed} == set(gcl.PROPERTY_NAMES)
    assert rep.capture_score == 9
    assert [f.prop for f in rep.blocking_failures] == ["P1", "P2", "P3"]


def test_clean_fixture_fails_none():
    doc = json.loads((FIXTURES / "graph_capture_clean.json").read_text())
    rep = _lint(doc)
    assert rep.failed == [], [f.as_dict() for f in rep.failed]
    assert rep.capture_score == 0


def test_static_fixtures_match_module_fixtures():
    assert json.loads((FIXTURES / "graph_capture_terrifying.json").read_text()) == gcl.terrifying_fixture()
    assert json.loads((FIXTURES / "graph_capture_clean.json").read_text()) == gcl.clean_fixture()


# ---------------------------------------------------------------------------
# 2. one defect at a time, starting from the clean graph
# ---------------------------------------------------------------------------

def test_p1_fully_closed_provenance_blocks():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("source", None)
        n["label"] = "claim"          # no file-like label either
    doc.pop("ratified_by")           # ratified_by counts as an outward reference
    assert "P1" in _failed(doc)


def test_p1_circular_warrant_blocks_even_with_some_grounding():
    doc = _clean()
    doc["nodes"] += [{"id": "X", "type": "claim", "label": "x", "falsifier": "f"},
                     {"id": "Y", "type": "claim", "label": "y", "falsifier": "f"}]
    doc["edges"] += [{"from": "X", "to": "Y", "rel": "supported_by"},
                     {"from": "Y", "to": "X", "rel": "supported_by"}]
    rep = _lint(doc)
    p1 = next(f for f in rep.findings if f.prop == "P1")
    assert p1.failed and any("circular warrant" in e for e in p1.evidence)


def test_p1_circular_chain_grounded_by_one_member_passes():
    doc = _clean()
    doc["nodes"] += [{"id": "X", "type": "claim", "label": "x", "falsifier": "f",
                      "source": "REGISTERED.md"},
                     {"id": "Y", "type": "claim", "label": "y", "falsifier": "f"}]
    doc["edges"] += [{"from": "X", "to": "Y", "rel": "supports"},
                     {"from": "Y", "to": "X", "rel": "supports"}]
    assert "P1" not in _failed(doc)


def test_p2_no_defeat_channel_blocks_and_label_words_do_not_rescue():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("falsifier", None)
    doc["edge_types"] = ["implements", "measures"]
    doc["edges"] = [e for e in doc["edges"] if e["rel"] != "conflicts_with"]
    doc["nodes"][0]["label"] = "REVERT path lives here"
    rep = _lint(doc)
    p2 = next(f for f in rep.findings if f.prop == "P2")
    assert p2.failed
    assert "free-text labels" in p2.message


def test_p2_defeat_stem_matches_compound_relation():
    assert gcl.is_defeat_rel("defeats_if_unmitigated")
    assert gcl.is_defeat_rel("conflicts_with")
    assert not gcl.is_defeat_rel("implements")
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("falsifier", None)
    doc["edge_types"] = ["implements", "measures", "defeats_if_unmitigated"]
    for e in doc["edges"]:
        if e["rel"] == "conflicts_with":
            e["rel"] = "defeats_if_unmitigated"
    assert "P2" not in _failed(doc)


def test_p2_declared_but_unused_channel_passes_with_note():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("falsifier", None)
    doc["edges"] = [e for e in doc["edges"] if e["rel"] != "conflicts_with"]
    rep = _lint(doc)
    p2 = next(f for f in rep.findings if f.prop == "P2")
    assert not p2.failed and "declared" in p2.message


def test_p2_defeat_state_in_enum_counts_as_channel():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("falsifier", None)
    doc["edge_types"] = ["implements", "measures"]
    doc["edges"] = [e for e in doc["edges"] if e["rel"] != "conflicts_with"]
    doc["edge_state_enum"] = ["CLAIMED", "OBSERVED", "RETRACTED"]
    assert "P2" not in _failed(doc)


def test_p3_no_temporal_anchor_blocks():
    doc = _clean()
    doc.pop("recorded_at")
    doc.pop("temporal_class")
    doc["nodes"][3].pop("observed_at")
    assert "P3" in _failed(doc)


def test_p3_historical_record_with_ordering_passes():
    doc = _clean()
    doc.pop("recorded_at")
    doc["temporal_class"] = "HISTORICAL_RECORD"
    doc["nodes"][3].pop("observed_at")
    assert "P3" not in _failed(doc)


def test_p4_uniform_max_confidence_warns():
    doc = _clean()
    for n in doc["nodes"]:
        n["confidence"] = 1.0
    assert "P4" in _failed(doc)


def test_p4_causal_edge_without_confidence_warns():
    doc = _clean()
    doc["edge_types"].append("causes")
    doc["edges"].append({"from": "C1", "to": "C2", "rel": "causes"})
    assert "P4" in _failed(doc)
    doc["edges"][-1]["confidence"] = 0.6
    assert "P4" not in _failed(doc)


def test_p5_unbased_merge_without_split_channel_warns():
    doc = _clean()
    doc["node_types"].append("person")
    doc["nodes"].append({"id": "P1", "type": "person", "label": "J. Doe",
                         "merged_from": ["P7", "P9"], "source": "crm export"})
    assert "P5" in _failed(doc)
    doc["nodes"][-1]["merge_basis"] = "shared verified email + manual review"
    assert "P5" not in _failed(doc)


def test_p6_same_identity_in_every_role_warns():
    doc = _clean()
    doc["author"] = doc["ratified_by"] = doc["executor"] = "oracle"
    assert "P6" in _failed(doc)


def test_p6_two_roles_sharing_identity_is_enough():
    doc = _clean()
    doc.pop("executor")
    doc["author"] = doc["ratified_by"] = "Night"
    assert "P6" in _failed(doc)


def test_p7_self_loop_and_measure_act_cycle_warn():
    doc = _clean()
    doc["edge_types"].append("feeds")
    doc["edges"].append({"from": "C2", "to": "M1", "rel": "feeds"})
    assert "P7" in _failed(doc)
    doc = _clean()
    doc["edge_types"].append("confirms")
    doc["edges"].append({"from": "M1", "to": "M1", "rel": "confirms"})
    assert "P7" in _failed(doc)


def test_p8_dangling_endpoint_and_undeclared_relation_warn():
    doc = _clean()
    doc["edges"].append({"from": "C1", "to": "GHOST", "rel": "implements"})
    assert "P8" in _failed(doc)
    doc = _clean()
    doc["edges"].append({"from": "C1", "to": "C2", "rel": "entails"})
    assert "P8" in _failed(doc)


def test_p8_ad_hoc_vocabulary_threshold():
    doc = _clean()
    doc.pop("edge_types")
    rels = ["r1", "r2", "r3", "r4", "r5"]
    doc["edges"] = [{"from": "C1", "to": "C2", "rel": r} for r in rels]
    assert "P8" in _failed(doc)
    doc["edges"] = doc["edges"][:4]
    assert "P8" not in _failed(doc)


def test_p9_no_verification_channel_warns():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("state", None)
    for e in doc["edges"]:
        e.pop("state", None)
    assert "P9" in _failed(doc)


# ---------------------------------------------------------------------------
# 3. normalisation
# ---------------------------------------------------------------------------

def test_normalize_dict_of_nodes_and_source_target_edges():
    doc = {"generated_at": "2026-01-01",
           "nodes": {"A": {"id": "A", "type": "process", "implementation": "a.py"},
                     "B": {"id": "B", "type": "ledger"}},
           "edges": [{"source": "A", "target": "B", "edge_type": "data_flow", "label": "x"}]}
    g = gcl.normalize("<dict>", doc)
    assert set(g.nodes) == {"A", "B"}
    assert len(g.edges) == 1 and g.edges[0].rel == "data_flow"


def test_normalize_collects_nodes_from_several_lists():
    doc = {"stages": [{"id": "S1", "label": "stage"}],
           "crb_nodes": [{"id": "R1", "type": "crb_role", "label": "role"}],
           "edges": [{"from": "S1", "to": "R1", "rel": "feeds"}]}
    g = gcl.normalize("<multi>", doc)
    assert set(g.nodes) == {"S1", "R1"}


def test_normalize_rejects_non_mapping():
    with pytest.raises(gcl.GraphLoadError):
        gcl.normalize("<list>", [1, 2, 3])


def test_outward_reference_in_nested_side_table_counts_for_p1():
    doc = {"recorded_at": "2026-01-01",
           "nodes": [{"id": "A", "type": "t", "label": "a", "falsifier": "f"}],
           "edges": [],
           "side": {"classifier": "tools/some_tool_v1_0.py"}}
    assert "P1" not in _failed(doc)
    doc.pop("side")
    assert "P1" in _failed(doc)


def test_canonical_graphs_parse_and_score():
    present = [REPO_ROOT / rel for rel in gcl.CANONICAL_GRAPHS if (REPO_ROOT / rel).exists()]
    assert present, "canonical graph set missing from the tree"
    reports = gcl.lint_paths([str(p) for p in present])
    assert all(len(r.findings) == 9 for r in reports)


# ---------------------------------------------------------------------------
# 4. baseline
# ---------------------------------------------------------------------------

def test_baseline_accepts_listed_failures_and_flags_stale_entries():
    rep = _lint(gcl.terrifying_fixture(), baseline={"P1": "known", "P2": "known", "P3": "known"})
    assert rep.blocking_failures == [] and set(rep.accepted) == {"P1", "P2", "P3"}
    assert gcl.exit_code([rep], strict=False) == 0
    stale = _lint(gcl.clean_fixture(), baseline={"P2": "was missing"})
    assert stale.stale == ["P2"]
    assert gcl.exit_code([stale], strict=False) == 1


def test_baseline_does_not_cover_unlisted_blocking_failure():
    rep = _lint(gcl.terrifying_fixture(), baseline={"P1": "known"})
    assert [f.prop for f in rep.blocking_failures] == ["P2", "P3"]


def test_load_baseline_refuses_malformed(tmp_path):
    bad = tmp_path / "b.json"
    bad.write_text(json.dumps({"accepted": {"g.json": {"P42": "nope"}}}))
    with pytest.raises(gcl.GraphLoadError):
        gcl.load_baseline(str(bad))
    bad.write_text(json.dumps({"accepted": {"g.json": {"P1": ""}}}))
    with pytest.raises(gcl.GraphLoadError):
        gcl.load_baseline(str(bad))
    bad.write_text(json.dumps({"nope": 1}))
    with pytest.raises(gcl.GraphLoadError):
        gcl.load_baseline(str(bad))


def test_repo_baseline_is_current():
    """The committed baseline must match the canonical set exactly: every
    listed entry still fails (no stale rows) and nothing blocking is unlisted."""
    baseline = gcl.load_baseline(str(REPO_ROOT / "crb" / "graph_capture_baseline.json"))
    paths = [str(REPO_ROOT / rel) for rel in gcl.CANONICAL_GRAPHS]
    reports = gcl.lint_paths(paths, baseline)
    problems = {gcl._rel(r.path): {"blocking": [f.prop for f in r.blocking_failures], "stale": r.stale}
                for r in reports if r.blocking_failures or r.stale}
    assert not problems, problems


# ---------------------------------------------------------------------------
# 5. cross-graph resolution
# ---------------------------------------------------------------------------

def test_cross_graph_endpoint_is_not_dangling_when_sibling_defines_it(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    base = _clean()
    base["edges"].append({"from": "C1", "to": "FAR", "rel": "implements"})
    a.write_text(json.dumps(base))
    other = _clean()
    other["nodes"].append({"id": "FAR", "type": "artifact", "label": "far.md", "source": "far.md"})
    b.write_text(json.dumps(other))
    alone = gcl.lint_paths([str(a)])[0]
    assert "P8" in {f.prop for f in alone.failed}
    together = gcl.lint_paths([str(a), str(b)])[0]
    assert "P8" not in {f.prop for f in together.failed}
    p8 = next(f for f in together.findings if f.prop == "P8")
    assert any("cross-graph" in e for e in p8.evidence)


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------

def _cli(*args: str):
    return subprocess.run([sys.executable, str(MODULE_PATH), *args],
                          capture_output=True, text=True, cwd=str(REPO_ROOT), check=False)


def test_cli_exit_codes():
    assert _cli(str(FIXTURES / "graph_capture_clean.json")).returncode == 0
    assert _cli(str(FIXTURES / "graph_capture_terrifying.json")).returncode == 1
    assert _cli().returncode == 2
    assert _cli(str(FIXTURES / "does_not_exist.json")).returncode == 2


def test_cli_strict_promotes_advisory():
    doc = _clean()
    for n in doc["nodes"]:
        n.pop("state", None)
    for e in doc["edges"]:
        e.pop("state", None)
    p = FIXTURES.parent / "_tmp_advisory_only.json"
    try:
        p.write_text(json.dumps(doc))
        assert _cli(str(p)).returncode == 0
        assert _cli("--strict", str(p)).returncode == 1
    finally:
        p.unlink(missing_ok=True)


def test_cli_json_shape_and_input_alias():
    r = _cli("--json", "--input", str(FIXTURES / "graph_capture_terrifying.json"))
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["tool"] == gcl.TOOL_NAME
    rep = data["reports"][0]
    assert rep["capture_score"] == 9
    assert rep["blocking_failures"] == ["P1", "P2", "P3"]
    assert {f["property"] for f in rep["findings"]} == set(gcl.PROPERTY_NAMES)


def test_cli_all_with_repo_baseline_is_green():
    r = _cli("--all", "--baseline", "crb/graph_capture_baseline.json")
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_rejects_bad_baseline(tmp_path):
    bad = tmp_path / "b.json"
    bad.write_text("not json")
    r = _cli("--baseline", str(bad), str(FIXTURES / "graph_capture_clean.json"))
    assert r.returncode == 2


# ---------------------------------------------------------------------------
# 7. smoke
# ---------------------------------------------------------------------------

def test_run_smoke_test(capsys):
    assert run_smoke_test()
    assert "PASSED" in capsys.readouterr().out
