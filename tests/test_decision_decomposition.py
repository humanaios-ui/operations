"""A decomposed candidate carries no decision of its own (red-team read of #410, ChatGPT, 2026-09-19).

`Q-INTENTOS-REFRESH-01` and `Q-INTENTOS-BUS-01` asked d23–d26/d32 and d27–d30 as tables inside one block;
#410 filed each call as its own board-ruling block (`Q-BOARD-RULING-NN`), but the parents kept the same
questions, so the queue held two decision objects per call and a by-hand `ratify.py --apply` on a parent
could read as a ruling on its children. The parents now say **Decomposed into:** and carry no `dNN` row.

This test makes that mechanical, at Z1's cap (no gate path): for every candidate file under z1-inbox/ with
a `**Decomposed into:**` line, each child it names is in INDEX.yaml and is a board-ruling block (a `## Ruling`
section with a `choice:` line — the shape ratify.py refuses to sign by hand), and the parent has no decision
table row (`| **dNN** |`) or decision-bearing `## Options` section left. The parent's ratification stays
independent of its children's (the parent accepts a mechanism; each child is its own call), so the rule is
structural, never a status dependency. Refusing to sign a parent that fails the structural rule is a Tier 2
change and is asked as G4 of `Q-INTENTOS-PAGES-GATE-01`.
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, "z1-inbox")
INDEX = os.path.join(INBOX, "INDEX.yaml")
DECOMPOSED_RE = re.compile(r"^\*\*Decomposed into:\*\*(.+)$", re.M)
QID_RE = re.compile(r"`(Q-[A-Z0-9-]+)`")
RULING_SHAPE_RE = re.compile(r"^## Ruling\s*\n(?:.*\n)*?choice:", re.M)
DECISION_ROW_RE = re.compile(r"^\| \*\*d\d+\*\* \|", re.M)


def decomposed_parents():
    out = {}
    for path in sorted(glob.glob(os.path.join(INBOX, "*", "*.md"))):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        m = DECOMPOSED_RE.search(text)
        if m:
            out[os.path.relpath(path, ROOT)] = (QID_RE.findall(m.group(1)), text)
    return out


def index_entry(index_text: str, q_id: str):
    for entry in re.split(r"(?m)^(?= *- q_id: )", index_text):
        if re.match(rf" *- q_id: {re.escape(q_id)}\s*$", entry.split("\n", 1)[0]):
            return entry
    return None


class DecisionDecomposition(unittest.TestCase):
    def setUp(self):
        with open(INDEX, encoding="utf-8") as fh:
            self.index = fh.read()
        self.parents = decomposed_parents()

    def test_the_two_parents_from_410_are_decomposed(self):
        self.assertIn("z1-inbox/2026-09-17/Q-INTENTOS-REFRESH-01.md", self.parents)
        self.assertIn("z1-inbox/2026-09-17/Q-INTENTOS-BUS-01.md", self.parents)
        self.assertEqual(self.parents["z1-inbox/2026-09-17/Q-INTENTOS-BUS-01.md"][0],
                         ["Q-BOARD-RULING-27", "Q-BOARD-RULING-28", "Q-BOARD-RULING-29", "Q-BOARD-RULING-30"])

    def test_every_child_is_an_indexed_board_ruling_block(self):
        for parent, (children, _) in self.parents.items():
            self.assertTrue(children, f"{parent}: a Decomposed line names no child")
            for child in children:
                entry = index_entry(self.index, child)
                self.assertIsNotNone(entry, f"{parent} names {child}, which is not in INDEX.yaml")
                m = re.search(r"(?m)^ +path: (\S+)", entry)
                self.assertIsNotNone(m, f"{child}: no path in its index entry")
                with open(os.path.join(ROOT, m.group(1)), encoding="utf-8") as fh:
                    self.assertRegex(fh.read(), RULING_SHAPE_RE, f"{child} is not a board-ruling block (## Ruling + choice:)")

    def test_a_decomposed_parent_carries_no_decision_of_its_own(self):
        for parent, (_, text) in self.parents.items():
            self.assertIsNone(DECISION_ROW_RE.search(text), f"{parent} still carries a | **dNN** | decision row")
            self.assertNotIn("\n## Options", text, f"{parent} still carries an Options section")
            self.assertIsNone(RULING_SHAPE_RE.search(text), f"{parent} carries a ruling section of its own")

    def test_a_synthetic_parent_that_kept_its_rows_fails(self):
        text = "**Decomposed into:** `Q-X`\n\n| id | question |\n|---|---|\n| **d99** | still here |\n"
        self.assertIsNotNone(DECISION_ROW_RE.search(text))


if __name__ == "__main__":
    unittest.main()
