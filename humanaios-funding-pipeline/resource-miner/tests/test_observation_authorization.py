import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

from resource_miner.mines import load_mines, stable_opportunity_id
from resource_miner.observation_authorization import (
    OBSERVATION_OPERATION,
    PROHIBITED_OPERATIONS,
    authorization_covers_query,
    canonical_query_plan_sha256,
    evaluate_observation_authorization,
)
from resource_miner.registry_query import plan_registry_query

ROOT = Path(__file__).resolve().parents[1]


class ObservationAuthorizationGateTests(unittest.TestCase):
    def setUp(self):
        self.mines = load_mines(ROOT / "data" / "mines.seed.json")
        self.colorado = next(
            mine for mine in self.mines
            if mine.name == "Colorado Great Colorado Payback"
        )
        configured = self.colorado.config["opportunities"][0]
        self.pathway_id = stable_opportunity_id(
            self.colorado.mine_id,
            configured.get("opportunity_identity") or configured["url"],
            configured["opportunity_kind"],
        )

    def query(self):
        return plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=self.pathway_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name", "last_known_location"],
            explicit_subject_request=True,
        )

    def test_schema_binds_allow_to_observation_only_authority(self):
        schema = json.loads(
            (
                ROOT
                / "schemas"
                / "observation-authorization-decision.v1.schema.json"
            ).read_text()
        )
        self.assertEqual(
            schema["properties"]["private_query_values_exposed"]["const"],
            False,
        )
        self.assertEqual(
            schema["properties"]["external_state_change"]["const"],
            False,
        )
        self.assertEqual(
            schema["properties"]["consequence_ceiling"]["const"],
            "EVIDENCE_ONLY",
        )
        self.assertEqual(schema["properties"]["max_executions"]["const"], 1)
        self.assertEqual(schema["properties"]["one_shot"]["const"], True)

    def test_exact_colorado_query_can_be_authorized_for_observation_only(self):
        query = self.query()
        decision = evaluate_observation_authorization(
            query=query,
            mine=self.colorado,
        )
        self.assertEqual(decision.decision, "ALLOW_OBSERVATION")
        self.assertEqual(decision.requested_operation, OBSERVATION_OPERATION)
        self.assertEqual(decision.authority_effect, "OBSERVATION_ONLY")
        self.assertEqual(decision.execution_state, "NOT_EXECUTED")
        self.assertEqual(decision.consumption_state, "UNUSED")
        self.assertTrue(decision.one_shot)
        self.assertEqual(decision.max_executions, 1)
        self.assertEqual(decision.consequence_ceiling, "EVIDENCE_ONLY")
        self.assertFalse(decision.external_state_change)
        self.assertFalse(decision.private_query_values_exposed)
        self.assertEqual(
            decision.query_plan_sha256,
            canonical_query_plan_sha256(query),
        )
        self.assertTrue(authorization_covers_query(decision, query))

    def test_oag_contains_no_private_query_values(self):
        decision = evaluate_observation_authorization(
            query=self.query(),
            mine=self.colorado,
        )
        payload = decision.to_dict()
        forbidden = {
            "query_values",
            "raw_query_values",
            "owner_name_value",
            "business_name_value",
            "last_known_location_value",
            "date_of_birth",
            "ssn",
            "tax_id",
            "email",
            "phone",
            "claim_id",
        }
        self.assertTrue(forbidden.isdisjoint(payload))
        self.assertEqual(payload["query_value_persistence"], "PRIVATE_RUNTIME_ONLY")
        self.assertFalse(payload["private_query_values_exposed"])

    def test_authorization_is_bound_to_exact_query_digest(self):
        query = self.query()
        decision = evaluate_observation_authorization(
            query=query,
            mine=self.colorado,
        )
        mutated = replace(query, query_fields=["owner_name"])
        self.assertNotEqual(
            canonical_query_plan_sha256(query),
            canonical_query_plan_sha256(mutated),
        )
        self.assertFalse(authorization_covers_query(decision, mutated))

        mutated_decision = evaluate_observation_authorization(
            query=mutated,
            mine=self.colorado,
        )
        self.assertNotEqual(
            decision.authorization_id,
            mutated_decision.authorization_id,
        )

    def test_all_claim_submission_and_mutation_operations_are_denied(self):
        query = self.query()
        for operation in sorted(PROHIBITED_OPERATIONS):
            decision = evaluate_observation_authorization(
                query=query,
                mine=self.colorado,
                requested_operation=operation,
            )
            self.assertEqual(decision.decision, "DENY", operation)
            self.assertEqual(decision.authority_effect, "NONE", operation)
            self.assertEqual(decision.consumption_state, "NOT_APPLICABLE", operation)
            self.assertFalse(authorization_covers_query(decision, query), operation)

    def test_unknown_operation_is_denied_not_inferred(self):
        decision = evaluate_observation_authorization(
            query=self.query(),
            mine=self.colorado,
            requested_operation="DO_SOMETHING_HELPFUL",
        )
        self.assertEqual(decision.decision, "DENY")
        self.assertEqual(decision.authority_effect, "NONE")

    def test_disabled_mine_is_denied(self):
        mine = copy.deepcopy(self.colorado)
        mine.enabled = False
        decision = evaluate_observation_authorization(
            query=self.query(),
            mine=mine,
        )
        self.assertEqual(decision.decision, "DENY")
        self.assertIn("target Mine is disabled", decision.decision_reasons)

    def test_wrong_mine_binding_is_denied(self):
        microsoft = next(
            mine for mine in self.mines
            if mine.name == "Microsoft for Startups"
        )
        decision = evaluate_observation_authorization(
            query=self.query(),
            mine=microsoft,
        )
        self.assertEqual(decision.decision, "DENY")
        self.assertEqual(decision.authority_effect, "NONE")
        self.assertIn(
            "RQY Mine binding does not match evaluated Mine",
            decision.decision_reasons,
        )

    def test_mutated_rqy_authority_or_state_change_is_denied(self):
        query = self.query()
        mutations = [
            replace(query, external_state_change=True),
            replace(query, query_value_persistence="PUBLIC"),
            replace(query, execution_state="EXECUTED"),
            replace(query, authority_effect="OBSERVATION_ONLY"),
        ]
        for mutated in mutations:
            decision = evaluate_observation_authorization(
                query=mutated,
                mine=self.colorado,
            )
            self.assertEqual(decision.decision, "DENY")
            self.assertEqual(decision.authority_effect, "NONE")

    def test_decision_receipt_is_deterministic(self):
        query = self.query()
        first = evaluate_observation_authorization(
            query=query,
            mine=self.colorado,
        )
        second = evaluate_observation_authorization(
            query=query,
            mine=self.colorado,
        )
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(
            len(first.policy_receipt_sha256),
            64,
        )

    def test_prohibited_actions_include_claim_and_document_surfaces(self):
        decision = evaluate_observation_authorization(
            query=self.query(),
            mine=self.colorado,
        )
        for required in [
            "CREATE_CLAIM",
            "SUBMIT_CLAIM",
            "UPDATE_CLAIM",
            "UPLOAD_DOCUMENT",
            "LOOKUP_PRIVATE_CLAIM_STATUS",
        ]:
            self.assertIn(required, decision.prohibited_actions)


if __name__ == "__main__":
    unittest.main()
