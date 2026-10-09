import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
PR_MANAGER = ROOT / ".claude" / "skills" / "pr-manager"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PR_MANAGER))

from bridge_receipt_feed import (
    BridgeReceiptFeed,
    canonical_interrogation_approval_payload,
)
from ed25519_validator import Ed25519Validator
from evidence_validator import EvidenceValidator
from tools.verified_receipts import read_receipt_events

spec = importlib.util.spec_from_file_location(
    "mutual_understanding_v0_1",
    PR_MANAGER / "mutual_understanding_v0_1.py",
)
mutual = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mutual
spec.loader.exec_module(mutual)


class InterrogationReceiptGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "receipts.jsonl")

        self.private = Ed25519PrivateKey.generate()
        public_bytes = self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.verifier = Ed25519Validator({
            "human-z2": {
                "public_key": public_bytes.hex(),
                "key_id": "test-z2-key",
            }
        })
        self.feed = BridgeReceiptFeed(
            self.path,
            authority_verifier=self.verifier,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def make_question(self):
        asker = mutual.PseudonymousActor.create_pseudonym("AGENT", "Z1_PROPOSER")
        return mutual.InterrogationQuestion(
            question_id="Q1",
            asker=asker,
            text="Is the governance objective accurate?",
            target_claim_or_uncertainty="H1",
            purpose="CLARIFY_MODEL",
        )

    def signature_for(self, question_id="Q1", approved=True):
        payload = canonical_interrogation_approval_payload(
            question_id,
            approved,
            "human-z2",
        )
        return self.private.sign(payload).hex()

    def trusted_snapshot_for_test(self):
        # TEST FIXTURE ONLY: production must pin this head through an independent
        # trust channel. The writable feed does not provide a trusted-head API.
        return read_receipt_events(self.path)

    def gate_from_explicit_anchor(self, events, trusted_head):
        return mutual.InterrogationGate(
            receipt_events=events,
            receipt_head_hash=trusted_head,
            receipt_feed=self.feed,
        )

    def emit_approval(self, question_id="Q1", approved=True, receipt_id=None):
        receipt_id = receipt_id or f"approval-{question_id.lower()}"
        self.feed.emit_interrogation_approval_receipt(
            receipt_id=receipt_id,
            question_id=question_id,
            approved=approved,
            signature_hex=self.signature_for(question_id, approved),
        )
        return receipt_id

    def test_missing_receipt_cannot_approve(self):
        gate = mutual.InterrogationGate()
        q = self.make_question()
        gate.submit_question(q)
        with self.assertRaisesRegex(ValueError, "APPROVAL_RECEIPT_REQUIRED"):
            gate.approve_question("Q1", True, "safe")
        self.assertEqual(mutual.QuestionStatus.PENDING_APPROVAL, q.status)

    def test_wrong_signature_cannot_emit_approval_receipt(self):
        other_key = Ed25519PrivateKey.generate()
        bad_signature = other_key.sign(
            canonical_interrogation_approval_payload("Q1", True)
        ).hex()
        with self.assertRaisesRegex(ValueError, "ED25519_VERIFICATION_FAILED"):
            self.feed.emit_interrogation_approval_receipt(
                receipt_id="approval-q1",
                question_id="Q1",
                approved=True,
                signature_hex=bad_signature,
            )

    def test_signature_for_other_question_cannot_be_rebound(self):
        q2_signature = self.signature_for("Q2", True)
        with self.assertRaisesRegex(ValueError, "ED25519_VERIFICATION_FAILED"):
            self.feed.emit_interrogation_approval_receipt(
                receipt_id="approval-q1",
                question_id="Q1",
                approved=True,
                signature_hex=q2_signature,
            )

    def test_wrong_question_receipt_fails_gate_requirement(self):
        self.emit_approval("Q2", True, "approval-q2")
        events, trusted_head = self.trusted_snapshot_for_test()
        gate = self.gate_from_explicit_anchor(events, trusted_head)
        q = self.make_question()
        gate.submit_question(q)

        with self.assertRaisesRegex(ValueError, "SUBJECT_MISMATCH"):
            gate.approve_question(
                "Q1",
                True,
                "safe",
                approval_receipt_id="approval-q2",
            )
        self.assertEqual(mutual.QuestionStatus.PENDING_APPROVAL, q.status)

    def test_valid_receipt_approves_and_is_consumed(self):
        self.emit_approval()
        events, trusted_head = self.trusted_snapshot_for_test()
        gate = self.gate_from_explicit_anchor(events, trusted_head)
        q = self.make_question()
        gate.submit_question(q)

        decision = gate.approve_question(
            "Q1",
            True,
            "safe",
            approval_receipt_id="approval-q1",
        )
        self.assertTrue(decision.receipt_verified)
        self.assertEqual(mutual.QuestionStatus.APPROVED, q.status)

        updated_events, updated_head = self.trusted_snapshot_for_test()
        replay_gate = self.gate_from_explicit_anchor(updated_events, updated_head)
        q2 = self.make_question()
        replay_gate.submit_question(q2)
        with self.assertRaisesRegex(ValueError, "RECEIPT_ALREADY_CONSUMED"):
            replay_gate.approve_question(
                "Q1",
                True,
                "replay",
                approval_receipt_id="approval-q1",
            )

    def test_two_gates_cannot_consume_same_snapshot(self):
        self.emit_approval()
        events, trusted_head = self.trusted_snapshot_for_test()

        gate_a = self.gate_from_explicit_anchor(events, trusted_head)
        gate_b = self.gate_from_explicit_anchor(events, trusted_head)
        qa = self.make_question()
        qb = self.make_question()
        gate_a.submit_question(qa)
        gate_b.submit_question(qb)

        gate_a.approve_question(
            "Q1", True, "first", approval_receipt_id="approval-q1"
        )
        with self.assertRaisesRegex(ValueError, "STALE_RECEIPT_HEAD"):
            gate_b.approve_question(
                "Q1", True, "second", approval_receipt_id="approval-q1"
            )
        self.assertEqual(mutual.QuestionStatus.PENDING_APPROVAL, qb.status)

    def test_terminal_question_cannot_reapply_decision(self):
        self.emit_approval()
        events, trusted_head = self.trusted_snapshot_for_test()
        gate = self.gate_from_explicit_anchor(events, trusted_head)
        q = self.make_question()
        gate.submit_question(q)
        gate.approve_question(
            "Q1", True, "first", approval_receipt_id="approval-q1"
        )
        with self.assertRaisesRegex(ValueError, "QUESTION_NOT_PENDING"):
            gate.approve_question(
                "Q1", True, "again", approval_receipt_id="approval-q1"
            )

    def test_simulated_evidence_is_not_validated(self):
        source = "fixture-source"
        import hashlib
        expected = hashlib.sha256(source.encode()).hexdigest()
        result = EvidenceValidator().validate_evidence_reference({
            "source": source,
            "expected_hash": expected,
        })
        self.assertFalse(result.valid)
        self.assertTrue(result.fixture_consistent)
        self.assertEqual("SIMULATED", result.verification_status)
        self.assertFalse(result.token_issued)


if __name__ == "__main__":
    unittest.main()
