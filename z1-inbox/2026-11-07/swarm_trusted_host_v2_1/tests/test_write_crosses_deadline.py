"""Follow-up to PR #1153 (CodeRabbit on src/writer.py): a write that starts inside the window but finishes after
not_after must not return COMPLETED with an out-of-window WRITE_RESULT event, which the verifier rejects
(EVENT_OUTSIDE_WINDOW). After the deadline NO event can be valid, so the episode is blocked: no WRITE_RESULT, no
receipt, a new episode id. Written BEFORE the fix (author-run)."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan, iso
from src import writer as writer_mod
from src.verifier import verify
from src.writer import HostWriter, EvidenceError, digest, pub_bytes

INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}
BAD_INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "other99", "value": "55"}


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate(); self.pub = pub_bytes(self.key)
        self.plan = make_plan(self.key); self.pin = digest(self.plan)
        self.w = HostWriter(self.td / "h", self.key, self.plan, self.pin)
        self.last = datetime.fromisoformat(self.plan["window"]["not_after"])
        self.inside = iso(self.last - timedelta(minutes=30))
        self.after = iso(self.last + timedelta(seconds=1))

    def clock(self, *stamps):
        # side_effect over a list: a third reading would raise StopIteration, so the call count is asserted too
        return mock.patch("src.writer.now", side_effect=list(stamps))

    def events(self):
        out = [json.loads(p.read_text()) for p in self.w.events.iterdir()]
        return sorted(out, key=lambda e: e["sequence"])

    def assert_blocked(self):
        self.assertEqual([e["kind"] for e in self.events()], ["REQUEST_RECORDED"])   # no WRITE_RESULT
        with self.assertRaisesRegex(EvidenceError, "WRITE_RESULT_OUTSIDE_WINDOW"):
            self.w.finalize()                                                         # no terminal event, no receipt
        self.assertFalse((self.w.ep / "snapshot.json").exists())
        with self.assertRaisesRegex(EvidenceError, "REPLAY_OR_ALREADY_STARTED"):
            self.w.write("A", "R2", INTENT)
        with self.assertRaises(EvidenceError):
            verify(self.w.plan, self.pin, self.pub, self.td / "h")


class ResultAfterTheDeadline(Base):
    def test_a_completed_write_that_finishes_after_not_after_blocks_the_episode(self):
        with self.clock(self.inside, self.after):
            with self.assertRaisesRegex(EvidenceError, "WRITE_RESULT_OUTSIDE_WINDOW"):
                self.w.write("A", "R1", INTENT)
        self.assert_blocked()
        self.assertEqual(list(self.w.artifacts.iterdir()), [])            # the late artifact is not left behind

    def test_a_rejected_request_whose_result_lands_after_not_after_is_blocked_too(self):
        with self.clock(self.inside, self.after):
            with self.assertRaisesRegex(EvidenceError, "WRITE_RESULT_OUTSIDE_WINDOW"):
                self.w.write("A", "R1", BAD_INTENT)
        self.assert_blocked()

    def test_a_failed_write_whose_result_lands_after_not_after_is_blocked_too(self):
        with mock.patch.object(writer_mod, "open_read_no_follow", lambda p: b"wrong"), self.clock(self.inside, self.after):
            with self.assertRaisesRegex(EvidenceError, "WRITE_RESULT_OUTSIDE_WINDOW"):
                self.w.write("A", "R1", INTENT)
        self.assert_blocked()
        self.assertEqual(list(self.w.artifacts.iterdir()), [])


class ResultInsideTheWindow(Base):
    def test_a_result_exactly_at_not_after_is_still_inside(self):
        with self.clock(self.inside, iso(self.last)):
            self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "COMPLETED")
        self.assertEqual([e["kind"] for e in self.events()], ["REQUEST_RECORDED", "WRITE_RESULT"])

    def test_the_event_carries_the_very_reading_that_was_checked(self):
        stamp = iso(self.last - timedelta(seconds=5))
        with self.clock(self.inside, stamp):
            self.w.write("A", "R1", INTENT)
        result = [e for e in self.events() if e["kind"] == "WRITE_RESULT"][0]
        self.assertEqual(result["observed_utc"], stamp)                   # one clock reading, not a second one

    def test_an_ordinary_write_still_completes_and_verifies(self):
        self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "COMPLETED")
        self.w.finalize()
        self.assertEqual(verify(self.w.plan, self.pin, self.pub, self.td / "h")["tool_status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
