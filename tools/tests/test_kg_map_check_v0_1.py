import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import kg_map_check_v0_1 as kg  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
SNAPSHOT = os.path.join(REPO_ROOT, "kg", "humanaios_kg_v0_1.json")


def _snapshot():
    with open(SNAPSHOT, encoding="utf-8") as fh:
        return json.load(fh)


def test_committed_snapshot_is_clean():
    assert kg.check(_snapshot(), REPO_ROOT) == []


def test_snapshot_counts_match_live_graph():
    snap = _snapshot()
    assert len(snap["nodes"]) == 22
    assert len(snap["edges"]) == 16
    areas = [n for n in snap["nodes"] if n["kind"] == "repo_area"]
    assert len(areas) == 12


def test_missing_evidence_path_is_flagged():
    snap = _snapshot()
    area = next(n for n in snap["nodes"] if n["id"] == "A01")
    area["repo_evidence"] = ["acat/does/not/exist.py"]
    problems = kg.check(snap, REPO_ROOT)
    assert any("evidence path missing" in p for p in problems)
    assert any("verified_path but no evidence path exists" in p for p in problems)


def test_dangling_edge_endpoint_is_flagged():
    snap = copy.deepcopy(_snapshot())
    snap["edges"][0]["target"] = "A99"
    problems = kg.check(snap, REPO_ROOT)
    assert any("unknown target 'A99'" in p for p in problems)


def test_edge_without_rationale_is_flagged():
    snap = copy.deepcopy(_snapshot())
    snap["edges"][0]["rationale"] = ""
    assert any("no rationale" in p for p in kg.check(snap, REPO_ROOT))


def test_no_repo_trace_with_evidence_is_flagged():
    snap = copy.deepcopy(_snapshot())
    area = next(n for n in snap["nodes"] if n["id"] == "A02")
    area["repo_evidence"] = ["comparison_engine.py"]
    assert any("no_repo_trace but evidence" in p for p in kg.check(snap, REPO_ROOT))
