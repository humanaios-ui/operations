"""Consent-gated, read-only public-profile discovery for an owner-controlled portfolio.

Inputs: committed private master (via private_profile_bridge), bounded public
search observations supplied by Resource Miner, and optional direct API probes
for GitHub/ORCID. No authentication credentials, contact emails, phone numbers,
cross-platform identity inference, automated claiming, edits or account recovery.
Nothing is persisted. Callers must keep outputs private.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

SCHEMA = "humanaios.profile-presence-review.v0.1"
MAX_CANDIDATES = 30
MAX_PUBLIC_BYTES = 65536
KNOWN_PROVIDERS = frozenset({"github", "linkedin", "orcid", "substack", "x", "huggingface"})
ALLOWED_SOCIAL_KEYS = KNOWN_PROVIDERS
SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,59}$")
ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$")
PROVIDER_DOMAIN = {
    "github": "github.com", "linkedin": "www.linkedin.com",
    "orcid": "orcid.org", "substack": "substack.com",
    "x": "x.com", "huggingface": "huggingface.co",
}


def canonical_profile_url(provider: str, url: str) -> str:
    """Only known public profile paths. Reject queries, redirects and arbitrary hosts."""
    if provider not in KNOWN_PROVIDERS or not isinstance(url, str) or len(url) > 300:
        raise ValueError("unapproved public-profile provider or URL")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        raise ValueError("profile reference must be a plain HTTPS URL")
    if parsed.query or parsed.fragment or parsed.hostname is None:
        raise ValueError("profile reference contains ambiguous or private parameters")
    host = parsed.hostname.lower()
    parts = parsed.path.strip("/").split("/")
    if provider == "github":
        if host != "github.com" or len(parts) != 1 or not SEGMENT.fullmatch(parts[0]):
            raise ValueError("unsupported GitHub profile")
        # Repository paths are not personal-account identity records.
        return "https://github.com/" + parts[0].casefold()
    if provider == "orcid":
        if host != "orcid.org" or len(parts) != 1 or not ORCID.fullmatch(parts[0]):
            raise ValueError("unsupported ORCID profile")
        return "https://orcid.org/" + parts[0]
    if provider == "linkedin":
        if host not in {"www.linkedin.com", "linkedin.com"} or len(parts) != 2 or parts[0] != "in" or not SEGMENT.fullmatch(parts[1]):
            raise ValueError("unsupported LinkedIn member profile")
        return "https://www.linkedin.com/in/" + parts[1].casefold()
    if provider == "huggingface":
        if host != "huggingface.co" or len(parts) != 1 or not SEGMENT.fullmatch(parts[0]):
            raise ValueError("unsupported Hugging Face profile")
        return "https://huggingface.co/" + parts[0]
    if provider == "x":
        if host not in {"x.com", "twitter.com"} or len(parts) != 1 or not SEGMENT.fullmatch(parts[0]):
            raise ValueError("unsupported X profile")
        return "https://x.com/" + parts[0].casefold()
    if provider == "substack":
        if len(parts) == 1 and host == "substack.com" and parts[0].startswith("@") and SEGMENT.fullmatch(parts[0][1:]):
            return "https://substack.com/@" + parts[0][1:].casefold()
        if host.endswith(".substack.com") and host.count(".") == 2 and parsed.path in ("", "/"):
            label = host.removesuffix(".substack.com")
            if SEGMENT.fullmatch(label):
                return "https://" + host + "/"
    raise ValueError("unsupported public profile reference")


def approved_seed_profiles(master: dict[str, Any], *, owner_approved: bool) -> list[dict[str, str]]:
    if not owner_approved:
        raise PermissionError("public-profile discovery requires explicit owner consent")
    if not isinstance(master.get("contact"), dict):
        raise ValueError("master missing contact section")
    social = master["contact"].get("social") or {}
    if not isinstance(social, dict):
        raise ValueError("master social record must be a map")
    out: list[dict[str, str]] = []
    for provider in sorted(KNOWN_PROVIDERS):
        candidate = social.get(provider) or (social.get("twitter") if provider == "x" else None)
        if not candidate:
            continue
        try:
            url = canonical_profile_url(provider, candidate)
        except ValueError:
            # Do not turn a stale/unsafe URL into an unbounded network fetch.
            out.append({
                "provider": provider, "url": "",
                "state": "INVALID_SEED_NEEDS_OWNER_REVIEW",
                "ownership": "NOT_ESTABLISHED",
            })
            continue
        out.append({
            "provider": provider, "url": url, "state": "OWNER_RECORDED_LINK",
            "ownership": "NOT_INDEPENDENTLY_AUTHENTICATED",
        })
    return out


def reconcile_public_candidates(
    seeds: list[dict[str, str]],
    observations: list[dict[str, Any]],
    *,
    owner_approved: bool,
) -> dict[str, Any]:
    """Review bounded external search results. Matching name or URL is not proof of ownership."""
    if not owner_approved:
        raise PermissionError("candidate review requires owner consent")
    if not isinstance(observations, list) or len(observations) > MAX_CANDIDATES:
        raise ValueError("too many search observations")
    known = {(row["provider"], row["url"]) for row in seeds if row.get("url")}
    seen: set[tuple[str, str]] = set()
    candidates = []
    invalid = 0
    for row in observations:
        if not isinstance(row, dict) or set(row) != {"provider", "url", "source_id"}:
            raise ValueError("observation must include provider, URL and source ID only")
        provider, source_id = row["provider"], row["source_id"]
        if not isinstance(source_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,79}", source_id):
            raise ValueError("invalid non-sensitive source ID")
        try:
            url = canonical_profile_url(provider, row["url"])
        except (TypeError, ValueError):
            invalid += 1
            continue
        key = (provider, url)
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "provider": provider,
            "url": url,
            "source_id": source_id,
            "state": "KNOWN_LINK_REOBSERVED" if key in known else "UNRECOGNIZED_PUBLIC_PROFILE_CANDIDATE",
            "ownership": "NOT_ESTABLISHED_BY_PUBLIC_SEARCH",
            "next_action": "OWNER_REVIEW",
        })
    return {
        "schema": SCHEMA,
        "authority_effect": "NONE",
        "automatic_claims": 0,
        "automatic_account_updates": 0,
        "invalid_source_count": invalid,
        "candidates": candidates,
        "status": "REVIEW_REQUIRED",
    }


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _get_public(url: str) -> tuple[int, bytes]:
    opener = build_opener(_NoRedirect)
    request = Request(url, method="GET", headers={
        "Accept": "application/json",
        "User-Agent": "HumanAIOS-OwnerProfileReadOnly/0.1",
    })
    with opener.open(request, timeout=8) as response:
        payload = response.read(MAX_PUBLIC_BYTES + 1)
        if len(payload) > MAX_PUBLIC_BYTES:
            raise ValueError("public response too large")
        return response.status, payload


def public_readback(
    seeds: list[dict[str, str]], *, owner_approved: bool,
    transport: Callable[[str], tuple[int, bytes]] = _get_public,
) -> list[dict[str, str]]:
    """Public read-only API probes for GitHub and ORCID only.

    LinkedIn and other platforms require an approved separate adapter or manual
    evidence. A successful API response proves that a record exists, not its owner.
    """
    if not owner_approved:
        raise PermissionError("public readback requires owner consent")
    result = []
    for seed in seeds:
        provider, original = seed["provider"], seed.get("url", "")
        if not original or provider not in {"github", "orcid"}:
            result.append({"provider": provider, "state": "REVIEW_ONLY_NO_AUTOMATED_PROBE"})
            continue
        canonical = canonical_profile_url(provider, original)
        identifier = canonical.rsplit("/", 1)[-1]
        url = (
            "https://api.github.com/users/" + identifier
            if provider == "github"
            else "https://pub.orcid.org/v3.0/" + identifier + "/record"
        )
        try:
            status, payload = transport(url)
            if status != 200 or len(payload) > MAX_PUBLIC_BYTES:
                state = "READBACK_INCONCLUSIVE"
            else:
                record = json.loads(payload.decode("utf-8"))
                if not isinstance(record, dict):
                    state = "READBACK_INCONCLUSIVE"
                elif provider == "github" and str(record.get("login", "")).casefold() == identifier.casefold():
                    state = "PUBLIC_RECORD_OBSERVED"
                elif provider == "orcid" and str(record.get("orcid-identifier", {}).get("path", "")) == identifier:
                    state = "PUBLIC_RECORD_OBSERVED"
                else:
                    state = "READBACK_INCONCLUSIVE"
        except (ValueError, OSError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
            state = "READBACK_FAILED"
        result.append({
            "provider": provider, "state": state,
            "ownership": "NOT_ESTABLISHED_BY_PUBLIC_READBACK",
        })
    return result


def observe_owner_presence(master: dict[str, Any], *,
                           owner_approved: bool,
                           observations: list[dict[str, Any]] | None = None,
                           probe_public: bool = False,
                           transport: Callable[[str], tuple[int, bytes]] = _get_public,
                           ) -> dict[str, Any]:
    """Single explicit read. Never auto-register a public candidate."""
    seeds = approved_seed_profiles(master, owner_approved=owner_approved)
    candidates = reconcile_public_candidates(
        seeds, observations or [], owner_approved=owner_approved
    )
    return {
        "schema": SCHEMA, "seed_links": seeds,
        "candidate_review": candidates,
        "public_readback": (
            public_readback(seeds, owner_approved=owner_approved, transport=transport)
            if probe_public else []
        ),
        "network_probed": bool(probe_public),
        "authority_effect": "NONE",
        "raw_master_exported": False,
        "owner_confirmation_required": True,
        "output_visibility": "PRIVATE_LOCAL_ONLY",
    }
