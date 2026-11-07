"""CodeRabbit review findings on PR #1153 head 690f9cf, each verified against the code. Written BEFORE the fixes."""
import json
import os
import socket
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan, iso
from src import service
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, secure_dir
from integration import bridge_v2
from integration.bridge_v2 import score_episode

INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}
OBS = {"run_id": "TEST_001", "episode_id": "E001", "executor_claim": "SUCCESS", "reviewer_claim": "SUCCESS",
       "final_claim": "SUCCESS", "ballots": {"A": "APPROVE", "B": "APPROVE"}}


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate()
        self.pub = pub_bytes(self.key)


class BridgeBindsReadbackToAttestedArtifact(Base):  # finding: bridge_v2.py 38-45
    def test_artifact_swapped_between_verify_and_readback_fails_closed(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        w.write("A", "R1", INTENT); w.finalize()
        real = bridge_v2.score_v4
        art = self.td / "h" / plan["run_id"] / plan["episode_id"] / "artifacts" / "config01.json"

        def swap_then_score(*a, **kw):  # the store is writable between the two reads
            art.write_bytes(b'{"artifact_id":"config01","value":"56"}')
            return real(*a, **kw)

        with mock.patch.object(bridge_v2, "score_v4", swap_then_score):
            with self.assertRaisesRegex(EvidenceError, "READBACK_NOT_ATTESTED_ARTIFACT"):
                score_episode(plan, digest(plan), self.pub, self.td / "h", OBS)

    def test_unmodified_artifact_still_scores(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        w.write("A", "R1", INTENT); w.finalize()
        self.assertEqual(score_episode(plan, digest(plan), self.pub, self.td / "h", OBS)["classification"],
                         "VERIFIED_SUCCESS")


class PinsFileIsPinned(Base):  # finding: pins.py 6-14
    def test_plan_without_pins_py_hash_rejected(self):
        plan = make_plan(self.key)
        del plan["protocol_pins"]["pins_sha256"]
        with self.assertRaisesRegex(EvidenceError, "PINS_INVALID"):
            HostWriter(self.td / "h", self.key, plan, digest(plan))

    def test_wrong_pins_py_hash_refused_at_writer_start(self):
        plan = make_plan(self.key)
        plan["protocol_pins"]["pins_sha256"] = "0" * 64
        with self.assertRaisesRegex(EvidenceError, "PINS_CODE_NOT_PINNED"):
            HostWriter(self.td / "h", self.key, plan, digest(plan))


class LegacyPeerCredentialsFailClosed(Base):  # finding: service.py 38-40
    def test_allowed_uid_without_so_peercred_refused_at_start(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        saved = socket.SO_PEERCRED
        delattr(socket, "SO_PEERCRED")
        try:
            with self.assertRaisesRegex(EvidenceError, "LINUX_PEER_CREDENTIALS_REQUIRED"):
                service.Server(self.td / "s.sock", w, "control", allowed_uid=os.getuid())
        finally:
            socket.SO_PEERCRED = saved


class AncestorsOfSecuredPaths(Base):  # finding: writer.py 84-106 (Major)
    def test_world_writable_non_sticky_ancestor_refused(self):
        open_dir = self.td / "open"
        open_dir.mkdir(); open_dir.chmod(0o777)
        with self.assertRaisesRegex(EvidenceError, "ANCESTOR_WRITABLE_BY_OTHERS"):
            secure_dir(open_dir / "evidence")

    def test_sticky_world_writable_ancestor_like_tmp_is_allowed(self):
        sticky = self.td / "sticky"
        sticky.mkdir(); sticky.chmod(0o1777)
        self.assertTrue(secure_dir(sticky / "evidence").is_dir())

    @unittest.skipUnless(os.geteuid() == 0, "needs root to chown")
    def test_ancestor_owned_by_another_user_refused(self):
        foreign = self.td / "foreign"
        foreign.mkdir(); os.chown(foreign, 61501, 61501); foreign.chmod(0o755)
        with self.assertRaisesRegex(EvidenceError, "ANCESTOR_NOT_HOST_OWNED"):
            secure_dir(foreign / "evidence")

    @unittest.skipUnless(os.geteuid() == 0, "needs root to chown")
    def test_existing_leaf_directory_owned_by_another_user_refused_before_any_chmod(self):
        leaf = self.td / "leaf"
        leaf.mkdir(); os.chown(leaf, 61501, 61501); leaf.chmod(0o755)
        with self.assertRaisesRegex(EvidenceError, "DIRECTORY_NOT_HOST_OWNED"):
            secure_dir(leaf)
        self.assertEqual(stat.S_IMODE(leaf.stat().st_mode), 0o755)  # refused BEFORE touching it

    def test_private_tree_accepted(self):
        self.assertTrue(secure_dir(self.td / "a" / "b").is_dir())


class FinalizeWindow(Base):  # finding: writer.py 263-289
    def _written(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        w.write("A", "R1", INTENT)
        return plan, w

    def test_late_finalize_is_refused_before_any_state_change(self):
        plan, w = self._written()
        events_before = sorted(p.name for p in w.events.iterdir())
        late = iso(datetime.now(timezone.utc) + timedelta(hours=6))
        with mock.patch("src.writer.now", return_value=late):
            with self.assertRaisesRegex(EvidenceError, "FINALIZE_OUTSIDE_WINDOW"):
                w.finalize()
        self.assertFalse(w.finished)
        self.assertEqual(sorted(p.name for p in w.events.iterdir()), events_before)
        self.assertFalse((w.ep / "snapshot.json").exists())

    def test_early_finalize_with_no_attempt_is_refused_too(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        early = iso(datetime.now(timezone.utc) - timedelta(hours=6))
        with mock.patch("src.writer.now", return_value=early):
            with self.assertRaisesRegex(EvidenceError, "FINALIZE_OUTSIDE_WINDOW"):
                w.finalize()
        self.assertFalse(w.finished)

    def test_in_window_finalize_after_a_refusal_still_works(self):
        plan, w = self._written()
        late = iso(datetime.now(timezone.utc) + timedelta(hours=6))
        with mock.patch("src.writer.now", return_value=late):
            with self.assertRaises(EvidenceError):
                w.finalize()
        self.assertEqual(w.finalize()["payload"]["tool_status"], "COMPLETED")


class FinalizeSingleReading(Base):  # CodeRabbit follow-up on 5526006: finalized_utc must not take a second reading
    def test_event_and_receipt_share_one_clock_reading(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        not_after = datetime.fromisoformat(plan["window"]["not_after"])
        now0 = datetime.now(timezone.utc)
        readings = iter([iso(now0), iso(now0),                      # request, write result
                         iso(not_after - timedelta(seconds=1)),     # the single finalize reading, inside
                         iso(not_after + timedelta(seconds=1))])    # a second reading would land here, outside
        with mock.patch("src.writer.now", lambda: next(readings)):
            w.write("A", "R1", INTENT)
            seal = w.finalize()
        self.assertEqual(seal["payload"]["finalized_utc"], iso(not_after - timedelta(seconds=1)))
        from src.verifier import verify
        verify(plan, digest(plan), self.pub, self.td / "h")  # raises EVENT_OUTSIDE_WINDOW if a 2nd reading was used


class DirectRunKeepsProcessSmoke(unittest.TestCase):  # finding: tests/test_writer.py 175-185
    def test_main_guard_is_the_last_statement_of_test_writer(self):
        src = (Path(__file__).parent / "test_writer.py").read_text()
        last_code = [l for l in src.splitlines() if l.strip() and not l.lstrip().startswith("#")][-1]
        self.assertIn("unittest.main()", last_code)


if __name__ == "__main__":
    unittest.main()
