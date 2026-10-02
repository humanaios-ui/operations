from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from ..normalize import normalize_generic, utcnow_iso

API_ROOT = "https://api.hackerone.com/v1/hackers"
DEFAULT_PAGE_SIZE = 100
USER_AGENT = "HumanAIOS-ResourceMiner/0.2"


class HackerOneConfigError(RuntimeError):
    """Raised when HackerOne API credentials are unavailable."""


class HackerOneAPIError(RuntimeError):
    """Raised for malformed or unsuccessful HackerOne API responses."""


Transport = Callable[[str, dict[str, str]], dict[str, Any]]


def _credentials(username: str | None = None, token: str | None = None) -> tuple[str, str]:
    username = username or os.getenv("HACKERONE_API_USERNAME")
    token = token or os.getenv("HACKERONE_API_TOKEN")
    if not username or not token:
        raise HackerOneConfigError(
            "HackerOne credentials missing; set HACKERONE_API_USERNAME and HACKERONE_API_TOKEN"
        )
    return username, token


def _auth_headers(username: str, token: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    return {
        "Accept": "application/json",
        "Authorization": f"Basic {encoded}",
        "User-Agent": USER_AGENT,
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_transport(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        # Deliberately do not include request headers: they contain the API token.
        raise HackerOneAPIError(f"HackerOne GET failed for {url}: {type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise HackerOneAPIError(f"HackerOne returned non-object JSON for {url}")
    return payload


@dataclass
class HackerOneClient:
    username: str | None = None
    token: str | None = None
    transport: Transport = _default_transport

    def _headers(self) -> dict[str, str]:
        username, token = _credentials(self.username, self.token)
        return _auth_headers(username, token)

    def _get(self, path_or_url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if path_or_url.startswith("https://"):
            url = path_or_url
        else:
            path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
            url = f"{API_ROOT}{path}"
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urllib.parse.urlencode(params)}"
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "api.hackerone.com":
            raise HackerOneAPIError("Refusing HackerOne API request outside https://api.hackerone.com")
        return self.transport(url, self._headers())

    def _iter_paginated(
        self,
        path: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_pages: int = 1000,
    ) -> Iterator[dict[str, Any]]:
        size = min(max(int(page_size), 1), 100)
        page = 1
        next_url: str | None = None
        while page <= max_pages:
            payload = self._get(
                next_url or path,
                None if next_url else {"page[number]": page, "page[size]": size},
            )
            rows = payload.get("data", [])
            if not isinstance(rows, list):
                raise HackerOneAPIError("HackerOne paginated response data must be a list")
            for row in rows:
                if isinstance(row, dict):
                    yield row
            links = payload.get("links") or {}
            candidate_next = links.get("next") if isinstance(links, dict) else None
            if isinstance(candidate_next, str) and candidate_next:
                next_url = candidate_next
                page += 1
                continue
            if len(rows) < size:
                break
            page += 1
            next_url = None
        else:
            raise HackerOneAPIError("HackerOne pagination exceeded max_pages safety bound")

    def list_programs(self, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict[str, Any]]:
        return list(self._iter_paginated("/programs", page_size=page_size))

    def get_program(self, handle: str) -> dict[str, Any]:
        handle = handle.strip()
        if not handle:
            raise ValueError("HackerOne program handle is required")
        payload = self._get(f"/programs/{urllib.parse.quote(handle, safe='')}")
        row = payload.get("data")
        if not isinstance(row, dict):
            raise HackerOneAPIError("HackerOne program response missing data object")
        return row

    def get_structured_scopes(self, handle: str, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict[str, Any]]:
        handle = handle.strip()
        return list(
            self._iter_paginated(
                f"/programs/{urllib.parse.quote(handle, safe='')}/structured_scopes",
                page_size=page_size,
            )
        )

    def get_scope_exclusions(self, handle: str) -> list[dict[str, Any]]:
        handle = handle.strip()
        payload = self._get(f"/programs/{urllib.parse.quote(handle, safe='')}/scope_exclusions")
        rows = payload.get("data", [])
        if not isinstance(rows, list):
            raise HackerOneAPIError("HackerOne scope exclusions response data must be a list")
        return [row for row in rows if isinstance(row, dict)]


def _program_candidate(program: dict[str, Any], observed: str):
    attrs = program.get("attributes") or {}
    handle = str(attrs.get("handle") or "").strip()
    if not handle:
        raise HackerOneAPIError("Program object missing handle")
    name = str(attrs.get("name") or handle).strip()
    offers_bounties = attrs.get("offers_bounties") is True
    policy = str(attrs.get("policy") or "")
    submission_state = str(attrs.get("submission_state") or "unknown")
    url = f"https://hackerone.com/{handle}?type=team"
    mechanism = "bug bounty" if offers_bounties else "vulnerability disclosure program"
    description = (
        f"HackerOne {mechanism}; submission_state={submission_state}; "
        f"open_scope={attrs.get('open_scope')!s}."
    )
    candidate = normalize_generic(
        title=f"{name} — HackerOne security program",
        url=url,
        source_name="HackerOne",
        discovery_method="hackerone_hacker_api:programs",
        description=description,
        sponsor=name,
        published_at=str(attrs.get("started_accepting_at") or "") or None,
        tags=[
            "hackerone",
            "security-research",
            "bug-bounty" if offers_bounties else "vulnerability-disclosure",
            f"submission-state:{submission_state}",
        ],
        body_text=f"{mechanism}\n{policy}",
        observed_at=observed,
        raw=program,
    )
    if offers_bounties and "bounty" not in candidate.resource_types:
        candidate.resource_types.append("bounty")
    return candidate


def discover(
    handles: list[str] | None = None,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    client: HackerOneClient | None = None,
):
    """Discover HackerOne programs only. This performs no target requests."""
    client = client or HackerOneClient()
    observed = utcnow_iso()
    if handles:
        programs = [client.get_program(handle) for handle in handles]
    else:
        programs = client.list_programs(page_size=page_size)
    for program in programs:
        yield _program_candidate(program, observed)
