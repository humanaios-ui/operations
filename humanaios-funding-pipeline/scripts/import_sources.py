#!/usr/bin/env python3
"""
scripts/import_sources.py — HumanAIOS Funding Pipeline
========================================================
Bulk-import opportunities from multiple sources into the canonical
data/sources.json, with deduplication, merge, and dry-run support.

Supported import modes:
  --from-csv   PATH        Import / merge from a CSV file
  --from-json  PATH        Import / merge from a JSON array file
  --from-url   URL         Fetch a remote JSON/CSV and import
  --from-grants-gov QUERY  Scrape grants.gov search results
  --from-sam   QUERY       Scrape SAM.gov opportunities
  --dry-run                Print what would change without writing

Deduplication key: lowercase(name) + lowercase(sponsor)
Merge strategy: existing record wins on all fields; only 'notes' and
  'eligibility_tags' are union-merged.

Usage:
    python scripts/import_sources.py --from-csv  new_grants.csv
    python scripts/import_sources.py --from-json extra.json --dry-run
    python scripts/import_sources.py --from-url  https://example.org/opps.json
    python scripts/import_sources.py --from-grants-gov "AI safety behavioral"
    python scripts/import_sources.py --from-sam "AI observability"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

# ── repo root resolution ───────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parent.parent
DATA_DIR   = REPO_ROOT / "data"
sys.path.insert(0, str(REPO_ROOT / "src"))

from humanaios_funding.loader import load_any, save_json, load_csv, load_json
from humanaios_funding.schema import Opportunity, Category, Status

DEFAULT_OUT = DATA_DIR / "sources.json"

HEADERS = {
    "User-Agent": "humanaios-funding-pipeline/1.0 import-bot"
}


# ─── Deduplication ─────────────────────────────────────────────────────────

def _key(opp: Opportunity) -> str:
    return f"{opp.name.strip().lower()}||{opp.sponsor.strip().lower()}"


def _build_index(items: List[Opportunity]) -> Dict[str, Opportunity]:
    return {_key(i): i for i in items}


def _merge(existing: Opportunity, incoming: Opportunity) -> Opportunity:
    """Existing wins on all fields; union-merge notes + tags."""
    merged = existing.model_copy()
    # Union-merge tags
    combined_tags = list(dict.fromkeys(
        existing.eligibility_tags + incoming.eligibility_tags
    ))
    merged.eligibility_tags = combined_tags
    # Append notes if new text isn't already present
    if incoming.notes and incoming.notes not in (existing.notes or ""):
        sep   = " | " if existing.notes else ""
        merged.notes = (existing.notes or "") + sep + incoming.notes
    return merged


# ─── Grants.gov scraper ───────────────────────────────────────────────────

def _scrape_grants_gov(query: str) -> List[Opportunity]:
    """
    Scrape grants.gov CFDA search for matching opportunities.
    Returns Opportunity objects for any result that looks relevant.
    Uses the public JSON API endpoint.
    """
    API = "https://api.grants.gov/v1/api/search2"
    payload = {
        "keyword": query,
        "rows": 25,
        "oppStatuses": "forecasted|posted",
    }
    out: List[Opportunity] = []
    try:
        r = requests.post(API, json=payload, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        hits = data.get("data", {}).get("oppHits", [])
    except Exception as e:
        print(f"[grants.gov] fetch failed: {e}")
        return out

    for h in hits:
        url = f"https://www.grants.gov/search-results-detail/{h.get('id', '')}"
        out.append(Opportunity(
            name=h.get("title", "Unknown Grant"),
            category=Category.research_grant,
            sponsor=h.get("agencyName", "Federal Agency"),
            url=url,
            eligibility_tags=["federal", "us_based"],
            award_size=_fmt_award(h.get("awardCeiling"), h.get("awardFloor")),
            deadline=h.get("closeDate"),
            deadline_cadence=None,
            native_eligible=False,
            ai_safety_relevant=False,
            trl_fit="any",
            status=Status.active if h.get("oppStatus") == "posted" else Status.upcoming,
            notes=f"CFDA: {h.get('cfdaList', '')}",
            source="grants.gov",
        ))
    print(f"[grants.gov] found {len(out)} opportunities for '{query}'")
    return out


def _fmt_award(ceiling, floor) -> Optional[str]:
    if ceiling and floor and ceiling != floor:
        return f"${int(floor):,} – ${int(ceiling):,}"
    elif ceiling:
        return f"up to ${int(ceiling):,}"
    return None


# ─── SAM.gov scraper ──────────────────────────────────────────────────────

def _scrape_sam_gov(query: str) -> List[Opportunity]:
    """
    Scrape SAM.gov contract / grant opportunities.
    Uses the public beta search API.
    """
    BASE = "https://sam.gov/api/prod/sgs/v1/search/"
    params = {
        "random": "1234",
        "index": "opp",
        "q": query,
        "page": "0",
        "sort": "-modifiedDate",
        "size": "20",
        "is_active": "true",
    }
    out: List[Opportunity] = []
    try:
        url = f"{BASE}?{urlencode(params)}"
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        hits = r.json().get("_embedded", {}).get("results", [])
    except Exception as e:
        print(f"[sam.gov] fetch failed: {e}")
        return out

    for h in hits:
        entity_url = (
            f"https://sam.gov/opp/{h.get('_id', '')}/view"
        )
        out.append(Opportunity(
            name=h.get("title", "SAM Opportunity"),
            category=Category.research_grant,
            sponsor=h.get("_source", {}).get("organization", {}).get("name", "US Gov"),
            url=entity_url,
            eligibility_tags=["federal", "sam_gov"],
            award_size=None,
            deadline=h.get("_source", {}).get("responseDeadLine"),
            native_eligible=False,
            ai_safety_relevant=False,
            trl_fit="any",
            status=Status.active,
            notes=f"NAICS: {h.get('_source', {}).get('naicsList', '')}",
            source="sam.gov",
        ))
    print(f"[sam.gov] found {len(out)} opportunities for '{query}'")
    return out


# ─── Remote URL fetch ─────────────────────────────────────────────────────

def _fetch_remote(url: str) -> List[Opportunity]:
    """Download a JSON array or CSV from a URL and parse into Opportunities."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    ct = r.headers.get("content-type", "")

    import io, tempfile, os

    if "json" in ct or url.endswith(".json"):
        data = r.json()
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump(data, tmp)
        tmp.close()
        items = load_json(tmp.name)
        os.unlink(tmp.name)
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False,
                                          mode="w", encoding="utf-8")
        tmp.write(r.text)
        tmp.close()
        items = load_csv(tmp.name)
        os.unlink(tmp.name)

    print(f"[remote] fetched {len(items)} opportunities from {url}")
    return items


# ─── Merge + write ────────────────────────────────────────────────────────

def merge_and_save(
    incoming:  List[Opportunity],
    out_path:  Path = DEFAULT_OUT,
    dry_run:   bool = False,
) -> None:
    # Load existing
    existing = load_any(out_path) if out_path.exists() else []
    idx = _build_index(existing)

    added, updated, skipped = 0, 0, 0

    for opp in incoming:
        k = _key(opp)
        if k in idx:
            merged = _merge(idx[k], opp)
            if merged.model_dump() != idx[k].model_dump():
                idx[k] = merged
                updated += 1
            else:
                skipped += 1
        else:
            idx[k] = opp
            added += 1

    result = list(idx.values())
    print(f"[import] added={added}  updated={updated}  skipped={skipped}  "
          f"total={len(result)}")

    if dry_run:
        print("[import] DRY RUN — nothing written.")
        return

    save_json(result, out_path)
    print(f"[import] Saved → {out_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Import funding opportunities into data/sources.json",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--out",             default=str(DEFAULT_OUT),
                   help="Output JSON file (default: data/sources.json)")
    p.add_argument("--from-csv",        metavar="PATH",
                   help="Import from local CSV file")
    p.add_argument("--from-json",       metavar="PATH",
                   help="Import from local JSON array file")
    p.add_argument("--from-url",        metavar="URL",
                   help="Fetch and import from remote JSON/CSV URL")
    p.add_argument("--from-grants-gov", metavar="QUERY",
                   help="Scrape grants.gov search results")
    p.add_argument("--from-sam",        metavar="QUERY",
                   help="Scrape SAM.gov contract/grant opportunities")
    p.add_argument("--dry-run",         action="store_true",
                   help="Preview changes without writing")
    args = p.parse_args(argv)

    incoming: List[Opportunity] = []

    if args.from_csv:
        incoming += load_csv(args.from_csv)
    if args.from_json:
        incoming += load_json(args.from_json)
    if args.from_url:
        incoming += _fetch_remote(args.from_url)
    if args.from_grants_gov:
        incoming += _scrape_grants_gov(args.from_grants_gov)
    if args.from_sam:
        incoming += _scrape_sam_gov(args.from_sam)

    if not incoming:
        print("No import sources specified. Use --help.")
        p.print_help()
        sys.exit(1)

    merge_and_save(incoming, out_path=Path(args.out), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
