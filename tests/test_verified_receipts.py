import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tools.verified_receipts import (
    ReceiptRequirement,
    VerifiedReceiptResolver,
    append_receipt_event,
    build_receipt_chain_for_testing,
    consume_receipt_atomic,
    read_receipt_events,
)


def receipt_event(receipt_id="r1", **overrides):
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": receipt_id,
        "receipt_type": "HARMONY_GATE",
        "subject": "dissent_preserved",
        "action": "ASSERT_GATE",
        "scope": "run:test",
        "issuer": "bridge-evidence-graph",
        "authority_scope": "NONE",
        "verification_status": "VERIFIED",
        "verification_strength": "OBSERVED",
        "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
        "evidence_ref": f"event:{receipt_id}",
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
        events, head = build_receipt_chain_for_testing([receipt_event(subject="other")])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertEqual("SUBJECT_MISMATCH", result.reason)

    def test_simulated_method_fails_after_canonicalization(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(verification_method="  simulated  ")
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertIn("UNSUPPORTED_VERIFICATION_METHOD", result.reason)

    def test_unknown_positive_sounding_method_fails_allowlist(self):
        events, head = build_receipt_chain_for_testing([
            receipt_event(verification_method="TOTALLY_REAL")
        ])
        result = VerifiedReceiptResolver(events, head).resolve("r1", self.requirement())
        self.assertFalse(result.valid)
        self.assertIn("UNSUPPORTED_VERIFICATION_METHOD", result.reason)

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

    def test_resolution_returns_receipt_copy(self):
        events, head = build_receipt_chain_for_testing([receipt_event()])
        resolver = VerifiedReceiptResolver(events, head)
        first = resolver.resolve("r1", self.requirement())
        first.receipt["subject"] = "mutated"
        second = resolver.resolve("r1", self.requirement())
        self.assertTrue(second.valid)
        self.assertEqual("dissent_preserved", second.receipt["subject"])

    def test_file_backed_append_chain_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.jsonl")
            append_receipt_event(path, receipt_event("r1"))
            append_receipt_event(path, receipt_event("r2"))
            events, head = read_receipt_events(path)
            resolver = VerifiedReceiptResolver(events, head)
            self.assertIsNone(resolver.chain_error)
            self.assertEqual(2, len(events))

    def test_concurrent_writers_do_not_fork_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.jsonl")
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(
                    lambda i: append_receipt_event(path, receipt_event(f"r{i}")),
                    range(16),
                ))
            events, head = read_receipt_events(path)
            resolver = VerifiedReceiptResolver(events, head)
            self.assertIsNone(resolver.chain_error)
            self.assertEqual(16, len(events))
            self.assertEqual(list(range(1, 17)), [e["seq"] for e in events])

    def test_atomic_consume_marks_one_time_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.jsonl")
            append_receipt_event(path, receipt_event("r1", one_time=True))
            _, trusted_head = read_receipt_events(path)

            consume_receipt_atomic(
                path,
                receipt_id="r1",
                requirement=self.requirement(),
                expected_head_hash=trusted_head,
                consumed_by="test",
                subject="dissent_preserved",
            )

            events, new_head = read_receipt_events(path)
            result = VerifiedReceiptResolver(events, new_head).resolve(
                "r1", self.requirement()
            )
            self.assertFalse(result.valid)
            self.assertEqual("RECEIPT_ALREADY_CONSUMED", result.reason)

    def test_atomic_consume_rejects_stale_head(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "receipts.jsonl")
            append_receipt_event(path, receipt_event("r1", one_time=True))
            _, stale_head = read_receipt_events(path)
            append_receipt_event(path, receipt_event("r2"))

            with self.assertRaisesRegex(ValueError, "STALE_RECEIPT_HEAD"):
                consume_receipt_atomic(
                    path,
                    receipt_id="r1",
                    requirement=self.requirement(),
                    expected_head_hash=stale_head,
                    consumed_by="test",
                    subject="dissent_preserved",
                )


if __name__ == "__main__":
    unittest.main()
