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
import subprocess
import sys
from pathlib import Path

TOOL_NAME = "run_constitution_check"
TOOL_VERSION = "0.1.0"

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "agents" / "_shared"))
sys.path.insert(0, str(REPO / ".doc-control"))

from constitution_checker import ConstitutionChecker  # noqa: E402
from strict_yaml import loads as strict_loads  # noqa: E402  - refuses duplicate keys


def practice_records() -> list[dict]:
    root = REPO / "mesh" / "practices"
    return [strict_loads(p.read_text()) for p in sorted(root.glob("*/practice.yaml"))]


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def branch_commits(base_ref: str = "origin/main") -> list[tuple[str, str, list[str]]]:
    """The branch's ACTUAL commits, as (sha, subject, files).

    An earlier version of this module carried a handwritten list of commit
    messages and file arrays. P-COMMIT-DISCIPLINE would then have returned clean
    against a fixture while the real history was oversized or carried files the
    fixture omitted — the check would be true of nothing. It reads git now.

    First-parent only, so a merge is one entry rather than the base branch's
    whole history. A clean merge's own diff is empty, which is the honest file
    count for a commit that resolved nothing.
    """
    base = git("merge-base", base_ref, "HEAD")
    shas = git("log", "--first-parent", "--format=%H", f"{base}..HEAD").split()
    out = []
    for sha in reversed(shas):
        subject = git("log", "-1", "--format=%s", sha)
        files = [f for f in git("show", "--pretty=", "--name-only", sha).split("\n") if f]
        out.append((sha, subject, files))
    return out


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
    try:
        commits = branch_commits()
    except subprocess.CalledProcessError as exc:
        print(f"  UNAVAILABLE: git could not resolve the branch history ({exc})")
        print("  This check is reported as not run rather than passed.")
        commits = None

    if commits is None:
        total += 1
    elif not commits:
        print("  no commits ahead of origin/main — nothing to check")
    else:
        print(f"  {len(commits)} commit(s) ahead of origin/main (first-parent)")
        for sha, subject, files in commits:
            violations = checker.check_commit(subject, files)
            total += len(violations)
            note = " (merge; own diff empty)" if not files else ""
            print(f"  [{len(files)} files]{note} {sha[:7]} {subject}")
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
