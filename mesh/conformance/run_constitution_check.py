#!/usr/bin/env python3
"""Run constitution.json against this drop via tools/agents/_shared/constitution_checker.py.

This is the B.0 Empirical Verification step for Q-MESH-LOCAL-COORDINATION-01: the
constitution is executed against the actual work, and whatever it returns is
reported. Violations are printed, not tuned away.

Usage:
    python3 mesh/conformance/run_constitution_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

TOOL_NAME = "run_constitution_check"
TOOL_VERSION = "0.1.0"

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "agents" / "_shared"))

from constitution_checker import ConstitutionChecker  # noqa: E402


def practice_records() -> list[dict]:
    root = REPO / "mesh" / "practices"
    return [yaml.safe_load(p.read_text()) for p in sorted(root.glob("*/practice.yaml"))]


# The decision this drop records, stated as it actually is.
DECISION = {
    "choice": "Add mesh/ as a local, unratified coordination layer for humanaios, website, grok-crossref",
    "rationale": (
        "Two of the three practices are AMBIGUOUS in ledgers/PRACTICE_RESOLUTION_MAP.md and "
        "cannot be resolved while Z2 decision D1 is open. A local record describes each practice "
        "without selecting a resolution target, so coordination proceeds and the calibration "
        "series stays uncorrupted."
    ),
    "zone": "Z-000",
    "reversibility": "exploratory",
    "confidence": 0.7,
    "counter_evidence": (
        "A local record adds a third candidate target, which widens D1 rather than narrowing it. "
        "Z2 may rule that local mesh work belongs in empirica-practice-mesh instead."
    ),
}

# The finding this drop produces, stated without hedging.
FINDING = {
    "finding": (
        "The local mesh layer adds a third candidate resolution target for two AMBIGUOUS "
        "practices. Z2 decision D1 governs which target the resolver reads. No NF_LEDGER.jsonl "
        "row is written by this drop."
    ),
    "impact": 5,
}

COMMITS = [
    ("docs(mesh): local mesh coordination charter and record schema",
     ["mesh/README.md", "mesh/MESH_LOCAL_CHARTER_V0_1.md", "mesh/practice_local.schema.json"]),
    ("docs(mesh): practice records for humanaios, website, grok-crossref",
     ["mesh/practices/humanaios/practice.yaml", "mesh/practices/humanaios/README.md",
      "mesh/practices/website/practice.yaml", "mesh/practices/website/README.md",
      "mesh/practices/grok-crossref/practice.yaml", "mesh/practices/grok-crossref/README.md"]),
    ("docs(mesh): cross-reference register and conformance evidence",
     ["mesh/CROSS_REFERENCE_REGISTER.md", "mesh/conformance/validate_mesh.py",
      "mesh/conformance/run_constitution_check.py", "mesh/conformance/CONFORMANCE_RUN.md",
      "z1-inbox/2026-09-22/Q-MESH-LOCAL-COORDINATION-01.md", "z1-inbox/INDEX.yaml"]),
]


def artifact_graph() -> list[dict]:
    """Artifacts this drop logs, typed per P-ARTIFACT-BREADTH."""
    artifacts: list[dict] = []
    for rec in practice_records():
        artifacts.append({
            "type": "decision",
            "id": f"practice:{rec['practice_id']}",
            "edges": [e["ref"] for e in rec.get("edges", [])],
        })
        for unknown in rec.get("unknowns", []):
            artifacts.append({
                "type": "unknown",
                "id": unknown[:60],
                "edges": [f"practice:{rec['practice_id']}"],
            })
    artifacts.append({
        "type": "assumption",
        "id": "local records are observation records, not resolution targets",
        "edges": ["mesh/MESH_LOCAL_CHARTER_V0_1.md", "ledgers/PRACTICE_RESOLUTION_MAP.md"],
    })
    artifacts.append({
        "type": "dead_end",
        "id": "reading /empirica-constitution plugin text — path not reachable from this session",
        "edges": ["SKILLS_MANIFEST.md", "mesh/MESH_LOCAL_CHARTER_V0_1.md"],
    })
    artifacts.append({
        "type": "finding",
        "id": "D1 widened from two candidate targets to three",
        "edges": ["ledgers/PRACTICE_RESOLUTION_MAP.md"],
    })
    return artifacts


def main() -> int:
    checker = ConstitutionChecker(str(REPO / "constitution.json"))
    total = 0

    print(f"{TOOL_NAME} v{TOOL_VERSION}")
    print(f"constitution: {checker.constitution['title']} (v{checker.constitution['version']}, "
          f"{len(checker.principles)} principles)\n")

    print("== check_commit ==")
    for msg, files in COMMITS:
        violations = checker.check_commit(msg, files)
        total += len(violations)
        print(f"  [{len(files)} files] {msg}")
        for v in violations:
            print(f"      VIOLATION: {v}")
        if not violations:
            print("      clean")

    print("\n== check_decision_log ==")
    violations = checker.check_decision_log(DECISION)
    total += len(violations)
    for v in violations:
        print(f"  VIOLATION: {v}")
    if not violations:
        print("  clean")

    print("\n== check_finding_log ==")
    violations = checker.check_finding_log(FINDING)
    total += len(violations)
    for v in violations:
        print(f"  VIOLATION: {v}")
    if not violations:
        print("  clean")

    print("\n== check_artifact_graph ==")
    artifacts = artifact_graph()
    types = sorted({a["type"] for a in artifacts})
    print(f"  {len(artifacts)} artifacts, types: {', '.join(types)}")
    violations = checker.check_artifact_graph(artifacts)
    total += len(violations)
    for v in violations:
        print(f"  VIOLATION: {v}")
    if not violations:
        print("  clean")

    print(f"\nRESULT: {total} violation(s)")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
