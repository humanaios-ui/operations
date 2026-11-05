"""Read-only public evidence discovery adapter for existing Project Evidence Records.

This module is an E0 source-discovery boundary: it composes bounded search
queries and joins search-provider results to a canonical PER, but does not
fetch webpages itself or mutate a PER. Provider execution stays separately
scoped and auditable. Returned records are proposals, never verified claims.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
from datetime import date
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_RE_SPACES = re.compile(r"\s+")
_TRACKING_PREFIXES = ("utm_", "mc_", "ga_")
_TRACKING_KEYS = {"fbclid", "gclid", "msclkid", "ref", "source"}


def canonical_public_url(url: str) -> str:
    """Normalize source URL only; do not fetch it or grant URL access."""
    p = urlsplit(url.strip())
    if p.scheme.lower() not in ("https", "http") or not p.hostname or p.username or p.password:
        raise ValueError("Only ordinary public HTTP(S) URLs are accepted")
    host = p.hostname.lower()
    if host in {"localhost", "local"} or host.endswith((".local", ".internal")):
        raise ValueError("Private/local URL is not eligible")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Nonpublic IP address is not eligible")
    except ValueError as exc:
        if "not eligible" in str(exc):
            raise
    netloc = host if p.port is None else f"{host}:{p.port}"
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in _TRACKING_KEYS and not k.lower().startswith(_TRACKING_PREFIXES)]
    return urlunsplit((p.scheme.lower(), netloc, p.path.rstrip("/") or "/", urlencode(sorted(query)), ""))


def _norm(s: str) -> str:
    return _RE_SPACES.sub(" ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def _phrase_present(haystack: str, needle: str) -> bool:
    a, b = _norm(haystack), _norm(needle)
    return bool(b and len(b) >= 4 and f" {b} " in f" {a} ")


def _parsed_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def plan_public_searches(per: Mapping[str, Any], *, aliases: Iterable[str] = (), limit: int = 8) -> list[dict[str, str]]:
    """Build bounded queries from an existing PER; no network access."""
    if not str(per.get("project_id", "")).startswith("PER-"):
        raise ValueError("Canonical PER ID required")
    orgs = [str(per.get("organization", "")).strip(), *[str(a).strip() for a in aliases]]
    orgs = list(dict.fromkeys(o for o in orgs if o))
    phrases = [str(p).strip() for p in (per.get("scope", []) or []) + (per.get("execution", []) or [])]
    phrases = list(dict.fromkeys(p for p in phrases if len(p) >= 5))[:max(1, limit)]
    results = []
    for org in orgs[:2]:
        for phrase in phrases[:max(1, limit // max(len(orgs[:2]), 1))]:
            results.append({"per_id": str(per["project_id"]), "query": f'"{org}" "{phrase}" report minutes quality', "purpose": "PUBLIC_SOURCE_DISCOVERY"})
    return results[:limit]


def _tenure_relation(hit: Mapping[str, Any], bounds: Mapping[str, str]) -> str:
    event = _parsed_date(hit.get("event_date"))
    published = _parsed_date(hit.get("published_date"))
    start = _parsed_date(bounds.get("start"))
    end = _parsed_date(bounds.get("end"))
    if not start or not end or start > end:
        return "DATES_NOT_ESTABLISHED"
    date_to_test = event or published
    if date_to_test is None:
        return "DATE_UNKNOWN"
    if date_to_test < start:
        return "PRE_TENURE"
    if date_to_test > end:
        return "POST_TENURE"
    return "IN_TENURE_EVENT" if event else "PUBLISHED_DURING_TENURE"


def propose_evidence_links(
    per: Mapping[str, Any],
    search_hits: Iterable[Mapping[str, Any]],
    *,
    tenure: Mapping[str, str],
    org_aliases: Iterable[str] = (),
    person_aliases: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Join hits to a PER. All evidence links remain proposed, never promoted."""
    per_id = str(per.get("project_id", ""))
    if not per_id.startswith("PER-"):
        raise ValueError("Unknown PER identity")
    names = [str(per.get("organization", "")), *list(org_aliases)]
    people = [str(p) for p in person_aliases]
    seen = set()
    proposals = []
    for hit in search_hits:
        try:
            url = canonical_public_url(str(hit.get("url") or ""))
        except ValueError:
            continue
        source_id = hashlib.sha256((per_id + "\x00" + url).encode("utf-8")).hexdigest()[:20]
        if source_id in seen:
            continue
        seen.add(source_id)
        title = str(hit.get("title") or "").strip()[:280]
        snippet = str(hit.get("snippet") or "").strip()[:1100]
        evidence_text = f"{title} {snippet} {str(hit.get('organization') or '')}"
        org_match = any(_phrase_present(evidence_text, n) for n in names if n)
        mentions_person = any(_phrase_present(evidence_text, a) for a in people if a)
        relation = _tenure_relation(hit, tenure)
        if not org_match:
            tier = "NO_ORG_MATCH"
        elif relation in ("PRE_TENURE", "POST_TENURE"):
            tier = "OUT_OF_TENURE_CONTEXT_ONLY"
        elif mentions_person:
            tier = "NAMED_PERSON_REVIEW_REQUIRED"
        else:
            tier = "INSTITUTIONAL_CONTEXT_REVIEW_REQUIRED"
        proposals.append({
            "per_id": per_id,
            "source_id": "PER-PUB-" + source_id,
            "canonical_url": url,
            "source_title": title,
            "excerpt": snippet,
            "published_date": hit.get("published_date"),
            "event_date": hit.get("event_date"),
            "date_relation": relation,
            "organization_match": org_match,
            "person_mentioned": mentions_person,
            "evidence_tier": tier,
            "status": "PROPOSED_REVIEW_ONLY",
            "can_append_to_canonical_per": False,
            "can_publish_personal_resume_claim": False,
            "requires": ["SOURCE_READ", "PERSON_ATTRIBUTION_REVIEW", "HUMAN_APPROVAL"],
        })
    return sorted(proposals, key=lambda x: (x["per_id"], x["source_id"]))


def run_discovery(
    per: Mapping[str, Any],
    provider: Any,
    *,
    tenure: Mapping[str, str],
    org_aliases: Iterable[str] = (),
    person_aliases: Iterable[str] = (),
    query_limit: int = 8,
    hit_limit: int = 40,
) -> dict[str, Any]:
    """Use a separately authorized injected search provider; never write a PER."""
    plan = plan_public_searches(per, aliases=org_aliases, limit=query_limit)
    hits = []
    for item in plan:
        if len(hits) >= hit_limit:
            break
        batch = list(provider(item["query"]))[:hit_limit - len(hits)]
        hits.extend(batch)
    proposals = propose_evidence_links(per, hits, tenure=tenure, org_aliases=org_aliases, person_aliases=person_aliases)
    return {
        "schema": "humanaios.resource_miner.public_evidence_discovery.e0.v1",
        "per_id": str(per["project_id"]),
        "read_only": True,
        "query_plan": plan,
        "proposed_source_links": proposals,
        "authority_effect": "NONE",
        "canonical_per_mutated": False,
        "source_contents_independently_verified": False,
    }
