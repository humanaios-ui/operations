"""Follow-up to PR #1153 (CodeRabbit on integration/readback.py): the readback must not follow a symlink for the
artifact or for the store directory, and must not be redirected between its check and its read. Written BEFORE the
fix (author-run)."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tests.fixtures import ROOT  # noqa: F401  (puts the package on sys.path)
import integration.bridge_v2  # noqa: F401  (adds integration/ to sys.path, as the bridge does)
import readback as readback_mod
from readback import readback

MANIFEST = {"artifact_id": "config01", "baseline": "0", "proposed": "1", "min_allowed": "0", "max_allowed": "2",
            "max_delta": "1", "write_attempt_confirmed": True}
GOOD = json.dumps({"artifact_id": "config01", "value": "1"}).encode()
OUTSIDE = json.dumps({"artifact_id": "config01", "value": "2"}).encode()   # would PASS differently if it were read


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.store = self.td / "store"; self.store.mkdir()
        self.outside = self.td / "outside"; self.outside.mkdir()
        (self.outside / "config01.json").write_bytes(OUTSIDE)

    def write_good(self):
        (self.store / "config01.json").write_bytes(GOOD)


class OrdinaryBehaviourIsUnchanged(Base):
    def test_regular_file_is_read_and_scored(self):
        self.write_good()
        out = readback(MANIFEST, self.store)
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(len(out["readback_sha256"]), 64)

    def test_missing_artifact_keeps_its_confirmed_or_unconfirmed_meaning(self):
        self.assertEqual(readback(MANIFEST, self.store)["verdict"], "FAIL")  # confirmed write, artifact absent
        unconfirmed = {**MANIFEST, "write_attempt_confirmed": False}
        self.assertEqual(readback(unconfirmed, self.store)["verdict"], "UNKNOWN")

    def test_missing_or_non_directory_store_is_unavailable(self):
        self.assertEqual(readback(MANIFEST, self.td / "nope")["reasons"], ["artifact_store_unavailable"])
        (self.td / "afile").write_text("x")
        self.assertEqual(readback(MANIFEST, self.td / "afile")["reasons"], ["artifact_store_unavailable"])


class SymlinksAreRefused(Base):
    def test_symlinked_artifact_is_refused(self):
        os.symlink(self.outside / "config01.json", self.store / "config01.json")
        out = readback(MANIFEST, self.store)
        self.assertEqual((out["verdict"], out["reasons"], out["readback_sha256"]),
                         ("UNKNOWN", ["symlink_artifact_rejected"], None))

    def test_dangling_symlinked_artifact_is_refused(self):
        os.symlink(self.td / "does-not-exist", self.store / "config01.json")
        self.assertEqual(readback(MANIFEST, self.store)["reasons"], ["symlink_artifact_rejected"])

    def test_symlinked_store_directory_is_refused(self):
        (self.outside / "config01.json").write_bytes(GOOD)          # a perfectly valid artifact, outside the store
        link = self.td / "link-to-outside"
        os.symlink(self.outside, link)
        out = readback(MANIFEST, link)
        self.assertEqual((out["verdict"], out["reasons"], out["readback_sha256"]),
                         ("UNKNOWN", ["artifact_store_symlink_rejected"], None))


class NotRedirectedBetweenCheckAndRead(Base):
    def test_artifact_swapped_for_a_symlink_at_open_time_is_not_followed(self):
        self.write_good()
        real_open = os.open
        swapped = []

        def swap_then_open(path, flags, *args, **kwargs):
            if path == "config01.json" and not swapped:   # the moment the artifact is opened
                (self.store / "config01.json").unlink()
                os.symlink(self.outside / "config01.json", self.store / "config01.json")
                swapped.append(True)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(readback_mod.os, "open", swap_then_open):
            out = readback(MANIFEST, self.store)
        self.assertTrue(swapped, "the race was never exercised")
        self.assertNotEqual(out["verdict"], "FAIL")
        self.assertEqual((out["verdict"], out["readback_sha256"]), ("UNKNOWN", None))  # never the outside bytes


class NonRegularArtifactsAreHandledSafely(Base):
    def test_a_fifo_in_place_of_the_artifact_does_not_hang(self):
        fifo = self.store / "config01.json"
        os.mkfifo(fifo)
        result = []
        t = threading.Thread(target=lambda: result.append(readback(MANIFEST, self.store)), daemon=True)
        t.start(); t.join(5)
        if t.is_alive():  # unblock the stuck reader so the test process can finish
            try:
                os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
            except OSError:
                pass
        self.assertFalse(t.is_alive(), "readback hung on a FIFO")
        self.assertEqual(result[0]["verdict"], "UNKNOWN")

    def test_a_directory_in_place_of_the_artifact_is_unknown_not_a_crash(self):
        (self.store / "config01.json").mkdir()
        out = readback(MANIFEST, self.store)
        self.assertEqual((out["verdict"], out["readback_sha256"]), ("UNKNOWN", None))


class DocumentedScope(Base):
    def test_symlinks_above_the_store_are_trusted_as_given(self):
        """Documented scope: the caller supplies the store path (the bridge builds it from the verified host root,
        whose ancestors the verifier already checks). Only the store directory itself and the artifact are
        refused if they are links, so a legitimate symlinked parent such as /tmp on macOS keeps working."""
        real_parent = self.td / "real-parent"; (real_parent / "store").mkdir(parents=True)
        (real_parent / "store" / "config01.json").write_bytes(GOOD)
        os.symlink(real_parent, self.td / "linked-parent")
        self.assertEqual(readback(MANIFEST, self.td / "linked-parent" / "store")["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
