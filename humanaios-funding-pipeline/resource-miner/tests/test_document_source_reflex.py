from __future__ import annotations

import copy
import unittest

from resource_miner.document_source_reflex import project_report


OID_A = "a" * 40
OID_B = "b" * 40
OID_C = "c" * 40
FINGERPRINT_A = "1" * 64
FINGERPRINT_B = "2" * 64


def report():
    return {
        "source_identity": "source-fixture-1",
        "receipt_identity": "receipt-fixture-1",
        "observed_at": "2026-10-20T13:00:00Z",
        "sources": [
            {
                "repo": "humanaios-ui/operations",
                "path": "docs/source.md",
                "before_oid": OID_A,
                "after_oid": OID_B,
                "source_kind": "DOCUMENT",
            }
        ],
        "bindings": [
            {
                "repo": "humanaios-ui/operations",
                "path": "docs/source.md",
                "claim_id": "claim-a",
                "document_id": "dependent-a",
            },
            {
                "repo": "humanaios-ui/operations",
                "path": "docs/source.md",
                "claim_id": "claim-a",
                "document_id": "dependent-b",
            },
        ],
        "pull_requests": [],
    }


def pull_request(**changes):
    value = {
        "repo": "humanaios-ui/operations",
        "number": 924,
        "head_oid": OID_A,
        "merged": True,
        "ci_status": "PASS",
        "coderabbit_status": "APPROVED",
        "human_approval": "APPROVED",
        "admission_status": "FAIL",
        "receipt_head": OID_A,
    }
    value.update(changes)
    return value


def findings(output):
    return [row["finding_code"] for row in output["candidates"]]


class DocumentSourceReflexTests(unittest.TestCase):
    def test_changed_source_keeps_many_to_many_explicit_links(self):
        result = project_report(report())
        candidate = next(
            row
            for row in result["candidates"]
            if row["finding_code"] == "SOURCE_CHANGED_REVERIFY"
        )
        self.assertEqual(candidate["raw"]["claim_ids"], ["claim-a"])
        self.assertEqual(
            candidate["raw"]["dependent_document_ids"],
            ["dependent-a", "dependent-b"],
        )
        self.assertEqual(
            candidate["raw"]["bindings"],
            [
                {"claim_id": "claim-a", "document_id": "dependent-a"},
                {"claim_id": "claim-a", "document_id": "dependent-b"},
            ],
        )

    def test_many_to_many_edges_are_not_collapsed_to_a_cross_product(self):
        value = report()
        value["bindings"] = [
            {
                "repo": "humanaios-ui/operations",
                "path": "docs/source.md",
                "claim_id": "claim-a",
                "document_id": "dependent-a",
            },
            {
                "repo": "humanaios-ui/operations",
                "path": "docs/source.md",
                "claim_id": "claim-b",
                "document_id": "dependent-b",
            },
        ]
        result = project_report(value)
        candidate = next(
            row
            for row in result["candidates"]
            if row["finding_code"] == "SOURCE_CHANGED_REVERIFY"
        )
        self.assertEqual(
            candidate["raw"]["bindings"],
            [
                {"claim_id": "claim-a", "document_id": "dependent-a"},
                {"claim_id": "claim-b", "document_id": "dependent-b"},
            ],
        )

    def test_unmapped_change_is_not_reported_as_no_impact(self):
        value = report()
        value["bindings"] = []
        result = project_report(value)
        self.assertIn("SOURCE_CHANGE_UNMAPPED", findings(result))
        self.assertNotIn("NO_IMPACT", str(result))

    def test_unchanged_source_is_observed_but_impact_remains_unknown(self):
        value = report()
        value["sources"][0]["after_oid"] = OID_A
        result = project_report(value)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["source_observations"][0]["state"], "UNCHANGED_FROM_INPUT")
        self.assertEqual(result["source_observations"][0]["impact_state"], "UNKNOWN")

    def test_merged_with_exact_head_failed_admission_is_escalated_not_green(self):
        value = report()
        value["pull_requests"] = [pull_request(coderabbit_status="MISSING")]
        result = project_report(value)
        self.assertIn("MERGED_WITH_FAILED_ADMISSION", findings(result))
        self.assertEqual(result["overall"], "UNVERIFIED")
        self.assertFalse(result["merge_authority"])
        missing = next(
            row
            for row in result["candidates"]
            if row["finding_code"] == "MISSING_VERIFICATION"
        )
        self.assertNotIn(
            "verify an exact-head admission receipt",
            missing["raw"]["smallest_next_steps"],
        )

    def test_all_reported_checks_passing_never_verifies_the_report(self):
        value = report()
        value["sources"][0]["after_oid"] = OID_A
        value["pull_requests"] = [
            pull_request(
                merged=False,
                admission_status="PASS",
                ci_status="PASS",
                coderabbit_status="APPROVED",
                human_approval="APPROVED",
            )
        ]
        result = project_report(value)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["overall"], "UNVERIFIED")
        self.assertEqual(
            result["pull_request_observations"][0]["transport_provenance"],
            "UNVERIFIED_CALLER_SUPPLIED",
        )

    def test_passing_ci_without_human_approval_requests_verification(self):
        value = report()
        value["pull_requests"] = [
            pull_request(merged=False, admission_status="PASS", human_approval="MISSING")
        ]
        result = project_report(value)
        candidate = next(
            row
            for row in result["candidates"]
            if row["finding_code"] == "MISSING_VERIFICATION"
        )
        self.assertIn("obtain human approval", candidate["raw"]["smallest_next_steps"])

    def test_stale_receipt_does_not_claim_latest_failed_admission(self):
        value = report()
        value["pull_requests"] = [pull_request(receipt_head=OID_B)]
        result = project_report(value)
        self.assertIn("STALE_RECEIPT", findings(result))
        self.assertNotIn("MERGED_WITH_FAILED_ADMISSION", findings(result))

    def test_missing_receipt_is_missing_verification_not_stale(self):
        value = report()
        value["pull_requests"] = [pull_request(receipt_head=None)]
        result = project_report(value)
        self.assertIn("MISSING_VERIFICATION", findings(result))
        self.assertNotIn("STALE_RECEIPT", findings(result))

    def test_two_conflicting_fingerprints_are_explicitly_reported(self):
        value = report()
        value["bindings"][0]["claim_fingerprint"] = FINGERPRINT_A
        value["bindings"][1]["claim_fingerprint"] = FINGERPRINT_B
        result = project_report(value)
        self.assertIn("CONFLICTING_CLAIM_BINDINGS", findings(result))

    def test_identical_replay_has_identical_report_and_digest(self):
        value = report()
        self.assertEqual(project_report(value), project_report(copy.deepcopy(value)))

    def test_source_order_does_not_change_report(self):
        value = report()
        second = dict(value["sources"][0], path="docs/other.md", before_oid=OID_B, after_oid=OID_C)
        value["sources"].append(second)
        shuffled = copy.deepcopy(value)
        shuffled["sources"].reverse()
        self.assertEqual(project_report(value), project_report(shuffled))

    def test_path_traversal_and_absolute_paths_are_rejected(self):
        for path in ("../outside.md", "/absolute.md", "docs/../outside.md", "docs\\outside.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                value = report()
                value["sources"][0]["path"] = path
                project_report(value)

    def test_malformed_blob_hash_is_rejected(self):
        value = report()
        value["sources"][0]["after_oid"] = "not-an-oid"
        with self.assertRaises(ValueError):
            project_report(value)

    def test_unknown_repository_is_rejected(self):
        value = report()
        value["sources"][0]["repo"] = "attacker.invalid/repo"
        with self.assertRaises(ValueError):
            project_report(value)

    def test_duplicate_source_binding_is_rejected(self):
        value = report()
        value["bindings"].append(copy.deepcopy(value["bindings"][0]))
        with self.assertRaises(ValueError):
            project_report(value)

    def test_duplicate_source_and_pr_are_rejected(self):
        value = report()
        value["sources"].append(copy.deepcopy(value["sources"][0]))
        with self.assertRaises(ValueError):
            project_report(value)
        value = report()
        value["pull_requests"] = [pull_request(), pull_request()]
        with self.assertRaises(ValueError):
            project_report(value)

    def test_undeclared_binding_and_private_payload_are_rejected(self):
        value = report()
        value["bindings"][0]["repo"] = "humanaios-ui/humanaios"
        with self.assertRaises(ValueError):
            project_report(value)
        value = report()
        value["sources"][0]["document_payload"] = "must not be accepted"
        with self.assertRaises(ValueError):
            project_report(value)

    def test_collection_bounds_are_enforced(self):
        value = report()
        value["sources"] *= 51
        with self.assertRaises(ValueError):
            project_report(value)

    def test_outputs_label_transport_unverified_and_never_authorize(self):
        value = report()
        value["pull_requests"] = [pull_request()]
        result = project_report(value)
        self.assertEqual(result["transport_provenance"], "UNVERIFIED_CALLER_SUPPLIED")
        self.assertTrue(all(row["evidence_state"] == "UNVERIFIED" for row in result["candidates"]))
        self.assertTrue(all(row["authority_effect"] == "NONE" for row in result["candidates"]))
        serialized = str(result)
        self.assertNotIn("must not be accepted", serialized)

    def test_three_pr_baseline_surfaces_failed_admission_and_missing_receipts(self):
        value = report()
        value["sources"] = []
        value["bindings"] = []
        value["pull_requests"] = [
            pull_request(
                number=63,
                repo="humanaios-ui/lasting-light-ai",
                head_oid="3f7b1b6d322c9c93436afd38e1d658f1f2b20d2b",
                merged=True,
                ci_status="PASS",
                coderabbit_status="APPROVED",
                human_approval="APPROVED",
                admission_status="MISSING",
                receipt_head=None,
            ),
            pull_request(
                number=924,
                head_oid="3423817775ab46852414a2ac5889b720673ced3e",
                merged=True,
                ci_status="PASS",
                coderabbit_status="MISSING",
                human_approval="APPROVED",
                admission_status="FAIL",
                receipt_head="3423817775ab46852414a2ac5889b720673ced3e",
            ),
            pull_request(
                number=116,
                repo="humanaios-ui/humanaios",
                head_oid="d9c8c1be4d80d3150644afdecf81d1ba5fed2e14",
                merged=True,
                ci_status="PASS",
                coderabbit_status="APPROVED",
                human_approval="APPROVED",
                admission_status="MISSING",
                receipt_head=None,
            ),
        ]
        result = project_report(value)
        by_pr = {}
        for candidate in result["candidates"]:
            by_pr.setdefault(candidate["raw"]["pull_request"], []).append(
                candidate["finding_code"]
            )
        self.assertEqual(
            by_pr["humanaios-ui/lasting-light-ai#63"], ["MISSING_VERIFICATION"]
        )
        self.assertCountEqual(
            by_pr["humanaios-ui/operations#924"],
            ["MERGED_WITH_FAILED_ADMISSION", "MISSING_VERIFICATION"],
        )
        self.assertEqual(
            by_pr["humanaios-ui/humanaios#116"], ["MISSING_VERIFICATION"]
        )


if __name__ == "__main__":
    unittest.main()
