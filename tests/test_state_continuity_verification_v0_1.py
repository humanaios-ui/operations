"""SCVC v0.1 synthetic regression. No GitHub/HLKS runtime or issuer authentication."""
import importlib.util
import json
import jsonschema
import pathlib
import unittest

TOOL = pathlib.Path(__file__).resolve().parents[1] / "tools" / "state_continuity_verification_v0_1.py"
spec = importlib.util.spec_from_file_location("scvc", TOOL)
scvc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scvc)

SHA = "a" * 40
CONTRACT = "b" * 40
SOURCE = "source:github:pull_request:55"
OBS = "OBS-SYN-55"


def vlr():
    # Synthetic VLR-shaped subset, not a verified or self-authenticating record.
    return {
        "schema_version": "humanaios.validated_learning_record.v1",
        "record_id": "VLR-SYN-55", "domain": "operations",
        "created_at": "2026-10-01T00:00:00Z",
        "confidence": {"score": 0.0, "method_ref": "synthetic-only"},
        "uncertainty": {"level": "UNKNOWN", "reason_codes": ["LIMITED_SAMPLE"]},
        "supersession": {"supersedes": [], "superseded_by": []},
        "source_commit": SHA, "authority_effect": "NONE",
        "source_refs": [{"source_id": SOURCE, "source_type": "pull_request",
                         "repository": "humanaios-ui/operations", "source_commit": SHA,
                         "locator": "synthetic://github/pull/55", "content_sha256": None}],
        "observation_refs": [{"observation_id": OBS, "source_id": SOURCE,
                              "observed_at": "2026-10-01T00:00:00Z",
                              "recorded_at": "2026-10-01T00:00:00Z", "kind": "FAILURE"}],
        "correction_refs": [],
        "validation_receipts": [{
            "receipt_id": "SYNTHETIC-FORGEABLE",
            "issuer_repository": "humanaios-ui/operations",
            "workflow_path": ".github/workflows/quality-baseline.yml",
            "run_id": "1", "run_attempt": 1,
            "workflow_commit": SHA, "subject_commit": SHA,
            "conclusion": "success",
            "issuer_claimed_verification_status": "VERIFIED",
            "verification_evidence_ref": "synthetic:unverified",
            "verified_at": "2026-10-01T00:00:00Z"
        }],
        "privacy_scope": {"owner_domain": "operations", "allowed_domains": ["operations"],
                          "purpose": "research", "data_classes": ["PUBLIC"],
                          "consent_ref": None, "retention_until": "2026-12-31T00:00:00Z",
                          "deletion_supported": True},
        "revocation": {"state": "ACTIVE", "event_ref": None, "changed_at": None},
        "retrieval": {"state": "ELIGIBLE", "eligible_domains": ["operations"],
                      "eligibility_checked_at": "2026-10-01T00:00:00Z"},
        "validity_window": {"valid_from": "2026-10-01T00:00:00Z",
                            "expires_at": "2026-11-01T00:00:00Z"},
        "applicability": {"contract_refs": [{"repository": "humanaios-ui/operations",
                                             "path": "schemas/validated_learning_record_v1.schema.json",
                                             "commit": CONTRACT}], "constraints": []},
    }


def graph():
    return {
        "status": "DERIVED_NON_CANONICAL",
        "graph_id": "humanaios-cross-chat-longitudinal-evidence-graph",
        "version": "0.2.0",
        "predecessor": {"sha256": "a" * 64, "nodes": 1,
                        "edges": 0, "status": "SYNTHETIC"},
        "invariants": ["GRAPH_IS_NOT_AUTHORITY"],
        "sources": [{"id": SOURCE, "type": "github_work_item_observation",
                     "evidence_class": "SOURCE_OBSERVED",
                     "authority_effect": "NONE"}],
        "entities": [{"id": "entity:55", "type": "semantic_entity",
                      "semantic_type": "issue", "hydration_state": "SOURCE_OBSERVED",
                      "source_refs": [SOURCE]}],
        "assertions": [{"id": "assertion:55", "subject": "entity:55",
                        "predicate": "HAS_OBSERVED_WORK_ITEM_METADATA",
                        "epistemic_state": "OBSERVED", "source_refs": [SOURCE],
                        "authority_effect": "NONE"}],
        "events": [{"id": OBS, "entity_ref": "entity:55",
                    "observed_on": "2026-10-01",
                    "type": "hydration_observation", "source_ref": SOURCE,
                    "authority_effect": "NONE"}],
    }


def request():
    return {"domain": "operations", "purpose": "research", "at": "2026-10-10T08:00:00Z",
            "source_commit": SHA, "contract_commit": CONTRACT}


class FiniteTests(unittest.TestCase):
    def test_369_is_exactly_recoverable(self):
        d = scvc.assess_finite(range(9), lambda s: (2*s) % 9, lambda _: None)
        self.assertEqual(d["status"], "EXACTLY_RECOVERABLE")
        self.assertFalse(d["authenticated"])

    def test_projection_collision_not_recoverable(self):
        states = [{"id": 1, "status": "OPEN"}, {"id": 1, "status": "DONE"}]
        d = scvc.assess_finite(states, lambda s: s["id"], lambda _: None,
                               lambda s: s["status"])
        self.assertEqual(d["status"], "NOT_ESTABLISHED")
        self.assertIn("FINITE_COLLISION_COUNTEREXAMPLE", d["reason_codes"])

    def test_semantic_only(self):
        states = [{"id": 1, "status": "DONE", "note": "a"},
                  {"id": 1, "status": "DONE", "note": "b"}]
        d = scvc.assess_finite(states, lambda s: s["id"], lambda _: None,
                               lambda s: s["status"])
        self.assertEqual(d["status"], "SEMANTICALLY_RECOVERABLE")

    def test_retained_witness_recovers_exactly(self):
        d = scvc.assess_finite(range(9), lambda x: x % 3, lambda x: x // 3)
        self.assertEqual(d["status"], "EXACTLY_RECOVERABLE")

    def test_empty_and_limit_fail_closed(self):
        self.assertEqual(scvc.assess_finite([], lambda x:x, lambda x:x)["status"], "NOT_ESTABLISHED")
        self.assertEqual(scvc.assess_finite(range(3), lambda x:x, lambda x:x, max_states=2)["status"], "NOT_ESTABLISHED")


class ContractShapeTests(unittest.TestCase):
    def test_source_vlr_fixture_conforms_to_canonical_schema(self):
        path = TOOL.parents[1] / "schemas" / "validated_learning_record_v1.schema.json"
        schema = json.loads(path.read_text())
        jsonschema.validate(vlr(), schema,
                            cls=jsonschema.Draft202012Validator,
                            format_checker=jsonschema.FormatChecker())

    def test_synthetic_session_graph_conforms_to_canonical_schema(self):
        path = TOOL.parents[1] / "chat_graph" / "schema" / "longitudinal_graph.schema.json"
        schema = json.loads(path.read_text())
        jsonschema.validate(graph(), schema, cls=jsonschema.Draft202012Validator)

    def test_scvc_report_conforms_to_its_own_schema(self):
        path = TOOL.parents[1] / "schemas" / "state_continuity_verification_v0_1.schema.json"
        schema = json.loads(path.read_text())
        report = scvc.assess_hlks_session(vlr(), graph(), "entity:55", request())
        jsonschema.validate(report, schema, cls=jsonschema.Draft202012Validator)
        altered = dict(report, can_authorize=True)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(altered, schema, cls=jsonschema.Draft202012Validator)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.v, self.g, self.r = vlr(), graph(), request()

    def audit(self):
        return scvc.assess_hlks_session(self.v, self.g, "entity:55", self.r)

    def test_binding_not_proof_even_with_verified_receipt_claim(self):
        a = self.audit()
        self.assertEqual(a["status"], "NOT_ESTABLISHED")
        self.assertIn("SOURCE_BINDING_NOT_PROOF", a["reason_codes"])
        self.assertEqual(a["source_refs"], [SOURCE])
        self.assertEqual(a["observation_refs"], [OBS])
        self.assertFalse(a["can_authorize"])
        self.assertEqual(a["authority_effect"], "NONE")

    def test_deterministic_report_id(self):
        self.assertEqual(self.audit(), self.audit())

    def test_changed_source_pin_fails_closed(self):
        self.r["source_commit"] = "c" * 40
        self.assertIn("SOURCE_COMMIT_MISMATCH", self.audit()["reason_codes"])

    def test_changed_contract_pin_fails_closed(self):
        self.r["contract_commit"] = "c" * 40
        self.assertIn("CONTRACT_COMMIT_MISMATCH", self.audit()["reason_codes"])

    def test_unpinned_source_fails_closed(self):
        self.v["source_refs"][0]["source_commit"] = None
        self.assertIn("UNPINNED_OR_CHANGED_SOURCE", self.audit()["reason_codes"])

    def test_cross_domain_is_denied(self):
        self.r["domain"] = "human"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")

    def test_wrong_purpose_is_denied(self):
        self.r["purpose"] = "learning"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")

    def test_private_content_never_crosses_graph_boundary(self):
        self.v["privacy_scope"]["data_classes"] = ["RECOVERY"]
        report = self.audit()
        self.assertEqual(report["status"], "RECONSTRUCTION_DENIED")
        self.assertEqual(report["source_refs"], [])
        self.assertNotIn("synthetic://", str(report))

    def test_revoked_and_expired_are_denied(self):
        self.v["revocation"]["state"] = "REVOKED"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")
        self.v["revocation"]["state"] = "ACTIVE"
        self.r["at"] = "2027-01-01T00:00:00Z"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")

    def test_conflicts_abstain_no_automatic_winner(self):
        self.g["assertions"][0]["epistemic_state"] = "CONTESTED"
        self.assertIn("UNRESOLVED_OR_CHAT_DERIVED_CLAIMS", self.audit()["reason_codes"])

    def test_corrections_require_replay(self):
        self.g["events"].append({"type":"correction", "entity_ref":"entity:55", "authority_effect":"NONE"})
        self.assertIn("CORRECTION_REPLAY_REQUIRED", self.audit()["reason_codes"])

    def test_cross_source_observation_mismatch_fails_closed(self):
        self.v["observation_refs"][0]["source_id"] = "unknown"
        self.assertIn("MALFORMED_OR_UNBOUND_RECORD", self.audit()["reason_codes"])

    def test_source_not_bound(self):
        self.g["entities"][0]["source_refs"] = []
        self.assertIn("NO_SHARED_SOURCE_BINDING", self.audit()["reason_codes"])

    def test_graph_authority_injection_denied(self):
        self.g["sources"][0]["authority_effect"] = "Z2"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")

    def test_vlr_authority_injection_denied(self):
        self.v["authority_effect"] = "Z2"
        self.assertEqual(self.audit()["status"], "RECONSTRUCTION_DENIED")

    def test_missing_entity_fails_closed(self):
        self.g["entities"].clear()
        self.assertIn("ENTITY_MISSING_OR_DUPLICATED", self.audit()["reason_codes"])

    def test_invalid_timestamp_fails_closed(self):
        self.r["at"] = "2026-10-10"
        self.assertIn("MALFORMED_OR_UNBOUND_RECORD", self.audit()["reason_codes"])

    def test_schema_version_drift_fails_closed(self):
        self.g["status"] = "CANONICAL"
        self.assertIn("INTERFACE_VERSION_MISMATCH", self.audit()["reason_codes"])

    def test_event_id_must_match_observation_reference(self):
        self.g["events"][0]["id"] = "another-event"
        self.assertIn("OBSERVATION_EVENT_NOT_BOUND", self.audit()["reason_codes"])

    def test_duplicate_graph_sources_fail_closed(self):
        self.g["sources"].append(dict(self.g["sources"][0]))
        self.assertIn("DUPLICATE_GRAPH_SOURCES", self.audit()["reason_codes"])

    def test_private_text_in_source_id_cannot_be_echoed(self):
        self.v["source_refs"][0]["source_id"] = "person@example.com"
        r = self.audit()
        self.assertIn("MALFORMED_OR_UNBOUND_RECORD", r["reason_codes"])
        self.assertNotIn("person@", str(r))

    def test_invalid_entity_identifier_abstains(self):
        d = scvc.assess_hlks_session(self.v, self.g, "private / secret", self.r)
        self.assertIn("INVALID_OPAQUE_ENTITY_REF", d["reason_codes"])
        self.assertEqual(d["subject_ref"], "unknown")

    def test_report_never_contains_raw_claim_or_private_locator(self):
        self.v["source_refs"][0]["locator"] = "SECRET: synthetic-only"
        self.g["assertions"][0]["object"] = "PRIVATE: synthetic-only"
        r = str(self.audit())
        self.assertNotIn("SECRET", r)
        self.assertNotIn("PRIVATE:", r)


if __name__ == "__main__":
    unittest.main()
