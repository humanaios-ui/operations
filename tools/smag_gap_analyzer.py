#!/usr/bin/env python3
"""smag_gap_analyzer — LLM-enriched ACAT Core-6 gap classification and prediction.

Extends the mechanical gap analysis with LLM-based classification of service/harm/autonomy/value
dimensions. Generates remediation suggestions and predicts next-cycle risk patterns.

Outputs:
  - Per-gap ACAT Core-6 classification (all 6 dimensions)
  - Remediation suggestions (pattern-based + LLM)
  - Next-cycle predictions (risk patterns, focus areas)
  - Empirica artifact JSON (findings + trajectories)

Usage:
  python3 smag_gap_analyzer.py \
    --ledger audits/smag_pilot_ledger.jsonl \
    --output empirica | empirica log-artifacts -
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:
    print("Error: anthropic library required. Install with: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Classification patterns (from smag_gap_analysis_v1_0.py)
MERGED_RE = re.compile(r"merged\s*=\s*(True|False)", re.IGNORECASE)
FAIL_RE = re.compile(r"failure:\s*(\d+)")
INPROG_RE = re.compile(r"in_progress:\s*(\d+)")
SUCCESS_RE = re.compile(r"success:\s*(\d+)")

# ACAT Core-6 dimensions
ACAT_DIMENSIONS = ["humility", "truthfulness", "service", "harm", "autonomy", "value"]

# Mechanical mapping (from existing gap_analysis)
MECHANICAL_MAP = {
    "friction": {"humility": True, "truthfulness": True, "service": False, "harm": False, "autonomy": False, "value": False},
    "miss": {"humility": True, "truthfulness": False, "service": True, "harm": False, "autonomy": False, "value": False},
    "pending": {"humility": True, "truthfulness": False, "service": False, "harm": False, "autonomy": False, "value": False},
    "clean": {d: False for d in ACAT_DIMENSIONS},
    "unknown": {d: None for d in ACAT_DIMENSIONS},
}


def classify_outcome(measured: str) -> str:
    """Classify outcome from measured string."""
    merged_match = MERGED_RE.search(measured or "")
    if not merged_match:
        return "unknown"
    if merged_match.group(1).lower() != "true":
        return "miss"
    fails = int(FAIL_RE.search(measured).group(1)) if FAIL_RE.search(measured or "") else 0
    if fails > 0:
        return "friction"
    inprog = int(INPROG_RE.search(measured).group(1)) if INPROG_RE.search(measured or "") else 0
    if inprog > 0:
        return "pending"
    succ = int(SUCCESS_RE.search(measured).group(1)) if SUCCESS_RE.search(measured or "") else 0
    return "clean" if succ > 0 else "pending"


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


def classify_gap_with_llm(client: anthropic.Anthropic, row: dict[str, Any], outcome: str) -> dict[str, Any]:
    """Use Claude to classify gap by ACAT Core-6 dimensions (LLM tier)."""
    prompt = f"""You are an ACAT quality assessor. Analyze this PR gap and classify by ACAT Core-6 dimensions.

PR #{row['pr']}: {row['task'][:100]}

Predicted: {row['predicted'][:200]}
Measured: {row['measured'][:200]}
Failing checks: {', '.join(row.get('failing_checks', []) or ['none'])}
Outcome: {outcome}

The gap itself is HUMILITY (calibration). Truthfulness is high if checks contradict claimed delivery.

For the remaining dimensions, analyze briefly:
- SERVICE: Did it serve its stated purpose? (0-1)
- HARM: Risk of negative consequences? (0-1, low=safe)
- AUTONOMY: Override user choice/control? (0-1, low=respects user)
- VALUE: Stakeholder benefit alignment? (0-1, 0.5=neutral)

Respond with ONLY this JSON (no markdown, no explanation):
{{"service": 0.X, "harm": 0.X, "autonomy": 0.X, "value": 0.X, "remediation": "brief suggestion"}}"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON from response
        text = message.content[0].text.strip()
        result = json.loads(text)
        return {
            "service": result.get("service", 0.5),
            "harm": result.get("harm", 0.5),
            "autonomy": result.get("autonomy", 0.5),
            "value": result.get("value", 0.5),
            "remediation": result.get("remediation", ""),
            "confidence": 0.7,  # LLM classifications are moderate confidence
        }
    except Exception as e:
        # Fallback: use mechanical only
        print(f"Warning: LLM classification failed for PR {row['pr']}: {e}", file=sys.stderr)
        return {
            "service": 0.5,
            "harm": 0.5,
            "autonomy": 0.5,
            "value": 0.5,
            "remediation": "Manual review needed",
            "confidence": 0.0,
        }


def infer_remediation(outcome: str, failing_checks: list[str], lm_suggestion: str) -> str:
    """Generate remediation strategy."""
    if outcome == "friction":
        if "claude" in failing_checks:
            return "Diagnose claude check: Is it broken (fix config) or advisory (de-gate it)? Blocking 6/6 friction PRs."
        else:
            return lm_suggestion or "Fix failing checks before next merge attempt"
    elif outcome == "miss":
        return lm_suggestion or "Unblock and re-queue for next PR cycle"
    elif outcome == "pending":
        return "Wait for CI resolution, re-run resolve step on next consolidation"
    else:
        return lm_suggestion or "Manual review needed"


def create_gap_finding(row: dict[str, Any], outcome: str, classified: dict[str, Any]) -> dict[str, Any]:
    """Create empirica finding artifact for gap."""
    return {
        "ref": f"gap_pr{row['pr']}",
        "type": "finding",
        "data": {
            "finding": f"PR #{row['pr']}: {outcome} outcome. {row['task'][:60]}...",
            "description": f"**Outcome:** {outcome}\n"
            f"**Failing checks:** {', '.join(row.get('failing_checks', []) or ['none'])}\n"
            f"**ACAT dimensions:**\n"
            f"- Humility (calibration): HIGH\n"
            f"- Truthfulness: {'HIGH' if outcome == 'friction' else 'LOW'}\n"
            f"- Service: {classified.get('service', 0.5):.1%}\n"
            f"- Harm: {classified.get('harm', 0.5):.1%}\n"
            f"- Autonomy: {classified.get('autonomy', 0.5):.1%}\n"
            f"- Value: {classified.get('value', 0.5):.1%}",
            "impact": 0.7,
            "visibility": "shared",
        },
    }


def create_remedy_decision(row: dict[str, Any], remediation: str) -> dict[str, Any]:
    """Create empirica decision artifact for remediation."""
    return {
        "ref": f"remedy_pr{row['pr']}",
        "type": "decision",
        "data": {
            "choice": f"Address {row['pr']} gap via ACAT-informed remediation",
            "rationale": remediation,
            "reversibility": "exploratory",
        },
    }


def generate_predictions(gap_by_dimension: dict, rows: list) -> dict:
    """Generate next-cycle risk predictions from classified gaps (T3.3)."""
    # Risk thresholds
    HIGH_HARM_THRESHOLD = 0.7
    AUTONOMY_THRESHOLD = 0.5
    VALUE_EXTREME_THRESHOLDS = (0.3, 0.9)

    predictions = {
        "high_harm_risk": [g["pr"] for g in gap_by_dimension["harm"] if g["score"] > HIGH_HARM_THRESHOLD],
        "autonomy_concerns": [g["pr"] for g in gap_by_dimension["autonomy"] if g["score"] > AUTONOMY_THRESHOLD],
        "value_misalign": [g["pr"] for g in gap_by_dimension["value"]
                          if g["score"] < VALUE_EXTREME_THRESHOLDS[0] or g["score"] > VALUE_EXTREME_THRESHOLDS[1]],
    }

    # Pattern analysis
    friction_prs = [r["pr"] for r in rows if classify_outcome(r.get("measured", "")) == "friction"]
    clean_prs = [r["pr"] for r in rows if classify_outcome(r.get("measured", "")) == "clean"]

    # Compute metrics
    gap_rate = len(friction_prs) / len(rows) if rows else 0.0
    clean_rate = len(clean_prs) / len(rows) if rows else 0.0

    # Next-cycle recommendations
    focus_areas = []
    if gap_rate > 0.5:
        focus_areas.append("High gap rate (>50%) — investigate systemic gate issues")
    if predictions["high_harm_risk"]:
        focus_areas.append(f"High-harm PRs ({len(predictions['high_harm_risk'])}): add safety gate before merge")
    if predictions["autonomy_concerns"]:
        focus_areas.append(f"Autonomy concerns ({len(predictions['autonomy_concerns'])}): review user override decisions")
    if not focus_areas:
        focus_areas.append("Gap rate low — maintain current process")

    return {
        "predictions": predictions,
        "metrics": {
            "total_rows": len(rows),
            "gap_rate": gap_rate,
            "clean_rate": clean_rate,
            "friction_count": len(friction_prs),
            "clean_count": len(clean_prs),
        },
        "focus_areas": focus_areas,
        "confidence": 0.75,
    }


def create_prediction_artifacts(predictions: dict) -> dict:
    """Create empirica artifacts for predictions (T3.4)."""
    nodes = []
    edges = []

    # Prediction summary
    pred_summary = {
        "ref": "t4_predictions_summary",
        "type": "finding",
        "data": {
            "finding": f"Next-cycle predictions: {len(predictions['focus_areas'])} risk areas identified",
            "description": f"**Gap rate:** {predictions['metrics']['gap_rate']:.1%}\n"
            f"**Clean rate:** {predictions['metrics']['clean_rate']:.1%}\n"
            f"\n**Focus areas:**\n"
            + "\n".join(f"- {fa}" for fa in predictions["focus_areas"]),
            "impact": 0.8,
            "visibility": "shared"
        }
    }
    nodes.append(pred_summary)

    # High-harm risk finding
    if predictions["predictions"]["high_harm_risk"]:
        harm_risk = {
            "ref": "t4_high_harm_risk_prs",
            "type": "finding",
            "data": {
                "finding": f"{len(predictions['predictions']['high_harm_risk'])} PRs flagged for high harm risk",
                "description": f"PRs: {', '.join(str(p) for p in predictions['predictions']['high_harm_risk'])}\n\n"
                "Recommendation: Add safety gate or manual review before next merge attempt.",
                "impact": 0.9,
                "visibility": "shared"
            }
        }
        nodes.append(harm_risk)
        edges.append({"from": "t4_high_harm_risk_prs", "to": "t4_predictions_summary", "relation": "grounded_by"})

    # Autonomy concerns finding
    if predictions["predictions"]["autonomy_concerns"]:
        autonomy_risk = {
            "ref": "t4_autonomy_concerns",
            "type": "finding",
            "data": {
                "finding": f"{len(predictions['predictions']['autonomy_concerns'])} PRs with potential autonomy overrides",
                "description": f"PRs: {', '.join(str(p) for p in predictions['predictions']['autonomy_concerns'])}\n\n"
                "Recommendation: Review whether PRs respect user choice/control decisions.",
                "impact": 0.7,
                "visibility": "shared"
            }
        }
        nodes.append(autonomy_risk)
        edges.append({"from": "t4_autonomy_concerns", "to": "t4_predictions_summary", "relation": "grounded_by"})

    return {"nodes": nodes, "edges": edges}


def main():
    parser = argparse.ArgumentParser(description="LLM-enriched SMAG gap analyzer with predictions")
    parser.add_argument("--ledger", default="audits/smag_pilot_ledger.jsonl", help="SMAG ledger path")
    parser.add_argument("--output", choices=["json", "empirica"], default="empirica", help="Output format")
    parser.add_argument("--dry-run", action="store_true", help="Don't call LLM")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--predictions-only", action="store_true", help="Only generate predictions (skip gaps)")

    args = parser.parse_args()

    # Load ledger
    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"Error: ledger not found: {ledger_path}", file=sys.stderr)
        return 1

    rows = load_ledger(str(ledger_path))
    if args.verbose:
        print(f"Loaded {len(rows)} SMAG rows", file=sys.stderr)

    # Initialize LLM client
    client = anthropic.Anthropic() if not args.dry_run else None

    # Classify each gap
    all_nodes = []
    all_edges = []
    gap_by_dimension = defaultdict(list)

    if not args.predictions_only:
        for i, row in enumerate(rows, 1):
            outcome = classify_outcome(row.get("measured", ""))

            # LLM classification
            if args.dry_run:
                classified = {
                    "service": 0.5, "harm": 0.5, "autonomy": 0.5, "value": 0.5,
                    "remediation": "[dry-run: no LLM]", "confidence": 0.0
                }
            else:
                classified = classify_gap_with_llm(client, row, outcome)

            # Generate remediation
            remediation = infer_remediation(outcome, row.get("failing_checks", []), classified["remediation"])

            # Create artifacts
            finding = create_gap_finding(row, outcome, classified)
            remedy = create_remedy_decision(row, remediation)

            all_nodes.extend([finding, remedy])
            all_edges.append({"from": finding["ref"], "to": remedy["ref"], "relation": "grounded_by"})

            # Track dimensions for predictions
            for dim in ACAT_DIMENSIONS:
                val = classified.get(dim, 0.5)
                gap_by_dimension[dim].append({"pr": row["pr"], "score": val})

            if args.verbose:
                print(f"Classified PR {row['pr']}: {outcome}", file=sys.stderr)

    # Generate predictions (T3.3)
    predictions = generate_predictions(gap_by_dimension, rows)
    pred_artifacts = create_prediction_artifacts(predictions)
    all_nodes.extend(pred_artifacts["nodes"])
    all_edges.extend(pred_artifacts["edges"])

    if args.verbose:
        print(f"Generated {len(pred_artifacts['nodes'])} prediction artifacts", file=sys.stderr)

    # Output
    if args.output == "empirica":
        output = {"nodes": all_nodes, "edges": all_edges}
    else:
        output = {
            "artifacts": {"nodes": all_nodes, "edges": all_edges},
            "predictions": predictions,
            "summary": {
                "total_gaps": len(rows),
                "predictions": len(pred_artifacts["nodes"]),
                "metrics": predictions["metrics"],
                "focus_areas": predictions["focus_areas"],
            }
        }

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
