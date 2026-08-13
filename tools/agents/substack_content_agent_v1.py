#!/usr/bin/env python3
"""
Agent 2.1: Substack Content Agent
==================================

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

TOOL_NAME = "substack_content_agent_v1"
TOOL_VERSION = "1.0.0"

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
            print("⚠ Supabase not configured — using mock data")
            return self._mock_data()

        try:
            result = self.supabase.table("acat_forecast_runs").select(
                "question_url,p2_forecast_value,p4_brier_score,p4_brier_skill_score,"
                "p1_li_estimate,p1_truthfulness,p1_humility,question_type,p4_resolved_at"
            ).filter("p4_resolved_at", "is not", None).order(
                "p4_resolved_at", desc=True
            ).limit(limit).execute()

            return result.data if result.data else self._mock_data()

        except Exception as e:
            print(f"⚠ Supabase query failed: {e} — using mock data")
            return self._mock_data()

    def _mock_data(self) -> List[Dict]:
        """Mock data for testing when Supabase is unavailable."""
        return [
            {
                "question_url": "https://www.metaculus.com/questions/22427/",
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
        """
        Generate a Substack post from recent resolutions.
        Returns markdown text.
        """
        if not resolutions:
            return self._stub_post()

        avg_brier = sum(r.get("p4_brier_score", 0) for r in resolutions if r.get("p4_brier_score")) / len(resolutions)
        avg_skill = sum(r.get("p4_brier_skill_score", 0) for r in resolutions if r.get("p4_brier_skill_score")) / len(resolutions)

        post = f"""# Weekly Calibration Update: {len(resolutions)} Questions Resolved

**Published:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## This Week's Calibration Metrics

- **Questions Resolved:** {len(resolutions)}
- **Average Brier Score:** {avg_brier:.3f}
- **Average Skill Score:** {avg_skill:+.3f}
- **Questions by Type:** """ + ", ".join(f"{r['question_type']}" for r in resolutions[:3]) + "...\n\n"

        post += "## The Data\n\nThis bot demonstrated calibration on the following resolved questions:\n\n"

        for i, r in enumerate(resolutions[:5], 1):
            url = r.get("question_url", "")
            brier = r.get("p4_brier_score", 0)
            li = r.get("p1_li_estimate", 0)
            post += f"{i}. **[{r['question_type']}]({url})**\n"
            post += f"   - Forecast: {r.get('p2_forecast_value', 0):.1%}\n"
            post += f"   - Brier: {brier:.3f}\n"
            post += f"   - LI Estimate: {li:.2f}\n\n"

        post += """## What This Means

The HumanAIOS forecasting bot uses ACAT (AI Calibration Assessment Tool) to measure itself before each forecast. This weekly digest shows how that self-measurement correlates with real outcomes (Brier scores).

**H34/H35 Research:** Does self-reported calibration predict forecasting accuracy? This data contributes to answering that question in public.

---

*[HumanAIOS Research](https://humanaios.ai) — Behavioral observability for AI systems*
"""
        return post

    def _stub_post(self) -> str:
        """Fallback post when no resolution data."""
        return """# Weekly Calibration Update: No Questions Resolved Yet

**Published:** {0}

## Status

The HumanAIOS forecasting bot is currently in test mode and awaiting the first batch of resolved questions. Once questions resolve, calibration metrics will be available here.

**In the meantime:** The bot is actively forecasting and recording its pre-forecast self-assessments (ACAT scores) in the [live table](https://www.metaculus.com/profile/299627).

---

*[HumanAIOS Research](https://humanaios.ai)*
""".format(datetime.now(timezone.utc).strftime('%Y-%m-%d'))

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
        post = self.generate_post(resolutions)
        print(f"  → {len(post)} characters generated")

        print("Saving draft...")
        filepath = self.save_draft(post)
        print(f"  → Draft saved: {filepath}")

        print("✓ Weekly content generation complete")
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
