import unittest

from entry_protocol.adaptive_intake import (
    AdaptiveEntryEvent,
    EvidenceState,
    ReturnForm,
    build_event,
    observe_return,
)


class AdaptiveEntryIntakeTests(unittest.TestCase):
    def test_unlabeled_question_is_accepted(self):
        obs = observe_return("How does this work?")
        self.assertIn(ReturnForm.QUESTION.value, obs.return_forms)
        self.assertFalse(obs.fixed_schema_required)

    def test_unknown_plain_reply_is_natural_return_not_rejected(self):
        obs = observe_return("Sounds interesting.")
        self.assertEqual(obs.return_forms, (ReturnForm.NATURAL_RETURN.value,))

    def test_perplexity_link_is_shared_ai_link(self):
        obs = observe_return(
            "Here is the run https://www.perplexity.ai/search/example"
        )
        self.assertIn(ReturnForm.SHARED_AI_LINK.value, obs.return_forms)
        self.assertIn("www.perplexity.ai", obs.ai_link_hosts)

    def test_file_is_valid_return_form(self):
        obs = observe_return("", attachment_count=1)
        self.assertIn(ReturnForm.FILE.value, obs.return_forms)

    def test_multiple_return_forms_can_coexist(self):
        obs = observe_return(
            "OBSERVATION: I noticed this. What changed? "
            "https://chatgpt.com/share/example"
        )
        self.assertIn(ReturnForm.OBSERVATION.value, obs.return_forms)
        self.assertIn(ReturnForm.QUESTION.value, obs.return_forms)
        self.assertIn(ReturnForm.SHARED_AI_LINK.value, obs.return_forms)

    def test_correction_extends_same_event(self):
        first = observe_return("Here is a test run.")
        second = observe_return(
            "I forgot to include the link. "
            "https://www.perplexity.ai/search/example"
        )
        event = build_event("ENTRY-001", [first, second])
        telemetry = event.telemetry()
        self.assertEqual(telemetry["message_count"], 2)
        self.assertEqual(telemetry["correction_count"], 1)
        self.assertIn(
            "EXTEND_PRIOR_EVENT_WITH_CORRECTION",
            telemetry["adaptations"],
        )

    def test_link_does_not_imply_capture_or_verification(self):
        event = build_event(
            "ENTRY-002",
            [observe_return("https://www.perplexity.ai/search/example")],
        )
        self.assertEqual(event.evidence_states, [EvidenceState.LINK_RECEIVED.value])

    def test_evidence_states_must_advance_sequentially(self):
        event = AdaptiveEntryEvent(event_ref="ENTRY-003")
        with self.assertRaises(ValueError):
            event.mark_evidence(EvidenceState.CONTENT_CAPTURED)

        event.mark_evidence(EvidenceState.LINK_RECEIVED)
        event.mark_evidence(EvidenceState.CONTENT_CAPTURED)
        event.mark_evidence(EvidenceState.CONTENT_VERIFIED)
        self.assertEqual(
            event.evidence_states,
            [
                EvidenceState.LINK_RECEIVED.value,
                EvidenceState.CONTENT_CAPTURED.value,
                EvidenceState.CONTENT_VERIFIED.value,
            ],
        )

    def test_telemetry_does_not_retain_raw_content_or_profile_identity(self):
        event = build_event(
            "ENTRY-004",
            [observe_return("My name is Example. OBSERVATION: useful.")],
        )
        telemetry = event.telemetry()
        self.assertFalse(telemetry["raw_content_retained"])
        self.assertFalse(telemetry["participant_identity_profiled"])
        self.assertNotIn("Example", str(telemetry))


if __name__ == "__main__":
    unittest.main()
