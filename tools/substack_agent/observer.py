"""HPRA v0.1: offline-only Substack RSS observation and draft projection.

HumanAIOS — Builder v1.7 compliant dependency.

This module has no network client, credentials, publishing transport, or authorization
mutations. XML strings and evidence are *untrusted data*, not instructions.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

MAX_FEED_BYTES = 262_144
MAX_ENTRIES = 50
MAX_TEXT = 4000
TOOL_NAME = "hpra_offline_observer"
TOOL_VERSION = "0.1.1"
TOOL_CATEGORY = "dependency"
TOOL_ZONE = 1


class ObservationError(ValueError):
    """Invalid or untrusted observation input."""


def _url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ObservationError("invalid URL")
    try:
        parts = urlsplit(value.strip())
        host = (parts.hostname or "").lower().rstrip(".")
        if (parts.scheme != "https" or not host or parts.username
                or parts.password or parts.fragment or parts.port not in (None, 443)):
            raise ValueError("only uncredentialed HTTPS URLs are supported")
        if host == "localhost":
            raise ValueError("local targets forbidden")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("non-public targets forbidden")
    except ValueError as exc:
        raise ObservationError(str(exc)) from exc
    netloc = f"[{host}]" if ":" in host else host
    return urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, ""))


def _digest(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8")).hexdigest()


def observe_rss(xml: str, *, feed_url: str) -> dict:
    """Project an explicitly supplied public RSS payload; without fetching a URL."""
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
    """Return a digest-bound *proposal*, without publishing permission."""
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
        if e["evidence_digest"] != _digest({k: v for k, v in e.items() if k != "evidence_digest"}):
            raise ObservationError("evidence integrity mismatch")
        refs.append({"observation_id": e["observation_id"],
                     "evidence_digest": e["evidence_digest"]})
    content = {"title": title.strip(), "body": body, "references": refs}
    return {"schema_version": "hpra.draft.v0.1",
            "status": "DRAFT_ONLY", "authorization": "NONE",
            "claims_status": "REQUIRES_INDEPENDENT_VERIFICATION",
            "content": content, "content_sha256": _digest(content),
            "human_approval": None, "publication": None}


def run_smoke_test():
    sample = observe_rss('<rss><channel><item><title>Test</title>'
                         '<link>https://example.org/a</link></item></channel></rss>',
                         feed_url="https://example.org/feed")
    return len(sample["entries"]) == 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Offline observer self-test")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    raise SystemExit(0 if args.smoke_test and run_smoke_test() else 1)
