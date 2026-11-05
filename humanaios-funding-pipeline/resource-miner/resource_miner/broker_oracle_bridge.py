"""Read-only adapter: existing Resource Broker -> Oracle consumer.

Source snapshots come from separate, authorized collection. No Gmail, network,
queue storage, GitHub comments, coordinator actions, or execution here.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from .internal_repository_broker import project


def _consumer_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "oracles" / "engine" / "resource_broker_consumer_v0_1.py"
    if not path.is_file():
        raise RuntimeError("Oracle consumer is unavailable; no fallback consumer is permitted")
    spec = importlib.util.spec_from_file_location("resource_broker_consumer_v0_1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Oracle consumer cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bridge(snapshot: dict, *, recorded_at: str | None = None) -> dict:
    """Use the actual broker function; hand its immutable result to Oracle."""
    return _consumer_module().consume(project(snapshot), recorded_at=recorded_at)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline Resource Broker to Oracle advisory bridge")
    parser.add_argument("--input", required=True, help="Privacy-reviewed public-safe broker snapshot")
    parser.add_argument("--recorded-at", help="Optional offset-aware record timestamp")
    args = parser.parse_args(argv)
    with open(args.input, encoding="utf-8") as stream:
        snapshot = json.load(stream)
    result = bridge(snapshot, recorded_at=args.recorded_at)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
