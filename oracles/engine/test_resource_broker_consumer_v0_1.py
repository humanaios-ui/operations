"""Standalone tests for the Oracle half; no Resource Miner or network needed."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from resource_broker_consumer_v0_1 import consume

R = "humanaios-ui/operations"
PR_URL = f"https://github.com/{R}/pull/1121"
ISSUE_URL = f"https://github.com/{R}/issues/1123"


def bundle():
    return {
        "schema": "humanaios.internal-resource-intelligence.v0.1",
        "as_of": "2026-11-03T20:43:59Z", "authority_effect": "NONE",
        "source_authentication": "NOT_ESTABLISHED",
        "board_role": "NON_AUTHORITATIVE_DERIVED_PROJECTION",
        "coverage": "BOUNDED_CALLER_SNAPSHOT",
        "resources": [{
            "resource_id": "RES-INT-A000111", "opportunity_id": "OPP-TEST-1121",
            "item_ref": R + "/PR#1121", "source_url": PR_URL,
            "canonical_url": PR_URL, "source_authentication": "NOT_ESTABLISHED",
            "evidence_provenance": "UNAUTHENTICATED_SOURCE_SNAPSHOT",
            "eligibility_status": "UNASSESSED", "authority_effect": "NONE",
            "head_sha": "a" * 40, "resource_affordances": ["source_verification"],
            "ci_observations": [],
        }],
        "brokerage": [{
            "need_id": "NEED-ORACLE-1123", "priority": "P1", "authority_effect": "NONE",
            "roi": "NOT_MEASURED", "state": "CANDIDATES_REQUIRE_HUMAN_REVIEW",
            "attractor": {"classes": ["DECLARED_CAPABILITY_DEPENDENCY"],
                          "source_ref": ISSUE_URL,
                          "expected_capabilities": ["source_verification"]},
            "candidates": [{"resource_id": "RES-INT-A000111", "item_ref": R + "/PR#1121",
                            "capability_codes": ["source_verification"],
                            "readiness": "REQUIRES_INDEPENDENT_VALIDATION",
                            "may_execute": False}],
        }],
        "agent_sessions": [], "quarantine": [],
        "oracle": {"claims_status": "INFERRED", "can_authorize": False, "can_execute": False},
        "mission_outcomes": {"resource_acquisition": "NOT_ESTABLISHED", "revenue": "NOT_ESTABLISHED",
                             "recovery_benefit": "NOT_ESTABLISHED"},
    }


class OracleConsumerTests(unittest.TestCase):
    def test_produces_conservative_oracle_batch(self):
        output = consume(bundle())
        self.assertEqual(output["queue_delivery"], "NOT_ATTEMPTED")
        self.assertFalse(output["persisted"])
        self.assertEqual(output["graph_delta"]["operations"][0]["object_id"], "RES-INT-A000111")
        self.assertEqual(output["graph_delta"]["operations"][0]["payload"]["opportunity_id"], "OPP-TEST-1121")
        self.assertEqual(output["observations"][0]["source"]["locator"], PR_URL)
        self.assertEqual(output["observations"][0]["relation"], None)
        self.assertFalse(output["can_authorize"])

    def test_deterministic_input_immutable(self):
        a = bundle()
        old = copy.deepcopy(a)
        self.assertEqual(consume(a), consume(a))
        self.assertEqual(a, old)

    def test_same_observation_identity_with_later_record_time(self):
        b = bundle()
        a = consume(b)
        later = consume(b, recorded_at="2026-11-03T21:00:00Z")
        self.assertEqual(a["observations"][0]["observation_id"], later["observations"][0]["observation_id"])
        self.assertEqual(a["graph_delta"]["delta_id"], later["graph_delta"]["delta_id"])

    def test_no_matches_preserve_gap(self):
        b = bundle()
        b["brokerage"][0]["candidates"] = []
        b["brokerage"][0]["state"] = "NO_MATCH_IN_BOUNDED_SNAPSHOT"
        self.assertEqual(consume(b)["strategies"][0]["next_test"], "VERIFY_MORE_INTERNAL_SOURCES")

    def test_reject_wrong_source_url_and_id(self):
        b = bundle(); b["resources"][0]["source_url"] = PR_URL + "?token=a"
        with self.assertRaises(ValueError): consume(b)

    def test_reject_claimed_review_and_account(self):
        for key in ("review_status", "account_entitlement", "raw_body", "private_email"):
            b = bundle(); b["resources"][0][key] = "REVIEWED"
            with self.subTest(key=key), self.assertRaises(ValueError): consume(b)

    def test_reject_claimed_verification(self):
        for field, value in (("source_authentication", "VERIFIED"), ("eligibility_status", "ELIGIBLE"),
                             ("evidence_provenance", "PROVIDER_VERIFIED"), ("authority_effect", "Z2")):
            b = bundle(); b["resources"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): consume(b)

    def test_reject_false_match_and_nonexistent_resource(self):
        for field, value in (("capability_codes", ["human_decision"]), ("resource_id", "RES-MISSING"),
                             ("may_execute", True)):
            b = bundle(); b["brokerage"][0]["candidates"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): consume(b)

    def test_reject_duplicate_needs_and_resources(self):
        for field in ("resources", "brokerage"):
            b = bundle(); b[field].append(copy.deepcopy(b[field][0]))
            with self.subTest(field=field), self.assertRaises(ValueError): consume(b)

    def test_reject_ci_self_authentication(self):
        b = bundle(); b["resources"][0]["ci_observations"] = [{
            "independently_authenticated": True, "head_alignment": "HEAD_MATCH"}]
        with self.assertRaises(ValueError): consume(b)

    def test_ci_head_mismatch_treated_as_recheck(self):
        b = bundle(); b["resources"][0]["ci_observations"] = [{
            "independently_authenticated": False, "head_alignment": "HEAD_MISMATCH"}]
        self.assertEqual(consume(b)["strategies"][0]["next_test"], "RECHECK_EXACT_HEAD_CI")

    def test_reject_broker_benefit_claim(self):
        b = bundle(); b["mission_outcomes"]["revenue"] = "PAID"
        with self.assertRaises(ValueError): consume(b)

    def test_reject_time_travel(self):
        with self.assertRaises(ValueError): consume(bundle(), recorded_at="2026-10-01T01:00:00Z")

    def test_reject_top_level_private_leak(self):
        b = bundle(); b["raw_body"] = "mail private"
        with self.assertRaises(ValueError): consume(b)


if __name__ == "__main__": unittest.main()
