#!/usr/bin/env python3
"""Program-level resource rollup for the HumanAIOS Program Graph layer.
Builder v1.7 compliant · governance_tool
HumanAIOS · PROGRAM_GRAPH_MAPPING.md (Layer 5 of the concept-to-code stack)

Reads Program nodes (the `kind: program` extension proposed for
INTENT_GRAPH.yaml) and RESOURCE_LEDGER.jsonl-shaped SPEND rows, and computes
a per-unit cost vector and benefit/cost density per Program — the same
formula PRIORITY_QUEUE.md already uses for individual work orders, applied
one level up.

This module does NOT do grounding or contradiction-checking — that is
tools/intent_graph_v1_0.py's job and stays there. It does not sum costs
across units: RESOURCE_UNITS.yaml ratifies P-NON-COMMENSURABLE (hash
b6b8233dd06400f565e5e21286cc0fec65a71472adfa1ebb98045f2dfaeff2a2, Night,
2026-09-13) and this tool treats that as binding, not advisory.

Usage:
  python3 program_graph.py --smoke-test
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

TOOL_NAME = "program_graph"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "PROGRAM_GRAPH_MAPPING.md"
TOOL_ZONE = 1

UNDEFINED_DENSITY = "undefined"  # explicit sentinel: zero cost incurred, not "infinitely good"


@dataclass
class Program:
    program_id: str
    name: str
    realizes: list[str] = field(default_factory=list)  # existing Objective id(s) in INTENT_GRAPH.yaml
    cost: dict[str, float] = field(default_factory=dict)  # per RESOURCE_UNITS.yaml symbol, e.g. "Z1-ktok"
    benefit: float = 0.0


def density(program: Program, unit: str) -> float | str:
    """benefit / cost[unit], for exactly one unit at a time. Never sums units."""
    cost = program.cost.get(unit, 0.0)
    if cost == 0:
        return UNDEFINED_DENSITY
    return program.benefit / cost


def rollup_spend(spend_rows: list[dict]) -> dict[str, dict[str, float]]:
    """Sum RESOURCE_LEDGER.jsonl-shaped SPEND rows by program_id, per unit, as a vector.

    Each row: {"program_id": str, "unit": str, "amount": float, ...}. Rows without a
    program_id are skipped here (they are the "untagged work" Part 3 of the mapping
    doc calls out as informative on its own, not an error in this function).
    """
    totals: dict[str, dict[str, float]] = {}
    for row in spend_rows:
        pid = row.get("program_id")
        if not pid:
            continue
        unit = row["unit"]
        amount = row["amount"]
        totals.setdefault(pid, {})
        totals[pid][unit] = totals[pid].get(unit, 0.0) + amount
    return totals


def smoke_test() -> int:
    custody = Program(
        program_id="PROGRAM-CUSTODY-PROVENANCE-01",
        name="Custody & Provenance Chain",
        realizes=["O-WITNESS"],
        cost={"Z1-ktok": 340.0},
        benefit=1.0,
    )
    stack = Program(
        program_id="PROGRAM-CONCEPT-TO-CODE-01",
        name="Concept-to-Code Stack",
        realizes=["O-INTENT-GRAPH"],
        cost={"Z1-ktok": 900.0},
        benefit=4.0,
    )
    attention = Program(
        program_id="PROGRAM-INTENT-OS-ATTENTION-01",
        name="INTENT-OS Attention Control Plane",
        realizes=[],  # the real gap PROGRAM_GRAPH_MAPPING.md Part 2 surfaces: no Objective yet
        cost={},
        benefit=0.0,
    )

    assert density(custody, "Z1-ktok") == 1.0 / 340.0
    assert density(stack, "Z1-ktok") == 4.0 / 900.0
    assert density(attention, "Z1-ktok") == UNDEFINED_DENSITY, "zero cost must be undefined, not 0 or inf"

    spend_rows = [
        {"program_id": "PROGRAM-CUSTODY-PROVENANCE-01", "unit": "Z1-ktok", "amount": 200.0},
        {"program_id": "PROGRAM-CUSTODY-PROVENANCE-01", "unit": "Z1-ktok", "amount": 140.0},
        {"program_id": "PROGRAM-CUSTODY-PROVENANCE-01", "unit": "Z3-hr", "amount": 2.0},
        {"program_id": None, "unit": "Z1-ktok", "amount": 50.0},  # untagged work — must not be attributed
    ]
    totals = rollup_spend(spend_rows)
    assert totals["PROGRAM-CUSTODY-PROVENANCE-01"]["Z1-ktok"] == 340.0
    assert totals["PROGRAM-CUSTODY-PROVENANCE-01"]["Z3-hr"] == 2.0
    assert "Z1-ktok" not in totals.get("None", {})
    assert len(totals) == 1, "untagged SPEND rows must never create a phantom program bucket"

    # P-NON-COMMENSURABLE: confirm this module never collapses units into one scalar anywhere.
    multi_unit = Program(program_id="X", name="x", cost={"Z1-ktok": 10.0, "Z3-hr": 1.0}, benefit=1.0)
    d1 = density(multi_unit, "Z1-ktok")
    d2 = density(multi_unit, "Z3-hr")
    assert d1 != d2, "two different units must produce two different, non-combined densities"

    print("smoke-test OK — density matches benefit/cost per unit, zero-cost is an explicit "
          "sentinel, untagged spend is never attributed, units are never summed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke-test", action="store_true", help="Run the self-test and exit.")
    args = ap.parse_args()

    if args.smoke_test:
        return smoke_test()

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
