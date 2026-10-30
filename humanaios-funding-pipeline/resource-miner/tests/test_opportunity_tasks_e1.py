"""Fail-closed tests for E1; no provider attestation is implied."""
import copy
import json
from pathlib import Path
import unittest
from resource_miner.opportunity_tasks_e1 import project_task_milestones

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "odin_tasks_e1.json"

class TestTaskMilestones(unittest.TestCase):
    def specimen(self):
        return json.loads(FIXTURE.read_text())
    def test_real_pilot_stays_blocked_not_paid(self):
        r = project_task_milestones(self.specimen())
        self.assertEqual(r["approved_count"], 3)
        self.assertEqual(r["state"], "BLOCKED_HARDWARE")
        self.assertEqual(r["payment"], "UNVERIFIED")
        self.assertEqual(r["recordings_submitted"], "UNVERIFIED")
        self.assertFalse(r["can_record"])
    def test_duplicate_and_order_idempotent(self):
        x = self.specimen()
        original = project_task_milestones(x)
        x["events"].reverse()
        x["events"].append(copy.deepcopy(x["events"][0]))
        self.assertEqual(original, project_task_milestones(x))
    def test_conflict_fails(self):
        x = self.specimen()
        duplicate = dict(x["events"][0], evidence_ref="OTHER")
        x["events"].append(duplicate)
        with self.assertRaises(ValueError):
            project_task_milestones(x)
    def test_human_approval_fails(self):
        x = self.specimen()
        x["events"][0]["source_kind"] = "HUMAN_REPORT"
        with self.assertRaises(ValueError):
            project_task_milestones(x)
    def test_fake_release_fails(self):
        x = self.specimen()
        x["events"].append(dict(x["events"][0], event_id="E5", kind="HARDWARE_VERIFIED"))
        with self.assertRaises(ValueError):
            project_task_milestones(x)
    def test_private_payload_fails(self):
        x = self.specimen()
        x["events"][0]["email_body"] = "secret"
        with self.assertRaises(ValueError):
            project_task_milestones(x)

if __name__ == "__main__":
    unittest.main()
