"""
system_graph_generator.py — System Graph Canonicalization

Generates canonical system_graph.json from edge list definition.
Every node is a process that runs, not a document that describes.

Pattern:
1. PARSE: Read edge definitions from source (markdown, Python, YAML)
2. BUILD: Create graph structure with nodes and edges
3. VALIDATE: Check for dangling nodes, cycles, orphaned edges
4. EMIT: Write system_graph.json (machine form, authoritative)

Zones:
- Z1: Proposes/builds (Claude)
- Z2: Rules/ratifies (Night)
- Z3: Lands to live repo
- CI: Enforces in code
- code: Mechanical, no discretion

Node types:
- Process: Runs code/workflow
- Ledger: Append-only storage
- Gate: Enforcement mechanism
- Ritual: Session procedure

Status:
- OPERATED: Fully implemented and tested in Phase 2
- LAID: Code written but not integrated into live system
- PLANNED: Spec only, no implementation
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime
from enum import Enum


class NodeType(Enum):
    """Types of nodes in system graph."""
    PROCESS = "process"
    LEDGER = "ledger"
    GATE = "gate"
    RITUAL = "ritual"


class NodeStatus(Enum):
    """Implementation status of node."""
    OPERATED = "OPERATED"      # Fully implemented and tested
    LAID = "LAID"              # Code written but not integrated
    PLANNED = "PLANNED"        # Spec only


class EdgeType(Enum):
    """Types of edges in system graph."""
    DATA_FLOW = "data_flow"    # Reads/writes data
    CONTROL_FLOW = "control_flow"  # Triggers/gates execution
    CAUSALITY = "causality"    # One process depends on output of another
    CALLOUT = "callout"        # Emergency signal


@dataclass
class Node:
    """Node in system graph."""
    id: str
    name: str
    type: str                  # Process, Ledger, Gate, Ritual
    status: str                # OPERATED, LAID, PLANNED
    zone: str                  # Z1, Z2, Z3, CI, code
    description: str
    implementation: Optional[str] = None  # Python file, yml, etc.
    tests: int = 0
    phase: str = ""            # M1-M15 phase


@dataclass
class Edge:
    """Edge in system graph (connection between nodes)."""
    source: str
    target: str
    edge_type: str             # data_flow, control_flow, causality, callout
    label: str
    description: str = ""


@dataclass
class SystemGraph:
    """Complete system graph."""
    version: str
    generated_at: str
    nodes: Dict[str, Dict[str, Any]]  # id → node_data
    edges: List[Dict[str, Any]]
    validation_status: Dict[str, Any]
    zone_distribution: Dict[str, int]


class SystemGraphGenerator:
    """System Graph Generator — builds canonical system_graph.json."""

    def __init__(self):
        self.nodes = {}                 # id → Node
        self.edges = []                 # List of Edge
        self.validation_errors = []

    def add_node(self, node: Node) -> Dict[str, Any]:
        """Add node to graph."""
        self.nodes[node.id] = node

        return {
            'node_id': node.id,
            'name': node.name,
            'type': node.type,
            'status': node.status,
        }

    def add_edge(self, edge: Edge) -> Dict[str, Any]:
        """Add edge to graph."""
        self.edges.append(edge)

        return {
            'source': edge.source,
            'target': edge.target,
            'type': edge.edge_type,
            'label': edge.label,
        }

    def validate_graph(self) -> Dict[str, Any]:
        """
        Validate graph for structural issues:
        - Dangling nodes (edges to non-existent nodes)
        - Orphaned nodes (no incoming or outgoing edges)
        - Cycles (for DAG-like workflows)
        """
        errors = []
        warnings = []
        node_ids = set(self.nodes.keys())

        # Check for dangling edges
        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f'Dangling edge: {edge.source} → {edge.target} (source not found)')
            if edge.target not in node_ids:
                errors.append(f'Dangling edge: {edge.source} → {edge.target} (target not found)')

        # Check for orphaned nodes (no edges)
        edges_set = set()
        for edge in self.edges:
            edges_set.add(edge.source)
            edges_set.add(edge.target)

        orphaned = node_ids - edges_set
        if orphaned:
            warnings.append(f'Orphaned nodes (no edges): {orphaned}')

        # Check for cycles in critical paths
        # (simplified: just check if we can do topological sort)
        try:
            self._topological_sort()
        except ValueError as e:
            errors.append(f'Cycle detected: {str(e)}')

        self.validation_errors = errors

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }

    def _topological_sort(self) -> List[str]:
        """Topological sort to detect cycles."""
        # Build adjacency list
        graph = {node_id: [] for node_id in self.nodes.keys()}
        in_degree = {node_id: 0 for node_id in self.nodes.keys()}

        for edge in self.edges:
            if edge.source in graph and edge.target in graph:
                graph[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        # Kahn's algorithm
        queue = [node_id for node_id in self.nodes.keys() if in_degree[node_id] == 0]
        sorted_nodes = []

        while queue:
            node = queue.pop(0)
            sorted_nodes.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError('Cycle detected in graph')

        return sorted_nodes

    def generate_schema(self) -> SystemGraph:
        """Generate canonical system graph schema."""
        # Validate before generating
        validation = self.validate_graph()

        # Calculate zone distribution
        zone_dist = {}
        for node in self.nodes.values():
            zone_dist[node.zone] = zone_dist.get(node.zone, 0) + 1

        # Convert nodes to dict
        nodes_dict = {}
        for node_id, node in self.nodes.items():
            nodes_dict[node_id] = asdict(node)

        # Convert edges to list of dicts
        edges_list = []
        for edge in self.edges:
            edges_list.append(asdict(edge))

        return SystemGraph(
            version="0.2",
            generated_at=datetime.now().isoformat(),
            nodes=nodes_dict,
            edges=edges_list,
            validation_status={
                'valid': validation['valid'],
                'errors': validation['errors'],
                'warnings': validation['warnings'],
            },
            zone_distribution=zone_dist,
        )

    def to_json(self) -> str:
        """Serialize graph to JSON."""
        schema = self.generate_schema()

        return json.dumps(asdict(schema), indent=2)

    def to_file(self, filepath: str) -> Dict[str, Any]:
        """Write graph to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

        return {
            'filepath': filepath,
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'status': 'WRITTEN',
        }

    def build_phase2_graph(self) -> Dict[str, Any]:
        """
        Build complete system graph from Phase 2 implementation.
        Includes all OPERATED nodes (M1-M15).
        """

        # INTAKE SUBGRAPH
        self.add_node(Node(
            id='Q',
            name='Priority Queue',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='Z2',
            description='Work order queue with scoring: score = impact + Σ impact(unblocks); READY gate controls start',
            implementation='priority_queue_engine.py',
            tests=15,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='FS',
            name='Findings Scan',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='Z1',
            description='Extract F/IC/H candidates from events, molt ledger, transcripts; emit candidate blocks',
            implementation='findings_scan.py (skill)',
            tests=12,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='OM',
            name='Operator Model',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='Z1',
            description='Z1 read of Z2 rules, contestable; D10 predictions on Z2 decisions',
            implementation='operator_model_v0_2.py',
            tests=10,
            phase='M1-M15',
        ))

        # RUN SUBGRAPH
        self.add_node(Node(
            id='PRS',
            name='PRS Runner',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Locked preregistered experiment execution; no parameter overrides',
            implementation='prs_run.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        self.add_node(Node(
            id='AG',
            name='Agent Runtime',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Task execution with capacity enforcement; investor/business caps',
            implementation='agent_core.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        self.add_node(Node(
            id='ADV',
            name='Adversarial Eval',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Gate robustness testing; attack execution and catch-rate tracking',
            implementation='adv_eval_v1.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        self.add_node(Node(
            id='TC',
            name='Behavior Dials',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Z1 reply tuning against behavior_spec.json dials; DRIFT detection',
            implementation='tune_check.py',
            tests=8,
            phase='M1-M15',
        ))

        # LEDGER SUBGRAPH
        self.add_node(Node(
            id='EV',
            name='Event Chains',
            type=NodeType.LEDGER.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Append-only hash-chained event logs (*.jsonl)',
            implementation='event logs',
            tests=20,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='NF',
            name='Calibration Ledger',
            type=NodeType.LEDGER.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Brier scores, calibration metrics per predictor/constant',
            implementation='NF_LEDGER.jsonl',
            tests=12,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='REG',
            name='REGISTERED.md',
            type=NodeType.LEDGER.value,
            status=NodeStatus.OPERATED.value,
            zone='Z2',
            description='Public record of all ratified decisions, hypotheses, measurements',
            implementation='REGISTERED.md',
            tests=15,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='CONST',
            name='Constants',
            type=NodeType.LEDGER.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='behavior_spec.json, integrity_modes.json, rubrics, weights; each carries molt_id',
            implementation='constants/*.json',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        # MOLT SUBGRAPH
        self.add_node(Node(
            id='MOLT',
            name='Molt Cycle',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='READ → PROPOSE → PREDICT → RATIFY → APPLY → MEASURE → KEEP/REVERT',
            implementation='molt_cycle.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        self.add_node(Node(
            id='ML',
            name='Molt Ledger',
            type=NodeType.LEDGER.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='molt_events.jsonl: chain of molt decisions and outcomes',
            implementation='molt_events.jsonl',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        # GATE SUBGRAPH
        self.add_node(Node(
            id='Z2',
            name='Z2 Ratification Gate',
            type=NodeType.GATE.value,
            status=NodeStatus.OPERATED.value,
            zone='Z2',
            description='Hash-based ratification; no prose decisions',
            implementation='CLAUDE.md authority spec',
            tests=20,
            phase='M1-M15',
        ))

        self.add_node(Node(
            id='CIG',
            name='CI Integration Gate',
            type=NodeType.GATE.value,
            status=NodeStatus.OPERATED.value,
            zone='CI',
            description='5-gate sequence: falsifier_lint, z2_hash_verify, anti_cascade, merkle_root, full_ci',
            implementation='ci_gates.py, z2_ratification_gate.yml',
            tests=141,
            phase='M11-M15',
        ))

        self.add_node(Node(
            id='MK',
            name='Merkle Root',
            type=NodeType.GATE.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Ledger inclusion and append-only proofs',
            implementation='registry_merkle_v1.py',
            tests=30,
            phase='M14',
        ))

        self.add_node(Node(
            id='OTS',
            name='Anchor (OpenTimestamps)',
            type=NodeType.GATE.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='OpenTimestamps → Bitcoin anchor for root hash',
            implementation='anchor_root.sh',
            tests=0,
            phase='Phase 3 planned',
        ))

        # CLOSE SUBGRAPH
        self.add_node(Node(
            id='RC',
            name='Receipt Reconciliation',
            type=NodeType.RITUAL.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='B.6 ritual: claim vs tree walk-back; RECEIPT-GAP detection',
            implementation='receipt_reconciliation.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        self.add_node(Node(
            id='ST',
            name='Stale Sweep',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Nightly constant decay detection; emit STALE gaps for Z2 review',
            implementation='stale_sweep.py',
            tests=0,
            phase='M1-M15 (Phase 3 deployment)',
        ))

        # EDGES: Data and Control Flow
        edges = [
            # Intake → Runs
            ('Q', 'PRS', EdgeType.CONTROL_FLOW.value, 'work order', ''),
            ('Q', 'AG', EdgeType.CONTROL_FLOW.value, 'work order', ''),
            ('Q', 'OM', EdgeType.CONTROL_FLOW.value, 'work order', ''),
            ('Q', 'ADV', EdgeType.CONTROL_FLOW.value, 'work order', ''),

            # Runs → Ledgers
            ('PRS', 'EV', EdgeType.DATA_FLOW.value, 'CYCLE / VERDICT events', ''),
            ('AG', 'EV', EdgeType.DATA_FLOW.value, 'CYCLE / VERDICT events', ''),
            ('ADV', 'EV', EdgeType.DATA_FLOW.value, 'ATTACK / VERDICT events', ''),
            ('TC', 'EV', EdgeType.DATA_FLOW.value, 'score events', ''),

            # Measurements → Ledgers
            ('PRS', 'NF', EdgeType.DATA_FLOW.value, 'p_expected resolved', ''),
            ('OM', 'NF', EdgeType.DATA_FLOW.value, 'D10 predictions resolved', ''),

            # Events → Findings
            ('EV', 'FS', EdgeType.DATA_FLOW.value, 'events', ''),

            # Candidates → Gate
            ('FS', 'Z2', EdgeType.CONTROL_FLOW.value, 'candidate block', ''),
            ('OM', 'Z2', EdgeType.CONTROL_FLOW.value, 'candidate block', ''),
            ('PRS', 'Z2', EdgeType.DATA_FLOW.value, 'prereg sha', ''),

            # Gate → Registry
            ('Z2', 'CIG', EdgeType.CONTROL_FLOW.value, 'RATIFY event', ''),
            ('CIG', 'REG', EdgeType.CONTROL_FLOW.value, 'merge', ''),

            # Registry → Reads
            ('REG', 'PRS', EdgeType.DATA_FLOW.value, 'IC-030 live read', ''),
            ('REG', 'FS', EdgeType.DATA_FLOW.value, 'IC-030 live read', ''),
            ('REG', 'Q', EdgeType.DATA_FLOW.value, 'IC-030 live read', ''),
            ('REG', 'MOLT', EdgeType.DATA_FLOW.value, 'IC-030 live read', ''),

            # Close → Findings
            ('RC', 'Q', EdgeType.CALLOUT.value, 'RECEIPT-GAP callouts', ''),
            ('ST', 'OM', EdgeType.CALLOUT.value, 'STALE gaps', ''),
            ('ST', 'Q', EdgeType.CALLOUT.value, 'STALE gaps', ''),

            # Metrics → Queue
            ('NF', 'Q', EdgeType.DATA_FLOW.value, 'Brier trend', ''),
            ('TC', 'Q', EdgeType.CALLOUT.value, 'DRIFT', ''),

            # Molt Cycle
            ('NF', 'MOLT', EdgeType.DATA_FLOW.value, 'Brier per predictor / constant', ''),
            ('EV', 'MOLT', EdgeType.DATA_FLOW.value, 'verdict, catch, drift rates', ''),
            ('Q', 'MOLT', EdgeType.DATA_FLOW.value, 'pin vs re-score gaps', ''),
            ('ST', 'MOLT', EdgeType.DATA_FLOW.value, 'STALE constants', ''),

            # Molt → Z2
            ('MOLT', 'Z2', EdgeType.CONTROL_FLOW.value, 'MOLT_CANDIDATE: change, prediction, falsifier', ''),

            # Z2 → Molt
            ('Z2', 'MOLT', EdgeType.CONTROL_FLOW.value, 'RATIFY hash', ''),

            # Molt → Constants
            ('MOLT', 'CONST', EdgeType.CONTROL_FLOW.value, 'apply (ratified) / revert (mechanical)', ''),
            ('MOLT', 'ML', EdgeType.DATA_FLOW.value, 'MOLT / MEASURE / KEEP / REVERT events', ''),

            # Constants → Processes
            ('CONST', 'TC', EdgeType.DATA_FLOW.value, 'dials', ''),
            ('CONST', 'Q', EdgeType.DATA_FLOW.value, 'weights', ''),
            ('CONST', 'PRS', EdgeType.DATA_FLOW.value, 'rubrics', ''),
            ('CONST', 'AG', EdgeType.DATA_FLOW.value, 'caps', ''),

            # Molt Ledger → Event Chain
            ('ML', 'EV', EdgeType.DATA_FLOW.value, 'chained', ''),

            # Molt Predictions → NF
            ('MOLT', 'NF', EdgeType.DATA_FLOW.value, 'molt prediction resolved', ''),

            # Revert → Findings
            ('MOLT', 'FS', EdgeType.CALLOUT.value, 'REVERT → F/IC candidate', ''),

            # Gate Changes → ADV
            ('MOLT', 'ADV', EdgeType.CONTROL_FLOW.value, 'gate changed → re-run', ''),

            # Registry Merges
            ('REG', 'MK', EdgeType.DATA_FLOW.value, 'every merge', ''),

            # Merkle Checks
            ('MK', 'CIG', EdgeType.CONTROL_FLOW.value, 'consistency FAIL blocks merge', ''),

            # Merkle → Anchor
            ('MK', 'OTS', EdgeType.DATA_FLOW.value, 'root', ''),
        ]

        for source, target, edge_type, label, desc in edges:
            self.add_edge(Edge(
                source=source,
                target=target,
                edge_type=edge_type,
                label=label,
                description=desc,
            ))

        return {
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'status': 'GRAPH_BUILT',
        }
