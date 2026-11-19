"""Follow-up to PR #1153 (CodeRabbit on src/service.py): the no-follow chmod of the socket can be unsupported (older
glibc) and it ran AFTER the socket was bound, so a failure left the socket file behind (a retry then failed) and
server_close() never removed it. Written BEFORE the fix (author-run)."""
import errno
import os
import socket
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src import service
from src.writer import HostWriter, EvidenceError, digest


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        key = Ed25519PrivateKey.generate(); plan = make_plan(key)
        self.w = HostWriter(self.td / "h", key, plan, digest(plan))
        self.sock = self.td / "ipc.sock"

    def server(self):
        return service.Server(self.sock, self.w, "agent", actor_id="A", allowed_uid=os.getuid())

    def mode(self):
        return stat.S_IMODE(os.lstat(self.sock).st_mode)


class UnsupportedNoFollowChmod(Base):
    def test_server_still_starts_with_a_private_socket_when_chmod_is_unsupported(self):
        for exc in (OSError(errno.ENOTSUP, "not supported"), NotImplementedError("chmod: follow_symlinks unavailable")):
            with self.subTest(exc=type(exc).__name__):
                with mock.patch("src.service.os.chmod", side_effect=exc):
                    srv = self.server()
                self.addCleanup(srv.server_close)
                self.assertEqual(self.mode(), 0o600)        # created private from the start, not by a later chmod
                self.assertTrue(stat.S_ISSOCK(os.lstat(self.sock).st_mode))
                srv.server_close()

    def test_a_socket_that_is_not_private_after_setup_is_refused_and_removed(self):
        # chmod unsupported AND no private creation mode: the post-condition (mode 0600) must still catch it.
        with mock.patch("src.service.os.chmod", side_effect=OSError(errno.ENOTSUP, "x")), \
                mock.patch("src.service.os.umask", lambda m: 0):
            with self.assertRaisesRegex(EvidenceError, "SOCKET_PERMISSIONS_NOT_ENFORCED"):
                self.server()
        self.assertFalse(os.path.lexists(self.sock))

    def test_any_other_chmod_failure_fails_closed_removes_the_socket_and_a_retry_works(self):
        with mock.patch("src.service.os.chmod", side_effect=PermissionError(errno.EPERM, "denied")):
            with self.assertRaisesRegex(EvidenceError, "SOCKET_PERMISSIONS_NOT_ENFORCED"):
                self.server()
        self.assertFalse(os.path.lexists(self.sock))          # not left behind
        srv = self.server()                                    # so the retry binds
        self.addCleanup(srv.server_close)
        self.assertEqual(self.mode(), 0o600)


class CleanupIsLimitedToTheSocketItCreated(Base):
    def test_a_stale_socket_from_someone_else_is_not_removed_when_bind_fails(self):
        stale = socket.socket(socket.AF_UNIX); stale.bind(str(self.sock)); stale.close()   # leaves the file behind
        before = os.lstat(self.sock).st_ino
        with self.assertRaises(OSError):                       # EADDRINUSE
            self.server()
        self.assertEqual(os.lstat(self.sock).st_ino, before)   # still there, untouched

    def test_a_failure_after_bind_but_before_serving_removes_the_socket_it_created(self):
        # listen() fails after bind() has created the file: the base class closes the listener but leaves the file.
        with mock.patch("socketserver.UnixStreamServer.server_activate", side_effect=OSError(errno.EIO, "listen failed")):
            with self.assertRaises(OSError):
                self.server()
        self.assertFalse(os.path.lexists(self.sock))
        srv = self.server()                                    # and a retry binds
        self.addCleanup(srv.server_close)

    def test_server_close_removes_its_own_socket_and_is_idempotent(self):
        srv = self.server()
        self.assertTrue(os.path.lexists(self.sock))
        srv.server_close()
        self.assertFalse(os.path.lexists(self.sock))
        srv.server_close()

    def test_server_close_does_not_remove_a_path_that_was_replaced(self):
        srv = self.server()
        os.unlink(self.sock)
        self.sock.write_text("not a socket")                   # someone swapped the path
        srv.server_close()
        self.assertEqual(self.sock.read_text(), "not a socket")

    def test_a_replaced_socket_is_not_removed_either(self):
        srv = self.server()
        os.unlink(self.sock)
        other = socket.socket(socket.AF_UNIX); other.bind(str(self.sock))   # a different socket at the same path
        self.addCleanup(other.close)
        ino = os.lstat(self.sock).st_ino
        srv.server_close()
        self.assertEqual(os.lstat(self.sock).st_ino, ino)


class ProcessStateIsRestored(Base):
    def test_umask_is_restored_after_success_and_after_failure(self):
        before = os.umask(0o022); os.umask(before)
        srv = self.server(); self.addCleanup(srv.server_close)
        now = os.umask(0o022); os.umask(now)
        self.assertEqual(now, before)
        with mock.patch("src.service.os.chmod", side_effect=PermissionError(errno.EPERM, "denied")):
            with self.assertRaises(EvidenceError):
                service.Server(self.td / "second.sock", self.w, "agent", actor_id="A", allowed_uid=os.getuid())
        now = os.umask(0o022); os.umask(now)
        self.assertEqual(now, before)


if __name__ == "__main__":
    unittest.main()
