"""The d33 hold, as a check rather than prose (Z2's red-team review of #410, residual risk 2).

Z2 (2026-09-19) asked for the board's rename to `ui/intent-os-board.html` as a successor block to d19
(Q-BOARD-RULING-33), held until d31 (Q-BOARD-PUBLISH-01) rules. The block's falsifier says a rename that
lands before d31's ruling merges is reverted. This test makes that mechanical: it fails whenever the new
filename exists in the tree while d31 is still awaiting Z2 in z1-inbox/INDEX.yaml, or while d33 itself is
still awaiting Z2 (the rename is d33's executing move, so it cannot precede d33's own ruling either).

It reads the index as text, not YAML, so it needs no dependency and cannot be fooled by a loader default.
Run by the quality-baseline job (pytest over tests/) and by the test harness (t3-pytest).
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_BOARD = os.path.join(ROOT, "ui", "intent-os-board.html")
INDEX = os.path.join(ROOT, "z1-inbox", "INDEX.yaml")


def candidate_status(index_text: str, q_id: str) -> str:
    """The `status:` of one `- q_id:` entry, read as text: the entry runs to the next `- q_id:` line."""
    for entry in re.split(r"(?m)^(?= *- q_id: )", index_text):
        if re.match(rf" *- q_id: {re.escape(q_id)}\s*$", entry.split("\n", 1)[0]):
            m = re.search(r"(?m)^ +status: ([a-z0-9_]+)\s*$", entry)  # awaiting_z2 carries a digit
            return m.group(1) if m else "absent"
    return "absent"


class BoardRenameHold(unittest.TestCase):
    def test_rename_waits_for_d31_and_d33(self):
        if not os.path.isfile(NEW_BOARD):
            return  # the hold holds: the new name is not in the tree
        with open(INDEX, encoding="utf-8") as fh:
            idx = fh.read()
        d31 = candidate_status(idx, "Q-BOARD-PUBLISH-01")
        d33 = candidate_status(idx, "Q-BOARD-RULING-33")
        self.assertEqual(d31, "ratified", f"ui/intent-os-board.html exists but d31 (Q-BOARD-PUBLISH-01) is {d31!r}: "
                                          "the rename is held until d31 rules (Q-BOARD-RULING-33, falsifier c)")
        self.assertEqual(d33, "ratified", f"ui/intent-os-board.html exists but d33 (Q-BOARD-RULING-33) is {d33!r}: "
                                          "the rename is d33's executing move and cannot precede its ruling (falsifier a)")

    def test_status_reader_reads_the_live_index(self):
        with open(INDEX, encoding="utf-8") as fh:
            idx = fh.read()
        self.assertIn(candidate_status(idx, "Q-BOARD-PUBLISH-01"), ("awaiting_z2", "ratified", "rejected", "edit_requested"))
        self.assertEqual(candidate_status(idx, "Q-NOT-A-CANDIDATE"), "absent")

    def test_status_reader_on_a_synthetic_index(self):
        idx = ("candidates:\n- q_id: Q-A\n  title: \"a\\\n    \\ b\"\n  status: awaiting_z2\n"
               "- q_id: Q-B\n  status: ratified\n  note: \"status: awaiting_z2 in prose must not count\"\n")
        self.assertEqual(candidate_status(idx, "Q-A"), "awaiting_z2")
        self.assertEqual(candidate_status(idx, "Q-B"), "ratified")
        self.assertEqual(candidate_status(idx, "Q-"), "absent")


if __name__ == "__main__":
    unittest.main()
