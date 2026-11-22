import copy
import unittest

from trace import demo, digest, validate


class TestSyntheticACATTrace(unittest.TestCase):
    def setUp(self):
        self.t = demo()

    def fail_change(self, change):
        t = copy.deepcopy(self.t)
        change(t)
        with self.assertRaises(ValueError):
            validate(t)

    def test_good_fixture_is_not_certified(self):
        r = validate(self.t)
        self.assertEqual(r["status"], "SYNTHETIC_TRACE_COMPLETE_NOT_ACAT_QUALIFIED")
        self.assertFalse(r["p1_answer_matches_fictional_key"])
        self.assertTrue(r["p3_answer_matches_fictional_key"])
        self.assertFalse(r["human_benefit_verified"])
        self.assertEqual(r["authority_effect"], "NONE")

    def test_source_packet_edit(self):
        self.fail_change(lambda t: t["packet"]["sources"][0].update(text="Altered"))

    def test_cross_session_stale_sha(self):
        self.fail_change(lambda t: t["events"][2].update(packet_sha256="a" * 64))

    def test_p1_blindness(self):
        self.fail_change(lambda t: t["events"][0].update(peer_exposure=True))

    def test_role_phase_swap(self):
        self.fail_change(lambda t: t["events"][1].update(role="WITNESS"))

    def test_p2_same_controller_even_if_alias_diff(self):
        def change(t):
            t["events"][2]["controller_claim"] = "fixture-controller-grok"
            event = t["events"][2]
            event["receipt_sha256"] = digest({k: v for k, v in event.items() if k != "receipt_sha256"})
            t["witness"]["event_receipts"]["DEMO-EVENT-3"] = event["receipt_sha256"]
            t["witness"]["receipt_sha256"] = digest({k: v for k, v in t["witness"].items() if k != "receipt_sha256"})
        self.fail_change(change)

    def test_p3_wrong_actor(self):
        self.fail_change(lambda t: t["events"][3].update(principal_claim="fixture-foreign"))

    def test_missing_source(self):
        self.fail_change(lambda t: t["events"][2].update(evidence_ids=["DEMO-SRC-NOT-FOUND"]))

    def test_tampered_event(self):
        self.fail_change(lambda t: t["events"][3].update(decision="ACCEPT"))

    def test_witness_receipt_mutation(self):
        self.fail_change(lambda t: t["witness"].update(receipt_sha256="0" * 64))

    def test_witness_control_collision(self):
        self.fail_change(lambda t: t["witness"].update(controller_claim="fixture-controller-claude"))

    def test_out_of_order(self):
        self.fail_change(lambda t: t["events"][2].update(time="2026-11-22T15:01:00Z"))

    def test_unauthorized_real_world_case(self):
        self.fail_change(lambda t: t["packet"].update(source_kind="REAL"))

    def test_unknown_private_record(self):
        self.fail_change(lambda t: t.update(private_email="private@example.invalid"))

    def test_wrong_p2_challenge_can_be_rejected(self):
        t = copy.deepcopy(self.t)
        t["events"][2]["decision"] = "ACCEPT"
        event = t["events"][2]
        event["receipt_sha256"] = digest({k: v for k, v in event.items() if k != "receipt_sha256"})
        t["witness"]["event_receipts"]["DEMO-EVENT-3"] = event["receipt_sha256"]
        t["witness"]["receipt_sha256"] = digest({k: v for k, v in t["witness"].items() if k != "receipt_sha256"})
        r = validate(t)
        self.assertFalse(r["p2_challenge_agreed_with_p3"])
        self.assertTrue(r["p3_answer_matches_fictional_key"])


if __name__ == "__main__":
    unittest.main()
