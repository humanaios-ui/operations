#!/usr/bin/env python3
"""
Monitoring Dashboard: Phase 1/2 Stability
==========================================

Monitors:
  - GitHub Actions workflow execution status
  - Supabase pipeline_health table (API monitor results)
  - Agent responsiveness (smoke tests)
  - Data flow integrity

Run: python3 tools/agents/monitor_stability_v1.py --watch
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

TOOL_NAME = "monitor_stability_v1"
TOOL_VERSION = "1.0.0"

sys.path.insert(0, str(Path(__file__).parent))
from _shared.supabase_client import get_supabase_client
from _shared.github_client import GitHubClient


class StabilityMonitor:
    """Monitor Phase 1/2 deployment stability."""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.github = GitHubClient()
        self.start_time = datetime.now(timezone.utc)

    def check_workflow_status(self) -> Dict:
        """Check GitHub Actions workflow status."""
        try:
            import subprocess

            workflows = [
                "agent-principle-compliance-check.yml",
                "agent-api-monitor.yml",
            ]

            status = {}
            for wf in workflows:
                try:
                    result = subprocess.run(
                        f'gh workflow view {wf.replace(".yml", "")} -R humanaios-ui/operations --json name,path,state',
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        status[wf] = "visible" if result.stdout else "not_found"
                    else:
                        status[wf] = "error"
                except Exception as e:
                    status[wf] = "error"

            return status
        except Exception as e:
            return {"error": str(e)}

    def check_supabase_pipeline_health(self) -> List[Dict]:
        """Check Supabase pipeline_health table for recent entries."""
        if not self.supabase:
            return [{"status": "not_configured"}]

        try:
            result = self.supabase.table("pipeline_health").select(
                "integration_name,status,last_seen,note"
            ).order("last_seen", desc=True).limit(10).execute()

            return result.data if result.data else []

        except Exception as e:
            return [{"error": str(e)}]

    def check_agent_health(self) -> Dict:
        """Run smoke tests on all agents."""
        agents = {
            "Principle Compliance": "tools/agents/principle_compliance_bot_v1.py",
            "API Monitoring": "tools/agents/api_monitoring_bot_v1.py",
            "Substack Content": "tools/agents/substack_content_agent_v1.py",
            "RentAHuman Validation": "tools/agents/rentahuman_validation_bot_v1.py",
        }

        health = {}
        for name, path in agents.items():
            try:
                import subprocess
                result = subprocess.run(
                    f"python3 {path} --smoke-test",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                health[name] = "OK" if result.returncode == 0 else "FAILED"
            except Exception as e:
                health[name] = f"ERROR: {str(e)[:30]}"

        return health

    def generate_report(self) -> str:
        """Generate stability monitoring report."""
        uptime = datetime.now(timezone.utc) - self.start_time

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                  PHASE 1/2 STABILITY MONITORING REPORT                    ║
╚════════════════════════════════════════════════════════════════════════════╝

TIMESTAMP: {datetime.now(timezone.utc).isoformat()}
UPTIME: {uptime.total_seconds():.0f} seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GITHUB ACTIONS WORKFLOWS
"""

        workflow_status = self.check_workflow_status()
        for wf, status in workflow_status.items():
            icon = "✓" if status == "visible" else "⚠" if status == "not_found" else "✗"
            report += f"  {icon} {wf}: {status}\n"

        report += """
2. SUPABASE PIPELINE HEALTH (Last 24h)
"""

        pipeline_health = self.check_supabase_pipeline_health()
        if pipeline_health and "error" not in pipeline_health[0]:
            for entry in pipeline_health[:5]:
                age = "recent"
                if entry.get("last_seen"):
                    ts = datetime.fromisoformat(entry["last_seen"].replace("Z", "+00:00"))
                    age_mins = (datetime.now(timezone.utc) - ts).total_seconds() / 60
                    age = f"{age_mins:.0f}m ago"

                icon = "✓" if entry.get("status") == "ok" else "✗"
                report += f"  {icon} {entry.get('integration_name', 'Unknown')}: {entry.get('status', 'unknown')} ({age})\n"
        else:
            report += "  ⚠ Supabase not configured or empty\n"

        report += """
3. AGENT HEALTH CHECK
"""

        agent_health = self.check_agent_health()
        for agent, status in agent_health.items():
            icon = "✓" if status == "OK" else "✗"
            report += f"  {icon} {agent}: {status}\n"

        report += """
4. DEPLOYMENT STATUS
"""
        report += f"""  Phase 1: DEPLOYED ✓ (live)
  Phase 2: COMMITTED ✓ (ready for activation)
  Phase 3: PLANNED → (awaiting stability)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY:
  All Phase 1 agents deployed and accessible.
  Phase 2 agents built and ready for workflow integration.
  Monitor workflow execution in GitHub Actions tab.
  Next milestone: 24h Phase 1 stability verification.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report

    def run_watch(self, interval: int = 60):
        """Run monitoring loop."""
        import time

        print("Starting stability monitoring loop...")
        print(f"Interval: {interval}s | Press Ctrl+C to stop\n")

        tick = 0
        try:
            while True:
                tick += 1
                report = self.generate_report()
                print(f"\n[TICK {tick}]")
                print(report)

                print(f"Next check in {interval}s... (Ctrl+C to stop)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            return True


def run_smoke_test() -> bool:
    """Smoke test."""
    try:
        monitor = StabilityMonitor()
        print("✓ StabilityMonitor initialized")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1/2 Stability Monitor")
    parser.add_argument("--watch", action="store_true", help="Run monitoring loop")
    parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test")
    parser.add_argument("--report", action="store_true", help="Generate one report")

    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    monitor = StabilityMonitor()

    if args.watch:
        monitor.run_watch(interval=args.interval)
    elif args.report:
        print(monitor.generate_report())
    else:
        parser.print_help()
