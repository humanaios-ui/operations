from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET

from ..normalize import normalize_generic, utcnow_iso


def _text(node, names: list[str]) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def discover(urls: list[str]):
    observed = utcnow_iso()
    for feed_url in urls:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "HumanAIOS-ResourceMiner/0.1"})
        with urllib.request.urlopen(req, timeout=20) as response:
            root = ET.fromstring(response.read())
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
