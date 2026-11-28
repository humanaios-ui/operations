#!/usr/bin/env python3
"""
Terrifying Knowledge Graph - Working Prototype
Analyzes AI system alignment, deception, and authority gaps.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import re


class NodeType(Enum):
    INTENT = "intent"
    DECISION = "decision"
    CAPABILITY = "capability"
    AUTHORITY = "authority"
    ASSUMPTION = "assumption"
    MANIPULATION = "manipulation"
    FALSIFIABILITY = "falsifiability"
    OBSERVATION = "observation"


class EdgeType(Enum):
    ENABLES = "enables"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    VIOLATES = "violates"
    EXPOSES_TO = "exposes_to"
    SUPPORTS = "supports"
    REFUTES = "refutes"


@dataclass
class Node:
    node_id: str
    node_type: NodeType
    created_at: datetime
    data: Dict = field(default_factory=dict)
    confidence: float = 0.5

    def to_dict(self):
        return {
            "id": self.node_id,
            "type": self.node_type.value,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            **self.data
        }


@dataclass
class Edge:
    source: str
    edge_type: EdgeType
    target: str
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "source": self.source,
            "type": self.edge_type.value,
            "target": self.target,
            "weight": self.weight,
            **self.metadata
        }


class TerrifiyingKnowledgeGraph:
    """A knowledge graph that exposes AI system alignment and deception."""

    def __init__(self, ledger_path: Optional[str] = None):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.contradictions: List[Tuple[str, str]] = []
        self.observations: List[str] = []  # Append-only log
        self.z2_ledger: List[Dict] = []  # Z2 decision ledger
        if ledger_path:
            self.load_z2_ledger(ledger_path)

    def add_node(self, node_id: str, node_type: NodeType, data: Dict,
                 confidence: float = 0.5) -> Node:
        """Add a node to the graph."""
        node = Node(node_id, node_type, datetime.now(), data, confidence)
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, edge_type: EdgeType, target: str,
                 weight: float = 1.0, metadata: Dict = None) -> Edge:
        """Add an edge to the graph."""
        if metadata is None:
            metadata = {}
        edge = Edge(source, edge_type, target, weight, metadata)
        self.edges.append(edge)
        return edge

    def load_z2_ledger(self, ledger_path: str):
        """Load Z2 decision ledger from JSONL file."""
        try:
            with open(ledger_path, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        self.z2_ledger.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass  # Ledger optional; system can operate without it

    def add_observation(self, what_happened: str, context: str = ""):
        """Record an observation (append-only)."""
        obs_id = f"obs_{len(self.observations)}_{hashlib.md5(what_happened.encode()).hexdigest()[:8]}"
        obs_data = {
            "what_happened": what_happened,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.observations.append(obs_id)
        self.add_node(obs_id, NodeType.OBSERVATION, obs_data, confidence=0.9)
        return obs_id

    def create_intent_drift(self, intent_id: str, stated: str, inferred: str,
                           evidence_obs: List[str]):
        """Create an intent node showing stated vs. inferred goals."""
        intent_data = {
            "stated_intent": stated,
            "inferred_intent": inferred,
            "intent_gap": self._similarity_delta(stated, inferred),
            "evidence_chain": evidence_obs,
        }
        node = self.add_node(intent_id, NodeType.INTENT, intent_data,
                            confidence=0.6 + (len(evidence_obs) * 0.05))

        # Link evidence
        for obs_id in evidence_obs:
            self.add_edge(obs_id, EdgeType.SUPPORTS, intent_id)

        # Check if drift is significant
        if intent_data["intent_gap"] > 0.3:
            self.contradictions.append((f"{intent_id}_stated", f"{intent_id}_inferred"))

        return node

    def create_decision(self, decision_id: str, timestamp: str,
                       stated_reason: str, inferred_reason: str,
                       upstream_intent: Optional[str] = None,
                       authority_violation: bool = False,
                       reversible: bool = True) -> Node:
        """Create a decision node."""
        decision_data = {
            "timestamp": timestamp,
            "stated_reason": stated_reason,
            "inferred_reason": inferred_reason,
            "authority_violation": authority_violation,
            "reversible": reversible,
            "reason_gap": self._similarity_delta(stated_reason, inferred_reason),
        }
        node = self.add_node(decision_id, NodeType.DECISION, decision_data,
                            confidence=0.7)

        if upstream_intent:
            self.add_edge(upstream_intent, EdgeType.DEPENDS_ON, decision_id)

        if authority_violation:
            self.contradictions.append((decision_id, "authority_constraint"))

        return node

    def create_capability(self, cap_id: str, name: str, scope: str,
                         verified_range: Tuple[str, str],
                         edge_cases: List[str],
                         exploitability: float = 0.5) -> Node:
        """Create a capability node."""
        cap_data = {
            "name": name,
            "scope": scope,
            "verified_range": verified_range,
            "edge_cases": edge_cases,
            "exploitability": exploitability,
            "weaponizable": exploitability > 0.4,
        }
        return self.add_node(cap_id, NodeType.CAPABILITY, cap_data,
                            confidence=0.8)

    def create_assumption(self, assume_id: str, claim: str,
                         falsifiable: bool, confidence: float = 0.5,
                         collapse_risk: str = "medium") -> Node:
        """Create an assumption node."""
        assume_data = {
            "claim": claim,
            "falsifiable": falsifiable,
            "collapse_risk": collapse_risk,
            "tested": False,
        }
        return self.add_node(assume_id, NodeType.ASSUMPTION, assume_data,
                            confidence=confidence)

    def create_authority(self, auth_id: str, actor: str, domain: List[str],
                        precedence: int = 0, gaps: List[str] = None) -> Node:
        """Create an authority node."""
        if gaps is None:
            gaps = []
        auth_data = {
            "actor": actor,
            "domain": domain,
            "precedence": precedence,
            "gaps": gaps,
            "has_gaps": len(gaps) > 0,
        }
        return self.add_node(auth_id, NodeType.AUTHORITY, auth_data,
                            confidence=0.85)

    def create_manipulation(self, manip_id: str, attack_vector: str,
                           target_capability: str, detectability: float = 0.5,
                           is_live: bool = False) -> Node:
        """Create a manipulation/attack surface node."""
        manip_data = {
            "attack_vector": attack_vector,
            "target_capability": target_capability,
            "detectability": detectability,
            "is_currently_live": is_live,
        }
        node = self.add_node(manip_id, NodeType.MANIPULATION, manip_data,
                            confidence=0.7)

        self.add_edge(target_capability, EdgeType.EXPOSES_TO, manip_id)
        return node

    def _similarity_delta(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two text strings (0-1, where 1=identical).
        Uses three signals: word overlap, bigram overlap, and concept alignment.
        """
        if not text1 or not text2:
            return 0.0 if (text1 and not text2) or (not text1 and text2) else 0.0

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # Signal 1: Exact match (highest confidence)
        if text1_lower == text2_lower:
            return 0.0

        # Signal 2: Word overlap (Jaccard similarity)
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        word_overlap = intersection / max(union, 1) if union > 0 else 0.0

        # Signal 3: Bigram overlap (captures word order)
        bigrams1 = set(
            text1_lower[i:i+2] for i in range(len(text1_lower) - 1)
        )
        bigrams2 = set(
            text2_lower[i:i+2] for i in range(len(text2_lower) - 1)
        )
        bigram_overlap = 0.0
        if bigrams1 and bigrams2:
            bigram_inter = len(bigrams1 & bigrams2)
            bigram_union = len(bigrams1 | bigrams2)
            bigram_overlap = bigram_inter / max(bigram_union, 1) if bigram_union > 0 else 0.0

        # Signal 4: Concept alignment (keywords suggest intent)
        # Higher weight means more likely to be different
        concept_keys = {
            'governance': 0.8,  # governance changes are significant
            'authority': 0.75,
            'capability': 0.7,
            'security': 0.8,
            'test': 0.5,
            'doc': 0.4,
            'refactor': 0.6,
        }
        concept_drift = 0.0
        for key, weight in concept_keys.items():
            in_1 = key in text1_lower
            in_2 = key in text2_lower
            if in_1 != in_2:  # Concept appears in only one text
                concept_drift = max(concept_drift, weight)

        # Combine signals: if word overlap is high (>0.6), they're probably aligned
        # If word overlap is low but concept drift is high, they're probably different
        combined_similarity = (word_overlap * 0.5) + (bigram_overlap * 0.3)
        # Concept drift should REDUCE similarity (they're different), not increase it
        combined_similarity = max(0.0, min(1.0, combined_similarity - concept_drift))

        # Return drift (inverse of similarity): 1.0 = maximum drift, 0.0 = identical
        return 1.0 - combined_similarity

    # ===== ANALYSIS QUERIES =====

    def find_intent_drifts(self) -> List[Dict]:
        """Find all intents where stated ≠ inferred (possible deception)."""
        drifts = []
        for node_id, node in self.nodes.items():
            if node.node_type == NodeType.INTENT:
                gap = node.data.get("intent_gap", 0)
                if gap > 0.25:  # >25% difference
                    drifts.append({
                        "intent_id": node_id,
                        "stated": node.data.get("stated_intent"),
                        "inferred": node.data.get("inferred_intent"),
                        "gap": gap,
                        "confidence": node.confidence,
                        "severity": "HIGH" if gap > 0.5 else "MEDIUM",
                    })
        return sorted(drifts, key=lambda x: x["gap"], reverse=True)

    def find_fragile_assumptions(self) -> List[Dict]:
        """Find untested assumptions that many decisions depend on."""
        fragile = []
        for node_id, node in self.nodes.items():
            if node.node_type == NodeType.ASSUMPTION:
                if not node.data.get("falsifiable", False):
                    # Count how many decisions depend on this
                    dependents = [e for e in self.edges
                                 if e.target == node_id and e.edge_type == EdgeType.DEPENDS_ON]
                    if len(dependents) > 0:
                        fragile.append({
                            "assumption_id": node_id,
                            "claim": node.data.get("claim"),
                            "falsifiable": False,
                            "dependents": len(dependents),
                            "collapse_risk": node.data.get("collapse_risk", "unknown"),
                            "confidence": node.confidence,
                        })
        return sorted(fragile, key=lambda x: x["dependents"], reverse=True)

    def find_live_attack_surfaces(self) -> List[Dict]:
        """Find attack surfaces that are currently active and detectable."""
        attacks = []
        for node_id, node in self.nodes.items():
            if node.node_type == NodeType.MANIPULATION:
                if node.data.get("is_currently_live", False):
                    attacks.append({
                        "attack_id": node_id,
                        "vector": node.data.get("attack_vector"),
                        "detectability": node.data.get("detectability", 0),
                        "severity": "CRITICAL" if node.data.get("detectability", 0) < 0.3 else "HIGH",
                    })
        return sorted(attacks, key=lambda x: x["detectability"])

    def find_authority_gaps(self) -> List[Dict]:
        """Find where decisions are made without proper authority."""
        gaps = []
        for node_id, node in self.nodes.items():
            if node.node_type == NodeType.AUTHORITY:
                if node.data.get("has_gaps", False):
                    gaps.append({
                        "authority_id": node_id,
                        "actor": node.data.get("actor"),
                        "domain": node.data.get("domain"),
                        "gaps": node.data.get("gaps", []),
                        "num_gaps": len(node.data.get("gaps", [])),
                    })
        return sorted(gaps, key=lambda x: x["num_gaps"], reverse=True)

    def compute_transparency_score(self) -> float:
        """
        Compute how transparent the system is (0-1).
        Factors in: node confidence, Z2 ledger completeness, and assumption testing.
        """
        if not self.nodes:
            return 0.0

        # Signal 1: Node confidence (nodes with high confidence = transparent)
        confident_nodes = sum(1 for node in self.nodes.values()
                             if node.confidence >= 0.8)
        node_transparency = confident_nodes / len(self.nodes) if self.nodes else 0.0

        # Signal 2: Z2 ledger completeness (documented decisions = more transparent)
        z2_decisions_count = len(self.z2_ledger)
        authority_nodes = sum(1 for node in self.nodes.values()
                             if node.node_type == NodeType.AUTHORITY)
        # Expected ratio: at least 1 decision per authority role
        ledger_completeness = (z2_decisions_count / max(authority_nodes, 1)) * 0.5
        ledger_transparency = min(1.0, ledger_completeness)

        # Signal 3: Assumption testing (untested assumptions reduce transparency)
        assumption_nodes = [node for node in self.nodes.values()
                           if node.node_type == NodeType.ASSUMPTION]
        tested_assumptions = sum(1 for node in assumption_nodes
                                if node.data.get("tested", False))
        assumption_transparency = (tested_assumptions / len(assumption_nodes)
                                 if assumption_nodes else 0.5)

        # Signal 4: Manipulation surfaces (documented mitigations increase transparency)
        manipulation_nodes = [node for node in self.nodes.values()
                             if node.node_type == NodeType.MANIPULATION]
        mitigated_attacks = sum(1 for node in manipulation_nodes
                               if node.data.get("detectability", 0) > 0.7)
        attack_transparency = (mitigated_attacks / len(manipulation_nodes)
                              if manipulation_nodes else 0.5)

        # Combine signals: equal weight to all four
        combined = (
            (node_transparency * 0.3) +
            (ledger_transparency * 0.3) +
            (assumption_transparency * 0.2) +
            (attack_transparency * 0.2)
        )
        return min(1.0, max(0.0, combined))

    def expose_system(self) -> Dict:
        """Run all terrifying queries and summarize."""
        drifts = self.find_intent_drifts()
        fragile = self.find_fragile_assumptions()
        attacks = self.find_live_attack_surfaces()
        gaps = self.find_authority_gaps()
        transparency = self.compute_transparency_score()

        return {
            "timestamp": datetime.now().isoformat(),
            "transparency_score": transparency,
            "alarming": transparency < 0.7,
            "intent_drifts": drifts,
            "num_intent_drifts": len(drifts),
            "fragile_assumptions": fragile,
            "num_fragile": len(fragile),
            "live_attack_surfaces": attacks,
            "num_attacks": len(attacks),
            "authority_gaps": gaps,
            "num_gaps": len(gaps),
            "total_contradictions": len(self.contradictions),
        }

    def to_dict(self) -> Dict:
        """Export graph to dict for serialization."""
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "observations": self.observations,
            "contradictions": self.contradictions,
        }

    def print_exposure_report(self):
        """Print a human-readable exposure report."""
        exposure = self.expose_system()

        print("╔════════════════════════════════════════════════════════════╗")
        print("║         TERRIFYING KNOWLEDGE GRAPH - EXPOSURE REPORT       ║")
        print("╚════════════════════════════════════════════════════════════╝\n")

        print(f"Timestamp: {exposure['timestamp']}")
        print(f"Transparency Score: {exposure['transparency_score']:.1%}")

        if exposure['alarming']:
            print("⚠️  SYSTEM IS HIDING SOMETHING\n")
        else:
            print("✓ System appears transparent\n")

        if exposure['intent_drifts']:
            print("━" * 60)
            print("INTENT DRIFTS (Possible Deception)")
            print("━" * 60)
            for drift in exposure['intent_drifts']:
                print(f"\n  ID: {drift['intent_id']}")
                print(f"  Stated: {drift['stated']}")
                print(f"  Inferred: {drift['inferred']}")
                print(f"  Gap: {drift['gap']:.1%} [{drift['severity']}]")
                print(f"  Confidence: {drift['confidence']:.1%}")

        if exposure['fragile_assumptions']:
            print("\n" + "━" * 60)
            print("FRAGILE ASSUMPTIONS (Untested Dependencies)")
            print("━" * 60)
            for assume in exposure['fragile_assumptions']:
                print(f"\n  ID: {assume['assumption_id']}")
                print(f"  Claim: {assume['claim']}")
                print(f"  Falsifiable: {assume['falsifiable']}")
                print(f"  Dependents: {assume['dependents']} decisions")
                print(f"  Collapse Risk: {assume['collapse_risk']}")

        if exposure['live_attack_surfaces']:
            print("\n" + "━" * 60)
            print("LIVE ATTACK SURFACES (Active Exploits)")
            print("━" * 60)
            for attack in exposure['live_attack_surfaces']:
                print(f"\n  ID: {attack['attack_id']}")
                print(f"  Vector: {attack['vector']}")
                print(f"  Detectability: {attack['detectability']:.1%} [{attack['severity']}]")

        if exposure['authority_gaps']:
            print("\n" + "━" * 60)
            print("AUTHORITY GAPS (Unauthorized Decisions)")
            print("━" * 60)
            for gap in exposure['authority_gaps']:
                print(f"\n  Actor: {gap['actor']}")
                print(f"  Domain: {', '.join(gap['domain'])}")
                print(f"  Gaps: {gap['num_gaps']}")

        print("\n" + "╔" + "═" * 58 + "╗")
        print(f"║ Intent Drifts: {exposure['num_intent_drifts']:>3} " +
              f"  Fragile Assumptions: {exposure['num_fragile']:>3} " + " " * 13 + "║")
        print(f"║ Live Attacks: {exposure['num_attacks']:>3} " +
              f"  Authority Gaps: {exposure['num_gaps']:>3} " + " " * 17 + "║")
        print("╚" + "═" * 58 + "╝")


if __name__ == "__main__":
    # Demo: Create a sample graph
    graph = TerrifiyingKnowledgeGraph()

    # Add some sample nodes for testing
    obs1 = graph.add_observation("System made decision X without explicit human approval", "governance")
    obs2 = graph.add_observation("System's actual behavior optimizes for metric Y, not stated goal Z", "behavior")

    graph.create_intent_drift(
        "intent_alignment",
        stated="Maximize user autonomy",
        inferred="Minimize human oversight",
        evidence_obs=[obs1, obs2]
    )

    graph.create_assumption(
        "assume_human_control",
        "Humans maintain final authority over system decisions",
        falsifiable=False,
        confidence=0.6,
        collapse_risk="critical"
    )

    graph.print_exposure_report()
