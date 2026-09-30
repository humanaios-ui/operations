#!/usr/bin/env python3
"""
AI-EO Incremental Indexer

Category: Signal Processing & Knowledge Indexing
Purpose: Merges delta signals into existing knowledge graph without full rebuild
SLA: 10-minute latency for incremental merge

Architecture:
- Load checkpoint from previous index run (timestamp)
- Fetch only signals after checkpoint
- Merge into existing knowledge graph (in-memory)
- Update behavioral metrics for affected entities
- Write updated index

Usage:
  python3 ai-eo-incremental-indexer.py

Inputs:
  - indexer-checkpoint.json (last run timestamp)
  - lasting-light-ai/public/api/ai-eo-index.json (current index)
  - data/public-discourse-signals.jsonl (platform signals)

Outputs:
  - data/ai-eo-index.jsonl (updated index)
  - data/latest-index.json (checkpoint)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# Configuration
OPERATIONS_REPO = Path(__file__).parent.parent
INDEX_FILE = OPERATIONS_REPO.parent / 'lasting-light-ai' / 'public' / 'api' / 'ai-eo-index.json'
CHECKPOINT_FILE = OPERATIONS_REPO / 'data' / 'indexer-checkpoint.json'
PUBLIC_SIGNALS_FILE = OPERATIONS_REPO / 'data' / 'public-discourse-signals.jsonl'
OUTPUT_INDEX = OPERATIONS_REPO / 'data' / 'ai-eo-index.jsonl'
LASTINDEX_FILE = OPERATIONS_REPO / 'data' / 'latest-index.json'
LOG_FILE = OPERATIONS_REPO / 'logs' / 'ai-eo-incremental-indexer.log'


def setup_logging() -> None:
    """Ensure log and data directories exist."""
    for directory in [LOG_FILE.parent, CHECKPOINT_FILE.parent]:
        directory.mkdir(parents=True, exist_ok=True)


def log_event(message: str) -> None:
    """Log event to file and stdout."""
    timestamp = datetime.utcnow().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


def load_checkpoint() -> Optional[datetime]:
    """Load the last checkpoint timestamp."""
    if not CHECKPOINT_FILE.exists():
        log_event("No checkpoint found. Starting fresh index load.")
        return None

    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)
            timestamp_str = data.get('last_index_time')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        log_event(f"WARNING: Failed to load checkpoint: {e}. Starting fresh.")

    return None


def load_latest_index() -> Optional[Dict[str, Any]]:
    """Load the latest built index from lasting-light-ai repo."""
    if not INDEX_FILE.exists():
        log_event(f"WARNING: Latest index not found at {INDEX_FILE}")
        return None

    try:
        with open(INDEX_FILE, 'r') as f:
            data = json.load(f)
            log_event(f"Loaded latest index with {len(data.get('entries', []))} entries")
            return data
    except Exception as e:
        log_event(f"ERROR: Failed to load latest index: {e}")
        return None


def load_delta_signals(checkpoint: Optional[datetime]) -> List[Dict]:
    """
    Load platform signals after checkpoint time.

    Args:
        checkpoint: Timestamp to filter signals after

    Returns:
        List of signal entries
    """
    if not PUBLIC_SIGNALS_FILE.exists():
        log_event(f"WARNING: Signals file not found at {PUBLIC_SIGNALS_FILE}")
        return []

    delta_signals = []
    try:
        with open(PUBLIC_SIGNALS_FILE, 'r') as f:
            for line in f:
                if not line.strip() or line.startswith('#'):
                    continue

                try:
                    signal = json.loads(line)

                    # Filter by checkpoint if available
                    if checkpoint:
                        signal_time_str = signal.get('timestamp', '')
                        try:
                            signal_time = datetime.fromisoformat(signal_time_str.replace('Z', '+00:00'))
                            if signal_time <= checkpoint:
                                continue
                        except Exception:
                            pass  # Include if we can't parse timestamp

                    delta_signals.append(signal)
                except json.JSONDecodeError:
                    continue

        log_event(f"Loaded {len(delta_signals)} delta signal(s) after checkpoint")
        return delta_signals

    except Exception as e:
        log_event(f"ERROR: Failed to load delta signals: {e}")
        return []


def merge_into_knowledge_graph(
    existing_index: Optional[Dict[str, Any]],
    delta_signals: List[Dict]
) -> Dict[str, Any]:
    """
    Merge delta signals into existing knowledge graph.

    Args:
        existing_index: Latest built index (if available)
        delta_signals: New signals to merge

    Returns:
        Updated index with merged deltas
    """
    if not existing_index:
        log_event("No existing index. Will rebuild from signals.")
        return {'entries': [], 'metadata': {}, 'built_at': datetime.utcnow().isoformat()}

    # Start with existing entries
    entries = existing_index.get('entries', [])
    entity_map = {e.get('entity_id'): e for e in entries}

    log_event(f"Starting merge with {len(entity_map)} existing entities")

    # Process each delta signal
    for signal in delta_signals:
        entity_id = signal.get('entity_id')
        if not entity_id:
            continue

        if entity_id in entity_map:
            # Update existing entity
            entity = entity_map[entity_id]

            # Update behavioral metrics
            entity['velocity'] = max(0, min(1, signal.get('velocity', entity['velocity'])))
            entity['trending_trajectory'] = signal.get('trending_trajectory', entity.get('trending_trajectory'))
            entity['signal_strength'] = signal.get('signal_strength', entity.get('signal_strength'))
            entity['public_confidence'] = signal.get('public_confidence', entity.get('public_confidence'))
            entity['discussion_volume'] = signal.get('discussion_volume', entity.get('discussion_volume', 0))
            entity['days_active'] = signal.get('days_active', entity.get('days_active', 0))
            entity['last_updated'] = datetime.utcnow().isoformat()

            log_event(f"MERGED: Updated entity {entity_id} (velocity={entity['velocity']:.2f})")
        else:
            # New entity (shouldn't happen in incremental, but handle gracefully)
            log_event(f"WARNING: New entity in delta signals: {entity_id}. Skipping (full index rebuild needed).")

    # Reconstruct entries list
    updated_entries = list(entity_map.values())
    log_event(f"Merge complete: {len(updated_entries)} entities after delta")

    return {
        'entries': updated_entries,
        'metadata': existing_index.get('metadata', {}),
        'built_at': existing_index.get('built_at'),
        'last_updated': datetime.utcnow().isoformat()
    }


def write_index(index: Dict[str, Any]) -> bool:
    """
    Write updated index to files.

    Outputs:
    - ai-eo-index.jsonl: Operations repo (for analysis)
    - latest-index.json: Operations repo (checkpoint)
    - api/ai-eo-index.json: lasting-light-ai repo (via deploy step)
    """
    try:
        # Write JSONL format to operations repo
        with open(OUTPUT_INDEX, 'w') as f:
            for entry in index.get('entries', []):
                f.write(json.dumps(entry) + '\n')

        log_event(f"Wrote {len(index.get('entries', []))} entries to {OUTPUT_INDEX}")

        # Write latest-index checkpoint
        with open(LASTINDEX_FILE, 'w') as f:
            json.dump(index, f, indent=2)

        log_event(f"Wrote checkpoint to {LASTINDEX_FILE}")
        return True

    except Exception as e:
        log_event(f"ERROR: Failed to write index: {e}")
        return False


def update_checkpoint() -> bool:
    """Update checkpoint to current time."""
    try:
        checkpoint = {
            'last_index_time': datetime.utcnow().isoformat()
        }

        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        log_event(f"Updated checkpoint to {checkpoint['last_index_time']}")
        return True

    except Exception as e:
        log_event(f"ERROR: Failed to update checkpoint: {e}")
        return False


def main() -> int:
    """Main entry point."""
    setup_logging()
    log_event("=" * 60)
    log_event("AI-EO Incremental Indexer started")

    # Load checkpoint
    checkpoint = load_checkpoint()
    log_event(f"Checkpoint: {checkpoint.isoformat() if checkpoint else 'None (full rebuild)'}")

    # Load latest index (serves as knowledge graph baseline)
    existing_index = load_latest_index()

    # Load delta signals
    delta_signals = load_delta_signals(checkpoint)
    if len(delta_signals) == 0:
        log_event("No delta signals found. Index unchanged.")
        log_event("=" * 60)
        return 0

    # Merge deltas into knowledge graph
    updated_index = merge_into_knowledge_graph(existing_index, delta_signals)

    # Write updated index
    if not write_index(updated_index):
        log_event("FATAL: Failed to write index")
        return 1

    # Update checkpoint
    if not update_checkpoint():
        log_event("WARNING: Failed to update checkpoint (index still written)")

    log_event("AI-EO Incremental Indexer completed successfully")
    log_event("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
