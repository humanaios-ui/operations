#!/usr/bin/env python3
"""
Agent 2.1: Substack Content Agent
==================================
Builder v1.7 compliant · reporting_tool
HumanAIOS

Purpose: Auto-generate weekly research posts from ACAT findings
Triggers: Weekly (or after N=10 new resolutions)
Output: Draft Substack posts → humanaios-ui/lasting-light-ai repo
Zone: Z1 (autonomous content generation)

Data flow:
  acat_forecast_runs (resolved questions + Brier scores)
  → Weekly digest markdown
  → GitHub commit to lasting-light-ai repo

Usage:
  python3 tools/agents/substack_content_agent_v1.py --generate-weekly
  python3 tools/agents/substack_content_agent_v1.py --smoke-test
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.substack_agent.research_draft import verified_research_draft, EvidenceUnavailable

TOOL_NAME = "substack_content_agent_v1"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "reporting_tool"

sys.path.insert(0, str(Path(__file__).parent))
from _shared.supabase_client import get_supabase_client
from _shared.github_client import GitHubClient


class SubstackContentAgent:
    """Auto-generates weekly research posts from ACAT findings."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.github = GitHubClient()

    def fetch_recent_resolutions(self, limit: int = 10) -> List[Dict]:
        """
        Fetch recently resolved questions from acat_forecast_runs.
        Returns questions with Brier scores.
        """
        if not self.supabase:
            print("NO_VERIFIED_EVIDENCE: Supabase not configured")
            return []

        try:
            result = self.supabase.table("acat_forecast_runs").select(
                "question_url,p2_forecast_value,p4_brier_score,p4_brier_skill_score,"
                "p1_li_estimate,p1_truthfulness,p1_humility,question_type,p4_resolved_at"
            ).filter("p4_resolved_at", "is not", None).order(
                "p4_resolved_at", desc=True
            ).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            print("NO_VERIFIED_EVIDENCE: Supabase query failed")
            return []

    def _mock_data(self) -> List[Dict]:
        """SYNTHETIC_TEST_ONLY. Never use to produce public research copy."""
        return [
            {
                "question_url": "https://www.metaculus.com/questions/22427/",
                "evidence_status": "SYNTHETIC_TEST_ONLY",
                "p2_forecast_value": 0.62,
                "p4_brier_score": 0.18,
                "p4_brier_skill_score": 0.15,
                "p1_li_estimate": 0.72,
                "p1_truthfulness": 82,
                "p1_humility": 75,
                "question_type": "binary",
                "p4_resolved_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    def generate_post(self, resolutions: List[Dict]) -> str:
        """Return evidence-qualified draft text; fail closed without real records."""
        proposal = self.generate_governed_draft(resolutions)
        return proposal["content"]["body"]

    def generate_governed_draft(self, resolutions: List[Dict]) -> dict:
        """Translate verified forecast records into the HPRA DRAFT_ONLY contract."""
        return verified_research_draft(resolutions)

    def _stub_post(self) -> str:
        """Never present absence of source data as a publishable report."""
        raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE")

    def save_draft(self, post: str, output_dir: str = "/tmp") -> str:
        """Save draft post to file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        filepath = Path(output_dir) / f"SUBSTACK_DRAFT_{timestamp}.md"
        filepath.write_text(post)
        return str(filepath)

    def run_weekly_generate(self) -> bool:
        """
        Run the weekly content generation pipeline.
        Returns True if successful.
        """
        print("Fetching recent resolutions from acat_forecast_runs...")
        resolutions = self.fetch_recent_resolutions(limit=10)
        print(f"  → {len(resolutions)} resolutions fetched")

        print("Generating post...")
        try:
            proposal = self.generate_governed_draft(resolutions)
        except EvidenceUnavailable as exc:
            print(f"Blocked: {exc}")
            return False
        post = proposal["content"]["body"]
        print(f"  → {len(post)} draft characters generated; authorization NONE")

        print("Saving draft...")
        filepath = self.save_draft(post)
        print(f"  → Draft saved: {filepath}")

        print("✓ DRAFT_ONLY generated; no publishing authorization")
        return True


def run_smoke_test() -> bool:
    """Smoke test for Builder v1.7."""
    try:
        agent = SubstackContentAgent()
        print(f"✓ SubstackContentAgent initialized")
        return True
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Substack Content Agent")
    parser.add_argument("--generate-weekly", action="store_true", help="Generate weekly post")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.generate_weekly:
        agent = SubstackContentAgent()
        sys.exit(0 if agent.run_weekly_generate() else 1)
    else:
        parser.print_help()
        sys.exit(1)
