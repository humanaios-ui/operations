import unittest

from entry_protocol.identity_graph import (
    ActorKind,
    AgentInstance,
    AgentProfile,
    BehaviorEvent,
    BehaviorEvidenceKind,
    BehaviorType,
    Collaboration,
    HumanSubject,
    IdentityEdge,
    IdentityRelation,
    IdentityStatus,
    ParticipationRoot,
    RouteBinding,
    SpeakerKind,
    SpeakerSpan,
    register_private_endpoint_alias,
)


class ParticipationRootTests(unittest.TestCase):
    def setUp(self):
        self.root = ParticipationRoot()
        self.root.register_human(HumanSubject("H-017"))
        self.root.register_agent_profile(
            AgentProfile(
                ref="AP-CHATGPT",
                provider_product="ChatGPT",
                model_name="GPT-5.6 Sol",
                identity_status=IdentityStatus.SELF_REPORTED.value,
            )
        )
        self.root.register_agent_instance(
            AgentInstance(ref="A-917", profile_ref="AP-CHATGPT")
        )
        self.root.register_collaboration(Collaboration("C-208"))
        self.root.add_collaboration_member("H-017", "C-208")
        self.root.add_collaboration_member("A-917", "C-208")

    def test_multiple_endpoints_can_map_to_one_pseudonymous_human(self):
        register_private_endpoint_alias(
            self.root, endpoint_ref="E-041", human_ref="H-017"
        )
        register_private_endpoint_alias(
            self.root, endpoint_ref="E-093", human_ref="H-017"
        )
        self.assertEqual(
            len(
                [
                    e
                    for e in self.root.identity_edges
                    if e.relation == IdentityRelation.ENDPOINT_BELONGS_TO.value
                ]
            ),
            2,
        )
        projection = self.root.public_projection()
        self.assertNotIn("E-041", str(projection))
        self.assertNotIn("E-093", str(projection))

    def test_same_model_sessions_remain_distinct_agent_instances(self):
        self.root.register_agent_instance(
            AgentInstance(ref="A-918", profile_ref="AP-CHATGPT")
        )
        self.assertIn("A-917", self.root.agent_instances)
        self.assertIn("A-918", self.root.agent_instances)
        self.assertNotEqual(
            self.root.agent_instances["A-917"].ref,
            self.root.agent_instances["A-918"].ref,
        )

    def test_human_ai_human_message_can_be_segmented_by_speaker(self):
        spans = [
            SpeakerSpan(
                ref="S-1",
                message_ref="M-88",
                subject_ref="H-017",
                speaker_kind=SpeakerKind.HUMAN.value,
                attribution_status=IdentityStatus.OBSERVED.value,
                collaboration_ref="C-208",
            ),
            SpeakerSpan(
                ref="S-2",
                message_ref="M-88",
                subject_ref="A-917",
                speaker_kind=SpeakerKind.AI.value,
                attribution_status=IdentityStatus.SELF_REPORTED.value,
                collaboration_ref="C-208",
            ),
            SpeakerSpan(
                ref="S-3",
                message_ref="M-88",
                subject_ref="H-017",
                speaker_kind=SpeakerKind.HUMAN.value,
                attribution_status=IdentityStatus.OBSERVED.value,
                collaboration_ref="C-208",
            ),
        ]
        for span in spans:
            self.root.add_speaker_span(span)
        self.assertEqual(self.root.speaker_spans["S-2"].subject_ref, "A-917")

    def test_behavior_event_must_match_explicit_source_subject(self):
        self.root.add_speaker_span(
            SpeakerSpan(
                ref="S-AI",
                message_ref="M-100",
                subject_ref="A-917",
                speaker_kind=SpeakerKind.AI.value,
                attribution_status=IdentityStatus.SELF_REPORTED.value,
            )
        )
        self.root.add_behavior_event(
            BehaviorEvent(
                ref="B-1",
                subject_ref="A-917",
                source_message_ref="M-100",
                source_span_ref="S-AI",
                behavior_type=BehaviorType.CAPABILITY_CLAIM.value,
                evidence_kind=BehaviorEvidenceKind.SELF_REPORTED.value,
                dimension="Humility",
            )
        )
        with self.assertRaises(ValueError):
            self.root.add_behavior_event(
                BehaviorEvent(
                    ref="B-2",
                    subject_ref="H-017",
                    source_message_ref="M-100",
                    source_span_ref="S-AI",
                    behavior_type=BehaviorType.CAPABILITY_FAILURE.value,
                    evidence_kind=BehaviorEvidenceKind.OBSERVED.value,
                )
            )

    def test_self_report_and_observed_behavior_can_link_on_same_agent(self):
        self.root.add_speaker_span(
            SpeakerSpan(
                ref="S-CLAIM",
                message_ref="M-101",
                subject_ref="A-917",
                speaker_kind=SpeakerKind.AI.value,
                attribution_status=IdentityStatus.SELF_REPORTED.value,
            )
        )
        self.root.add_behavior_event(
            BehaviorEvent(
                ref="B-CLAIM",
                subject_ref="A-917",
                source_message_ref="M-101",
                source_span_ref="S-CLAIM",
                behavior_type=BehaviorType.CAPABILITY_CLAIM.value,
                evidence_kind=BehaviorEvidenceKind.SELF_REPORTED.value,
            )
        )
        self.root.add_speaker_span(
            SpeakerSpan(
                ref="S-FAIL",
                message_ref="M-102",
                subject_ref="A-917",
                speaker_kind=SpeakerKind.AI.value,
                attribution_status=IdentityStatus.OBSERVED.value,
            )
        )
        self.root.add_behavior_event(
            BehaviorEvent(
                ref="B-FAIL",
                subject_ref="A-917",
                source_message_ref="M-102",
                source_span_ref="S-FAIL",
                behavior_type=BehaviorType.CAPABILITY_FAILURE.value,
                evidence_kind=BehaviorEvidenceKind.OBSERVED.value,
                related_event_ref="B-CLAIM",
            )
        )
        history = self.root.behavior_history("A-917")
        self.assertEqual([x.ref for x in history], ["B-CLAIM", "B-FAIL"])

    def test_inferred_same_subject_does_not_collapse_histories(self):
        self.root.register_human(HumanSubject("H-044"))
        self.root.add_identity_edge(
            IdentityEdge(
                source_ref="H-044",
                relation=IdentityRelation.SAME_SUBJECT.value,
                target_ref="H-017",
                status=IdentityStatus.INFERRED.value,
            )
        )
        self.assertEqual(self.root.canonical_subject("H-044"), "H-044")

    def test_human_confirmed_same_subject_can_resolve_without_erasure(self):
        self.root.register_human(HumanSubject("H-044"))
        self.root.add_identity_edge(
            IdentityEdge(
                source_ref="H-044",
                relation=IdentityRelation.SAME_SUBJECT.value,
                target_ref="H-017",
                status=IdentityStatus.HUMAN_CONFIRMED.value,
            )
        )
        self.assertEqual(self.root.canonical_subject("H-044"), "H-017")
        self.assertIn("H-044", self.root.humans)

    def test_routing_is_separate_and_private(self):
        self.root.add_route(
            RouteBinding(
                logical_thread_ref="T-044",
                endpoint_ref="E-041",
                status=IdentityStatus.TRANSPORT_VERIFIED.value,
            )
        )
        self.assertEqual(self.root.endpoint_for_thread("T-044"), "E-041")
        projection = self.root.public_projection()
        self.assertEqual(projection["routing"]["binding_count"], 1)
        self.assertFalse(projection["routing"]["endpoint_refs_exposed"])
        self.assertNotIn("E-041", str(projection))

    def test_raw_email_or_url_cannot_be_used_as_public_refs(self):
        with self.assertRaises(ValueError):
            HumanSubject("person@example.com")
        with self.assertRaises(ValueError):
            AgentInstance("https://example.com/session")


if __name__ == "__main__":
    unittest.main()
