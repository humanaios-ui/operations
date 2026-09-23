"""
test_repository_coordinator_v0_1.py
Builder v1.7 compliant - repository_coordinator tests.

The coordinator is advisory. These tests prove it distinguishes repository
state drift from elapsed time and keeps separate signals separate.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from repository_coordinator_v0_1 import analyze

TOOL_NAME = "test_repository_coordinator"
TOOL_VERSION = "0.1.0"


def pr(n, title="Work item", body="", files=None, patch="", reviews=None, mergeable_state="clean"):
    files = ["x.py"] if files is None else files
    return {
        "number": n,
        "title": title,
        "body": body,
        "files": files,
        "file_details": [{"filename": f, "patch": patch if i == 0 else ""} for i, f in enumerate(files)],
        "reviews": reviews or [],
        "mergeable_state": mergeable_state,
        "html_url": f"https://example.test/pull/{n}",
    }


def run(prs, *, refs=None, paths=None, pq=""):
    return analyze({
        "repository": "example/repo",
        "main_sha": "abc",
        "main_paths": paths or [],
        "referenced_pull_requests": refs or {},
        "pull_requests": prs,
    }, pq)


def item(index, n):
    return next(x for x in index["items"] if x["number"] == n)


def test_clean_live_work_advances():
    idx = run([pr(1)])
    assert item(idx, 1)["guidance"]["action"] == "ADVANCE"


def test_zero_diff_is_preserve_close_not_merge_work():
    idx = run([pr(1, files=[])])
    assert item(idx, 1)["guidance"]["action"] == "CLOSE_PRESERVE"


def test_competing_prs_require_comparison_not_winner_selection():
    a = pr(1, "SMAG s1 gate wire-up", files=["tools/smag.py", ".github/workflows/q.yml"])
    b = pr(2, "SMAG s1 gate enforcement", files=["tools/smag.py", ".github/workflows/q.yml"])
    a["body"] = b["body"] = "- [x] **Z2**"
    idx = run([a, b])
    assert item(idx, 1)["guidance"]["action"] == "COMPARE_CONSOLIDATE"
    assert item(idx, 2)["guidance"]["action"] == "COMPARE_CONSOLIDATE"


def test_same_requirements_file_different_dependencies_are_not_competing():
    a = pr(1, "build deps update anthropic requirement", files=["tools/requirements.txt"])
    b = pr(2, "build deps update mcp requirement", files=["tools/requirements.txt"])
    idx = run([a, b])
    assert item(idx, 1)["guidance"]["action"] == "ADVANCE"
    assert item(idx, 2)["guidance"]["action"] == "ADVANCE"


def test_closed_unmerged_dependency_forces_reexamination():
    p = pr(1, body="Implements follow-up from #9")
    idx = run([p], refs={"9": {"state": "closed", "merged": False}})
    assert item(idx, 1)["guidance"]["action"] == "REEXAMINE"


def test_missing_referenced_artifact_forces_reexamination():
    p = pr(1, body="Authority: `z1-inbox/2026-09-21/Z2_RULING.md`")
    idx = run([p], paths=["PRIORITY_QUEUE.md"])
    assert item(idx, 1)["guidance"]["action"] == "REEXAMINE"


def test_temporal_control_under_active_gate_forces_reexamination():
    p = pr(
        1,
        body="- [x] **Z2**\n30-day rolling window pauses merge",
        files=[".github/workflows/q.yml", "tools/gate.py"],
        patch="+ enforce 30-day rolling window before merge",
    )
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource state\n**State:** `GATING`\n"
    idx = run([p], pq=pq)
    got = item(idx, 1)
    assert got["guidance"]["action"] == "REEXAMINE"
    assert got["canonical_gates"]["status"] == "REVIEW_REQUIRED"


def test_workflow_change_without_z2_claim_is_authority_mismatch():
    p = pr(1, body="- [x] **Z1**", files=[".github/workflows/new.yml"])
    idx = run([p])
    got = item(idx, 1)
    assert got["guidance"]["action"] == "REEXAMINE"
    assert got["aut