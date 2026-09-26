import base64
import json
import os
import tempfile
import unittest
from email.message import EmailMessage

from entry_protocol.gmail_push_adapter import (
    AUTOMATION_HEADER,
    AUTOMATION_HEADER_VALUE,
    GmailAdapterConfig,
    GmailInboundAdapter,
    GmailTransportError,
    HistoryExpired,
    PrivateMailLedger,
    decode_pubsub_notification,
    extract_item_catalog,
    is_relevant_subject,
)


def _b64url(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def gmail_message(
    message_id,
    thread_id,
    *,
    subject,
    body,
    from_addr="aioshuman@gmail.com",
    labels=("INBOX", "SENT"),
    automation=False,
):
    headers = [
        {"name": "From", "value": from_addr},
        {"name": "To", "value": "aioshuman@gmail.com"},
        {"name": "Subject", "value": subject},
        {"name": "Message-ID", "value": f"<{message_id}@test>"},
    ]
    if automation:
        headers.append(
            {"name": AUTOMATION_HEADER, "value": AUTOMATION_HEADER_VALUE}
        )
    return {
        "id": message_id,
        "threadId": thread_id,
        "labelIds": list(labels),
        "payload": {
            "mimeType": "text/plain",
            "headers": headers,
            "body": {"data": _b64url(body)},
        },
    }


class FakeGmail:
    user_id = "me"

    def __init__(self):
        self.watch_response = {"historyId": "100", "expiration": "999999"}
        self.history = {}
        self.messages = {}
        self.threads = {}
        self.sent = []
        self.expire = False

    def register_watch(self, *, topic_name, label_ids=("INBOX",)):
        self.topic_name = topic_name
        self.label_ids = tuple(label_ids)
        return dict(self.watch_response)

    def list_added_message_ids(self, *, start_history_id, label_id="INBOX"):
        if self.expire:
            raise HistoryExpired("expired")
        return self.history.get(start_history_id, ([], start_history_id))

    def get_message(self, message_id):
        return self.messages[message_id]

    def get_thread(self, thread_id):
        return self.threads[thread_id]

    def send_message(self, *, raw_message, thread_id=None):
        self.sent.append((raw_message, thread_id))
        n = len(self.sent)
        return {"id": f"sent-{n}", "threadId": thread_id or f"child-{n}"}


class GmailAdapterTests(unittest.TestCase):
    def setUp(self):
        self.gmail = FakeGmail()
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "private.sqlite3")
        self.config = GmailAdapterConfig(
            mailbox_address="aioshuman@gmail.com",
            command_endpoints=("aioshuman@gmail.com",),
            evidence_hmac_key=b"x" * 32,
            database_path=self.db,
            send_enabled=False,
            acknowledgement_to="aioshuman@gmail.com",
        )
        self.store = PrivateMailLedger(self.db)
        self.adapter = GmailInboundAdapter(
            gmail=self.gmail,
            store=self.store,
            config=self.config,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_pubsub_decode(self):
        payload = base64.b64encode(
            json.dumps(
                {
                    "emailAddress": "aioshuman@gmail.com",
                    "historyId": "123",
                }
            ).encode()
        ).decode()
        email, history, msg_id = decode_pubsub_notification(
            {"message": {"data": payload, "messageId": "p1"}}
        )
        self.assertEqual(email, "aioshuman@gmail.com")
        self.assertEqual(history, "123")
        self.assertEqual(msg_id, "p1")

    def test_watch_seeds_history_baseline(self):
        response = self.adapter.register_watch(
            topic_name="projects/p/topics/mail"
        )
        self.assertEqual(response["historyId"], "100")
        self.assertEqual(self.store.get_state("gmail_history_id"), "100")
        self.assertEqual(
            self.store.get_state("gmail_watch_expiration_ms"), "999999"
        )


    def test_root_digest_is_not_command_eligible(self):
        self.assertFalse(
            is_relevant_subject(
                "HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers"
            )
        )
        self.assertTrue(
            is_relevant_subject(
                "Re: HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers"
            )
        )

    def test_multiline_digest_item_catalog_prefers_task_label(self):
        catalog = extract_item_catalog(
            "I. RESOURCE MINER\n"
            "ITEM_ID: RM-20260926-03\n"
            "STATE: NEW\n"
            "TASK: Run the first real Resource Miner intake cycle\n"
            "AUTHORITY: Z1\n"
        )
        self.assertEqual(
            catalog["RM-20260926-03"],
            "Run the first real Resource Miner intake cycle",
        )

    def test_matching_from_without_sent_is_not_human_authority(self):
        self._seed_digest_reply("Begin thread RM-20260926-03.")
        self.gmail.messages["reply-1"] = gmail_message(
            "reply-1",
            "thread-digest",
            subject="Re: HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers",
            body="Begin thread RM-20260926-03.",
            from_addr="aioshuman@gmail.com",
            labels=("INBOX",),
        )
        result = self.adapter.handle_push("101")
        self.assertEqual(
            result.results[0].disposition,
            "OBSERVATION_ONLY_NON_HUMAN",
        )
        self.assertEqual(
            self.store.thread_states()["RM-20260926-03"].value,
            "NEW",
        )

    def test_resync_gap_blocks_watch_reset_without_explicit_ack(self):
        self.store.set_state("gmail_resync_required", "1")
        with self.assertRaises(GmailTransportError):
            self.adapter.register_watch(topic_name="projects/p/topics/mail")
        response = self.adapter.register_watch(
            topic_name="projects/p/topics/mail",
            acknowledge_resync_gap=True,
        )
        self.assertEqual(response["historyId"], "100")
        self.assertEqual(self.store.get_state("gmail_resync_required"), "0")

    def _seed_digest_reply(self, command):
        digest = gmail_message(
            "digest-1",
            "thread-digest",
            subject="HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers",
            body=(
                "I. RESOURCE MINER\n"
                "ITEM_ID: RM-20260926-03 | STATE: NEW | "
                "TASK: Run the first real Resource Miner intake cycle\n"
            ),
        )
        reply = gmail_message(
            "reply-1",
            "thread-digest",
            subject="Re: HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers",
            body=command,
        )
        self.gmail.messages["reply-1"] = reply
        self.gmail.threads["thread-digest"] = {
            "messages": [digest, reply]
        }
        self.gmail.history["100"] = (["reply-1"], "101")
        self.store.set_state("gmail_history_id", "100")

    def test_natural_digest_reply_activates_item(self):
        self._seed_digest_reply(
            "Begin a thread for the first real Resource Miner intake cycle and track progress."
        )
        result = self.adapter.handle_push("101")
        self.assertEqual(result.processed, 1)
        event = result.results[0]
        self.assertEqual(event.target_item_id, "RM-20260926-03")
        self.assertEqual(event.thread_state, "ACTIVE")
        self.assertEqual(event.disposition, "Z1_PROPOSED_TRANSITION")
        self.assertEqual(event.outbound_status, "OUTBOUND_DISABLED")

    def test_replayed_message_does_not_transition_twice(self):
        self._seed_digest_reply(
            "Begin thread RM-20260926-03 and track progress."
        )
        first = self.adapter.handle_push("101")
        self.assertEqual(first.processed, 1)

        self.gmail.history["101"] = (["reply-1"], "102")
        second = self.adapter.handle_push("102")
        self.assertEqual(second.replays, 1)
        self.assertEqual(
            self.store.thread_states()["RM-20260926-03"].value,
            "ACTIVE",
        )

    def test_automation_generated_child_mail_is_ignored(self):
        self.store.set_state("gmail_history_id", "100")
        generated = gmail_message(
            "auto-1",
            "child-1",
            subject="THREAD RM-20260926-03 — Resource Miner cycle — ACTIVE",
            body="ITEM_ID: RM-20260926-03\nSTATE: ACTIVE",
            automation=True,
        )
        self.gmail.messages["auto-1"] = generated
        self.gmail.history["100"] = (["auto-1"], "101")
        result = self.adapter.handle_push("101")
        self.assertEqual(result.ignored, 1)
        self.assertNotIn("RM-20260926-03", self.store.thread_states())

    def test_unrecognized_sender_cannot_create_human_transition(self):
        self._seed_digest_reply("Begin thread RM-20260926-03.")
        self.gmail.messages["reply-1"] = gmail_message(
            "reply-1",
            "thread-digest",
            subject="Re: HumanAIOS Daily Digest — 2026-09-26 | 0 decisions | 0 blockers",
            body="Begin thread RM-20260926-03.",
            from_addr="someone@example.net",
            labels=("INBOX",),
        )
        result = self.adapter.handle_push("101")
        self.assertEqual(
            result.results[0].disposition,
            "OBSERVATION_ONLY_NON_HUMAN",
        )
        self.assertEqual(
            self.store.thread_states()["RM-20260926-03"].value,
            "NEW",
        )

    def test_z3_command_is_held(self):
        self._seed_digest_reply(
            "Begin thread RM-20260926-03 and deploy it when ready."
        )
        result = self.adapter.handle_push("101")
        event = result.results[0]
        self.assertEqual(event.authority_level, "Z3")
        self.assertEqual(event.disposition, "HOLD_FOR_HUMAN_AUTHORITY")
        self.assertEqual(event.thread_state, "NEW")
        self.assertEqual(result.held, 1)

    def test_history_expiry_surfaces_resync_requirement(self):
        self.store.set_state("gmail_history_id", "100")
        self.gmail.expire = True
        result = self.adapter.handle_push("999")
        self.assertEqual(result.status, "HISTORY_EXPIRED_RESYNC_REQUIRED")
        self.assertEqual(self.store.get_state("gmail_resync_required"), "1")
        self.assertEqual(self.store.get_state("gmail_history_id"), "100")

    def test_missing_baseline_fails_closed(self):
        result = self.adapter.handle_push("123")
        self.assertEqual(result.status, "BASELINE_MISSING_RESYNC_REQUIRED")
        self.assertEqual(self.store.get_state("gmail_resync_required"), "1")
        self.assertEqual(self.store.get_state("gmail_history_id"), "123")

    def test_send_enabled_creates_child_thread_and_loop_guard_header(self):
        config = GmailAdapterConfig(
            mailbox_address="aioshuman@gmail.com",
            command_endpoints=("aioshuman@gmail.com",),
            evidence_hmac_key=b"x" * 32,
            database_path=self.db,
            send_enabled=True,
            acknowledgement_to="aioshuman@gmail.com",
        )
        adapter = GmailInboundAdapter(
            gmail=self.gmail,
            store=self.store,
            config=config,
        )
        self.adapter = adapter
        self._seed_digest_reply("Begin thread RM-20260926-03.")
        result = adapter.handle_push("101")
        self.assertEqual(result.results[0].outbound_status, "CHILD_THREAD_SENT")
        raw, thread_id = self.gmail.sent[0]
        self.assertIsNone(thread_id)
        self.assertIn(
            f"{AUTOMATION_HEADER}: {AUTOMATION_HEADER_VALUE}".encode(),
            raw,
        )
        row = self.store.get_thread("RM-20260926-03")
        self.assertEqual(row["child_gmail_thread_id"], "child-1")


if __name__ == "__main__":
    unittest.main()
