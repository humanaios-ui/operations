"""HPRA v0.1: offline-only Substack RSS observation and draft projection.

This module has no network client, credentials, publishing transport, or authorization
mutations. XML strings and evidence are *untrusted data*, never instructions.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

MAX_FEED_BYTES = 262_144
MAX_ENTRIES = 50
MAX_TEXT = 4000


class ObservationError(ValueError):
    """Invalid or untrusted observation input."""


def _url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ObservationError("invalid URL")
    parts = urlsplit(value.strip())
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.fragment or parts.port not in (None, 443)):
        raise ObservationError("only uncredentialed HTTPS URLs are supported")
    if parts.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise ObservationError("local targets forbidden")
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, ""))


def _digest(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8")).hexdigest()


def observe_rss(xml: str, *, feed_url: str) -> dict:
    """Project an explicitly supplied public RSS payload; never fetch a URL."""
    origin = _url(feed_url)
    if not isinstance(xml, str) or len(xml.encode("utf-8")) > MAX_FEED_BYTES:
        raise ObservationError("feed exceeds byte limit")
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        raise ObservationError("DTD/entities forbidden")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ObservationError("malformed XML") from exc
    if root.tag != "rss" or root.find("channel") is None:
        raise ObservationError("expected RSS channel")
    items = root.findall("./channel/item")
    if len(items) > MAX_ENTRIES:
        raise ObservationError("entry limit exceeded")
    observations = []
    seen = set()
    for item in items:
        link = _url((item.findtext("link") or "").strip())
        title = (item.findtext("title") or "").strip()[:MAX_TEXT]
        published = (item.findtext("pubDate") or "").strip()[:200]
        if not title or link in seen:
            continue
        seen.add(link)
        record = {
            "source": "substack_public_rss",
            "feed_url": origin,
            "url": link,
            "title": title,
            "published_unverified": published,
            "trust": "UNTRUSTED_EXTERNAL_TEXT",
            "authorization": "OBSERVATION_ONLY",
            "status": "OBSERVED_UNVERIFIED",
        }
        record["observation_id"] = "hpra:" + _digest([origin, link])
        record["evidence_digest"] = _digest(record)
        observations.append(record)
    return {"schema_version": "hpra.observations.v0.1",
            "authorization": "OBSERVATION_ONLY", "entries": observations,
            "feed_digest": hashlib.sha256(xml.encode("utf-8")).hexdigest()}


def propose_draft(*, title: str, body: str, evidence: list[dict]) -> dict:
    """Return a digest-bound *proposal*, never publishing permission."""
    if not isinstance(title, str) or not title.strip() or len(title) > 250:
        raise ObservationError("invalid title")
    if not isinstance(body, str) or not body.strip() or len(body) > 30_000:
        raise ObservationError("invalid body")
    if not isinstance(evidence, list) or not evidence:
        raise ObservationError("evidence required")
    refs = []
    for e in evidence:
        if (not isinstance(e, dict) or
                e.get("status") != "OBSERVED_UNVERIFIED" or
                e.get("authorization") != "OBSERVATION_ONLY" or
                not isinstance(e.get("observation_id"), str) or
                not isinstance(e.get("evidence_digest"), str)):
            raise ObservationError("invalid evidence reference")
        refs.append({"observation_id": e["observation_id"],
                     "evidence_digest": e["evidence_digest"]})
    content = {"title": title.strip(), "body": body, "references": refs}
    return {"schema_version": "hpra.draft.v0.1",
            "status": "DRAFT_ONLY", "authorization": "NONE",
            "claims_status": "REQUIRES_INDEPENDENT_VERIFICATION",
            "content": content, "content_sha256": _digest(content),
            "human_approval": None, "publication": None}
