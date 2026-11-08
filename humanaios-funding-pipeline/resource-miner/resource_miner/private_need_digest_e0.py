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
        # Mail-supplied URLs are untrusted. E0 permits *origin-only* citations;
        # path segments may hold tracking tokens or private message IDs.
        if (p.path not in ("", "/") or p.query or p.fragment or p.username
                or p.password or p.port not in (None, 443)):
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
    """Read-only, order-independent private proposal projection.

    Identical observations deduplicate. Differing observations for one
    message+need are not silently dropped: they become a SOURCE_CONFLICT hold.
    The projection never includes raw Gmail IDs, bodies or mail URL paths.
    """
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

    # Keys contain only a keyed digest and an allowlisted need ID. The key is
    # supplied by the private runtime; never ship or persist it in public CI.
    groups: dict[tuple[str, str], set[tuple[str, str, str, str, str]]] = {}
    duplicate_count = 0
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
        if (r["priority"] not in PRIORITIES or r["source_status"] not in SOURCE_STATES
                or r["next_action"] not in ACTIONS):
            raise ValueError("unsupported state, priority, or action")
        url = r["public_url"]
        if not isinstance(url, str) or (url and not _public_url(url)):
            raise ValueError("private, unsafe or tracking URL")
        token = hmac.new(hmac_key, message_id.encode("ascii"), hashlib.sha256).hexdigest()[:24]
        key = (token, need_id)
        value = (r["observed_at"], r["priority"], r["source_status"], r["next_action"], url)
        observations = groups.setdefault(key, set())
        if value in observations:
            duplicate_count += 1
        observations.add(value)

    def chronological(ts: str) -> tuple[datetime, str]:
        # Normalise offset-aware timestamps to avoid lexicographic date errors.
        from datetime import timezone
        return (datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc), ts)

    rows = []
    conflicting_groups = 0
    for (token, need_id), observations in groups.items():
        disputed = len(observations) > 1
        if disputed:
            conflicting_groups += 1
        mapped = need_id in graph
        status = "SOURCE_CONFLICT" if disputed else next(iter(observations))[2]
        priority = min((o[1] for o in observations), key={"HIGH": 0, "MEDIUM": 1, "WATCH": 2}.__getitem__)
        observed_at = max((o[0] for o in observations), key=chronological)
        urls = {o[4] for o in observations}
        # Disagreement about a public source URL must not choose one arbitrarily.
        public_url = urls.pop() if len(urls) == 1 else ""
        if status == "SOURCE_CONFLICT":
            route, action = "HOLD_CONFLICT", "VERIFY_SOURCE"
        elif not mapped:
            route, action = "NEED_GRAPH_REVIEW", "REVIEW_NEED_GRAPH"
        else:
            route, action = ("REVIEW_NOW" if priority == "HIGH" else "WATCH"), next(iter(observations))[3]

        rows.append({
            "source_token": token,
            "need_id": need_id,
            "need_label": graph[need_id] if mapped else "Unmapped candidate need",
            "need_graph_gap": not mapped,
            "priority": priority,
            "source_status": status,
            "source_conflict": status == "SOURCE_CONFLICT",
            "observed_at": observed_at,
            "public_source_url": public_url or None,
            "next_action": action,
            "route": route,
            "origin": "PRIVATE_GMAIL_REVIEWED_PROPOSAL",
            "human_intent_verified": False,
            "provider_eligibility_verified": False,
            "application_submitted_inferred": False,
            "benefit_verified": False,
            "authority_effect": "NONE",
        })
    rows.sort(key=lambda r: (
        {"HIGH": 0, "MEDIUM": 1, "WATCH": 2}[r["priority"]],
        r["need_id"], r["source_token"],
    ))
    return {
        "schema": "humanaios.private-need-digest-e0.v0.1",
        "source_rows": len(records),
        "unique_proposals": len(rows),
        "duplicate_suppressed": duplicate_count,
        "conflicting_observation_groups": conflicting_groups,
        "need_graph_gaps": sum(r["need_graph_gap"] for r in rows),
        "source_conflicts": sum(r["source_conflict"] for r in rows),
        "authority_effect": "NONE",
        "records": rows,
    }
