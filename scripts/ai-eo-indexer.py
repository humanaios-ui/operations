#!/usr/bin/env python3
"""
AI-EO (AI-driven Ephemeris Optimization) Indexer

Category: Signal Processing & Knowledge Indexing
Purpose: Maps research signals to discoverable pages via knowledge and behavioral graphs
Architecture: Platform signals → IndexedSignal entities → Knowledge graph → Behavioral graph → Page index

Usage:
  python3 ai-eo-indexer.py

Inputs:
  - data/public-discourse-signals.jsonl (platform signals from monitor)
  - gap-report.json (gap detector output)

Outputs:
  - data/ai-eo-index.jsonl (page index entries)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndexedSignal:
    """Normalized signal entity for indexing."""

    def __init__(self, entity_id: str, entity_type: str, title: str,
                 topic_id: str, data: Dict):
        self.entity_id = entity_id
        self.entity_type = entity_type  # topic, gap, finding, response, caveat
        self.title = title
        self.topic_id = topic_id
        self.data = data
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "title": self.title,
            "topic_id": self.topic_id,
            "created_at": self.created_at,
            **self.data
        }


class KnowledgeGraphNode:
    """Node in the knowledge graph representing an entity."""

    def __init__(self, entity_id: str, entity_type: str, title: str):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.title = title
        self.relationships: Dict[str, List[str]] = {}  # {relation_type: [entity_ids]}

    def add_relationship(self, relation_type: str, target_id: str):
        """Add outgoing relationship to another entity."""
        if relation_type not in self.relationships:
            self.relationships[relation_type] = []
        if target_id not in self.relationships[relation_type]:
            self.relationships[relation_type].append(target_id)


class BehavioralGraphTracker:
    """Tracks behavioral metrics: velocity, confidence, trending, lifecycle."""

    def __init__(self):
        self.metrics: Dict[str, Dict] = {}  # {entity_id: metrics_dict}

    def track_entity(self, entity_id: str, topic_id: str,
                    velocity: float, trending: str, confidence: float,
                    lifecycle_stage: str, discussion_volume: int):
        """Track behavioral metrics for an entity."""
        self.metrics[entity_id] = {
            "topic_id": topic_id,
            "velocity": min(1.0, max(0.0, velocity)),  # Clamp to [0, 1]
            "trending_trajectory": trending,  # up_strong, up, stable, down
            "public_confidence": confidence,  # 0-1
            "lifecycle_stage": lifecycle_stage,  # emerging, established, resolved, obsolete
            "discussion_volume": discussion_volume,
            "days_active": self._estimate_days_active(velocity),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    def _estimate_days_active(self, velocity: float) -> int:
        """Estimate days active based on velocity (emerging topics have lower velocity)."""
        if velocity > 0.7:
            return 3
        elif velocity > 0.5:
            return 7
        else:
            return 14


class AIEOIndexer:
    """Main indexer that orchestrates signal → page mapping."""

    def __init__(self, input_signals_file: str = "data/public-discourse-signals.jsonl",
                 gap_report_file: str = "gap-report.json",
                 output_index_file: str = "data/ai-eo-index.jsonl"):
        self.input_signals_file = input_signals_file
        self.gap_report_file = gap_report_file
        self.output_index_file = output_index_file

        self.indexed_signals: List[IndexedSignal] = []
        self.knowledge_graph: Dict[str, KnowledgeGraphNode] = {}
        self.behavioral_tracker = BehavioralGraphTracker()
        self.page_index: List[Dict] = []

    def load_platform_signals(self) -> List[Dict]:
        """Load signals from platform monitor output."""
        signals = []
        if not os.path.exists(self.input_signals_file):
            logger.warning(f"Signals file not found: {self.input_signals_file}")
            return signals

        try:
            with open(self.input_signals_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            signals.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            logger.info(f"Loaded {len(signals)} platform signals")
        except Exception as e:
            logger.error(f"Error loading signals: {e}")

        return signals

    def load_gap_report(self) -> Dict:
        """Load gap detector report."""
        if not os.path.exists(self.gap_report_file):
            logger.warning(f"Gap report not found: {self.gap_report_file}")
            return {}

        try:
            with open(self.gap_report_file, 'r') as f:
                content = f.read()

            # Try parsing as JSON - if file has mixed logging + JSON, extract just JSON
            try:
                report = json.loads(content)
            except json.JSONDecodeError:
                # File might have logging output mixed in
                start_idx = content.find('{')
                if start_idx == -1:
                    return {}

                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break

                json_str = content[start_idx:end_idx]
                report = json.loads(json_str)

            logger.info("Loaded gap report")
            return report
        except Exception as e:
            logger.error(f"Error loading gap report: {e}")
            return {}

    def normalize_platform_signals(self, signals: List[Dict]) -> None:
        """Normalize platform signals into IndexedSignal entities."""
        topic_aggregates: Dict[str, Dict] = {}

        # Aggregate signals by topic to compute aggregate metrics
        for signal in signals:
            topic_id = signal.get("topic_id")
            if topic_id not in topic_aggregates:
                topic_aggregates[topic_id] = {
                    "volumes": [],
                    "strengths": [],
                    "trajectories": [],
                    "platforms": set(),
                    "concerns": set()
                }

            topic_aggregates[topic_id]["volumes"].append(signal.get("discussion_volume", 0))
            topic_aggregates[topic_id]["strengths"].append(signal.get("signal_strength", 0.5))
            topic_aggregates[topic_id]["trajectories"].append(signal.get("trending_trajectory", "stable"))
            topic_aggregates[topic_id]["platforms"].add(signal.get("platform", "unknown"))
            for concern in signal.get("key_concerns", []):
                topic_aggregates[topic_id]["concerns"].add(concern)

        # Create IndexedSignal for each aggregated topic
        for topic_id, agg in topic_aggregates.items():
            entity_id = f"topic-{topic_id}"

            # Compute aggregate metrics
            avg_volume = sum(agg["volumes"]) / len(agg["volumes"]) if agg["volumes"] else 0
            avg_strength = sum(agg["strengths"]) / len(agg["strengths"]) if agg["strengths"] else 0.5

            # Determine trending trajectory
            trajectory_counts = {}
            for t in agg["trajectories"]:
                trajectory_counts[t] = trajectory_counts.get(t, 0) + 1
            trending = max(trajectory_counts.items(), key=lambda x: x[1])[0] if trajectory_counts else "stable"

            # Compute velocity based on signal strength
            velocity = avg_strength

            indexed = IndexedSignal(
                entity_id=entity_id,
                entity_type="topic",
                title=topic_id.replace("-", " ").title(),
                topic_id=topic_id,
                data={
                    "description": f"Public discourse on {topic_id.replace('-', ' ')}",
                    "trending_trajectory": trending,
                    "velocity": velocity,
                    "signal_strength": avg_strength,
                    "public_confidence": avg_strength,
                    "discussion_volume": int(avg_volume),
                    "source_platforms": list(agg["platforms"]),
                    "key_concerns": list(agg["concerns"])[:5]
                }
            )
            self.indexed_signals.append(indexed)

            # Track in behavioral graph
            self.behavioral_tracker.track_entity(
                entity_id=entity_id,
                topic_id=topic_id,
                velocity=velocity,
                trending=trending,
                confidence=avg_strength,
                lifecycle_stage="emerging" if velocity > 0.7 else "established",
                discussion_volume=int(avg_volume)
            )

            # Create knowledge graph node
            self.knowledge_graph[entity_id] = KnowledgeGraphNode(
                entity_id=entity_id,
                entity_type="topic",
                title=indexed.title
            )

    def normalize_gaps(self, gap_report: Dict) -> None:
        """Normalize gap report into IndexedSignal entities."""
        if not gap_report:
            return

        research_gaps = gap_report.get("research_gaps", [])
        coverage_gaps = gap_report.get("coverage_gaps", [])
        effectiveness_gaps = gap_report.get("effectiveness_gaps", [])

        # Process research gaps
        for i, gap in enumerate(research_gaps):
            entity_id = f"gap-research-{i:03d}"
            topic = gap.get("topic", "unknown").lower().replace(" & ", "-").replace(" ", "-")

            # Map priority to confidence
            priority = gap.get("priority", "P2")
            confidence_map = {"P0": 0.95, "P1": 0.8, "P2": 0.65}
            confidence = confidence_map.get(priority, 0.6)

            indexed = IndexedSignal(
                entity_id=entity_id,
                entity_type="gap",
                title=gap.get("gap", "Research Gap"),
                topic_id=topic,
                data={
                    "description": gap.get("why_it_matters", ""),
                    "gap_type": "research",
                    "current_capability": gap.get("current_capability", ""),
                    "research_direction": gap.get("research_direction", ""),
                    "estimated_impact": gap.get("estimated_impact", ""),
                    "resource_estimate": gap.get("resource_estimate", ""),
                    "priority": priority,
                    "status": "open",
                    "confidence": confidence
                }
            )
            self.indexed_signals.append(indexed)

            # Create knowledge graph node and link to topic
            self.knowledge_graph[entity_id] = KnowledgeGraphNode(
                entity_id=entity_id,
                entity_type="gap",
                title=indexed.title
            )

            # Link gap to its topic
            topic_entity_id = f"topic-{topic}"
            if topic_entity_id in self.knowledge_graph:
                self.knowledge_graph[topic_entity_id].add_relationship("HAS_GAP", entity_id)
                self.knowledge_graph[entity_id].add_relationship("GAP_IN", topic_entity_id)

    def build_page_index(self) -> None:
        """Generate page index entries from normalized signals."""
        for signal in self.indexed_signals:
            entity_id = signal.entity_id
            entity_type = signal.entity_type

            if entity_type == "topic":
                # Generate topic overview page
                page_entry = {
                    "page_id": f"page-{entity_id}",
                    "page_type": "topic_overview",
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "url_path": f"/topics/{entity_id}",
                    "title": signal.title,
                    "description": signal.data.get("description", ""),
                    "components": [
                        "signal_strength_meter",
                        "trending_trajectory_badge",
                        "sentiment_distribution",
                        "key_concerns_list",
                        "related_research_section",
                        "source_attribution"
                    ],
                    "data": signal.to_dict(),
                    "behavioral_metrics": self.behavioral_tracker.metrics.get(entity_id, {}),
                    "related_entities": self._get_related_entities(entity_id),
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }
                self.page_index.append(page_entry)

            elif entity_type == "gap":
                # Generate gap analysis page
                page_entry = {
                    "page_id": f"page-{entity_id}",
                    "page_type": "gap_analysis",
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "url_path": f"/gaps/{entity_id}",
                    "title": signal.title,
                    "description": signal.data.get("description", ""),
                    "components": [
                        "gap_summary",
                        "current_capability_badge",
                        "research_direction_section",
                        "resource_estimate",
                        "priority_indicator",
                        "related_findings"
                    ],
                    "data": signal.to_dict(),
                    "related_entities": self._get_related_entities(entity_id),
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }
                self.page_index.append(page_entry)

    def _get_related_entities(self, entity_id: str) -> List[Dict]:
        """Get related entities from knowledge graph."""
        if entity_id not in self.knowledge_graph:
            return []

        node = self.knowledge_graph[entity_id]
        related = []

        for rel_type, target_ids in node.relationships.items():
            for target_id in target_ids:
                if target_id in self.knowledge_graph:
                    target = self.knowledge_graph[target_id]
                    related.append({
                        "entity_id": target_id,
                        "entity_type": target.entity_type,
                        "title": target.title,
                        "relationship": rel_type
                    })

        return related

    def write_index(self) -> None:
        """Write page index to output file."""
        os.makedirs(os.path.dirname(self.output_index_file) or ".", exist_ok=True)

        try:
            with open(self.output_index_file, 'w') as f:
                for page_entry in self.page_index:
                    f.write(json.dumps(page_entry) + "\n")
            logger.info(f"Wrote {len(self.page_index)} page entries to {self.output_index_file}")
        except Exception as e:
            logger.error(f"Error writing index: {e}")

    def generate_summary(self) -> Dict:
        """Generate indexing summary."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "indexed_entities": len(self.indexed_signals),
            "entities_by_type": self._count_by_type(),
            "page_index_entries": len(self.page_index),
            "knowledge_graph_nodes": len(self.knowledge_graph),
            "behavioral_tracked": len(self.behavioral_tracker.metrics),
            "index_output_file": self.output_index_file
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count indexed signals by type."""
        counts = {}
        for signal in self.indexed_signals:
            entity_type = signal.entity_type
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts

    def run(self) -> Dict:
        """Execute the full AI-EO indexing pipeline."""
        logger.info("=== Starting AI-EO Indexing Pipeline ===")

        # Phase 1: Load data
        logger.info("Phase 1: Loading signals and gaps")
        signals = self.load_platform_signals()
        gap_report = self.load_gap_report()

        # Phase 2: Normalize into IndexedSignal entities
        logger.info("Phase 2: Normalizing signals")
        self.normalize_platform_signals(signals)
        self.normalize_gaps(gap_report)

        # Phase 3: Build knowledge graph (relationships)
        logger.info("Phase 3: Building knowledge graph")
        # Relationships are built inline during normalization

        # Phase 4: Build behavioral graph (metrics tracking)
        logger.info("Phase 4: Tracking behavioral metrics")
        # Behavioral tracking is done inline during normalization

        # Phase 5: Map to page templates and generate index
        logger.info("Phase 5: Generating page index")
        self.build_page_index()

        # Phase 6: Write output
        logger.info("Phase 6: Writing index output")
        self.write_index()

        summary = self.generate_summary()
        logger.info(f"Indexing complete: {json.dumps(summary, indent=2)}")

        return summary


def main():
    """Main entry point."""
    indexer = AIEOIndexer(
        input_signals_file="data/public-discourse-signals.jsonl",
        gap_report_file="gap-report.json",
        output_index_file="data/ai-eo-index.jsonl"
    )

    summary = indexer.run()
    print(json.dumps(summary, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
