import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PR_MANAGER = ROOT / ".claude" / "skills" / "pr-manager"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PR_MANAGER))

from bridge_receipt_feed import BridgeReceiptFeed
from tools.verified_receipts import read_receipt_events

spec = importlib.util.spec_from_file_location(
    "mutual_understanding_v0_1",
    PR_MANAGER / "mutual_understanding_v0_1.py",
)
mutual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mutual)


class InterrogationReceiptGateTests(unittest.TestCase):
    def make_question(self):
        asker = mutual.PseudonymousActor.create_pseudonym("AGENT", "Z1_PROPOSER")
        return mutual.InterrogationQuestion(
            question_id="Q1",
            asker=asker,
            text="Is the governance objective accurate?",
            target_claim_or_uncertainty="H1",
            purpose="CLARIFY_MODEL",
        )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "receipts.jsonl")
        self.feed = BridgeReceiptFeed(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def gate_with_snapshot(self):
        events, head = read_receipt_events(self.path)
        return mutual.InterrogationGate(
            receipt_events=events,
            receipt_head_hash=head,
            receipt_feed=self.feed,
        )

    def test_missing_receipt_cannot_approve(self):
        gate = mutual.InterrogationGate()
        q = self.make_question()
        gate.submit_question(q)
        with self.assertRaisesRegex(ValueError, "APPROVAL_RECEIPT_REQUIRED"):
            gate.approve_question("Q1", True, "safe")
        self.assertEqual(mutual.QuestionStatus.PENDING_APPROVAL, q.status)

    def test_non_ed25519_emitter_refuses_approval_receipt(self):
        with self.assertRaisesRegex(ValueError, "ED25519"):
            self.feed.emit_interrogation_approval_receipt(
                receipt_id="approval-q1",
                question_id="Q1",
                approved=True,
                evidence_ref="signature:abc",
                verification_method="HUMAN_ATTESTED",
            )

    def test_wrong_question_receipt_fails(self):
        self.feed.emit_interrogation_approval_receipt(
            receipt_id="approval-q2",
            question_id="Q2",
            approved=True,
            evidence_ref="signature:test-only",
            verification_method="ED25519",
        )
        gate = self.gate_with_snapshot()
        q = self.make_question()
        gate.submit_question(q)
        with self.assertRaisesRegex(ValueError, "SUBJECT_MISMATCH"):
            gate.approve_question(
                "Q1", True, "safe", approval_receipt_id="approval-q2"
            )
        self.assertEqual(mutual.QuestionStatus.PENDING_APPROVAL, q.status)

    def test_valid_receipt_approves_and_is_consumed(self):
        self.feed.emit_interrogation_approval_receipt(
            receipt_id="approval-q1",
            question_id="Q1",
            approved=True,
            evidence_ref="signature:test-only",
            verification_method="ED25519",
        )
        gate = self.gate_with_snapshot()
        q = self.make_question()
        gate.submit_question(q)

        decision = gate.approve_question(
            "Q1", True, "safe", approval_receipt_id="approval-q1"
        )
        self.assertTrue(decision.receipt_verified)
        self.assertEqual(mutual.QuestionStatus.APPROVED, q.status)

        # Refresh from the now-extended ledger. The same one-time receipt must
        # no longer resolve in a fresh gate instance.
        events, head = read_receipt_events(self.path)
        replay_gate = mutual.InterrogationGate(
            receipt_events=events,
            receipt_head_hash=head,
            receipt_feed=self.feed,
        )
        q2 = self.make_question()
        replay_gate.submit_question(q2)
        with self.assertRaisesRegex(ValueError, "RECEIPT_ALREADY_CONSUMED"):
            replay_gate.approve_question(
                "Q1", True, "replay", approval_receipt_id="approval-q1"
            )


if __name__ == "__main__":
    unittest.main()
