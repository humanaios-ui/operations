#!/usr/bin/env python3
"""smag_to_empirica_connector — wire SMAG rows to empirica CLI for trajectory generation.

Converts predicted-vs-measured rows from the SMAG pilot ledger into empirica
findings/decisions/trajectories. This closes the gap between mechanical SMAG
(capture → consolidate → analyze) and the learning trajectory layer.

Each SMAG row becomes:
  - Finding: observed outcome (gap between predicted and measured)
  - Decision: inferred remediation strategy
  - Edges: trajectory chain (gap → remedy → prediction)

Usage:
  python3 smag_to_empirica_connector.py \
    --ledger audits/smag_pilot_ledger.jsonl \
    --output JSON | empirica log-artifacts -

  python3 smag_to_empirica_connector.py \
    --ledger audits/smag_pilot_ledger.jsonl \
    --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Outcome classification patterns (from smag_gap_analysis_v1_0.py)
MERGED_RE = re.compile(r"merged\s*=\s*(True|False)", re.IGNORECASE)
FAIL_RE = re.compile(r"failure:\s*(\d+)")
INPROG_RE = re.compile(r"in_progress:\s*(\d+)")
SUCCESS_RE = re.compile(r"success:\s*(\d+)")


def classify_outcome(measured: str) -> tuple[str, dict[str, int]]:
    """Classify outcome from measured string.

    Returns (classification, counts) where classification is one of:
      clean    = merged AND failure=0 AND in_progress=0 AND success>0
      friction = merged AND failure>0
      pending  = merged AND in_progress>0 AND failure=0
      miss     = not merged
      unknown  = unparseable

    counts dict contains failure, in_progress, success counts.
    """
    counts = {
        "failure": int(FAIL_RE.search(measured or "").group(1))
        if FAIL_RE.search(measured or "")
        else 0,
        "in_progress": int(INPROG_RE.search(measured or "").group(1))
        if INPROG_RE.search(measured or "")
        else 0,
        "success": int(SUCCESS_RE.search(measured or "").group(1))
        if SUCCESS_RE.search(measured or "")
        else 0,
    }

    merged_match = MERGED_RE.search(measured or "")
    if not merged_match:
        return "unknown", counts

    if merged_match.group(1).lower() != "true":
        return "miss", counts

    if counts["failure"] > 0:
        return "friction", counts

    if counts["in_progress"] > 0:
        return "pending", counts

    return "clean" if counts["success"] > 0 else "pending", counts


def compute_gap_magnitude(outcome: str, counts: dict[str, int]) -> float:
    """Compute gap magnitude (0.0-1.0) from outcome classification.

    clean    = 0.0 (no gap)
    pending  = 0.2 (un-measured, defer judgment)
    friction = 0.8 (merged but checks failed)
    miss     = 1.0 (predicted but didn't land)
    unknown  = 0.5 (uncertain)
    """
    gap_map = {
        "clean": 0.0,
        "pending": 0.2,
        "friction": 0.8,
        "miss": 1.0,
        "unknown": 0.5,
    }
    return gap_map.get(outcome, 0.5)


def infer_remediation(outcome: str, measured: str, failing_checks: list[str]) -> str:
    """Infer remediation strategy from outcome."""
    if outcome == "clean":
        return "Outcome matched prediction. No remediation needed."
    elif outcome == "friction":
        checks_str = ", ".join(failing_checks) if failing_checks else "unknown"
        return f"Merged but {len(failing_checks) or '?'} checks failed ({checks_str}). Diagnose check failures and update tooling/process."
    elif outcome == "pending":
        return "Merged but CI still in progress at capture time. Re-check terminal state in next consolidation cycle."
    elif outcome == "miss":
        return "PR predicted to merge but didn't. Review blocking issues and re-queue or close."
    else:
        return "Unable to classify outcome. Manual review needed."


def convert_smag_row(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    """Convert one SMAG row to empirica artifacts + edges.

    Returns: {"nodes": [...], "edges": [...]}
    """
    pr_id = row.get("pr", "?")
    task = row.get("task", "unknown")
    substrate = row.get("substrate", "unknown")
    measured = row.get("measured", "")
    failing_checks = row.get("failing_checks", [])

    # Classify outcome
    outcome, counts = classify_outcome(measured)
    gap_mag = compute_gap_magnitude(outcome, counts)

    # Generate finding (gap observed)
    finding_ref = f"gap_pr{pr_id}"
    finding_node = {
        "ref": finding_ref,
        "type": "finding",
        "data": {
            "finding": f"PR #{pr_id}: {outcome} outcome. {task[:60]}{'...' if len(task) > 60 else ''}",
            "description": f"**Measured outcome:** {measured}\n"
            f"**Gap magnitude:** {gap_mag:.1%}\n"
            f"**Substrate:** {substrate}\n"
            f"**Failing checks:** {', '.join(failing_checks) if failing_checks else '(none)'}",
            "impact": gap_mag,
            "visibility": "shared",
        },
    }

    # Generate decision (remediation inferred)
    decision_ref = f"remedy_pr{pr_id}"
    remediation = infer_remediation(outcome, measured, failing_checks)
    decision_node = {
        "ref": decision_ref,
        "type": "decision",
        "data": {
            "choice": f"Address {outcome} outcome for PR #{pr_id}",
            "rationale": remediation,
            "reversibility": "exploratory",
        },
    }

    # Create edges (trajectory)
    edges = [
        {"from": finding_ref, "to": decision_ref, "relation": "grounded_by"},
        {"from": decision_ref, "to": finding_ref, "relation": "caused_by"},
    ]

    return {"nodes": [finding_node, decision_node], "edges": edges}


def load_ledger(ledger_path: str) -> list[dict[str, Any]]:
    """Load SMAG ledger.jsonl."""
    rows = []
    with open(ledger_path) as f:
        for i, line in enumerate(f, 1):
            try:
                row = json.loads(line.strip())
                rows.append(row)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed row {i}: {e}", file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Convert SMAG rows to empirica artifacts."
    )
    parser.add_argument(
        "--ledger",
        default="audits/smag_pilot_ledger.jsonl",
        help="Path to SMAG ledger",
    )
    parser.add_argument(
        "--output",
        choices=["json", "human"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't emit JSON, just summarize",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Load ledger
    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"Error: ledger not found: {ledger_path}", file=sys.stderr)
        return 1

    rows = load_ledger(str(ledger_path))
    if args.verbose:
        print(f"Loaded {len(rows)} SMAG rows", file=sys.stderr)

    # Convert to empirica artifacts
    all_nodes = []
    all_edges = []

    for i, row in enumerate(rows, 1):
        batch = convert_smag_row(row, i)
        all_nodes.extend(batch["nodes"])
        all_edges.extend(batch["edges"])

    # Dry-run: summarize
    if args.dry_run:
        print(f"Converted {len(rows)} SMAG rows", file=sys.stderr)
        print(f"Generated {len(all_nodes)} empirica artifacts", file=sys.stderr)
        print(f"Created {len(all_edges)} edges (trajectories)", file=sys.stderr)

        # Show sample
        if all_nodes:
            sample = all_nodes[0]
            print(f"\nSample artifact:\n{json.dumps(sample, indent=2)}", file=sys.stderr)
        return 0

    # Emit JSON for piping to empirica log-artifacts
    output = {"nodes": all_nodes, "edges": all_edges}

    if args.output == "json":
        print(json.dumps(output, indent=2))
    else:
        print(f"Converted {len(rows)} SMAG rows → {len(all_nodes)} artifacts")
        print(f"Edges: {len(all_edges)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
