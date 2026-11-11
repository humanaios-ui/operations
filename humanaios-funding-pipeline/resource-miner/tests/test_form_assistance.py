import unittest
from resource_miner.form_assistance import build_packet, FIELDS


def by_id(packet):
    return {f["id"]: f for f in packet["fields"]}


def ok(value, ref="ref"):
    return {"value": value, "origin": "USER_VERIFIED", "evidence_ref": ref}


class FormAssistanceE0Tests(unittest.TestCase):
    def test_captured_form_fields(self):
        packet = build_packet()
        self.assertEqual(len(packet["fields"]), len(FIELDS))
        self.assertTrue(all(f["status"] == "NEEDS_INPUT" for f in packet["fields"]))
        self.assertEqual(packet["submission"], "DISABLED")
        self.assertEqual(packet["authority"], "NONE")
        self.assertFalse(packet["policy_verified"])

    def test_verified_profile_and_unverified_claim(self):
        packet = build_packet({
            "public_profile": ok("https://example.org", "public"),
            "name": {"value": "fabricated", "origin": "MODEL_INFERRED"},
            "progress": {"value": "unsupported achievement", "origin": "MODEL_INFERRED"},
        })
        values = by_id(packet)
        self.assertEqual(values["public_profile"]["suggested_value"], "https://example.org")
        self.assertIsNone(values["name"]["suggested_value"])
        self.assertIsNone(values["progress"]["suggested_value"])

    def test_origin_preserved(self):
        packet = build_packet({
            "public_profile": ok("https://example.org"),
            "location": {"value": "Texas", "origin": "SOURCE_VERIFIED", "evidence_ref": "doc"},
        })
        values = by_id(packet)
        self.assertEqual(values["public_profile"]["origin"], "USER_VERIFIED")
        self.assertEqual(values["location"]["origin"], "SOURCE_VERIFIED")
        self.assertIsNone(values["name"]["origin"])

    def test_restricted_writing_and_consent(self):
        packet = build_packet({
            "project_detail": ok("Draft text"),
            "public_consent": ok("yes"),
        }, assistance_policy="PROOFREAD_ONLY", policy_evidence_ref="policy-url")
        values = by_id(packet)
        self.assertIsNone(values["project_detail"]["suggested_value"])
        self.assertIsNone(values["public_consent"]["suggested_value"])

    def test_draft_only_when_allowed_and_policy_verified(self):
        data = {"project_detail": ok("Human-reviewed draft")}
        # Allowed but no evidence recorded: still blocked, packet says unverified.
        packet = build_packet(data, assistance_policy="DRAFT_ALLOWED")
        self.assertIsNone(by_id(packet)["project_detail"]["suggested_value"])
        self.assertFalse(packet["policy_verified"])
        # Allowed with recorded evidence: ready, and packet agrees.
        packet = build_packet(data, assistance_policy="DRAFT_ALLOWED", policy_evidence_ref="bluedot-policy-2026-10-24")
        self.assertEqual(by_id(packet)["project_detail"]["suggested_value"], "Human-reviewed draft")
        self.assertTrue(packet["policy_verified"])

    def test_blank_evidence_ref_does_not_verify(self):
        packet = build_packet({"project_detail": ok("x")}, assistance_policy="DRAFT_ALLOWED", policy_evidence_ref="   ")
        self.assertFalse(packet["policy_verified"])
        self.assertIsNone(by_id(packet)["project_detail"]["suggested_value"])

    def test_process_feedback_is_gated_as_draft(self):
        self.assertEqual(by_id(build_packet())["process_feedback"]["kind"], "draft")
        for policy in ("UNKNOWN", "RESEARCH_ONLY", "PROOFREAD_ONLY"):
            packet = build_packet({"process_feedback": ok("Faster replies")},
                                  assistance_policy=policy, policy_evidence_ref="p")
            self.assertIsNone(by_id(packet)["process_feedback"]["suggested_value"], policy)

    def test_funding_amount_validation(self):
        for bad in ("unknown", -50, 0, 75, "75", float("nan"), float("inf"), True, "", "-100", "5,0", "15,00", "1,50", "$5,0"):
            packet = build_packet({"request_usd": {"value": bad, "origin": "USER_VERIFIED"}})
            self.assertIsNone(by_id(packet)["request_usd"]["suggested_value"], repr(bad))
        for good in (50, 1500, "2000", 20000.0, "$1,500"):
            packet = build_packet({"request_usd": ok(good)})
            self.assertEqual(by_id(packet)["request_usd"]["status"], "READY_FOR_HUMAN_REVIEW", repr(good))

    def test_no_private_echo_on_unknown(self):
        packet = build_packet({"email": {"value": "secret@example.org", "origin": "UNVERIFIED"}})
        self.assertNotIn("secret@example.org", str(packet))


if __name__ == "__main__":
    unittest.main()
