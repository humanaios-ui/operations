"""Tests for tools/graph_lookup_v0_1.py (Q-REPO-GRAPH-LOOKUP-01).

Each test builds a small synthetic graph with a valid integrity digest and, where
freshness matters, a throwaway git repository under tmp_path. Nothing outside
tmp_path is written.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import graph_lookup_v0_1 as gl  # noqa: E402


def _digest(graph):
    candidate = copy.deepcopy(graph)
    candidate["integrity"]["sha256"] = None
    return hashlib.sha256(gl._canonical_bytes(candidate)).hexdigest()


def make_graph(head):
    graph = {
        "graph_id": "test-graph",
        "graph_kind": "DERIVED_READ_MODEL",
        "authority_effect": "NONE",
        "source": {"repository": "example/repo", "head_commit": head, "worktree_state": "CLEAN"},
        "nodes": [
            {"id": "artifact:SESSION_RITUALS.md", "type": "artifact", "label": "SESSION_RITUALS.md",
             "provenance": [{"source_ref": "SESSION_RITUALS.md", "locator": None,
                             "source_hash": "a" * 64, "method": "path_projection", "confidence": 1.0}]},
            {"id": "artifact:tools/x.py", "type": "artifact", "label": "x.py", "provenance": []},
        ],
        "edges": [
            {"id": "edge:1", "from": "artifact:SESSION_RITUALS.md", "to": "artifact:tools/x.py",
             "relation": "REFERENCES", "evidence_state": "OBSERVED", "authority_effect": "NONE",
             "provenance": [{"source_ref": "SESSION_RITUALS.md", "locator": "line:33",
                             "source_hash": "b" * 64, "method": "regex_path_reference", "confidence": 1.0}]},
        ],
        "views": [],
        "integrity": {"algorithm": "sha256", "canonicalization": "json-sort-keys-utf8", "sha256": None},
    }
    graph["integrity"]["sha256"] = _digest(graph)
    return graph


def write_graph(path, graph):
    path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")
    return path


def git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init")
    return repo, git(repo, "rev-parse", "HEAD")


def run(argv, capsys):
    code = gl.main(argv)
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip().startswith("{") else None)


# --- integrity ----------------------------------------------------------------

def test_valid_graph_passes_integrity():
    graph = make_graph("f" * 40)
    assert gl.verify_integrity(graph) == graph["integrity"]["sha256"]


def test_tampered_graph_is_refused(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    graph = make_graph(head)
    graph["nodes"][0]["label"] = "EDITED AFTER COMPILE"
    path = write_graph(tmp_path / "graph.json", graph)
    code, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert code == gl.EXIT_REFUSED
    assert "integrity mismatch" in report["refused"]
    assert "results" not in report


def test_graph_without_authority_none_is_refused(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    graph = make_graph(head)
    graph["authority_effect"] = "GRANTED"
    graph["integrity"]["sha256"] = _digest(graph)
    path = write_graph(tmp_path / "graph.json", graph)
    code, _ = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert code == gl.EXIT_REFUSED


def test_unreadable_graph_is_refused(tmp_path, capsys):
    repo, _ = make_repo(tmp_path)
    code, report = run(["--graph", str(tmp_path / "missing.json"), "--repo", str(repo), "--node", "x"], capsys)
    assert code == gl.EXIT_REFUSED
    assert "cannot read graph" in report["refused"]


# --- answers carry citations ----------------------------------------------------

def test_search_answer_cites_edge_provenance(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    code, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert code == gl.EXIT_OK
    assert len(report["results"]) == 1
    answer = report["results"][0]
    assert answer["node"]["id"] == "artifact:SESSION_RITUALS.md"
    edge = answer["incident_edges"][0]
    assert edge["edge_id"] == "edge:1"
    assert edge["direction"] == "OUT"
    assert edge["citations"][0]["source_ref"] == "SESSION_RITUALS.md"
    assert edge["citations"][0]["locator"] == "line:33"
    assert edge["citations"][0]["source_hash"] == "b" * 64


def test_node_lookup_and_unknown_node(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    code, report = run(["--graph", str(path), "--repo", str(repo), "--node", "artifact:tools/x.py"], capsys)
    assert code == gl.EXIT_OK
    assert report["results"][0]["incident_edge_total"] == 1
    code, _ = run(["--graph", str(path), "--repo", str(repo), "--node", "artifact:nope"], capsys)
    assert code == gl.EXIT_BAD_ARGS


def test_report_pins_commit_and_declares_no_authority(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    _, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert report["graph"]["pinned_head_commit"] == head
    assert report["repository"]["current_head_commit"] == head
    assert report["authority_effect"] == "NONE"
    assert report["read_only"] is True


# --- freshness ------------------------------------------------------------------

def test_fresh_when_pinned_to_clean_head(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    code, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert report["freshness"]["state"] == "FRESH"
    assert code == gl.EXIT_OK


def test_stale_after_new_commit_and_require_fresh_withholds_answers(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    (repo / "README.md").write_text("changed\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "next")
    code, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert report["freshness"]["state"] == "STALE"
    assert code == gl.EXIT_NOT_FRESH
    assert report["results"] is not None
    code, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual", "--require-fresh"], capsys)
    assert code == gl.EXIT_NOT_FRESH
    assert report["results"] is None


def test_dirty_worktree_is_flagged(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    (repo / "scratch.txt").write_text("untracked\n", encoding="utf-8")
    _, report = run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert report["freshness"]["state"] == "DIRTY"
    assert report["freshness"]["worktree_dirty"] is True


def test_unknown_when_repo_is_not_git(tmp_path, capsys):
    plain = tmp_path / "plain"
    plain.mkdir()
    path = write_graph(tmp_path / "graph.json", make_graph("e" * 40))
    code, report = run(["--graph", str(path), "--repo", str(plain), "--search", "ritual"], capsys)
    assert report["freshness"]["state"] == "UNKNOWN"
    assert code == gl.EXIT_NOT_FRESH


# --- read-only -----------------------------------------------------------------

def test_lookup_writes_nothing(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    graph_before = path.read_bytes()
    status_before = git(repo, "status", "--porcelain", "--ignored")
    files_before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    run(["--graph", str(path), "--repo", str(repo), "--search", "ritual"], capsys)
    assert path.read_bytes() == graph_before
    assert git(repo, "status", "--porcelain", "--ignored") == status_before
    assert sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*")) == files_before


def test_argument_validation(tmp_path, capsys):
    repo, head = make_repo(tmp_path)
    path = write_graph(tmp_path / "graph.json", make_graph(head))
    with pytest.raises(SystemExit):
        gl.main(["--graph", str(path), "--search", "a", "--node", "b"])
    capsys.readouterr()
    code, _ = run(["--graph", str(path), "--repo", str(repo), "--search", "a", "--limit", "0"], capsys)
    assert code == gl.EXIT_BAD_ARGS
