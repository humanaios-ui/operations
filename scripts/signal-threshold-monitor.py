#!/usr/bin/env python3
"""
Signal Threshold Monitor
Detects emerging trends (velocity > 0.6, trending up) and emits events for event-driven indexing.

Architecture:
- Loads latest AI-EO index
- Scans for topics exceeding velocity threshold
- Emits GitHub Actions workflow_dispatch events for incremental indexing
- Targets: 8-minute latency from detection to index update
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configuration
VELOCITY_THRESHOLD = 0.6
TRENDING_KEYWORDS = ['up_strong', 'up']
INDEX_FILE = Path(__file__).parent.parent.parent / 'lasting-light-ai' / 'public' / 'api' / 'ai-eo-index.json'
OPERATIONS_REPO = Path(__file__).parent.parent
LOG_FILE = OPERATIONS_REPO / 'logs' / 'signal-threshold-monitor.log'


def setup_logging() -> None:
    """Ensure log directory exists."""
    log_dir = LOG_FILE.parent
    log_dir.mkdir(parents=True, exist_ok=True)


def log_event(message: str) -> None:
    """Log event to file and stdout."""
    timestamp = datetime.utcnow().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)

    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


def load_index() -> Optional[list]:
    """Load the latest AI-EO index file."""
    if not INDEX_FILE.exists():
        log_event(f"ERROR: Index file not found at {INDEX_FILE}")
        return None

    try:
        with open(INDEX_FILE, 'r') as f:
            data = json.load(f)
            # If it's a dict with an 'entries' key, extract the list
            if isinstance(data, dict) and 'entries' in data:
                return data['entries']
            # Otherwise assume it's already a list of entries
            return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        log_event(f"ERROR: Failed to parse index JSON: {e}")
        return None
    except Exception as e:
        log_event(f"ERROR: Failed to load index: {e}")
        return None


def check_velocity_threshold(entry: dict) -> bool:
    """
    Check if an entry exceeds velocity threshold and is trending up.

    Args:
        entry: Index entry with velocity and trending_trajectory fields

    Returns:
        True if entry should trigger event, False otherwise
    """
    velocity = entry.get('velocity', 0)
    trending = entry.get('trending_trajectory', 'stable')

    # Must exceed velocity threshold AND be trending up
    return velocity > VELOCITY_THRESHOLD and trending in TRENDING_KEYWORDS


def detect_high_velocity_signals(entries: list) -> list:
    """
    Scan index entries for high-velocity signals.

    Returns:
        List of entries that exceed velocity threshold
    """
    high_velocity = []

    for entry in entries:
        if entry.get('entity_type') == 'topic' and check_velocity_threshold(entry):
            high_velocity.append(entry)
            log_event(
                f"SIGNAL DETECTED: {entry.get('title', 'unknown')} "
                f"(velocity={entry.get('velocity'):.2f}, "
                f"trending={entry.get('trending_trajectory')})"
            )

    return high_velocity


def emit_event(signals: list) -> bool:
    """
    Emit GitHub Actions workflow_dispatch event for incremental indexing.

    Strategy: Collect all high-velocity signals and trigger ONE indexing run
    to process them together (batch efficiency).

    Args:
        signals: List of high-velocity signal entries

    Returns:
        True if event was emitted successfully
    """
    if not signals:
        log_event("No high-velocity signals detected. Skipping event emission.")
        return False

    try:
        # Prepare payload with signal metadata
        signal_ids = [s.get('entity_id') for s in signals]

        log_event(f"Emitting event for {len(signals)} high-velocity signal(s): {', '.join(signal_ids)}")

        # Use GitHub CLI to trigger workflow_dispatch
        # This requires GITHUB_TOKEN to be set in environment
        result = subprocess.run([
            'gh', 'workflow', 'run',
            'daily-topic-digest.yml',
            '--repo', 'humanaios-ui/operations',
            '-f', f'trigger=signal-threshold-monitor',
            '-f', f'signal_count={len(signals)}',
            '-f', f'signal_ids={",".join(signal_ids)}'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            log_event(f"ERROR: Failed to emit event: {result.stderr}")
            return False

        log_event(f"SUCCESS: Event emitted to workflow (signals: {len(signals)})")
        return True

    except FileNotFoundError:
        log_event("ERROR: 'gh' CLI not found. Install GitHub CLI to enable event emission.")
        return False
    except Exception as e:
        log_event(f"ERROR: Failed to emit event: {e}")
        return False


def generate_summary(signals: list) -> dict:
    """Generate summary of monitoring run."""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'signals_detected': len(signals),
        'event_emitted': len(signals) > 0,
        'signal_ids': [s.get('entity_id') for s in signals],
        'velocities': {s.get('entity_id'): s.get('velocity') for s in signals}
    }


def main() -> int:
    """Main entry point."""
    setup_logging()
    log_event("=" * 60)
    log_event("Signal Threshold Monitor started")

    # Load index
    entries = load_index()
    if entries is None:
        log_event("FATAL: Could not load index. Aborting.")
        return 1

    log_event(f"Loaded index with {len(entries)} entries")

    # Detect high-velocity signals
    signals = detect_high_velocity_signals(entries)
    log_event(f"Detected {len(signals)} high-velocity signal(s)")

    # Emit event if signals found
    success = emit_event(signals)

    # Generate summary
    summary = generate_summary(signals)
    log_event(f"Summary: {json.dumps(summary)}")
    log_event("Signal Threshold Monitor completed")
    log_event("=" * 60)

    return 0 if success or len(signals) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
