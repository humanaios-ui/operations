#!/usr/bin/env python3
"""
Constitution Checker — P19: Detection beats compliance

Validates decisions/artifacts against the 22-principle constitution.
Used by: Principle Compliance Bot + governance audits.
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# TOOL_NAME and TOOL_VERSION for Builder v1.7 compliance
TOOL_NAME = "constitution_checker"
TOOL_VERSION = "1.0.0"


class ConstitutionChecker:
    """Check work against HumanAIOS constitution principles."""

    def __init__(self, constitution_path: str = "constitution.json"):
        """Load constitution from JSON."""
        self.path = Path(constitution_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Constitution not found: {constitution_path}")

        with open(self.path) as f:
            self.constitution = json.load(f)

        self.principles = {p["id"]: p for p in self.constitution["principles"]}

    def check_commit(self, commit_msg: str, files_changed: List[str]) -> List[str]:
        """
        Check a commit for principle violations.
        Returns list of violation strings (empty = clean).
        """
        violations = []
        msg_lower = commit_msg.lower()

        # P8: Attraction not promotion (T11)
        if re.search(r'\b(click here|sign up|buy now|limited time|exclusive)\b', msg_lower):
            violations.append("P8: Promotional language detected in commit — use attraction not promotion (T11)")

        # P5: Primary purpose filter
        if "refactor" in msg_lower and "test" not in msg_lower and "data" not in msg_lower:
            violations.append("P5: Refactor without stated purpose — does it generate data/test hypothesis/revenue?")

        # P-COMMIT-DISCIPLINE: Check commit granularity (oversized changes)
        if len(files_changed) > 10:
            violations.append(f"P-COMMIT-DISCIPLINE: Oversized commit ({len(files_changed)} files) — split into atomic per-task commits")

        # P-T10: TRL framing (no overclaims in commit message)
        if re.search(r'\b(is now|now live|production ready|fully implements)\b', msg_lower) and "dev" not in msg_lower:
            violations.append("P-T10: Overclaimed readiness — use TRL framing ('being developed as', not 'is')")

        return violations

    def check_decision_log(self, decision: Dict[str, Any]) -> List[str]:
        """Check a decision log entry for violations."""
        violations = []

        choice = decision.get("choice", "").lower()
        rationale = decision.get("rationale", "").lower()

        # P-TRANSPARENCY: Decision must have rationale + zone
        if not rationale:
            violations.append("P-TRANSPARENCY: Decision logged without rationale — must explain reasoning")

        zone = decision.get("zone", None)
        reversibility = decision.get("reversibility", "exploratory").lower()

        if reversibility == "committal" and not zone:
            violations.append("P-T2: Committal decision logged without Zone assignment — needs Z2/Z3 ratification")

        # P-HUMILITY: Check confidence overreach
        confidence = decision.get("confidence", 0)
        counter_evidence = decision.get("counter_evidence", "")
        if confidence > 0.95 and not counter_evidence:
            violations.append(f"P-HUMILITY: Overconfidence (conf={confidence}) without counter-evidence")

        return violations

    def check_finding_log(self, finding: Dict[str, Any]) -> List[str]:
        """Check a finding log entry for violations."""
        violations = []

        finding_text = finding.get("finding", "").lower()
        impact = finding.get("impact", 0)

        # P3: No unverified claims
        if re.search(r'\b(probably|likely|might|could be)\b', finding_text):
            violations.append("P3: Unverified language in finding — use grounded observations only")

        # P-ARTIFACT-BREADTH: Check if finding is mislabeled
        if "unknown" in finding_text or "don't know" in finding_text:
            violations.append("P-ARTIFACT-BREADTH: Finding phrased as unknown — log as unknown-log instead")

        return violations

    def check_artifact_graph(self, artifacts: List[Dict[str, Any]]) -> List[str]:
        """Check artifact connectivity and breadth."""
        violations = []

        types_logged = set(a.get("type") for a in artifacts)
        orphan_count = sum(1 for a in artifacts if not a.get("edges") or len(a.get("edges", [])) == 0)

        # P-ARTIFACT-BREADTH: Check type diversity
        expected_types = {"finding", "unknown", "assumption", "decision", "dead_end", "mistake"}
        if len(types_logged) == 1:
            violations.append("P-ARTIFACT-BREADTH: Only one artifact type logged — log the full spectrum (findings, unknowns, assumptions, decisions, dead-ends, mistakes)")

        # P-GRAPH: Check orphan ratio
        if len(artifacts) > 0:
            orphan_ratio = orphan_count / len(artifacts)
            if orphan_ratio > 0.5:
                violations.append(f"P-GRAPH: {orphan_ratio*100:.0f}% of artifacts are orphans (no edges) — connect to prior work")

        return violations

    def check_principle(self, plan_step: Dict[str, Any]) -> List[str]:
        """
        Generic principle check on a plan step (used by haios_agent_orchestrator).
        Returns violations list (empty = pass).
        """
        violations = []
        step_text = json.dumps(plan_step).lower()

        # P3: verification — no unverified raw data claims
        if "unverified" in step_text:
            violations.append(f"P3: Unverified claim detected in plan step")

        # P19: detection beats compliance — must have a detector, not just a rule
        if "compliance" in step_text and "detect" not in step_text:
            violations.append(f"P19: Compliance-only approach; add detector")

        # P-HUMILITY: flag if confidence > 0.95 without counter-evidence
        confidence = plan_step.get("confidence", 0)
        if confidence > 0.95 and not plan_step.get("counter_evidence"):
            violations.append(f"P-HUMILITY: Overconfidence flag (conf={confidence}); add counter-evidence")

        return violations

    def summary(self) -> str:
        """Return human-readable principle summary."""
        lines = ["HumanAIOS Constitution Summary", "=" * 50]
        for framework in ["12 Steps", "12 Traditions", "Governance (Detection)", "Hawkins / Calibration", "Epistemic", "Collaboration", "Praxic"]:
            plist = [p for p in self.principles.values() if p.get("framework") == framework]
            if plist:
                lines.append(f"\n{framework}:")
                for p in plist:
                    lines.append(f"  {p['id']}: {p['name']}")
        return "\n".join(lines)


def run_smoke_test() -> bool:
    """Smoke test for Builder v1.7 compliance."""
    try:
        checker = ConstitutionChecker("constitution.json")
        violations = checker.check_commit("refactor: cleanup", ["file1.py"])
        print(f"✓ ConstitutionChecker loaded ({len(checker.principles)} principles)")
        return True
    except Exception as e:
        print(f"✗ Smoke test failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        run_smoke_test()
    else:
        checker = ConstitutionChecker("constitution.json")
        print(checker.summary())
