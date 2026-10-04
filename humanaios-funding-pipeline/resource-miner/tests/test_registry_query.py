import json
import unittest
from pathlib import Path

from resource_miner.mines import load_mines, stable_opportunity_id
from resource_miner.registry_query import (
    plan_registry_query,
    registry_query_from_dict,
    stable_registry_query_id,
)

ROOT = Path(__file__).resolve().parents[1]


class RegistryQueryPlanTests(unittest.TestCase):
    def setUp(self):
        self.mines = load_mines(ROOT / "data" / "mines.seed.json")
        self.colorado = next(
            mine for mine in self.mines
            if mine.name == "Colorado Great Colorado Payback"
        )
        configured = self.colorado.config["opportunities"][0]
        self.pathway_opportunity_id = stable_opportunity_id(
            self.colorado.mine_id,
            configured.get("opportunity_identity") or configured["url"],
            configured["opportunity_kind"],
        )

    def test_schema_is_planning_only_and_privacy_bounded(self):
        schema = json.loads(
            (ROOT / "schemas" / "registry-query-plan.v1.schema.json").read_text()
        )
        self.assertEqual(schema["properties"]["execution_state"]["const"], "NOT_AUTHORIZED")
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")
        self.assertEqual(schema["properties"]["external_state_change"]["const"], False)
        self.assertEqual(
            schema["properties"]["query_value_persistence"]["const"],
            "PRIVATE_RUNTIME_ONLY",
        )
        self.assertFalse(schema["additionalProperties"])

    def test_colorado_query_plan_contains_no_query_values(self):
        plan = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_opportunity_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name", "last_known_location"],
            explicit_subject_request=True,
        )
        data = plan.to_dict()
        self.assertTrue(plan.query_id.startswith("RQY-"))
        self.assertEqual(plan.execution_state, "NOT_AUTHORIZED")
        self.assertEqual(plan.authority_effect, "NONE")
        self.assertEqual(plan.query_value_persistence, "PRIVATE_RUNTIME_ONLY")
        self.assertEqual(
            plan.expected_response_class,
            "ZERO_OR_MORE_CANDIDATE_RECORDS",
        )
        self.assertEqual(
            plan.zero_result_semantics,
            "NO_MATCH_OBSERVED_NOT_NO_ENTITLEMENT",
        )
        self.assertEqual(
            plan.match_result_semantics,
            "CANDIDATE_RECORD_NOT_OWNERSHIP",
        )
        self.assertNotIn("query_values", data)
        self.assertNotIn("name", data)
        self.assertNotIn("dob", data)
        self.assertNotIn("ssn", data)
        self.assertNotIn("email", data)

    def test_public_rqy_deserializer_rejects_private_query_values(self):
        plan = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_opportunity_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name"],
            explicit_subject_request=True,
        )
        payload = plan.to_dict()
        payload["query_values"] = {"owner_name": "private runtime value"}
        with self.assertRaises(ValueError):
            registry_query_from_dict(payload)

    def test_business_subject_can_use_business_name_only(self):
        plan = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_opportunity_id,
            subject_ref="SUBJ-BBBBBBBBBBBBBBBB",
            subject_kind="ORGANIZATION",
            query_fields=["business_name"],
            explicit_subject_request=True,
        )
        self.assertEqual(plan.subject_kind, "ORGANIZATION")
        self.assertEqual(plan.query_fields, ["business_name"])

    def test_missing_explicit_subject_request_fails_closed(self):
        with self.assertRaises(PermissionError):
            plan_registry_query(
                mine=self.colorado,
                pathway_opportunity_id=self.pathway_opportunity_id,
                subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
                subject_kind="NATURAL_PERSON",
                query_fields=["owner_name"],
                explicit_subject_request=False,
            )

    def test_raw_identity_is_not_accepted_as_subject_ref(self):
        for bad in [
            "Jane Doe",
            "jane@example.com",
            "123-45-6789",
            "SUBJ-jane-doe",
        ]:
            with self.assertRaises(ValueError):
                plan_registry_query(
                    mine=self.colorado,
                    pathway_opportunity_id=self.pathway_opportunity_id,
                    subject_ref=bad,
                    subject_kind="NATURAL_PERSON",
                    query_fields=["owner_name"],
                    explicit_subject_request=True,
                )

    def test_query_fields_must_be_declared_by_mine(self):
        with self.assertRaises(ValueError):
            plan_registry_query(
                mine=self.colorado,
                pathway_opportunity_id=self.pathway_opportunity_id,
                subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
                subject_kind="NATURAL_PERSON",
                query_fields=["date_of_birth"],
                explicit_subject_request=True,
            )

    def test_non_registry_mine_cannot_emit_registry_query(self):
        microsoft = next(
            mine for mine in self.mines
            if mine.name == "Microsoft for Startups"
        )
        with self.assertRaises(ValueError):
            plan_registry_query(
                mine=microsoft,
                pathway_opportunity_id="OPP-1111111111111111",
                subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
                subject_kind="NATURAL_PERSON",
                query_fields=["owner_name"],
                explicit_subject_request=True,
            )

    def test_foreign_pathway_opportunity_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_registry_query(
                mine=self.colorado,
                pathway_opportunity_id="OPP-1111111111111111",
                subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
                subject_kind="NATURAL_PERSON",
                query_fields=["owner_name"],
                explicit_subject_request=True,
            )

    def test_query_identity_is_order_independent(self):
        a = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_opportunity_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name", "last_known_location"],
            explicit_subject_request=True,
        )
        b = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_opportunity_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["last_known_location", "owner_name"],
            explicit_subject_request=True,
        )
        self.assertEqual(a.query_id, b.query_id)
        self.assertEqual(a.to_dict(), b.to_dict())

    def test_query_identity_changes_with_subject(self):
        common = dict(
            registry_mine_id=self.colorado.mine_id,
            pathway_opportunity_id=self.pathway_opportunity_id,
            query_class="UNCLAIMED_PROPERTY_OWNER_SEARCH",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name"],
            purpose="DISCOVER_CANDIDATE_UNCLAIMED_PROPERTY_RECORDS",
        )
        a = stable_registry_query_id(
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            **common,
        )
        b = stable_registry_query_id(
            subject_ref="SUBJ-BBBBBBBBBBBBBBBB",
            **common,
        )
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
