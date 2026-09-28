from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET

from ..normalize import normalize_generic, utcnow_iso

MAX_FEED_BYTES = 2 * 1024 * 1024


class FeedRejected(ValueError):
    """Raised when a feed violates Resource Miner input safety limits."""


def _text(node, names: list[str]) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _parse_feed(data: bytes) -> ET.Element:
    if len(data) > MAX_FEED_BYTES:
        raise FeedRejected(f"feed exceeds {MAX_FEED_BYTES} byte limit")
    upper = data.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise FeedRejected("DTD/entity declarations are not accepted")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise FeedRejected(f"invalid XML: {exc}") from exc


def _read_feed(response) -> bytes:
    content_length = response.headers.get("Content-Length") if getattr(response, "headers", None) else None
    if content_length:
        try:
            if int(content_length) > MAX_FEED_BYTES:
                raise FeedRejected(f"feed exceeds {MAX_FEED_BYTES} byte limit")
        except ValueError:
            pass
    data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise FeedRejected(f"feed exceeds {MAX_FEED_BYTES} byte limit")
    return data


def discover(urls: list[str]):
    observed = utcnow_iso()
    for feed_url in urls:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "HumanAIOS-ResourceMiner/0.1.1"})
        with urllib.request.urlopen(req, timeout=20) as response:
            root = _parse_feed(_read_feed(response))
        items = root.findall(".//item")
        if not items:
            items = root.findall("{http://www.w3.org/2005/Atom}entry")
        for item in items:
            title = _text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
            link = _text(item, ["link"])
            if not link:
                atom_link = item.find("{http://www.w3.org/2005/Atom}link")
                if atom_link is not None:
                    link = atom_link.attrib.get("href", "")
            desc = _text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])
            published = _text(item, ["pubDate", "published", "{http://www.w3.org/2005/Atom}published"])
            if title and link:
                yield normalize_generic(
                    title=title,
                    url=link,
                    source_name="RSS/Atom",
                    discovery_method=f"feed:{feed_url}",
                    description=desc,
                    published_at=published or None,
                    body_text=desc,
                    observed_at=observed,
                )
