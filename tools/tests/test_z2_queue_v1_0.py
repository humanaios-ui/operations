"""
test_z2_queue_v1_0.py
Builder v1.7 compliant
HumanAIOS

Focused regression tests for tools/z2_queue_v1_0.py.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_NAME = "test_z2_queue_v1_0"
TOOL_VERSION = "1.0.0"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import z2_queue_v1_0 as z2_queue  # noqa: E402


class TestZ2QueueLocalFallback(unittest.TestCase):
    def setUp(self) -> None:
        self._old_url = os.environ.get("SUPABASE_URL")
        self._old_key = os.environ.get("SUPABASE_KEY")
        os.environ.pop("SUPABASE_URL", None)
        os.environ.pop("SUPABASE_KEY", None)
        self.tmpdir = tempfile.TemporaryDirectory()
        self.local_path = str(Path(self.tmpdir.name) / "queue.jsonl")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        if self._old_url is None:
            os.environ.pop("SUPABASE_URL", None)
        else:
            os.environ["SUPABASE_URL"] = self._old_url
        if self._old_key is None:
            os.environ.pop("SUPABASE_KEY", None)
        else:
            os.environ["SUPABASE_KEY"] = self._old_key

    def test_append_entry_falls_back_to_local_when_supabase_missing(self) -> None:
        entry = {
            "id_slug": "IC-CAND-LOCAL",
            "class": "IC",
            "synopsis": "local fallback test",
            "zone2_ratification": "Night - S-TEST",
        }

        result = z2_queue.append_entry(entry, "S-TEST-1", self.local_path)

        self.assertTrue(result["written"])
        self.assertEqual(result["target"], "local_fallback")

        rows = z2_queue.load_local_fallback(self.local_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id_slug"], "IC-CAND-LOCAL")
        self.assertFalse(rows[0]["synced"])
        self.assertTrue(rows[0]["pending_sync"])

    def test_missing_ratification_is_rejected_before_any_write(self) -> None:
        entry = {
            "id_slug": "IC-CAND-BAD",
            "class": "IC",
            "synopsis": "missing ratification",
        }

        result = z2_queue.append_entry(entry, "S-TEST-1", self.local_path)

        self.assertFalse(result["written"])
        self.assertIn("zone2_ratification", result["missing"])
        self.assertEqual(z2_queue.load_local_fallback(self.local_path), [])


def run_smoke_test() -> bool:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestZ2QueueLocalFallback)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=0).run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if run_smoke_test() else 1)
