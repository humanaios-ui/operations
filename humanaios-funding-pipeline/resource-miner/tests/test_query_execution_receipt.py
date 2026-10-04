import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from resource_miner.mines import load_mines, stable_opportunity_id
from resource_miner.observation_authorization import (
    evaluate_observation_authorization,
)
from resource_miner.query_execution_receipt import (
    append_query_execution_receipt,
    load_query_execution_receipts,
    mint_query_execution_receipt,
    query_execution_receipt_from_dict,
)
from resource_miner.registry_query import plan_registry_query

ROOT = Path(__file__).resolve().parents[1]


class QueryExecutionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.mines = load_mines(ROOT / "data" / "mines.seed.json")
        self.colorado = next(
            mine for mine in self.mines
            if mine.name == "Colorado Great Colorado Payback"
        )
        configured = self.colorado.config["opportunities"][0]
        pathway_id = stable_opportunity_id(
            self.colorado.mine_id,
            configured.get("opportunity_identity") or configured["url"],
            configured["opportunity_kind"],
        )
        self.query = plan_registry_query(
            mine=self.colorado,
            pathway_opportunity_id=pathway_id,
            subject_ref="SUBJ-AAAAAAAAAAAAAAAA",
            subject_kind="NATURAL_PERSON",
            query_fields=["owner_name", "last_known_location"],
            explicit_subject_request=True,
        )
        self.authorization = evaluate_observation_authorization(
            query=self.query,
            mine=self.colorado,
        )

    def receipt(self, **overrides):
        args = {
            "authorization": self.authorization,
            "query": self.query,
            "private_subject_binding_attestation_id": "PSB-BBBBBBBBBBBBBBBB",
            "executed_query_fields": ["owner_name", "last_known_location"],
            "observed_origin_key": "unclaimedproperty.colorado.gov",
            "execution_nonce": "EXE-CCCCCCCCCCCCCCCC",
            "started_at": "2026-10-04T09:00:00Z",
            "finished_at": "2026-10-04T09:00:01Z",
            "result_state": "ZERO_MATCHES_OBSERVED",
            "observed_record_count": 0,
            "prior_receipts": [],
        }
        args.update(overrides)
        return mint_query_execution_receipt(**args)

    def test_schema_preserves_privacy_and_non_authority_boundary(self):
        schema = json.loads(
            (ROOT / "schemas" / "query-execution-receipt.v1.schema.json").read_text()
        )
        self.assertEqual(schema["properties"]["private_query_values_exposed"]["const"], False)
        self.assertEqual(schema["properties"]["raw_request_exposed"]["const"], False)
        self.assertEqual(schema["properties"]["raw_response_exposed"]["const"], False)
        self.assertEqual(schema["properties"]["external_state_change"]["const"], False)
        self.assertEqual(schema["properties"]["claim_submission_permitted"]["const"], False)
        self.assertEqual(schema["properties"]["prohibited_action_executed"]["const"], False)
        self.assertEqual(schema["properties"]["authorization_consumed"]["const"], True)
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")

    def test_zero_match_receipt_consumes_exact_oag_once(self):
        receipt = self.receipt()
        self.assertTrue(receipt.receipt_id.startswith("QRC-"))
        self.assertEqual(receipt.authorization_id, self.authorization.authorization_id)
        self.assertEqual(receipt.query_id, self.query.query_id)
        self.assertTrue(receipt.private_subject_binding_attested)
        self.assertEqual(receipt.result_state, "ZERO_MATCHES_OBSERVED")
        self.assertEqual(receipt.observed_record_count, 0)
        self.assertTrue(receipt.authorization_consumed)
        self.assertEqual(receipt.authorization_consumption_ordinal, 1)
        self.assertEqual(receipt.evidence_effect, "OBSERVATION_RECEIPT_ONLY")
        self.assertEqual(receipt.authority_effect, "NONE")

    def test_match_receipt_requires_positive_count(self):
        receipt = self.receipt(
            execution_nonce="EXE-DDDDDDDDDDDDDDDD",
            result_state="MATCHES_OBSERVED",
            observed_record_count=3,
        )
        self.assertEqual(receipt.result_state, "MATCHES_OBSERVED")
        self.assertEqual(receipt.observed_record_count, 3)

        with self.assertRaises(ValueError):
            self.receipt(
                execution_nonce="EXE-EEEEEEEEEEEEEEEE",
                result_state="MATCHES_OBSERVED",
                observed_record_count=0,
            )

    def test_failed_observation_requires_null_count(self):
        receipt = self.receipt(
            execution_nonce="EXE-FFFFFFFFFFFFFFFF",
            result_state="OBSERVATION_FAILED",
            observed_record_count=None,
        )
        self.assertIsNone(receipt.observed_record_count)

        with self.assertRaises(ValueError):
            self.receipt(
                execution_nonce="EXE-1111111111111111",
                result_state="OBSERVATION_FAILED",
                observed_record_count=0,
            )

    def test_zero_match_semantics_do_not_become_no_entitlement(self):
        receipt = self.receipt()
        self.assertEqual(
            receipt.zero_result_semantics,
            "NO_MATCH_OBSERVED_NOT_NO_ENTITLEMENT",
        )
        self.assertEqual(
            receipt.match_result_semantics,
            "CANDIDATE_RECORD_NOT_OWNERSHIP",
        )

    def test_duplicate_authorization_consumption_is_rejected(self):
        first = self.receipt()
        with self.assertRaises(PermissionError):
            self.receipt(
                execution_nonce="EXE-2222222222222222",
                prior_receipts=[first],
            )

    def test_exact_authorized_fields_are_required(self):
        with self.assertRaises(PermissionError):
            self.receipt(executed_query_fields=["owner_name"])
        with self.assertRaises(PermissionError):
            self.receipt(
                executed_query_fields=[
                    "owner_name",
                    "last_known_location",
                    "business_name",
                ]
            )

    def test_observed_origin_must_be_authorized(self):
        with self.assertRaises(PermissionError):
            self.receipt(observed_origin_key="example.com")

    def test_private_binding_and_execution_nonce_are_opaque_tokens(self):
        with self.assertRaises(ValueError):
            self.receipt(private_subject_binding_attestation_id="Jane Doe")
        with self.assertRaises(ValueError):
            self.receipt(execution_nonce="my-run")

    def test_denied_or_detached_oag_cannot_mint_receipt(self):
        denied = evaluate_observation_authorization(
            query=self.query,
            mine=self.colorado,
            requested_operation="SUBMIT_CLAIM",
        )
        with self.assertRaises(PermissionError):
            self.receipt(authorization=denied)

        other_query = replace(
            self.query,
            query_fields=["owner_name"],
        )
        with self.assertRaises(PermissionError):
            self.receipt(query=other_query)

    def test_forged_oag_policy_receipt_is_rejected(self):
        forged = replace(
            self.authorization,
            policy_receipt_sha256="0" * 64,
        )
        with self.assertRaises(PermissionError):
            self.receipt(authorization=forged)

    def test_public_receipt_contains_no_private_query_values(self):
        payload = self.receipt().to_dict()
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
            "address",
            "claim_id",
            "cookie",
            "session_token",
        }
        self.assertTrue(forbidden.isdisjoint(payload))
        self.assertFalse(payload["private_query_values_exposed"])
        self.assertFalse(payload["raw_request_exposed"])
        self.assertFalse(payload["raw_response_exposed"])

    def test_receipt_hash_detects_tampering(self):
        payload = self.receipt().to_dict()
        parsed = query_execution_receipt_from_dict(payload)
        self.assertEqual(parsed.to_dict(), payload)

        tampered = dict(payload)
        tampered["observed_record_count"] = 1
        with self.assertRaises(ValueError):
            query_execution_receipt_from_dict(tampered)

    def test_append_only_ledger_rejects_second_consumption(self):
        receipt = self.receipt()
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "qrc.jsonl"
            append_query_execution_receipt(ledger, receipt)
            rows = load_query_execution_receipts(ledger)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].receipt_id, receipt.receipt_id)

            duplicate = self.receipt(execution_nonce="EXE-3333333333333333")
            with self.assertRaises(PermissionError):
                append_query_execution_receipt(ledger, duplicate)

    def test_finished_time_cannot_precede_start(self):
        with self.assertRaises(ValueError):
            self.receipt(
                started_at="2026-10-04T09:00:02Z",
                finished_at="2026-10-04T09:00:01Z",
            )


if __name__ == "__main__":
    unittest.main()
