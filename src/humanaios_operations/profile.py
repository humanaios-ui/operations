"""
Profile Management — Fetch and analyze research profile from ORCID.
"""

import json
import os
from pathlib import Path
from typing import Any

import requests


ORCID_ID = "0009-0003-7540-4245"
ORCID_API = "https://pub.orcid.org/v3.0"


def fetch_orcid_profile(orcid_id: str = ORCID_ID, verbose: bool = False) -> dict[str, Any]:
    """Fetch research profile from ORCID."""
    url = f"{ORCID_API}/{orcid_id}"
    headers = {"Accept": "application/json"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        profile = resp.json()

        if verbose:
            print(f"✓ Fetched ORCID profile: {profile.get('person', {}).get('name', {}).get('given-names', {}).get('value')}")

        return profile
    except requests.RequestException as e:
        print(f"✗ Failed to fetch ORCID profile: {e}")
        return {}


def extract_research_areas(profile: dict[str, Any]) -> list[str]:
    """Extract research areas from ORCID profile keywords."""
    areas = []

    if "person" in profile:
        keywords = profile["person"].get("keywords", {}).get("keyword", [])
        if isinstance(keywords, dict):
            keywords = [keywords]

        for kw in keywords:
            if isinstance(kw, dict) and "content" in kw:
                areas.append(kw["content"])

    return areas


def extract_publications(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract publications from ORCID works."""
    works = []

    activities = profile.get("activities-summary", {})
    works_group = activities.get("works", {}).get("group", [])

    for group in works_group:
        for work_summary in group.get("work-summary", []):
            work = {
                "title": work_summary.get("title", {}).get("title", {}).get("value", ""),
                "year": work_summary.get("publication-date", {}).get("year", {}).get("value", ""),
                "type": work_summary.get("type", ""),
                "url": work_summary.get("url", {}).get("value", ""),
            }
            if work["title"]:
                works.append(work)

    return works


def save_profile_data(data: dict[str, Any], output_dir: str = "data") -> None:
    """Save extracted profile data to JSON files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(f"{output_dir}/research_profile.json", "w") as f:
        json.dump(data, f, indent=2)


def sync_profile(orcid_id: str = ORCID_ID, output_dir: str = "data", verbose: bool = False) -> dict[str, Any]:
    """Sync ORCID profile: fetch, extract, save."""
    profile = fetch_orcid_profile(orcid_id, verbose=verbose)

    if not profile:
        return {"status": "error", "message": "Failed to fetch ORCID profile"}

    research_areas = extract_research_areas(profile)
    publications = extract_publications(profile)

    data = {
        "orcid_id": orcid_id,
        "research_areas": research_areas,
        "publications": publications,
        "profile": profile,
    }

    save_profile_data(data, output_dir)

    if verbose:
        print(f"✓ Synced {len(research_areas)} research areas, {len(publications)} publications")

    return data
