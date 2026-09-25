import json
import tempfile
import unittest
from pathlib import Path

from crb.gate import ADVANCE, HOLD, compute_gate, evaluate_independence
from crb.prp import event_hash, package_root, verify_event_chain


class GateTests(unittest.TestCase):
    def test_internal_profile_satisfies(self):
        result = evaluate_independence(
            {"S": 1, "C": 2, "T": 1, "O": 0, "D": 1},
            "INTERNAL_MACHINE_INDEPENDENT",
        )
        self.assertTrue(result.satisfied)

    def test_external_requires_external_operator(self):
        result = evaluate_independence(
            {"S": 2, "C": 2, "T": 2, "O": 1, "D": 2},
            "EXTERNALLY_REPLAYED",
            external_replay_performed=True,
        )
        self.assertFalse(result.satisfied)
        self.assertIn("O:1<2", result.deficits)

    def test_disqualifier_blocks(self):
        result = evaluate_independence(
            {"S": 2, "C": 2, "T": 2, "O": 2, "D": 2},
            "EXTERNALLY_REPLAYED",
            external_replay_performed=True,
            disqualifiers=["FIRST_PASS_CONTEXT_LEAK"],
        )
        self.assertFalse(result.satisfied)

    def test_gate_is_mechanical(self):
        self.assertEqual(
            compute_gate(
                ["SUPPORTED", "SUPPORTED", "SUPPORTED"],
                evidence_integrity="VALID",
                process_integrity="VALID",
                independence_satisfied=True,
                unresolved_critical_challenges=0,
            ),
            ADVANCE,
        )
        self.assertEqual(
            compute_gate(
                ["SUPPORTED", "NOT_SUPPORTED", "SUPPORTED"],
                evidence_integrity="VALID",
                process_integrity="VALID",
                independence_satisfied=True,
                unresolved_critical_challenges=0,
            ),
            HOLD,
        )


class PackageTests(unittest.TestCase):
    def test_digest_excludes_its_own_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "receipts").mkdir()
            (root / "claim.txt").write_text("claim", encoding="utf-8")
            before = package_root(root)
            (root / "receipts" / "package.sha256").write_text(before, encoding="utf-8")
            after = package_root(root)
            self.assertEqual(before, after)

    def test_event_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            first = {
                "seq": 1,
                "event_type": "SUBMITTED",
                "artifact_refs": [],
                "prev_event_hash": None,
            }
            first["event_hash"] = event_hash(first)
            second = {
                "seq": 2,
                "event_type": "EVIDENCE_FROZEN",
                "artifact_refs": ["evidence:root"],
                "prev_event_hash": first["event_hash"],
            }
            second["event_hash"] = event_hash(second)
            path.write_text(
                json.dumps(first, sort_keys=True) + "\n" +
                json.dumps(second, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(verify_event_chain(path), (True, "VALID"))


if __name__ == "__main__":
    unittest.main()
