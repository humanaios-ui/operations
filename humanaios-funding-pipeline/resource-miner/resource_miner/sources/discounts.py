"""Bounded official-source discount discovery; observations never prove entitlement."""
from __future__ import annotations

import hashlib
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

from ..models import EvidenceRef
from ..normalize import normalize_generic

MAX_BYTES = 524288
OFFERS = (
    ("startup", "https://www.coderabbit.ai/startup-program", "CodeRabbit startup discount",
     ("50%", "6 months", "annual", "accelerator"),
     "50% off Team for six months; annual commitment; VC/accelerator backing and funding below $25M required. Confirm full invoice and renewal with provider."),
    ("annual", "https://www.coderabbit.ai/pricing", "CodeRabbit annual billing",
     ("20%", "annual"),
     "Annual billing discount; annual commitment. Seat count, full invoice, renewal and stacking need confirmation."),
    ("oss", "https://kb.coderabbit.ai/articles/8856795235-how-do-i-activate-coderabbit-pro-for-my-open-source-project",
     "CodeRabbit free public-repository reviews", ("public", "free", "rate limits"),
     "Free public-repository reviews, subject to limits. Paid chat/MCP entitlement must be checked separately."),
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused")


def fetch(url):
    if url not in {row[1] for row in OFFERS}:
        raise ValueError("source is not allowlisted")
    request = urllib.request.Request(url, headers={"User-Agent": "HumanAIOS-ResourceMiner/discount-pilot"})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=8) as response:
        body = response.read(MAX_BYTES + 1)
        return {"status": response.status, "final_url": response.geturl(),
                "content_type": response.headers.get("Content-Type", ""), "body": body}


class _Text(HTMLParser):
    """Ignore comments and explicitly hidden/script/style/template content."""
    def __init__(self):
        super().__init__()
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = bool(self.stack and self.stack[-1][1]) or tag in {"script", "style", "template", "noscript"}
        hidden = hidden or "hidden" in attrs or attrs.get("aria-hidden") == "true"
        style = re.sub(r"\s", "", attrs.get("style", "")).lower()
        hidden = hidden or "display:none" in style or "visibility:hidden" in style
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, hidden))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def compare_quotes(*, offer_cents, baseline_cents, same_scope=False):
    """Compare complete USD quotes for identical seats, term, and features only."""
    if not same_scope:
        return {"state": "NOT_COMPARABLE", "savings_cents": None}
    if any(type(x) is not int or x < 0 for x in (offer_cents, baseline_cents)):
        raise ValueError("complete nonnegative integer-cent quotes required")
    savings = baseline_cents - offer_cents
    return {"state": "LOWER_COST" if savings > 0 else "NO_SAVINGS", "savings_cents": savings}


def discover(*, transport=fetch, now=None):
    """On-demand GETs only. No arbitrary URLs, checkout, credentials, or code testing."""
    observed = (now or datetime.now(timezone.utc)).isoformat()
    for kind, url, title, markers, terms in OFFERS:
        metadata = {"vendor": "CodeRabbit", "offer_kind": kind, "source_kind": "OFFICIAL_ENDPOINT",
                    "observed_at": observed, "verification": "SOURCE_UNAVAILABLE",
                    "coupon_code": None, "code_status": "NOT_TESTED", "eligibility": "UNASSESSED",
                    "terms": terms, "renewal": "UNVERIFIED", "stacking": "UNVERIFIED",
                    "total_commitment_cents": None, "baseline": "FREE_PUBLIC_REPO_REVIEWS",
                    "savings": {"state": "NOT_COMPARABLE", "savings_cents": None}}
        try:
            result = transport(url)
            body = result["body"]
            if not isinstance(body, bytes) or len(body) > MAX_BYTES:
                raise ValueError("invalid or oversized response")
            if result["status"] != 200 or result["final_url"] != url:
                raise ValueError("unexpected response or redirect")
            if "text/html" not in result["content_type"].lower():
                raise ValueError("expected HTML")
            parser = _Text()
            parser.feed(body.decode("utf-8", errors="replace"))
            text = " ".join(" ".join(parser.parts).split()).casefold()
            metadata["content_sha256"] = hashlib.sha256(body).hexdigest()
            metadata["verification"] = "TERMS_RECHECK_REQUIRED"
            if all(marker.casefold() in text for marker in markers):
                metadata["verification"] = "OFFER_TEXT_OBSERVED"
        except (OSError, ValueError, KeyError, TypeError) as exc:
            metadata["error_type"] = type(exc).__name__
        candidate = normalize_generic(title=title, url=url, source_name="CodeRabbit official discount pilot",
                                      discovery_method="official_discount_endpoint", sponsor="CodeRabbit",
                                      description=f"{metadata['verification']}. Candidate terms to recheck: {terms}",
                                      observed_at=observed, tags=["software", "discount", "independent validation"],
                                      primary_source_url=url)
        candidate.resource_types = ["discount" if kind != "oss" else "free_infrastructure"]
        candidate.resource_affordances = ["software_cost_reduction"]
        candidate.cash_mentions_usd = []  # A funding cap is not a cash award.
        candidate.discount_offer = metadata
        candidate.status = "UNVERIFIED"
        candidate.source_verification_status = "RECHECK_REQUIRED"
        candidate.evidence = [EvidenceRef(url=url, kind="discount_observation", observed_at=observed,
                                         claim=f"{metadata['verification']}; no eligibility or redemption verified")]
        yield candidate
