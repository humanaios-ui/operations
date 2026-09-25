import unittest

from entry_protocol.inbound_command_processor import (
    ActorKind,
    InboundCommandProcessor,
    extract_new_text,
    projection_contains_private_material,
)


CATALOG = {
    "RM-20260925-03": "Run the first real Resource Miner intake cycle",
    "CURR-20260925-01": "Diagnose PR 534 failed gates",
    "MOVE-20260925-01": "Close the RNOLA evidence gap",
}


class InboundCommandProcessorTests(unittest.TestCase):
    def test_strips_quoted_digest_and_signature(self):
        raw = """Begin thread RM-20260925-03 and track progress.

Carly Anderson (Night)
Founder

On Fri, Sep 25, 2026 at 15:46 Human AIOS <x@example.com> wrote:
> begin thread CURR-20260925-01
"""
        self.assertEqual(
            extract_new_text(raw),
            "Begin thread RM-20260925-03 and track progress.",
        )

    def test_explicit_id_begins_thread(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="EVT-opaque-001",
            raw_body="Begin thread RM-20260925-03 and track its progress.",
        )
        self.assertEqual(event.target_item_id, "RM-20260925-03")
        self.assertEqual(event.command_kind, "BEGIN_THREAD")
        self.assertEqual(event.proposed_state, "ACTIVE")
        self.assertTrue(event.tracking_requested)

    def test_natural_title_resolution(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="EVT-opaque-002",
            raw_body=(
                "Begin thread to activate Run the first real Resource Miner "
                "intake cycle; track its progress."
            ),
        )
        self.assertEqual(event.target_item_id, "RM-20260925-03")
        self.assertEqual(event.resolution_state, "RESOLVED")
        self.assertEqual(event.proposed_state, "ACTIVE")

    def test_quoted_command_does_not_execute(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="EVT-opaque-003",
            raw_body="""Looks good.

On Fri, Sep 25, 2026 at 15:46 Human AIOS wrote:
Begin thread RM-20260925-03
""",
        )
        self.assertIsNone(event.target_item_id)
        self.assertEqual(
            event.execution_disposition,
            "NO_EXECUTABLE_TRANSITION",
        )

    def test_agent_span_is_observation_only(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="EVT-opaque-004",
            raw_body="Begin thread RM-20260925-03.",
            actor_kind=ActorKind.AGENT,
        )
        self.assertEqual(
            event.execution_disposition,
            "OBSERVATION_ONLY_NON_HUMAN",
        )
        self.assertIsNone(processor.thread_states.get("RM-20260925-03"))

    def test_z3_language_is_held(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="EVT-opaque-005",
            raw_body="Begin thread RM-20260925-03 and deploy it when ready.",
        )
        self.assertEqual(event.authority_level, "Z3")
        self.assertEqual(
            event.execution_disposition,
            "HOLD_FOR_HUMAN_AUTHORITY",
        )
        self.assertEqual(event.proposed_state, "NEW")

    def test_replay_rejected(self):
        processor = InboundCommandProcessor(CATALOG)
        processor.process(
            private_event_ref="EVT-opaque-006",
            raw_body="Begin thread RM-20260925-03.",
        )
        with self.assertRaises(ValueError):
            processor.process(
                private_event_ref="EVT-opaque-006",
                raw_body="Begin thread RM-20260925-03.",
            )

    def test_pause_resume_close_transitions(self):
        processor = InboundCommandProcessor(CATALOG)
        processor.process(
            private_event_ref="EVT-a",
            raw_body="Begin thread RM-20260925-03.",
        )
        pause = processor.process(
            private_event_ref="EVT-b",
            raw_body="Pause thread RM-20260925-03.",
        )
        self.assertEqual(pause.proposed_state, "PAUSED")

        resume = processor.process(
            private_event_ref="EVT-c",
            raw_body="Resume thread RM-20260925-03.",
        )
        self.assertEqual(resume.proposed_state, "ACTIVE")

        close = processor.process(
            private_event_ref="EVT-d",
            raw_body="Close thread RM-20260925-03.",
        )
        self.assertEqual(close.proposed_state, "CLOSED")

    def test_public_projection_drops_private_event_ref(self):
        processor = InboundCommandProcessor(CATALOG)
        event = processor.process(
            private_event_ref="gmail-private-123",
            raw_body="Begin thread RM-20260925-03 and track progress.",
        )
        projection = event.public_projection()
        self.assertNotIn("private_event_ref", projection)
        self.assertFalse(projection_contains_private_material(projection))


if __name__ == "__main__":
    unittest.main()
