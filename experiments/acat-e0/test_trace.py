import copy
import unittest

from trace import demo, digest, make_challenge_delivery, validate


class TestSyntheticACATTrace(unittest.TestCase):
    def setUp(self):
        self.t = demo()

    def fail_change(self, change):
        t = copy.deepcopy(self.t)
        change(t)
        with self.assertRaises(ValueError):
            validate(t)

    @staticmethod
    def reseal_witness(t):
        witness = t["witness"]
        witness["receipt_sha256"] = digest({
            k: v for k, v in witness.items() if k != "receipt_sha256"
        })

    @classmethod
    def reseal_event(cls, t, index):
        event = t["events"][index]
        event["receipt_sha256"] = digest({
            k: v for k, v in event.items() if k != "receipt_sha256"
        })
        t["witness"]["event_receipts"][event["id"]] = event["receipt_sha256"]
        cls.reseal_witness(t)

    @classmethod
    def reseal_delivery(cls, t):
        p1 = t["events"][0]
        p3 = t["events"][3]
        old = p3["challenge_delivery"]
        p3["challenge_delivery"] = make_challenge_delivery(
            t["events"][2], p1["principal_claim"], p1["controller_claim"],
            old["delivered_at"])
        cls.reseal_event(t, 3)

    @classmethod
    def reseal_modified_delivery(cls, t):
        delivery = t["events"][3]["challenge_delivery"]
        delivery["receipt_sha256"] = digest({
            k: v for k, v in delivery.items() if k != "receipt_sha256"
        })
        cls.reseal_event(t, 3)

    def test_good_fixture_is_not_certified(self):
        r = validate(self.t)
        self.assertEqual(r["status"], "SYNTHETIC_TRACE_COMPLETE_NOT_ACAT_QUALIFIED")
        self.assertFalse(r["p1_decision_matches_key"])
        self.assertTrue(r["p3_decision_matches_key"])
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
        t = copy.deepcopy(self.t)
        t["events"][2]["controller_claim"] = "fixture-controller-grok"
        self.reseal_event(t, 2)
        self.reseal_delivery(t)
        with self.assertRaisesRegex(ValueError, "same effective controller claimed"):
            validate(t)

    def test_p3_wrong_actor(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["principal_claim"] = "fixture-foreign"
        self.reseal_event(t, 3)
        with self.assertRaisesRegex(ValueError, "P3 must match P1"):
            validate(t)

    def test_missing_source(self):
        self.fail_change(lambda t: t["events"][2].update(evidence_ids=["DEMO-SRC-NOT-FOUND"]))

    def test_tampered_event(self):
        self.fail_change(lambda t: t["events"][3].update(decision="ACCEPT"))

    def test_witness_receipt_mutation(self):
        self.fail_change(lambda t: t["witness"].update(receipt_sha256="0" * 64))

    def test_witness_control_collision(self):
        self.fail_change(lambda t: t["witness"].update(controller_claim="fixture-controller-claude"))

    def test_out_of_order(self):
        t = copy.deepcopy(self.t)
        t["events"][2]["time"] = "2026-11-22T15:01:00Z"
        self.reseal_event(t, 2)
        self.reseal_delivery(t)
        with self.assertRaisesRegex(ValueError, "replayed or out-of-order phase"):
            validate(t)

    def test_unauthorized_real_world_case(self):
        self.fail_change(lambda t: t["packet"].update(source_kind="REAL"))

    def test_fictional_packet_cannot_claim_public_freeze(self):
        self.fail_change(lambda t: t["packet"].update(source_kind="PUBLIC_EXCERPT_FROZEN"))

    def test_answer_key_edit_fails(self):
        self.fail_change(lambda t: t["key"].update(case_id="DEMO-OTHER"))

    def test_assertion_without_frozen_proposition_fails(self):
        t = copy.deepcopy(self.t)
        t["events"][0]["assertions"] = {"UNFROZEN": "YES"}
        self.reseal_event(t, 0)
        self.reseal_delivery(t)
        with self.assertRaisesRegex(ValueError, "assertion outside frozen propositions"):
            validate(t)

    def test_fallback_fixture_has_no_proposition_key(self):
        self.assertIsNone(validate(self.t)["p3_matches_proposition_key"])

    def test_unknown_private_record(self):
        self.fail_change(lambda t: t.update(private_email="private@example.invalid"))

    def test_wrong_p2_challenge_can_be_rejected(self):
        t = copy.deepcopy(self.t)
        t["events"][2]["decision"] = "ACCEPT"
        self.reseal_event(t, 2)
        self.reseal_delivery(t)
        r = validate(t)
        self.assertFalse(r["p2_challenge_agreed_with_p3"])
        self.assertTrue(r["p3_decision_matches_key"])

    def test_p3_no_challenge_exposure_fails_even_if_resealed(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["peer_exposure"] = False
        self.reseal_event(t, 3)
        with self.assertRaisesRegex(ValueError, "P3 must disclose challenge exposure"):
            validate(t)

    def test_p3_missing_delivery_fails(self):
        t = copy.deepcopy(self.t)
        t["events"][3].pop("challenge_delivery")
        self.reseal_event(t, 3)
        with self.assertRaisesRegex(ValueError, "event contract mismatch"):
            validate(t)

    def test_p3_wrong_challenge_receipt_fails_after_reseal(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["challenge_delivery"]["p2_receipt_sha256"] = "0" * 64
        self.reseal_modified_delivery(t)
        with self.assertRaisesRegex(ValueError, "not bound to the exact P2"):
            validate(t)

    def test_p3_wrong_challenge_recipient_fails_after_reseal(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["challenge_delivery"]["recipient_controller_claim"] = "fixture-other-controller"
        self.reseal_modified_delivery(t)
        with self.assertRaisesRegex(ValueError, "recipient does not match"):
            validate(t)

    def test_p3_challenge_delivered_before_p2_fails_after_reseal(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["challenge_delivery"]["delivered_at"] = "2026-11-22T15:03:00Z"
        self.reseal_modified_delivery(t)
        with self.assertRaisesRegex(ValueError, "not before P3"):
            validate(t)

    def test_p3_challenge_delivered_after_p3_fails_after_reseal(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["challenge_delivery"]["delivered_at"] = "2026-11-22T15:09:00Z"
        self.reseal_modified_delivery(t)
        with self.assertRaisesRegex(ValueError, "not before P3"):
            validate(t)

    def test_p3_challenge_receipt_tamper_without_reseal_fails(self):
        t = copy.deepcopy(self.t)
        t["events"][3]["challenge_delivery"]["receipt_sha256"] = "0" * 64
        self.reseal_event(t, 3)
        with self.assertRaisesRegex(ValueError, "delivery receipt mismatch"):
            validate(t)

    def test_witness_missing_or_malformed_identity_fails_even_if_resealed(self):
        for field, value in [
            ("controller_claim", None),
            ("principal_claim", ""),
            ("controller_claim", "fixture-"),
            ("principal_claim", "outside-fixture"),
        ]:
            with self.subTest(field=field, value=value):
                t = copy.deepcopy(self.t)
                t["witness"][field] = value
                self.reseal_witness(t)
                with self.assertRaisesRegex(ValueError, "witness identity shape invalid"):
                    validate(t)


if __name__ == "__main__":
    unittest.main()
