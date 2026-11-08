"""Demarius same-UID control-socket finding: isolated Linux UID falsifiers.

All tests are offline. Root-only probe drops client privileges in child processes,
not via threads. It tests real kernel socket permissions and key/store denial.
"""
import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from tests.fixtures import make_plan
from src.writer import HostWriter, EvidenceError, digest, canonical
from src.service import Server

AGENT_A_UID, AGENT_B_UID, CONTROL_UID = 61501, 61502, 61503
WRITE = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}

CHILD = r"""
import json, os, socket, pathlib, sys
path, verb = sys.argv[1:3]
try:
    if verb in ("key", "proc_mem"):
        pathlib.Path(path).read_bytes()
        result = {"outcome": "UNEXPECTED_READ"}
    else:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect(path)
            request = {"op": "finalize"} if verb == "finalize" else {
                "op": "write", "request_id": "R1", "intent": {
                    "action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}}
            s.sendall(json.dumps(request).encode() + b"\n")
            raw = s.recv(5000)
            result = {"outcome": "REPLY", "reply": json.loads(raw)}
except OSError as exc:
    result = {"outcome": "DENIED", "errno": exc.errno}
result["uid"] = os.geteuid()
print(json.dumps(result))
"""


def call_as(uid, path, verb):
    # Do not use preexec_fn in a multi-threaded server test.
    # subprocess performs credential change without a Python child hook.
    out = subprocess.run([sys.executable, "-c", CHILD, str(path), verb],
                         capture_output=True, text=True, timeout=7,
                         user=uid, group=uid, extra_groups=[])
    if out.returncode:
        raise AssertionError(out.stderr)
    return json.loads(out.stdout)


class IdentityBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.key = Ed25519PrivateKey.generate()

    def test_duplicate_uid_policy_rejected(self):
        plan = make_plan(self.key)
        plan["role_uids"] = {"host": os.getuid(), "agent_a": 61501,
                             "agent_b": 61502, "control": 61501}
        with self.assertRaisesRegex(EvidenceError, "ROLE_UIDS_NOT_DISTINCT"):
            HostWriter(self.base / "host", self.key, plan, digest(plan))

    def test_unpinned_isolation_server_rejected(self):
        plan = make_plan(self.key)
        host = HostWriter(self.base / "host", self.key, plan, digest(plan))
        with self.assertRaisesRegex(EvidenceError, "ROLE_UID_POLICY_NOT_PINNED"):
            Server(self.base / "agent.sock", host, "agent", actor_id="A",
                   allowed_uid=61501, enforce_isolation=True)

    def test_pinned_policy_cannot_run_in_demo_mode(self):
        plan = make_plan(self.key)
        plan["role_uids"] = {"host": os.getuid(), "agent_a": 61501,
                             "agent_b": 61502, "control": 61503}
        # Only valid on Linux root (otherwise host UID may equal test UID).
        if os.getuid() in (61501, 61502, 61503):
            self.skipTest("test UID collision")
        host = HostWriter(self.base / "host", self.key, plan, digest(plan))
        with self.assertRaisesRegex(EvidenceError, "ISOLATION_REQUIRED_BY_PLAN"):
            Server(self.base / "control.sock", host, "control",
                   allowed_uid=os.getuid(), enforce_isolation=False)

    def test_mismatched_control_uid_rejected(self):
        plan = make_plan(self.key)
        plan["role_uids"] = {"host": os.getuid(), "agent_a": 61501,
                             "agent_b": 61502, "control": 61503}
        host = HostWriter(self.base / "host", self.key, plan, digest(plan))
        with self.assertRaisesRegex(EvidenceError, "ROLE_UID_NOT_AUTHORIZED"):
            Server(self.base / "control.sock", host, "control",
                   allowed_uid=61501, enforce_isolation=True)

    @unittest.skipUnless(sys.platform == "linux" and os.geteuid() == 0,
                         "requires Linux root for independent real-UID child clients")
    def test_agent_cannot_finalize_or_read_private_store(self):
        os.chmod(self.base, 0o711)  # traverse only, never list or write
        plan = make_plan(self.key)
        plan["role_uids"] = {"host": 0, "agent_a": AGENT_A_UID,
                             "agent_b": AGENT_B_UID, "control": CONTROL_UID}
        host = HostWriter(self.base / "host", self.key, plan, digest(plan))
        key_file = host.root / "private_signer_key"
        # Persist the actual ephemeral test signer, not a dummy placeholder.
        # Client probes must never return or print the key bytes.
        key_file.write_bytes(self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()))
        key_file.chmod(0o600)
        ipc = self.base / "ipc"
        ipc.mkdir(mode=0o700)
        sockets = [
            (ipc / "a.sock", "agent", "A", AGENT_A_UID),
            (ipc / "b.sock", "agent", "B", AGENT_B_UID),
            (ipc / "ctrl.sock", "control", None, CONTROL_UID),
        ]
        servers = []
        for path, role, actor, uid in sockets:
            srv = Server(path, host, role, actor_id=actor, allowed_uid=uid,
                         enforce_isolation=True)
            servers.append(srv)
            self.addCleanup(srv.server_close)
            thread = threading.Thread(target=srv.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(srv.shutdown)
        a, b, ctrl = [s[0] for s in sockets]
        for uid in (AGENT_A_UID, AGENT_B_UID):
            refused = call_as(uid, ctrl, "finalize")
            self.assertEqual(refused["outcome"], "DENIED")
            self.assertEqual(refused["errno"], 13)
            private = call_as(uid, key_file, "key")
            self.assertEqual(private["outcome"], "DENIED")
            self.assertEqual(private["errno"], 13)
            process_memory = call_as(uid, "/proc/%s/mem" % os.getpid(), "proc_mem")
            self.assertEqual(process_memory["outcome"], "DENIED")
            self.assertIn(process_memory["errno"], (1, 13))
        self.assertFalse(host.finished)
        self.assertEqual(call_as(AGENT_B_UID, a, "write")["outcome"], "DENIED")
        valid = call_as(AGENT_A_UID, a, "write")
        self.assertEqual(valid["reply"]["reply"]["tool_status"], "COMPLETED")
        control = call_as(CONTROL_UID, ctrl, "finalize")
        self.assertEqual(control["reply"]["reply"]["status"], "FINALIZED")
        self.assertTrue(host.finished)
        self.assertEqual(host.outcome, "COMPLETED")
        self.assertEqual(os.stat(ctrl).st_uid, CONTROL_UID)
        self.assertEqual(stat.S_IMODE(os.stat(ctrl).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(ipc).st_mode), 0o711)


if __name__ == "__main__":
    unittest.main()
