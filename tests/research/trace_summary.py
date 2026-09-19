from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict


def summarize_trace(trace_path: str) -> Dict[str, Any]:
    first_failure_tick_by_component: Dict[str, int] = {}
    total_delta_by_resource = defaultdict(float)
    source_strength = defaultdict(float)
    event_count = 0

    with Path(trace_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            event_count += 1

            metadata = event.get("metadata") or {}
            if metadata.get("failure"):
                component = event.get("component", "unknown")
                first_failure_tick_by_component.setdefault(component, event.get("tick", -1))

            for resource, value in (event.get("delta") or {}).items():
                total_delta_by_resource[resource] += float(value)

            signal = event.get("signal") or {}
            source = signal.get("source")
            strength = signal.get("strength")
            if source is not None and strength is not None:
                source_strength[str(source)] += abs(float(strength))

    top_signal_sources_by_abs_effect = [
        {"source": source, "abs_effect": effect}
        for source, effect in sorted(source_strength.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "trace_path": trace_path,
        "event_count": event_count,
        "first_failure_tick_by_component": first_failure_tick_by_component,
        "total_delta_by_resource": dict(total_delta_by_resource),
        "top_signal_sources_by_abs_effect": top_signal_sources_by_abs_effect,
    }


def write_summary(summary: Dict[str, Any], out_path: str) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize research trace JSONL output.")
    parser.add_argument("--trace", required=True, help="Path to trace jsonl file")
    parser.add_argument(
        "--out",
        default="artifacts/traces/S2_liver_stagnation_trace_summary.json",
        help="Path to output summary json",
    )
    args = parser.parse_args()

    summary = summarize_trace(args.trace)
    out_path = write_summary(summary, args.out)
    print(out_path)


if __name__ == "__main__":
    main()
