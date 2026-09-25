import unittest

from entry_protocol.adaptive_intake import (
    AdaptiveEntryEvent,
    AgentCapability,
    AgentParticipationProfile,
    EvidenceState,
    ExposureLevel,
    ParticipationMode,
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

    def test_perplexity_link_is_shared_ai_link_without_retaining_raw_url(self):
        raw = "https://www.perplexity.ai/search/private-token-123"
        obs = observe_return(f"Here is the run {raw}")
        self.assertIn(ReturnForm.SHARED_AI_LINK.value, obs.return_forms)
        self.assertIn("www.perplexity.ai", obs.ai_link_hosts)
        self.assertFalse(obs.raw_links_retained)
        self.assertNotIn(raw, str(obs.to_dict()))

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
        event = build_event("PRIVATE-MAIL-ID-DO-NOT-PROJECT", [first, second])
        telemetry = event.telemetry()
        self.assertEqual(telemetry["message_count"], 2)
        self.assertEqual(telemetry["correction_count"], 1)
        self.assertIn(
            "EXTEND_PRIOR_EVENT_WITH_CORRECTION",
            telemetry["adaptations"],
        )
        self.assertNotIn("PRIVATE-MAIL-ID-DO-NOT-PROJECT", str(telemetry))
        self.assertFalse(telemetry["event_ref_retained"])

    def test_link_does_not_imply_capture_or_verification(self):
        event = build_event(
            "ENTRY-002",
            [observe_return("https://www.perplexity.ai/search/example")],
        )
        self.assertEqual(event.evidence_states, [EvidenceState.LINK_RECEIVED.value])

    def test_duplicate_link_after_advanced_state_is_safe(self):
        event = build_event(
            "ENTRY-003",
            [observe_return("https://www.perplexity.ai/search/example")],
        )
        event.mark_evidence(EvidenceState.CONTENT_CAPTURED)
        event.mark_evidence(EvidenceState.CONTENT_VERIFIED)
        event.append(
            observe_return(
                "Correction: another link https://www.perplexity.ai/search/second"
            )
        )
        self.assertEqual(event.evidence_states[-1], EvidenceState.CONTENT_VERIFIED.value)
        self.assertEqual(len(event.observations), 2)

    def test_evidence_states_must_advance_sequentially(self):
        event = AdaptiveEntryEvent(event_ref="ENTRY-004")
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

    def test_research_enrichment_can_add_agent_provenance_and_review_interest(self):
        event = build_event("ENTRY-005", [observe_return("I am interested.")])
        event.set_participation_modes(
            [ParticipationMode.REVIEW, ParticipationMode.REVIEW_BOARD_INTEREST]
        )
        event.set_agent_profile(
            AgentParticipationProfile(
                provider_product="ChatGPT",
                model_name="GPT-5.6 Sol",
                prior_exposure=ExposureLevel.FULL.value,
                capabilities=(
                    AgentCapability.PUBLIC_WEB.value,
                    AgentCapability.REPOSITORY_READ.value,
                    AgentCapability.CODE_EXECUTION.value,
                ),
                self_reported_behavior_provided=True,
                observed_behavior_provided=True,
                limitations_provided=True,
            )
        )
        telemetry = event.telemetry()
        self.assertIn(
            ParticipationMode.REVIEW_BOARD_INTEREST.value,
            telemetry["participation_modes"],
        )
        self.assertEqual(telemetry["agent_profile"]["model_name"], "GPT-5.6 Sol")
        self.assertIn(
            "ENRICH_AGENT_PROVENANCE_FOR_RESEARCH",
            telemetry["adaptations"],
        )

    def test_agent_label_rejects_email_or_url(self):
        with self.assertRaises(ValueError):
            AgentParticipationProfile(provider_product="person@example.com")
        with self.assertRaises(ValueError):
            AgentParticipationProfile(model_name="https://example.com/model")

    def test_telemetry_does_not_retain_raw_content_or_profile_human_identity(self):
        event = build_event(
            "ENTRY-006",
            [observe_return("My name is Example. OBSERVATION: useful.")],
        )
        telemetry = event.telemetry()
        self.assertFalse(telemetry["raw_content_retained"])
        self.assertFalse(telemetry["raw_links_retained"])
        self.assertFalse(telemetry["participant_identity_profiled"])
        self.assertNotIn("Example", str(telemetry))


if __name__ == "__main__":
    unittest.main()
