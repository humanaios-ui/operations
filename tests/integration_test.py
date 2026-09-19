#!/usr/bin/env python3
"""
Integration Tests: End-to-end workflow testing

Simulates the complete GitHub Actions workflow:
1. Profile sync (Monday 09:00)
2. Funding rescore + dashboard (Monday 09:30)
3. Deadline alerts (Daily 08:00)
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "./src")

from humanaios_operations import profile, email_alerts, deadline_checker, dashboard


class TestIntegration:
    """Integration test suite for HumanAIOS operations workflows."""

    @staticmethod
    def test_workflow_1_profile_sync():
        """TEST: Weekly Profile Sync Workflow (Monday 09:00 UTC)"""
        print("\n" + "="*70)
        print("WORKFLOW 1: Weekly Profile Sync (Monday 09:00)")
        print("="*70)

        # Step 1: Fetch ORCID profile
        print("\n[Step 1/2] Fetching ORCID profile...")
        result = profile.sync_profile(verbose=True)

        if result.get("status") == "error":
            print(f"❌ FAILED: {result.get('message')}")
            return False

        # Verify output
        profile_file = "data/research_profile.json"
        if not Path(profile_file).exists():
            print(f"❌ FAILED: {profile_file} not created")
            return False

        with open(profile_file) as f:
            profile_data = json.load(f)

        areas = len(profile_data.get("research_areas", []))
        pubs = len(profile_data.get("publications", []))

        print(f"✅ Profile synced: {areas} research areas, {pubs} publications")

        # Step 2: Verify commit (in real workflow)
        print("\n[Step 2/2] Git commit simulation...")
        print("✅ Would commit: data/research_profile.json")

        print("\n✅ WORKFLOW 1 PASSED")
        return True

    @staticmethod
    def test_workflow_2_funding_rescore():
        """TEST: Weekly Funding Rescore Workflow (Monday 09:30 UTC)"""
        print("\n" + "="*70)
        print("WORKFLOW 2: Weekly Funding Rescore (Monday 09:30)")
        print("="*70)

        # Create test opportunities if not present
        test_file = "data/ranked_opportunities.json"
        if not Path(test_file).exists():
            test_opps = [
                {
                    "name": "Longview Grants",
                    "sponsor": "Longview Philanthropy",
                    "deadline": "2026-08-31",
                    "award_size": "$50,000-$200,000",
                    "fit_score": 0.92,
                    "days_to_deadline": 41
                },
                {
                    "name": "Blue Dot Rapid Grants",
                    "sponsor": "Blue Dot Impact",
                    "deadline": "2026-08-15",
                    "award_size": "$25,000-$75,000",
                    "fit_score": 0.88,
                    "days_to_deadline": 25
                },
            ]
            Path("data").mkdir(exist_ok=True)
            with open(test_file, "w") as f:
                json.dump(test_opps, f, indent=2)

        # Step 1: Rank opportunities
        print("\n[Step 1/3] Ranking opportunities by research fit...")
        with open(test_file) as f:
            opps = json.load(f)

        ranked = sorted(opps, key=lambda x: x.get("fit_score", 0), reverse=True)
        print(f"✅ Ranked {len(ranked)} opportunities")
        for i, opp in enumerate(ranked[:3], 1):
            fit = int(opp.get("fit_score", 0) * 100)
            print(f"   {i}. {opp['name']} ({fit}%)")

        # Step 2: Generate dashboard
        print("\n[Step 2/3] Generating dashboard...")
        success = dashboard.generate_dashboard(
            opportunities_file=test_file,
            profile_file="data/research_profile.json",
            output_file="reports/dashboard.html"
        )
        if not success:
            print("❌ FAILED: Dashboard generation failed")
            return False

        # Step 3: Send email alerts (if configured)
        print("\n[Step 3/3] Sending email digest (SMTP check)...")
        config = email_alerts.get_smtp_config()
        if config["host"]:
            print("✅ SMTP configured - email would be sent")
        else:
            print("⚠️  SMTP not configured - email skipped")
            print("   (This is OK in testing environment)")

        print("\n✅ WORKFLOW 2 PASSED")
        return True

    @staticmethod
    def test_workflow_3_deadline_alerts():
        """TEST: Daily Deadline Alerts Workflow (Daily 08:00 UTC)"""
        print("\n" + "="*70)
        print("WORKFLOW 3: Daily Deadline Alerts (Daily 08:00)")
        print("="*70)

        # Create test opportunities
        test_file = "data/ranked_opportunities.json"
        if not Path(test_file).exists():
            test_opps = [
                {"name": "Urgent Opp", "deadline": "2026-07-25", "days_to_deadline": 4},
                {"name": "Soon Opp", "deadline": "2026-08-15", "days_to_deadline": 25},
            ]
            Path("data").mkdir(exist_ok=True)
            with open(test_file, "w") as f:
                json.dump(test_opps, f, indent=2)

        # Step 1: Check deadlines
        print("\n[Step 1/2] Checking for upcoming deadlines...")
        result = deadline_checker.check_deadlines(
            opportunities_file=test_file,
            days_ahead=7,
            dry_run=True
        )

        if result.get("status") == "error":
            print(f"❌ FAILED: {result.get('message')}")
            return False

        summary = result.get("summary", {})
        print(f"✅ Checked deadlines:")
        print(f"   Urgent (<7d): {summary.get('urgent')}")
        print(f"   Soon (7-30d): {summary.get('soon')}")
        print(f"   Upcoming (30+): {summary.get('upcoming')}")

        # Step 2: Send alert (if configured)
        print("\n[Step 2/2] Sending deadline alert (SMTP check)...")
        config = email_alerts.get_smtp_config()
        if config["host"]:
            print("✅ SMTP configured - alert would be sent")
        else:
            print("⚠️  SMTP not configured - alert skipped")

        print("\n✅ WORKFLOW 3 PASSED")
        return True

    @staticmethod
    def test_end_to_end_flow():
        """TEST: Complete end-to-end flow (all 3 workflows in sequence)"""
        print("\n" + "="*70)
        print("END-TO-END TEST: Complete Workflow Flow")
        print("="*70)

        workflow_1 = TestIntegration.test_workflow_1_profile_sync()
        workflow_2 = TestIntegration.test_workflow_2_funding_rescore()
        workflow_3 = TestIntegration.test_workflow_3_deadline_alerts()

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Workflow 1 (Profile Sync):      {'✅ PASS' if workflow_1 else '❌ FAIL'}")
        print(f"Workflow 2 (Rescore + Email):   {'✅ PASS' if workflow_2 else '❌ FAIL'}")
        print(f"Workflow 3 (Deadline Alerts):   {'✅ PASS' if workflow_3 else '❌ FAIL'}")
        print("="*70)

        all_passed = workflow_1 and workflow_2 and workflow_3
        print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return all_passed


def main():
    """Run integration tests."""
    print("\n" + "="*70)
    print("INTEGRATION TEST SUITE")
    print("HumanAIOS Operations - End-to-End Workflow Testing")
    print("="*70)

    # Create data directories
    Path("data").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    # Run tests
    success = TestIntegration.test_end_to_end_flow()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
