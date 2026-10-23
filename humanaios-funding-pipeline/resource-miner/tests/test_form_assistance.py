import unittest
from resource_miner.form_assistance import build_packet, FIELDS

class FormAssistanceE0Tests(unittest.TestCase):
    def test_captured_form_fields(self):
        packet = build_packet()
        self.assertEqual(len(packet["fields"]), len(FIELDS))
        self.assertTrue(all(f["status"] == "NEEDS_INPUT" for f in packet["fields"]))
        self.assertEqual(packet["submission"], "DISABLED")
        self.assertEqual(packet["authority"], "NONE")

    def test_verified_profile_and_unverified_claim(self):
        packet = build_packet({
            "public_profile": {"value": "https://example.org", "origin": "USER_VERIFIED", "evidence_ref": "public"},
            "name": {"value": "fabricated", "origin": "MODEL_INFERRED"},
            "progress": {"value": "unsupported achievement", "origin": "MODEL_INFERRED"},
        })
        values = {f["id"]: f for f in packet["fields"]}
        self.assertEqual(values["public_profile"]["suggested_value"], "https://example.org")
        self.assertIsNone(values["name"]["suggested_value"])
        self.assertIsNone(values["progress"]["suggested_value"])

    def test_restricted_writing_and_consent(self):
        packet = build_packet({
            "project_detail": {"value": "Draft text", "origin": "USER_VERIFIED"},
            "public_consent": {"value": "yes", "origin": "USER_VERIFIED"},
        }, assistance_policy="PROOFREAD_ONLY")
        values = {f["id"]: f for f in packet["fields"]}
        self.assertIsNone(values["project_detail"]["suggested_value"])
        self.assertIsNone(values["public_consent"]["suggested_value"])

    def test_draft_only_when_explicitly_allowed(self):
        values = {f["id"]: f for f in build_packet({
            "project_detail": {"value": "Human-reviewed draft", "origin": "USER_VERIFIED"}
        }, assistance_policy="DRAFT_ALLOWED")["fields"]}
        self.assertEqual(values["project_detail"]["suggested_value"], "Human-reviewed draft")

    def test_no_private_echo_on_unknown(self):
        packet = build_packet({"email": {"value": "secret@example.org", "origin": "UNVERIFIED"}})
        self.assertNotIn("secret@example.org", str(packet))

if __name__ == "__main__":
    unittest.main()
