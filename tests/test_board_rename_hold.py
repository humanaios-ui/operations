"""The d33 hold as a check: choice-aware, read off the ruling sections and the Worker, not the index status alone.

Z2 (2026-09-19) asked for the board's rename to `ui/intent-os-board.html` as a successor block to d19
(Q-BOARD-RULING-33), conditioned on d31 (Q-BOARD-PUBLISH-01): the rename executes only after d31's ruling PR
has merged, carries the Worker's redirect from the old path exactly when d31 ruled `serve behind login`, carries
no Worker obligation when d31 ruled `stay local`, and stays held while d31 is `later`. Two red-team reads
(#410, #411) found a status-only check would pass unauthorised trees, so this one reads the `choice:` line of
both ruling sections (the relay writes it; a by-hand PR writes the same line) and the Worker source:

  new file exists  ⇒  d33 ratified with choice `rename to intent-os-board.html`            (falsifier a)
                   ⇒  d31 ratified with choice `serve behind login` or `stay local`, never `later`  (falsifier c)
                   ⇒  `serve behind login`: board/worker.mjs answers the old path with a 301   (falsifier d)
                   ⇒  `stay local`: no redirect in the Worker — the wrong branch would be a redirect (falsifier d)
  new file absent  ⇒  nothing to check: the hold holds, or the ruled move has not executed yet

Shape contract for the index reader (documented because it is text, not a YAML load): a candidate entry
begins at a line `- q_id: <id>` (any indent) and runs to the next such line; its status is the first line
`status: <token>` inside it, any indent, the token optionally quoted. `.z1-control/validate.py` emits exactly
that shape today; if the shape changes, `test_status_reader_reads_the_live_index` fails first.

Where it runs: the harness's `t3-pytest-research` row (pytest over tests/), so the refresh job after every
merge to main — post-merge detection. `quality-baseline` lists its pytest files one by one and does not
include this one; adding it is G2 of Q-INTENTOS-PAGES-GATE-01, Z2's to rule. Until then a bad merge is
proven, not refused.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_BOARD = os.path.join(ROOT, "ui", "intent-os-board.html")
OLD_BOARD_NAME = "intent-os-humanaios-v3_3.html"
INDEX = os.path.join(ROOT, "z1-inbox", "INDEX.yaml")
D31 = os.path.join(ROOT, "z1-inbox", "2026-09-18", "Q-BOARD-PUBLISH-01.md")
D33 = os.path.join(ROOT, "z1-inbox", "2026-09-19", "Q-BOARD-RULING-33.md")
WORKER = os.path.join(ROOT, "board", "worker.mjs")
RENAME, SERVE, STAY = "rename to intent-os-board.html", "serve behind login", "stay local"


def candidate_status(index_text: str, q_id: str) -> str:
    """The `status:` of one `- q_id:` entry, read as text (see the shape contract above)."""
    for entry in re.split(r"(?m)^(?= *- q_id: )", index_text):
        if re.match(rf" *- q_id: {re.escape(q_id)}\s*$", entry.split("\n", 1)[0]):
            m = re.search(r"(?m)^ *status:[ \t]*[\"']?([a-z0-9_]+)[\"']?[ \t]*$", entry)  # awaiting_z2 carries a digit
            return m.group(1) if m else "absent"
    return "absent"


def ruling_choice(block_text: str):
    """The `choice:` line of a block's `## Ruling` section — None while it is empty (OPEN)."""
    m = re.search(r"(?ms)^## Ruling[ \t]*\n.*?^choice:[ \t]*([^\n]*?)[ \t]*$", block_text)
    return (m.group(1) or None) if m else None


def worker_redirects_old_path(worker_text) -> bool:
    return worker_text is not None and OLD_BOARD_NAME in worker_text and "301" in worker_text


def hold_violations(new_exists, d31_status, d31_choice, d33_status, d33_choice, worker_text):
    """Every way a tree can contradict d33's state table. Empty = the hold holds or the ruled move executed."""
    if not new_exists:
        return []
    v = []
    if d33_status != "ratified" or d33_choice != RENAME:
        v.append(f"ui/intent-os-board.html exists but d33 is {d33_status} / {d33_choice!r}: the rename was not authorised (falsifier a)")
    if d31_status != "ratified" or d31_choice not in (SERVE, STAY):
        v.append(f"ui/intent-os-board.html exists but d31 is {d31_status} / {d31_choice!r}: the hold was not honoured (falsifier c)")
    if d31_choice == SERVE and not worker_redirects_old_path(worker_text):
        v.append("d31 ruled serve behind login but board/worker.mjs does not answer the old path with a 301: the move was not one move (falsifier d)")
    if d31_choice == STAY and worker_redirects_old_path(worker_text):
        v.append("d31 ruled stay local but board/worker.mjs carries a redirect: the wrong branch of the state table executed (falsifier d)")
    return v


def read(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class BoardRenameHold(unittest.TestCase):
    def test_the_live_tree_honours_the_hold(self):
        idx = read(INDEX)
        v = hold_violations(os.path.isfile(NEW_BOARD),
                            candidate_status(idx, "Q-BOARD-PUBLISH-01"), ruling_choice(read(D31) or ""),
                            candidate_status(idx, "Q-BOARD-RULING-33"), ruling_choice(read(D33) or ""),
                            read(WORKER))
        self.assertEqual(v, [], "\n".join(v))

    def test_status_reader_reads_the_live_index(self):
        idx = read(INDEX)
        self.assertIn(candidate_status(idx, "Q-BOARD-PUBLISH-01"), ("awaiting_z2", "ratified", "rejected", "edit_requested"))
        self.assertIn(candidate_status(idx, "Q-BOARD-RULING-33"), ("awaiting_z2", "ratified", "rejected", "edit_requested"))
        self.assertEqual(candidate_status(idx, "Q-NOT-A-CANDIDATE"), "absent")

    def test_status_reader_on_synthetic_shapes(self):
        idx = ("candidates:\n- q_id: Q-A\n  title: \"a\\\n    \\ b\"\n  status: awaiting_z2\n"
               "- q_id: Q-B\n  status: ratified\n  note: \"status: awaiting_z2 in prose must not count\"\n"
               "    - q_id: Q-C\n        status: 'ratified'\n"
               "- q_id: Q-D\n  status: \"rejected\"\n")
        self.assertEqual(candidate_status(idx, "Q-A"), "awaiting_z2")
        self.assertEqual(candidate_status(idx, "Q-B"), "ratified")
        self.assertEqual(candidate_status(idx, "Q-C"), "ratified", "deeper indent and single quotes")
        self.assertEqual(candidate_status(idx, "Q-D"), "rejected", "double quotes")
        self.assertEqual(candidate_status(idx, "Q-"), "absent")

    def test_choice_reader_on_the_live_blocks_and_synthetic_rulings(self):
        self.assertIn(ruling_choice(read(D31)), (None, SERVE, STAY, "later"))
        self.assertIn(ruling_choice(read(D33)), (None, RENAME, "keep the frozen path", "later"))
        open_block = "# x\n\n## Ruling\n\nchoice:\nby:\nat:\nstatus: OPEN\n"
        self.assertIsNone(ruling_choice(open_block))
        ruled = "# x\n\n## Ruling\n\nchoice: rename to intent-os-board.html\nby: Night\nat: 2026-09-19T00:00:00Z\nstatus: DECIDED\n"
        self.assertEqual(ruling_choice(ruled), RENAME)
        self.assertIsNone(ruling_choice("# x\n\nchoice: decoy outside a ruling section\n"))

    def test_every_invalid_transition_is_caught(self):
        with_redirect = 'if (path === "/intent-os-humanaios-v3_3.html") return Response.redirect(new URL("/intent-os-board.html", url), 301);'
        without = "export default { fetch() {} }"
        ok = [
            (True, "ratified", SERVE, "ratified", RENAME, with_redirect),
            (True, "ratified", STAY, "ratified", RENAME, without),
            (True, "ratified", STAY, "ratified", RENAME, None),        # the Worker file gone: still no obligation
            (False, "awaiting_z2", None, "awaiting_z2", None, without),  # today's tree
            (False, "ratified", "later", "ratified", RENAME, without),   # ruled rename, d31 later: held, nothing executed
            (False, "ratified", SERVE, "ratified", "keep the frozen path", without),
        ]
        for case in ok:
            self.assertEqual(hold_violations(*case), [], case)
        bad = [
            ((True, "ratified", "later", "ratified", RENAME, with_redirect), "falsifier c"),   # d31 later, rename landed
            ((True, "ratified", SERVE, "ratified", "keep the frozen path", with_redirect), "falsifier a"),
            ((True, "ratified", SERVE, "ratified", "later", with_redirect), "falsifier a"),
            ((True, "ratified", SERVE, "awaiting_z2", None, with_redirect), "falsifier a"),
            ((True, "awaiting_z2", None, "ratified", RENAME, without), "falsifier c"),
            ((True, "ratified", SERVE, "ratified", RENAME, without), "falsifier d"),          # served, no redirect
            ((True, "ratified", STAY, "ratified", RENAME, with_redirect), "falsifier d"),     # local, redirect resurrected
            ((True, "ratified", "later", "awaiting_z2", None, None), "falsifier a"),          # everything wrong at once
        ]
        for case, expect in bad:
            v = hold_violations(*case)
            self.assertTrue(v, case)
            self.assertTrue(any(expect in x for x in v), (case, v))


if __name__ == "__main__":
    unittest.main()
