from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from ..normalize import normalize_generic, utcnow_iso

API = "https://api.github.com/search/issues"


def discover(queries: list[str], per_query: int = 30):
    observed = utcnow_iso()
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "HumanAIOS-ResourceMiner/0.1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for query in queries:
        params = urllib.parse.urlencode({"q": query, "per_page": min(max(per_query, 1), 100), "sort": "updated", "order": "desc"})
        req = urllib.request.Request(f"{API}?{params}", headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for issue in payload.get("items", []):
            if issue.get("pull_request"):
                continue
            title = str(issue.get("title") or "")
            body = str(issue.get("body") or "")
            url = str(issue.get("html_url") or "")
            labels = [str(x.get("name")) for x in issue.get("labels", []) if isinstance(x, dict)]
            if not url or not title:
                continue
            yield normalize_generic(
                title=title,
                url=url,
                source_name="GitHub Issues",
                discovery_method=f"github_search:{query}",
                description=body[:800],
                sponsor=str((issue.get("user") or {}).get("login") or ""),
                published_at=str(issue.get("created_at") or "") or None,
                tags=labels,
                body_text=body,
                observed_at=observed,
                raw=issue,
            )
