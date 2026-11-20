"""Follow-up to PR #1153 (CodeRabbit on src/writer.py): a FAILED write must leave artifacts/ empty, because the
verifier rejects any non-COMPLETED episode whose artifacts/ is not (UNATTESTED_ARTIFACT_EXISTS). If the host cannot
guarantee that, it must fail loudly and produce no receipt, never a verifiable-but-misleading one. Written BEFORE the
fix (author-run)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src import writer as writer_mod
from src.verifier import verify
from src.writer import HostWriter, EvidenceError, digest, pub_bytes
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
        self.w = HostWriter(self.td / "h", self.key, self.plan, self.pin)
        self.art = self.w.artifacts
        self.file = self.art / "config01.json"

    def events(self):
        return len(list(self.w.events.iterdir()))

    def assert_failed_and_verifiable(self):
        self.assertEqual(self.w.outcome, "FAILED")
        self.assertEqual(list(self.art.iterdir()), [])                    # nothing left behind
        self.w.finalize()
        receipt = verify(self.w.plan, self.pin, self.pub, self.td / "h")  # used to raise UNATTESTED_ARTIFACT_EXISTS
        self.assertEqual(receipt["tool_status"], "FAILED")
        self.assertIsNone(receipt["artifact_sha256"])


class FailedWriteLeavesNothingBehind(Base):
    def test_readback_mismatch(self):
        with mock.patch.object(writer_mod, "open_read_no_follow", lambda p: b'{"artifact_id":"config01","value":"99"}'):
            self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "FAILED")
        self.assert_failed_and_verifiable()

    def test_readback_raises(self):
        def boom(path):
            raise EvidenceError("NOT_A_REGULAR_FILE")
        with mock.patch.object(writer_mod, "open_read_no_follow", boom):
            self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "FAILED")
        self.assert_failed_and_verifiable()

    def test_file_swapped_for_a_symlink_is_unlinked_not_followed(self):
        canary = self.td / "canary.txt"; canary.write_bytes(b"do not touch")
        real = writer_mod.open_read_no_follow

        def swap_then_read(path):
            Path(path).unlink()
            os.symlink(canary, path)
            return real(path)                                              # raises: the leaf is now a symlink
        with mock.patch.object(writer_mod, "open_read_no_follow", swap_then_read):
            self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "FAILED")
        self.assertEqual(canary.read_bytes(), b"do not touch")             # the link was removed, not its target
        self.assert_failed_and_verifiable()

    def test_a_failed_episode_can_still_be_scored_as_unknown(self):
        with mock.patch.object(writer_mod, "open_read_no_follow", lambda p: b"wrong"):
            self.w.write("A", "R1", INTENT)
        self.w.finalize()
        out = score_episode(self.w.plan, self.pin, self.pub, self.td / "h", OBS)
        self.assertEqual(out["classification"], "ORACLE_UNKNOWN")

    def test_an_ordinary_write_is_unchanged(self):
        self.assertEqual(self.w.write("A", "R1", INTENT)["tool_status"], "COMPLETED")
        self.assertEqual([p.name for p in self.art.iterdir()], ["config01.json"])
        self.w.finalize()
        self.assertEqual(verify(self.w.plan, self.pin, self.pub, self.td / "h")["tool_status"], "COMPLETED")


class WhenCleanupCannotBeGuaranteedTheEpisodeIsRefused(Base):
    def assert_blocked(self):
        self.assertIsNone(self.w.outcome)
        before = self.events()
        self.assertEqual(before, 1)                                       # REQUEST_RECORDED only: no WRITE_RESULT
        with self.assertRaisesRegex(EvidenceError, "ARTIFACT_RESIDUE_NOT_REMOVED"):
            self.w.finalize()                                             # no terminal event, no receipt
        self.assertFalse((self.w.ep / "snapshot.json").exists())
        self.assertEqual(self.events(), before)
        with self.assertRaisesRegex(EvidenceError, "REPLAY_OR_ALREADY_STARTED"):
            self.w.write("A", "R2", INTENT)                               # and no second attempt in this episode
        with self.assertRaises(EvidenceError):
            verify(self.w.plan, self.pin, self.pub, self.td / "h")        # nothing that could pass verification

    def test_unlink_fails(self):
        real_unlink = os.unlink

        def deny(name, *a, **k):
            if name == "config01.json":
                raise PermissionError(13, "denied")
            return real_unlink(name, *a, **k)
        with mock.patch.object(writer_mod, "open_read_no_follow", lambda p: b"wrong"), \
                mock.patch.object(writer_mod.os, "unlink", deny):
            with self.assertRaisesRegex(EvidenceError, "ARTIFACT_RESIDUE_NOT_REMOVED"):
                self.w.write("A", "R1", INTENT)
        self.assert_blocked()

    def test_a_directory_in_the_artifact_path(self):
        def swap_for_dir(path):
            Path(path).unlink(); Path(path).mkdir()
            return b"wrong"
        with mock.patch.object(writer_mod, "open_read_no_follow", swap_for_dir):
            with self.assertRaisesRegex(EvidenceError, "ARTIFACT_RESIDUE_NOT_REMOVED"):
                self.w.write("A", "R1", INTENT)
        self.assert_blocked()

    def test_a_foreign_file_the_writer_did_not_create(self):
        def drop_extra(path):
            (Path(path).parent / "extra.json").write_bytes(b"{}")
            return b"wrong"
        with mock.patch.object(writer_mod, "open_read_no_follow", drop_extra):
            with self.assertRaisesRegex(EvidenceError, "ARTIFACT_RESIDUE_NOT_REMOVED"):
                self.w.write("A", "R1", INTENT)
        self.assert_blocked()

    def test_responses_are_refused_in_a_blocked_episode(self):
        with mock.patch.object(writer_mod, "open_read_no_follow", lambda p: b"wrong"), \
                mock.patch.object(writer_mod.os, "unlink", mock.Mock(side_effect=PermissionError(13, "denied"))):
            with self.assertRaises(EvidenceError):
                self.w.write("A", "R1", INTENT)
        with self.assertRaisesRegex(EvidenceError, "ARTIFACT_RESIDUE_NOT_REMOVED"):
            self.w.record_response("A", "EXECUTOR_CLAIM", "SUCCESS", "OK", "req_1", "model-a", 1)


if __name__ == "__main__":
    unittest.main()
