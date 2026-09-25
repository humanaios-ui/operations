"""Private Gmail push adapter for the HumanAIOS Daily Digest message board.

Phase B: Gmail Pub/Sub/history transport -> private evidence ledger ->
InboundCommandProcessor -> optional child-thread acknowledgement.

This module is intentionally split from the public research projection:
raw Gmail identifiers and human-authored command text remain in the private
SQLite ledger. Public Git receipts must use CommandEvent.public_projection().

No deployment is performed by importing this module. Gmail watch registration,
credentials, Pub/Sub configuration, and outbound sending are runtime actions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from html.parser import HTMLParser
import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable, Mapping, Protocol, Sequence

from entry_protocol.inbound_command_processor import (
    ActorKind,
    CommandEvent,
    CommandKind,
    InboundCommandProcessor,
    ResolutionState,
    ThreadState,
)


AUTOMATION_HEADER = "X-HumanAIOS-Automation"
AUTOMATION_HEADER_VALUE = "digest-gmail-adapter-v1"

_DIGEST_SUBJECT_RE = re.compile(
    r"^(?:re:\s*)?HumanAIOS Daily Digest\b", re.I
)
_THREAD_SUBJECT_RE = re.compile(
    r"^(?:re:\s*)?THREAD\s+([A-Z0-9-]+)(?:\s+[—-]\s+(.+?))?(?:\s+[—-]\s+(?:NEW|ACTIVE|PAUSED|WAITING|BLOCKED|CLOSED))?\s*$",
    re.I,
)
_ITEM_ID_RE = re.compile(
    r"\b(?:"
    r"RM-\d{8}-\d{2}|CURR-\d{8}-\d{2}|MOVE-\d{8}-\d{2}|RQ-\d{8}-\d{2}|"
    r"FL-\d{8}-\d{2}|EPQ-\d{8}-\d{2}|PR-\d+|HARC-[A-Z0-9-]+|Q-[A-Z0-9-]+"
    r")\b",
    re.I,
)
_ITEM_LINE_RE = re.compile(
    r"ITEM_ID\s*:\s*([A-Z0-9-]+).*?"
    r"(?:TASK|ACTION|TESTABLE QUESTION|WORKFLOW)\s*:\s*([^|\n]+)",
    re.I,
)


class HistoryExpired(RuntimeError):
    """Gmail no longer retains the requested history baseline."""


class GmailTransportError(RuntimeError):
    """Gmail transport/API operation failed."""


class GmailClient(Protocol):
    user_id: str

    def register_watch(
        self,
        *,
        topic_name: str,
        label_ids: Sequence[str] = ("INBOX",),
    ) -> Mapping[str, Any]:
        ...

    def list_added_message_ids(
        self,
        *,
        start_history_id: str,
        label_id: str = "INBOX",
    ) -> tuple[list[str], str]:
        ...

    def get_message(self, message_id: str) -> Mapping[str, Any]:
        ...

    def get_thread(self, thread_id: str) -> Mapping[str, Any]:
        ...

    def send_message(
        self,
        *,
        raw_message: bytes,
        thread_id: str | None = None,
    ) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class GmailAdapterConfig:
    mailbox_address: str
    command_endpoints: tuple[str, ...]
    evidence_hmac_key: bytes
    database_path: str
    send_enabled: bool = False
    acknowledgement_to: str | None = None

    def __post_init__(self) -> None:
        if len(self.evidence_hmac_key) < 32:
            raise ValueError("evidence_hmac_key must contain at least 32 bytes")
        if not self.mailbox_address.strip():
            raise ValueError("mailbox_address is required")
        if not self.command_endpoints:
            raise ValueError("at least one command endpoint is required")

    @classmethod
    def from_env(cls) -> "GmailAdapterConfig":
        key_b64 = os.environ.get("MAIL_EVIDENCE_HMAC_KEY_B64", "").strip()
        if not key_b64:
            raise RuntimeError("MAIL_EVIDENCE_HMAC_KEY_B64 is required")
        try:
            key = base64.b64decode(key_b64, validate=True)
        except Exception as exc:
            raise RuntimeError("MAIL_EVIDENCE_HMAC_KEY_B64 must be valid base64") from exc

        mailbox = os.environ.get("GMAIL_USER_ID", "").strip()
        raw_endpoints = os.environ.get("HUMAN_COMMAND_ENDPOINTS", "").strip()
        endpoints = tuple(
            normalize_address(value)
            for value in raw_endpoints.split(",")
            if normalize_address(value)
        )
        return cls(
            mailbox_address=normalize_address(mailbox),
            command_endpoints=endpoints,
            evidence_hmac_key=key,
            database_path=os.environ.get(
                "MAIL_PRIVATE_LEDGER_PATH",
                "/data/humanaios-mail-ledger.sqlite3",
            ),
            send_enabled=os.environ.get("GMAIL_SEND_ENABLED", "0") == "1",
            acknowledgement_to=normalize_address(
                os.environ.get("GMAIL_ACK_TO", mailbox)
            ),
        )


@dataclass(frozen=True)
class ParsedGmailMessage:
    gmail_message_id: str
    gmail_thread_id: str
    label_ids: tuple[str, ...]
    from_address: str
    to_addresses: tuple[str, ...]
    subject: str
    rfc_message_id: str | None
    references: str | None
    automation_generated: bool
    body_text: str


@dataclass(frozen=True)
class AdapterEventResult:
    status: str
    target_item_id: str | None = None
    thread_state: str | None = None
    disposition: str | None = None
    authority_level: str | None = None
    outbound_status: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class PushBatchResult:
    status: str
    start_history_id: str | None
    end_history_id: str | None
    processed: int
    ignored: int
    replays: int
    held: int
    results: tuple[AdapterEventResult, ...] = ()


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(self.parts)


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    _, addr = parseaddr(value)
    return (addr or value).strip().lower()


def _header_map(payload: Mapping[str, Any]) -> dict[str, str]:
    headers = payload.get("headers") or []
    out: dict[str, str] = {}
    for item in headers:
        name = str(item.get("name", "")).strip().lower()
        if name:
            out[name] = str(item.get("value", ""))
    return out


def _decode_b64url(value: str | None) -> str:
    if not value:
        return ""
    padded = value + "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode(
            "utf-8", errors="replace"
        )
    except Exception:
        return ""


def _collect_mime_parts(part: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    plain: list[str] = []
    html: list[str] = []
    mime_type = str(part.get("mimeType", "")).lower()
    body = part.get("body") or {}
    data = body.get("data")

    if data:
        decoded = _decode_b64url(str(data))
        if mime_type == "text/plain":
            plain.append(decoded)
        elif mime_type == "text/html":
            html.append(decoded)

    for child in part.get("parts") or []:
        child_plain, child_html = _collect_mime_parts(child)
        plain.extend(child_plain)
        html.extend(child_html)
    return plain, html


def decode_message_body(payload: Mapping[str, Any]) -> str:
    plain, html_parts = _collect_mime_parts(payload)
    if plain:
        return "\n".join(x for x in plain if x.strip()).strip()
    if html_parts:
        parser = _HTMLTextExtractor()
        parser.feed("\n".join(html_parts))
        return parser.text().strip()

    body = payload.get("body") or {}
    return _decode_b64url(body.get("data")).strip()


def parse_gmail_message(message: Mapping[str, Any]) -> ParsedGmailMessage:
    payload = message.get("payload") or {}
    headers = _header_map(payload)
    recipients = tuple(
        normalize_address(part)
        for part in headers.get("to", "").split(",")
        if normalize_address(part)
    )
    return ParsedGmailMessage(
        gmail_message_id=str(message.get("id", "")),
        gmail_thread_id=str(message.get("threadId", "")),
        label_ids=tuple(str(x) for x in message.get("labelIds") or []),
        from_address=normalize_address(headers.get("from")),
        to_addresses=recipients,
        subject=headers.get("subject", "").strip(),
        rfc_message_id=headers.get("message-id") or None,
        references=headers.get("references") or None,
        automation_generated=(
            headers.get(AUTOMATION_HEADER.lower(), "") == AUTOMATION_HEADER_VALUE
        ),
        body_text=decode_message_body(payload),
    )


def is_relevant_subject(subject: str) -> bool:
    # The root Daily Digest is data, never a command. Only a reply to it is
    # command-eligible. THREAD roots are allowed, but adapter-generated roots
    # are separately rejected by the automation header.
    return bool(_DIGEST_REPLY_RE.match(subject or "") or _THREAD_SUBJECT_RE.match(subject or ""))


def extract_subject_target(subject: str) -> tuple[str | None, str | None]:
    match = _THREAD_SUBJECT_RE.match(subject or "")
    if not match:
        return None, None
    item_id = match.group(1).upper()
    title = (match.group(2) or "").strip(" —-")
    return item_id, title or None


def extract_item_catalog(text: str) -> dict[str, str]:
    """Extract visible digest item IDs and nearby human-readable labels."""
    catalog: dict[str, str] = {}
    if not text:
        return catalog

    for match in _ITEM_LINE_RE.finditer(text):
        catalog[match.group(1).upper()] = match.group(2).strip()

    lines = text.splitlines()
    for index, line in enumerate(lines):
        ids = _ITEM_ID_RE.findall(line)
        for item_id in ids:
            key = item_id.upper()
            if key in catalog:
                continue
            cleaned = line
            cleaned = re.sub(r"(?i)ITEM_ID\s*:\s*", "", cleaned)
            cleaned = re.sub(re.escape(item_id), "", cleaned, flags=re.I)
            cleaned = cleaned.strip(" -*—|:\t")
            if cleaned:
                catalog[key] = cleaned[:240]
                continue
            if index + 1 < len(lines):
                next_line = lines[index + 1].strip(" -*—|:\t")
                if next_line:
                    catalog[key] = next_line[:240]
    return catalog


def decode_pubsub_notification(envelope: Mapping[str, Any]) -> tuple[str, str, str | None]:
    message = envelope.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("Pub/Sub envelope missing message")
    data = message.get("data")
    if not isinstance(data, str) or not data:
        raise ValueError("Pub/Sub message missing data")
    padded = data + "=" * (-len(data) % 4)
    try:
        decoded = base64.b64decode(padded).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as exc:
        raise ValueError("invalid Pub/Sub Gmail notification payload") from exc

    email_address = normalize_address(str(payload.get("emailAddress", "")))
    history_id = str(payload.get("historyId", "")).strip()
    if not email_address or not history_id:
        raise ValueError("Gmail notification missing emailAddress/historyId")
    return email_address, history_id, str(message.get("messageId") or "") or None


class PrivateMailLedger:
    """Private durable state. Never publish this SQLite file or its rows to Git."""

    def __init__(self, path: str) -> None:
        self.path = path
        db_path = Path(path)
        if db_path.parent and str(db_path.parent) not in ("", "."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        if path != ":memory:":
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS adapter_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mail_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail_message_id TEXT NOT NULL UNIQUE,
                gmail_thread_id TEXT NOT NULL,
                private_event_ref TEXT NOT NULL UNIQUE,
                actor_kind TEXT NOT NULL,
                transport_status TEXT NOT NULL,
                subject TEXT NOT NULL,
                human_span TEXT NOT NULL,
                body_commitment TEXT NOT NULL,
                event_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS item_threads (
                item_id TEXT PRIMARY KEY,
                title TEXT,
                state TEXT NOT NULL,
                child_gmail_thread_id TEXT,
                child_root_message_id TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def get_state(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM adapter_state WHERE key = ?", (key,)
        ).fetchone()
        return str(row["value"]) if row else None

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO adapter_state(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )
        self.conn.commit()

    def has_message(self, gmail_message_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM mail_events WHERE gmail_message_id = ?",
            (gmail_message_id,),
        ).fetchone()
        return bool(row)

    def thread_states(self) -> dict[str, ThreadState]:
        rows = self.conn.execute("SELECT item_id, state FROM item_threads").fetchall()
        return {
            str(row["item_id"]): ThreadState(str(row["state"]))
            for row in rows
        }

    def get_thread(self, item_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM item_threads WHERE item_id = ?",
            (item_id.upper(),),
        ).fetchone()

    def upsert_thread(
        self,
        *,
        item_id: str,
        title: str | None,
        state: str,
        child_gmail_thread_id: str | None = None,
        child_root_message_id: str | None = None,
    ) -> None:
        current = self.get_thread(item_id)
        child_thread = (
            child_gmail_thread_id
            if child_gmail_thread_id is not None
            else (str(current["child_gmail_thread_id"]) if current and current["child_gmail_thread_id"] else None)
        )
        child_root = (
            child_root_message_id
            if child_root_message_id is not None
            else (str(current["child_root_message_id"]) if current and current["child_root_message_id"] else None)
        )
        retained_title = title or (
            str(current["title"]) if current and current["title"] else None
        )
        self.conn.execute(
            """
            INSERT INTO item_threads(
                item_id, title, state, child_gmail_thread_id, child_root_message_id
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                title = excluded.title,
                state = excluded.state,
                child_gmail_thread_id = excluded.child_gmail_thread_id,
                child_root_message_id = excluded.child_root_message_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                item_id.upper(),
                retained_title,
                state,
                child_thread,
                child_root,
            ),
        )
        self.conn.commit()

    def record_event(
        self,
        *,
        parsed: ParsedGmailMessage,
        private_event_ref: str,
        actor_kind: str,
        transport_status: str,
        human_span: str,
        body_commitment: str,
        event: CommandEvent,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO mail_events(
                gmail_message_id, gmail_thread_id, private_event_ref,
                actor_kind, transport_status, subject, human_span,
                body_commitment, event_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                parsed.gmail_message_id,
                parsed.gmail_thread_id,
                private_event_ref,
                actor_kind,
                transport_status,
                parsed.subject,
                human_span,
                body_commitment,
                json.dumps(asdict(event), sort_keys=True),
            ),
        )
        self.conn.commit()


class GoogleGmailClient:
    """Thin Gmail API v1 client using an already-authorized OAuth refresh token."""

    SCOPES = (
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    )

    def __init__(self, service: Any, *, user_id: str) -> None:
        self.service = service
        self.user_id = user_id or "me"

    @classmethod
    def from_env(cls) -> "GoogleGmailClient":
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError(
                "google-api-python-client and google-auth are required for live Gmail"
            ) from exc

        client_id = os.environ.get("GMAIL_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "").strip()
        refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN", "").strip()
        if not (client_id and client_secret and refresh_token):
            raise RuntimeError(
                "GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REFRESH_TOKEN are required"
            )

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=list(cls.SCOPES),
        )
        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )
        return cls(
            service,
            user_id=os.environ.get("GMAIL_API_USER_ID", "me").strip() or "me",
        )

    def register_watch(
        self,
        *,
        topic_name: str,
        label_ids: Sequence[str] = ("INBOX",),
    ) -> Mapping[str, Any]:
        body = {
            "topicName": topic_name,
            "labelIds": list(label_ids),
            "labelFilterBehavior": "include",
        }
        return (
            self.service.users()
            .watch(userId=self.user_id, body=body)
            .execute()
        )

    def list_added_message_ids(
        self,
        *,
        start_history_id: str,
        label_id: str = "INBOX",
    ) -> tuple[list[str], str]:
        try:
            page_token: str | None = None
            message_ids: list[str] = []
            seen: set[str] = set()
            latest_history_id = start_history_id
            while True:
                response = (
                    self.service.users()
                    .history()
                    .list(
                        userId=self.user_id,
                        startHistoryId=start_history_id,
                        historyTypes=["messageAdded"],
                        labelId=label_id,
                        pageToken=page_token,
                    )
                    .execute()
                )
                latest_history_id = str(
                    response.get("historyId", latest_history_id)
                )
                for history in response.get("history") or []:
                    for added in history.get("messagesAdded") or []:
                        message = added.get("message") or {}
                        message_id = str(message.get("id", ""))
                        if message_id and message_id not in seen:
                            seen.add(message_id)
                            message_ids.append(message_id)
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
            return message_ids, latest_history_id
        except Exception as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status == 404:
                raise HistoryExpired(
                    "Gmail history baseline expired or is no longer available"
                ) from exc
            raise GmailTransportError("Gmail history.list failed") from exc

    def get_message(self, message_id: str) -> Mapping[str, Any]:
        try:
            return (
                self.service.users()
                .messages()
                .get(userId=self.user_id, id=message_id, format="full")
                .execute()
            )
        except Exception as exc:
            raise GmailTransportError("Gmail messages.get failed") from exc

    def get_thread(self, thread_id: str) -> Mapping[str, Any]:
        try:
            return (
                self.service.users()
                .threads()
                .get(userId=self.user_id, id=thread_id, format="full")
                .execute()
            )
        except Exception as exc:
            raise GmailTransportError("Gmail threads.get failed") from exc

    def send_message(
        self,
        *,
        raw_message: bytes,
        thread_id: str | None = None,
    ) -> Mapping[str, Any]:
        encoded = base64.urlsafe_b64encode(raw_message).decode("ascii")
        body: dict[str, Any] = {"raw": encoded}
        if thread_id:
            body["threadId"] = thread_id
        try:
            return (
                self.service.users()
                .messages()
                .send(userId=self.user_id, body=body)
                .execute()
            )
        except Exception as exc:
            raise GmailTransportError("Gmail messages.send failed") from exc


class GmailInboundAdapter:
    def __init__(
        self,
        *,
        gmail: GmailClient,
        store: PrivateMailLedger,
        config: GmailAdapterConfig,
    ) -> None:
        self.gmail = gmail
        self.store = store
        self.config = config

    def _hmac(self, domain: str, value: str) -> str:
        return hmac.new(
            self.config.evidence_hmac_key,
            f"{domain}:{value}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _private_event_ref(self, gmail_message_id: str) -> str:
        return "MAIL-" + self._hmac("event", gmail_message_id)[:24].upper()

    def _body_commitment(self, human_span: str) -> str:
        return self._hmac("body", human_span)

    def register_watch(
        self,
        *,
        topic_name: str,
        label_ids: Sequence[str] = ("INBOX",),
        acknowledge_resync_gap: bool = False,
    ) -> Mapping[str, Any]:
        if (
            self.store.get_state("gmail_resync_required") == "1"
            and not acknowledge_resync_gap
        ):
            raise GmailTransportError(
                "resync gap is unresolved; rerun watch registration only after "
                "manual gap review with acknowledge_resync_gap=True"
            )
        response = self.gmail.register_watch(
            topic_name=topic_name,
            label_ids=label_ids,
        )
        history_id = str(response.get("historyId", "")).strip()
        expiration = str(response.get("expiration", "")).strip()
        if not history_id:
            raise GmailTransportError("Gmail watch response omitted historyId")
        self.store.set_state("gmail_history_id", history_id)
        if expiration:
            self.store.set_state("gmail_watch_expiration_ms", expiration)
        self.store.set_state("gmail_resync_required", "0")
        return response

    def _catalog_from_thread(
        self,
        *,
        parsed: ParsedGmailMessage,
        current_message_id: str,
    ) -> dict[str, str]:
        subject_target, subject_title = extract_subject_target(parsed.subject)
        if subject_target:
            return {subject_target: subject_title or subject_target}

        if not _DIGEST_SUBJECT_RE.match(parsed.subject):
            return {}

        thread = self.gmail.get_thread(parsed.gmail_thread_id)
        messages = thread.get("messages") or []
        # Most recent prior digest is the best catalog source.
        for raw in reversed(messages):
            if str(raw.get("id", "")) == current_message_id:
                continue
            candidate = parse_gmail_message(raw)
            if (
                not _DIGEST_SUBJECT_RE.match(candidate.subject)
                or candidate.subject.lower().startswith("re:")
            ):
                continue
            catalog = extract_item_catalog(candidate.body_text)
            if catalog:
                return catalog
        return {}

    def _transport_actor(self, parsed: ParsedGmailMessage) -> tuple[ActorKind, str]:
        # Initial Phase B authority is deliberately narrow: an actionable human
        # command must be present as a Gmail SENT copy from a configured endpoint.
        # A matching From: header without SENT is not sufficient proof of control.
        if (
            parsed.from_address in self.config.command_endpoints
            and "SENT" in parsed.label_ids
        ):
            return ActorKind.HUMAN, "CONFIGURED_ENDPOINT_SENT_COPY"
        if parsed.from_address in self.config.command_endpoints:
            return ActorKind.UNKNOWN, "CONFIGURED_ENDPOINT_UNATTESTED"
        return ActorKind.UNKNOWN, "UNRECOGNIZED_ENDPOINT"

    def _send_mail(
        self,
        *,
        subject: str,
        body: str,
        thread_id: str | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> Mapping[str, Any]:
        message = EmailMessage()
        message["From"] = self.config.mailbox_address
        message["To"] = self.config.acknowledgement_to or self.config.mailbox_address
        message["Subject"] = subject
        message[AUTOMATION_HEADER] = AUTOMATION_HEADER_VALUE
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = (
                f"{references} {in_reply_to}".strip()
                if references
                else in_reply_to
            )
        message.set_content(body)
        return self.gmail.send_message(
            raw_message=message.as_bytes(),
            thread_id=thread_id,
        )

    def _acknowledge(
        self,
        *,
        parsed: ParsedGmailMessage,
        event: CommandEvent,
        title: str | None,
    ) -> str:
        if not self.config.send_enabled:
            return "OUTBOUND_DISABLED"

        target = event.target_item_id
        if not target:
            return "NO_TARGET"

        state = event.proposed_state
        held = event.execution_disposition == "HOLD_FOR_HUMAN_AUTHORITY"
        body = "\n".join(
            [
                f"ITEM_ID: {target}",
                f"STATE: {state}",
                f"COMMAND: {event.command_kind}",
                f"AUTHORITY: {event.authority_level}",
                f"DISPOSITION: {event.execution_disposition}",
                "",
                (
                    "The requested consequential action is held for explicit human authority; "
                    "no merge/deploy/publish/submit/purchase/account action was executed."
                    if held
                    else "Thread state recorded by the private Gmail adapter."
                ),
                "",
                "Reply naturally or use: STATUS, PAUSE, RESUME, or CLOSE with this ITEM_ID.",
            ]
        )

        if (
            event.command_kind == CommandKind.BEGIN_THREAD.value
            and event.execution_disposition == "Z1_PROPOSED_TRANSITION"
        ):
            response = self._send_mail(
                subject=f"THREAD {target} — {title or target} — {state}",
                body=body,
            )
            child_thread_id = str(response.get("threadId", "")) or None
            child_message_id = str(response.get("id", "")) or None
            self.store.upsert_thread(
                item_id=target,
                title=title,
                state=state,
                child_gmail_thread_id=child_thread_id,
                child_root_message_id=child_message_id,
            )
            return "CHILD_THREAD_SENT"

        self._send_mail(
            subject=(
                parsed.subject
                if parsed.subject.lower().startswith("re:")
                else f"Re: {parsed.subject}"
            ),
            body=body,
            thread_id=parsed.gmail_thread_id or None,
            in_reply_to=parsed.rfc_message_id,
            references=parsed.references,
        )
        return "ACK_SENT"

    def process_message_id(self, message_id: str) -> AdapterEventResult:
        if self.store.has_message(message_id):
            return AdapterEventResult(status="REPLAY")

        raw = self.gmail.get_message(message_id)
        parsed = parse_gmail_message(raw)

        if parsed.automation_generated:
            return AdapterEventResult(status="IGNORED", detail="automation-generated")
        if not is_relevant_subject(parsed.subject):
            return AdapterEventResult(status="IGNORED", detail="unrelated-subject")

        actor_kind, transport_status = self._transport_actor(parsed)
        catalog = self._catalog_from_thread(
            parsed=parsed,
            current_message_id=message_id,
        )
        subject_target, subject_title = extract_subject_target(parsed.subject)
        if subject_target and subject_target not in catalog:
            catalog[subject_target] = subject_title or subject_target

        processor = InboundCommandProcessor(catalog)
        processor.thread_states = self.store.thread_states()

        private_event_ref = self._private_event_ref(parsed.gmail_message_id)
        event = processor.process(
            private_event_ref=private_event_ref,
            raw_body=parsed.body_text,
            actor_kind=actor_kind,
        )

        # Processor performs quote/signature suppression. Persist the exact new
        # human-authored span privately for reconstruction, never public Git.
        from entry_protocol.inbound_command_processor import extract_new_text
        human_span = extract_new_text(parsed.body_text)

        title = catalog.get(event.target_item_id or "")
        if event.target_item_id:
            self.store.upsert_thread(
                item_id=event.target_item_id,
                title=title,
                state=event.proposed_state,
            )

        self.store.record_event(
            parsed=parsed,
            private_event_ref=private_event_ref,
            actor_kind=actor_kind.value,
            transport_status=transport_status,
            human_span=human_span,
            body_commitment=self._body_commitment(human_span),
            event=event,
        )

        outbound = "NOT_APPLICABLE"
        if actor_kind is ActorKind.HUMAN and event.target_item_id:
            outbound = self._acknowledge(
                parsed=parsed,
                event=event,
                title=title,
            )

        return AdapterEventResult(
            status="PROCESSED",
            target_item_id=event.target_item_id,
            thread_state=event.proposed_state,
            disposition=event.execution_disposition,
            authority_level=event.authority_level,
            outbound_status=outbound,
        )

    def handle_push(self, notification_history_id: str) -> PushBatchResult:
        start = self.store.get_state("gmail_history_id")
        if self.store.get_state("gmail_resync_required") == "1":
            return PushBatchResult(
                status="RESYNC_REQUIRED",
                start_history_id=start,
                end_history_id=None,
                processed=0,
                ignored=0,
                replays=0,
                held=0,
            )
        if not start:
            # Correct deployment seeds this through register_watch(). Fail closed:
            # establish a baseline but do not claim the triggering message was read.
            self.store.set_state("gmail_history_id", notification_history_id)
            self.store.set_state("gmail_resync_required", "1")
            return PushBatchResult(
                status="BASELINE_MISSING_RESYNC_REQUIRED",
                start_history_id=None,
                end_history_id=notification_history_id,
                processed=0,
                ignored=0,
                replays=0,
                held=0,
            )

        try:
            message_ids, end = self.gmail.list_added_message_ids(
                start_history_id=start,
                label_id="INBOX",
            )
        except HistoryExpired:
            self.store.set_state("gmail_resync_required", "1")
            return PushBatchResult(
                status="HISTORY_EXPIRED_RESYNC_REQUIRED",
                start_history_id=start,
                end_history_id=None,
                processed=0,
                ignored=0,
                replays=0,
                held=0,
            )

        results: list[AdapterEventResult] = []
        for message_id in message_ids:
            results.append(self.process_message_id(message_id))

        # Advance only after the full batch returns; retries are idempotent because
        # processed message IDs are private-ledger unique.
        self.store.set_state("gmail_history_id", end or notification_history_id)
        self.store.set_state("gmail_resync_required", "0")

        return PushBatchResult(
            status="PROCESSED",
            start_history_id=start,
            end_history_id=end or notification_history_id,
            processed=sum(r.status == "PROCESSED" for r in results),
            ignored=sum(r.status == "IGNORED" for r in results),
            replays=sum(r.status == "REPLAY" for r in results),
            held=sum(r.disposition == "HOLD_FOR_HUMAN_AUTHORITY" for r in results),
            results=tuple(results),
        )


def _build_live_adapter() -> GmailInboundAdapter:
    config = GmailAdapterConfig.from_env()
    return GmailInboundAdapter(
        gmail=GoogleGmailClient.from_env(),
        store=PrivateMailLedger(config.database_path),
        config=config,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="HumanAIOS Gmail adapter control")
    sub = parser.add_subparsers(dest="command", required=True)

    watch = sub.add_parser("watch", help="Register/renew Gmail Pub/Sub watch")
    watch.add_argument(
        "--topic",
        default=os.environ.get("GMAIL_PUBSUB_TOPIC", ""),
        help="projects/<project>/topics/<topic>",
    )
    watch.add_argument(
        "--acknowledge-resync-gap",
        action="store_true",
        help="explicitly establish a new baseline after manual review of a known gap",
    )

    status = sub.add_parser("status", help="Print private adapter state summary")

    args = parser.parse_args()
    adapter = _build_live_adapter()

    if args.command == "watch":
        if not args.topic:
            parser.error("--topic or GMAIL_PUBSUB_TOPIC is required")
        response = adapter.register_watch(
            topic_name=args.topic,
            acknowledge_resync_gap=args.acknowledge_resync_gap,
        )
        print(
            json.dumps(
                {
                    "historyId": response.get("historyId"),
                    "expiration": response.get("expiration"),
                    "send_enabled": adapter.config.send_enabled,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "status":
        print(
            json.dumps(
                {
                    "history_id_present": bool(
                        adapter.store.get_state("gmail_history_id")
                    ),
                    "watch_expiration_ms": adapter.store.get_state(
                        "gmail_watch_expiration_ms"
                    ),
                    "resync_required": adapter.store.get_state(
                        "gmail_resync_required"
                    ),
                    "send_enabled": adapter.config.send_enabled,
                    "thread_count": len(adapter.store.thread_states()),
                },
                indent=2,
            )
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
