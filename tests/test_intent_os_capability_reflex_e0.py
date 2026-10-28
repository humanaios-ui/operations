import unittest
from tools.intent_os_capability_reflex_e0 import route, project

class ReflexTests(unittest.TestCase):
    def test_no_execution(self):
        result = route("Find resources", ["resource_discovery"])
        self.assertEqual(result["execution"], "DISABLED")
        self.assertEqual(result["capabilities"][0]["status"], "AVAILABLE")
        self.assertEqual(result["capabilities"][1]["status"], "NOT_VERIFIED")

    def test_missing_receipt(self):
        result = project({}, [{"state": "SUPPORTED", "source_ref": "issue:1", "revision": "abc"}])
        self.assertIn("INDEPENDENT_RECEIPT_MISSING", [x["gap"] for x in result["witness_evidence_gaps"]])
        self.assertEqual(result["human_outcomes_verified"], 0)

    def test_graphs_are_non_authoritative(self):
        result = project({"system": {"source_ref": "system_graph.json", "revision": "abc"}}, [])
        self.assertEqual(result["graph_observations"][0]["state"], "UNVERIFIED")

    def test_unknown_graph_fails(self):
        with self.assertRaises(ValueError):
            project({"fake": {"source_ref": "x", "revision": "y"}}, [])

    def test_unknown_state_fails(self):
        with self.assertRaises(ValueError):
            project({}, [{"state": "APPROVED"}])

    def test_empty_objective_fails(self):
        with self.assertRaises(ValueError):
            route(" ")

if __name__ == "__main__":
    unittest.main()
