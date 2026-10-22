from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from ..normalize import normalize_generic, utcnow_iso

API = "https://dev.to/api/articles"


def _get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "HumanAIOS-ResourceMiner/0.1"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def discover(tags: list[str] | None = None, per_page: int = 30, hydrate: bool = True):
    observed = utcnow_iso()
    seen: set[int] = set()
    for tag in (tags or ["devchallenge"]):
        query = urllib.parse.urlencode({"tag": tag, "per_page": min(max(per_page, 1), 100)})
        rows = _get_json(f"{API}?{query}")
        for article in rows if isinstance(rows, list) else []:
            article_id = article.get("id")
            if not isinstance(article_id, int) or article_id in seen:
                continue
            seen.add(article_id)
            organization = (article.get("organization") or {}).get("username", "")
            title = str(article.get("title") or "")
            tag_list = article.get("tag_list") or []
            if organization != "devteam" and not any(x in title.lower() for x in ("join the", "challenge", "hackathon", "contest")):
                continue
            detail = article
            if hydrate:
                try:
                    detail = _get_json(f"{API}/{article_id}")
                except Exception:
                    detail = article
            body = str(detail.get("body_markdown") or "")
            url = str(article.get("url") or "")
            if not url:
                continue
            yield normalize_generic(
                title=title,
                url=url,
                source_name="DEV Community",
                discovery_method=f"devto_api:tag={tag}",
                description=str(article.get("description") or ""),
                sponsor=str((article.get("organization") or {}).get("name") or ""),
                published_at=str(article.get("published_at") or "") or None,
                tags=[str(x) for x in tag_list],
                body_text=body,
                observed_at=observed,
                raw=detail,
            )
