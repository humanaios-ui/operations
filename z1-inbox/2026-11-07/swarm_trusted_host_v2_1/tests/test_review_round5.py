"""Round-5 review findings on PR #1153 (CodeRabbit + Copilot), each written BEFORE its fix (author-run)."""
import ast
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src import service
from src.writer import HostWriter, EvidenceError, digest
from tests.test_deploy_check import Base as DeployBase, TOOL, PKG

INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}


class WriterLockReleasedOnInitFailure(unittest.TestCase):
    def test_failed_init_does_not_leave_the_lock_held(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        root = Path(td.name) / "h"
        key = Ed25519PrivateKey.generate()
        plan = make_plan(key)
        first = HostWriter(root, key, plan, digest(plan))
        first.write("A", "R1", INTENT)
        os.close(first.lock_fd)  # drop the first writer's lock so the second one can take it
        with self.assertRaisesRegex(EvidenceError, "EXISTING_EVIDENCE_REJECTED"):
            HostWriter(root, key, plan, digest(plan))
        import fcntl
        probe = os.open(root / ".writer_lock", os.O_RDWR)
        self.addCleanup(os.close, probe)
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)  # raises BlockingIOError if the failed init leaked the lock

    def test_lock_fd_is_close_on_exec(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        key = Ed25519PrivateKey.generate(); plan = make_plan(key)
        w = HostWriter(Path(td.name) / "h", key, plan, digest(plan))
        self.assertFalse(os.get_inheritable(w.lock_fd))


class SlowTrickleHasAnAbsoluteDeadline(unittest.TestCase):
    def test_byte_per_interval_client_cannot_hold_the_channel(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        key = Ed25519PrivateKey.generate(); plan = make_plan(key)
        w = HostWriter(Path(td.name) / "h", key, plan, digest(plan))
        sock = Path(td.name) / "a.sock"
        srv = service.Server(sock, w, "agent", actor_id="A", allowed_uid=os.getuid(), timeout=0.4)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (srv.shutdown(), srv.server_close()))
        slow = socket.socket(socket.AF_UNIX); slow.connect(str(sock)); self.addCleanup(slow.close)
        stop = threading.Event()

        def trickle():
            try:
                while not stop.is_set():
                    slow.send(b" "); time.sleep(0.15)  # always inside the per-recv timeout
            except OSError:
                pass
        threading.Thread(target=trickle, daemon=True).start()
        self.addCleanup(stop.set)
        time.sleep(0.05)
        good = socket.socket(socket.AF_UNIX); good.settimeout(3); good.connect(str(sock)); self.addCleanup(good.close)
        start = time.monotonic()
        good.sendall(json.dumps({"op": "write", "request_id": "R1", "intent": INTENT}).encode() + b"\n")
        reply = good.makefile("rb").readline()
        self.assertTrue(json.loads(reply)["ok"])
        self.assertLess(time.monotonic() - start, 1.5)  # the trickler is cut off at ~timeout, not held forever


class DeployCheckCrashPaths(DeployBase):
    def test_fifo_in_place_of_an_initializer_does_not_hang(self):
        init = self.pkg / "src" / "__init__.py"
        init.unlink(); os.mkfifo(init)
        proc = subprocess.run([sys.executable, "-I", str(TOOL), "--package-root", str(self.pkg), "--plan",
                               str(self.plan_path), "--plan-sha256", self.plan_sha],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("INITIALIZER_NOT_EMPTY:src/__init__.py", json.loads(proc.stdout)["problems"])

    def test_src_is_a_regular_file_reports_instead_of_crashing(self):
        shutil.rmtree(self.pkg / "src"); (self.pkg / "src").write_text("x")
        code, body = self.run_tool()
        self.assertEqual(code, 2)
        self.assertFalse(body["ok"])

    def test_walk_error_is_reported_not_swallowed(self):
        ns = {}
        exec(compile(TOOL.read_text(), str(TOOL), "exec"), ns)

        def failing_walk(top, onerror=None, **kw):
            if onerror:
                onerror(PermissionError(13, "denied", top))
            return iter(())
        with mock.patch.object(os, "walk", failing_walk):
            result = ns["check"](str(self.pkg), str(self.plan_path), self.plan_sha)
        self.assertFalse(result["ok"])
        self.assertIn("UNREADABLE_DIRECTORY:src", result["problems"])


class DeployCheckIsStdlibOnlyByAst(unittest.TestCase):
    def test_no_import_of_the_checked_package_by_any_spelling(self):
        tree = ast.parse(TOOL.read_text())
        banned = {"src", "integration", "tests"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn(a.name.split(".")[0], banned)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertNotIn((node.module or "").split(".")[0], banned)
            elif isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
                self.assertNotIn(name, {"__import__", "import_module", "exec_module", "spec_from_file_location"})
        stdlib = set(sys.stdlib_module_names)
        for node in ast.walk(tree):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                   [node.module] if isinstance(node, ast.ImportFrom) else []
            for m in mods:
                self.assertIn(m.split(".")[0], stdlib)


class RaceTestIsNotVacuous(unittest.TestCase):
    def test_round3_race_test_makes_the_outer_dir_searchable_and_checks_attacker_progress(self):
        src = (Path(__file__).parent / "test_secure_dir_round3.py").read_text()
        self.assertTrue("0o711" in src, "outer dir not search-only")           # other users can traverse to the sticky dir
        self.assertTrue("attacker_ops" in src, "attacker progress unchecked")    # and the test asserts the attacker actually did something


if __name__ == "__main__":
    unittest.main()
