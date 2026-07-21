"""
CLI — Command-line interface for HumanAIOS operations.

Usage:
    python -m humanaios_operations.cli profile sync --verbose
    python -m humanaios_operations.cli funding rank --markdown <output>
    python -m humanaios_operations.cli deadline_checker check --dry-run
    python -m humanaios_operations.cli email_alerts digest
"""

import argparse
import json
import sys
from pathlib import Path

from . import profile, dashboard, email_alerts, deadline_checker


def cmd_profile_sync(args):
    """Sync research profile from ORCID."""
    result = profile.sync_profile(
        orcid_id=args.orcid_id,
        output_dir=args.output_dir,
        verbose=args.verbose
    )

    if result.get("status") == "error":
        print(f"✗ {result.get('message')}")
        return 1

    print(f"✓ Profile synced: {len(result['research_areas'])} areas, {len(result['publications'])} publications")
    return 0


def cmd_funding_rank(args):
    """Rank opportunities by research fit."""
    # Load opportunities from humanaios_funding data
    opps_file = args.opportunities_file
    if not Path(opps_file).exists():
        print(f"✗ Opportunities file not found: {opps_file}")
        return 1

    with open(opps_file) as f:
        opportunities = json.load(f)

    # For now, just copy them with placeholder fit scores
    # In a full implementation, this would use the research profile to rank
    for opp in opportunities:
        opp["fit_score"] = opp.get("fit_score", 0.5)  # Placeholder

    # Sort by fit score
    opportunities.sort(key=lambda x: x.get("fit_score", 0), reverse=True)

    # Save markdown report if requested
    if args.markdown:
        output_file = args.markdown
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        md = "# Ranked Funding Opportunities\n\n"
        for i, opp in enumerate(opportunities[:20], 1):
            fit = opp.get("fit_score", 0)
            fit_pct = int(fit * 100)
            md += f"{i}. **{opp.get('name')}** ({fit_pct}% fit)\n"
            md += f"   - Sponsor: {opp.get('sponsor')}\n"
            md += f"   - Deadline: {opp.get('deadline', 'Rolling')}\n"
            md += f"   - Award: {opp.get('award_size', 'N/A')}\n\n"

        with open(output_file, "w") as f:
            f.write(md)

        print(f"✓ Markdown report saved to {output_file}")

    # Save JSON
    json_file = args.opportunities_file.replace(".json", "_ranked.json")
    with open(json_file, "w") as f:
        json.dump(opportunities, f, indent=2)

    print(f"✓ Ranked {len(opportunities)} opportunities")
    return 0


def cmd_deadline_check(args):
    """Check for upcoming deadlines."""
    result = deadline_checker.check_deadlines(
        opportunities_file=args.opportunities_file,
        days_ahead=args.days,
        dry_run=args.dry_run
    )

    if result.get("status") == "error":
        print(f"✗ {result.get('message')}")
        return 1

    summary = result.get("summary", {})
    print(f"✓ Checked deadlines: {summary.get('urgent')} urgent, {summary.get('soon')} soon")
    return 0


def cmd_email_digest(args):
    """Send email digest of top opportunities."""
    success = email_alerts.digest_report(
        opportunities_file=args.opportunities_file
    )
    return 0 if success else 1


def cmd_email_alert(args):
    """Send deadline alert email."""
    success = email_alerts.deadline_alert(
        opportunities_file=args.opportunities_file,
        days_ahead=args.days
    )
    return 0 if success else 1


def cmd_dashboard_generate(args):
    """Generate HTML dashboard."""
    success = dashboard.generate_dashboard(
        opportunities_file=args.opportunities_file,
        profile_file=args.profile_file,
        output_file=args.output
    )
    return 0 if success else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="humanaios-operations",
        description="HumanAIOS Operations Hub — Manage funding, research profile, and applications.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Profile commands
    profile_parser = subparsers.add_parser("profile", help="Manage research profile")
    profile_subs = profile_parser.add_subparsers(dest="profile_cmd")

    sync_parser = profile_subs.add_parser("sync", help="Sync ORCID profile")
    sync_parser.add_argument("--orcid-id", default="0009-0003-7540-4245", help="ORCID ID")
    sync_parser.add_argument("--output-dir", default="data", help="Output directory for profile data")
    sync_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    sync_parser.set_defaults(func=cmd_profile_sync)

    # Funding commands
    funding_parser = subparsers.add_parser("funding", help="Manage funding opportunities")
    funding_subs = funding_parser.add_subparsers(dest="funding_cmd")

    rank_parser = funding_subs.add_parser("rank", help="Rank opportunities by research fit")
    rank_parser.add_argument("--opportunities-file", default="data/opportunities.json", help="Opportunities file")
    rank_parser.add_argument("--markdown", help="Output markdown report")
    rank_parser.set_defaults(func=cmd_funding_rank)

    # Deadline checker
    deadline_parser = subparsers.add_parser("deadline_checker", help="Check funding deadlines")
    deadline_subs = deadline_parser.add_subparsers(dest="deadline_cmd")

    check_parser = deadline_subs.add_parser("check", help="Check for upcoming deadlines")
    check_parser.add_argument("--opportunities-file", default="data/opportunities.json", help="Opportunities file")
    check_parser.add_argument("--days", type=int, default=30, help="Days ahead to check")
    check_parser.add_argument("--dry-run", action="store_true", help="Dry run (no side effects)")
    check_parser.set_defaults(func=cmd_deadline_check)

    # Email alerts
    email_parser = subparsers.add_parser("email_alerts", help="Send email alerts")
    email_subs = email_parser.add_subparsers(dest="email_cmd")

    digest_parser = email_subs.add_parser("digest", help="Send weekly digest")
    digest_parser.add_argument("--opportunities-file", default="data/ranked_opportunities.json", help="Opportunities file")
    digest_parser.set_defaults(func=cmd_email_digest)

    alert_parser = email_subs.add_parser("alert", help="Send deadline alert")
    alert_parser.add_argument("--opportunities-file", default="data/ranked_opportunities.json", help="Opportunities file")
    alert_parser.add_argument("--days", type=int, default=7, help="Days until deadline")
    alert_parser.set_defaults(func=cmd_email_alert)

    # Dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Generate dashboard")
    dashboard_subs = dashboard_parser.add_subparsers(dest="dashboard_cmd")

    gen_parser = dashboard_subs.add_parser("generate", help="Generate HTML dashboard")
    gen_parser.add_argument("--opportunities-file", default="data/ranked_opportunities.json", help="Opportunities file")
    gen_parser.add_argument("--profile-file", default="data/research_profile.json", help="Profile file")
    gen_parser.add_argument("--output", default="reports/dashboard.html", help="Output HTML file")
    gen_parser.set_defaults(func=cmd_dashboard_generate)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
