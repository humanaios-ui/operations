"""The evidence reader (used by the verifier) must not hang on a FIFO, must refuse non-regular files, must not follow
a symlink leaf and must not leak a descriptor. This closes the part of the earlier held reader patch that was still
open after the descriptor-relative rewrite. Written BEFORE the fix (author-run)."""
import os
import tempfile
import threading
import unittest
from pathlib import Path

from src.writer import open_read_no_follow, EvidenceError


def read_with_timeout(path, seconds=5):
    """Read in a thread so a hang is reported as HUNG instead of freezing the suite; unblock the stuck reader after."""
    out = []

    def run():
        try:
            out.append(open_read_no_follow(path))
        except (EvidenceError, OSError) as exc:
            out.append(exc)
    t = threading.Thread(target=run, daemon=True); t.start(); t.join(seconds)
    if t.is_alive():
        try:
            os.close(os.open(path, os.O_WRONLY | os.O_NONBLOCK))
        except OSError:
            pass
        t.join(2)
        return "HUNG"
    return out[0]


def open_fds():
    return len(os.listdir("/proc/self/fd")) if os.path.isdir("/proc/self/fd") else None


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.d = Path(td.name) / "d"; self.d.mkdir(); self.d.chmod(0o700)


class ReaderHardening(Base):
    def test_regular_file_is_read(self):
        (self.d / "f").write_bytes(b"abc")
        self.assertEqual(open_read_no_follow(self.d / "f"), b"abc")

    def test_a_fifo_does_not_hang_the_reader(self):
        fifo = self.d / "f"
        os.mkfifo(fifo)
        out = read_with_timeout(fifo)
        self.assertNotEqual(out, "HUNG", "open_read_no_follow hung on a FIFO")
        self.assertIsInstance(out, EvidenceError)
        self.assertEqual(str(out), "NOT_A_REGULAR_FILE")

    def test_a_directory_is_refused(self):
        (self.d / "f").mkdir()
        with self.assertRaises((EvidenceError, OSError)):
            open_read_no_follow(self.d / "f")

    def test_a_symlink_leaf_is_refused(self):
        (self.d / "real").write_bytes(b"secret")
        os.symlink(self.d / "real", self.d / "f")
        with self.assertRaises((EvidenceError, OSError)):
            open_read_no_follow(self.d / "f")

    @unittest.skipIf(open_fds() is None, "needs /proc/self/fd")
    def test_no_descriptor_is_leaked_on_any_outcome(self):
        (self.d / "ok").write_bytes(b"x")
        os.mkfifo(self.d / "fifo")
        (self.d / "dir").mkdir()
        os.symlink(self.d / "ok", self.d / "link")
        before = open_fds()
        for name in ("ok", "fifo", "dir", "link", "missing") * 3:
            read_with_timeout(self.d / name, seconds=2)
        self.assertEqual(open_fds(), before)


if __name__ == "__main__":
    unittest.main()
