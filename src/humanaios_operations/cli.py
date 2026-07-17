"""Integrated CLI for HumanAIOS Operations Hub

Commands:
  profile sync        - Fetch ORCID and extract research areas
  funding rank        - Score opportunities by your research fit
  apps create         - Create new application record
  apps list          - List applications
  apps submit        - Mark application as submitted
  apps decide        - Record funding decision
  dashboard          - Show full status dashboard
"""

import argparse
import json
import sys
from pathlib import Path

from humanaios_operations.profile import ResearchProfile
from humanaios_operations.scoring import score_all_opportunities, generate_ranked_report
from humanaios_operations.applications import ApplicationTracker


class HumanAIOSOps:
    """Main CLI interface"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def cmd_profile_sync(self, args):
        """Fetch ORCID and save research profile"""
        print(f"Fetching ORCID profile: {args.orcid_id}")

        profile = ResearchProfile(args.orcid_id, str(self.data_dir))

        if not profile.fetch():
            print("✗ Failed to fetch ORCID profile")
            return 1

        profile_file, expertise_file = profile.save()
        print(f"✓ Profile saved: {profile_file}")
        print(f"✓ Expertise map saved: {expertise_file}")

        if args.verbose:
            data = profile.to_dict()
            print(f"\nName: {data['profile'].get('name')}")
            print(f"Publications: {data['publication_count']}")
            print("\nResearch Areas:")
            for area, score in data['research_areas'].items():
                print(f"  {area}: {score:.2f}")

        return 0

    def cmd_funding_rank(self, args):
        """Score opportunities by research fit"""
        profile_file = self.data_dir / "research_profile.json"
        opps_file = Path(args.opportunities)

        if not profile_file.exists():
            print(f"✗ Research profile not found: {profile_file}")
            print("  Run 'haios profile sync' first")
            return 1

        if not opps_file.exists():
            print(f"✗ Opportunities file not found: {opps_file}")
            return 1

        print(f"Loading research profile: {profile_file}")
        print(f"Scoring {opps_file}...")

        with open(profile_file) as f:
            profile = json.load(f)

        with open(opps_file) as f:
            opps = json.load(f)

        scored = score_all_opportunities(profile, opps)

        # Save ranked opportunities
        output_file = self.data_dir / "ranked_opportunities.json"
        with open(output_file, "w") as f:
            json.dump(scored, f, indent=2)
        print(f"✓ Ranked opportunities saved: {output_file}")

        # Generate markdown report
        if args.markdown:
            report = generate_ranked_report(scored, top_n=15)
            report_file = Path(args.markdown)
            with open(report_file, "w") as f:
                f.write(report)
            print(f"✓ Markdown report saved: {report_file}")

        # Print top 5
        print("\nTop 5 Opportunities for You:")
        for i, opp in enumerate(scored[:5], 1):
            name = opp.get("name", "Unknown")
            score = opp.get("fit_score", 0.0)
            rec = opp.get("recommendation", "unknown").upper()
            print(f"  {i}. {name}")
            print(f"     Score: {score:.2f} ({rec})")

        return 0

    def cmd_apps_create(self, args):
        """Create new application"""
        tracker = ApplicationTracker(str(self.data_dir / "applications.db"))

        app_id = tracker.create_application(
            args.opportunity_id,
            args.title,
            args.amount,
            args.proposal_file
        )

        print(f"✓ Created application: {app_id}")
        if args.verbose:
            app = tracker.get_application(app_id)
            print(json.dumps(app, indent=2, default=str))

        return 0

    def cmd_apps_list(self, args):
        """List applications"""
        tracker = ApplicationTracker(str(self.data_dir / "applications.db"))
        apps = tracker.list_applications(args.status)

        if not apps:
            print("No applications found")
            return 0

        print(f"Applications ({len(apps)}):")
        for app in apps:
            status = app['status'].upper()
            title = app['title'][:50]
            print(f"  {app['id']}")
            print(f"    Title: {title}")
            print(f"    Status: {status}")
            print()

        return 0

    def cmd_apps_submit(self, args):
        """Mark application as submitted"""
        tracker = ApplicationTracker(str(self.data_dir / "applications.db"))

        if tracker.submit_application(args.app_id):
            print(f"✓ Marked as submitted: {args.app_id}")
            return 0
        else:
            print(f"✗ Application not found: {args.app_id}")
            return 1

    def cmd_apps_decide(self, args):
        """Record decision on application"""
        tracker = ApplicationTracker(str(self.data_dir / "applications.db"))

        if tracker.record_decision(args.app_id, args.decision, args.amount, args.feedback):
            print(f"✓ Recorded decision: {args.app_id} ({args.decision})")
            return 0
        else:
            print(f"✗ Application not found: {args.app_id}")
            return 1

    def cmd_dashboard(self, args):
        """Show dashboard"""
        tracker = ApplicationTracker(str(self.data_dir / "applications.db"))
        profile_file = self.data_dir / "research_profile.json"

        print("=" * 60)
        print("HumanAIOS OPERATIONS DASHBOARD")
        print("=" * 60)

        # Research Profile
        if profile_file.exists():
            with open(profile_file) as f:
                profile = json.load(f)
            print("\n📊 RESEARCH PROFILE")
            print(f"  Name: {profile['profile'].get('name')}")
            print(f"  Publications: {profile['publication_count']}")
            print(f"  Research Areas: {', '.join(list(profile['research_areas'].keys())[:3])}")
        else:
            print("\n📊 RESEARCH PROFILE")
            print("  No profile found. Run 'haios profile sync' first.")

        # Application Pipeline
        print("\n📋 APPLICATION PIPELINE")
        status = tracker.get_pipeline_status()
        print(f"  Total Applications: {status['total_applications']}")
        print(f"  In Progress: {status['status_counts']['draft'] + status['status_counts']['submitted']}")
        print(f"  Pending Decision: {status['status_counts']['pending']}")
        print(f"  Funded: {status['funded_count']} (${status['total_awarded']:.0f})")
        print(f"  Rejected: {status['status_counts']['rejected']}")

        if status['total_applications'] > 0:
            success_rate = status['success_rate']
            print(f"  Success Rate: {success_rate:.1%}")

        # Top Opportunities
        opps_file = self.data_dir / "ranked_opportunities.json"
        if opps_file.exists():
            with open(opps_file) as f:
                opps = json.load(f)
            print("\n🎯 TOP OPPORTUNITIES FOR YOU")
            for i, opp in enumerate(opps[:3], 1):
                print(f"  {i}. {opp['name']}")
                print(f"     Score: {opp['fit_score']:.2f} | {opp['recommendation'].upper()}")
        else:
            print("\n🎯 TOP OPPORTUNITIES FOR YOU")
            print("  No opportunities scored yet. Run 'haios funding rank' first.")

        print("\n" + "=" * 60)
        return 0

    def run(self, argv):
        """Main entry point"""
        parser = argparse.ArgumentParser(
            description="HumanAIOS Operations Hub - Integrated funding discovery + research profiling",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  haios profile sync
  haios funding rank
  haios apps create --opportunity-id longview-grants --title "My Proposal"
  haios apps list --status draft
  haios dashboard
            """
        )

        parser.add_argument("--data-dir", default="data", help="Data directory")
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # profile sync
        profile = subparsers.add_parser("profile", help="Research profile commands")
        profile_sub = profile.add_subparsers(dest="profile_cmd")
        sync = profile_sub.add_parser("sync", help="Fetch ORCID and save research profile")
        sync.add_argument("--orcid-id", default="0009-0003-7540-4245", help="ORCID ID")
        sync.add_argument("-v", "--verbose", action="store_true")

        # funding rank
        funding = subparsers.add_parser("funding", help="Funding discovery commands")
        funding_sub = funding.add_subparsers(dest="funding_cmd")
        rank = funding_sub.add_parser("rank", help="Score opportunities by research fit")
        rank.add_argument("--opportunities", default="data/sources.json", help="Opportunities file")
        rank.add_argument("--markdown", help="Generate markdown report to file")

        # apps commands
        apps = subparsers.add_parser("apps", help="Application tracking commands")
        apps_sub = apps.add_subparsers(dest="apps_cmd")

        create = apps_sub.add_parser("create", help="Create new application")
        create.add_argument("--opportunity-id", required=True)
        create.add_argument("--title", required=True)
        create.add_argument("--amount", type=float, help="Amount requested")
        create.add_argument("--proposal-file", help="Proposal file path")
        create.add_argument("-v", "--verbose", action="store_true")

        list_cmd = apps_sub.add_parser("list", help="List applications")
        list_cmd.add_argument("--status", help="Filter by status (draft, submitted, pending, funded, rejected)")

        submit = apps_sub.add_parser("submit", help="Mark as submitted")
        submit.add_argument("app_id")

        decide = apps_sub.add_parser("decide", help="Record decision")
        decide.add_argument("app_id")
        decide.add_argument("--decision", required=True, choices=["funded", "rejected"])
        decide.add_argument("--amount", type=float, help="Amount awarded")
        decide.add_argument("--feedback", default="", help="Funder feedback")

        # dashboard
        subparsers.add_parser("dashboard", help="Show operations dashboard")

        args = parser.parse_args(argv)
        self.data_dir = Path(args.data_dir)

        # Route commands
        if args.command == "profile" and args.profile_cmd == "sync":
            return self.cmd_profile_sync(args)
        elif args.command == "funding" and args.funding_cmd == "rank":
            return self.cmd_funding_rank(args)
        elif args.command == "apps" and args.apps_cmd == "create":
            return self.cmd_apps_create(args)
        elif args.command == "apps" and args.apps_cmd == "list":
            return self.cmd_apps_list(args)
        elif args.command == "apps" and args.apps_cmd == "submit":
            return self.cmd_apps_submit(args)
        elif args.command == "apps" and args.apps_cmd == "decide":
            return self.cmd_apps_decide(args)
        elif args.command == "dashboard":
            return self.cmd_dashboard(args)
        else:
            parser.print_help()
            return 0


def main():
    ops = HumanAIOSOps()
    return ops.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
