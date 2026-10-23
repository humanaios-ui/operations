"""Falsifier tests for architecture/operations_canvas.py.

These check the canvas contract: display only, no authority, registry counts
parsed from the source files, and no script that could close its own data tag.
"""
import json
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


class RenderTest(unittest.TestCase):
    def test_embedded_json_cannot_close_its_script_tag(self):
        data = oc.build_canvas(ATLAS_FIXTURE, ZONE_FIXTURE, PLANNED_FIXTURE)
        data["code_graph"]["limitations"] = ["</script><script>alert(1)</script>"]
        page = oc.render_html(data)
        self.assertNotIn("</script><script>alert", page)
        self.assertIn("<\\/script>", page)

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
