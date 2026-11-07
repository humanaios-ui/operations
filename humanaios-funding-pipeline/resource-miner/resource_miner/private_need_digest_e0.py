"""Z1 read-only private Gmail -> existing Need Graph digest bridge.

No Gmail API, credentials, networking, public write, or eligibility decisions.
Input is an operator-selected, private, allowlisted observation. The output
never includes Gmail IDs or message text. The HMAC key belongs in a private
runtime (a one-run ephemeral key was used for the bounded pilot).
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import ipaddress
import re
from urllib.parse import urlsplit

FIELDS = frozenset({"message_id", "need_id", "observed_at", "priority", "source_status", "next_action", "public_url"})
PRIORITIES = frozenset({"HIGH", "MEDIUM", "WATCH"})
SOURCE_STATES = frozenset({"EMAIL_REPORTED", "OFFICIAL_PAGE_RETRIEVED", "SOURCE_CONFLICT", "UNVERIFIED"})
ACTIONS = frozenset({"VERIFY_SOURCE", "CHECK_STATUS", "REVIEW_DEADLINE", "REVIEW_BLOCKER", "HUMAN_REVIEW", "REVIEW_NEED_GRAPH"})
NEED_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


def _public_url(url: str) -> bool:
    if not isinstance(url, str) or not url:
        return False
    try:
        p = urlsplit(url)
        if p.scheme != "https" or not p.hostname or not p.hostname.count("."):
            return False
        if p.query or p.fragment or p.username or p.password or p.port not in (None, 443):
            return False
        if any(c in url for c in ("\\", "\n", "\r", "@")) or ".." in p.path:
            return False
        try:
            ipaddress.ip_address(p.hostname)
            return False
        except ValueError:
            pass
        return not p.hostname.lower().endswith((".local", ".internal", ".test"))
    except (ValueError, AttributeError):
        return False


def _timestamp(ts: str) -> bool:
    if not isinstance(ts, str) or len(ts) > 40:
        return False
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return d.utcoffset() is not None
    except ValueError:
        return False


def project(records: list[dict], needs_graph: list[dict], hmac_key: bytes) -> dict:
    """Build a private-safe digest proposal, never an instruction or execution grant."""
    if not isinstance(records, list) or not 0 < len(records) <= 100:
        raise ValueError("bounded nonempty observations required")
    if not isinstance(needs_graph, list) or not all(isinstance(x, dict) for x in needs_graph):
        raise ValueError("invalid needs graph")
    if not isinstance(hmac_key, bytes) or len(hmac_key) < 32:
        raise ValueError("private HMAC key must be >=32 bytes")
    graph: dict[str, str] = {}
    for item in needs_graph:
        need_id, label = item.get("need_id"), item.get("label")
        if not isinstance(need_id, str) or not NEED_ID.fullmatch(need_id) or not isinstance(label, str) or not label:
            raise ValueError("invalid graph entry")
        if need_id in graph:
            raise ValueError("duplicated need graph identifier")
        graph[need_id] = label
    seen = set()
    rows = []
    dupes = 0
    for r in records:
        if not isinstance(r, dict) or set(r) != FIELDS:
            raise ValueError("private source contains missing or unapproved fields")
        message_id, need_id = r["message_id"], r["need_id"]
        if not isinstance(message_id, str) or not re.fullmatch(r"[0-9a-f]{16,32}", message_id):
            raise ValueError("invalid original private message reference")
        if not isinstance(need_id, str) or not NEED_ID.fullmatch(need_id):
            raise ValueError("invalid need identifier")
        if not _timestamp(r["observed_at"]):
            raise ValueError("invalid observed time")
        if r["priority"] not in PRIORITIES or r["source_status"] not in SOURCE_STATES or r["next_action"] not in ACTIONS:
            raise ValueError("unsupported state, priority, or action")
        url = r["public_url"]
        if url and not _public_url(url):
            raise ValueError("private, unsafe or tracking URL")
        token = hmac.new(hmac_key, message_id.encode("ascii"), hashlib.sha256).hexdigest()[:24]
        key = (token, need_id)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        mapped = need_id in graph
        state = ("NEED_GRAPH_REVIEW" if not mapped else
                 "HOLD_CONFLICT" if r["source_status"] == "SOURCE_CONFLICT" else
                 "REVIEW_NOW" if r["priority"] == "HIGH" else "WATCH")
        rows.append({
            "source_token": token, "need_id": need_id,
            "need_label": graph[need_id] if mapped else "Unmapped candidate need",
            "priority": r["priority"], "source_status": r["source_status"],
            "observed_at": r["observed_at"], "public_source_url": url or None,
            "next_action": "REVIEW_NEED_GRAPH" if not mapped else r["next_action"],
            "route": state, "origin": "PRIVATE_GMAIL_REVIEWED_PROPOSAL",
            "human_intent_verified": False, "provider_eligibility_verified": False,
            "application_submitted_inferred": False, "benefit_verified": False,
            "authority_effect": "NONE",
        })
    rows.sort(key=lambda r: ({"HIGH": 0, "MEDIUM": 1, "WATCH": 2}[r["priority"]],r["need_id"],r["source_token"]))
    return {"schema": "humanaios.private-need-digest-e0.v0.1", "source_rows": len(records),
            "unique_proposals": len(rows), "duplicate_suppressed": dupes,
            "need_graph_gaps": sum(r["route"] == "NEED_GRAPH_REVIEW" for r in rows),
            "source_conflicts": sum(r["route"] == "HOLD_CONFLICT" for r in rows),
            "authority_effect": "NONE", "records": rows}
