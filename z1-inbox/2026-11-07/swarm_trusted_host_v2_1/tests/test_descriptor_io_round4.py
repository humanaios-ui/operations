"""Round 4 regression: filesystem reads and writes stay bound to checked directory descriptors.

These synthetic tests do not prove deployment isolation. They force the exact
check/use interleaving without requiring a probabilistic timing race.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.writer import EvidenceError, new_file, open_read_no_follow


class DescriptorRelativeEvidenceIO(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="swarm_descriptor_io_")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.anchor = self.root / "anchor"
        self.anchor.mkdir(mode=0o700)
        self.directory = self.anchor / "evidence"
        self.directory.mkdir(mode=0o700)
        self.canary = self.root / "canary"
        self.canary.mkdir(mode=0o700)
        (self.canary / "evidence").mkdir(mode=0o700)

    def test_new_file_uses_parent_directory_descriptor(self):
        original = os.open
        seen = []
        def tracked(path, flags, *args, **kwargs):
            if str(path) == "artifact.bin":
                seen.append(kwargs.get("dir_fd"))
            return original(path, flags, *args, **kwargs)
        with mock.patch("src.writer.os.open", side_effect=tracked):
            new_file(self.directory / "artifact.bin", b"valid")
        self.assertEqual((self.directory / "artifact.bin").read_bytes(), b"valid")
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], int)

    def test_read_file_uses_parent_directory_descriptor(self):
        (self.directory / "artifact.bin").write_bytes(b"valid")
        original = os.open
        seen = []
        def tracked(path, flags, *args, **kwargs):
            if str(path) == "artifact.bin":
                seen.append(kwargs.get("dir_fd"))
            return original(path, flags, *args, **kwargs)
        with mock.patch("src.writer.os.open", side_effect=tracked):
            found = open_read_no_follow(self.directory / "artifact.bin")
        self.assertEqual(found, b"valid")
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], int)

    def test_ancestor_substitution_does_not_redirect_creation(self):
        original = os.open
        switched = [False]
        def substitute(path, flags, *args, **kwargs):
            if str(path) == "artifact.bin" and not switched[0]:
                switched[0] = True
                self.anchor.rename(self.root / "moved_anchor")
                self.anchor.symlink_to(self.canary, target_is_directory=True)
            return original(path, flags, *args, **kwargs)
        with mock.patch("src.writer.os.open", side_effect=substitute):
            new_file(self.directory / "artifact.bin", b"evidence")
        self.assertTrue(switched[0])
        self.assertEqual((self.root / "moved_anchor" / "evidence" / "artifact.bin").read_bytes(), b"evidence")
        self.assertFalse((self.canary / "evidence" / "artifact.bin").exists())

    def test_ancestor_substitution_does_not_redirect_read(self):
        (self.directory / "artifact.bin").write_bytes(b"genuine")
        (self.canary / "evidence" / "artifact.bin").write_bytes(b"forged")
        original = os.open
        switched = [False]
        def substitute(path, flags, *args, **kwargs):
            if str(path) == "artifact.bin" and not switched[0]:
                switched[0] = True
                self.anchor.rename(self.root / "moved_anchor")
                self.anchor.symlink_to(self.canary, target_is_directory=True)
            return original(path, flags, *args, **kwargs)
        with mock.patch("src.writer.os.open", side_effect=substitute):
            found = open_read_no_follow(self.directory / "artifact.bin")
        self.assertTrue(switched[0])
        self.assertEqual(found, b"genuine")

    def test_symlink_leaf_read_is_denied(self):
        victim = self.root / "victim"
        victim.write_bytes(b"secret")
        (self.directory / "artifact.bin").symlink_to(victim)
        with self.assertRaises(OSError):
            open_read_no_follow(self.directory / "artifact.bin")

    def test_symlink_parent_write_is_denied(self):
        link = self.root / "link"
        link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(OSError):
            new_file(link / "artifact.bin", b"wrong")
        self.assertFalse((self.directory / "artifact.bin").exists())


if __name__ == "__main__":
    unittest.main()
