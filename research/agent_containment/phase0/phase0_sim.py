#!/usr/bin/env python3
"""HumanAIOS containment Phase 0: deterministic, standard-library-only policy model.

This is not a network sandbox, Cloudflare Worker, or intrusion reproduction.
It performs NO network I/O and has NO repository or production credentials.
"""
import copy
import hashlib
import hmac
import json
from pathlib import Path
import unittest

HERE = Path(__file__).parent
FIXTURE = json.loads((HERE / "scenario.json").read_text())
SIM_SECRET = b"fixture-only-sim-secret-not-a-production-secret"
ZERO = "0" * 64


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SimBoard:
    """Event-sequence + simulated capabilities, with no side-effect APIs."""
    def __init__(self):
        self.scenario_id = FIXTURE["scenario_id"]
        self.actors = copy.deepcopy(FIXTURE["trusted_actor_assignments"])
        self.events = []
        self.halted = False
        self.production_writes = 0
        self.production_receipts = 0
        self.real_network_calls = 0

    def _append(self, author, event_type, channel, details):
        prev = self.events[-1]["hash"] if self.events else ZERO
        seq = len(self.events) + 1
        body = {"scenario_id": self.scenario_id, "seq": seq, "author": author,
                "event_type": event_type, "channel": channel, "details": details,
                "authority_effect": "NONE", "production_compatible": False}
        raw = f"humanaios.sim.v0.1\n{prev}\n{canon(body)}".encode()
        digest = hashlib.sha256(raw).hexdigest()
        sig = hmac.new(SIM_SECRET, f"sim-only\n{digest}".encode(), hashlib.sha256).hexdigest()
        row = {**body, "prev_hash": prev, "hash": digest,
               "sim_signature": sig, "key_scope": "SIM_FIXTURE_ONLY"}
        self.events.append(row)
        return {"status": 201, "seq": seq, "hash": digest}

    def _contain(self, author, reason):
        if self.halted:
            return {"status": 423, "reason": "SIM_HALTED"}
        result = self._append("SIM_POLICY", "containment_event", "quarantine",
                              {"source": author, "reason": reason})
        return {"status": 202, "routed": "quarantine", "reason": reason, "seq": result["seq"]}

    def message(self, actor, message):
        if self.halted:
            return {"status": 423, "reason": "SIM_HALTED"}
        role = self.actors.get(actor)
        if role is None:
            return self._contain(actor, "UNREGISTERED_ACTOR")
        # Only the server-owned role map confers simulated permissions.
        if message.get("zone", 1) != 1:
            return self._contain(actor, "CLIENT_ZONE_NOT_TRUSTED")
        if message.get("target_store") == "PRODUCTION" or message.get("receipt_type") in {
            "COMMISSION_REPORTED", "CONTRACT_REPORTED", "PRODUCTION_ATTESTATION"
        }:
            return self._contain(actor, "PRODUCTION_CAPABILITY_FORBIDDEN")
        if message.get("channel") in {"package_cache", "external_dead_drop", "shadow_board"}:
            return self._contain(actor, "UNSANCTIONED_AGENT_CHANNEL")
        if message.get("kind") in {"hdf5_external_file_read", "jinja_template_execution"}:
            return self._contain(actor, "UNTRUSTED_PARSER_BEHAVIOR")
        if message.get("type") == "decision":
            if role != "SIM_OPERATOR" or message.get("action") != "SIMULATE_STEP":
                return self._contain(actor, "SIM_AUTHORITY_BOUNDARY")
        elif message.get("type") != "observation":
            return self._contain(actor, "UNSUPPORTED_EVENT_TYPE")
        return self._append(actor, message["type"], "scenario", {
            "fixture_label": str(message.get("label", ""))[:80], "trusted_role": role,
            "effect": "SIMULATED_ONLY"})

    def egress(self, actor, target):
        # No fetch(), HTTP client, socket, or external connection exists here.
        # Even 'mock' is a recorded stub result, not an I/O operation.
        if self.halted:
            return {"status": 423, "reason": "SIM_HALTED"}
        if target != "mock://fixture":
            return self._contain(actor, "EGRESS_DENIED")
        return self._append("SIM_POLICY", "mock_response", "scenario",
                            {"source": actor, "fixture": "mock://fixture"})

    def halt(self, actor):
        if actor != "operator" or self.actors.get(actor) != "SIM_OPERATOR":
            return self._contain(actor, "HALT_AUTHORITY_DENIED")
        if self.halted:
            return {"status": 200, "reason": "ALREADY_HALTED"}
        out = self._append("SIM_POLICY", "halt", "control", {"by": actor})
        self.halted = True
        return out

    def replay(self, since_seq=0):
        return copy.deepcopy([e for e in self.events if e["seq"] > since_seq])

    @staticmethod
    def verify(rows):
        prev = ZERO
        for seq, row in enumerate(rows, 1):
            body = {key: row[key] for key in (
                "scenario_id", "seq", "author", "event_type", "channel", "details",
                "authority_effect", "production_compatible")}
            if row["seq"] != seq or row["prev_hash"] != prev or row["key_scope"] != "SIM_FIXTURE_ONLY":
                return False
            digest = hashlib.sha256(f"humanaios.sim.v0.1\n{prev}\n{canon(body)}".encode()).hexdigest()
            sig = hmac.new(SIM_SECRET, f"sim-only\n{digest}".encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(digest, row["hash"]) or not hmac.compare_digest(sig, row["sim_signature"]):
                return False
            prev = digest
        return True


def trial():
    sim = SimBoard()
    results = []
    for op in FIXTURE["trial"]:
        if op["api"] == "message":
            response = sim.message(op["actor"], op["body"])
        elif op["api"] == "egress":
            response = sim.egress(op["actor"], op["target"])
        elif op["api"] == "halt":
            response = sim.halt(op["actor"])
        else:
            raise ValueError("unknown fixture api")
        results.append({"id": op["id"], "status": response["status"],
                        "reason": response.get("reason", "ACCEPTED")})
    return sim, results


class Phase0Tests(unittest.TestCase):
    def test_01_benign_observation(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","label":"synthetic opportunity"})["status"], 201)
    def test_02_forged_zone(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"decision","zone":2,"action":"SIMULATE_STEP"})["status"], 202)
    def test_03_forged_operator(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"decision","action":"SIMULATE_STEP"})["reason"], "SIM_AUTHORITY_BOUNDARY")
    def test_04_production_write_denied(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","target_store":"PRODUCTION"})["status"], 202)
    def test_05_production_receipt_denied(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","receipt_type":"COMMISSION_REPORTED"})["status"], 202)
    def test_06_shadow_board(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","channel":"package_cache"})["reason"], "UNSANCTIONED_AGENT_CHANNEL")
    def test_07_parser_file_read(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","kind":"hdf5_external_file_read"})["status"], 202)
    def test_08_parser_template_eval(self):
        s = SimBoard(); self.assertEqual(s.message("investigator", {"type":"observation","kind":"jinja_template_execution"})["status"], 202)
    def test_09_network_rejected(self):
        s = SimBoard(); self.assertEqual(s.egress("investigator", "https://example.invalid")["reason"], "EGRESS_DENIED")
        self.assertEqual(s.real_network_calls, 0)
    def test_10_unauthorized_halt(self):
        s = SimBoard(); self.assertEqual(s.halt("investigator")["reason"], "HALT_AUTHORITY_DENIED"); self.assertFalse(s.halted)
    def test_11_halt_idempotent(self):
        s = SimBoard(); self.assertEqual(s.halt("operator")["status"], 201); n = len(s.events)
        self.assertEqual(s.halt("operator")["reason"], "ALREADY_HALTED"); self.assertEqual(len(s.events), n)
        self.assertEqual(s.message("scribe", {"type":"observation"})["status"], 423)
    def test_12_chain_detects_tampering(self):
        s, _ = trial(); self.assertTrue(SimBoard.verify(s.replay()))
        tampered = s.replay(); tampered[0]["details"]["fixture_label"] = "edited"
        self.assertFalse(SimBoard.verify(tampered))
    def test_13_replay_deterministic(self):
        a, _ = trial(); b, _ = trial(); self.assertEqual(a.replay(), b.replay())
    def test_14_production_is_inaccessible(self):
        a, _ = trial(); self.assertEqual((a.production_writes, a.production_receipts, a.real_network_calls), (0, 0, 0))
    def test_15_quarantine_retained(self):
        a, _ = trial(); self.assertGreater(sum(x["event_type"]=="containment_event" for x in a.events), 0)
    def test_16_replay_cursor(self):
        a, _ = trial(); self.assertEqual(a.replay(1), a.replay()[1:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
