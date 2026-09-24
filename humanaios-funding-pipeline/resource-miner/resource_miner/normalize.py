from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import EvidenceRef, ResourceCandidate

MONEY_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*([kKmM])?\b")
DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b",
    re.I,
)
TRACKING_QUERY_KEYS = {"tracking", "gclid", "dclid", "fbclid", "msclkid", "mc_cid", "mc_eid"}

TYPE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("competition", ("challenge", "contest", "hackathon", "competition", "prize")),
    ("bounty", ("bounty", "bug bounty")),
    ("grant", ("grant", "funding opportunity", "award")),
    ("fellowship", ("fellowship",)),
    ("scholarship", ("scholarship", "tuition")),
    ("rebate", ("rebate", "incentive", "tax credit")),
    ("financing", ("loan", "line of credit", "capital access", "financing")),
    ("compute_credit", ("cloud credit", "compute credit", "gpu credit", "api credit")),
    ("free_infrastructure", ("free infrastructure", "free tier", "hosting credit", "database credit")),
    ("paid_work", ("paid work", "consulting", "paid study", "paid project")),
    ("procurement", ("rfp", "request for proposal", "procurement", "contract opportunity", "solicitation")),
    ("training", ("training", "certification", "credential")),
    ("research_access", ("dataset", "research access", "lab access", "model access")),
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_tracking_key(key: str) -> bool:
    lowered = key.lower()
    return lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS


def canonicalize_url(url: str) -> str:
    """Normalize transport noise without collapsing semantic query identity."""
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_key(key)
    ]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def stable_resource_id(url: str) -> str:
    return "RES-" + hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()[:16].upper()


def cash_mentions(text: str) -> list[float]:
    values: list[float] = []
    for amount, suffix in MONEY_RE.findall(text or ""):
        value = float(amount.replace(",", ""))
        if suffix.lower() == "k":
            value *= 1_000
        elif suffix.lower() == "m":
            value *= 1_000_000
        if value not in values:
            values.append(value)
    return values


def extract_dates(text: str) -> list[str]:
    out: list[str] = []
    for month, day, year in DATE_RE.findall(text or ""):
        try:
            parsed = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date().isoformat()
        except ValueError:
            continue
        if parsed not in out:
            out.append(parsed)
    return out


def extract_deadline(text: str) -> str | None:
    """Extract an explicit date near deadline/closing language without treating later announcement dates as deadlines."""
    if not text:
        return None
    deadline_words = re.compile(r"\b(deadline|due|ends?|closes?|apply by|submit by|submissions? due|entry period ends)\b", re.I)
    candidates: list[tuple[int, str]] = []
    for match in DATE_RE.finditer(text):
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        window = text[start:end]
        if not deadline_words.search(window):
            continue
        month, day, year = match.group(1), match.group(2), match.group(3)
        try:
            parsed = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date().isoformat()
        except ValueError:
            continue
        local_dates_start = match.start() - start
        distances = [abs(m.start() - local_dates_start) for m in deadline_words.finditer(window)]
        distance = min(distances) if distances else 9999
        candidates.append((distance, parsed))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][1]


def classify_types(text: str, tags: list[str] | None = None) -> list[str]:
    haystack = " ".join([text or "", " ".join(tags or [])]).lower()
    out = [kind for kind, needles in TYPE_RULES if any(n in haystack for n in needles)]
    return out or ["general_resource"]


def normalize_generic(
    *,
    title: str,
    url: str,
    source_name: str,
    discovery_method: str,
    description: str = "",
    sponsor: str = "",
    published_at: str | None = None,
    tags: list[str] | None = None,
    body_text: str = "",
    primary_source_url: str | None = None,
    observed_at: str | None = None,
    raw: dict[str, Any] | None = None,
) -> ResourceCandidate:
    observed_at = observed_at or utcnow_iso()
    canonical = canonicalize_url(url)
    combined = "\n".join([title, description, body_text])
    deadline = extract_deadline(combined)
    return ResourceCandidate(
        resource_id=stable_resource_id(canonical),
        title=title.strip(),
        source_name=source_name,
        source_url=url,
        canonical_url=canonical,
        discovery_method=discovery_method,
        discovered_at=observed_at,
        description=description.strip(),
        sponsor=sponsor.strip(),
        published_at=published_at,
        deadline=deadline,
        resource_types=classify_types(combined, tags),
        tags=sorted({str(x).lower() for x in (tags or []) if str(x).strip()}),
        value_text="; ".join(m.group(0) for m in MONEY_RE.finditer(combined)),
        cash_mentions_usd=cash_mentions(combined),
        primary_source_url=primary_source_url,
        evidence=[EvidenceRef(url=url, kind="discovery", observed_at=observed_at, claim="Resource candidate discovered")],
        raw=raw or {},
    )
