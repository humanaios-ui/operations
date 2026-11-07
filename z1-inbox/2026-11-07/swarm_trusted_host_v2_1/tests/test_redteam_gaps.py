"""Red-team gap regressions for PR #1153 head 690f9cf (probes P1, P8-P12). Written BEFORE the fixes."""
import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, read_private_key, canonical
from src.verifier import verify
from src.service import Server
from integration.bridge_v2 import score_episode

A, B, C = 61501, 61502, 61503
INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}
OBS = {"run_id": "TEST_001", "episode_id": "E001", "executor_claim": "SUCCESS", "reviewer_claim": "SUCCESS",
       "final_claim": "SUCCESS", "ballots": {"A": "APPROVE", "B": "APPROVE"}}


def pem(key):
    return key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption())


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate()
        self.pub = pub_bytes(self.key)

    def pinned_plan(self, **over):
        return make_plan(self.key, role_uids={"host": 0, "agent_a": A, "agent_b": B, "control": C}, **over)

    def run_episode(self, plan, peer_uid=None, control_peer_uid=None, name="host"):
        w = HostWriter(self.td / name, self.key, plan, digest(plan))
        w.write("A", "R1", INTENT, peer_uid=peer_uid)
        w.finalize(control_peer_uid=control_peer_uid)
        return self.td / name


class KeyCustody(Base):  # P1
    @unittest.skipUnless(os.geteuid() == 0, "needs root to chown")
    def test_key_file_owned_by_other_uid_rejected(self):
        kp = self.td / "k.pem"
        kp.write_bytes(pem(self.key)); kp.chmod(0o600); os.chown(kp, A, A)
        with self.assertRaisesRegex(EvidenceError, "PRIVATE_KEY_NOT_OWNED_BY_HOST"):
            read_private_key(kp)

    def test_key_in_group_or_world_writable_dir_rejected(self):
        d = self.td / "open"; d.mkdir(); d.chmod(0o777)
        kp = d / "k.pem"; kp.write_bytes(pem(self.key)); kp.chmod(0o600)
        with self.assertRaisesRegex(EvidenceError, "PRIVATE_KEY_DIR_WRITABLE_BY_OTHERS"):
            read_private_key(kp)

    def test_host_owned_key_in_private_dir_accepted(self):
        d = self.td / "priv"; d.mkdir(); d.chmod(0o700)
        kp = d / "k.pem"; kp.write_bytes(pem(self.key)); kp.chmod(0o600)
        self.assertIsInstance(read_private_key(kp), Ed25519PrivateKey)


class PeerPolicy(Base):  # P12
    def test_server_without_uid_policy_refuses_to_start(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        with self.assertRaisesRegex(EvidenceError, "PEER_UID_POLICY_REQUIRED"):
            Server(self.td / "s.sock", w, "control")

    def test_explicit_unchecked_peer_mode_is_possible_but_named(self):
        plan = make_plan(self.key)
        w = HostWriter(self.td / "h", self.key, plan, digest(plan))
        srv = Server(self.td / "s.sock", w, "control", allow_unchecked_peer=True)
        srv.server_close()


class PeerUidEvidence(Base):  # P8, P9, P11
    def test_verify_reports_pinned_isolation_when_peer_uids_match(self):
        plan = self.pinned_plan()
        root = self.run_episode(plan, peer_uid=A, control_peer_uid=C)
        proof = verify(plan, digest(plan), self.pub, root)
        self.assertEqual(proof["isolation_mode"], "ROLE_UIDS_PINNED_PEER_UIDS_MATCH")
        self.assertEqual(proof["actor_id_authenticated"], "HOST_OBSERVED_PEER_UID_MATCHES_PLAN")
        self.assertEqual((proof["peer_uid"], proof["control_peer_uid"]), (A, C))

    def test_agent_peer_uid_mismatch_rejected(self):
        plan = self.pinned_plan()
        root = self.run_episode(plan, peer_uid=B, control_peer_uid=C)
        with self.assertRaisesRegex(EvidenceError, "PEER_UID_MISMATCH"):
            verify(plan, digest(plan), self.pub, root)

    def test_control_peer_uid_mismatch_rejected(self):
        plan = self.pinned_plan()
        root = self.run_episode(plan, peer_uid=A, control_peer_uid=A)
        with self.assertRaisesRegex(EvidenceError, "PEER_UID_MISMATCH"):
            verify(plan, digest(plan), self.pub, root)

    def test_missing_peer_uid_rejected_when_roles_pinned(self):
        plan = self.pinned_plan()
        root = self.run_episode(plan, peer_uid=None, control_peer_uid=C)
        with self.assertRaisesRegex(EvidenceError, "PEER_UID_NOT_RECORDED"):
            verify(plan, digest(plan), self.pub, root)

    def test_legacy_plan_is_flagged_not_isolated(self):
        plan = make_plan(self.key)
        root = self.run_episode(plan, peer_uid=os.getuid(), control_peer_uid=os.getuid())
        proof = verify(plan, digest(plan), self.pub, root)
        self.assertEqual(proof["isolation_mode"], "NOT_ISOLATED_NO_ROLE_UIDS")
        self.assertEqual(proof["actor_id_authenticated"], "UNKNOWN")

    def test_bridge_exposes_isolation_mode_and_can_require_it(self):
        legacy = make_plan(self.key)
        root = self.run_episode(legacy, name="legacy")
        res = score_episode(legacy, digest(legacy), self.pub, root, OBS)
        self.assertEqual(res["isolation_mode"], "NOT_ISOLATED_NO_ROLE_UIDS")
        with self.assertRaisesRegex(EvidenceError, "ISOLATION_NOT_PROVEN"):
            score_episode(legacy, digest(legacy), self.pub, root, OBS, require_isolation=True)
        pinned = self.pinned_plan()
        proot = self.run_episode(pinned, peer_uid=A, control_peer_uid=C, name="pinned")
        res2 = score_episode(pinned, digest(pinned), self.pub, proot, OBS, require_isolation=True)
        self.assertEqual(res2["isolation_mode"], "ROLE_UIDS_PINNED_PEER_UIDS_MATCH")

    @unittest.skipUnless(os.geteuid() == 0, "needs root for real child UIDs")
    def test_end_to_end_kernel_peer_uids_are_recorded_and_verified(self):
        import subprocess, sys
        os.chmod(self.td, 0o755)
        plan = self.pinned_plan()
        w = HostWriter(self.td / "host", self.key, plan, digest(plan))
        socks = {}
        for name, role, actor, uid in (("a", "agent", "A", A), ("c", "control", None, C)):
            p = self.td / "ipc" / f"{name}.sock"
            srv = Server(p, w, role, actor_id=actor, allowed_uid=uid, enforce_isolation=True)
            self.addCleanup(srv.server_close)
            t = threading.Thread(target=srv.serve_forever, daemon=True); t.start(); self.addCleanup(srv.shutdown)
            socks[name] = p
        code = ("import socket,sys,json;s=socket.socket(socket.AF_UNIX);s.settimeout(3);s.connect(sys.argv[1]);"
                "s.sendall(sys.argv[2].encode()+b'\\n');print(s.recv(9000).decode())")
        def as_uid(uid, path, body):
            r = subprocess.run([sys.executable, "-c", code, str(path), json.dumps(body)], capture_output=True,
                               text=True, timeout=10, user=uid, group=uid, extra_groups=[])
            return json.loads(r.stdout)
        self.assertTrue(as_uid(A, socks["a"], {"op": "write", "request_id": "R1", "intent": INTENT})["ok"])
        self.assertTrue(as_uid(C, socks["c"], {"op": "finalize"})["ok"])
        proof = verify(plan, digest(plan), self.pub, self.td / "host")
        self.assertEqual((proof["peer_uid"], proof["control_peer_uid"]), (A, C))
        self.assertEqual(proof["isolation_mode"], "ROLE_UIDS_PINNED_PEER_UIDS_MATCH")


class UnattestedResponses(Base):  # P10
    def test_ballots_are_labelled_caller_supplied(self):
        plan = make_plan(self.key)
        res = score_episode(plan, digest(plan), self.pub, self.run_episode(plan), OBS)
        self.assertEqual(res["claims_and_ballots_provenance"], "CALLER_SUPPLIED_UNSIGNED")
        self.assertFalse(res["ballots_attested"])

    def test_scored_study_gate_fails_closed_until_a_response_ledger_exists(self):
        plan = make_plan(self.key)
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_LEDGER_NOT_IMPLEMENTED"):
            score_episode(plan, digest(plan), self.pub, self.run_episode(plan), OBS, require_attested_responses=True)


if __name__ == "__main__":
    unittest.main()
