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


if __name__ == "__main__":
    unittest.main()
