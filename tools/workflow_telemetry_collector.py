#!/usr/bin/env python3
"""
Workflow Telemetry Collector

Aggregates workflow behavioral telemetry emitted by GitHub Actions workflows
(quality-baseline.yml, governance-files.yml) to understand:
- When workflows trigger/skip
- PR intent vs. actual workflow execution
- Patterns in deployment frequency
- Edge cases and unexpected behavior

Usage:
  python3 workflow_telemetry_collector.py <artifact_dir> [output_file]

Example:
  python3 workflow_telemetry_collector.py ./workflow_telemetry workflow_analysis.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def collect_telemetry(artifact_dir: str) -> Dict[str, Any]:
    """
    Collect all telemetry files from workflow artifact directory.
    Returns aggregated behavioral data for analysis.
    """
    artifact_path = Path(artifact_dir)

    if not artifact_path.exists():
        return {
            "error": f"Artifact directory not found: {artifact_dir}",
            "collection_period": None,
            "workflows": {}
        }

    telemetry_files = list(artifact_path.glob("*.json"))

    data = {
        "collection_period": {
            "start": None,
            "end": None,
            "file_count": len(telemetry_files)
        },
        "workflows": {
            "quality-baseline": {
                "runs": 0,
                "successful": 0,
                "failed": 0,
                "path_filter_hits": 0,
                "trigger_reasons": {},
                "avg_duration_seconds": None
            },
            "governance-files": {
                "runs": 0,
                "successful": 0,
                "failed": 0,
                "path_filter_hits": 0,
                "trigger_reasons": {},
                "avg_duration_seconds": None
            }
        },
        "pr_patterns": {
            "code_only": 0,
            "governance_only": 0,
            "mixed": 0,
            "docs_only": 0,
            "dependency_only": 0,
            "other": 0
        },
        "per_workflow_details": []
    }

    if len(telemetry_files) == 0:
        return data

    # Aggregate telemetry files
    for telemetry_file in sorted(telemetry_files):
        try:
            with open(telemetry_file) as f:
                record = json.load(f)
        except:
            continue

        # Update time range
        if "timestamp" in record:
            ts = record["timestamp"]
            if data["collection_period"]["start"] is None:
                data["collection_period"]["start"] = ts
            data["collection_period"]["end"] = ts

        workflow = record.get("workflow")
        if workflow not in data["workflows"]:
            continue

        # Aggregate workflow-level stats
        data["workflows"][workflow]["runs"] += 1

        if record.get("validation_result") == "success":
            data["workflows"][workflow]["successful"] += 1
        else:
            data["workflows"][workflow]["failed"] += 1

        if record.get("path_filter_hit"):
            data["workflows"][workflow]["path_filter_hits"] += 1

        # Track trigger reasons
        trigger = record.get("trigger_reason", "unknown")
        if trigger not in data["workflows"][workflow]["trigger_reasons"]:
            data["workflows"][workflow]["trigger_reasons"][trigger] = 0
        data["workflows"][workflow]["trigger_reasons"][trigger] += 1

        # Classify PR intent
        files_changed = record.get("files_changed", [])
        if files_changed:
            classify_pr_intent(files_changed, data["pr_patterns"])

        # Store full record for detailed analysis
        data["per_workflow_details"].append(record)

    return data


def classify_pr_intent(files_changed: List[str], patterns: Dict[str, int]):
    """
    Classify PR intent based on files changed.
    Updates patterns dict with classification.
    """
    has_code = any(f.startswith(("src/", "tools/", "acat/", "tests/")) for f in files_changed)
    has_governance = any(f.startswith(".gov-control/") or f == "GOVERNANCE_FILES.md" for f in files_changed)
    has_docs = any(f.endswith(".md") and not f == "GOVERNANCE_FILES.md" for f in files_changed)
    has_dependencies = any(f in ("requirements.txt", "setup.py", "pyproject.toml") for f in files_changed)

    if has_code and not has_governance and not has_docs and not has_dependencies:
        patterns["code_only"] += 1
    elif has_governance and not has_code:
        patterns["governance_only"] += 1
    elif has_docs and not has_code and not has_governance:
        patterns["docs_only"] += 1
    elif has_dependencies and not has_code and not has_governance:
        patterns["dependency_only"] += 1
    elif has_code or has_governance or has_docs or has_dependencies:
        patterns["mixed"] += 1
    else:
        patterns["other"] += 1


def format_report(data: Dict[str, Any]) -> str:
    """Format aggregated telemetry data as human-readable report."""
    lines = []

    lines.append("=" * 70)
    lines.append("WORKFLOW TELEMETRY ANALYSIS REPORT")
    lines.append("=" * 70)

    # Collection period
    period = data.get("collection_period", {})
    lines.append(f"\nCollection Period: {period.get('start')} to {period.get('end')}")
    lines.append(f"Files Analyzed: {period.get('file_count', 0)}")

    # Per-workflow summary
    lines.append("\n" + "=" * 70)
    lines.append("WORKFLOW EXECUTION SUMMARY")
    lines.append("=" * 70)

    for workflow_name, stats in data.get("workflows", {}).items():
        lines.append(f"\n{workflow_name}:")
        lines.append(f"  Total Runs: {stats['runs']}")
        lines.append(f"  Successful: {stats['successful']}")
        lines.append(f"  Failed: {stats['failed']}")
        lines.append(f"  Path Filter Hits: {stats['path_filter_hits']}")

        if stats['trigger_reasons']:
            lines.append(f"  Trigger Reasons:")
            for reason, count in stats['trigger_reasons'].items():
                lines.append(f"    - {reason}: {count}")

    # PR patterns
    lines.append("\n" + "=" * 70)
    lines.append("PR PATTERN ANALYSIS")
    lines.append("=" * 70)
    patterns = data.get("pr_patterns", {})
    for pattern, count in patterns.items():
        if count > 0:
            lines.append(f"  {pattern}: {count}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_telemetry_collector.py <artifact_dir> [output_file]")
        print("Example: workflow_telemetry_collector.py ./workflow_telemetry/ report.json")
        sys.exit(2)

    artifact_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    data = collect_telemetry(artifact_dir)

    # Print report
    print(format_report(data))

    # Save JSON if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Telemetry data saved to: {output_file}")


if __name__ == "__main__":
    main()
