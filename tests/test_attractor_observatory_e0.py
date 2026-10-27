"""Falsifiers for the read-only Attractor Observatory E0."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "attractor_observatory_e0.py"
SPEC = importlib.util.spec_from_file_location("attractor_e0", SOURCE)
observer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observer)

REV = "a" * 40
DIGEST = hashlib.sha256(b"fixture-only").hexdigest()
WHEN = "2026-10-26T00:00:00Z"
GRAPH = {
    "generated_at": WHEN,
    "nodes": {v: {"id": v} for v in ("A", "B", "C")},
    "edges": [
        {"source": "A", "target": "B"},
        {"source": "B", "target": "A"},
        {"source": "B", "target": "C"},
    ],
    "validation_status": {"valid": False, "errors": ["Cycle detected"]},
}


def trail(node, step):
    return {
        "trail_id": "T1", "actor_kind": "agent", "actor_id": "agent-1",
        "step": step, "node_id": node, "observed_at": WHEN,
        "source_ref": "fixture:trail", "source_revision": REV,
    }


def event(event_type="RESOURCE_ACQUIRED"):
    row = {
        "event_id": "E1", "objective_id": "OBJ-1",
        "event_type": event_type, "process_id": "B",
        "observed_at": WHEN, "source_ref": "fixture:receipt",
        "source_revision": REV, "evidence_digest": DIGEST,
        "observer_id": "agent-1", "resource_id": "RES-1",
        "reviewer_id": "reviewer-1", "review_verdict": "SUPPORTS",
    }
    return row


class AttractorTests(unittest.TestCase):
    def test_first_link_cycles_are_not_terminal_claims(self):
        report = observer.build(GRAPH)
        self.assertEqual(report["internal"]["node_count"], 3)
        self.assertEqual(report["internal"]["edge_count"], 3)
        self.assertEqual(report["internal"]["first_stored_edge_loop_starts"], 2)
        comps = report["internal"]["strongly_connected_components"]
        cyclic = next(c for c in comps if c["size"] == 2)
        self.assertTrue(cyclic["cyclic"])
        self.assertFalse(cyclic["terminal"])  # B can exit to C.
        self.assertEqual(cyclic["reachable_from_start_count"], 2)
        self.assertEqual(report["source_graph_validation"], GRAPH["validation_status"])

    def test_no_events_means_not_measured_not_zero(self):
        report = observer.build(GRAPH)
        self.assertEqual(report["observed_returns"]["state"], "NOT_MEASURED")
        self.assertIsNone(report["observed_returns"]["trails"])
        self.assertIsNone(report["external_conversion"]["outcomes"])
        self.assertEqual(report["external_conversion"]["state"], "NOT_MEASURED")

    def test_empty_window_is_different_from_missing_input(self):
        report = observer.build(GRAPH, [], [])
        self.assertEqual(report["observed_returns"]["state"], "EMPTY_OBSERVATION_WINDOW")
        self.assertEqual(report["observed_returns"]["trails"], 0)
        self.assertEqual(report["external_conversion"]["event_count"], 0)

    def test_actual_return_counts_are_observations_not_structure(self):
        report = observer.build(GRAPH, [trail("A", 0), trail("B", 1), trail("A", 2)])
        self.assertEqual(report["observed_returns"]["trails"], 1)
        self.assertEqual(report["observed_returns"]["repeated_returns"],
                         [{"node_id": "A", "extra_visits_in_trails": 1}])
        self.assertEqual(report["observed_returns"]["by_actor_kind"]["agent"], 1)

    def test_invalid_trail_transition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "edge absent"):
            observer.build(GRAPH, [trail("A", 0), trail("C", 1)])

    def test_gap_or_duplicate_step_rejected(self):
        with self.assertRaisesRegex(ValueError, "without duplicates or gaps"):
            observer.build(GRAPH, [trail("A", 0), trail("B", 2)])

    def test_unobserved_actor_switch_rejected(self):
        rows = [trail("A", 0), trail("B", 1)]
        rows[1]["actor_kind"] = "decision"
        with self.assertRaisesRegex(ValueError, "changes actor"):
            observer.build(GRAPH, rows)

    def test_source_commit_required_for_trails(self):
        rows = [trail("A", 0)]
        rows[0]["source_revision"] = "main"
        with self.assertRaisesRegex(ValueError, "40-character"):
            observer.build(GRAPH, rows)

    def test_external_success_is_only_an_unverified_assertion(self):
        report = observer.build(GRAPH, outcomes=[event()])
        x = report["external_conversion"]
        self.assertEqual(x["outcomes"]["RESOURCE_ACQUIRED"], 1)
        self.assertEqual(x["separately_review_attested_outcomes"]["RESOURCE_ACQUIRED"], 1)
        self.assertIn("NOT_INDEPENDENTLY_AUTHENTICATED", x["state"])
        self.assertEqual(x["by_process"][0]["process_id"], "B")
        self.assertFalse(report["merge_authority"])
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertEqual(report["execution"], "DISABLED")

    def test_self_review_never_counts_as_second_reviewer(self):
        row = event()
        row["reviewer_id"] = row["observer_id"]
        x = observer.build(GRAPH, outcomes=[row])["external_conversion"]
        self.assertEqual(x["outcomes"]["RESOURCE_ACQUIRED"], 1)
        self.assertNotIn("RESOURCE_ACQUIRED", x["separately_review_attested_outcomes"])

    def test_non_outcome_is_never_conversion(self):
        row = event("CANDIDATE_IDENTIFIED")
        x = observer.build(GRAPH, outcomes=[row])["external_conversion"]
        self.assertEqual(x["outcomes"], {})
        self.assertEqual(x["by_process"], [])

    def test_existing_inventory_is_not_new_acquisition(self):
        row = event("RESOURCE_INVENTORIED")
        x = observer.build(GRAPH, outcomes=[row])["external_conversion"]
        self.assertEqual(x["outcomes"], {})

    def test_benefit_requires_pseudonymous_receipt_identifiers(self):
        row = event("RECOVERY_BENEFIT_DELIVERED")
        with self.assertRaisesRegex(ValueError, "benefit requires"):
            observer.build(GRAPH, outcomes=[row])
        row["benefit_id"] = "BEN-1"
        row["beneficiary_alias"] = "PSEUDONYM-1"
        x = observer.build(GRAPH, outcomes=[row])["external_conversion"]
        self.assertEqual(x["outcomes"]["RECOVERY_BENEFIT_DELIVERED"], 1)
        self.assertNotIn("PSEUDONYM-1", json.dumps(x))

    def test_private_fields_are_rejected_not_exported(self):
        row = event()
        row["resume_text"] = "sensitive"
        with self.assertRaisesRegex(ValueError, "invalid record keys"):
            observer.build(GRAPH, outcomes=[row])

    def test_duplicate_acquisition_claim_rejected(self):
        row = event()
        with self.assertRaisesRegex(ValueError, "duplicate external event"):
            observer.build(GRAPH, outcomes=[row, copy.deepcopy(row)])

    def test_malformed_provenance_rejected(self):
        row = event()
        row["evidence_digest"] = "unverified"
        with self.assertRaisesRegex(ValueError, "digest invalid"):
            observer.build(GRAPH, outcomes=[row])

    def test_unauthorized_status_and_eligibility_rejected(self):
        row = event()
        row["eligibility_verified"] = True
        with self.assertRaisesRegex(ValueError, "invalid record keys"):
            observer.build(GRAPH, outcomes=[row])

    def test_unmapped_process_is_explicit(self):
        row = event()
        row["process_id"] = "resource_miner:discovery"
        x = observer.build(GRAPH, outcomes=[row])["external_conversion"]
        self.assertEqual(x["unmapped_process_ids"], ["resource_miner:discovery"])

    def test_dangling_graph_edge_fails_closed(self):
        bad = copy.deepcopy(GRAPH)
        bad["edges"][1]["target"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "dangling"):
            observer.build(bad)

    def test_same_input_deterministic(self):
        a = observer.build(GRAPH, [trail("A", 0)], [event()])
        b = observer.build(copy.deepcopy(GRAPH), [trail("A", 0)], [event()])
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_cli_real_graph_smoke_does_not_write_repository(self):
        real_graph = SOURCE.parents[1] / "system_graph.json"
        if not real_graph.exists():
            self.skipTest("source graph not in test checkout")
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "report.json"
            result = subprocess.run(
                [sys.executable, str(SOURCE), "--graph", str(real_graph),
                 "--output", str(dest)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(dest.read_text())
            self.assertGreaterEqual(payload["internal"]["node_count"], 3)
            self.assertEqual(payload["authority_effect"], "NONE")
            self.assertEqual(payload["external_conversion"]["state"], "NOT_MEASURED")


if __name__ == "__main__":
    unittest.main()
