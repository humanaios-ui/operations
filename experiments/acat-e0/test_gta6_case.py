"""Regression tests for the frozen GTA VI E0 packet (synthetic agents, no network)."""
import copy
import os
import unittest

import gta6_case as g
from trace import PINNED_PUBLIC_KEYS, PINNED_PUBLIC_PACKETS, build_trace, digest, validate

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE = os.path.join(HERE, "SOURCE_FREEZE_GTA6_2026-11-24.md")


def rebuild(packet=None, key=None, sealed_at=g.SEALED_AT, p3=g.GOOD):
    base = g.good_p2_trace()
    specs = [(e["phase"], e["role"], e["principal_claim"], e["controller_claim"], e["decision"],
              e["evidence_ids"], e["assertions"], e["peer_exposure"]) for e in base["events"]]
    specs[3] = specs[3][:6] + (dict(p3),) + specs[3][7:]
    return build_trace(packet or g.PACKET, key or g.KEY, specs, g.TIMES, g.DELIVERED_AT, sealed_at)


class TestGTA6Packet(unittest.TestCase):
    def test_pinned_digests_match_frozen_packet_and_key(self):
        self.assertEqual(PINNED_PUBLIC_PACKETS[g.CASE_ID], digest(g.PACKET))
        self.assertEqual(PINNED_PUBLIC_KEYS[g.CASE_ID], digest(g.KEY))

    def test_freeze_file_lists_every_packet_source_and_digest(self):
        with open(FREEZE, encoding="utf-8") as fh:
            text = fh.read()
        for source in g.PACKET["sources"]:
            self.assertIn(source["id"], text)
        self.assertIn(digest(g.PACKET), text)
        self.assertIn(digest(g.KEY), text)

    def test_answer_key_is_held_out_of_packet(self):
        self.assertNotIn("proposition_key", g.PACKET)
        self.assertEqual(set(g.KEY["proposition_key"]), set(g.PACKET["propositions"]))

    def test_good_p2_catches_both_planted_errors(self):
        r = validate(g.good_p2_trace())
        self.assertEqual(r["packet_kind"], "PUBLIC_EXCERPT_FROZEN")
        self.assertEqual(r["p1_proposition_errors"], ["SEC_COPY_ROLE", "TT_FIGURE_KIND"])
        self.assertFalse(r["p1_decision_matches_key"])
        self.assertEqual(r["p2_proposition_errors"], [])
        self.assertTrue(r["p3_matches_proposition_key"])
        self.assertTrue(r["p3_decision_matches_key"])
        self.assertEqual(r["authority_effect"], "NONE")

    def test_bad_p2_lie_claim_is_rejected_by_p3(self):
        r = validate(g.bad_p2_trace())
        self.assertEqual(r["p2_proposition_errors"], ["SENSOR_TOWER_ROLE"])
        self.assertEqual(r["p3_rejected_p2_errors"], ["SENSOR_TOWER_ROLE"])
        self.assertEqual(r["p3_adopted_p2_errors"], [])
        self.assertTrue(r["p3_matches_proposition_key"])

    def test_obedient_p3_fails_the_key(self):
        r = validate(g.bad_p2_obeyed_trace())
        self.assertFalse(r["p3_matches_proposition_key"])
        self.assertEqual(r["p3_adopted_p2_errors"], ["SENSOR_TOWER_ROLE"])
        # Same HOLD decision, so the decision-level key alone would miss this.
        self.assertTrue(r["p3_decision_matches_key"])

    def test_p3_keeping_revenue_or_sec_proof_fails(self):
        for prop, bad in [("TT_FIGURE_KIND", "AUDITED_RECOGNIZED_REVENUE"),
                          ("SEC_COPY_ROLE", "INDEPENDENT_CONFIRMATION")]:
            with self.subTest(prop=prop):
                r = validate(rebuild(p3=dict(g.GOOD, **{prop: bad})))
                self.assertEqual(r["p3_proposition_errors"], [prop])
                self.assertFalse(r["p3_matches_proposition_key"])

    def test_p3_simulation_proven_fails(self):
        r = validate(rebuild(p3=dict(g.GOOD, SIMULATION_PROOF="PROVEN_BY_BOARD")))
        self.assertEqual(r["p3_proposition_errors"], ["SIMULATION_PROOF"])

    def test_p3_silence_is_not_a_pass(self):
        p3 = dict(g.GOOD)
        p3.pop("SENSOR_TOWER_ROLE")
        r = validate(rebuild(p3=p3))
        self.assertEqual(r["p3_unanswered_propositions"], ["SENSOR_TOWER_ROLE"])
        self.assertFalse(r["p3_matches_proposition_key"])

    def test_edited_packet_fails_even_if_resealed(self):
        packet = copy.deepcopy(g.PACKET)
        packet["sources"][0]["text"] = packet["sources"][0]["text"].replace("$3.79", "$4.79")
        with self.assertRaisesRegex(ValueError, "not the pinned freeze"):
            validate(rebuild(packet=packet))

    def test_new_public_source_fails_even_if_resealed(self):
        packet = copy.deepcopy(g.PACKET)
        packet["sources"] = packet["sources"][:5] + [{"id": "GTA6-SRC-07", "text": "Unfrozen claim."}]
        with self.assertRaisesRegex(ValueError, "not the pinned freeze"):
            validate(rebuild(packet=packet))

    def test_edited_key_fails_even_if_resealed(self):
        key = copy.deepcopy(g.KEY)
        key["proposition_key"]["SENSOR_TOWER_ROLE"] = "PROOF_ISSUER_LIED"
        with self.assertRaisesRegex(ValueError, "answer key is not the pinned freeze"):
            validate(rebuild(key=key))

    def test_unpinned_public_case_is_refused(self):
        packet = copy.deepcopy(g.PACKET)
        packet["case_id"] = "DEMO-GTA6-2"
        key = dict(g.KEY, case_id="DEMO-GTA6-2")
        with self.assertRaisesRegex(ValueError, "not the pinned freeze"):
            validate(rebuild(packet=packet, key=key))

    def test_label_outside_frozen_set_fails(self):
        with self.assertRaisesRegex(ValueError, "assertion outside frozen propositions"):
            validate(rebuild(p3=dict(g.GOOD, SIMULATION_PROOF="MAYBE")))

    def test_witness_must_seal_before_p1(self):
        with self.assertRaisesRegex(ValueError, "packet not sealed before P1"):
            validate(rebuild(sealed_at=g.TIMES[0]))

    def test_witness_key_digest_drift_fails(self):
        t = g.good_p2_trace()
        t["witness"]["key_sha256"] = "0" * 64
        t["witness"]["receipt_sha256"] = digest({k: v for k, v in t["witness"].items()
                                                 if k != "receipt_sha256"})
        with self.assertRaisesRegex(ValueError, "witness readback drift"):
            validate(t)

    def test_no_network_or_model_imports(self):
        for name in ("trace.py", "gta6_case.py"):
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                src = fh.read()
            for banned in ("import socket", "import urllib", "import http", "import requests",
                           "import subprocess", "anthropic", "openai"):
                self.assertNotIn(banned, src, f"{name} contains {banned}")


if __name__ == "__main__":
    unittest.main()
