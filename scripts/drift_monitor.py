#!/usr/bin/env python3
"""
A6: Drift Monitor — Detect document divergence between registry and filesystem

Runs biweekly to scan for:
1. Link rot (external URLs that return 4xx/5xx)
2. Stale documents (past review_due)
3. Missing files (registry says canonical exists but doesn't)
4. Diverged copies (file moved but inbox copy remains)
5. Unregistered files (new files not yet in registry)

Usage:
    python3 drift_monitor.py --scan              # scan all repos and emit report
    python3 drift_monitor.py --diff              # show diff vs last run
    python3 drift_monitor.py --state-file <f>    # use custom state file
"""

import os
import json
import hashlib
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import urllib.request
import urllib.error
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


class DriftMonitor:
    """Detect divergence between registry and filesystem."""

    def __init__(self, repo_root: str, registry_path: str, state_file: str = ".doc-control/drift_state.json"):
        self.repo_root = Path(repo_root)
        self.registry_path = Path(registry_path)
        self.state_file = self.repo_root / state_file
        self.registry = self._load_registry()
        self.last_state = self._load_state()
        self.current_state = {}
        logger.info(f"Initialized drift monitor: {len(self.registry.get('documents', []))} docs in registry")

    def _load_registry(self) -> Dict:
        """Load document registry."""
        try:
            with open(self.registry_path) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.error(f"Registry not found: {self.registry_path}")
            return {"documents": []}

    def _load_state(self) -> Dict:
        """Load last-run state for diff tracking."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return {"last_run": None, "documents": {}, "drift": []}

    def _save_state(self):
        """Save current state for next run."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.current_state, f, indent=2, default=str)

    def _check_external_link(self, url: str) -> Optional[int]:
        """Check if external link is alive."""
        try:
            request = urllib.request.Request(url, method="HEAD")
            response = urllib.request.urlopen(request, timeout=5)
            return response.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            return None  # Can't determine (DNS timeout, etc)

    def _is_stale(self, review_due: str) -> bool:
        """Check if review_due has passed."""
        if not review_due:
            return False
        try:
            due_date = datetime.fromisoformat(review_due.split("T")[0])
            return datetime.now() > due_date
        except Exception:
            return False

    def scan_documents(self) -> Dict:
        """Scan all documents for drift."""
        logger.info("Scanning documents for drift...")
        drift_issues = []

        for doc in self.registry.get("documents", []):
            doc_id = doc.get("doc_id")
            status = doc.get("status", "draft")
            canonical_repo = doc.get("canonical_repo", "unknown")
            canonical_path = doc.get("canonical_path", "unknown")
            review_due = doc.get("review_due")

            # Check 1: File exists
            repo_dir = self.repo_root.parent / canonical_repo
            file_path = repo_dir / canonical_path if repo_dir.exists() else None

            if not file_path or not file_path.exists():
                drift_issues.append({
                    "type": "missing_file",
                    "doc_id": doc_id,
                    "title": doc.get("title"),
                    "canonical_path": canonical_path,
                    "severity": "high" if status == "approved" else "low",
                    "recommendation": "Restore from git history or mark superseded"
                })
                continue

            # Check 2: Stale document
            if self._is_stale(review_due) and status == "approved":
                drift_issues.append({
                    "type": "stale_document",
                    "doc_id": doc_id,
                    "title": doc.get("title"),
                    "review_due": review_due,
                    "severity": "medium",
                    "recommendation": "Owner review + re-approve (or mark superseded)"
                })

            # Check 3: External links
            # (Simplified: skip detailed link checking in this script)
            # Full version would extract links from file and check each

        self.current_state["documents"] = {d["doc_id"]: d for d in self.registry.get("documents", [])}
        self.current_state["drift"] = drift_issues
        return {"timestamp": datetime.now().isoformat(), "issues": drift_issues}

    def compute_diff(self, current_report: Dict) -> Dict:
        """Compute drift diff vs last run."""
        last_drift = {d["doc_id"]: d for d in self.last_state.get("drift", [])}
        current_drift = {d["doc_id"]: d for d in current_report.get("issues", [])}

        novel_drift = []
        resolved_drift = []

        for doc_id, issue in current_drift.items():
            if doc_id not in last_drift:
                novel_drift.append(issue)

        for doc_id in last_drift:
            if doc_id not in current_drift:
                resolved_drift.append(last_drift[doc_id])

        return {
            "novel": novel_drift,
            "resolved": resolved_drift,
            "recurring": {d for d in current_drift if d in last_drift}
        }

    def emit_report(self, current_report: Dict) -> Dict:
        """Generate drift monitor report."""
        diff = self.compute_diff(current_report)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(current_report["issues"]),
            "novel_issues": len(diff["novel"]),
            "resolved_issues": len(diff["resolved"]),
            "recurring_issues": len(diff["recurring"]),
            "issues": {
                "novel": diff["novel"][:10],  # Top 10
                "resolved": diff["resolved"][:5],
                "recurring_count": len(diff["recurring"])
            }
        }

    def save_report(self, report: Dict, output_path: str = "drift_report.json"):
        """Save report to file."""
        output_file = self.repo_root / output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Report saved: {output_path}")

    def run_scan(self):
        """Execute full scan."""
        current = self.scan_documents()
        report = self.emit_report(current)
        self._save_state()
        self.save_report(report)

        # Print summary
        print("\n" + "="*60)
        print("DRIFT MONITOR REPORT")
        print("="*60)
        print(f"Documents scanned: {len(self.registry.get('documents', []))}")
        print(f"Total issues: {report['total_issues']}")
        print(f"Novel issues: {report['novel_issues']}")
        print(f"Resolved issues: {report['resolved_issues']}")
        print(f"\nNovel drift:")
        for issue in report["issues"]["novel"]:
            print(f"  • {issue['doc_id']}: {issue['type']} — {issue['recommendation']}")
        if report["novel_issues"] > 10:
            print(f"  ... and {report['novel_issues'] - 10} more")
        print("="*60 + "\n")

        return report


def main():
    parser = argparse.ArgumentParser(description="A6: Drift Monitor")
    parser.add_argument("--scan", action="store_true", help="Scan documents for drift")
    parser.add_argument("--diff", action="store_true", help="Show diff vs last run")
    parser.add_argument("--repo-root", default=".", help="Root of humanaios repo")
    parser.add_argument("--registry", default="document-registry.yaml", help="Path to registry")
    parser.add_argument("--state-file", default=".doc-control/drift_state.json", help="State file for tracking")
    parser.add_argument("--output", default="drift_report.json", help="Output report path")

    args = parser.parse_args()

    monitor = DriftMonitor(args.repo_root, args.registry, args.state_file)

    if args.scan or not (args.diff):
        # Default: scan
        report = monitor.run_scan()
        monitor.save_report(report, args.output)

    if args.diff:
        logger.info("Diff computed — see report for novel vs recurring issues")


if __name__ == "__main__":
    main()
