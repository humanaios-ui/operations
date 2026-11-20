"""
test_admission_ruling_graph_workflow.py
Builder v1.7 compliant - structural tests for .github/workflows/admission-ruling-graph.yml.

The workflow holds a write token on main, so its shape is pinned here: event-driven only, main only,
no loop on its own output, a draft pull request, and nothing beyond the two standard actions.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PATH = REPO / ".github" / "workflows" / "admission-ruling-graph.yml"
TEXT = PATH.read_text(encoding="utf-8")
WF = yaml.safe_load(TEXT)
TRIGGERS = WF.get("on") or WF.get(True)  # YAML 1.1 reads a bare `on` as True
JOBS = WF["jobs"]


def _steps(job):
    return JOBS[job]["steps"]


def test_event_driven_only_with_no_clock():
    assert set(TRIGGERS) == {"pull_request", "push", "workflow_dispatch"}
    assert not re.search(r"(?m)^\s*(schedule|cron)\s*:", TEXT)
    assert "pull_request_target" not in TEXT


def test_push_is_main_only():
    assert TRIGGERS["push"]["branches"] == ["main"]


def test_top_level_permissions_are_read_only():
    assert WF["permissions"] == {"contents": "read"}


def test_check_job_is_read_only_and_pull_request_only():
    job = JOBS["check"]
    assert job["permissions"] == {"contents": "read"}
    assert job["if"] == "github.event_name == 'pull_request'"


def test_refresh_job_has_exactly_the_write_scopes_it_needs():
    perms = JOBS["refresh"]["permissions"]
    assert perms == {"contents": "write", "pull-requests": "write"}


def test_refresh_runs_only_from_main_and_skips_its_own_merge():
    cond = " ".join(str(JOBS["refresh"]["if"]).split())
    assert "github.event_name != 'pull_request'" in cond
    assert "github.ref == 'refs/heads/main'" in cond
    assert "!contains(github.event.head_commit.message, 'admission-graph/refresh-')" in cond


def test_only_the_two_standard_actions_are_used():
    uses = {s["uses"] for job in JOBS.values() for s in job["steps"] if "uses" in s}
    assert uses == {"actions/checkout@v7", "actions/setup-python@v7"}


def test_refresh_self_tests_before_it_writes():
    names = [s.get("name", "") for s in _steps("refresh")]
    test_at = next(i for i, n in enumerate(names) if n.startswith("Tool self-tests"))
    write_at = next(i for i, n in enumerate(names) if n.startswith("Open the refresh pull request"))
    assert test_at < write_at


def test_refresh_opens_a_draft_and_supersedes_older_ones():
    body = next(s["run"] for s in _steps("refresh") if s.get("name", "").startswith("Open the refresh"))
    assert "gh pr create --draft" in body
    assert 'startswith("admission-graph/refresh-")' in body
    assert "gh pr close" in body


def test_refresh_touches_only_the_page():
    body = next(s["run"] for s in _steps("refresh") if s.get("name", "").startswith("Open the refresh"))
    assert "git add ADMISSION_RULING_GRAPH.md" in body
    assert body.count("git add ") == 1


def test_refresh_marker_is_in_the_commit_and_the_title():
    body = next(s["run"] for s in _steps("refresh") if s.get("name", "").startswith("Open the refresh"))
    assert 'subject="${branch}:' in body
    assert 'git commit -m "$subject"' in body
    assert '--title "$subject"' in body


def test_refresh_retries_a_missing_pull_request_on_an_existing_branch():
    body = next(s["run"] for s in _steps("refresh") if s.get("name", "").startswith("Open the refresh"))
    assert "gh pr list --state open --head" in body
    assert "exit 0" in body and body.count("gh pr create") == 1
    assert body.index("gh pr create") < body.index("gh pr close")
