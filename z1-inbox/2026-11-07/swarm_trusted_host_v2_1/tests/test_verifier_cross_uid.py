"""Follow-up to PR #1153 (Copilot and CodeRabbit on src/writer.py and src/verifier.py): the verifier read evidence
through a helper that required the containing directory to be owned by the verifier's OWN euid, so an independent
verifier running as another user was refused a host-owned, read-only snapshot. Written BEFORE the fix (author-run).

Policy under test: for READS, a directory may be owned by the verifier, by root (ancestors only), or by a UID the
frozen plan names as the host (plan role_uids.host). It still may not be writable by others, carry an ACL, or be a
symlink. The writer's own paths keep the strict rule."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, open_read_no_follow

PKG = Path(__file__).resolve().parents[1]
ROOT_ONLY = unittest.skipUnless(os.geteuid() == 0, "needs root to run a verifier under another UID")
A, B, C, V = 61711, 61712, 61713, 61720          # agent A, agent B, control, and the independent verifier
INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}

VERIFY = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from src.verifier import verify
from src.writer import EvidenceError
d = json.load(sys.stdin)
try:
    r = verify(d["plan"], d["pin"], bytes.fromhex(d["pub"]), Path(d["root"]))
    print(json.dumps({"ok": True, "status": r["tool_status"]}))
except EvidenceError as e:
    print(json.dumps({"ok": False, "error": str(e)}))
"""


class ReadPolicyUnit(unittest.TestCase):
    """Ownership policy of the read helper, tested by presenting a different euid (works without root)."""

    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.sub = self.td / "snap"; self.sub.mkdir()
        (self.sub / "f.json").write_bytes(b"{}")
        self.owner = os.stat(self.sub).st_uid
        self.other = self.owner + 1000

    def read(self, **kw):
        with mock.patch("src.writer.os.geteuid", return_value=self.other):    # "the verifier runs as someone else"
            return open_read_no_follow(self.sub / "f.json", **kw)

    def test_default_is_still_strict(self):
        with self.assertRaisesRegex(EvidenceError, "NOT_HOST_OWNED"):
            self.read()

    def test_a_directory_owned_by_a_trusted_uid_is_readable(self):
        self.assertEqual(self.read(trusted_uids=frozenset({self.owner})), b"{}")

    def test_trusting_some_other_uid_does_not_help(self):
        with self.assertRaisesRegex(EvidenceError, "NOT_HOST_OWNED"):
            self.read(trusted_uids=frozenset({self.owner + 7}))

    def test_a_trusted_owner_does_not_excuse_a_group_or_world_writable_directory(self):
        self.sub.chmod(0o777)
        with self.assertRaisesRegex(EvidenceError, "WRITABLE_BY_OTHERS"):
            self.read(trusted_uids=frozenset({self.owner}))
        self.sub.chmod(0o775)
        with self.assertRaisesRegex(EvidenceError, "WRITABLE_BY_OTHERS"):
            self.read(trusted_uids=frozenset({self.owner}))

    def test_a_symlinked_directory_is_still_refused(self):
        link = self.td / "link"; os.symlink(self.sub, link)
        with mock.patch("src.writer.os.geteuid", return_value=self.other):
            with self.assertRaises((EvidenceError, OSError)):          # ENOTDIR from O_NOFOLLOW|O_DIRECTORY
                open_read_no_follow(link / "f.json", trusted_uids=frozenset({self.owner}))

    def test_the_verifier_owning_the_directory_still_works_with_no_policy_at_all(self):
        self.assertEqual(open_read_no_follow(self.sub / "f.json"), b"{}")


@ROOT_ONLY
class VerifyAsAnotherUser(unittest.TestCase):
    """A real independent verifier process, started under a different UID, against a host-owned snapshot."""

    def setUp(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate(); self.pub = pub_bytes(self.key)

    def episode(self, with_role_uids=True):
        extra = {"role_uids": {"host": 0, "agent_a": A, "agent_b": B, "control": C}} if with_role_uids else {}
        plan = make_plan(self.key, **extra)
        pin = digest(plan)
        root = self.td / "host"
        w = HostWriter(root, self.key, plan, pin)
        w.write("A", "R1", INTENT, peer_uid=A if with_role_uids else None)
        w.finalize(control_peer_uid=C if with_role_uids else None)
        w.close()
        return plan, pin, root

    def export_readable(self, root):
        """What a read-only snapshot export does: keep the owner, open up read and traverse for others."""
        os.chmod(self.td, 0o755)
        for current, dirs, files in os.walk(root):
            os.chmod(current, 0o755)
            for name in files:
                os.chmod(os.path.join(current, name), 0o644)

    def verify_as(self, plan, pin, root, uid=V):
        proc = subprocess.run([sys.executable, "-I", "-c", VERIFY, str(PKG)], capture_output=True, text=True,
                              input=json.dumps({"plan": plan, "pin": pin, "pub": self.pub.hex(), "root": str(root)}),
                              timeout=60, user=uid, group=uid, extra_groups=[])
        self.assertTrue(proc.stdout.strip(), proc.stderr[-400:])
        return json.loads(proc.stdout)

    def test_independent_verifier_reads_a_host_owned_snapshot(self):
        plan, pin, root = self.episode()
        self.export_readable(root)
        out = self.verify_as(plan, pin, root)
        self.assertEqual(out, {"ok": True, "status": "COMPLETED"})

    def test_without_a_host_uid_in_the_plan_a_foreign_owner_is_still_refused(self):
        plan, pin, root = self.episode(with_role_uids=False)
        self.export_readable(root)
        out = self.verify_as(plan, pin, root)
        self.assertFalse(out["ok"])
        self.assertRegex(out["error"], "NOT_HOST_OWNED")

    def test_directories_owned_by_an_agent_uid_are_refused_even_for_a_cross_uid_verifier(self):
        plan, pin, root = self.episode()
        self.export_readable(root)
        ep = root / plan["run_id"] / plan["episode_id"]
        for d in (ep, ep / "events", ep / "artifacts", ep / "responses"):
            os.chown(d, A, A)                                   # an agent now owns the evidence directories
        out = self.verify_as(plan, pin, root)
        self.assertFalse(out["ok"])
        self.assertRegex(out["error"], "NOT_HOST_OWNED")

    def test_a_world_writable_evidence_directory_is_refused(self):
        plan, pin, root = self.episode()
        self.export_readable(root)
        os.chmod(root / plan["run_id"] / plan["episode_id"] / "events", 0o777)
        out = self.verify_as(plan, pin, root)
        self.assertFalse(out["ok"])
        self.assertRegex(out["error"], "WRITABLE_BY_OTHERS")

    def test_the_host_user_still_verifies_its_own_evidence(self):
        plan, pin, root = self.episode()
        self.export_readable(root)
        from src.verifier import verify
        self.assertEqual(verify(plan, pin, self.pub, root)["tool_status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main()
