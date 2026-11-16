"""Offline-only, evidence-first news observations for Resource Miner issue #1238.

This module never fetches URLs, stores article bodies, invokes Witness, or creates
ResourceCandidates. Importing it has no network or authentication side effects.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .normalize import canonicalize_url

MAX_BATCH = 100
MAX_FIXTURE_BYTES = 256 * 1024
MAX_TITLE = 360
MAX_URL = 1200
SAFE_QUERY_KEYS = frozenset({
    "id", "article", "article_id", "p", "page", "story", "story_id",
    "nid", "news_id",
})
TRACKING_KEYS = frozenset({"gclid", "fbclid", "msclkid", "mc_cid", "mc_eid"})


class NewsObservationRejected(ValueError):
    """Invalid, unsafe, or out-of-scope news fixture."""


def _bounded_fixture(payload: object, key: str) -> list[dict]:
    if not isinstance(payload, dict):
        raise NewsObservationRejected("Expected a mapping fixture")
    try:
        size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise NewsObservationRejected("Fixture must be JSON compatible") from exc
    if size > MAX_FIXTURE_BYTES:
        raise NewsObservationRejected("Fixture exceeds byte budget")
    items = payload.get(key)
    if not isinstance(items, list) or len(items) > MAX_BATCH:
        raise NewsObservationRejected("Fixture records missing or over limit")
    if not all(isinstance(item, dict) for item in items):
        raise NewsObservationRejected("Every record must be a mapping")
    return items


def _timestamp(value: object, *, required: bool = False) -> str | None:
    if value in (None, ""):
        if required:
            raise NewsObservationRejected("Observation time is required")
        return None
    if not isinstance(value, str) or len(value) > 48:
        if required:
            raise NewsObservationRejected("Invalid observation time")
        return None
    try:
        # Event Registry/GDELT DOC API often uses compact UTC dates for 'seen'.
        if re.fullmatch(r"\d{8}T\d{6}Z", value):
            parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
            return parsed.isoformat() + "Z"
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed.isoformat()
    except ValueError as exc:
        if required:
            raise NewsObservationRejected("Invalid observation time") from exc
        return None


def _plain_title(value: object) -> str:
    if not isinstance(value, str):
        raise NewsObservationRejected("Title must be text")
    title = value.strip()
    if not title or len(title) > MAX_TITLE or "<" in title or ">" in title:
        raise NewsObservationRejected("Title invalid or contains markup")
    if any(ord(ch) < 32 for ch in title):
        raise NewsObservationRejected("Title contains control characters")
    return title


def _public_url(value: object) -> str:
    if not isinstance(value, str) or not 8 <= len(value) <= MAX_URL:
        raise NewsObservationRejected("Public URL missing or oversized")
    try:
        parts = urlsplit(value)
        host = (parts.hostname or "").lower().rstrip(".")
        if (parts.scheme != "https" or not host or "." not in host
                or parts.username is not None or parts.password is not None
                or parts.port not in (None, 443)
                or host.endswith((".local", ".internal", ".localhost", ".test", ".invalid"))
                or any(ord(c) < 32 for c in value)):
            raise NewsObservationRejected("Public HTTPS URL required")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            # E0 deliberately refuses IP literals, including public IPs.
            raise NewsObservationRejected("IP literals cannot be source URLs")
        cleaned_query = []
        for key, val in parse_qsl(parts.query, keep_blank_values=True):
            lowered = key.lower()
            if lowered.startswith("utm_") or lowered in TRACKING_KEYS:
                continue
            if lowered not in SAFE_QUERY_KEYS:
                raise NewsObservationRejected("Unapproved URL query parameter")
            if len(val) > 120:
                raise NewsObservationRejected("URL query value too long")
            cleaned_query.append((key, val))
        safe = urlunsplit(("https", host, parts.path or "/", urlencode(cleaned_query), ""))
        return canonicalize_url(safe)
    except ValueError as exc:
        if isinstance(exc, NewsObservationRejected):
            raise
        raise NewsObservationRejected("Invalid URL") from exc


def _observation(provider: str, item: dict, observed_at: str) -> dict:
    title = _plain_title(item.get("title"))
    canonical = _public_url(item.get("url"))
    # GDELT 'seendate' and Miniflux 'published_at' are different clocks.
    published = _timestamp(item.get("published_at")) if provider == "Miniflux" else None
    seen = _timestamp(item.get("seendate")) if provider == "GDELT" else None
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    # Never carry 'content', feed credentials, raw HTML, or unsupported claims.
    return {
        "schema": "humanaios.news_observation.e0.v1",
        "kind": "SOURCE_OBSERVATION",
        "source_provider": provider,
        "source_url": canonical,
        "source_identity_sha256": digest,
        "title": title,
        "published_at": published,
        "provider_seen_at": seen,
        "observed_at": observed_at,
        "verification_state": "UNVERIFIED",
        "event_state": "NOT_ASSESSED",
        "resource_candidate": False,
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }


def parse_gdelt_fixture(payload: object, *, observed_at: str) -> list[dict]:
    """Parse already-acquired GDELT DOC article-list JSON; no HTTP calls."""
    timestamp = _timestamp(observed_at, required=True)
    return [_observation("GDELT", item, timestamp)
            for item in _bounded_fixture(payload, "articles")]


def parse_miniflux_fixture(payload: object, *, observed_at: str) -> list[dict]:
    """Parse already-acquired Miniflux entries JSON; no credentials/API calls."""
    timestamp = _timestamp(observed_at, required=True)
    return [_observation("Miniflux", item, timestamp)
            for item in _bounded_fixture(payload, "entries")]


def group_exact_url_duplicates(observations: list[dict]) -> list[dict]:
    """Group exact public canonical URL matches; never infer a common event."""
    if not isinstance(observations, list) or len(observations) > MAX_BATCH * 2:
        raise NewsObservationRejected("Observation batch invalid or too large")
    groups: dict[str, list[dict]] = {}
    for row in observations:
        if (not isinstance(row, dict)
                or row.get("schema") != "humanaios.news_observation.e0.v1"
                or row.get("kind") != "SOURCE_OBSERVATION"
                or row.get("resource_candidate") is not False
                or row.get("authority_effect") != "NONE"
                or row.get("execution") != "DISABLED"):
            raise NewsObservationRejected("Only non-authorizing E0 observations allowed")
        canonical = _public_url(row.get("source_url"))
        groups.setdefault(canonical, []).append(row)
    return [
        {
            "canonical_url": url,
            "observation_count": len(members),
            "providers": sorted({member["source_provider"] for member in members}),
            "relationship": "EXACT_URL_MATCH" if len(members) > 1 else "SINGLE_OBSERVATION",
            "event_claim": "NOT_ASSESSED",
            "verification_state": "UNVERIFIED",
            "authority_effect": "NONE",
        }
        for url, members in sorted(groups.items())
    ]
