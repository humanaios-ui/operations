"""Read-only Resource Broker -> actual Oracle consumer integration contract."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from resource_miner.broker_oracle_bridge import bridge
from resource_miner.internal_repository_broker import project

FIXTURE = Path(__file__).parent / "fixtures" / "broker_oracle_public_snapshot.json"


def snapshot():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class BrokerOracleBridgeTests(unittest.TestCase):
    def test_real_broker_to_oracle_consumer_matches_existing_ids(self):
        source = snapshot()
        broker = project(source)
        result = bridge(source)
        self.assertEqual(result["upstream_schema"], broker["schema"])
        self.assertEqual(result["graph_delta"]["schema_version"], "1.0")
        self.assertEqual(result["queue_delivery"], "NOT_ATTEMPTED")
        self.assertFalse(result["persisted"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["can_authorize"])
        original = broker["brokerage"][0]["candidates"][0]
        output = result["graph_delta"]["operations"][0]
        self.assertEqual(output["object_id"], original["resource_id"])
        self.assertEqual(output["payload"]["opportunity_id"], broker["resources"][0]["opportunity_id"])
        self.assertEqual(result["strategies"][0]["next_test"], "INDEPENDENT_GITHUB_SOURCE_READBACK")
        self.assertEqual(result["independent_verification"], "NOT_ESTABLISHED")

    def test_input_not_mutated_and_ids_stable_across_repeat(self):
        first = snapshot()
        original = copy.deepcopy(first)
        a, b = bridge(first), bridge(first)
        self.assertEqual(a, b)
        self.assertEqual(first, original)
        self.assertEqual(a["graph_delta"]["delta_id"], b["graph_delta"]["delta_id"])

    def test_no_capability_match_keeps_research_gap(self):
        row = snapshot()
        row["needs"][0]["capabilities"] = ["recovery_outcome"]
        output = bridge(row)
        self.assertEqual(output["strategies"][0]["state"], "RESEARCH_GAP")
        self.assertEqual(output["graph_delta"]["operations"][0]["payload"]["state"], "NO_MATCH_IN_BOUNDED_SNAPSHOT")

    def test_no_needs_does_not_emit_unsupported_delta(self):
        row = snapshot()
        row["needs"] = []
        output = bridge(row)
        self.assertEqual(output["status"], "NO_DECLARED_NEEDS")
        self.assertIsNone(output["graph_delta"])
        self.assertEqual(output["observations"], [])

    def test_mismatch_ci_is_not_verified_and_prioritized(self):
        row = snapshot()
        row["ci_observations"] = [{
            "item_ref": "humanaios-ui/operations/PR#1121",
            "head_sha": "b" * 40, "run_id": 17, "conclusion": "SUCCESS",
            "source_url": "https://github.com/humanaios-ui/operations/actions/runs/17",
        }]
        output = bridge(row)
        self.assertEqual(output["strategies"][0]["next_test"], "RECHECK_EXACT_HEAD_CI")
        self.assertTrue(output["graph_delta"]["operations"][0]["payload"]["ci_head_mismatch_reported"])
        self.assertEqual(output["independent_verification"], "NOT_ESTABLISHED")

    def test_rejects_private_data_and_forged_authority_upstream(self):
        for key, value in (("raw_body", "private"), ("private_email", "a@example.org"),
                           ("authority_effect", "Z2"), ("can_authorize", True)):
            with self.subTest(key=key):
                row = snapshot()
                row["items"][0][key] = value
                with self.assertRaises(ValueError):
                    bridge(row)

    def test_duplicate_resource_and_need_identity_rejected_by_real_broker(self):
        for kind in ("items", "needs"):
            with self.subTest(kind=kind):
                row = snapshot()
                row[kind].append(copy.deepcopy(row[kind][0]))
                with self.assertRaises(ValueError):
                    bridge(row)

    def test_pr_url_identity_and_suspicious_url_rejected(self):
        for url in ("https://github.com/humanaios-ui/operations/pull/9999",
                    "https://github.com/humanaios-ui/operations/pull/1121?token=x",
                    "https://mail.google.com/mail/u/0/#all/id"):
            with self.subTest(url=url):
                row = snapshot()
                row["items"][0]["source_url"] = url
                with self.assertRaises(ValueError):
                    bridge(row)

    def test_oracle_observation_and_graph_delta_schema_shape(self):
        row = bridge(snapshot())
        root = Path(__file__).resolve().parents[3]
        for name, objects in (("oracle_observation_v1.schema.json", row["observations"]),
                              ("oracle_graph_delta_v1.schema.json", [row["graph_delta"]])):
            schema = json.loads((root / "oracles" / "schemas" / name).read_text(encoding="utf-8"))
            for item in objects:
                self.assertTrue(set(schema["required"]) <= set(item))
                self.assertEqual(set(item) - set(schema["properties"]), set())
                for field, contract in schema["properties"].items():
                    if "const" in contract and field in item:
                        self.assertEqual(item[field], contract["const"])
        self.assertEqual(row["observations"][0]["source"]["substrate"], "github")

    def test_no_email_or_review_or_entitlement_claim_in_oracle_output(self):
        rendered = json.dumps(bridge(snapshot()), sort_keys=True)
        for word in ("@gmail.com", "mail.google.com", "ENTITLED", "REVIEWED", "GRANT_APPROVED"):
            self.assertNotIn(word, rendered)
        self.assertIn("NOT_ESTABLISHED", rendered)


if __name__ == "__main__":
    unittest.main()
