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
        # The umask mock leaves the PROCESS umask in force, so pin a known real one first (review of PR #1274):
        # a caller running with umask 0177 would otherwise get a 0600 socket and no refusal.
        real = os.umask(0)
        try:
            with mock.patch("src.service.os.chmod", side_effect=OSError(errno.ENOTSUP, "x")), \
                    mock.patch("src.service.os.umask", lambda m: 0):
                with self.assertRaisesRegex(EvidenceError, "SOCKET_PERMISSIONS_NOT_ENFORCED"):
                    self.server()
        finally:
            os.umask(real)
        self.assertFalse(os.path.lexists(self.sock))

    def test_the_refusal_does_not_depend_on_the_callers_umask(self):
        real = os.umask(0o177)
        try:
            with mock.patch("src.service.os.chmod", side_effect=OSError(errno.ENOTSUP, "x")), \
                    mock.patch("src.service.os.umask", lambda m: 0o177):
                srv = self.server()          # umask 0177 really makes the socket 0600: accepted, and it is private
                self.addCleanup(srv.server_close)
                self.assertEqual(self.mode(), 0o600)
        finally:
            os.umask(real)

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

    def test_a_competing_bind_that_wins_after_the_absence_check_is_not_unlinked(self):
        # PR #1274 review (Copilot, CodeRabbit): another server binds the path AFTER our absence check and BEFORE
        # our bind. Our bind fails with EADDRINUSE and must leave the winner's live socket alone.
        winner = socket.socket(socket.AF_UNIX)
        self.addCleanup(winner.close)
        real_bind = service.Server.server_bind

        def competing_bind(srv):
            winner.bind(str(self.sock)); winner.listen(1)       # the winner gets there first
            return real_bind(srv)                               # ...so this raises EADDRINUSE
        with mock.patch.object(service.Server, "server_bind", competing_bind):
            with self.assertRaises(OSError) as ctx:
                self.server()
        self.assertEqual(ctx.exception.errno, errno.EADDRINUSE)
        self.assertTrue(stat.S_ISSOCK(os.lstat(self.sock).st_mode))
        probe = socket.socket(socket.AF_UNIX); self.addCleanup(probe.close)
        probe.connect(str(self.sock))                           # the winner is still reachable at its path

    def test_any_failure_of_the_bind_itself_unlinks_nothing(self):
        # Even a bind that fails some other way must not touch whatever is at the path.
        other = socket.socket(socket.AF_UNIX); other.bind(str(self.sock)); self.addCleanup(other.close)
        ino = os.lstat(self.sock).st_ino
        with mock.patch.object(service.Server, "server_bind", side_effect=OSError(errno.EIO, "bind failed")):
            with self.assertRaises(OSError):
                self.server()
        self.assertEqual(os.lstat(self.sock).st_ino, ino)

    def test_a_good_bind_followed_by_an_interrupted_address_lookup_removes_the_socket(self):
        # PR #1274 re-review (CodeRabbit): server_bind() is bind() then getsockname(). An interrupt between them
        # means the bind SUCCEEDED, so the file this process created must not be left behind.
        with mock.patch.object(socket.socket, "getsockname", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.server()
        self.assertFalse(os.path.lexists(self.sock))
        srv = self.server()                                    # and a retry binds
        self.addCleanup(srv.server_close)

    def test_cleanup_never_unlinks_when_the_identity_is_unknown(self):
        # If the post-bind stat failed, identity is None: leave the path alone rather than risk a replacement.
        other = socket.socket(socket.AF_UNIX); other.bind(str(self.sock)); self.addCleanup(other.close)
        ino = os.lstat(self.sock).st_ino
        parent_fd = os.open(self.td, os.O_RDONLY | os.O_DIRECTORY); self.addCleanup(os.close, parent_fd)
        service.Server._discard_socket(parent_fd, "ipc.sock", None)
        self.assertEqual(os.lstat(self.sock).st_ino, ino)

    def test_a_first_stat_failure_after_a_good_bind_does_not_remove_a_replacement(self):
        # The post-bind stat fails (identity unknown) and someone else's socket sits at the path: it survives.
        other = socket.socket(socket.AF_UNIX)
        self.addCleanup(other.close)
        real_stat = os.stat

        def failing_stat(path, *a, **k):
            if path == "ipc.sock" and k.get("dir_fd") is not None and not other.getsockname():
                os.unlink(self.sock); other.bind(str(self.sock))     # a replacement arrives, then our stat fails
                raise OSError(errno.EIO, "stat failed")
            return real_stat(path, *a, **k)
        with mock.patch("src.service.os.stat", failing_stat):
            with self.assertRaises(OSError):
                self.server()
        self.assertTrue(stat.S_ISSOCK(os.lstat(self.sock).st_mode))
        self.assertEqual(other.getsockname(), str(self.sock))     # still the replacement's own socket

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
