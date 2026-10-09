from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any, Callable

from ..models import EvidenceRef, ResourceMine
from ..normalize import normalize_generic, utcnow_iso

Transport = Callable[[str, dict[str, str]], Any]

DEFAULT_LABELS = {
    "bounty",
    "bug bounty",
    "reward",
    "prize",
    "grant",
    "paid",
    "paid work",
    "contract",
}


def _default_transport(url: str, headers: dict[str, str]) -> Any:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "HumanAIOS-ResourceMiner/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _repo_full_name(mine: ResourceMine) -> str:
    configured = str(mine.config.get("repository") or "").strip()
    if configured:
        return configured
    parsed = urllib.parse.urlparse(mine.canonical_url)
    path = parsed.path.strip("/")
    if parsed.hostname != "github.com" or path.count("/") != 1:
        raise ValueError("GitHub repository mine requires owner/repo")
    return path


def _labels(issue: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for row in issue.get("labels") or []:
        if isinstance(row, dict):
            name = str(row.get("name") or "").strip().casefold()
        else:
            name = str(row).strip().casefold()
        if name:
            out.add(name)
    return out


def _is_opportunity(issue: dict[str, Any], mine: ResourceMine) -> bool:
    configured = {
        str(x).strip().casefold()
        for x in mine.config.get("opportunity_labels") or []
        if str(x).strip()
    }
    labels = configured or DEFAULT_LABELS
    if _labels(issue) & labels:
        return True

    # Text matching is disabled by default because repository issues are often
    # work items rather than externally valuable resource opportunities.
    if not mine.config.get("allow_text_signals", False):
        return False
    text = " ".join(
        [str(issue.get("title") or ""), str(issue.get("body") or "")[:2000]]
    ).casefold()
    signals = [
        str(x).strip().casefold()
        for x in mine.config.get("text_signals") or []
        if str(x).strip()
    ]
    return any(signal in text for signal in signals)


def discover(
    mine: ResourceMine,
    *,
    transport: Transport = _default_transport,
):
    """Resolve high-signal issue opportunities from one configured repository."""
    observed = utcnow_iso()
    repo = _repo_full_name(mine)
    owner, name = repo.split("/", 1)
    headers = _headers()
    per_page = min(max(int(mine.config.get("per_page", 100)), 1), 100)
    max_pages = min(max(int(mine.config.get("max_pages", 2)), 1), 10)

    for page in range(1, max_pages + 1):
        params = urllib.parse.urlencode(
            {
                "state": "open",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }
        )
        url = f"https://api.github.com/repos/{owner}/{name}/issues?{params}"
        payload = transport(url, headers)
        if not isinstance(payload, list):
            raise ValueError("GitHub issues endpoint must return a list")
        if not payload:
            break

        for issue in payload:
            if not isinstance(issue, dict) or issue.get("pull_request"):
                continue
            if not _is_opportunity(issue, mine):
                continue
            html_url = str(issue.get("html_url") or "").strip()
            title = str(issue.get("title") or "").strip()
            if not html_url or not title:
                continue
            labels = sorted(_labels(issue))
            candidate = normalize_generic(
                title=title,
                url=html_url,
                source_name=repo,
                discovery_method="persistent_mine:github_repository_issue",
                description=str(issue.get("body") or "")[:1200],
                sponsor=str((issue.get("user") or {}).get("login") or owner),
                published_at=str(issue.get("created_at") or "") or None,
                tags=labels,
                body_text=str(issue.get("body") or ""),
                observed_at=observed,
                mine_name=mine.name,
                mine_url=mine.canonical_url,
                opportunity_identity=html_url,
                opportunity_kind="github_issue_opportunity",
                opportunity_source_kind="github_issue",
                raw={
                    "repository": repo,
                    "issue_number": issue.get("number"),
                    "issue_id": issue.get("id"),
                    "labels": labels,
                    "updated_at": issue.get("updated_at"),
                    "state": issue.get("state"),
                },
            )
            candidate.evidence.append(
                EvidenceRef(
                    url=html_url,
                    kind="repository_issue",
                    observed_at=observed,
                    claim="Open repository opportunity issue observed.",
                )
            )
            yield candidate

        if len(payload) < per_page:
            break
