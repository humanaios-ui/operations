import unittest

from workspace_evidence_bus.tools.workspace_event import build_event, validate_event


class WorkspaceEventTests(unittest.TestCase):
    def make_event(self):
        return build_event(
            event_id="EVT-test-001",
            event_type="ROUNDTRIP_TEST",
            subject_ref="SESSION-WORKSPACE-EVIDENCE-BUS-001",
            actor_ref="SYSTEM-GITHUB-ACTIONS",
            source_system="GITHUB",
            source_ref="issue:681",
            observed_at="2026-10-02T20:52:00Z",
            idempotency_key="roundtrip:test:001",
            state_version=0,
            payload={"paper_only": True, "test": "write-read-hash"},
        )

    def test_valid_event(self):
        self.assertEqual(validate_event(self.make_event()), [])

    def test_payload_tamper_fails(self):
        event = self.make_event()
        event["payload"]["test"] = "tampered"
        self.assertTrue(any("payload_hash mismatch" in e for e in validate_event(event)))

    def test_bad_previous_hash_fails(self):
        event = self.make_event()
        event["previous_event_hash"] = "abc"
        self.assertIn("previous_event_hash must be null or lowercase SHA-256", validate_event(event))

    def test_authority_is_explicit(self):
        event = self.make_event()
        event["authority_effect"] = "AUTO_EXECUTE"
        self.assertIn("invalid authority_effect", validate_event(event))


if __name__ == "__main__":
    unittest.main()
