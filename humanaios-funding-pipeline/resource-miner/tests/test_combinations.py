import copy
import json
import unittest
from pathlib import Path

from resource_miner.combinations import evaluate_combinations, load_snapshot

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "data/experiments/resource_complementarity_pilot.v1.json").read_text())


def row(resource_id, affordance, source, *, deadline=None):
    return dict(resource_id=resource_id, resource_affordances=[affordance],
                source_url=f"https://{source}/", evidence=[{"kind": "discovery", "url": f"https://{source}/"}],
                eligibility_assessed=False, authority_effect="NONE", resource_state="CANDIDATE",
                user_disposition="UNSET", route="WATCH", status="ACTIVE", deadline=deadline)


def setup():
    rows = [row("A", "compute", "one.example"), row("B", "infra", "two.example"), row("C", "api", "three.example")]
    cfg = {"as_of": "2026-10-14", "candidate_ids": ["A", "B", "C"],
           "target_affordances": ["compute", "infra", "api"],
           "assumed_review_minutes": {"A": 30, "B": 45, "C": 45},
           "review_budget_minutes": 120}
    return rows, cfg


class ComplementarityTests(unittest.TestCase):
    def test_real_snapshots_from_three_distinct_providers(self):
        rows = load_snapshot(ROOT / "data/resources.snapshot.jsonl")
        out = evaluate_combinations(rows, CONFIG)
        self.assertEqual(out["baseline_single"]["coverage_count"], 1)
        self.assertEqual(out["best_multi_resource"]["coverage_count"], 3)
        self.assertEqual(out["incremental_reported_coverage"], 2)
        self.assertEqual(len(out["best_multi_resource"]["source_hosts"]), 3)
        self.assertEqual(out["verified_synergy"], "NOT_ESTABLISHED")
        self.assertEqual(out["authority_effect"], "NONE")
        self.assertEqual(out["action_requests"], [])
        self.assertTrue(out["best_multi_resource"]["needs_eligibility_verification"])

    def test_budget_dispatch_and_no_false_gain(self):
        rows, cfg = setup()
        cfg["review_budget_minutes"] = 80
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["best_multi_resource"]["coverage_count"], 2)
        self.assertEqual(out["incremental_reported_coverage"], 1)
        cfg["review_budget_minutes"] = 50
        out = evaluate_combinations(rows, cfg)
        self.assertIsNone(out["best_multi_resource"])
        self.assertIsNone(out["incremental_reported_coverage"])

    def test_deadline_passed_and_archived_are_excluded(self):
        rows, cfg = setup()
        rows[2]["deadline"] = "2026-10-11"
        rows[1]["route"] = "ARCHIVE"
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["rejected"], {"B": "ARCHIVED", "C": "DEADLINE_PASSED"})
        self.assertIsNone(out["best_multi_resource"])

    def test_pass_and_fake_authority_fail_closed(self):
        rows, cfg = setup()
        rows[0]["user_disposition"] = "PASS"
        rows[1]["authority_effect"] = "ADMIT"
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["rejected"], {"A": "USER_EXCLUDED", "B": "CLAIMED_AUTHORITY"})
        self.assertEqual(out["authorization_state"], "NOT_REQUESTED")

    def test_no_source_evidence_excludes(self):
        rows, cfg = setup()
        rows[1]["evidence"] = []
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["rejected"]["B"], "NO_BOUND_SOURCE_EVIDENCE")

    def test_wrong_source_evidence_cannot_launder_record(self):
        rows, cfg = setup()
        rows[0]["evidence"] = [{"kind": "discovery", "url": "https://wrong.example/"}]
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["rejected"]["A"], "NO_BOUND_SOURCE_EVIDENCE")

    def test_missing_ids_or_duplicate_observation_rejected(self):
        rows, cfg = setup()
        with self.assertRaisesRegex(ValueError, "Missing snapshot candidates"):
            evaluate_combinations(rows[:-1], cfg)
        with self.assertRaisesRegex(ValueError, "Duplicate candidate"):
            evaluate_combinations(rows + [copy.deepcopy(rows[0])], cfg)

    def test_unbounded_or_unpriced_input_rejected(self):
        rows, cfg = setup()
        del cfg["assumed_review_minutes"]["C"]
        with self.assertRaisesRegex(ValueError, "explicit review cost"):
            evaluate_combinations(rows, cfg)
        cfg["assumed_review_minutes"]["C"] = 45
        cfg["review_budget_minutes"] = -1
        with self.assertRaisesRegex(ValueError, "non-negative"):
            evaluate_combinations(rows, cfg)
        cfg["review_budget_minutes"] = 120
        cfg["candidate_ids"] = ["A"] * 9
        with self.assertRaisesRegex(ValueError, "1..8"):
            evaluate_combinations(rows, cfg)

    def test_determinism_and_no_verified_synergy_from_coverage(self):
        rows, cfg = setup()
        self.assertEqual(evaluate_combinations(rows, cfg), evaluate_combinations(rows, cfg))
        for item in evaluate_combinations(rows, cfg).values():
            self.assertNotEqual(item, "VERIFIED")
        rows[2]["resource_affordances"] = ["infra"]
        out = evaluate_combinations(rows, cfg)
        self.assertEqual(out["incremental_reported_coverage"], 1)
        self.assertEqual(out["verified_synergy"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
