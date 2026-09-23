import unittest

from tools.verified_receipts import (
    ReceiptRequirement,
    VerifiedReceiptResolver,
    build_receipt_chain_for_testing,
)


def receipt_event(**overrides):
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "r1",
        "receipt_type": "HARMONY_GATE",
        "subject": "dissent_preserved",
        "action": "ASSERT_GATE",
        "scope": "run:test",
        "issuer": "bridge-evidence-graph",
        "authority_scope": "NONE",
        "verification_status": "VERIFIED",
        "verification_strength": "OBSERVED",
        "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
        "evidence_ref": "event:123",
        "one_time": False,
    }
    event.update(overrides)
    return event


class VerifiedReceiptResolverTests(unittest.TestCase):
    def requirement(self):
        return ReceiptRequirement(
            receipt_type="HARMONY_GATE",
            subject="dissent_preserved",
            action="ASSERT_GATE",
            scope="run:test",
            min_strength="OBSERVED",
        )

    def test_valid_receipt_resolves(self):
        events, head = build_receipt_chain_for_testing([receipt_event()])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertTrue(result.valid)

    def test_pinned_head_mismatch_fails(self):
        events, _ = build_receipt_chain_for_testing([receipt_event()])
        result = VerifiedReceiptResolver(events, "0" * 64).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertIn("PINNED_HEAD_MISMATCH", result.reason)

    def test_wrong_subject_fails(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(subject="other")
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertEqual("SUBJECT_MISMATCH", result.reason)

    def test_simulated_method_fails(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(verification_method="SIMULATED")
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertIn("DISALLOWED_VERIFICATION_METHOD", result.reason)

    def test_revoked_receipt_fails(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(),
            {"type": "RECEIPT_REVOKED", "receipt_id": "r1", "by": "bridge"},
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertEqual("RECEIPT_REVOKED", result.reason)

    def test_consumed_one_time_receipt_fails(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(one_time=True),
            {
                "type": "RECEIPT_CONSUMED",
                "receipt_id": "r1",
                "subject": "dissent_preserved",
                "by": "consumer",
            },
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertEqual("RECEIPT_ALREADY_CONSUMED", result.reason)


if __name__ == "__main__":
    unittest.main()
