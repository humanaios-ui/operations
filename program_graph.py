#!/usr/bin/env python3
"""Program-level resource rollup for the HumanAIOS Program Graph layer.
Builder v1.7 compliant · governance_tool
HumanAIOS · PROGRAM_GRAPH_MAPPING.md (Layer 5 of the concept-to-code stack)

Reads Program nodes (the `type: program` extension proposed for
INTENT_GRAPH.yaml) and RESOURCE_LEDGER.jsonl SPEND rows (joined through a
separate, append-only order-to-program mapping — see below), and computes a
per-unit cost vector and benefit/cost density per Program, using
PRIORITY_QUEUE.md's own Band A / Band B logic one level up from individual
work orders.

This module does NOT do grounding or contradiction-checking — that is
tools/intent_graph_v1_0.py's job and stays there. It does not sum costs
across units: RESOURCE_UNITS.yaml ratifies P-NON-COMMENSURABLE (hash
b6b8233dd06400f565e5e21286cc0fec65a71472adfa1ebb98045f2dfaeff2a2, Night,
2026-09-13) and this tool treats that as binding, not advisory.

It also never mutates RESOURCE_LEDGER.jsonl: that ledger is append-only and
hash-chained (docs/RESOURCE_UNITS.md: "any edited prior line" breaks
`verify`), and the real SPEND event shape (tools/resource_ledger_v0_1.py)
carries no program tag at all — just {type, at, by, order_id, unit, qty,
source, obligation_class}. Program attribution is a read-only join against
a separate order_id -> program_id mapping file, never a ledger edit.

Usage:
  python3 program_graph.py --smoke-test
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

TOOL_NAME = "program_graph"
TOOL_VERSION = "0.2.0"
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "PROGRAM_GRAPH_MAPPING.md"
TOOL_ZONE = 1

BAND_A = "BAND_A"  # explicit zero cost: rank by raw benefit, no ratio computed
BAND_B = "BAND_B"  # positive cost: rank by benefit / cost
UNMEASURED = "UNMEASURED"  # no SPEND rows at all for this program+unit — an instrumentation gap


@dataclass
class Program:
    program_id: str
    name: str
    realizes: list[str] = field(default_factory=list)  # existing Objective id(s) in INTENT_GRAPH.yaml
    cost: dict[str, float] = field(default_factory=dict)  # per RESOURCE_UNITS.yaml symbol, e.g. "Z1-ktok"
    benefit: float = 0.0


@dataclass
class DensityResult:
    band: str  # BAND_A | BAND_B | UNMEASURED
    value: float | None  # benefit (Band A), benefit/cost (Band B), or None (UNMEASURED)


def density(program: Program, unit: str) -> DensityResult:
    """Mirrors priority_queue_engine.py's own rule exactly: 'a missing key is
    nobody costed this, which is not the same claim as this costs nothing.'
    A missing unit -> UNMEASURED. An explicit zero -> Band A, rank by benefit.
    A positive cost -> Band B, rank by benefit/cost. Never sums across units.
    """
    if unit not in program.cost:
        return DensityResult(UNMEASURED, None)
    cost = program.cost[unit]
    if cost == 0:
        return DensityResult(BAND_A, program.benefit)
    return DensityResult(BAND_B, program.benefit / cost)


def rollup_spend(spend_rows: list[dict], order_to_program: dict[str, str]) -> dict[str, dict[str, float]]:
    """Sum RESOURCE_LEDGER.jsonl SPEND rows by program, per unit, as a vector.

    spend_rows: real SPEND event shape — {"order_id": str, "unit": str, "qty": float, ...}.
    order_to_program: a separate, append-only order_id -> program_id mapping (never a
    field on the SPEND row itself, and never written back into RESOURCE_LEDGER.jsonl).
    Orders with no mapping entry are skipped here — the "untagged work" Part 3 of the
    mapping doc calls out as informative on its own, not an error in this function.
    """
    totals: dict[str, dict[str, float]] = {}
    for row in spend_rows:
        pid = order_to_program.get(row["order_id"])
        if not pid:
            continue
        unit = row["unit"]
        qty = row["qty"]
        totals.setdefault(pid, {})
        totals[pid][unit] = totals[pid].get(unit, 0.0) + qty
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
        cost={},  # zero SPEND rows exist for this program at all — not the same as spending zero
        benefit=0.0,
    )
    zero_cost = Program(
        program_id="PROGRAM-BAND-A-EXAMPLE",
        name="A program that drew nothing on this constraint, on purpose",
        cost={"Z1-ktok": 0.0},  # an explicit, recorded zero — distinct from "no row at all"
        benefit=2.0,
    )

    r_custody = density(custody, "Z1-ktok")
    assert r_custody.band == BAND_B and r_custody.value == 1.0 / 340.0

    r_stack = density(stack, "Z1-ktok")
    assert r_stack.band == BAND_B and r_stack.value == 4.0 / 900.0

    r_attention = density(attention, "Z1-ktok")
    assert r_attention.band == UNMEASURED and r_attention.value is None, (
        "no SPEND rows at all must read UNMEASURED, never 0 or an undefined-division sentinel"
    )

    r_zero = density(zero_cost, "Z1-ktok")
    assert r_zero.band == BAND_A and r_zero.value == 2.0, (
        "an explicit recorded zero must be Band A (rank by benefit), distinct from UNMEASURED"
    )

    # Real SPEND event shape: order_id + qty, no program tag on the row itself.
    spend_rows = [
        {"order_id": "ORD-001", "unit": "Z1-ktok", "qty": 200.0},
        {"order_id": "ORD-002", "unit": "Z1-ktok", "qty": 140.0},
        {"order_id": "ORD-001", "unit": "Z3-hr", "qty": 2.0},
        {"order_id": "ORD-999", "unit": "Z1-ktok", "qty": 50.0},  # no mapping entry — untagged
    ]
    order_to_program = {
        "ORD-001": "PROGRAM-CUSTODY-PROVENANCE-01",
        "ORD-002": "PROGRAM-CUSTODY-PROVENANCE-01",
        # ORD-999 deliberately absent — never attributed, never a phantom bucket
    }
    totals = rollup_spend(spend_rows, order_to_program)
    assert totals["PROGRAM-CUSTODY-PROVENANCE-01"]["Z1-ktok"] == 340.0
    assert totals["PROGRAM-CUSTODY-PROVENANCE-01"]["Z3-hr"] == 2.0
    assert len(totals) == 1, "an order with no mapping entry must never create a phantom program bucket"

    # P-NON-COMMENSURABLE: confirm this module never collapses units into one scalar anywhere.
    multi_unit = Program(program_id="X", name="x", cost={"Z1-ktok": 10.0, "Z3-hr": 1.0}, benefit=1.0)
    d1 = density(multi_unit, "Z1-ktok")
    d2 = density(multi_unit, "Z3-hr")
    assert d1.value != d2.value, "two different units must produce two different, non-combined densities"

    print("smoke-test OK — Band A / Band B / UNMEASURED match priority_queue_engine.py's own "
          "missing-vs-zero rule, SPEND attribution never touches the ledger, untagged orders "
          "are never attributed, units are never summed.")
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
