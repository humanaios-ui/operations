"""Round 3 hardening of secure_dir (CodeRabbit thread on writer.py): descriptor-relative walk, ACL refusal,
hostile concurrent rename. Written BEFORE the implementation (author-run). Real-UID tests need root."""
import os
import struct
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from src.writer import secure_dir, EvidenceError

ROOT_ONLY = unittest.skipUnless(os.geteuid() == 0, "needs root to run an attacker under another UID")
ATTACKER = 61711


def acl_blob(extra_uid):
    def ent(tag, perm, ident=0xFFFFFFFF):
        return struct.pack("<HHI", tag, perm, ident)
    return struct.pack("<I", 2) + ent(1, 7) + ent(2, 5, extra_uid) + ent(4, 0) + ent(0x10, 5) + ent(0x20, 0)


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.td.chmod(0o700)


class DescriptorWalk(Base):
    def test_creates_missing_parents_private_and_returns_the_path(self):
        out = secure_dir(self.td / "a" / "b" / "c")
        self.assertEqual(out, self.td / "a" / "b" / "c")
        self.assertEqual(oct(out.stat().st_mode & 0o777), "0o700")

    def test_dotdot_components_refused(self):
        with self.assertRaisesRegex(EvidenceError, "PATH_NOT_NORMALIZED"):
            secure_dir(self.td / "a" / ".." / "b")

    def test_relative_input_is_made_absolute_and_still_checked(self):
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.td)
        out = secure_dir("rel")
        self.assertTrue(out.is_absolute())

    def test_symlink_leaf_and_symlink_ancestor_refused(self):
        real = self.td / "real"; real.mkdir()
        (self.td / "link").symlink_to(real)
        with self.assertRaisesRegex(EvidenceError, "SYMLINK_PATH"):
            secure_dir(self.td / "link")
        with self.assertRaisesRegex(EvidenceError, "SYMLINK_PATH"):
            secure_dir(self.td / "link" / "child")

    def test_a_file_in_the_way_is_refused_cleanly(self):
        (self.td / "file").write_text("x")
        with self.assertRaises(EvidenceError):
            secure_dir(self.td / "file")
        with self.assertRaises(EvidenceError):
            secure_dir(self.td / "file" / "child")

    def test_chmod_is_applied_through_the_checked_descriptor_not_the_path(self):
        # the leaf is chmod-ed via fchmod on the descriptor that was ownership-checked
        d = self.td / "leaf"; d.mkdir(); d.chmod(0o755)
        secure_dir(d)
        self.assertEqual(oct(d.stat().st_mode & 0o777), "0o700")


class ChmodUsesTheCheckedDescriptor(Base):
    def test_leaf_mode_is_set_with_fchmod_never_a_path_chmod(self):
        from unittest import mock
        with mock.patch("src.writer.os.chmod", side_effect=AssertionError("path-based chmod")) as by_path, \
                mock.patch("src.writer.os.fchmod", wraps=os.fchmod) as by_fd:
            out = secure_dir(self.td / "leaf")
        by_path.assert_not_called()
        self.assertEqual(by_fd.call_count, 1)
        self.assertEqual(oct(out.stat().st_mode & 0o777), "0o700")


class RepointedPath(Base):
    def test_path_that_resolves_elsewhere_after_the_walk_is_refused(self):
        from unittest import mock
        real_stat = os.stat
        def swapped(target, *args, **kwargs):
            info = real_stat(target, *args, **kwargs)
            if kwargs.get("dir_fd") is None and Path(str(target)) == self.td / "x":
                values = list(info); values[1] = info.st_ino + 1  # a different inode: the path was re-pointed
                return os.stat_result(values)
            return info
        with mock.patch("src.writer.os.stat", side_effect=swapped):
            with self.assertRaisesRegex(EvidenceError, "PATH_CHANGED_DURING_CHECK"):
                secure_dir(self.td / "x")


class AclRefusal(Base):
    def setUp(self):
        super().setUp()
        try:
            probe = self.td / "probe"; probe.mkdir()
            os.setxattr(probe, "system.posix_acl_access", acl_blob(12345))
            os.removexattr(probe, "system.posix_acl_access")
            probe.rmdir()
        except OSError:
            self.skipTest("filesystem has no POSIX ACL support")

    def test_access_acl_on_an_existing_leaf_refused_before_chmod(self):
        d = self.td / "leaf"; d.mkdir(); d.chmod(0o755)
        os.setxattr(d, "system.posix_acl_access", acl_blob(12345))
        with self.assertRaisesRegex(EvidenceError, "ACL_PRESENT"):
            secure_dir(d)

    def test_acl_on_an_ancestor_refused(self):
        anc = self.td / "anc"; anc.mkdir()
        os.setxattr(anc, "system.posix_acl_access", acl_blob(12345))
        with self.assertRaisesRegex(EvidenceError, "ACL_PRESENT"):
            secure_dir(anc / "child")

    def test_default_acl_on_a_directory_refused(self):
        d = self.td / "leaf"; d.mkdir()
        os.setxattr(d, "system.posix_acl_default", acl_blob(12345))
        with self.assertRaisesRegex(EvidenceError, "ACL_PRESENT"):
            secure_dir(d)

    def test_no_acl_is_accepted(self):
        secure_dir(self.td / "clean")


@ROOT_ONLY
class HostileConcurrentRename(Base):
    """An unprivileged attacker in a sticky world-writable parent races the host. Whatever the interleaving,
    a returned path must be a host-owned, non-symlink, 0700 directory, and nothing outside may be chmod-ed."""

    ATTACK = textwrap.dedent('''
        import os, sys, time
        parent, canary, end = sys.argv[1], sys.argv[2], float(sys.argv[3])
        target = os.path.join(parent, "run")
        while time.time() < end:
            for step in range(4):
                try:
                    if step == 0: os.mkdir(target, 0o777)
                    elif step == 1: os.rmdir(target)
                    elif step == 2: os.symlink(canary, target)
                    else: os.unlink(target)
                except OSError:
                    pass
    ''')

    def test_returned_directory_is_always_host_owned_and_the_canary_is_never_touched(self):
        parent = self.td / "sticky"; parent.mkdir(); parent.chmod(0o1777)
        canary = self.td / "canary"; canary.mkdir(); canary.chmod(0o755)
        os.chown(canary, ATTACKER, ATTACKER)
        import time
        end = time.time() + 6
        proc = subprocess.Popen([sys.executable, "-I", "-c", self.ATTACK, str(parent), str(canary), str(end)],
                                user=ATTACKER, group=ATTACKER, extra_groups=[])
        self.addCleanup(proc.kill)
        ok = refused = 0
        allowed = {"SYMLINK_PATH", "DIRECTORY_NOT_HOST_OWNED", "UNSAFE_DIRECTORY", "PATH_CHANGED_DURING_CHECK"}
        while time.time() < end:
            try:
                out = secure_dir(parent / "run")
            except EvidenceError as exc:
                self.assertIn(str(exc), allowed)
                refused += 1
            else:
                info = os.lstat(out)
                self.assertTrue(os.path.isdir(out) and not os.path.islink(out))
                self.assertEqual(info.st_uid, os.geteuid())
                self.assertEqual(info.st_mode & 0o777, 0o700)
                ok += 1
                try:
                    os.rmdir(out)  # reset so the race continues
                except OSError:
                    pass
        proc.wait(timeout=10)
        self.assertEqual(oct(canary.stat().st_mode & 0o777), "0o755", "host chmod-ed through a hostile symlink")
        self.assertGreater(ok + refused, 50)

    def test_attacker_owned_ancestor_swap_is_refused(self):
        anc = self.td / "anc"; anc.mkdir(); os.chown(anc, ATTACKER, ATTACKER)
        with self.assertRaisesRegex(EvidenceError, "ANCESTOR_NOT_HOST_OWNED"):
            secure_dir(anc / "run")


if __name__ == "__main__":
    unittest.main()
