"""Red-team round 2: gaps found in the signed response ledger. Written BEFORE the fixes (author-run)."""
import json
import os
import socket
import threading
import unittest
from unittest import mock

from src import service
from src.responses import parse_response, MAX_RAW
from src.writer import EvidenceError
from tests.test_response_ledger import Base, claim, ballot, A, B, C


class HostileModelText(Base):
    """The raw reply comes from a model, so it is attacker-controlled text. It must never crash the host."""

    def test_deeply_nested_json_is_unparseable_not_a_crash(self):
        raw = "[" * 20000 + "]" * 20000
        self.assertEqual(parse_response("BALLOT", raw.encode(), "OK"), ("UNKNOWN", "UNPARSEABLE"))

    def test_deeply_nested_reply_is_recorded_as_unparseable(self):
        out = self.rec("A", "BALLOT", "[" * 30000)
        self.assertEqual((out["value"], out["parse_status"]), ("UNKNOWN", "UNPARSEABLE"))

    def test_deeply_nested_object_is_unparseable(self):
        raw = '{"a":' * 5000 + "1" + "}" * 5000
        self.assertEqual(parse_response("BALLOT", raw.encode(), "OK"), ("UNKNOWN", "UNPARSEABLE"))

    def test_huge_number_literal_is_unparseable_not_a_crash(self):
        raw = ('{"ballot":' + "9" * 5000 + "}").encode()
        self.assertEqual(parse_response("BALLOT", raw, "OK"), ("UNKNOWN", "UNPARSEABLE"))


class ModelIdentityBinding(Base):
    """The ledger names the model that answered. It must be the model the frozen plan pinned for that actor."""

    def test_actor_a_must_use_the_pinned_model_a(self):
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_MODEL_NOT_PINNED"):
            self.rec("A", "BALLOT", ballot("APPROVE"), model="SYNTHETIC_B")

    def test_actor_b_must_use_the_pinned_model_b(self):
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_MODEL_NOT_PINNED"):
            self.rec("B", "BALLOT", ballot("APPROVE"), model="SYNTHETIC_A")

    def test_pinned_models_are_accepted(self):
        self.rec("A", "BALLOT", ballot("APPROVE"), rid="req_1", model="SYNTHETIC_A")
        self.rec("B", "BALLOT", ballot("REJECT"), rid="req_2", model="SYNTHETIC_B")

    def test_refusal_changes_no_state(self):
        with self.assertRaises(EvidenceError):
            self.rec("A", "BALLOT", ballot("APPROVE"), model="other")
        self.rec("A", "BALLOT", ballot("APPROVE"), model="SYNTHETIC_A")  # slot still free

    def test_off_pin_model_in_a_signed_ledger_is_rejected_by_the_verifier(self):
        # Relax ONLY the writer's rule (as a compromised host would), then check the verifier still refuses.
        with mock.patch("src.writer.pinned_model", lambda plan, actor: "off-pin-model"):
            self.rec("A", "BALLOT", ballot("APPROVE"), model="off-pin-model")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_MODEL_NOT_PINNED"):
            self.finish(write=False)


class ProviderIdReuse(Base):
    """One provider reply must not be able to fill two slots."""

    def test_same_provider_request_id_refused_for_a_second_slot(self):
        self.rec("A", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_A")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_PROVIDER_ID_REUSED"):
            self.rec("B", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_B")

    def test_distinct_ids_are_fine(self):
        self.rec("A", "BALLOT", ballot("APPROVE"), rid="req_1", model="SYNTHETIC_A")
        self.rec("B", "BALLOT", ballot("APPROVE"), rid="req_2", model="SYNTHETIC_B")

    def test_reused_id_in_a_signed_ledger_is_rejected_by_the_verifier(self):
        self.rec("A", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_A")
        self.w._provider_ids.clear()  # what a compromised host could do; the verifier must still refuse
        self.rec("B", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_B")
        with self.assertRaisesRegex(EvidenceError, "RESPONSE_PROVIDER_ID_REUSED"):
            self.finish(write=False)

    def test_refused_reuse_leaves_the_slot_free(self):
        self.rec("A", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_A")
        with self.assertRaises(EvidenceError):
            self.rec("B", "BALLOT", ballot("APPROVE"), rid="req_same", model="SYNTHETIC_B")
        self.rec("B", "BALLOT", ballot("APPROVE"), rid="req_other", model="SYNTHETIC_B")


class LargestLegalReplyFitsTheControlChannel(Base):
    """A legal MAX_RAW reply, JSON-escaped by the orchestrator, must not be refused by the line limit."""

    def test_max_raw_of_control_characters_round_trips_over_the_socket(self):
        sock = self.td / "c.sock"
        srv = service.Server(sock, self.w, "control", allowed_uid=os.getuid())
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(srv.shutdown)
        self.addCleanup(srv.server_close)
        req = {"op": "record_response", "actor_id": "A", "kind": "BALLOT", "raw_response": "\x01" * MAX_RAW,
               "transport_status": "OK", "provider_request_id": "req_big", "model_id": "SYNTHETIC_A", "attempt": 1}
        c = socket.socket(socket.AF_UNIX)
        c.settimeout(10)
        c.connect(str(sock))
        c.sendall((json.dumps(req) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = c.recv(65536)
            if not chunk:
                break
            data += chunk
        reply = json.loads(data)
        self.assertTrue(reply.get("ok") or reply.get("recorded"), reply)


if __name__ == "__main__":
    unittest.main()
