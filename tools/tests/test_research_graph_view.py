"""
test_research_graph_view.py
Fixture tests for tools/research_graph_view.py (issue #874, Phase 1).
No network. Covers AC1–AC5 and AC7 of the design issue.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import research_graph_view as rgv  # noqa: E402

ACTORS = ["humanaios-ui"]
HEAD = "a" * 40
OLD = "b" * 40
GENERATED = "2026-10-15T00:00:00Z"

ADMISSION_ISSUE = {"state": "open", "title": "RG-A", "body": "## ADMISSION_REQUESTED\nstate: ADMISSION_REQUESTED"}

# Minimal workflow texts shaped like the repo's own files.
WF_SECURITY = "name: security-gates\non:\n  pull_request:\n  push:\n"
WF_TOOL_MANIFEST = (
    "name: tool-manifest\non:\n  pull_request:\n    paths:\n"
    "      - \"tools/**\"\n      - \"scripts/**\"\n  push:\n"
)


def _run(name, conclusion="success", status="completed", run_id=1, head=HEAD):
    return {"id": run_id, "workflow_name": name, "event": "pull_request",
            "head_sha": head, "status": status, "conclusion": conclusion}


def _pr(number=10, body="", **over):
    base = {
        "number": number, "title": f"PR {number}", "body": body, "state": "open",
        "draft": False, "merged": False, "head_sha": HEAD,
        "changed_files": ["docs/readme.md"],
        "reviews": [{"login": "humanaios-ui", "state": "APPROVED",
                     "commit_id": HEAD, "submitted_at": "2026-10-10T10:00:00Z"}],
        "runs": [],
    }
    base.update(over)
    return base


def _snapshot(pulls, issues=None, texts=None, errors=None, truncated=False):
    return {
        "repository": "humanaios-ui/operations",
        "default_head_sha": "c" * 40,
        "pulls": pulls,
        "issues": issues if issues is not None else {"800": ADMISSION_ISSUE},
        "workflow_texts": texts if texts is not None else [WF_SECURITY, WF_TOOL_MANIFEST],
        "errors": errors or [],
        "truncated": truncated,
    }


def _build(snapshot):
    return rgv.build_view(snapshot, actors=ACTORS, generated_at=GENERATED, policy_sha="p" * 64)


def _pr_node(view, number):
    return next(n for n in view["nodes"] if n.get("number") == number and n["kind"] == "PULL_REQUEST")


class ReasonCodeTests(unittest.TestCase):
    def test_reason_code_list_is_pinned(self):
        self.assertEqual(rgv.REASON_CODES, (
            "DRAFT", "NO_ADMISSION_LINK", "LATEST_REVIEW_NOT_APPROVED",
            "HEAD_CHANGED_SINCE_EVALUATION", "REQUIRED_RUN_MISSING:",
            "REQUIRED_RUN_NOT_GREEN:", "REQUIRED_WORKFLOW_UNDEFINED:", "CONDITIONAL:",
        ))

    def test_closing_keyword_to_admission_issue_satisfies_link(self):
        pr = _pr(body="Closes #800", runs=[_run("security-gates", run_id=1),
                                           _run("tool-manifest", run_id=2)],
                 changed_files=["tools/x.py"])
        node = _pr_node(_build(_snapshot([pr])), 10)
        self.assertNotIn("NO_ADMISSION_LINK", node["missing_conditions"])

    def test_closing_keyword_absent_reports_no_admission_link(self):
        view = _build(_snapshot([_pr(body="Refs #800")]))
        self.assertIn("NO_ADMISSION_LINK", _pr_node(view, 10)["missing_conditions"])
        self.assertTrue(any(e["kind"] == "REFERENCES" and e["to"] == "ISSUE#800"
                            for e in view["edges"]))

    def test_closing_target_without_admission_marker_reports_no_admission_link(self):
        issues = {"800": {"state": "open", "body": "ordinary bug report"}}
        view = _build(_snapshot([_pr(body="Closes #800")], issues=issues))
        self.assertIn("NO_ADMISSION_LINK", _pr_node(view, 10)["missing_conditions"])

    def test_commented_review_is_not_approval(self):
        pr = _pr(body="Closes #800", reviews=[
            {"login": "humanaios-ui", "state": "COMMENTED", "commit_id": HEAD,
             "submitted_at": "2026-10-10T10:00:00Z"}])
        self.assertIn("LATEST_REVIEW_NOT_APPROVED", _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"])

    def test_approval_from_unauthorized_actor_does_not_count(self):
        pr = _pr(body="Closes #800", reviews=[
            {"login": "some-contributor", "state": "APPROVED", "commit_id": HEAD,
             "submitted_at": "2026-10-10T10:00:00Z"}])
        self.assertIn("LATEST_REVIEW_NOT_APPROVED", _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"])

    def test_approval_on_older_head_reports_head_changed(self):
        pr = _pr(body="Closes #800", reviews=[
            {"login": "humanaios-ui", "state": "APPROVED", "commit_id": OLD,
             "submitted_at": "2026-10-10T10:00:00Z"}])
        conds = _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"]
        self.assertIn("HEAD_CHANGED_SINCE_EVALUATION", conds)
        self.assertNotIn("LATEST_REVIEW_NOT_APPROVED", conds)

    def test_missing_required_run_is_reported(self):
        conds = _pr_node(_build(_snapshot([_pr(body="Closes #800")])), 10)["missing_conditions"]
        self.assertIn("REQUIRED_RUN_MISSING:security-gates", conds)

    def test_required_run_not_green_is_reported(self):
        pr = _pr(body="Closes #800", runs=[_run("security-gates", conclusion="failure")])
        conds = _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"]
        self.assertIn("REQUIRED_RUN_NOT_GREEN:security-gates", conds)

    def test_only_latest_run_for_a_workflow_counts(self):
        pr = _pr(body="Closes #800", runs=[
            _run("security-gates", conclusion="failure", run_id=1),
            _run("security-gates", conclusion="success", run_id=2)])
        conds = _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"]
        self.assertFalse(any("security-gates" in c for c in conds))

    def test_undefined_required_workflow_is_flagged_not_silent(self):
        view = _build(_snapshot([_pr(body="Closes #800")], texts=[WF_TOOL_MANIFEST]))
        conds = _pr_node(view, 10)["missing_conditions"]
        self.assertIn("REQUIRED_WORKFLOW_UNDEFINED:security-gates", conds)


class PathFilterTests(unittest.TestCase):
    def test_unmatched_path_filter_is_conditional_not_missing(self):
        """AC7: tool-manifest does not run for docs-only PRs; that is not a missing check."""
        pr = _pr(body="Closes #800", changed_files=["experiments/scvc_v02/x.py"],
                 runs=[_run("security-gates")])
        conds = _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"]
        self.assertIn("CONDITIONAL:tool-manifest", conds)
        self.assertNotIn("REQUIRED_RUN_MISSING:tool-manifest", conds)

    def test_matched_path_filter_without_run_is_missing(self):
        pr = _pr(body="Closes #800", changed_files=["tools/x.py"],
                 runs=[_run("security-gates")])
        conds = _pr_node(_build(_snapshot([pr])), 10)["missing_conditions"]
        self.assertIn("REQUIRED_RUN_MISSING:tool-manifest", conds)

    def test_glob_double_star_spans_directories_single_star_does_not(self):
        self.assertTrue(rgv.glob_matches("tools/**", "tools/a/b/c.py"))
        self.assertFalse(rgv.glob_matches("tools/**", "toolsx.py"))
        self.assertFalse(rgv.glob_matches("tools/*", "tools/a/b.py"))
        self.assertTrue(rgv.glob_matches("tools/*", "tools/b.py"))

    def test_parse_workflow_reads_pull_request_paths_only(self):
        name, paths = rgv.parse_workflow(WF_TOOL_MANIFEST)
        self.assertEqual(name, "tool-manifest")
        self.assertEqual(paths, ["tools/**", "scripts/**"])
        name, paths = rgv.parse_workflow(WF_SECURITY)
        self.assertEqual((name, paths), ("security-gates", None))


class LaneAndTerminalTests(unittest.TestCase):
    def test_merged_pr_is_terminal_with_no_conditions(self):
        pr = _pr(number=791, merged=True, state="closed", body="Closes #800")
        view = _build(_snapshot([pr]))
        node = _pr_node(view, 791)
        self.assertEqual(node["lane"], "TERMINAL")
        self.assertEqual(node["state"], "merged")
        self.assertEqual(node["missing_conditions"], [])

    def test_draft_is_draft_lane(self):
        view = _build(_snapshot([_pr(draft=True)]))
        self.assertEqual(_pr_node(view, 10)["missing_conditions"], ["DRAFT"])

    def test_unresolved_issue_reference_is_marked(self):
        view = _build(_snapshot([_pr(body="Refs #999")], issues={}))
        issue = next(n for n in view["nodes"] if n["id"] == "ISSUE#999")
        self.assertEqual(issue["state"], "UNRESOLVED")


class SnapshotAndAuthorityTests(unittest.TestCase):
    def test_errors_or_truncation_mark_snapshot_incomplete(self):
        """AC5: never silently partial."""
        self.assertEqual(_build(_snapshot([_pr()], errors=["list open PRs: HTTP 403"]))["snapshot"]["status"], "INCOMPLETE")
        self.assertEqual(_build(_snapshot([_pr()], truncated=True))["snapshot"]["status"], "INCOMPLETE")
        self.assertEqual(_build(_snapshot([_pr()]))["snapshot"]["status"], "OK")

    def test_every_output_carries_no_authority(self):
        """AC4: authority fields on the view and in the rendered markdown."""
        view = _build(_snapshot([_pr(body="Closes #800")]))
        for field, expected in {"authority_effect": "NONE", "can_admit": False,
                                "can_merge": False, "merge_authority": False,
                                "execution_authorized": False}.items():
            self.assertEqual(view[field], expected, field)
        self.assertIn("Authority: **NONE**", rgv.render_markdown(view))

    def test_output_contains_no_coordinator_command_or_approval_instruction(self):
        """AC3: descriptive text only."""
        pr = _pr(body="Closes #800", reviews=[], runs=[])
        view = _build(_snapshot([pr], errors=["x"]))
        text = json.dumps(view) + rgv.render_markdown(view)
        for forbidden in ("/coordinator", "/admission-", "/admit", "/approve", "APPROVE this"):
            self.assertNotIn(forbidden, text)

    def test_build_is_deterministic(self):
        """AC1: same inputs, same bytes."""
        snap = _snapshot([_pr(number=12), _pr(number=3, body="Closes #800")])
        a = json.dumps(_build(snap), sort_keys=True)
        b = json.dumps(_build(snap), sort_keys=True)
        self.assertEqual(a, b)
        numbers = [n["number"] for n in _build(snap)["nodes"] if n["kind"] == "PULL_REQUEST"]
        self.assertEqual(numbers, [3, 12])


class WriteGuardTests(unittest.TestCase):
    def test_writes_exactly_two_files_into_research_graph(self):
        view = _build(_snapshot([_pr()]))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "research-graph"
            rgv.write_outputs(view, out)
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["GRAPH.md", "graph.json"])

    def test_refuses_any_other_output_directory(self):
        view = _build(_snapshot([_pr()]))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                rgv.write_outputs(view, Path(tmp) / "elsewhere")

    def test_module_has_no_dependency_on_gate_code(self):
        """Independence: no import of the admission gate's trusted tools."""
        source = (TOOLS / "research_graph_view.py").read_text(encoding="utf-8")
        imports = [ln for ln in source.splitlines()
                   if ln.lstrip().startswith(("import ", "from "))]
        self.assertFalse(any("repository_coordinator" in ln for ln in imports), imports)

    def test_client_is_get_only(self):
        source = (TOOLS / "research_graph_view.py").read_text(encoding="utf-8")
        for verb in ("POST", "PATCH", "PUT", "DELETE"):
            self.assertNotIn(f'method="{verb}"', source)


class RepoConsistencyTests(unittest.TestCase):
    def test_required_run_names_exist_as_workflow_names_on_disk(self):
        """Every required name must be a real workflow `name:` in this repo."""
        wf_dir = ROOT / ".github" / "workflows"
        if not wf_dir.is_dir():
            self.skipTest("workflows directory not present")
        names = set(rgv.workflow_index([p.read_text(encoding="utf-8")
                                        for p in wf_dir.glob("*.yml")]))
        missing = [n for n in rgv.REQUIRED_RUN_NAMES if n not in names]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
