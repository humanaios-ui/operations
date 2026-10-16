"""Private, durable newsletter participation core. No publication or voting authority.

Identity and reply routing must be attested by the calling transport, never inferred
from From headers or prose. Public outputs use only editor-supplied edition text.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import uuid

from entry_protocol.inbound_command_processor import extract_new_text


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def classify_reply(text):
    """Bounded suggestions only; ambiguous/multiple intents require clarification."""
    patterns = {
        "UNSUBSCRIBE": r"\b(?:unsubscribe|stop emailing me|remove me from (?:the |your )?(?:list|newsletter))\b",
        "CORRECTION": r"\b(?:correction|incorrect|factual error)\b",
        "PROPOSAL": r"\b(?:suggest|propose|proposal|please change|could we|can we)\b",
        "OBJECTION": r"\b(?:object|objection|disagree|concern)\b",
        "CONSENT": r"\b(?:consent|permission|you may quote)\b",
        "QUESTION": r"\?|\b(?:why|how|what|when|where)\b",
    }
    if re.search(patterns["UNSUBSCRIBE"], text, re.I):
        return "UNSUBSCRIBE"
    found = [kind for kind, pattern in patterns.items()
             if kind != "UNSUBSCRIBE" and re.search(pattern, text, re.I)]
    # A proposal phrased as a question remains a proposal, not a vote.
    if "PROPOSAL" in found and "QUESTION" in found:
        found.remove("QUESTION")
    return found[0] if len(found) == 1 else "NEEDS_CLARIFICATION"


class NewsletterStore:
    """SQLite belongs on private durable storage, never in the public repository."""

    def __init__(self, path):
        if path != ":memory:":
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch(mode=0o600, exist_ok=True)
            p.chmod(0o600)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS newsletter_editions (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS newsletter_participants (
                id TEXT PRIMARY KEY, subscribed INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS newsletter_contributions (
                source_id TEXT PRIMARY KEY, receipt TEXT UNIQUE NOT NULL,
                edition TEXT NOT NULL REFERENCES newsletter_editions(id),
                participant TEXT NOT NULL REFERENCES newsletter_participants(id),
                text TEXT NOT NULL, kind TEXT NOT NULL, proposal TEXT,
                response TEXT NOT NULL, delivery TEXT NOT NULL DEFAULT 'PENDING');
            CREATE TABLE IF NOT EXISTS newsletter_review_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, proposal TEXT NOT NULL,
                reviewer TEXT NOT NULL, stance TEXT NOT NULL, rationale TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)

    def add_edition(self, edition_id, *, title, body, references):
        """Freeze a public-safe editorial snapshot; ID reuse never overwrites it."""
        if not re.fullmatch(r"NL-[A-Z0-9-]{1,64}", edition_id):
            raise ValueError("invalid edition ID")
        if not title.strip() or not body.strip() or not references:
            raise ValueError("title, body and evidence references required")
        payload = {"edition_id": edition_id, "title": title, "body": body,
                   "references": references, "status": "DRAFT_ONLY",
                   "publication_authorization": "NONE"}
        with self.db:
            self.db.execute("INSERT INTO newsletter_editions VALUES (?,?,?)",
                            (edition_id, json.dumps(payload), digest(payload)))
        return self.edition(edition_id)

    def edition(self, edition_id):
        row = self.db.execute("SELECT * FROM newsletter_editions WHERE id=?",
                              (edition_id,)).fetchone()
        if row is None:
            raise ValueError("unknown edition")
        payload = json.loads(row["payload"])
        if digest(payload) != row["digest"]:
            raise ValueError("edition integrity mismatch")
        return {"content": payload, "content_sha256": row["digest"]}

    def enroll(self, participant_ref):
        """Call only after explicit opt-in and transport identity verification."""
        if not re.fullmatch(r"H-[A-Za-z0-9-]{1,80}", participant_ref):
            raise ValueError("opaque human participant reference required")
        with self.db:
            self.db.execute("INSERT INTO newsletter_participants(id) VALUES (?)",
                            (participant_ref,))

    def receive(self, *, source_id, edition_id, participant_ref, body,
                identity_verified=False, automated=False):
        """Record once and prepare a bounded reply. Consent prose grants no rights."""
        if automated:
            return {"status": "IGNORED_AUTOMATION"}
        if not identity_verified:
            return {"status": "IDENTITY_VERIFICATION_REQUIRED"}
        if not isinstance(source_id, str) or not source_id or len(source_id) > 512:
            raise ValueError("source ID required")
        if not isinstance(body, str) or len(body.encode()) > 65536:
            raise ValueError("reply exceeds byte limit")
        self.edition(edition_id)
        with self.db:
            # Serialize read+write so concurrent deliveries cannot create two proposals.
            self.db.execute("BEGIN IMMEDIATE")
            previous = self.db.execute(
                "SELECT * FROM newsletter_contributions WHERE source_id=?", (source_id,)
            ).fetchone()
            if previous:
                if previous["participant"] != participant_ref or previous["edition"] != edition_id:
                    raise ValueError("source ID binding mismatch")
                return self._receipt(previous, replay=True)
            participant = self.db.execute(
                "SELECT * FROM newsletter_participants WHERE id=?", (participant_ref,)
            ).fetchone()
            if not participant:
                return {"status": "ENROLLMENT_REQUIRED"}
            if not participant["subscribed"]:
                return {"status": "UNSUBSCRIBED"}
            text = extract_new_text(body)
            kind = classify_reply(text)
            receipt = "NLC-" + uuid.uuid4().hex
            proposal = "NLP-" + uuid.uuid4().hex if kind in {"PROPOSAL", "CORRECTION", "OBJECTION"} else None
            response = {
                "QUESTION": "Your question is recorded for an evidence-backed answer. No answer is established yet.",
                "CONSENT": "Permission needs review of the exact text, attribution and scope. Nothing has been made public.",
                "UNSUBSCRIBE": "Newsletter replies and mailings are stopped for this participant.",
                "NEEDS_CLARIFICATION": "Please state one question, correction, proposed change or objection.",
            }.get(kind, "Your contribution opens a change proposal. Human review is pending; consensus is not established.")
            response += "\nReceipt: " + receipt
            if proposal:
                response += "\nProposal: " + proposal
            if kind == "UNSUBSCRIBE":
                self.db.execute("UPDATE newsletter_participants SET subscribed=0 WHERE id=?",
                                (participant_ref,))
            self.db.execute("INSERT INTO newsletter_contributions "
                            "(source_id,receipt,edition,participant,text,kind,proposal,response) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (source_id, receipt, edition_id, participant_ref, text, kind, proposal, response))
            return self._receipt(self.db.execute(
                "SELECT * FROM newsletter_contributions WHERE source_id=?", (source_id,)
            ).fetchone())

    @staticmethod
    def _receipt(row, replay=False):
        return {"status": "REPLAY" if replay else "RECORDED", "receipt_id": row["receipt"],
                "proposal_id": row["proposal"], "kind": row["kind"],
                "response": row["response"], "delivery": row["delivery"],
                "consensus": "NOT_ESTABLISHED", "publication_authorization": "NONE"}

    def claim_delivery(self, receipt_id):
        """One send attempt. An uncertain outcome needs read-back, never blind retry."""
        with self.db:
            changed = self.db.execute("UPDATE newsletter_contributions SET delivery='SENDING' "
                                      "WHERE receipt=? AND delivery='PENDING' AND "
                                      "(kind='UNSUBSCRIBE' OR participant IN "
                                      "(SELECT id FROM newsletter_participants WHERE subscribed=1))",
                                      (receipt_id,)).rowcount
        return changed == 1

    def complete_delivery(self, receipt_id, *, verified):
        with self.db:
            self.db.execute("UPDATE newsletter_contributions SET delivery=? "
                            "WHERE receipt=? AND delivery='SENDING'",
                            ("READ_BACK_VERIFIED" if verified else "OUTCOME_UNKNOWN", receipt_id))

    def export_draft(self, edition_id, directory):
        """Both channel candidates derive from identical content; no private replies."""
        edition = self.edition(edition_id)
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(edition, ensure_ascii=False, sort_keys=True, indent=2)
        for channel in ("website", "substack"):
            (target / f"{edition_id}.{channel}.json").write_text(encoded, encoding="utf-8")
        content = edition["content"]
        (target / f"{edition_id}.substack.md").write_text(
            f"# {content['title']}\n\nDRAFT — NOT PUBLISHED\n\n{content['body']}\n",
            encoding="utf-8")
        # Escape all editorial text. Raw HTML/scripts from sources never execute.
        (target / f"{edition_id}.website.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>Newsletter draft</title>"
            "<main><p>DRAFT — NOT PUBLISHED</p><h1>" + html.escape(content["title"])
            + "</h1><pre style='white-space:pre-wrap'>" + html.escape(content["body"])
            + "</pre><p>Edition: " + edition_id + "</p><p>Content SHA256: "
            + edition["content_sha256"] + "</p></main>", encoding="utf-8")
        return edition

    def record_review(self, proposal_id, *, reviewer_ref, stance, rationale,
                      identity_verified=False):
        """Append human deliberation, never infer quorum or ratification."""
        if not identity_verified or stance not in {"SUPPORT", "CONCERN", "OBJECT", "WITHDRAW"}:
            raise ValueError("verified human and explicit stance required")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 8000:
            raise ValueError("bounded rationale required")
        if not self.db.execute("SELECT 1 FROM newsletter_participants WHERE id=?",
                               (reviewer_ref,)).fetchone():
            raise ValueError("unknown human reviewer")
        if not self.db.execute("SELECT 1 FROM newsletter_contributions WHERE proposal=?",
                               (proposal_id,)).fetchone():
            raise ValueError("unknown proposal")
        with self.db:
            self.db.execute("INSERT INTO newsletter_review_events "
                            "(proposal,reviewer,stance,rationale) VALUES (?,?,?,?)",
                            (proposal_id, reviewer_ref, stance, rationale))
        return {"proposal_id": proposal_id, "consensus": "NOT_ESTABLISHED",
                "ratification": "HUMAN_PROCESS_REQUIRED", "publication_authorization": "NONE"}
