"""
node_status_report.py — System Graph Node Status Documentation

Reports implementation status (OPERATED vs LAID) for each node in system_graph.json.

OPERATED: Fully implemented, tested, and integrated in Phase 2 (M1-M15).
LAID: Code written in Phase 3 Option 4 deployment; ready for integration; awaiting Z2 ratification.
PLANNED: Spec only, no implementation yet.

This document serves as the ground truth for deployment readiness and testing coverage.
Updated after each phase completion.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class NodeStatusEntry:
    """Status of a single node."""
    node_id: str
    name: str
    type: str
    status: str                # OPERATED, LAID, PLANNED
    implementation: str
    tests: int
    phase: str
    description: str
    readiness: Dict[str, bool]  # code_written, tested, integrated, documented


class NodeStatusReport:
    """Generates node status documentation."""

    def __init__(self, graph_json_path: str):
        """Load system graph and initialize report."""
        with open(graph_json_path, 'r') as f:
            self.graph = json.load(f)

        self.nodes = self.graph.get('nodes', {})

    def generate_status_matrix(self) -> Dict[str, Any]:
        """Generate status matrix (status distribution)."""
        matrix = {
            'OPERATED': [],
            'LAID': [],
            'PLANNED': [],
        }

        for node_id, node in self.nodes.items():
            status = node['status']
            matrix[status].append({
                'id': node_id,
                'name': node['name'],
                'type': node['type'],
                'tests': node['tests'],
            })

        return {
            'operated_count': len(matrix['OPERATED']),
            'laid_count': len(matrix['LAID']),
            'planned_count': len(matrix['PLANNED']),
            'total_nodes': len(self.nodes),
            'by_status': matrix,
        }

    def generate_type_breakdown(self) -> Dict[str, Any]:
        """Breakdown by node type."""
        breakdown = {}

        for node_id, node in self.nodes.items():
            node_type = node['type']
            if node_type not in breakdown:
                breakdown[node_type] = {
                    'OPERATED': [],
                    'LAID': [],
                    'PLANNED': [],
                }

            breakdown[node_type][node['status']].append(node_id)

        return breakdown

    def generate_zone_breakdown(self) -> Dict[str, Any]:
        """Breakdown by zone (Z1, Z2, Z3, CI, code)."""
        breakdown = {}

        for node_id, node in self.nodes.items():
            zone = node['zone']
            if zone not in breakdown:
                breakdown[zone] = {
                    'OPERATED': [],
                    'LAID': [],
                    'PLANNED': [],
                }

            breakdown[zone][node['status']].append(node_id)

        return breakdown

    def generate_markdown_report(self) -> str:
        """Generate comprehensive markdown report."""
        report = []
        report.append("# System Graph Node Status Report\n")
        report.append(f"**Generated:** {datetime.now().isoformat()}\n")
        report.append(f"**Graph Version:** {self.graph.get('version', 'unknown')}\n\n")

        # Summary statistics
        matrix = self.generate_status_matrix()
        report.append("## Summary\n")
        report.append(f"- **OPERATED nodes:** {matrix['operated_count']} (fully implemented, tested, integrated)")
        report.append(f"- **LAID nodes:** {matrix['laid_count']} (code written, ready for integration)")
        report.append(f"- **PLANNED nodes:** {matrix['planned_count']} (spec only)")
        report.append(f"- **Total nodes:** {matrix['total_nodes']}\n\n")

        # Operated nodes
        report.append("## OPERATED Nodes (Phase 2 Complete)\n\n")
        report.append("Fully implemented, tested, and integrated in Phase 2 (M1-M15).\n\n")

        for node in sorted(matrix['by_status']['OPERATED'], key=lambda x: x['name']):
            node_full = self.nodes[node['id']]
            report.append(f"### {node['id']} — {node['name']}\n")
            report.append(f"- **Type:** {node['type']}\n")
            report.append(f"- **Description:** {node_full['description']}\n")
            report.append(f"- **Implementation:** {node_full['implementation']}\n")
            report.append(f"- **Tests:** {node['tests']}\n")
            report.append(f"- **Phase:** {node_full['phase']}\n\n")

        # LAID nodes
        report.append("## LAID Nodes (Phase 3 Option 4 Deployment)\n\n")
        report.append("Code written in Phase 3; ready for integration once Z2 ratifies and CI gates pass.\n\n")

        for node in sorted(matrix['by_status']['LAID'], key=lambda x: x['name']):
            node_full = self.nodes[node['id']]
            report.append(f"### {node['id']} — {node['name']}\n")
            report.append(f"- **Type:** {node['type']}\n")
            report.append(f"- **Description:** {node_full['description']}\n")
            report.append(f"- **Implementation:** {node_full['implementation']}\n")
            report.append(f"- **Status:** Code written, awaiting integration tests\n")
            report.append(f"- **Phase:** {node_full['phase']}\n\n")

        # Type breakdown
        report.append("## Breakdown by Node Type\n\n")
        type_breakdown = self.generate_type_breakdown()
        for node_type in sorted(type_breakdown.keys()):
            counts = type_breakdown[node_type]
            report.append(f"**{node_type.title()}:** ")
            report.append(f"{len(counts['OPERATED'])} OPERATED, ")
            report.append(f"{len(counts['LAID'])} LAID, ")
            report.append(f"{len(counts['PLANNED'])} PLANNED\n")

        report.append("\n")

        # Zone breakdown
        report.append("## Breakdown by Zone\n\n")
        zone_breakdown = self.generate_zone_breakdown()
        for zone in sorted(zone_breakdown.keys()):
            counts = zone_breakdown[zone]
            report.append(f"**{zone}:** ")
            report.append(f"{len(counts['OPERATED'])} OPERATED, ")
            report.append(f"{len(counts['LAID'])} LAID, ")
            report.append(f"{len(counts['PLANNED'])} PLANNED\n")

        report.append("\n")

        # Integration readiness
        report.append("## Integration Readiness\n\n")
        report.append("### Ready for Production (OPERATED)\n\n")
        report.append("These nodes have been tested and integrated in Phase 2:\n\n")

        operated = [n for n in matrix['by_status']['OPERATED']]
        for node in operated:
            report.append(f"- {node['id']}: {node['name']} ({node['tests']} tests)\n")

        report.append("\n### Pending Z2 Ratification (LAID)\n\n")
        report.append("These nodes have code written but require Z2 ratification and CI gate pass:\n\n")

        laid = [n for n in matrix['by_status']['LAID']]
        for node in laid:
            node_full = self.nodes[node['id']]
            report.append(f"- {node['id']}: {node['name']}\n")
            report.append(f"  - File: {node_full['implementation']}\n")
            report.append(f"  - Awaiting: Z2 ratification + CI integration tests\n\n")

        # Test coverage
        report.append("## Test Coverage\n\n")
        total_tests = sum(node.get('tests', 0) for node in self.nodes.values())
        operated_tests = sum(n['tests'] for n in matrix['by_status']['OPERATED'])
        report.append(f"- **Total Phase 2 tests:** {operated_tests}\n")
        report.append(f"- **Coverage:** {len(matrix['by_status']['OPERATED'])} nodes tested\n\n")

        return "\n".join(report)

    def write_report(self, filepath: str) -> Dict[str, Any]:
        """Write report to markdown file."""
        markdown = self.generate_markdown_report()

        with open(filepath, 'w') as f:
            f.write(markdown)

        return {
            'filepath': filepath,
            'status': 'WRITTEN',
            'nodes_documented': len(self.nodes),
        }

    def report_deployment_readiness(self) -> Dict[str, Any]:
        """Report readiness for Phase 3 deployment."""
        matrix = self.generate_status_matrix()

        return {
            'phase_2_complete': matrix['operated_count'] > 0,
            'operated_nodes': matrix['operated_count'],
            'laid_nodes': matrix['laid_count'],
            'ready_for_deployment': {
                'code_written': matrix['laid_count'] > 0,
                'awaiting_z2_ratification': matrix['laid_count'] > 0,
                'awaiting_ci_integration': matrix['laid_count'] > 0,
            },
            'by_type': self.generate_type_breakdown(),
            'by_zone': self.generate_zone_breakdown(),
        }
