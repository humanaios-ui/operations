"""Newsletter hook for the existing Gmail ingress, with injected verified bindings.

The resolver is a trusted private identity service, not a model or From-header
lookup. It returns (human participant ref, originating verified endpoint) only
for authenticated, opted-in thread participants. No resolver means no processing.
"""
from email.message import EmailMessage

from entry_protocol.gmail_push_adapter import parse_gmail_message, normalize_address


class NewsletterGmailBridge:
    def __init__(self, *, store, gmail, mailbox, resolve_identity, resolve_edition,
                 send_enabled=False):
        self.store = store
        self.gmail = gmail
        self.mailbox = normalize_address(mailbox)
        self.resolve_identity = resolve_identity
        self.resolve_edition = resolve_edition
        self.send_enabled = send_enabled

    def process_message(self, raw):
        """Return None for non-newsletter threads so existing digest handling runs."""
        parsed = parse_gmail_message(raw)
        edition_id = self.resolve_edition(parsed.gmail_thread_id)
        if not edition_id:
            return None
        headers = {h["name"].lower(): h.get("value", "")
                   for h in raw.get("payload", {}).get("headers", [])}
        if (parsed.automation_generated or headers.get("x-humanaios-newsletter")
                or headers.get("auto-submitted", "no").lower() != "no"
                or headers.get("precedence", "").lower() in {"bulk", "list", "junk"}
                or parsed.from_address == self.mailbox):
            return {"status": "IGNORED_AUTOMATION"}
        identity = self.resolve_identity(raw)
        if not identity:
            return {"status": "IDENTITY_VERIFICATION_REQUIRED"}
        participant, endpoint = identity
        if normalize_address(endpoint) != parsed.from_address:
            return {"status": "IDENTITY_VERIFICATION_REQUIRED"}
        result = self.store.receive(source_id=parsed.gmail_message_id,
                                    edition_id=edition_id, participant_ref=participant,
                                    body=parsed.body_text, identity_verified=True)
        if result["status"] not in {"RECORDED", "REPLAY"} or not self.send_enabled:
            return result
        if not parsed.rfc_message_id or not self.store.claim_delivery(result["receipt_id"]):
            return result
        message = EmailMessage()
        message["From"] = self.mailbox
        message["To"] = endpoint
        message["Subject"] = "Re: HumanAIOS Newsletter " + edition_id
        message["In-Reply-To"] = parsed.rfc_message_id
        message["References"] = parsed.rfc_message_id
        message["Auto-Submitted"] = "auto-replied"
        message["X-HumanAIOS-Newsletter"] = result["receipt_id"]
        message.set_content(result["response"])
        verified = False
        try:
            sent = self.gmail.send_message(raw_message=message.as_bytes(),
                                           thread_id=parsed.gmail_thread_id)
            readback = self.gmail.get_message(sent["id"])
            check = parse_gmail_message(readback)
            returned_headers = {h["name"].lower(): h.get("value", "")
                                for h in readback.get("payload", {}).get("headers", [])}
            verified = (check.body_text.strip() == result["response"].strip()
                        and check.to_addresses == (normalize_address(endpoint),)
                        and returned_headers.get("x-humanaios-newsletter") == result["receipt_id"])
        except Exception:
            # A timeout can follow a successful send. Do not send a duplicate.
            verified = False
        self.store.complete_delivery(result["receipt_id"], verified=verified)
        return {**result, "delivery": "READ_BACK_VERIFIED" if verified else "OUTCOME_UNKNOWN"}
