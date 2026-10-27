"""Falsifier tests for architecture/operations_canvas.py.

These check the canvas contract: display only, no authority, registry counts
parsed from the source files, and no script that could close its own data tag.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "architecture"))

import operations_canvas as oc  # noqa: E402

ZONE_FIXTURE = """# ZONE_REGISTRY.md — 3-Zone Ecosystem Map

| Zone ID | Repo Name | Purpose | Z3 Executor | Resource Cap | Status |
|:--------|:----------|:--------|:-----------|:-------------|:-------|
| Z-000 | operations | Governance | TBD | 80 units/cycle | ✅ ACTIVE |
| Z-008 | lasting-light-ai | Research repo | RQ1/RQ2/RQ3 only | TBD | 30 units/cycle | ⚠️ LIMITED |
| Z-011 | research | Frozen papers archive | 🔒 READ-ONLY |
| Z-013+ | See PLANNED_REPOS.md | PLANNED | Phases 2–3 | 12 planned |
"""

PLANNED_FIXTURE = """| Status | Meaning | Z2 Action | Z3 Action |
|:--------|:--------|:---|:---|
| **PLANNED** | Planned but never created | Approve | Monitor |
| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **website** | PLANNED | Night | Landing page | Phase 1 (infrastructure) |
| **empirica-autonomy-archive** | ARCHIVED | Night | Snapshots | N/A |
| Repo | Status | Z2 Authority | Notes | Roadmap Phase |
|:-----|:--------|:---|:---|:---|
| **Repo A** | Other HumanAIOS org | UNKNOWN | Night | Phase 1b |
"""

ATLAS_FIXTURE = {
    "head_sha": "a" * 40,
    "nodes": [
        {"id": "tools", "label": "Operational Tools", "file_count": 3},
        {"id": "docs", "label": "Docs & Design", "file_count": 2},
    ],
    "edges": [{"source": "tools", "target": "docs", "kind": "doc_link", "count": 1}],
    "coverage": {"tracked_files": 5, "mapped_files": 5, "unmapped_files": 0},
    "limitations": ["Static source links do not prove runtime execution."],
}


class ParseRegistryTest(unittest.TestCase):
    def test_zone_rows_parsed_with_status_and_cap(self):
        rows, claimed = oc.parse_zone_registry(ZONE_FIXTURE)
        self.assertEqual(claimed, 3)
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(by_id["Z-000"]["status"], "ACTIVE")
        self.assertEqual(by_id["Z-000"]["cap"], 80)
        self.assertEqual(by_id["Z-008"]["status"], "LIMITED")
        self.assertEqual(by_id["Z-008"]["cap"], 30)
        self.assertEqual(by_id["Z-011"]["status"], "READ-ONLY")
        self.assertIsNone(by_id["Z-011"]["cap"])

    def test_status_reads_final_column_only(self):
        # Free-text purpose mentioning ACTIVE must not change an ARCHIVED-status row.
        text = "| Z-020 | sample | purpose says ACTIVE | TBD | 10 units/cycle | ARCHIVED |\n"
        rows, _ = oc.parse_zone_registry(text)
        self.assertEqual(rows[0]["status"], "UNKNOWN")

    def test_pointer_row_is_not_a_zone(self):
        rows, _ = oc.parse_zone_registry(ZONE_FIXTURE)
        self.assertFalse(any("+" in r["id"] for r in rows))

    def test_planned_legend_rows_are_skipped(self):
        rows = oc.parse_planned_repos(PLANNED_FIXTURE)
        names = [r["name"] for r in rows]
        self.assertNotIn("PLANNED", names)
        self.assertIn("website", names)
        self.assertIn("Repo A", names)
        self.assertEqual(len(names), len(set(names)))

    def test_archived_and_unknown_statuses_kept(self):
        rows = {r["name"]: r["status"] for r in oc.parse_planned_repos(PLANNED_FIXTURE)}
        self.assertEqual(rows["empirica-autonomy-archive"], "ARCHIVED")
        self.assertEqual(rows["Repo A"], "UNKNOWN")


class BuildCanvasTest(unittest.TestCase):
    def setUp(self):
        self.data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)

    def test_authority_is_none_and_not_ratified(self):
        self.assertEqual(self.data["authority_effect"], "NONE")
        self.assertFalse(self.data["ratified"])

    def test_header_mismatch_is_reported_not_hidden(self):
        checks = self.data["registry_checks"]
        self.assertEqual(checks["registry_header_claims"], 3)
        self.assertEqual(checks["registry_rows_counted"], 6)
        self.assertFalse(checks["header_matches_rows"])

    def test_source_head_pinned_from_atlas(self):
        self.assertEqual(self.data["source_head"], "a" * 40)

    def test_real_registry_counts_are_visible(self):
        real = oc.build_canvas(
            ATLAS_FIXTURE,
            (REPO / "ZONE_REGISTRY.md").read_text(encoding="utf-8"),
            (REPO / "PLANNED_REPOS.md").read_text(encoding="utf-8"),
        )
        statuses = [r["status"] for r in real["repo_map"]]
        self.assertEqual(statuses.count("ACTIVE"), 9)
        self.assertEqual(statuses.count("LIMITED"), 3)
        self.assertEqual(statuses.count("READ-ONLY"), 1)


CLEAN = dict(ATLAS_FIXTURE, snapshot="HEAD_WORKTREE", worktree_clean=True)


class ProvenanceTest(unittest.TestCase):
    def test_clean_head_snapshot_generated_this_run_is_verified(self):
        prov = oc.provenance_from_atlas(CLEAN, oc.GENERATED_SOURCE)
        self.assertTrue(prov["verified"])
        self.assertEqual(prov["snapshot"], "HEAD_WORKTREE")

    def test_clean_supplied_atlas_is_not_verified(self):
        # A supplied file's self-reported fields cannot be checked here.
        prov = oc.provenance_from_atlas(CLEAN, oc.SUPPLIED_SOURCE)
        self.assertFalse(prov["verified"])
        self.assertEqual(prov["source"], oc.SUPPLIED_SOURCE)

    def test_dirty_worktree_is_not_verified_and_keeps_its_marker(self):
        atlas = dict(ATLAS_FIXTURE, snapshot="UNVERIFIED_WORKTREE", worktree_clean=False)
        prov = oc.provenance_from_atlas(atlas, oc.GENERATED_SOURCE)
        self.assertFalse(prov["verified"])
        self.assertEqual(prov["snapshot"], "UNVERIFIED_WORKTREE")
        self.assertIs(prov["worktree_clean"], False)

    def test_missing_provenance_is_not_verified(self):
        prov = oc.provenance_from_atlas({"head_sha": "b" * 40}, oc.GENERATED_SOURCE)
        self.assertFalse(prov["verified"])
        self.assertIsNone(prov["snapshot"])

    def test_text_equivalent_block_present(self):
        page = oc.render_html(oc.build_canvas(CLEAN, ZONE_FIXTURE, PLANNED_FIXTURE))
        self.assertIn('id="edge-rows"', page)
        self.assertIn('id="node-rows"', page)


# Runs the rendered page script against a small DOM stub. Counts the warning
# elements the page actually creates, so the test checks behavior, not source text.
DOM_HARNESS = r"""
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const made = [];
function mk(tag) {
  const e = {
    tagName: tag, children: [], attrs: {}, className: "", textContent: "",
    parentNode: null, nextSibling: null,
    setAttribute(k, v) { this.attrs[k] = String(v); },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c; },
    insertBefore(c) { this.children.push(c); c.parentNode = this; return c; },
  };
  made.push(e);
  return e;
}
const byId = {};
byId["canvas-data"] = mk("script");
byId["canvas-data"].textContent = input.data;
byId["intro"] = mk("p");
byId["intro"].parentNode = mk("header");
global.document = {
  getElementById(id) { return byId[id] || (byId[id] = mk(id)); },
  createElement: mk,
  createElementNS(ns, tag) { return mk(tag); },
};
eval(input.script);
console.log(JSON.stringify({ warnings: made.filter((e) => e.className === "warn").length }));
"""


def run_page_script(data):
    page = oc.render_html(data)
    payload = re.search(r'<script id="canvas-data" type="application/json">(.*?)</script>', page, re.S)
    scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
    request = json.dumps({"data": payload.group(1), "script": scripts[-1]})
    result = subprocess.run(
        ["node", "-e", DOM_HARNESS], input=request, capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


class RenderedWarningTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("node"), "node is required to run the page script")

    def test_unverified_input_creates_warning_element(self):
        atlas = dict(ATLAS_FIXTURE, snapshot="UNVERIFIED_WORKTREE", worktree_clean=False)
        data = oc.build_canvas(atlas, ZONE_FIXTURE, PLANNED_FIXTURE, oc.GENERATED_SOURCE)
        self.assertEqual(run_page_script(data)["warnings"], 1)

    def test_verified_input_creates_no_warning_element(self):
        data = oc.build_canvas(CLEAN, ZONE_FIXTURE, PLANNED_FIXTURE, oc.GENERATED_SOURCE)
        self.assertEqual(run_page_script(data)["warnings"], 0)

    def test_supplied_file_creates_warning_element(self):
        data = oc.build_canvas(CLEAN, ZONE_FIXTURE, PLANNED_FIXTURE, oc.SUPPLIED_SOURCE)
        self.assertEqual(run_page_script(data)["warnings"], 1)


class RenderTest(unittest.TestCase):
    def test_embedded_json_cannot_close_its_script_tag(self):
        data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)
        data["code_graph"]["limitations"] = ["</script><script>alert(1)</script>"]
        page = oc.render_html(data)
        self.assertNotIn("</script><script>alert", page)
        self.assertIn("\\u003c/script\\u003e", page)

    def test_comment_and_script_openers_are_escaped(self):
        data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)
        data["code_graph"]["limitations"] = ["<!--<script>x&y\u2028z"]
        page = oc.render_html(data)
        self.assertNotIn("<!--<script>", page)
        self.assertIn("\\u003c!--\\u003cscript\\u003e", page)
        self.assertIn("\\u0026", page)
        self.assertIn("\\u2028", page)
        # The payload must still parse back to the original text.
        payload = re.search(r'<script id="canvas-data" type="application/json">(.*?)</script>', page, re.S)
        self.assertEqual(json.loads(payload.group(1))["code_graph"]["limitations"], ["<!--<script>x&y\u2028z"])

    def test_page_loads_no_external_scripts(self):
        data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)
        page = oc.render_html(data)
        self.assertNotIn("<script src=", page)

    def test_write_outputs_round_trip(self):
        data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            out = oc.write_outputs(data, Path(tmp) / "canvas")
            back = json.loads((out / "canvas.json").read_text(encoding="utf-8"))
            self.assertEqual(back["authority_effect"], "NONE")
            self.assertTrue((out / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
