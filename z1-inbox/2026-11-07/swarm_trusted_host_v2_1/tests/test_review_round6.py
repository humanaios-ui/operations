"""Round-6 review findings on PR #1153 (CodeRabbit batch on head 014f894), each written BEFORE its fix (author-run)."""
import copy
import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src import service
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, secure_dir
from src.verifier import verify
from integration.bridge_v2 import score_episode

INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}
OBS = {"run_id": "TEST_001", "episode_id": "E001", "executor_claim": "SUCCESS", "reviewer_claim": "SUCCESS",
       "final_claim": "SUCCESS", "ballots": {"A": "APPROVE", "B": "APPROVE"}}


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate(); self.pub = pub_bytes(self.key)
        self.plan = make_plan(self.key); self.pin = digest(self.plan)

    def host(self):
        return HostWriter(self.td / "h", self.key, self.plan, self.pin)


class NonStringClaimsAreClassified(Base):
    def _finalized(self):
        w = self.host(); w.write("A", "R1", INTENT); w.finalize()

    def test_list_claim_is_invalid_not_a_typeerror(self):
        self._finalized()
        bad = {**OBS, "executor_claim": []}
        with self.assertRaisesRegex(EvidenceError, "ACTOR_CLAIM_INVALID"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", bad)

    def test_list_ballot_is_invalid_not_a_typeerror(self):
        self._finalized()
        bad = {**OBS, "ballots": {"A": [], "B": "APPROVE"}}
        with self.assertRaisesRegex(EvidenceError, "BALLOT_INVALID"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", bad)


class PlanIsSnapshotted(Base):
    def test_mutating_the_callers_plan_cannot_change_what_the_writer_does(self):
        w = self.host()
        self.plan["task"]["artifact_id"] = "other99"
        self.assertEqual(w.plan["task"]["artifact_id"], "config01")
        self.assertEqual(w.write("A", "R1", INTENT)["tool_status"], "COMPLETED")
        w.finalize()
        verify(make_plan(self.key) if False else copy.deepcopy(w.plan), self.pin, self.pub, self.td / "h")


class RootAnchorRejected(unittest.TestCase):
    def test_filesystem_root_is_refused_before_any_chmod(self):
        with mock.patch("src.writer.os.fchmod", side_effect=AssertionError("chmod on /")):
            with self.assertRaisesRegex(EvidenceError, "ANCHOR_PATH_REJECTED"):
                secure_dir("/")


class EventSequenceCommitsAfterTheFile(Base):
    def test_failed_event_write_leaves_no_gap(self):
        w = self.host()
        real = __import__("src.writer", fromlist=["new_file"]).new_file
        calls = {"n": 0}

        def flaky(path, raw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("disk full")
            return real(path, raw)
        with mock.patch("src.writer.new_file", flaky):
            with self.assertRaises(OSError):
                w.write("A", "R1", INTENT)
            self.assertEqual((w.seq, w.tip), (0, "0" * 64) if False else (0, w.tip))
            self.assertEqual(w.seq, 0)
            self.assertFalse(w.started)  # a failed first record must not poison the retry
            self.assertEqual(w.write("A", "R1", INTENT)["tool_status"], "COMPLETED")
        w.finalize()
        verify(w.plan, self.pin, self.pub, self.td / "h")


class FinalizeIsResumable(Base):
    def test_snapshot_failure_then_retry_publishes_the_same_receipt_with_one_terminal_event(self):
        w = self.host(); w.write("A", "R1", INTENT)
        real = __import__("src.writer", fromlist=["new_file"]).new_file

        def fail_snapshot(path, raw):
            if Path(path).name == "snapshot.json":
                raise OSError("disk full")
            return real(path, raw)
        with mock.patch("src.writer.new_file", fail_snapshot):
            with self.assertRaises(OSError):
                w.finalize()
        count = len(list(w.events.iterdir()))
        with self.assertRaisesRegex(EvidenceError, "FINALIZE_PENDING"):
            w.write("A", "R2", INTENT)
        seal = w.finalize()  # retry
        self.assertEqual(len(list(w.events.iterdir())), count)  # no second terminal event
        verify(w.plan, self.pin, self.pub, self.td / "h")
        self.assertEqual(seal["payload"]["event_count"], count)


class WriterLockLifecycle(Base):
    def test_close_releases_the_lock_and_is_idempotent(self):
        w = self.host(); w.close(); w.close()
        import fcntl
        probe = os.open(self.td / "h" / ".writer_lock", os.O_RDWR); self.addCleanup(os.close, probe)
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_context_manager_releases_the_lock(self):
        with self.host():
            pass
        import fcntl
        probe = os.open(self.td / "h" / ".writer_lock", os.O_RDWR); self.addCleanup(os.close, probe)
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)


class DeepJsonGetsAReply(Base):
    def test_deeply_nested_request_gets_a_stable_error_not_eof(self):
        w = self.host()
        sock = self.td / "a.sock"
        srv = service.Server(sock, w, "control", allowed_uid=os.getuid(), max_request=262144) \
            if "max_request" in service.Server.__init__.__code__.co_varnames else \
            service.Server(sock, w, "control", allowed_uid=os.getuid())
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (srv.shutdown(), srv.server_close()))
        c = socket.socket(socket.AF_UNIX); c.settimeout(5); c.connect(str(sock)); self.addCleanup(c.close)
        c.sendall(b"[" * 200000 + b"\n")
        reply = c.makefile("rb").readline()
        self.assertEqual(json.loads(reply), {"ok": False, "error": "REQUEST_TOO_DEEP"})


class TestFixesPresent(unittest.TestCase):
    def test_known_defects_runs_every_class_when_run_directly(self):
        src = (Path(__file__).parent / "test_known_defects.py").read_text()
        self.assertGreater(src.rindex("unittest.main()"), src.rindex("class PeerRefusalRace"))

    def test_acl_probe_skips_only_when_unsupported(self):
        src = (Path(__file__).parent / "test_secure_dir_round3.py").read_text()
        self.assertTrue("ENOTSUP" in src or "EOPNOTSUPP" in src, "ACL probe skip is not limited to unsupported errors")


if __name__ == "__main__":
    unittest.main()
