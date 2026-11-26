"""
test_admission_ruling_graph.py
Builder v1.7 compliant - tests for admission_ruling_graph_v1_0 (Q-ADMISSION-RULING-GRAPH-01).

The tool joins the admission ledger to Z2 rulings. These tests prove it keeps ledger order,
does not read a clock, does not treat issues as pull requests, and flags a merged pull
request whose ledger history does not end in a merged row.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import admission_ruling_graph_v1_0 as g


def _ev(n, decision, kind="PULL_REQUEST"):
    return {"subject_kind": kind, "subject_number": n, "decision": decision}


def test_smoke_test_passes():
    assert g.run_smoke_test() is True


def test_pr_events_keep_ledger_order_and_skip_issues():
    out = g.pr_events([_ev(2, "ADMIT"), _ev(1, "ADMIT"), _ev(2, "REVOKE"), _ev(9, "ADMIT", "ISSUE")])
    assert list(out) == [2, 1]
    assert out[2] == [(1, "ADMIT"), (3, "REVOKE")]


def test_merge_log_reads_only_merge_pull_request_subjects():
    log = (
        "\x01a\tMerge pull request #7 from o/b\nz1-inbox/2026-01-01/Q-X-01.md\nREADME.md\n"
        "\x01b\tdocs: a direct commit\nz1-inbox/2026-01-01/Q-Y-01.md\n"
    )
    merged, carried = g.parse_merge_log(log)
    assert merged == [7]
    assert carried == {7: ["Q-X-01"]}


def test_a_merged_pr_ending_in_revoke_is_a_gap_but_an_unmerged_one_is_not():
    graph = g.build_graph(
        events=[_ev(1, "ADMIT"), _ev(1, "REVOKE"), _ev(2, "ADMIT"), _ev(2, "REVOKE")],
        merged=[1], carried={}, candidates={}, rulings={},
    )
    assert graph["gaps"] == [{"pr": 1, "last": "REVOKE"}]


def test_a_ruling_without_a_pull_request_is_kept():
    rulings = g.ruling_prs({"f.md": "## Q-A-01 — ACCEPT\n\nsigned by ratify.py\n"})
    graph = g.build_graph(
        events=[], merged=[], carried={},
        candidates={"Q-A-01": {"status": "ratified", "z2_hash": "h"}}, rulings=rulings,
    )
    assert [b["q_id"] for b in graph["blocks"]] == ["Q-A-01"]
    assert graph["blocks"][0]["ruled_by_pr"] is None


def test_page_has_no_authority_and_no_clock():
    graph = g.build_graph(events=[_ev(1, "ADMIT")], merged=[], carried={}, candidates={}, rulings={})
    page = g.render_markdown(graph, ledger_ref="x", main_ref="y")
    assert "authority_effect: NONE" in page
    assert "T00:" not in page and "UTC" not in page
