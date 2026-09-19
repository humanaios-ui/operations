"""
Deadline Checker — Check for upcoming funding deadlines and opportunities.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


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
    """Check for deadlines and categorize by urgency."""
    if not Path(opportunities_file).exists():
        return {"status": "error", "message": f"File not found: {opportunities_file}"}

    with open(opportunities_file) as f:
        opportunities = json.load(f)

    now = datetime.now()
    results = {
        "urgent": [],  # < 7 days
        "soon": [],    # 7-30 days
        "upcoming": [], # 30+ days
        "rolling": [],  # No deadline
    }

    for opp in opportunities:
        deadline_str = opp.get("deadline")
        if deadline_str and deadline_str.lower() == "rolling":
            results["rolling"].append(opp)
            continue

        deadline = parse_deadline(deadline_str)
        if not deadline:
            continue

        days_left = (deadline - now).days

        if days_left < 0:
            continue  # Skip past deadlines
        elif days_left < 7:
            results["urgent"].append({"opp": opp, "days": days_left})
        elif days_left < 30:
            results["soon"].append({"opp": opp, "days": days_left})
        else:
            results["upcoming"].append({"opp": opp, "days": days_left})

    # Print summary
    if not dry_run:
        print(f"📊 Deadline Check Summary ({datetime.now().strftime('%Y-%m-%d %H:%M UTC')})")
        print(f"  🚨 URGENT (<7d):  {len(results['urgent'])}")
        print(f"  ⏰ SOON (7-30d):   {len(results['soon'])}")
        print(f"  📅 UPCOMING (30+): {len(results['upcoming'])}")
        print(f"  🔄 ROLLING:        {len(results['rolling'])}")

        for item in results["urgent"]:
            opp = item["opp"]
            days = item["days"]
            print(f"     🚨 {opp.get('name')} — {days}d ({opp.get('deadline')})")

    return {
        "status": "ok",
        "checked_at": now.isoformat(),
        "summary": {
            "urgent": len(results["urgent"]),
            "soon": len(results["soon"]),
            "upcoming": len(results["upcoming"]),
            "rolling": len(results["rolling"]),
        },
        "details": results,
    }
