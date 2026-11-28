"""Parser smoke test for the workflow inventory renderer."""

import tempfile
import unittest
from pathlib import Path

import tools.render_workflow_inventory as inv


SAMPLE = """\
name: example
on:
  pull_request:
    types: [opened]
  schedule:
    - cron: "15 4 * * 1"
  workflow_dispatch: {}

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
"""


class RenderWorkflowInventoryTest(unittest.TestCase):
    def test_parse_triggers_and_cron(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example.yml"
            path.write_text(SAMPLE, encoding="utf-8")
            row = inv.parse_workflow(path)
        self.assertEqual(row["name"], "example")
        self.assertEqual(row["triggers"], ["pull_request", "schedule", "workflow_dispatch"])
        self.assertEqual(row["crons"], ["15 4 * * 1"])
        self.assertEqual(row["duplicates"], [])
        self.assertTrue(row["has_on"])

    def test_duplicate_top_level_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.yml"
            path.write_text("name: one\nname: two\non: push\n", encoding="utf-8")
            row = inv.parse_workflow(path)
        self.assertIn("name", row["duplicates"])

    def test_marked_region_round_trip(self):
        rows = inv.load()
        self.assertGreaterEqual(len(rows), 100)
        document = inv.DOC.read_text(encoding="utf-8")
        updated = inv.replace_region(document, inv.render(rows))
        self.assertEqual(updated, document)

    def test_scalar_and_quoted_on(self):
        row = inv.parse_text("name: s\non: push\njobs: {}\n", "s.yml")
        self.assertEqual(row["triggers"], ["push"])
        self.assertTrue(row["has_on"])
        row = inv.parse_text("name: q\n\"on\":\n  workflow_dispatch: {}\n", "q.yml")
        self.assertEqual(row["triggers"], ["workflow_dispatch"])
        self.assertEqual(row["status"], "manual only")
        row = inv.parse_text("name: l\non: [push, pull_request]\n", "l.yml")
        self.assertEqual(row["triggers"], ["push", "pull_request"])

    def test_status_from_marker_and_schedule(self):
        paused = "name: p\n# Schedule paused by Q-AGENT-WORKFLOWS-01 W2 (2026-11-26): x.\non:\n  workflow_dispatch: {}\n"
        self.assertEqual(inv.parse_text(paused, "p.yml")["status"], "paused")
        self.assertEqual(inv.parse_text(SAMPLE, "e.yml")["status"], "timer")
        self.assertEqual(inv.parse_text("name: n\njobs: {}\n", "n.yml")["status"], "no trigger")

    def test_runs_report_uses_injected_fetch(self):
        rows = [inv.parse_text(SAMPLE, "example.yml")]
        out = inv.render_runs(rows, 3, fetch=lambda f, n: ["success", "failure", "cancelled"])
        self.assertIn("| `example.yml` | timer | 3 | 1 | 1 | 1 |", out)

    def test_smoke_test_passes(self):
        self.assertEqual(inv.run_smoke_test(), 0)


if __name__ == "__main__":
    unittest.main()
