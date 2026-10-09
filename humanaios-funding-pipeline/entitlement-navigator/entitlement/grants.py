from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

SEARCH_URL = "https://api.grants.gov/v1/api/search2"
FETCH_URL = "https://api.grants.gov/v1/api/fetchOpportunity"


class GrantsGovError(RuntimeError):
    pass


def search(keyword: str, rows: int = 25, statuses: str = "posted|forecasted") -> dict[str, Any]:
    """Search the public Grants.gov API. No API key is required for search2."""
    payload = json.dumps(
        {
            "rows": max(1, min(int(rows), 100)),
            "keyword": keyword.strip(),
            "oppStatuses": statuses,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        SEARCH_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "EntitlementNavigator/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GrantsGovError(f"Grants.gov search failed: {exc}") from exc


def normalized_hits(api_response: dict[str, Any]) -> list[dict[str, Any]]:
    hits = api_response.get("data", {}).get("oppHits", []) or []
    out = []
    for h in hits:
        out.append(
            {
                "id": h.get("id"),
                "number": h.get("number"),
                "title": h.get("title"),
                "agency": h.get("agencyName") or h.get("agencyCode"),
                "open_date": h.get("openDate"),
                "close_date": h.get("closeDate"),
                "status": h.get("oppStatus"),
                "aln": h.get("alnist", []),
                "classification": "GENERAL_OPPORTUNITY",
                "eligibility_assessed": False,
                "note": "Discovered from Grants.gov. Applicant eligibility has not yet been deterministically established.",
            }
        )
    return out
