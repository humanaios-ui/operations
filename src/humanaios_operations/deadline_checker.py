"""
Deadline Checker — Check for upcoming funding deadlines and opportunities.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def parse_deadline(deadline_str: str | None) -> datetime | None:
    """Parse deadline string to datetime. Returns None if can't parse."""
    if not deadline_str:
        return None

    formats = ["%Y-%m-%d", "%Y-%m", "%B %d, %Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(deadline_str, fmt)
        except ValueError:
            continue

    return None


def check_deadlines(opportunities_file: str = "data/ranked_opportunities.json", days_ahead: int = 30, dry_run: bool = False) -> dict:
    """List opportunities with deadline metadata (OBSERVATIONAL only, no urgency-based categorization).

    NOTE: This function provides deadline information for reference only (OBSERVATIONAL class per Q-TEMPORAL-DISSOLUTION-01).
    Deadlines are NOT used to prioritize work. Work prioritization is resource-state based (PRIORITY_QUEUE.md).
    External regulatory deadlines require Z2 ratification via external_constraint schema.
    """
    if not Path(opportunities_file).exists():
        return {"status": "error", "message": f"File not found: {opportunities_file}"}

    with open(opportunities_file) as f:
        opportunities = json.load(f)

    now = datetime.now()
    valid_opportunities = []
    expired_opportunities = []

    for opp in opportunities:
        deadline_str = opp.get("deadline")

        # Handle rolling deadlines (no deadline provided)
        if deadline_str and deadline_str.lower() == "rolling":
            valid_opportunities.append({
                "opportunity": opp,
                "deadline_type": "rolling",
                "deadline_parsed": None,
                "days_until_deadline": None
            })
            continue

        # Parse deadline if present
        deadline = parse_deadline(deadline_str)
        if not deadline:
            valid_opportunities.append({
                "opportunity": opp,
                "deadline_type": "unknown",
                "deadline_parsed": None,
                "days_until_deadline": None
            })
            continue

        days_left = (deadline - now).days

        if days_left < 0:
            # Expired opportunity - exclude from results
            expired_opportunities.append({
                "opportunity": opp,
                "deadline_parsed": deadline.isoformat(),
                "days_expired": abs(days_left)
            })
        else:
            # Valid opportunity - store with deadline metadata (OBSERVATIONAL)
            valid_opportunities.append({
                "opportunity": opp,
                "deadline_type": "dated",
                "deadline_parsed": deadline.isoformat(),
                "days_until_deadline": days_left
            })

    # Print summary
    if not dry_run:
        print(f"📊 Opportunity Listing ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})")
        print(f"  ✅ ACTIVE:         {len(valid_opportunities)}")
        print(f"  ⏳ EXPIRED:        {len(expired_opportunities)}")
        print("")
        print("NOTE: Deadline metadata provided for reference (OBSERVATIONAL class).")
        print("Work prioritization uses resource-state allocation, not calendar proximity.")
        print("External regulatory deadlines require Z2 ratification.")

    return {
        "status": "ok",
        "checked_at": now.isoformat(),
        "temporal_class": "OBSERVATIONAL",
        "summary": {
            "active_opportunities": len(valid_opportunities),
            "expired_opportunities": len(expired_opportunities),
        },
        "opportunities": valid_opportunities,
        "expired": expired_opportunities,
    }
