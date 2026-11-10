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
    notes: str = ""            # caveats, e.g. why a node has no proven edge


@dataclass
class Edge:
    """Edge in system graph (connection between nodes)."""
    source: str
    target: str
    edge_type: str             # data_flow, control_flow, causality, callout
    label: str
    description: str = ""
    feedback: bool = False     # loop-closing edge; excluded from the acyclicity check


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
            warnings.append('Orphaned nodes (no edges): %s' % sorted(orphaned))

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
            if edge.feedback:
                continue
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

        # RESOURCE SUBGRAPH (Q-RBE-01) — CANDIDATE until Z2 ratifies
        # RESOURCE_UNITS.yaml. The economics side of the books: NF scores
        # predictions, RL scores consumption.
        self.add_node(Node(
            id='RU',
            name='Resource Units',
            type=NodeType.LEDGER.value,
            status=NodeStatus.LAID.value,
            zone='Z2',
            description=('Canonical unit registry: dimension, kind, sign, conservation, instrument, '
                         'substitutes, falsifier per unit. No numeraire; cross-dimension conversion '
                         'only via a measured PRICE event'),
            implementation='RESOURCE_UNITS.yaml',
            tests=0,
            phase='Q-RBE-01 (candidate)',
        ))

        self.add_node(Node(
            id='RL',
            name='Resource Ledger',
            type=NodeType.LEDGER.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description=('Append-only, hash-chained CLAIM / SPEND / YIELD / CAP / PRICE / WASTE / CLOSE '
                         'events; yield density per constraint unit'),
            implementation='resource_ledger_v0_1.py, ledgers/RESOURCE_LEDGER.jsonl',
            tests=0,
            phase='Q-RBE-01 (candidate)',
        ))

        self.add_node(Node(
            id='RCEN',
            name='Resource Census',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='Z1',
            description=('Mechanical count of open obligations, stocks and liabilities against the '
                         'binding constraint; writes outputs/resource_census.json'),
            implementation='resource_census_v0_1.py',
            tests=0,
            phase='Q-RBE-01 (candidate)',
        ))

        # ADDITIONS SINCE 2026-09-13 (regenerated 2026-11-08). Each node cites files
        # that exist in the tree; each edge below is backed by a reference in those files.
        self.add_node(Node(
            id='TDG',
            name='Temporal Dissolution Gate',
            type=NodeType.GATE.value,
            status=NodeStatus.OPERATED.value,
            zone='CI',
            description='Blocks PRs that add an unclassified internal time-based control (deadline, window, schedule); allowed classes OBSERVATIONAL, TECHNICAL_SAFETY, REGULATORY_EXTERNAL, HISTORICAL_RECORD',
            implementation='tests/test_temporal_dissolution_gate.py, .github/workflows/temporal-dissolution-gate.yml',
            tests=10,
            phase='post-M15 (added 2026-11-08)',
            notes='No proven edge. It is a standalone workflow and test; ci_gates.py and z2_ratification_gate.yml do not reference it, so it was not linked to CIG. Removed after review.',
        ))

        self.add_node(Node(
            id='MTC',
            name='Molt Tier Check',
            type=NodeType.GATE.value,
            status=NodeStatus.OPERATED.value,
            zone='CI',
            description="Advisory: measures a PR's molt tier (0/1/2) from the paths its diff touches and compares it with the author's claim; advisory only, does not block merge",
            implementation='tools/molting_protocol_diff_v1_0.py, .github/workflows/molt-tier-check.yml',
            tests=0,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='CIP',
            name='CI Prediction',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='CI',
            description="PIN a PR author's per-check predictions before checks resolve, RESOLVE against actual conclusions, CONSOLIDATE into a hash-chained ledger; inherited declarations are refused",
            implementation='tools/ci_predict_pin_v1_0.py, tools/ci_predict_resolve_v1_0.py, tools/ci_predict_consolidate_v1_0.py',
            tests=57,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='SMAG',
            name='SMAG Calibration Loop',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description="Author-confidence capture on PRs, consolidation, gap analysis and feedback; Meta-SMAG reviews the loop's own accuracy",
            implementation='tools/smag_consolidate_v1_0.py, tools/smag_gap_analysis_v1_0.py, .github/workflows/smag-capture.yml, .github/workflows/smag-consolidate.yml',
            tests=26,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='EMP',
            name='Empirica Connector',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Connects SMAG calibration output to Empirica and records on-track reflex checkpoints',
            implementation='tools/smag_to_empirica_connector.py, .github/workflows/on-track-reflex-observe.yml, .empirica_reflex_logs/',
            tests=0,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='IOS',
            name='Intent-OS',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='Z1',
            description='Intent board, form and collaboration surfaces; reconcile relays awaiting_z2 candidates to Z2 (merge is the Z2 act); test harness tiers T0-T7',
            implementation='INTENT_GRAPH.yaml, tools/intent_os_reconcile_v1_0.py, tools/intent_os_test_harness_v1_0.py, .github/workflows/intent-os-reconcile.yml',
            tests=14,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='RCO',
            name='Repository Coordinator',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='CI',
            description='Admission and backpressure index over open PRs (lanes, operator-queue capacity, decision receipts); admission routing only, no merge authority',
            implementation='tools/repository_coordinator_v0_1.py, .github/workflows/repository-coordinator.yml',
            tests=99,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='SG',
            name='System Graph',
            type=NodeType.LEDGER.value,
            status=NodeStatus.OPERATED.value,
            zone='Z2',
            description='This graph: canonical machine form of the governance process graph, generated from the edge list, validated for dangling edges and forward cycles',
            implementation='system_graph_generator.py, system_graph.json',
            tests=5,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='SGF',
            name='System Graph Freshness',
            type=NodeType.GATE.value,
            status=NodeStatus.LAID.value,
            zone='CI',
            description='Fails when the committed graph is invalid, differs from generator output, or (weekly) is older than 45 days; graph-capture-lint scores the multiplex',
            implementation='tools/graph_capture_lint_v1_0.py, .github/workflows/system-graph-freshness.yml, .github/workflows/graph-capture-lint.yml',
            tests=48,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='ORC',
            name='Oracle Engine',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Projects repository and workspace state (including system_graph.json) into oracle assertions; forecast replay',
            implementation='oracles/engine/oracle_engine_v0_1.py',
            tests=43,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='ACAT',
            name='ACAT API',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='ACAT assessment API with async job queue and database, deployed on Railway',
            implementation='acat/api, acat/db',
            tests=76,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='ACATR',
            name='ACAT-R',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='General runtime calibration research prototype built on the three-phase ACAT method; authority effect NONE',
            implementation='experiments/acat_r_v01, .github/workflows/acat-r-v01.yml',
            tests=40,
            phase='post-M15 (added 2026-11-08)',
            notes='No proven edge. Its README says it extends the three-phase ACAT method; that is a method, not the code in acat/api, so no edge to the ACAT API node was kept.',
        ))

        self.add_node(Node(
            id='RMN',
            name='Resource Miner',
            type=NodeType.PROCESS.value,
            status=NodeStatus.OPERATED.value,
            zone='code',
            description='Broad discovery of externally available resource opportunities; upstream of Entitlement Navigator',
            implementation='humanaios-funding-pipeline/resource-miner, .github/workflows/resource-miner-scan.yml',
            tests=0,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='ENAV',
            name='Entitlement Navigator',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Resolves candidate opportunities toward eligibility and acquisition',
            implementation='humanaios-funding-pipeline/entitlement-navigator',
            tests=0,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='RSYS',
            name='Resource System',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Local prototype v0.1 (issue #588) composing Resource Miner and Entitlement Navigator through their handoff functions; caller-driven, explicit-tick only',
            implementation='humanaios-resource-system/resource_system',
            tests=55,
            phase='post-M15 (added 2026-11-08)',
        ))

        self.add_node(Node(
            id='MODE',
            name='MODE-HumanAIOS Interop E0',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Candidate-only synthetic interoperability and publisher-influence experiments; no credentials, providers or authority',
            implementation='experiments/mode_haios_interop_e0.py, .github/workflows/mode-haios-interop-e0.yml',
            tests=15,
            phase='post-M15 (added 2026-11-08)',
            notes='No proven edge. The E0 workflow runs tests/test_verified_receipts.py and lists tools/verified_receipts.py as a trigger path, but experiments/mode_haios_interop_e0.py imports nothing from it. A trigger path is not a data flow.',
        ))

        self.add_node(Node(
            id='COCK',
            name='Cockpit v1',
            type=NodeType.PROCESS.value,
            status=NodeStatus.PLANNED.value,
            zone='Z1',
            description='Unified operator view candidate; docs only, pending Z2 ratification',
            implementation='COCKPIT_V1_PRIORITY_QUEUE_ENTRY.md, COCKPIT_V1_IMPLEMENTATION_ROADMAP.md',
            tests=0,
            phase='post-M15 (added 2026-11-08)',
        ))

        # SECOND PASS (2026-11-10): nodes from the PRs the first pass left unsorted.
        self.add_node(Node(
            id='VER',
            name='Verified Receipts',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Shared verifier for receipts that name an observed action and outcome; imported by the collaboration-harmony prototype and the Core Machine (humanaios_core_machine_v0_1.py line 649); the MODE E0 workflow runs its tests but does not import it',
            implementation='tools/verified_receipts.py, tests/test_verified_receipts.py',
            tests=17,
            phase='post-M15 (second pass 2026-11-10)',
        ))

        self.add_node(Node(
            id='GNER',
            name='GitHub Notification Evidence Relay',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Read-only relay: treats email as untrusted discovery only and verifies GitHub receipts outside the module (E0 interpret, E1 verify, E2 failure-signature correlation); no authority',
            implementation='tools/gner_notification_e0.py, tools/gner_verify_e1.py, tools/gner_failure_signatures_e2.py',
            tests=32,
            phase='post-M15 (second pass 2026-11-10)',
            notes='No proven edge. gner_notification_e0.py only has a parameter named verified_receipts; it does not import tools/verified_receipts.py, and E1 verifies run metadata through the GitHub API directly. Removed after review.',
        ))

        self.add_node(Node(
            id='HCOLLAB',
            name='Collaboration Harmony Prototype',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Executable stress prototype for H-COLLAB-HARMONY-01 that consumes pinned verified receipts',
            implementation='experiments/collab_harmony_01',
            tests=8,
            phase='post-M15 (second pass 2026-11-10)',
        ))

        self.add_node(Node(
            id='HCM',
            name='HumanAIOS Core Machine v0.1',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Bytecode compiler, integrity-checking decoder and pure replay VM for the Operations contract; no external-action handler; authority effect NONE; ratified as Q-HCM-CORE-MACHINE-01',
            implementation='tools/humanaios_core_machine_v0_1.py, humanaios_core.py',
            tests=47,
            phase='post-M15 (second pass 2026-11-10)',
        ))

        self.add_node(Node(
            id='CONV',
            name='Graph Convergence Grader',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Grades convergence between two agent-authored graphs by source disjointness and access record; corroboration weight is zero when both read the same source',
            implementation='tools/graph_convergence_v1_0.py, GRAPH_CONVERGENCE.md',
            tests=0,
            phase='post-M15 (second pass 2026-11-10)',
        ))

        self.add_node(Node(
            id='WIT',
            name='Witness',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Witness framework and experiments (arena, live proof, voice texture, SCVC milestone witness) plus the REGISTERED.md fix-citation check; read-only and evidence-first',
            implementation='tools/witness_framework.py, WITNESS_SERVICE_CONTRACT.md, experiments/witness-arena, .github/workflows/scvc-milestone-witness.yml',
            tests=15,
            phase='post-M15 (second pass 2026-11-10)',
        ))

        self.add_node(Node(
            id='HIAE',
            name='HIAE Assurance',
            type=NodeType.PROCESS.value,
            status=NodeStatus.PLANNED.value,
            zone='Z1',
            description='Z1 proposal, not ratified: neutral rotation-based reviewer assignment with conflict exclusion and versioned assessment receipts',
            implementation='tools/hiae_assurance.py',
            tests=39,
            phase='post-M15 (second pass 2026-11-10)',
            notes='No proven edge. The receipt carries an acat_version string (example value hard-coded), which names a protocol version and does not consume output from acat/api. Removed after review.',
        ))

        # DOCUMENTED ORPHANS (2026-11-10): real, present in the tree, but no edge could be proven from files.
        # Each carries a note saying why. They are kept visible so a reader does not assume the graph is complete.
        self.add_node(Node(
            id='CUST',
            name='Control-Plane Custody Observer',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Normalizes replayable control-plane observations and derives custody state; read-only, observation is not authority (CPC-001)',
            implementation='tools/control_plane_custody_observer_v0_1.py, schemas/control_plane_custody_event_v0_1.schema.json',
            tests=5,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. PR titles say it adapts GitHub evidence into custody observations (#621, #623), but no file in the tree names the producer or consumer of that data. Add an edge when one does.',
        ))

        self.add_node(Node(
            id='WEB',
            name='Workspace Evidence Bus',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Connects Google Workspace evidence custody to GitHub validation (issue #681) without making Gmail, Drive or GitHub the single source of truth; round-trip CI workflow',
            implementation='workspace_evidence_bus/, .github/workflows/workspace-evidence-bus-roundtrip.yml',
            tests=10,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. Its README names external systems (Gmail, Drive, Apps Script, GitHub), none of which are graph nodes. The link to HMBM continuity (#685) is by PR title only.',
        ))

        self.add_node(Node(
            id='ATLAS',
            name='Codebase Atlas',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Internal evidence-linked atlas of the codebase (issue #834) with component map and bridges; has its own CI workflow',
            implementation='architecture/codebase_atlas.py, architecture/codebase_atlas_bridges.py, .github/workflows/codebase-atlas.yml',
            tests=18,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes="No proven edge. It describes the codebase and may read many nodes' files, but no single reference was checked. Status not verified by a run.",
        ))

        self.add_node(Node(
            id='ITEL',
            name='Industry Telemetry',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Bounded Q4 industry telemetry and human triage pilot: fetches fixed public indexes and proposes human review of new links; no forecast resolution, no governance change',
            implementation='tools/industry_telemetry_v0_1.py, .github/workflows/industry-telemetry.yml',
            tests=8,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. Observational only by design (temporal class OBSERVATIONAL): its output goes to human triage, not to a graph node.',
        ))

        self.add_node(Node(
            id='OBS',
            name='Operations Observatory E0',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Living Operations Observatory: read-only three-repo GitHub kinetics view (issue #1088), browser UI plus tests',
            implementation='ui/operations-observatory-e0.js, ui/operations-observatory-e0.html, tools/tests/test_operations_observatory_e0.py',
            tests=5,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. Reads GitHub activity, which is outside the graph. Risk-observation tests (RISK-OBS-001) mention it, but the direction of any data flow was not checked.',
        ))

        self.add_node(Node(
            id='HOBJ',
            name='Human Objective E0/E1',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Offline human-objective to evidence-backed synthetic recommendation (E0), and URA-format recommendation (E1); synthetic fixtures only',
            implementation='experiments/human_objective_e0.py, experiments/human_objective_e1.py',
            tests=17,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. The MODE E0 workflow lists human_objective_e1.py among its trigger paths, but a trigger path does not show a data flow, so no edge was added.',
        ))

        self.add_node(Node(
            id='GPCS',
            name='GPCS Translation Contract',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='GPCS-001: advisory cross-session memory translation contract with its own CI workflow',
            implementation='gpcs/translation.py, .github/workflows/gpcs-contract.yml',
            tests=9,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. Advisory by its own description. No file shows which node consumes the translation.',
        ))

        self.add_node(Node(
            id='DIGEST',
            name='Daily Topic Digest',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Scheduled platform signal collection, topic-to-mitigation mapping and gap detection; inbound email command processor for digest replies',
            implementation='scripts/platform-monitor.py, scripts/map-to-mitigation.py, scripts/gap-detector.py, entry_protocol/gmail_push_adapter.py, .github/workflows/daily-topic-digest.yml',
            tests=0,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. It runs on a schedule, so it carries a temporal class that was not reviewed here. Test count 0 because no matching test file was identified.',
        ))

        self.add_node(Node(
            id='GL',
            name='Guiding Light',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='General evidence-to-target gradient engine (v0.2) with adapters and a career-gradient example',
            implementation='services/guiding_light.py, services/guiding_light_adapters.py, data/GUIDING_LIGHT_GRADIENT.schema.json',
            tests=10,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes="No proven edge. Its docs describe user-facing gradients; none of the graph's nodes is named as input or output.",
        ))

        self.add_node(Node(
            id='ORCID',
            name='ORCID Publications Reconcile',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Read-only ORCID reconciliation (milestone B) for the publications manager, with tests run in CI',
            implementation='orcid-publications-manager/orcid_works.py, orcid-publications-manager/fetch_orcid.py, .github/workflows/orcid-reconcile-tests.yml',
            tests=33,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='No proven edge. Talks to an external service (ORCID) only.',
        ))

        self.add_node(Node(
            id='EXPS',
            name='Z1 Research Experiments',
            type=NodeType.PROCESS.value,
            status=NodeStatus.LAID.value,
            zone='Z1',
            description='Grouped research tree: arena, automata lineage lab, constitutional tuning, PIER-001, OSF OAuth audit, wardens, risk-obs-001, SCVC and others; each has its own protocol and tests',
            implementation='experiments/',
            tests=0,
            phase='post-M15 (orphan, noted 2026-11-10)',
            notes='Grouped node, not one process. No proven edge as a whole; some members are covered by their own nodes (ACAT-R, MODE, Witness, Collaboration Harmony). Test count 0 because the tree has many suites that were not totalled.',
        ))

        self.add_node(Node(
            id='CIL',
            name='CI Prediction Ledger',
            type=NodeType.LEDGER.value,
            status=NodeStatus.LAID.value,
            zone='code',
            description='Hash-chained ledger of CI-check predictions, kept separate from NF_LEDGER.jsonl on purpose so no pending Z2 governance item is settled by side effect',
            implementation='ledgers/CI_PREDICT_LEDGER.jsonl, .github/workflows/ci-predict-consolidate.yml',
            tests=57,
            phase='post-M15 (added 2026-11-10 after review)',
            notes='Status from file presence and a consolidating workflow, not from a verified run.',
        ))

        # Loop-closing edges. The governance machinery is a deliberate feedback
        # loop (measure -> propose -> ratify -> apply -> measure), so a strict
        # DAG check over every edge cannot pass. These edges are the ones that
        # return state to an earlier stage; the forward edges must stay acyclic
        # (validate_graph), so a NEW cycle among forward edges is still an error.
        # Keep this set minimal: tests/test_system_graph_generator.py asserts
        # that removing any one entry reintroduces a cycle.
        feedback_edges = {
            ('REG', 'PRS'), ('REG', 'FS'), ('REG', 'Q'), ('REG', 'MOLT'),
            ('NF', 'Q'), ('Z2', 'MOLT'), ('ML', 'EV'), ('Q', 'RL'), ('Z2', 'RL'),
            ('MK', 'CIG'), ('CONST', 'TC'), ('CONST', 'Q'), ('CONST', 'PRS'),
            ('CONST', 'AG'), ('MOLT', 'NF'), ('MOLT', 'ADV'),
        }

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

            # Resource subgraph (Q-RBE-01)
            ('RU', 'RL', EdgeType.DATA_FLOW.value, 'registered units; unknown unit refused', ''),
            ('RU', 'RCEN', EdgeType.DATA_FLOW.value, 'demand priors, constraint designation', ''),
            ('RCEN', 'RL', EdgeType.DATA_FLOW.value, 'obligation counts priced in the constraint unit', ''),
            ('RCEN', 'Q', EdgeType.CALLOUT.value, 'constraint backlog / oversubscription', ''),
            ('RL', 'Q', EdgeType.DATA_FLOW.value, 'cost vectors, measured prices, yield density', ''),
            ('Q', 'RL', EdgeType.DATA_FLOW.value, 'CLAIM per work order', ''),
            ('Z2', 'RL', EdgeType.DATA_FLOW.value, 'RAT-min SPEND; capacity declaration (hashed)', ''),
            ('RL', 'MOLT', EdgeType.DATA_FLOW.value, 'density trend vs constraint constants', ''),
            ('RCEN', 'FS', EdgeType.CALLOUT.value, 'F-RBE candidates', ''),
            # Added 2026-11-08 (each backed by a reference in the cited files)
            ('MTC', 'MOLT', EdgeType.DATA_FLOW.value, 'classifier named in MOLT_STATE.md; measured tier vs claimed (advisory)', ''),
            ('CIP', 'CIL', EdgeType.DATA_FLOW.value, 'PIN / RESOLVE events, hash-chained (separate from NF by design)', ''),
            ('SMAG', 'EMP', EdgeType.DATA_FLOW.value, 'smag_to_empirica_connector', ''),
            ('IOS', 'Z2', EdgeType.CONTROL_FLOW.value, 'awaiting_z2 candidate relay; merge is the Z2 act', ''),
            ('RCO', 'Z2', EdgeType.CONTROL_FLOW.value, 'ROUTE_TO_Z2; receipts are admission routing only', ''),
            ('SGF', 'SG', EdgeType.CONTROL_FLOW.value, 'fails PR / weekly when stale or invalid', ''),
            ('SG', 'ORC', EdgeType.DATA_FLOW.value, 'repository projection reads system_graph.json', ''),
            ('IOS', 'ACAT', EdgeType.CONTROL_FLOW.value, 'harness tier T6 boots the ACAT API', ''),
            ('RMN', 'ENAV', EdgeType.DATA_FLOW.value, 'upstream discovery handoff', ''),
            ('RMN', 'RSYS', EdgeType.DATA_FLOW.value, 'handoff function composed by Resource System', ''),
            ('ENAV', 'RSYS', EdgeType.DATA_FLOW.value, 'handoff function composed by Resource System', ''),
            ('COCK', 'Q', EdgeType.CONTROL_FLOW.value, 'candidate block for PRIORITY_QUEUE.md (pending Z2)', ''),

            # Second pass (2026-11-10), each backed by a reference in the cited files
            ('VER', 'HCOLLAB', EdgeType.DATA_FLOW.value, 'consumes pinned verified receipts', ''),
            ('VER', 'HCM', EdgeType.DATA_FLOW.value, 'verified-receipt consumption contract', ''),
            ('Z2', 'HCM', EdgeType.CAUSALITY.value, 'ratified as Q-HCM-CORE-MACHINE-01', ''),
            ('IOS', 'CONV', EdgeType.DATA_FLOW.value, 'INTENT_GRAPH / EVIDENCE_GRAPH read for grading', ''),
            ('REG', 'WIT', EdgeType.DATA_FLOW.value, 'REGISTERED.md Fix-citation entries read', ''),
        ]


        for source, target, edge_type, label, desc in edges:
            self.add_edge(Edge(
                source=source,
                target=target,
                edge_type=edge_type,
                label=label,
                description=desc,
                feedback=(source, target) in feedback_edges,
            ))

        return {
            'nodes': len(self.nodes),
            'edges': len(self.edges),
            'status': 'GRAPH_BUILT',
        }


# --------------------------------------------------------------------------
# CLI — regenerate / check. Added so the graph can be kept fresh mechanically.
#   python3 system_graph_generator.py --write            regenerate system_graph.json
#   python3 system_graph_generator.py --check            exit 1 if invalid, or the
#                                                         committed JSON differs from
#                                                         what this generator emits
#                                                         (generated_at ignored)
#   python3 system_graph_generator.py --check --max-age-days 45
#                                                         also exit 1 if generated_at
#                                                         is older than N days
# --------------------------------------------------------------------------
import argparse
import os
import sys

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_graph.json')


def build_graph_dict() -> Dict[str, Any]:
    gen = SystemGraphGenerator()
    gen.build_phase2_graph()
    return json.loads(gen.to_json())


def _comparable(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if k != 'generated_at'}


def check(path: str, max_age_days: Optional[int] = None) -> List[str]:
    """Return a list of problems (empty = fresh and valid)."""
    problems: List[str] = []
    fresh = build_graph_dict()
    if not fresh['validation_status']['valid']:
        problems.append('generator output is invalid: %s' % fresh['validation_status']['errors'])
    try:
        with open(path) as f:
            committed = json.load(f)
    except (OSError, ValueError) as e:
        return problems + ['cannot read %s: %s' % (path, e)]
    if _comparable(committed) != _comparable(fresh):
        problems.append('%s differs from generator output: run `python3 system_graph_generator.py --write`'
                        % os.path.basename(path))
    try:
        stamp = datetime.fromisoformat(committed['generated_at'])
    except (KeyError, TypeError, ValueError):
        problems.append('generated_at is missing or not an ISO timestamp')
    else:
        if max_age_days is not None:
            age = (datetime.now() - stamp).days
            if age > max_age_days:
                problems.append('generated_at is %d days old (limit %d)' % (age, max_age_days))
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Regenerate or check system_graph.json')
    ap.add_argument('--path', default=DEFAULT_PATH)
    ap.add_argument('--write', action='store_true', help='regenerate the JSON file')
    ap.add_argument('--check', action='store_true', help='exit 1 if stale or invalid')
    ap.add_argument('--max-age-days', type=int, default=None)
    args = ap.parse_args(argv)
    if not (args.write or args.check):
        ap.error('pass --write or --check')
    if args.write:
        fresh = build_graph_dict()
        if not fresh['validation_status']['valid']:
            print('REFUSING to write invalid graph: %s' % fresh['validation_status']['errors'], file=sys.stderr)
            return 1
        with open(args.path, 'w') as f:
            f.write(json.dumps(fresh, indent=2) + '\n')
        print('wrote %s: %d nodes, %d edges' % (args.path, len(fresh['nodes']), len(fresh['edges'])))
        return 0
    problems = check(args.path, args.max_age_days)
    for p in problems:
        print('STALE/INVALID: ' + p, file=sys.stderr)
    if not problems:
        print('system_graph.json fresh and valid')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
