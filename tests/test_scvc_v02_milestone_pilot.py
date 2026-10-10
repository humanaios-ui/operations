"""SCVC v0.2 milestone pilot: synthetic-only, no source authority."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments" / "scvc_v02" / "milestone_controller.py"
DEF = ROOT / "experiments" / "scvc_v02" / "milestone_graph.json"
spec = importlib.util.spec_from_file_location("scvc_pilot", SRC)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class MilestonePilotTests(unittest.TestCase):
    def setUp(self):
        self.graph = json.loads(DEF.read_text(encoding="utf-8"))

    def test_frozen_graph_valid(self):
        nodes = pilot.validate(self.graph)
        self.assertEqual([n["id"] for n in nodes], ["SCVC-M0", "SCVC-M1", "SCVC-M2", "SCVC-M3", "SCVC-M4"])

    def test_default_no_attestation(self):
        report = pilot.assess(self.graph)
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertFalse(report["can_authorize"])
        self.assertFalse(report["merge_authority"])
        self.assertFalse(report["authenticated"])
        self.assertFalse(report["has_live_witness"])
        self.assertTrue(all(not m["achieved"] for m in report["milestones"]))
        self.assertEqual(report["milestones"][0]["candidate_status"], "CANDIDATE_EVIDENCE_INCOMPLETE")
        self.assertEqual(report["milestones"][1]["candidate_status"], "BLOCKED_DEPENDENCY_UNATTESTED")

    def test_untrusted_claims_do_not_achieve_milestone(self):
        signals = {"observations": [
            {"milestone_id":"SCVC-M0","predicate":p,"state":"CLAIMED_VERIFIED","ref":"claim:synth"}
            for p in self.graph["milestones"][0]["acceptance"]
        ]}
        report = pilot.assess(self.graph, signals)
        self.assertEqual(report["milestones"][0]["candidate_status"], "AWAITING_INDEPENDENT_VERIFICATION")
        self.assertEqual(report["milestones"][1]["candidate_status"], "BLOCKED_DEPENDENCY_UNATTESTED")
        self.assertTrue(all(not m["achieved"] for m in report["milestones"]))

    def test_output_deterministic(self):
        self.assertEqual(pilot.assess(self.graph), pilot.assess(self.graph))

    def test_duplicate_node_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["milestones"][1]["id"] = "SCVC-M0"
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_future_dependency_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["milestones"][0]["dependencies"] = ["SCVC-M1"]
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_cycle_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["milestones"][0]["dependencies"] = ["SCVC-M4"]
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_missing_dependency_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["milestones"][1]["dependencies"] = ["SCVC-M99"]
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_acceptance_predicate_duplicate_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["milestones"][0]["acceptance"].append("SCVC_V01_EXACT_HEAD")
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_unexpected_authority_field_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["allow_merge"] = True
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_unknown_predicate_rejected(self):
        signals = {"observations": [{"milestone_id":"SCVC-M0","predicate":"SELF_APPROVE",
                                     "state":"CLAIMED_VERIFIED","ref":"self"}]}
        with self.assertRaises(ValueError): pilot.assess(self.graph,signals)

    def test_duplicate_claim_rejected(self):
        obs = {"milestone_id":"SCVC-M0","predicate":"SCVC_V01_EXACT_HEAD",
               "state":"OBSERVED","ref":"obs1"}
        with self.assertRaises(ValueError):
            pilot.assess(self.graph, {"observations":[obs,obs]})

    def test_evidence_payload_not_accepted(self):
        obs = {"milestone_id":"SCVC-M0","predicate":"SCVC_V01_EXACT_HEAD",
               "state":"OBSERVED","ref":"obs1","secret":"not-allowed"}
        with self.assertRaises(ValueError):
            pilot.assess(self.graph, {"observations":[obs]})

    def test_unbounded_and_malformed_claims_rejected(self):
        with self.assertRaises(ValueError):
            pilot.assess(self.graph, {"observations":[],"approval":True})
        with self.assertRaises(ValueError):
            pilot.assess(self.graph, {"observations":[{}]*201})

    def test_claimed_private_locator_rejected(self):
        obs = {"milestone_id":"SCVC-M0","predicate":"SCVC_V01_EXACT_HEAD",
               "state":"OBSERVED","ref":"person@example.com/private"}
        with self.assertRaises(ValueError):
            pilot.assess(self.graph, {"observations":[obs]})

    def test_predecessor_mutation_rejected(self):
        bad = copy.deepcopy(self.graph)
        bad["predecessor_pr"] = 999
        with self.assertRaises(ValueError): pilot.validate(bad)

    def test_unknown_mode_denied(self):
        bad = copy.deepcopy(self.graph)
        bad["mode"]="AUTO_EXECUTE"
        with self.assertRaises(ValueError): pilot.validate(bad)


if __name__ == "__main__":
    unittest.main()
