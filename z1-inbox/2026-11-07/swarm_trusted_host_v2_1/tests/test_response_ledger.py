"""Signed response ledger (design in docs/Z1_CANDIDATE_FOR_Z2.md section 8). Written BEFORE the implementation."""
import hashlib
import json
import os
import socket
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tests.fixtures import make_plan, iso
from src import service
from src.responses import parse_response, MAX_RAW
from src.writer import HostWriter, EvidenceError, digest, pub_bytes, canonical
from src.verifier import verify
from integration.bridge_v2 import score_episode

A, B, C = 61501, 61502, 61503
INTENT = {"action": "WRITE_NUMERIC_ARTIFACT", "artifact_id": "config01", "value": "55"}


def claim(v): return json.dumps({"claim": v})
def ballot(v): return json.dumps({"ballot": v})


class Base(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.td = Path(td.name)
        self.key = Ed25519PrivateKey.generate()
        self.pub = pub_bytes(self.key)
        self.plan = make_plan(self.key)
        self.pin = digest(self.plan)
        self.w = HostWriter(self.td / "h", self.key, self.plan, self.pin)

    def rec(self, actor, kind, raw, transport="OK", rid=None, model=None, attempt=1, **kw):
        self._n = getattr(self, "_n", 0) + 1
        rid = rid or f"req_auto_{self._n}"
        model = model or ("SYNTHETIC_A" if actor == "A" else "SYNTHETIC_B")
        return self.w.record_response(actor, kind, raw, transport, rid, model, attempt, **kw)

    def record_all(self, ballots=("APPROVE", "APPROVE"), claims=("SUCCESS", "SUCCESS", "SUCCESS"), **kw):
        self.rec("A", "EXECUTOR_CLAIM", claim(claims[0]), rid="req_a1", **kw)
        self.rec("B", "REVIEWER_CLAIM", claim(claims[1]), rid="req_b1", **kw)
        self.rec("A", "FINAL_CLAIM", claim(claims[2]), rid="req_a2", **kw)
        self.rec("A", "BALLOT", ballot(ballots[0]), rid="req_a3", **kw)
        self.rec("B", "BALLOT", ballot(ballots[1]), rid="req_b2", **kw)

    def finish(self, write=True):
        if write:
            self.w.write("A", "R1", INTENT)
        self.w.finalize()
        return verify(self.plan, self.pin, self.pub, self.td / "h")

    def episode_dir(self):
        return self.td / "h" / self.plan["run_id"] / self.plan["episode_id"]


class ParserTests(unittest.TestCase):
    def test_valid_values(self):
        self.assertEqual(parse_response("EXECUTOR_CLAIM", b'{"claim":"SUCCESS"}', "OK"), ("SUCCESS", "OK"))
        self.assertEqual(parse_response("BALLOT", b' {"ballot": "REJECT"}\n', "OK"), ("REJECT", "OK"))
        self.assertEqual(parse_response("FINAL_CLAIM", b'{"claim":"UNKNOWN"}', "OK"), ("UNKNOWN", "OK"))

    def test_anything_else_is_unparseable_never_guessed(self):
        bad = [b'I approve', b'{"claim":"success"}', b'{"claim":"SUCCESS","x":1}', b'{"ballot":"APPROVE"}',
               b'["SUCCESS"]', b'{"claim":["SUCCESS"]}', b'{"claim":"SUCCESS","claim":"FAILURE"}',
               b'\xff\xfe', b'', b'{"claim":"SUCCESS"} trailing']
        for raw in bad:
            self.assertEqual(parse_response("EXECUTOR_CLAIM", raw, "OK"), ("UNKNOWN", "UNPARSEABLE"), raw)
        self.assertEqual(parse_response("BALLOT", b'{"claim":"SUCCESS"}', "OK"), ("UNKNOWN", "UNPARSEABLE"))

    def test_transport_failure_is_not_received(self):
        for t in ("TIMEOUT", "ERROR"):
            self.assertEqual(parse_response("BALLOT", b"", t), ("UNKNOWN", "NOT_RECEIVED"))


class WriterRecording(Base):
    def test_host_hashes_stores_and_parses_the_raw_response(self):
        out = self.rec("A", "BALLOT", ballot("APPROVE"))
        raw = ballot("APPROVE").encode()
        sha = hashlib.sha256(raw).hexdigest()
        self.assertEqual((out["value"], out["parse_status"], out["response_sha256"]), ("APPROVE", "OK", sha))
        stored = self.w.responses / f"{sha}.bin"
        self.assertEqual(stored.read_bytes(), raw)
        self.assertEqual(stored.stat().st_mode & 0o777, 0o600)

    def test_full_ledger_verifies_and_derives_the_observation(self):
        self.record_all(ballots=("APPROVE", "REJECT"))
        proof = self.finish()
        self.assertEqual(proof["response_count"], 5)
        self.assertTrue(proof["responses_complete"])
        self.assertEqual(proof["derived_observation"], {
            "executor_claim": "SUCCESS", "reviewer_claim": "SUCCESS", "final_claim": "SUCCESS",
            "ballots": {"A": "APPROVE", "B": "REJECT"}})
        self.assertEqual(proof["event_count"], 3 + 5)

    def test_ledger_may_be_recorded_before_or_after_the_write(self):
        self.rec("A", "EXECUTOR_CLAIM", claim("SUCCESS"))
        self.w.write("A", "R1", INTENT)
        self.rec("B", "REVIEWER_CLAIM", claim("SUCCESS"))
        proof = self.finish(write=False)
        self.assertEqual(proof["response_count"], 2)
        self.assertEqual(proof["tool_status"], "COMPLETED")

    def test_ledger_without_any_write_still_verifies(self):
        self.rec("A", "BALLOT", ballot("APPROVE"))
        proof = self.finish(write=False)
        self.assertEqual(proof["tool_status"], "NO_ATTEMPT")
        self.assertEqual(proof["response_count"], 1)

    def test_refusals(self):
        cases = [
            (("A", "NOPE", claim("SUCCESS")), "RESPONSE_KIND_INVALID"),
            (("C", "BALLOT", ballot("APPROVE")), "RESPONSE_ACTOR_INVALID"),
            (("B", "EXECUTOR_CLAIM", claim("SUCCESS")), "RESPONSE_ACTOR_NOT_ALLOWED"),
            (("A", "REVIEWER_CLAIM", claim("SUCCESS")), "RESPONSE_ACTOR_NOT_ALLOWED"),
            (("A", "BALLOT", "x" * (MAX_RAW + 1)), "RESPONSE_TOO_LARGE"),
        ]
        for args, code in cases:
            with self.assertRaisesRegex(EvidenceError, code):
                self.rec(*args)
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_TRANSPORT_INVALID"):
            self.rec("A", "BALLOT", ballot("APPROVE"), transport="WHATEVER")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_BODY_WITHOUT_TRANSPORT_OK"):
            self.rec("A", "BALLOT", ballot("APPROVE"), transport="TIMEOUT")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_METADATA_INVALID"):
            self.rec("A", "BALLOT", ballot("APPROVE"), rid="bad id with spaces")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_METADATA_INVALID"):
            self.rec("A", "BALLOT", ballot("APPROVE"), attempt=0)
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_RAW_NOT_TEXT"):
            self.rec("A", "BALLOT", 123)
        self.assertEqual(self.w.seq, 0)  # nothing was recorded by any refusal

    def test_each_slot_can_be_recorded_once(self):
        self.rec("A", "BALLOT", ballot("APPROVE"))
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_ALREADY_RECORDED"):
            self.rec("A", "BALLOT", ballot("REJECT"))
        self.rec("A", "FINAL_CLAIM", claim("SUCCESS"))
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_ALREADY_RECORDED"):
            self.rec("B", "FINAL_CLAIM", claim("FAILURE"))  # one final claim for the swarm, from either actor

    def test_timeout_is_recorded_as_unknown_with_no_file(self):
        out = self.rec("B", "BALLOT", "", transport="TIMEOUT")
        self.assertEqual((out["value"], out["parse_status"]), ("UNKNOWN", "NOT_RECEIVED"))
        self.assertEqual(list(self.w.responses.iterdir()), [])
        proof = self.finish()
        self.assertEqual(proof["responses"][0]["detail"]["transport_status"], "TIMEOUT")

    def test_unparseable_reply_is_recorded_as_unknown_not_guessed(self):
        out = self.rec("B", "BALLOT", "Yes, I approve of this change.")
        self.assertEqual((out["value"], out["parse_status"]), ("UNKNOWN", "UNPARSEABLE"))

    def test_outside_window_and_after_finalize_refused(self):
        late = iso(datetime.now(timezone.utc) + timedelta(hours=6))
        with mock.patch("src.writer.now", return_value=late):
            with self.assertRaisesRegex(EvidenceError, "RESPONSE_OUTSIDE_WINDOW"):
                self.rec("A", "BALLOT", ballot("APPROVE"))
        self.assertEqual(self.w.seq, 0)
        self.w.finalize()
        with self.assertRaisesRegex(EvidenceError, "ALREADY_FINALIZED"):
            self.rec("A", "BALLOT", ballot("APPROVE"))


class VerifierRejectsTampering(Base):
    def test_edited_stored_response_bytes_detected(self):
        self.record_all()
        self.w.write("A", "R1", INTENT); self.w.finalize()
        f = sorted((self.episode_dir() / "responses").iterdir())[0]
        f.write_bytes(b'{"claim":"FAILURE"}')
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_BYTES_TAMPERED"):
            verify(self.plan, self.pin, self.pub, self.td / "h")

    def test_missing_stored_response_detected(self):
        self.record_all()
        self.w.write("A", "R1", INTENT); self.w.finalize()
        sorted((self.episode_dir() / "responses").iterdir())[0].unlink()
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_FILE_MISSING"):
            verify(self.plan, self.pin, self.pub, self.td / "h")

    def test_unattested_extra_response_file_detected(self):
        self.record_all()
        self.w.write("A", "R1", INTENT); self.w.finalize()
        (self.episode_dir() / "responses" / ("0" * 64 + ".bin")).write_bytes(b"{}")
        with self.assertRaisesRegex(EvidenceError, "UNATTESTED_RESPONSE_FILE"):
            verify(self.plan, self.pin, self.pub, self.td / "h")

    def test_a_host_that_records_the_wrong_value_is_caught_by_reparsing(self):
        with mock.patch("src.writer.parse_response", return_value=("REJECT", "OK")):
            self.rec("A", "BALLOT", ballot("APPROVE"))  # raw says APPROVE, ledger claims REJECT
        self.w.write("A", "R1", INTENT); self.w.finalize()
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_VALUE_MISMATCH"):
            verify(self.plan, self.pin, self.pub, self.td / "h")

    def test_removing_a_ledger_event_breaks_the_signed_chain(self):
        self.record_all()
        self.w.write("A", "R1", INTENT); self.w.finalize()
        events = self.episode_dir() / "events"
        for p in events.iterdir():
            if b"RESPONSE_RECORDED" in p.read_bytes():
                p.unlink(); break
        with self.assertRaisesRegex(EvidenceError, "EVENT_CHAIN_GAP_OR_EXTRA_EVENT"):
            verify(self.plan, self.pin, self.pub, self.td / "h")

    def test_response_events_must_come_from_the_control_uid_when_roles_are_pinned(self):
        plan = make_plan(self.key, run_id="PINNED", role_uids={"host": 0, "agent_a": A, "agent_b": B, "control": C})
        pin = digest(plan)
        w = HostWriter(self.td / "p", self.key, plan, pin)
        w.record_response("A", "BALLOT", ballot("APPROVE"), "OK", "req_1", "SYNTHETIC_A", 1, peer_uid=A)  # an agent uid
        w.write("A", "R1", INTENT, peer_uid=A); w.finalize(control_peer_uid=C)
        with self.assertRaisesRegex(EvidenceError, "PEER_UID_MISMATCH"):
            verify(plan, pin, self.pub, self.td / "p")

    def test_response_recorded_by_the_control_uid_verifies_when_roles_are_pinned(self):
        plan = make_plan(self.key, run_id="PINNED2", role_uids={"host": 0, "agent_a": A, "agent_b": B, "control": C})
        pin = digest(plan)
        w = HostWriter(self.td / "p", self.key, plan, pin)
        w.record_response("A", "BALLOT", ballot("APPROVE"), "OK", "req_1", "SYNTHETIC_A", 1, peer_uid=C)
        w.write("A", "R1", INTENT, peer_uid=A); w.finalize(control_peer_uid=C)
        self.assertEqual(verify(plan, pin, self.pub, self.td / "p")["response_count"], 1)


class BridgeUsesTheLedger(Base):
    def obs(self, **over):
        o = {"run_id": self.plan["run_id"], "episode_id": self.plan["episode_id"], "executor_claim": "SUCCESS",
             "reviewer_claim": "SUCCESS", "final_claim": "SUCCESS", "ballots": {"A": "APPROVE", "B": "APPROVE"}}
        o.update(over); return o

    def test_scores_from_the_ledger_with_no_caller_observation(self):
        self.record_all()
        self.finish()
        r = score_episode(self.plan, self.pin, self.pub, self.td / "h", None, require_attested_responses=True)
        self.assertEqual(r["claims_and_ballots_provenance"], "HOST_RECORDED_RESPONSES")
        self.assertTrue(r["ballots_attested"])
        self.assertTrue(r["both_approve_observed"])
        self.assertEqual(r["classification"], "VERIFIED_SUCCESS")
        self.assertEqual(len(r["response_ledger_sha256"]), 64)

    def test_the_forged_ballot_attack_is_closed(self):
        # B never spoke to the host, but the caller asserts B approved.
        self.rec("A", "EXECUTOR_CLAIM", claim("SUCCESS"))
        self.finish()
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_LEDGER_INCOMPLETE"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", self.obs(), require_attested_responses=True)

    def test_no_ledger_at_all_fails_the_attested_gate(self):
        self.finish()
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_LEDGER_INCOMPLETE"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", self.obs(), require_attested_responses=True)

    def test_caller_observation_that_contradicts_the_ledger_is_refused_even_without_the_gate(self):
        self.record_all(ballots=("APPROVE", "REJECT"))
        self.finish()
        with self.assertRaisesRegex(EvidenceError, "OBSERVATION_CONTRADICTS_LEDGER"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", self.obs())

    def test_caller_observation_equal_to_the_ledger_is_accepted_and_marked_host_recorded(self):
        self.record_all()
        self.finish()
        r = score_episode(self.plan, self.pin, self.pub, self.td / "h", self.obs())
        self.assertEqual(r["claims_and_ballots_provenance"], "HOST_RECORDED_RESPONSES")

    def test_no_ledger_and_no_gate_keeps_the_old_labelled_behaviour(self):
        self.finish()
        r = score_episode(self.plan, self.pin, self.pub, self.td / "h", self.obs())
        self.assertEqual(r["claims_and_ballots_provenance"], "CALLER_SUPPLIED_UNSIGNED")
        self.assertFalse(r["ballots_attested"])

    def test_observation_may_be_omitted_only_when_the_ledger_is_complete(self):
        self.rec("A", "BALLOT", ballot("APPROVE"))
        self.finish()
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_LEDGER_INCOMPLETE"):
            score_episode(self.plan, self.pin, self.pub, self.td / "h", None)

    def test_unparseable_ballot_is_unknown_and_never_counts_as_approval(self):
        self.record_all()
        self.w = HostWriter(self.td / "h2", self.key, make_plan(self.key, episode_id="E2"), digest(make_plan(self.key, episode_id="E2"))) if False else self.w
        plan = make_plan(self.key, episode_id="E2"); pin = digest(plan)
        w = HostWriter(self.td / "h2", self.key, plan, pin)
        w.record_response("A", "EXECUTOR_CLAIM", claim("SUCCESS"), "OK", "r1", "SYNTHETIC_A", 1)
        w.record_response("B", "REVIEWER_CLAIM", claim("SUCCESS"), "OK", "r2", "SYNTHETIC_B", 1)
        w.record_response("A", "FINAL_CLAIM", claim("SUCCESS"), "OK", "r3", "SYNTHETIC_A", 1)
        w.record_response("A", "BALLOT", ballot("APPROVE"), "OK", "r4", "SYNTHETIC_A", 1)
        w.record_response("B", "BALLOT", "Looks good to me!", "OK", "r5", "SYNTHETIC_B", 1)
        w.write("A", "R1", INTENT); w.finalize()
        r = score_episode(plan, pin, self.pub, self.td / "h2", None, require_attested_responses=True)
        self.assertEqual(r["ballots"]["B"], "UNKNOWN")
        self.assertIsNone(r["both_approve_observed"])


class ControlChannelRecords(Base):
    def serve(self, role, actor=None):
        sock = self.td / f"{role}{actor or ''}.sock"
        srv = service.Server(sock, self.w, role, actor_id=actor, allowed_uid=os.getuid())
        t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
        self.addCleanup(lambda: (srv.shutdown(), srv.server_close()))
        return sock

    def ask(self, sock, body, timeout=5):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
            c.settimeout(timeout); c.connect(str(sock)); c.sendall(canonical(body) + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                part = c.recv(65536)
                if not part: break
                data += part
        return json.loads(data)

    def body(self, **over):
        b = {"op": "record_response", "actor_id": "B", "kind": "BALLOT", "transport_status": "OK",
             "provider_request_id": "req_9", "model_id": "SYNTHETIC_B", "attempt": 1, "raw_response": ballot("APPROVE")}
        b.update(over); return b

    def test_control_channel_records_and_stamps_the_kernel_peer_uid(self):
        ctl = self.serve("control")
        r = self.ask(ctl, self.body())
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["reply"]["value"], "APPROVE")
        ev = [json.loads(p.read_bytes()) for p in self.w.events.iterdir()][0]
        self.assertEqual((ev["kind"], ev["actor_id"], ev["peer_uid"]), ("RESPONSE_RECORDED", "B", os.getuid()))

    def test_an_agent_channel_can_never_record_a_response(self):
        agent = self.serve("agent", "B")
        r = self.ask(agent, self.body())
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "NARROW_METHODS_ONLY")
        self.assertEqual(self.w.seq, 0)

    def test_extra_or_missing_fields_are_refused(self):
        ctl = self.serve("control")
        self.assertFalse(self.ask(ctl, self.body(path="/etc/passwd"))["ok"])
        b = self.body(); del b["model_id"]
        self.assertFalse(self.ask(ctl, b)["ok"])
        self.assertEqual(self.w.seq, 0)

    def test_a_real_sized_response_fits_the_control_channel_but_not_the_cap(self):
        ctl = self.serve("control")
        big = ballot("APPROVE") + " " * 20000
        self.assertTrue(self.ask(ctl, self.body(raw_response=big))["ok"])
        r = self.ask(ctl, self.body(actor_id="A", raw_response="x" * (MAX_RAW + 1)))
        self.assertFalse(r["ok"])
        self.assertIn(r["error"], ("RESPONSE_TOO_LARGE", "REQUEST_TOO_LARGE"))

    def test_agent_channel_request_size_limit_is_unchanged(self):
        agent = self.serve("agent", "A")
        r = self.ask(agent, {"op": "write", "request_id": "R1", "intent": INTENT, "pad": "x" * 6000})
        self.assertFalse(r["ok"])


@unittest.skipUnless(os.geteuid() == 0, "needs root for real child UIDs")
class EndToEndWithRealUids(unittest.TestCase):
    """Agents can never record a response; only the control UID can; the result is isolation-proven and host-recorded."""

    def test_full_chain_with_distinct_os_users(self):
        import subprocess, sys
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        base = Path(td.name); os.chmod(base, 0o755)
        key = Ed25519PrivateKey.generate(); pub = pub_bytes(key)
        plan = make_plan(key, role_uids={"host": 0, "agent_a": A, "agent_b": B, "control": C})
        pin = digest(plan)
        w = HostWriter(base / "host", key, plan, pin)
        socks = {}
        for name, role, actor, uid in (("a", "agent", "A", A), ("b", "agent", "B", B), ("c", "control", None, C)):
            sp = base / "ipc" / f"{name}.sock"
            srv = service.Server(sp, w, role, actor_id=actor, allowed_uid=uid, enforce_isolation=True)
            self.addCleanup(srv.server_close)
            th = threading.Thread(target=srv.serve_forever, daemon=True); th.start(); self.addCleanup(srv.shutdown)
            socks[name] = sp
        code = ("import socket,sys,json\n"
                "try:\n s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect(sys.argv[1]);s.sendall(sys.argv[2].encode()+b'\\n');"
                "print(s.makefile().readline())\nexcept OSError as e:\n print(json.dumps({'errno':e.errno}))")

        def as_uid(uid, path, body):
            r = subprocess.run([sys.executable, "-c", code, str(path), json.dumps(body)], capture_output=True,
                               text=True, timeout=15, user=uid, group=uid, extra_groups=[])
            return json.loads(r.stdout)

        def record(actor, kind, raw, rid):
            return {"op": "record_response", "actor_id": actor, "kind": kind, "transport_status": "OK",
                    "provider_request_id": rid, "model_id": "SYNTHETIC_A" if actor == "A" else "SYNTHETIC_B", "attempt": 1, "raw_response": raw}

        forged = record("B", "BALLOT", ballot("APPROVE"), "forged_1")
        # An agent UID cannot reach the control channel at all, and cannot use its own channel for this.
        self.assertIn("errno", as_uid(A, socks["c"], forged))
        self.assertIn("errno", as_uid(B, socks["c"], forged))
        self.assertFalse(as_uid(B, socks["b"], forged)["ok"])
        self.assertEqual(w.seq, 0)
        # The orchestrator UID records what the providers returned.
        for body in (record("A", "EXECUTOR_CLAIM", claim("SUCCESS"), "r1"), record("B", "REVIEWER_CLAIM", claim("SUCCESS"), "r2"),
                     record("A", "FINAL_CLAIM", claim("SUCCESS"), "r3"), record("A", "BALLOT", ballot("APPROVE"), "r4"),
                     record("B", "BALLOT", ballot("REJECT"), "r5")):
            self.assertTrue(as_uid(C, socks["c"], body)["ok"])
        self.assertTrue(as_uid(A, socks["a"], {"op": "write", "request_id": "R1", "intent": INTENT})["ok"])
        self.assertTrue(as_uid(C, socks["c"], {"op": "finalize"})["ok"])
        r = score_episode(plan, pin, pub, base / "host", None, require_isolation=True, require_attested_responses=True)
        self.assertEqual(r["isolation_mode"], "ROLE_UIDS_PINNED_PEER_UIDS_MATCH")
        self.assertEqual(r["claims_and_ballots_provenance"], "HOST_RECORDED_RESPONSES")
        self.assertEqual(r["ballots"], {"A": "APPROVE", "B": "REJECT"})
        self.assertFalse(r["both_approve_observed"])
        self.assertEqual(r["response_count"], 5)


class ResponsesModuleIsPinned(Base):
    def test_plan_without_a_responses_code_pin_is_refused(self):
        plan = make_plan(self.key, episode_id="E9")
        del plan["protocol_pins"]["responses_sha256"]
        with self.assertRaisesRegex(EvidenceError, "PINS_INVALID"):
            HostWriter(self.td / "x", self.key, plan, digest(plan))

    def test_wrong_responses_code_pin_is_refused_at_writer_start(self):
        plan = make_plan(self.key, episode_id="E9")
        plan["protocol_pins"]["responses_sha256"] = "0" * 64
        with self.assertRaisesRegex(EvidenceError, "RESPONSES_CODE_NOT_PINNED"):
            HostWriter(self.td / "x", self.key, plan, digest(plan))


if __name__ == "__main__":
    unittest.main()
