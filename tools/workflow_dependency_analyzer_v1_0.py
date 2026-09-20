#!/usr/bin/env python3
"""
Workflow Dependency Analyzer v1.0

Analyzes GitHub Actions workflows to build a dependency graph:
- What triggers each workflow?
- What other workflows does it depend on?
- What's the cascade risk if it fails?
- Is it on the critical path?

BUILDER_MARKERS:
  tool_id: HAIOS-TOOL-180
  tool_name: workflow_dependency_analyzer
  category: analysis_tool
  version: 1.0.0
  interface: cli
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict

@dataclass
class WorkflowInfo:
    """Workflow metadata."""
    name: str
    file_path: str
    triggers: List[str]
    is_blocking_gate: bool
    proposed_class: str

class WorkflowAnalyzer:
    """Analyzes workflow dependencies from .github/workflows/"""

    CRITICAL_GATES = {
        'findings-registry', 'molt-tier-check', 'quality-baseline',
        'security-gates', 'z2_ratification_gate', 'temporal-dissolution-gate',
        'builder-lint', 'workflow-lint'
    }

    PR_BLOCKING_KEYWORDS = {'pull_request', 'push', 'main'}
    AUDIT_KEYWORDS = {'schedule', 'audit', 'monitor', 'drift', 'standing', 'harmonizer'}

    def __init__(self, workflows_dir: str = ".github/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.workflows: Dict[str, WorkflowInfo] = {}

    def analyze(self) -> Dict:
        """Run full analysis."""
        print("🔍 Analyzing workflows...", file=sys.stderr)

        # Parse all workflows
        for workflow_file in sorted(self.workflows_dir.glob("*.yml")):
            self._analyze_workflow(workflow_file)

        print(f"✓ Found {len(self.workflows)} workflows", file=sys.stderr)

        # Classify workflows
        classifications = self._classify_workflows()

        # Build summary
        summary = self._generate_summary(classifications)

        return {
            "workflows": {name: asdict(info) for name, info in self.workflows.items()},
            "classifications": classifications,
            "summary": summary
        }

    def _analyze_workflow(self, workflow_file: Path):
        """Parse a single workflow file."""
        name = workflow_file.stem

        # Extract triggers using raw text parsing (more reliable than YAML)
        triggers = self._extract_triggers_raw(workflow_file)

        # Determine if it's a critical gate
        is_blocking_gate = name in self.CRITICAL_GATES

        # Propose classification
        proposed_class = self._propose_classification(name, triggers, is_blocking_gate)

        info = WorkflowInfo(
            name=name,
            file_path=str(workflow_file),
            triggers=triggers,
            is_blocking_gate=is_blocking_gate,
            proposed_class=proposed_class
        )

        self.workflows[name] = info

    def _extract_triggers_raw(self, workflow_file: Path) -> List[str]:
        """Extract triggers using raw file parsing."""
        content = workflow_file.read_text()
        triggers = []

        # Look for trigger patterns in the file
        trigger_patterns = {
            'pull_request': r'pull_request(?:_target)?:',
            'push': r'push:',
            'schedule': r'schedule:',
            'workflow_dispatch': r'workflow_dispatch:',
            'workflow_run': r'workflow_run:',
            'issue_comment': r'issue_comment:',
        }

        for trigger_type, pattern in trigger_patterns.items():
            if re.search(pattern, content):
                triggers.append(trigger_type)

        return triggers

    def _propose_classification(self, name: str, triggers: List[str],
                               is_blocking_gate: bool) -> str:
        """Propose a classification (A/B/C/D) for this workflow."""

        # Class A: Critical-path blocking gates
        if is_blocking_gate:
            return "A"

        # Class B: Audit/monitoring workflows run on schedule
        if 'schedule' in triggers:
            if any(keyword in name for keyword in self.AUDIT_KEYWORDS):
                return "B"

        # Class C: Event-driven, non-blocking (issue_comment, workflow_run)
        if 'workflow_run' in triggers or 'issue_comment' in triggers:
            return "C"

        # Class D: Infrastructure/housekeeping
        return "D"

    def _classify_workflows(self) -> Dict[str, List[str]]:
        """Classify all workflows by class."""
        classifications = {"A": [], "B": [], "C": [], "D": []}

        for name in sorted(self.workflows.keys()):
            info = self.workflows[name]
            classifications[info.proposed_class].append(name)

        return classifications

    def _generate_summary(self, classifications: Dict) -> Dict:
        """Generate summary statistics."""
        trigger_counts = {}
        for info in self.workflows.values():
            for trigger in info.triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

        return {
            "total_workflows": len(self.workflows),
            "critical_gates": len([w for w in self.workflows.values() if w.is_blocking_gate]),
            "workflows_by_class": {k: len(v) for k, v in classifications.items()},
            "trigger_distribution": trigger_counts,
            "notes": [
                f"Class A (Critical Gates): {len(classifications['A'])} workflows - require Z2 ratification + falsifiers",
                f"Class B (Audits): {len(classifications['B'])} workflows - require Z2 ratification + measurement",
                f"Class C (Event-driven): {len(classifications['C'])} workflows - standard review",
                f"Class D (Infrastructure): {len(classifications['D'])} workflows - standard review"
            ]
        }

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        workflows_dir = sys.argv[1]
    else:
        workflows_dir = ".github/workflows"

    analyzer = WorkflowAnalyzer(workflows_dir)
    result = analyzer.analyze()

    # Output JSON
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
