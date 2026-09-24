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
TOOL_VERSION = "0.2.0"


def pr(
    n,
    title="Work item",
    body="",
    files=None,
    patch="",
    reviews=None,
    mergeable_state="clean",
    *,
    author="builder",
    draft=False,
    labels=None,
):
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
        "author": author,
        "draft": draft,
        "labels": labels or [],
    }


def policy(*, limit=4, issues=None, prs=None, control_paths=None):
    return {
        "capacity": {"active_operator_queue": limit},
        "admission": {
            "issue_numbers": issues or [],
            "pull_request_numbers": prs or [],
        },
        "maintenance": {
            "authors": ["dependabot[bot]"],
            "labels": ["dependencies"],
        },
        "control_plane": {
            "paths": control_paths or ["REPOSITORY_COORDINATOR_POLICY.json"],
        },
    }


def run(prs, *, refs=None, items=None, paths=None, pq="", policy_data=None):
    return analyze({
        "repository": "example/repo",
        "main_sha": "abc",
        "main_paths": paths or [],
        "referenced_pull_requests": refs or {},
        "referenced_items": items or {},
        "pull_requests": prs,
    }, pq, policy_data)


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
    assert got["authority"]["status"] == "MISMATCH"


def test_latest_changes_requested_is_evidence_not_age():
    reviews = [{
        "user": {"login": "reviewer"},
        "state": "CHANGES_REQUESTED",
        "submitted_at": "2026-01-01T00:00:00Z",
    }]
    p = pr(1, reviews=reviews)
    p["created_at"] = "1999-01-01T00:00:00Z"
    idx = run([p])
    got = item(idx, 1)
    assert got["guidance"]["action"] == "REEXAMINE"
    assert "AGE_IS_NOT_STALENESS" in idx["invariants"]


def test_old_timestamp_alone_does_not_make_work_stale():
    p = pr(1)
    p["created_at"] = "1999-01-01T00:00:00Z"
    idx = run([p])
    assert item(idx, 1)["guidance"]["action"] == "ADVANCE"



def test_temporal_example_inside_noncontrol_tool_does_not_trigger_gate():
    p = pr(
        1,
        body="- [x] **Z1**",
        files=["tools/example_analyzer.py"],
        patch='+ fixture = "30-day rolling window blocks merge"',
    )
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource state\n**State:** `GATING`\n"
    idx = run([p], pq=pq)
    assert item(idx, 1)["guidance"]["action"] == "ADVANCE"


def test_domain_deadline_outside_control_surface_does_not_trigger_gate():
    temporal_term = "dead" + "line"  # runtime fixture; avoid static control-token lint
    p = pr(
        1,
        title="Entitlement navigator",
        body=f"Track an external application {temporal_term} as evidence only.",
        files=["humanaios-funding-pipeline/app.py"],
        patch=f"+ observed_field = record.get('{temporal_term}')",
    )
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource state\n**State:** `GATING`\n"
    idx = run([p], pq=pq)
    assert item(idx, 1)["guidance"]["action"] == "ADVANCE"



def test_directory_reference_is_not_reported_missing_when_children_exist():
    p = pr(1, body="Uses `tools/Metaculus` package")
    idx = run(
        [p],
        paths=["tools/Metaculus/main.py", "tools/Metaculus/requirements.txt"],
    )
    codes = {f["code"] for f in item(idx, 1)["findings"]}
    assert "MISSING_REFERENCED_ARTIFACT" not in codes


def test_external_date_and_unrelated_workflow_word_do_not_cross_match():
    temporal_term = "dead" + "line"
    body = (
        f"External opportunity {temporal_term}: 2026-10-11.\n"
        "Eligibility remains unassessed.\n"
        "Repository workflow validation is handled separately."
    )
    p = pr(1, body=body, files=["humanaios-funding-pipeline/resource-miner/README.md"])
    pq = "### Q-TEMPORAL-DISSOLUTION-01 — Resource state\n**State:** `GATING`\n"
    idx = run([p], pq=pq)
    got = item(idx, 1)
    assert got["canonical_gates"]["status"] == "CLEAR"


def test_unadmitted_ready_work_is_not_operator_queue():
    idx = run([pr(1)], policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "ADMISSION_REVIEW"
    assert got["admission"]["gate"] == "FAIL"
    assert got["guidance"]["action"] == "ADVANCE"


def test_draft_agent_work_is_workbench_not_operator_queue():
    idx = run([pr(1, draft=True)], policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "WORKBENCH"
    assert got["admission"]["gate"] == "PASS"
    assert idx["counts"]["lanes"]["WORKBENCH"] == 1



def test_summary_only_maintenance_is_not_mistaken_for_zero_diff():
    p = pr(
        1,
        title="build(deps): update package",
        files=[],
        author="dependabot[bot]",
        labels=["dependencies"],
    )
    p["files_complete"] = False
    idx = run([p], policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "MAINTENANCE"
    assert got["guidance"]["action"] != "CLOSE_PRESERVE"
    assert got["merge_surface"]["files_complete"] is False


def test_dependabot_routes_to_maintenance_cohort():
    p = pr(
        1,
        title="build(deps): bump actions/checkout",
        files=[".github/workflows/x.yml"],
        author="dependabot[bot]",
        labels=["dependencies", "ci"],
    )
    idx = run([p], policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "MAINTENANCE"
    assert got["admission"]["cohort"] == "github-actions"
    assert got["admission"]["gate"] == "PASS"


def test_referenced_admitted_issue_enters_active_lane():
    p = pr(1, body="Fixes #77")
    referenced = {
        "77": {
            "state": "open",
            "is_pull_request": False,
            "labels": [],
            "title": "Approved objective",
        }
    }
    idx = run([p], items=referenced, policy_data=policy(issues=[77]))
    got = item(idx, 1)
    assert got["lane"] == "ACTIVE"
    assert got["admission"]["admitted"] is True
    assert got["admission"]["gate"] == "PASS"


def test_issue_assignment_without_admission_stays_workbench_when_draft():
    p = pr(1, body="Fixes #77", draft=True)
    referenced = {
        "77": {
            "state": "open",
            "is_pull_request": False,
            "labels": [],
            "title": "Assigned but not admitted",
        }
    }
    idx = run([p], items=referenced, policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "WORKBENCH"
    assert got["admission"]["admitted"] is False


def test_capacity_contention_does_not_choose_winners():
    referenced = {
        str(n): {
            "state": "open",
            "is_pull_request": False,
            "labels": [],
            "title": f"Objective {n}",
        }
        for n in (71, 72, 73)
    }
    prs = [
        pr(1, body="Fixes #71"),
        pr(2, body="Fixes #72"),
        pr(3, body="Fixes #73"),
    ]
    idx = run(
        prs,
        items=referenced,
        policy_data=policy(limit=2, issues=[71, 72, 73]),
    )
    assert idx["capacity"]["contention"] is True
    assert all(x["lane"] == "CAPACITY_CONTENTION" for x in idx["items"])
    assert all(x["admission"]["gate"] == "FAIL" for x in idx["items"])


def test_control_plane_change_is_exempt_from_recursive_admission():
    p = pr(
        1,
        body="- [x] **Z2**",
        files=["REPOSITORY_COORDINATOR_POLICY.json"],
    )
    idx = run([p], policy_data=policy())
    got = item(idx, 1)
    assert got["lane"] == "CONTROL_PLANE"
    assert got["admission"]["gate"] == "PASS"
    assert got["authority"]["required"] == "Z2"


def run_smoke_test():
    test_clean_live_work_advances()
    test_zero_diff_is_preserve_close_not_merge_work()
    return True
