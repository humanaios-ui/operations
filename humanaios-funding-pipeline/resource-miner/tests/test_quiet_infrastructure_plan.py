"""Contract tests for the Quiet Infrastructure plan; no network or deployment."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from resource_miner.planning import (
    miner_requirements_from_plan, resolve_resource_plan, validate_resource_plan,
)

PLAN = Path(__file__).resolve().parents[1] / "data/resource_plans/quiet_infrastructure.seed.json"


class QuietInfrastructurePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_existing_graph_contract_and_authority_boundary(self):
        self.assertIsNone(validate_resource_plan(self.plan))
        self.assertEqual(self.plan["authority_effect"], "NONE")
        self.assertEqual(self.plan["execution"], "DISABLED")
        self.assertEqual(self.plan["status"], "Z1_PROPOSAL_NOT_ADMITTED")
        self.assertEqual(resolve_resource_plan(self.plan)["authority_effect"], "NONE")

    def test_tokens_are_unique_source_linked_and_bounded(self):
        items = self.plan["thesis_tokens"]
        self.assertEqual(len(items), 8)
        self.assertEqual(len(set(x["token_id"] for x in items)), len(items))
        needs = {x["need_id"] for x in self.plan["needs"]}
        states = {"OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED",
                  "UNVERIFIED", "CONTRADICTED"}
        for item in items:
            self.assertIn(item["evidence_state"], states)
            self.assertTrue(item["source_refs"])
            self.assertTrue(item["limitation"])
            self.assertTrue(set(item["maps_to_need_ids"]) <= needs)
        self.assertEqual(next(x for x in items if x["token_id"] == "QI-T07")
                         ["evidence_state"], "UNVERIFIED")

    def test_only_two_external_gaps_feed_existing_miner(self):
        before = copy.deepcopy(self.plan)
        exported = miner_requirements_from_plan(self.plan)
        self.assertEqual({x["requirement_id"] for x in exported},
                         {"RR-QI-HUMAN", "RR-QI-BUYER"})
        self.assertEqual({x["requirement_id"]: x["gap_status"]
                          for x in exported},
                         {"RR-QI-HUMAN": "CONFIRMED",
                          "RR-QI-BUYER": "UNKNOWN"})
        self.assertTrue(all(x["authority_effect"] == "NONE" for x in exported))
        self.assertTrue(all(x["source_plan_id"] == self.plan["plan_id"]
                            for x in exported))
        self.assertEqual(before, self.plan)

    def test_internal_evidence_is_partial_and_pilot_unknown(self):
        rows = {x["requirement_id"]: x for x in
                resolve_resource_plan(self.plan)["resource_requirements"]}
        self.assertEqual(rows["RR-QI-OFFLINE"]["gap_status"], "PARTIAL")
        self.assertEqual(rows["RR-QI-TRACE"]["gap_status"], "PARTIAL")
        self.assertEqual(rows["RR-QI-BUYER"]["gap_status"], "UNKNOWN")
        self.assertFalse(any(x["gap_status"] == "SATISFIED" for x in rows.values()))

    def test_hardware_and_compliance_never_mined_without_new_gate(self):
        rows = {x["requirement_id"]: x for x in
                resolve_resource_plan(self.plan)["resource_requirements"]}
        for key in ("RR-QI-HARDWARE", "RR-QI-COMPLIANCE"):
            self.assertFalse(rows[key]["mine_external"])
            self.assertEqual(rows[key]["gap_status"], "CONDITIONAL")

    def test_escalted_authority_fails_closed(self):
        bad = copy.deepcopy(self.plan)
        bad["authority_effect"] = "APPROVED"
        with self.assertRaisesRegex(ValueError, "Resource planning cannot grant authority"):
            miner_requirements_from_plan(bad)

    def test_business_and_compliance_claims_are_explicitly_unverified(self):
        toks = {x["token_id"]: x for x in self.plan["thesis_tokens"]}
        self.assertIn("No 10x", toks["QI-T03"]["limitation"])
        self.assertIn("No customer", toks["QI-T04"]["limitation"])
        self.assertIn("No certification", toks["QI-T07"]["limitation"])
        self.assertIn("Low-profile does not mean hidden accountability",
                      toks["QI-T06"]["limitation"])


if __name__ == "__main__":
    unittest.main()
