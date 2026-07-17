"""
cli.py — HumanAIOS Funding Pipeline
Filter and query funding opportunities from the command line.

Examples:
    # Native-eligible + AI-safety intersection
    python -m src.humanaios_funding.cli --native --ai-safety

    # Deadlines within 45 days
    python -m src.humanaios_funding.cli --deadline-soon 45

    # All compute credits
    python -m src.humanaios_funding.cli --category compute_credit

    # Only rolling/active, output as JSON
    python -m src.humanaios_funding.cli --status rolling --format json

    # Full summary stats
    python -m src.humanaios_funding.cli --summary
"""
from __future__ import annotations

import argparse
import json
import sys

from .loader import load_any, summarise
from .schema import Category, Status


def _render_table(items) -> None:
    CATEGORY_EMOJI = {
        "native": "🏛️ ",
        "ai_safety": "🛡️ ",
        "research_grant": "🔬",
        "contest": "🏆",
        "compute_credit": "☁️ ",
        "fellowship": "🎓",
        "paid_work": "💰",
        "publishing": "📄",
        "free_api": "🆓",
        "free_infra": "🖥️ ",
    }
    for i in items:
        flags = []
        if i.native_eligible:    flags.append("NATIVE")
        if i.ai_safety_relevant: flags.append("AISAFETY")
        if i.is_deadline_soon(7):   flags.append("⚠️ <7d")
        elif i.is_deadline_soon(30): flags.append("⏰ <30d")

        emoji   = CATEGORY_EMOJI.get(i.category.value, "  ")
        award   = i.award_size or "—"
        cadence = i.deadline or i.deadline_cadence or "—"
        flag_str = " ".join(f"[{f}]" for f in flags)

        print(f"{emoji} {i.name}")
        print(f"   Sponsor : {i.sponsor}")
        print(f"   Award   : {award}")
        print(f"   Timing  : {cadence}  Status: {i.status.value}")
        print(f"   URL     : {i.url}")
        if flag_str:
            print(f"   Flags   : {flag_str}")
        print()


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="haios-funding",
        description="Query HumanAIOS funding opportunities.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--data",         default="data/sources.json",
                   help="Path to sources.json or sources.csv")
    p.add_argument("--category",     choices=[c.value for c in Category],
                   help="Filter by category")
    p.add_argument("--native",       action="store_true",
                   help="Only native_eligible")
    p.add_argument("--ai-safety",    dest="ai_safety", action="store_true",
                   help="Only ai_safety_relevant")
    p.add_argument("--status",       choices=[s.value for s in Status],
                   help="Filter by status")
    p.add_argument("--deadline-soon", dest="deadline_soon", type=int, metavar="DAYS",
                   help="Only opportunities with deadline <= N days away")
    p.add_argument("--trl",          help="TRL tag substring match (e.g. TRL2-3)")
    p.add_argument("--tag",          help="Filter by eligibility tag substring")
    p.add_argument("--search",       help="Case-insensitive name/notes search")
    p.add_argument("--summary",      action="store_true",
                   help="Print summary stats and exit")
    p.add_argument("--format",       choices=["table", "json", "csv", "urls"],
                   default="table",
                   help="Output format (default: table)")
    p.add_argument("--sort-by",      choices=["name", "priority", "deadline"],
                   default="priority",
                   help="Sort order (default: priority)")

    args = p.parse_args(argv)
    items = load_any(args.data)

    # ── Summary mode ──────────────────────────────────────────────────────
    if args.summary:
        s = summarise(items)
        print(f"HumanAIOS Funding Pipeline — {s.generated}")
        print(f"  Total opportunities   : {s.total}")
        print(f"  Native-eligible       : {s.native_eligible}")
        print(f"  AI-safety relevant    : {s.ai_safety_relevant}")
        print(f"  Both flags            : {s.both_flags}")
        print(f"  Active / rolling      : {s.active_rolling}")
        print(f"  Deadline ≤30d         : {s.deadline_soon_30d}")
        print("\n  By category:")
        for cat, cnt in sorted(s.by_category.items(), key=lambda x: -x[1]):
            print(f"    {cat:<20} {cnt}")
        return

    # ── Filters ───────────────────────────────────────────────────────────
    if args.category:
        items = [i for i in items if i.category.value == args.category]
    if args.native:
        items = [i for i in items if i.native_eligible]
    if args.ai_safety:
        items = [i for i in items if i.ai_safety_relevant]
    if args.status:
        items = [i for i in items if i.status.value == args.status]
    if args.trl:
        items = [i for i in items if args.trl.lower() in (i.trl_fit or "").lower()]
    if args.tag:
        items = [i for i in items
                 if any(args.tag.lower() in t.lower() for t in i.eligibility_tags)]
    if args.search:
        q = args.search.lower()
        items = [i for i in items
                 if q in i.name.lower() or q in (i.notes or "").lower()]
    if args.deadline_soon is not None:
        items = [i for i in items if i.is_deadline_soon(args.deadline_soon)]

    # ── Sort ──────────────────────────────────────────────────────────────
    if args.sort_by == "priority":
        items.sort(key=lambda i: (i.priority_score(), i.name.lower()))
    elif args.sort_by == "name":
        items.sort(key=lambda i: i.name.lower())
    elif args.sort_by == "deadline":
        items.sort(key=lambda i: (i.deadline or "9999", i.name.lower()))

    # ── Output ────────────────────────────────────────────────────────────
    if not items:
        print("No opportunities match the given filters.")
        return

    if args.format == "table":
        _render_table(items)
        print(f"── {len(items)} opportunities ──")

    elif args.format == "json":
        print(json.dumps([i.model_dump() for i in items], indent=2, default=str))

    elif args.format == "csv":
        import csv
        import io
        buf = io.StringIO()
        fields = list(items[0].model_fields.keys()) if items else []
        w = csv.DictWriter(buf, fieldnames=fields)
        w.writeheader()
        for i in items:
            row = i.model_dump()
            row["eligibility_tags"] = "|".join(row["eligibility_tags"])
            w.writerow(row)
        print(buf.getvalue(), end="")

    elif args.format == "urls":
        for i in items:
            print(i.url)


if __name__ == "__main__":
    main()
