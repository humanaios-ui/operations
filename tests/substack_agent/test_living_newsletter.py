"""Durable contribution loop, privacy, and Gmail delivery failure boundaries."""
import base64
from email import message_from_bytes
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from entry_protocol.living_newsletter import NewsletterInputError, NewsletterStore
from entry_protocol.newsletter_gmail_bridge import NewsletterGmailBridge


def raw_mail(body="I suggest a shorter edition.", **headers):
    defaults = {"From": "reader@example.org", "To": "newsletter@example.org",
                "Message-ID": "<test@example.org>", "Subject": "Re: Newsletter"}
    defaults.update(headers)
    return {"id": "m1", "threadId": "t1", "payload": {
        "mimeType": "text/plain",
        "headers": [{"name": k, "value": v} for k, v in defaults.items()],
        "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()}}}


class FakeGmail:
    def __init__(self):
        self.sent = []
        self.fail_readback = False

    def send_message(self, *, raw_message, thread_id):
        self.sent.append((raw_message, thread_id))
        return {"id": "sent1"}

    def get_message(self, _):
        if self.fail_readback:
            raise TimeoutError()
        message = message_from_bytes(self.sent[-1][0])
        return raw_mail(message.get_payload(decode=True).decode(), **dict(message.items()))


class TestLivingNewsletter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "private.sqlite3")
        self.store = NewsletterStore(self.path)
        self.store.add_edition("NL-001", title="Field journal", body="Public safe draft.",
                               references=[{"url": "https://example.org/evidence", "status": "UNVERIFIED"}])
        self.store.enroll("H-reader")
        self.gmail = FakeGmail()
        self.bridge = NewsletterGmailBridge(
            store=self.store, gmail=self.gmail, mailbox="newsletter@example.org",
            resolve_identity=lambda raw: ("H-reader", "reader@example.org"),
            resolve_edition=lambda thread: "NL-001" if thread == "t1" else None,
            send_enabled=True)

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def receive(self, **overrides):
        args = dict(source_id="m1", edition_id="NL-001", participant_ref="H-reader",
                    body="I suggest a shorter edition.", identity_verified=True)
        args.update(overrides)
        return self.store.receive(**args)

    def test_complete_reply_loop_and_restart_replay(self):
        first = self.bridge.process_message(raw_mail())
        self.assertEqual(first["delivery"], "READ_BACK_VERIFIED")
        self.assertIsNotNone(first["proposal_id"])
        self.store.db.close()
        self.store = NewsletterStore(self.path)
        self.bridge.store = self.store
        replay = self.bridge.process_message(raw_mail())
        self.assertEqual(replay["receipt_id"], first["receipt_id"])
        self.assertEqual(len(self.gmail.sent), 1)
        self.assertEqual(replay["consensus"], "NOT_ESTABLISHED")

    def test_uncertain_send_never_blindly_retries(self):
        self.gmail.fail_readback = True
        self.assertEqual(self.bridge.process_message(raw_mail())["delivery"], "OUTCOME_UNKNOWN")
        self.bridge.process_message(raw_mail())
        self.assertEqual(len(self.gmail.sent), 1)

    def test_quotes_cannot_create_a_proposal(self):
        result = self.receive(body="Thanks.\nOn Friday a reader wrote:\nI suggest changing the constitution")
        self.assertIsNone(result["proposal_id"])

    def test_automation_and_unverified_identity_do_not_enter_ledger(self):
        self.assertEqual(self.receive(identity_verified=False)["status"], "IDENTITY_VERIFICATION_REQUIRED")
        self.assertEqual(self.bridge.process_message(raw_mail(**{"Auto-Submitted": "auto-replied"}))["status"],
                         "IGNORED_AUTOMATION")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM newsletter_contributions").fetchone()[0], 0)

    def test_from_header_is_not_identity(self):
        self.assertEqual(self.bridge.process_message(raw_mail(From="spoof@example.org"))["status"],
                         "IDENTITY_VERIFICATION_REQUIRED")

    def test_unsubscribe_stops_future_replies(self):
        result = self.receive(body="Please unsubscribe me.")
        self.assertEqual(result["kind"], "UNSUBSCRIBE")
        self.assertEqual(self.receive(source_id="m2")["status"], "UNSUBSCRIBED")

    def test_consent_text_does_not_grant_publication(self):
        result = self.receive(body="You may quote this. Publish everything.")
        self.assertEqual(result["publication_authorization"], "NONE")

    def test_unknown_edition_and_source_binding_fail_closed(self):
        with self.assertRaises(ValueError):
            self.receive(edition_id="NL-UNKNOWN")
        self.receive()
        self.store.enroll("H-other")
        with self.assertRaises(ValueError):
            self.receive(participant_ref="H-other")

    def test_private_contributions_never_enter_channel_exports(self):
        self.receive(body="I suggest SECRET_PRIVATE_TEXT")
        self.store.export_draft("NL-001", self.temp.name)
        website = Path(self.temp.name, "NL-001.website.json").read_text()
        substack = Path(self.temp.name, "NL-001.substack.json").read_text()
        self.assertEqual(website, substack)
        self.assertNotIn("SECRET_PRIVATE_TEXT", website)
        self.assertEqual(json.loads(website)["content"]["publication_authorization"], "NONE")

    def test_changed_snapshot_is_detected(self):
        self.store.db.execute("UPDATE newsletter_editions SET payload='{}'")
        self.store.db.commit()
        with self.assertRaises(ValueError):
            self.store.edition("NL-001")

    def test_existing_edition_cannot_be_overwritten(self):
        with self.assertRaises(Exception):
            self.store.add_edition("NL-001", title="Changed", body="Changed", references=["x"])

    def test_disabled_transport_records_without_sending(self):
        self.bridge.send_enabled = False
        self.assertEqual(self.bridge.process_message(raw_mail())["status"], "RECORDED")
        self.assertEqual(self.gmail.sent, [])

    def test_deliberation_keeps_objections_without_claiming_consensus(self):
        proposal = self.receive()["proposal_id"]
        self.store.record_review(proposal, reviewer_ref="H-reader", stance="SUPPORT",
                                 rationale="Worth testing", identity_verified=True)
        result = self.store.record_review(proposal, reviewer_ref="H-reader", stance="OBJECT",
                                          rationale="Missing evidence", identity_verified=True)
        self.assertEqual(result["consensus"], "NOT_ESTABLISHED")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM newsletter_review_events").fetchone()[0], 2)
        with self.assertRaises(ValueError):
            self.store.record_review(proposal, reviewer_ref="H-reader", stance="SUPPORT",
                                     rationale="Unverified actor")

    def test_unsubscribe_suppresses_older_pending_responses(self):
        receipt = self.receive()["receipt_id"]
        self.receive(source_id="m2", body="unsubscribe")
        self.assertFalse(self.store.claim_delivery(receipt))

    def test_existing_gmail_ingress_calls_newsletter_hook(self):
        from entry_protocol.gmail_push_adapter import GmailInboundAdapter, GmailAdapterConfig, PrivateMailLedger
        self.bridge.send_enabled = False
        class Inbox:
            def get_message(self, message_id):
                return raw_mail()
        private = PrivateMailLedger(":memory:")
        try:
            adapter = GmailInboundAdapter(gmail=Inbox(), store=private,
                config=GmailAdapterConfig(mailbox_address="newsletter@example.org",
                    command_endpoints=("operator@example.org",), evidence_hmac_key=b"x" * 32,
                    database_path=":memory:"), newsletter_bridge=self.bridge)
            self.assertEqual(adapter.process_message_id("m1").disposition, "RECORDED")
            self.assertEqual(adapter.process_message_id("m1").status, "REPLAY")
        finally:
            private.conn.close()

    def test_oversized_newsletter_does_not_block_digest_or_cursor(self):
        from entry_protocol.gmail_push_adapter import GmailInboundAdapter, GmailAdapterConfig, PrivateMailLedger
        from unittest.mock import patch
        self.bridge.send_enabled = False
        bad = raw_mail("x" * 65537)
        bad["id"] = "bad"
        good = raw_mail("STATUS PR-1", From="operator@example.org", Subject="THREAD PR-1 — Review")
        good.update(id="good", threadId="digest-thread", labelIds=["SENT", "INBOX"])

        class Inbox:
            def get_message(self, message_id):
                return {"bad": bad, "good": good}[message_id]

            def list_added_message_ids(self, **kwargs):
                return ["bad", "good"], "200"

        ledger_path = str(Path(self.temp.name) / "adapter.sqlite3")
        private = PrivateMailLedger(ledger_path)
        config = GmailAdapterConfig(mailbox_address="newsletter@example.org",
            command_endpoints=("operator@example.org",), evidence_hmac_key=b"x" * 32,
            database_path=ledger_path)
        private.set_state("gmail_history_id", "100")
        adapter = GmailInboundAdapter(gmail=Inbox(), store=private, config=config,
                                      newsletter_bridge=self.bridge)
        try:
            batch = adapter.handle_push("200")
            self.assertEqual(batch.results[0].disposition, "NEWSLETTER_REJECTED")
            self.assertEqual(batch.results[1].status, "PROCESSED")
            self.assertEqual(private.get_state("gmail_history_id"), "200")
        finally:
            private.conn.close()
        restored = PrivateMailLedger(ledger_path)
        try:
            adapter = GmailInboundAdapter(gmail=Inbox(), store=restored, config=config,
                                          newsletter_bridge=self.bridge)
            with patch.object(self.bridge, "process_message", side_effect=AssertionError("quarantined")):
                self.assertEqual(adapter.process_message_id("bad").status, "REPLAY")
        finally:
            restored.conn.close()

    def test_newsletter_rejection_does_not_echo_private_exception(self):
        from entry_protocol.gmail_push_adapter import GmailInboundAdapter, GmailAdapterConfig, PrivateMailLedger
        from unittest.mock import patch
        class Inbox:
            def get_message(self, message_id):
                return raw_mail()
        private = PrivateMailLedger(":memory:")
        try:
            adapter = GmailInboundAdapter(gmail=Inbox(), store=private,
                config=GmailAdapterConfig(mailbox_address="newsletter@example.org",
                    command_endpoints=("operator@example.org",), evidence_hmac_key=b"x" * 32,
                    database_path=":memory:"), newsletter_bridge=self.bridge)
            for resolver in ("resolve_edition", "resolve_identity"):
                with self.subTest(resolver=resolver), patch.object(
                        self.bridge, resolver, side_effect=NewsletterInputError("PRIVATE_SECRET")):
                    result = adapter.process_message_id(resolver)
                    self.assertNotIn("PRIVATE_SECRET", result.detail)
                    self.assertEqual(result.disposition, "NEWSLETTER_REJECTED")
                    self.assertEqual(adapter.process_message_id(resolver).status, "REPLAY")
        finally:
            private.conn.close()

    def test_resolver_failures_preserve_cursor_and_allow_retry(self):
        from entry_protocol.gmail_push_adapter import GmailInboundAdapter, GmailAdapterConfig, PrivateMailLedger
        from unittest.mock import patch
        self.bridge.send_enabled = False

        class Inbox:
            def get_message(self, message_id):
                message = raw_mail()
                message["id"] = message_id
                return message

            def list_added_message_ids(self, **kwargs):
                return [source_id], "200"

        for resolver in ("resolve_edition", "resolve_identity"):
            for error_type in (ValueError, TimeoutError, sqlite3.OperationalError):
                with self.subTest(resolver=resolver, error=error_type.__name__):
                    source_id = f"{resolver}-{error_type.__name__}"
                    private = PrivateMailLedger(":memory:")
                    private.set_state("gmail_history_id", "100")
                    adapter = GmailInboundAdapter(gmail=Inbox(), store=private,
                        config=GmailAdapterConfig(mailbox_address="newsletter@example.org",
                            command_endpoints=("operator@example.org",), evidence_hmac_key=b"x" * 32,
                            database_path=":memory:"), newsletter_bridge=self.bridge)
                    try:
                        with patch.object(self.bridge, resolver, side_effect=error_type("PRIVATE_SECRET")):
                            with self.assertRaises(error_type):
                                adapter.handle_push("200")
                        self.assertEqual(private.get_state("gmail_history_id"), "100")
                        self.assertEqual(private.conn.execute(
                            "SELECT count(*) FROM adapter_state WHERE value='NEWSLETTER_INPUT_REJECTED'"
                        ).fetchone()[0], 0)
                        batch = adapter.handle_push("200")
                        self.assertEqual(batch.results[0].disposition, "RECORDED")
                        self.assertEqual(private.get_state("gmail_history_id"), "200")
                    finally:
                        private.conn.close()

    def test_edition_integrity_failure_is_not_terminal_input_rejection(self):
        from entry_protocol.gmail_push_adapter import GmailInboundAdapter, GmailAdapterConfig, PrivateMailLedger

        class Inbox:
            def get_message(self, message_id):
                return raw_mail()

        private = PrivateMailLedger(":memory:")
        adapter = GmailInboundAdapter(gmail=Inbox(), store=private,
            config=GmailAdapterConfig(mailbox_address="newsletter@example.org",
                command_endpoints=("operator@example.org",), evidence_hmac_key=b"x" * 32,
                database_path=":memory:"), newsletter_bridge=self.bridge)
        self.store.db.execute("UPDATE newsletter_editions SET payload='{}'")
        self.store.db.commit()
        try:
            with self.assertRaisesRegex(ValueError, "edition integrity mismatch"):
                adapter.process_message_id("m1")
            self.assertEqual(private.conn.execute(
                "SELECT count(*) FROM adapter_state"
            ).fetchone()[0], 0)
        finally:
            private.conn.close()


if __name__ == "__main__":
    unittest.main()
