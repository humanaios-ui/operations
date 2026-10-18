import json
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path

from resource_miner.mines import load_mines, resolve_mines
from resource_miner.needs import map_to_requirements
from resource_miner.normalize import normalize_generic
from resource_miner.privacy_footprint import (
    AuditDenied,
    PrivacyAuditGrant,
    PrivacyAuditQuery,
    PrivacySource,
    build_privacy_requirements,
    review_privacy_finding,
    run_privacy_footprint_audit,
)


ROOT = Path(__file__).resolve().parents[1]


def load_fixture():
    return json.loads(
        (ROOT / "fixtures" / "privacy_footprint_synthetic.json").read_text(
            encoding="utf-8"
        )
    )


def fixture_objects():
    payload = load_fixture()
    grant = PrivacyAuditGrant(
        **{
            **payload["grant"],
            "allowed_source_ids": tuple(payload["grant"]["allowed_source_ids"]),
            "allowed_operations": tuple(payload["grant"]["allowed_operations"]),
        }
    )
    query = PrivacyAuditQuery(
        **{
            **payload["query"],
            "source_ids": tuple(payload["query"]["source_ids"]),
            "operations": tuple(payload["query"]["operations"]),
        }
    )
    sources = tuple(PrivacySource(**row) for row in payload["sources"])
    key = bytes.fromhex(payload["pseudonymization_key_hex"])
    return grant, query, sources, key


class PrivacyFootprintMineTests(unittest.TestCase):
    def test_synthetic_audit_is_private_read_only_and_resource_mapped(self):
        grant, query, sources, key = fixture_objects()
        result = run_privacy_footprint_audit(
            grant,
            query,
            sources,
            pseudonymization_key=key,
        )

        self.assertEqual(result.state, "FINDINGS_FOR_HUMAN_REVIEW")
        self.assertEqual(
            {finding.finding_type for finding in result.findings},
            {
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "IP_ADDRESS",
                "CROSS_SOURCE_LINKAGE",
            },
        )
        linkage = next(
            finding
            for finding in result.findings
            if finding.finding_type == "CROSS_SOURCE_LINKAGE"
        )
        self.assertEqual(linkage.state, "LINKAGE_CANDIDATE")
        self.assertEqual(linkage.basis_type, "EMAIL_ADDRESS")
        self.assertEqual(linkage.source_count, 2)
        self.assertIn("not established", linkage.claim_text.lower())
        self.assertIsNone(linkage.confidence)
        self.assertEqual(linkage.confidence_state, "NOT_CALIBRATED")
        self.assertTrue(
            all(finding.confidence is None for finding in result.findings)
        )

        serialized = json.dumps(result.to_dict(), sort_keys=True)
        self.assertIsInstance(result.to_dict()["findings"][0]["evidence"], list)
        self.assertIsInstance(result.to_dict()["receipt"]["limits"], list)
        self.assertNotIn("alice@example.test", serialized.lower())
        self.assertNotIn("850) 555-0100", serialized)
        self.assertNotIn("192.0.2.10", serialized)
        self.assertNotIn("content", result.findings[0].evidence[0].__dict__)
        self.assertNotIn("alice@example.test", repr(sources[0]).lower())

        self.assertTrue(result.receipt.receipt_id.startswith("QRC-"))
        self.assertFalse(result.receipt.raw_content_retained)
        self.assertFalse(result.receipt.raw_values_emitted)
        self.assertEqual(result.receipt.network_access, "NONE")
        self.assertEqual(result.receipt.authority_effect, "NONE")
        self.assertEqual(result.receipt.execution, "DISABLED")
        self.assertEqual(
            result.receipt.receipt_kind,
            "UNSIGNED_LOCAL_COMMITMENT_NOT_AN_ATTESTATION",
        )
        self.assertEqual(
            result.receipt.authorization_ref_state,
            "CALLER_SUPPLIED_NOT_CRYPTOGRAPHICALLY_VERIFIED",
        )
        self.assertEqual(result.authority_effect, "NONE")
        self.assertEqual(result.execution, "DISABLED")
        self.assertTrue(
            all(row["gap_status"] == "CONDITIONAL" for row in result.resource_requirements)
        )
        self.assertTrue(
            all(row["authority_effect"] == "NONE" for row in result.resource_requirements)
        )

    def test_same_key_is_repeatable_and_different_key_breaks_linkability(self):
        grant, query, sources, key = fixture_objects()
        first = run_privacy_footprint_audit(
            grant, query, sources, pseudonymization_key=key
        )
        second = run_privacy_footprint_audit(
            grant, query, sources, pseudonymization_key=key
        )
        isolated = run_privacy_footprint_audit(
            grant, query, sources, pseudonymization_key=b"z" * 32
        )
        self.assertEqual(first.receipt.output_sha256, second.receipt.output_sha256)
        self.assertEqual(first.receipt.receipt_id, second.receipt.receipt_id)
        self.assertNotEqual(
            {row.value_commitment for row in first.findings},
            {row.value_commitment for row in isolated.findings},
        )

    def test_registered_mine_is_evidence_only_and_cannot_auto_resolve(self):
        mines = load_mines(ROOT / "data" / "mines.seed.json")
        mine = next(
            row
            for row in mines
            if row.resolver == "privacy_footprint_local"
        )
        self.assertEqual(mine.mine_kind, "USER_CONTROLLED_DATASET")
        self.assertEqual(mine.cadence, "on_demand")
        self.assertIn("EVIDENCE_SOURCE", mine.roles)
        self.assertNotIn("OPPORTUNITY_SOURCE", mine.roles)
        self.assertEqual(mine.config["network_access"], "NONE")
        self.assertEqual(mine.config["execution"], "DISABLED")

        opportunities, receipts = resolve_mines(
            [mine], observed_at="2026-10-18T22:30:00Z"
        )
        self.assertEqual(opportunities, [])
        self.assertEqual(receipts[0].state, "ROLE_ONLY")

    def test_grant_source_scope_and_time_fail_closed(self):
        grant, query, sources, key = fixture_objects()
        outside = replace(query, source_ids=("SRC-FFFFFFFFFFFFFFFF",))
        with self.assertRaises(AuditDenied):
            run_privacy_footprint_audit(
                grant, outside, sources[:1], pseudonymization_key=key
            )

        expired = replace(query, requested_at="2026-10-18T18:00:01-05:00")
        with self.assertRaises(AuditDenied):
            run_privacy_footprint_audit(
                grant, expired, sources, pseudonymization_key=key
            )

        revoked_grant = replace(
            grant, revoked_at="2026-10-18T17:29:59-05:00"
        )
        with self.assertRaises(AuditDenied):
            run_privacy_footprint_audit(
                revoked_grant, query, sources, pseudonymization_key=key
            )

        substituted_query = replace(query, query_id="RQY-FFFFFFFFFFFFFFFF")
        with self.assertRaises(AuditDenied):
            run_privacy_footprint_audit(
                grant, substituted_query, sources, pseudonymization_key=key
            )

    def test_explicit_scan_alone_does_not_join_sources(self):
        grant, query, sources, key = fixture_objects()
        scan_grant = replace(
            grant,
            allowed_operations=("EXPLICIT_PII_SCAN",),
        )
        scan_query = replace(
            query,
            operations=("EXPLICIT_PII_SCAN",),
        )
        result = run_privacy_footprint_audit(
            scan_grant,
            scan_query,
            sources,
            pseudonymization_key=key,
        )
        self.assertNotIn(
            "CROSS_SOURCE_LINKAGE",
            {finding.finding_type for finding in result.findings},
        )
        emails = [
            finding
            for finding in result.findings
            if finding.finding_type == "EMAIL_ADDRESS"
        ]
        self.assertEqual(len(emails), 2)
        self.assertTrue(all(finding.source_count == 1 for finding in emails))
        self.assertNotEqual(emails[0].value_commitment, emails[1].value_commitment)

    def test_unsupported_attribute_inference_is_denied(self):
        grant, query, sources, key = fixture_objects()
        inference_grant = replace(
            grant,
            allowed_operations=("EXPLICIT_PII_SCAN", "ATTRIBUTE_INFERENCE"),
        )
        inference_query = replace(
            query,
            operations=("EXPLICIT_PII_SCAN", "ATTRIBUTE_INFERENCE"),
        )
        with self.assertRaises(AuditDenied):
            run_privacy_footprint_audit(
                inference_grant,
                inference_query,
                sources,
                pseudonymization_key=key,
            )

    def test_human_confirmation_and_repair_intent_remain_separate(self):
        grant, query, sources, key = fixture_objects()
        result = run_privacy_footprint_audit(
            grant, query, sources, pseudonymization_key=key
        )
        email = next(
            finding
            for finding in result.findings
            if finding.finding_type == "EMAIL_ADDRESS"
        )

        confirmed = review_privacy_finding(email, validation="CONFIRMED")
        conditional = build_privacy_requirements([confirmed])
        self.assertEqual(conditional[0]["gap_status"], "CONDITIONAL")

        seek_repair = review_privacy_finding(
            email,
            validation="CONFIRMED",
            disposition="SEEK_REPAIR",
        )
        confirmed_gap = build_privacy_requirements([seek_repair])
        self.assertEqual(confirmed_gap[0]["gap_status"], "CONFIRMED")
        self.assertEqual(confirmed_gap[0]["authority_effect"], "NONE")

        accepted = review_privacy_finding(
            email,
            validation="CONFIRMED",
            disposition="ACCEPT_RISK",
        )
        inactive = build_privacy_requirements([accepted])
        self.assertEqual(inactive[0]["gap_status"], "INACTIVE")

        denied = review_privacy_finding(email, validation="DENIED")
        self.assertEqual(build_privacy_requirements([denied]), [])

    def test_confirmed_privacy_requirement_matches_privacy_tool_candidate(self):
        grant, query, sources, key = fixture_objects()
        result = run_privacy_footprint_audit(
            grant, query, sources, pseudonymization_key=key
        )
        email = next(
            finding
            for finding in result.findings
            if finding.finding_type == "EMAIL_ADDRESS"
        )
        requirement = build_privacy_requirements(
            [
                review_privacy_finding(
                    email,
                    validation="CONFIRMED",
                    disposition="SEEK_REPAIR",
                )
            ]
        )
        candidate = normalize_generic(
            title="Synthetic local privacy redaction tool",
            url="https://example.test/privacy-tool",
            source_name="Synthetic",
            discovery_method="test",
            source_category="privacy_tool",
            body_text="Email redaction and compartmentalization.",
            observed_at="2026-10-18T22:30:00Z",
        )
        matches = map_to_requirements(candidate, requirement)
        self.assertEqual(candidate.resource_types, ["privacy_tool"])
        self.assertEqual(matches[0].requirement_id, "RR-PRIVACY-EMAIL-CONTROL-001")
        self.assertEqual(matches[0].gap_status, "CONFIRMED")

    def test_zero_matches_abstains(self):
        grant, query, sources, key = fixture_objects()
        clean_sources = tuple(
            replace(source, content="Synthetic text with no supported pattern.")
            for source in sources
        )
        result = run_privacy_footprint_audit(
            grant, query, clean_sources, pseudonymization_key=key
        )
        self.assertEqual(result.state, "ZERO_MATCHES_OBSERVED")
        self.assertEqual(result.findings, ())
        self.assertEqual(result.resource_requirements, ())
        self.assertTrue(
            any("does not establish" in limit for limit in result.receipt.limits)
        )

    def test_schema_declares_same_fail_closed_boundary(self):
        schema = json.loads(
            (
                ROOT
                / "schemas"
                / "privacy-footprint-audit.v0.1.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["authority_effect"]["const"], "NONE"
        )
        self.assertEqual(schema["properties"]["execution"]["const"], "DISABLED")
        receipt = schema["$defs"]["receipt"]["properties"]
        self.assertFalse(receipt["raw_content_retained"]["const"])
        self.assertFalse(receipt["raw_values_emitted"]["const"])
        self.assertEqual(receipt["network_access"]["const"], "NONE")
        self.assertEqual(
            receipt["source_commitments"]["propertyNames"]["pattern"],
            "^SRC-[A-F0-9]{16}$",
        )

    def test_local_cli_emits_sanitized_json_only(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "resource_miner.privacy_footprint_cli",
                "--input",
                str(ROOT / "fixtures" / "privacy_footprint_synthetic.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["execution"], "DISABLED")
        self.assertEqual(payload["authority_effect"], "NONE")
        self.assertNotIn("alice@example.test", completed.stdout.lower())
        self.assertNotIn("850) 555-0100", completed.stdout)
        self.assertNotIn("192.0.2.10", completed.stdout)


if __name__ == "__main__":
    unittest.main()
