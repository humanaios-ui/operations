#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.research.trace_summary import summarize_trace, write_summary

SCENARIO_MODULE = "tests.research.test_research_scenarios"
SCENARIO_FUNCTIONS = [
    "test_S1_baseline_homeostasis",
    "test_S2_signal_semantics",
    "test_S3_distributed_resilience",
    "test_S4_resource_clamp_invariants",
    "test_S5_control_vs_generative_opposition",
    "test_S6_composite_signal_fanout",
    "test_S7_sanjiao_threshold_edges",
    "test_S8_wuxing_transfer_conservation_like",
    "test_S9_no_regulate_on_channel_propagation",
    "test_S10_blood_attribution_dropout_detection",
]


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _load_scenarios() -> Dict[str, Callable[[], Dict[str, Any]]]:
    module = importlib.import_module(SCENARIO_MODULE)
    loaded: Dict[str, Callable[[], Dict[str, Any]]] = {}
    for fn_name in SCENARIO_FUNCTIONS:
        fn = getattr(module, fn_name, None)
        if fn is None:
            raise RuntimeError(f"Missing required scenario: {SCENARIO_MODULE}.{fn_name}")
        loaded[fn_name.replace("test_", "", 1)] = fn
    return loaded


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run research validation scenarios.")
    parser.add_argument("--scenario", action="append", default=[], help="Scenario id, e.g. S2_signal_semantics")
    parser.add_argument("--with-trace", action="store_true", help="Run traced liver stagnation scenario")
    parser.add_argument("--trace-ticks", type=int, default=20, help="Ticks to run in traced scenario")
    return parser.parse_args()


def _artifact_paths() -> tuple[Path, Path]:
    stamp = _utc_now().strftime("%Y%m%dT%H%M%SZ")
    root = Path("artifacts")
    root.mkdir(parents=True, exist_ok=True)
    return root / f"research_validation_{stamp}.json", root / f"research_validation_{stamp}.csv"


def _run_scenarios(selected: List[str]) -> List[Dict[str, Any]]:
    scenarios = _load_scenarios()
    to_run = selected if selected else list(scenarios.keys())

    unknown = sorted(set(to_run) - set(scenarios.keys()))
    if unknown:
        raise SystemExit(f"Unknown scenarios: {unknown}")

    results: List[Dict[str, Any]] = []
    for scenario in to_run:
        start = _utc_now()
        try:
            payload = scenarios[scenario]() or {}
            status = "PASS"
            error = ""
        except AssertionError as exc:
            payload = {}
            status = "FAIL"
            error = f"AssertionError: {exc}"
        except Exception as exc:  # pylint: disable=broad-except
            payload = {}
            status = "ERROR"
            error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        end = _utc_now()
        results.append(
            {
                "scenario": scenario,
                "status": status,
                "duration_ms": int((end - start).total_seconds() * 1000),
                "error": error,
                "payload": payload,
                "started_at": start.isoformat(),
                "ended_at": end.isoformat(),
            }
        )
    return results


def _summary(results: List[Dict[str, Any]], started_at: dt.datetime, ended_at: dt.datetime) -> Dict[str, Any]:
    return {
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_ms": int((ended_at - started_at).total_seconds() * 1000),
        "total": len(results),
        "pass": sum(1 for row in results if row["status"] == "PASS"),
        "fail": sum(1 for row in results if row["status"] == "FAIL"),
        "error": sum(1 for row in results if row["status"] == "ERROR"),
    }


def _write_csv(csv_path: Path, results: List[Dict[str, Any]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["scenario", "status", "duration_ms", "error", "started_at", "ended_at"],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})


def _run_trace(trace_ticks: int) -> Dict[str, Any]:
    trace_module = importlib.import_module("tests.research.scenarios_trace")
    trace_metadata = trace_module.run_traced_liver_stagnation(ticks=trace_ticks)

    summary_path = Path("artifacts/traces/S2_liver_stagnation_trace_summary.json")
    summary = summarize_trace(trace_metadata["trace_path"])
    write_summary(summary, str(summary_path))

    trace_metadata["summary_path"] = str(summary_path)
    trace_metadata["summary"] = summary
    return trace_metadata


def main() -> None:
    args = _parse_args()
    started_at = _utc_now()
    results = _run_scenarios(args.scenario)

    trace: Dict[str, Any] | None = None
    if args.with_trace:
        trace = _run_trace(args.trace_ticks)

    ended_at = _utc_now()
    report = {
        "scenario_module": SCENARIO_MODULE,
        "summary": _summary(results, started_at, ended_at),
        "results": results,
    }
    if trace is not None:
        report["trace"] = trace

    json_path, csv_path = _artifact_paths()
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    _write_csv(csv_path, results)

    print(f"[artifact] {json_path}")
    print(f"[artifact] {csv_path}")
    print(f"[summary] {report['summary']}")

    if report["summary"]["fail"] > 0 or report["summary"]["error"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
