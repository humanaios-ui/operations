"""Three real, permitted Resource Miner sources. Passive experiment only.

Uses the existing funding, DEV public API and GitHub public-issue adapters,
plus canonical ResourceCandidate/Need Graph routing. It cannot authorize actions.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlsplit

from resource_miner.cli import DEFAULT_FUNDING, DEFAULT_NEEDS, DEFAULT_REQUIREMENTS
from resource_miner.miner import enrich
from resource_miner.sources import funding_pipeline, devto, github

SOURCES = ("funding", "devto", "github")
PROVIDER_NAMES = {
    "funding": "HumanAIOS Funding Pipeline",
    "devto": "DEV Community",
    "github": "GitHub Issues",
}

def public_source(url, provider):
    if not isinstance(url, str) or len(url) > 2000:
        return False
    try:
        p = urlsplit(url)
        host = (p.hostname or "").lower().rstrip(".")
        if (p.scheme != "https" or not host or p.username or p.password or
                p.port not in (None, 443) or "." not in host or
                host.endswith((".local", ".localhost", ".internal", ".invalid", ".test"))):
            return False
        if provider == "devto":
            return host == "dev.to"
        if provider == "github":
            return host == "github.com" and "/issues/" in p.path
        return not host.replace(".", "").isdigit()
    except ValueError:
        return False

def benefit_kind(types):
    kinds = set(types)
    if "bounty" in kinds: return "CONTINGENT_BOUNTY"
    if "paid_work" in kinds: return "POSSIBLE_WAGES"
    if "competition" in kinds: return "CONTINGENT_PRIZE"
    if kinds.intersection(("grant", "fellowship")): return "RESTRICTED_FUNDING"
    if kinds.intersection(("compute_credit", "free_infrastructure", "api_access")):
        return "NONCASH_CAPACITY"
    if "financing" in kinds: return "BORROWED_CAPITAL"
    return "UNCLASSIFIED"

def screen(row, as_of):
    provider = next((key for key, val in PROVIDER_NAMES.items()
                     if val == row.source_name), None)
    if not provider or not public_source(row.source_url, provider):
        return None
    deadline = row.deadline
    expired = row.route == "ARCHIVE" or row.status == "CLOSED_OR_STALE"
    if deadline:
        try:
            expired |= date.fromisoformat(deadline) < as_of
        except ValueError:
            deadline = None
    # Issue assignments do not establish claimant access.
    raw = row.raw if isinstance(row.raw, dict) else {}
    assigned = provider == "github" and bool(raw.get("assignee") or raw.get("assignees"))
    aggregator = (provider == "github" and
                  "open bounties" in row.title.lower() and
                  "bounty" not in row.title.lower().replace("open bounties", ""))
    dev_old_and_undated = False
    if provider == "devto" and not deadline:
        try:
            published = datetime.fromisoformat((row.published_at or "").replace("Z", "+00:00"))
            dev_old_and_undated = (as_of - published.date()).days > 7
        except ValueError:
            dev_old_and_undated = True
    state = ("ARCHIVE_EXPIRED" if expired else
             "CHECK_ASSIGNED_OR_CLAIMED" if assigned else
             "HOLD_SECONDARY_AGGREGATOR" if aggregator else
             "HOLD_CURRENTNESS" if dev_old_and_undated else
             "VERIFY_TERMS_ACCESS_COSTS")
    # Existing need/requirement match => verification relevance only.
    scores = [m.score for m in row.need_matches] + [
        m.score for m in row.requirement_matches if m.gap_status == "CONFIRMED"
    ]
    score = 0 if state != "VERIFY_TERMS_ACCESS_COSTS" else round(100 * max(scores, default=0), 1)
    return {
        "resource_id": row.resource_id, "title": row.title,
        "source_name": row.source_name, "source_url": row.source_url,
        "discovered_at": row.discovered_at, "discovery_method": row.discovery_method,
        "types": row.resource_types, "value_kind": benefit_kind(row.resource_types),
        "advertised_usd_mentions": row.cash_mentions_usd, "deadline": deadline,
        "miner_route": row.route, "verification_state": state,
        "verification_relevance_not_profit": score,
        "eligibility": "NOT_ASSESSED", "financial_terms": "NOT_INDEPENDENTLY_VERIFIED",
        "expected_net_usd": None, "realized_usd": None,
        "authority_effect": "NONE", "authorization": "NOT_GRANTED",
        "execution": "DISABLED",
    }

def official_dev_challenges(per_page=100):
    """Bounded first-party DEV organization intake; filter out entrant submissions.

    Uses the same public DEV API transport and canonical Miner normalizer.
    An article about a contest is not necessarily an open contest.
    """
    from resource_miner.normalize import normalize_generic, utcnow_iso
    url = "https://dev.to/api/organizations/devteam/articles?per_page=" + str(per_page)
    payload = devto._get_json(url)
    if not isinstance(payload, list):
        raise ValueError("DEV organization API did not return article records")
    observed = utcnow_iso()
    for article in payload:
        if not isinstance(article, dict):
            continue
        tags = article.get("tag_list") or []
        if "devchallenge" not in [str(v).lower() for v in tags]:
            continue
        title = str(article.get("title") or "")
        if not title.lower().startswith(("join the ", "hacktoberfest 2026 dev challenges")):
            continue
        url = str(article.get("url") or "")
        if not public_source(url, "devto"):
            continue
        detail = article
        article_id = article.get("id")
        if isinstance(article_id, int):
            try:
                detail = devto._get_json(devto.API + "/" + str(article_id))
            except Exception:
                detail = article
        yield normalize_generic(
            title=title, url=url, source_name="DEV Community",
            discovery_method="devto_org_public_api:devteam:devchallenge",
            description=str(article.get("description") or ""),
            sponsor="The DEV Team",
            published_at=str(article.get("published_at") or "") or None,
            tags=[str(v) for v in tags],
            body_text=str(detail.get("body_markdown") or ""),
            observed_at=observed,
        )


def collect(max_per_source=12, collectors=None):
    if not 1 <= max_per_source <= 30:
        raise ValueError("max_per_source must be 1..30")
    collectors = collectors if collectors is not None else {
        "funding": lambda: funding_pipeline.discover(DEFAULT_FUNDING),
        "devto": lambda: official_dev_challenges(per_page=100),
        "github": lambda: github.discover(["is:issue is:open label:bounty"], per_query=30),
    }
    at = datetime.now(timezone.utc).isoformat()
    captured, receipts = [], []
    for name in SOURCES:
        try:
            items = list(collectors[name]())
            if name == "devto":
                items.sort(key=lambda x: x.published_at or "", reverse=True)
            items = items[:max_per_source]
            captured.extend(items)
            receipts.append({
                "source": name, "state": "OBSERVED" if items else "ZERO_MATCHES_OBSERVED",
                "observed_count": len(items), "error_type": None,
            })
        except Exception as exc:
            receipts.append({
                "source": name, "state": "OBSERVATION_FAILED",
                "observed_count": 0, "error_type": type(exc).__name__,
            })
    mapped = enrich(captured, DEFAULT_NEEDS, DEFAULT_REQUIREMENTS)
    records, omissions = [], []
    for item in mapped:
        record = screen(item, as_of=date.today())
        if record is None:
            omissions.append(item.resource_id)
        else:
            records.append(record)
    records.sort(key=lambda r: (
        r["verification_state"] != "VERIFY_TERMS_ACCESS_COSTS",
        -r["verification_relevance_not_profit"],
        r["resource_id"],
    ))
    return {
        "schema": "humanaios.three-source-observation.v1",
        "observed_at": at, "source_receipts": receipts,
        "observed_source_count": sum(x["observed_count"] > 0 for x in receipts),
        "candidate_count": len(records),
        "source_counts": dict(Counter(r["source_name"] for r in records)),
        "omitted_resource_ids": omissions, "candidates": records,
        "economic_outcome": "NOT_ESTABLISHED", "authority_effect": "NONE",
        "authorization": "NOT_GRANTED",
        "disclosure": (
            "Funding records come from the local curated dataset; official DEV org and GitHub use "
            "public read-only APIs. No applicant eligibility, payment, independent "
            "source authentication, or commercial return is claimed. "
            "A source failure must not count as zero available opportunities."
        ),
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="evidence/three-source-observations.json")
    p.add_argument("--per-source", type=int, default=12)
    p.add_argument("--require-three", action="store_true")
    args = p.parse_args()
    result = collect(max_per_source=args.per_source)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_receipts": result["source_receipts"],
        "observed_source_count": result["observed_source_count"],
        "candidate_count": result["candidate_count"],
        "source_counts": result["source_counts"],
        "output": str(out)
    }, indent=2))
    if args.require_three and result["observed_source_count"] < 3:
        raise SystemExit("FAIL: fewer than three actual source observations")

if __name__ == "__main__":
    main()
